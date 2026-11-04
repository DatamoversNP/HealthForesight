"""Process-isolated analytical execution with hard cancel of DB work.

Celery soft/hard time limits alone do not reliably terminate an in-flight
PostgreSQL query. This module:
  1. Runs work in a child *subprocess* (own interpreter + connection).
  2. Records pg_backend_pid in a status file for the parent.
  3. On timeout/cancel: kill the child process group AND pg_terminate_backend.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

_CHILD_SCRIPT = r"""
import json, os, sys
status_path = sys.argv[1]
fn_module = sys.argv[2]
fn_name = sys.argv[3]
kwargs = json.loads(sys.argv[4])
out_path = sys.argv[5]
status = {"pid": os.getpid(), "pg_backend_pid": None, "phase": "running"}
open(status_path, "w").write(json.dumps(status))
try:
    import importlib
    mod = importlib.import_module(fn_module)
    fn = getattr(mod, fn_name)
    result = fn(**kwargs)
    # If DB work published pg_backend_pid, surface it for parent cancel
    if isinstance(result, dict) and result.get("pg_backend_pid"):
        status["pg_backend_pid"] = result.get("pg_backend_pid")
        open(status_path, "w").write(json.dumps(status))
    open(out_path, "w").write(json.dumps({"ok": True, "result": result}))
    status["phase"] = "done"
    open(status_path, "w").write(json.dumps(status))
except Exception as e:
    open(out_path, "w").write(json.dumps({"ok": False, "error": str(e)[:800]}))
    status["phase"] = "error"
    status["error"] = str(e)[:400]
    open(status_path, "w").write(json.dumps(status))
    sys.exit(1)
"""


def _terminate_pg_backend(pg_backend_pid: Optional[int]) -> bool:
    if not pg_backend_pid:
        return False
    try:
        from sqlalchemy import text
        from uepi_api.database import get_engine

        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SET statement_timeout = '5s'"))
            res = conn.execute(
                text("SELECT pg_terminate_backend(:pid)"),
                {"pid": int(pg_backend_pid)},
            ).scalar()
            conn.commit()
            return bool(res)
    except Exception:
        return False


def run_isolated(
    *,
    fn_module: str,
    fn_name: str,
    kwargs: Optional[dict] = None,
    timeout_s: float = 30.0,
    status_dir: Optional[Path] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
    """Run callable in a subprocess; hard-kill + pg_terminate on timeout/cancel."""
    kwargs = kwargs or {}
    status_dir = status_dir or Path("/tmp/uepi_isolated")
    status_dir.mkdir(parents=True, exist_ok=True)
    stamp = f"{os.getpid()}_{int(time.time() * 1000)}"
    status_path = status_dir / f"status_{stamp}.json"
    out_path = status_dir / f"out_{stamp}.json"

    env = os.environ.copy()
    env["UEPI_ISOLATED_STATUS_PATH"] = str(status_path)
    cmd = [
        sys.executable,
        "-c",
        _CHILD_SCRIPT,
        str(status_path),
        fn_module,
        fn_name,
        json.dumps(kwargs),
        str(out_path),
    ]
    started = time.time()
    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        start_new_session=True,  # own process group for killpg
    )
    cancelled = False
    timed_out = False
    pg_pid = None

    while proc.poll() is None:
        elapsed = time.time() - started
        if cancel_check and cancel_check():
            cancelled = True
            break
        if elapsed >= timeout_s:
            timed_out = True
            break
        try:
            if status_path.exists():
                st = json.loads(status_path.read_text())
                pg_pid = st.get("pg_backend_pid") or pg_pid
        except Exception:
            pass
        time.sleep(0.05)

    result: Dict[str, Any] = {
        "ok": False,
        "timed_out": timed_out,
        "cancelled": cancelled,
        "child_pid": proc.pid,
        "pg_backend_pid": pg_pid,
        "elapsed_s": round(time.time() - started, 3),
        "pg_terminated": False,
        "result": None,
        "error": None,
    }

    if timed_out or cancelled:
        try:
            if status_path.exists():
                st = json.loads(status_path.read_text())
                pg_pid = st.get("pg_backend_pid") or pg_pid
                result["pg_backend_pid"] = pg_pid
        except Exception:
            pass
        result["pg_terminated"] = _terminate_pg_backend(pg_pid)
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
        try:
            proc.wait(timeout=1.0)
        except Exception:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            try:
                proc.wait(timeout=1.0)
            except Exception:
                pass
        result["error"] = "CANCELLED" if cancelled else "TIMEOUT"
        result["ok"] = False
    else:
        try:
            proc.wait(timeout=2.0)
        except Exception:
            pass
        if out_path.exists():
            try:
                payload = json.loads(out_path.read_text())
                result["ok"] = bool(payload.get("ok"))
                result["result"] = payload.get("result")
                result["error"] = payload.get("error")
            except Exception as e:
                result["error"] = f"bad_out:{e}"
        else:
            result["error"] = "NO_RESULT"
            result["ok"] = False

    for p in (status_path, out_path):
        try:
            p.unlink(missing_ok=True)
        except Exception:
            pass
    return result


def probe_sleep_work(seconds: float = 0.2, marker: str = "") -> dict:
    """Lightweight probe used by concurrency benchmarks (no DB)."""
    time.sleep(float(seconds))
    return {"marker": marker, "slept": seconds, "pid": os.getpid()}


def probe_db_count_work(statement_sleep_s: float = 0.0) -> dict:
    """Bounded DB probe: optional pg_sleep then count claims (statement_timeout applies).

    Publishes pg_backend_pid early (via status file side-channel) by writing a
    sidecar when SLEEP_STATUS_PATH is set; always returns pid in the result.
    """
    from sqlalchemy import text
    from uepi_api.database import get_engine

    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SET statement_timeout = '25s'"))
        conn.execute(text("SET application_name = 'uepi_policy_analytics_probe'"))
        pid = conn.execute(text("SELECT pg_backend_pid()")).scalar()
        # Publish pid early so parent can terminate during long sleep
        status_env = os.environ.get("UEPI_ISOLATED_STATUS_PATH")
        if status_env and pid:
            try:
                Path(status_env).write_text(
                    json.dumps(
                        {"pid": os.getpid(), "pg_backend_pid": int(pid), "phase": "db_running"}
                    )
                )
            except Exception:
                pass
        if statement_sleep_s and statement_sleep_s > 0:
            conn.execute(text("SELECT pg_sleep(:s)"), {"s": float(statement_sleep_s)})
        n = conn.execute(text("SELECT COUNT(*) FROM claims_lines")).scalar()
    return {"claims_lines": int(n or 0), "pg_backend_pid": int(pid) if pid else None}
