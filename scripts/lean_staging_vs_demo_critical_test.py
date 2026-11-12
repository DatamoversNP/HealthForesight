#!/usr/bin/env python3
"""Ruthless demo vs lean-staging comparison: systems, integration, performance.

Read-only against demo. Staging may be exercised with login + list APIs.
Writes JSON+MD report under docs/production/releases/.
"""
from __future__ import annotations

import json
import os
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "docs" / "production" / "releases"
OUT_JSON = OUT_DIR / "LEAN_STAGING_VS_DEMO_CRITICAL_TEST.json"
OUT_MD = OUT_DIR / "LEAN_STAGING_VS_DEMO_CRITICAL_TEST.md"

DEMO_API = os.environ.get("DEMO_API_BASE", "https://healthforesight-api.azurewebsites.net/api/v1")
DEMO_WEB = os.environ.get("DEMO_WEB_BASE", "https://healthforesight-web.azurewebsites.net")
STG_API = os.environ.get(
    "STAGING_API_BASE",
    "https://hfleanstg-api.whiteplant-64737337.eastus2.azurecontainerapps.io/api/v1",
)
STG_WEB = os.environ.get(
    "STAGING_WEB_BASE",
    "https://hfleanstg-web.whiteplant-64737337.eastus2.azurecontainerapps.io",
)
EMAIL = os.environ.get("HF_TEST_EMAIL", "admin@healthforesight.com")
PASSWORD = os.environ.get("HF_TEST_PASSWORD", "Swan@1234")
NINE = [
    "d403f101-08dd-45c9-ab83-d42e37c62018",
    "d0eeb370-df14-4478-8755-dad6c3a35a47",
    "d7441dd9-3bfe-405e-ae6c-0377204bbb7e",
    "58b839b5-b6e0-59e0-9406-d817877c3ce8",
    "e11b049d-fcce-55cc-bcd7-71329038383b",
    "f2b8e7f3-1627-5dbe-8d7e-757ce21aa55b",
    "11218053-bdc0-569f-a415-fb61c5dcda37",
    "4f8c34e3-015b-509d-90ba-521261464258",
    "649b4ac8-ca82-5b84-aa87-84834490731a",
]


def _req(
    method: str,
    url: str,
    *,
    token: Optional[str] = None,
    body: Optional[dict] = None,
    timeout: float = 60,
) -> Tuple[int, float, Any]:
    data = None if body is None else json.dumps(body).encode()
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            dt = time.perf_counter() - t0
            try:
                payload = json.loads(raw.decode() or "null")
            except Exception:
                payload = raw[:200].decode("utf-8", "replace")
            return r.status, dt, payload
    except urllib.error.HTTPError as e:
        dt = time.perf_counter() - t0
        raw = e.read()[:800]
        try:
            payload = json.loads(raw.decode() or "null")
        except Exception:
            payload = raw.decode("utf-8", "replace")
        return e.code, dt, payload
    except Exception as e:
        dt = time.perf_counter() - t0
        return 0, dt, {"error": type(e).__name__, "detail": str(e)[:300]}


def _http_get(url: str, timeout: float = 45) -> Tuple[int, float, str]:
    req = urllib.request.Request(url, method="GET")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(500).decode("utf-8", "replace")
            return r.status, time.perf_counter() - t0, body
    except urllib.error.HTTPError as e:
        return e.code, time.perf_counter() - t0, e.read(200).decode("utf-8", "replace")
    except Exception as e:
        return 0, time.perf_counter() - t0, f"{type(e).__name__}: {e}"


def login(api: str) -> Tuple[Optional[str], float, Any]:
    code, dt, payload = _req("POST", f"{api}/auth/login", body={"email": EMAIL, "password": PASSWORD})
    if code == 200 and isinstance(payload, dict) and payload.get("access_token"):
        return payload["access_token"], dt, payload
    return None, dt, payload


def bench(api: str, token: str, path: str, repeats: int = 5) -> Dict[str, Any]:
    times: List[float] = []
    codes: List[int] = []
    last: Any = None
    for _ in range(repeats):
        code, dt, payload = _req("GET", f"{api}{path}", token=token, timeout=90)
        times.append(dt)
        codes.append(code)
        last = payload
    ok = all(c == 200 for c in codes)
    return {
        "path": path,
        "ok": ok,
        "codes": codes,
        "n": repeats,
        "p50_s": round(statistics.median(times), 3),
        "p95_s": round(sorted(times)[max(0, int(0.95 * (len(times) - 1)))], 3),
        "mean_s": round(statistics.mean(times), 3),
        "max_s": round(max(times), 3),
        "sample_keys": list(last.keys())[:12] if isinstance(last, dict) else type(last).__name__,
        "sample_len": len(last) if isinstance(last, list) else None,
    }


def env_probe(name: str, api: str, web: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"env": name, "api_base": api, "web_base": web, "systems": {}, "integration": {}, "performance": {}}

    # Systems
    for label, url in [
        ("web_root", web + "/"),
        ("api_health", api.replace("/api/v1", "") + "/health"),
        ("api_ready", api + "/ready" if api.endswith("/api/v1") else api.replace("/api/v1", "") + "/ready"),
        ("api_docs", api.replace("/api/v1", "") + "/docs"),
    ]:
        # ready is under /ready at root or /api/v1/ready
        if label == "api_ready":
            code, dt, body = _http_get(api.replace("/api/v1", "") + "/ready")
            if code == 404:
                code, dt, body = _http_get(api + "/ready")
        else:
            code, dt, body = _http_get(url)
        out["systems"][label] = {
            "http": code,
            "latency_s": round(dt, 3),
            "pass": code == 200,
            "snippet": (body[:120] if isinstance(body, str) else str(body)[:120]),
        }

    tok, login_s, login_payload = login(api)
    out["systems"]["login"] = {
        "pass": bool(tok),
        "latency_s": round(login_s, 3),
        "detail": "ok" if tok else login_payload,
    }
    if not tok:
        out["verdict"] = "FAIL"
        out["critical_findings"] = ["Login failed — cannot continue integration/perf"]
        return out

    # Integration
    policies_code, policies_dt, policies = _req("GET", f"{api}/policies", token=tok, timeout=120)
    policy_list = policies if isinstance(policies, list) else (policies.get("items") or policies.get("policies") or []) if isinstance(policies, dict) else []
    ids = {str(p.get("id") or p.get("policy_id")) for p in policy_list if isinstance(p, dict)}
    nine_present = [pid for pid in NINE if pid in ids]
    out["integration"]["policies_list"] = {
        "pass": policies_code == 200 and len(policy_list) >= 9,
        "http": policies_code,
        "latency_s": round(policies_dt, 3),
        "count": len(policy_list),
        "nine_present": len(nine_present),
        "nine_missing": [pid for pid in NINE if pid not in ids],
    }

    obs_code, obs_dt, obs = _req("GET", f"{api}/observations?latest_only=true", token=tok, timeout=120)
    obs_list = obs if isinstance(obs, list) else (obs.get("items") or obs.get("observations") or []) if isinstance(obs, dict) else []
    out["integration"]["observations_latest"] = {
        "pass": obs_code == 200 and len(obs_list) >= 1,
        "http": obs_code,
        "latency_s": round(obs_dt, 3),
        "count": len(obs_list) if isinstance(obs_list, list) else None,
        "raw_type": type(obs).__name__,
    }

    # Monitoring / dashboard endpoints used by UI
    for path, key in [
        ("/dashboard/executive", "executive"),
        ("/monitoring/policies", "monitoring_policies"),
        ("/policies/verdicts", "verdicts"),
    ]:
        code, dt, payload = _req("GET", f"{api}{path}", token=tok, timeout=120)
        if code == 404:
            # try alternate shapes
            alts = {
                "/dashboard/executive": ["/executive/summary", "/dashboard/summary"],
                "/monitoring/policies": ["/policies/monitoring", "/observations/monitoring"],
                "/policies/verdicts": ["/verdicts", "/policy-verdicts"],
            }
            for alt in alts.get(path, []):
                code, dt, payload = _req("GET", f"{api}{alt}", token=tok, timeout=90)
                if code != 404:
                    path = alt
                    break
        out["integration"][key] = {
            "path_tried": path,
            "http": code,
            "latency_s": round(dt, 3),
            "pass": code == 200,
            "payload_hint": (
                list(payload.keys())[:10]
                if isinstance(payload, dict)
                else (f"list[{len(payload)}]" if isinstance(payload, list) else str(payload)[:100])
            ),
        }

    # Per-policy workspace smoke for MRI
    mri = NINE[0]
    code, dt, payload = _req("GET", f"{api}/policies/{mri}", token=tok, timeout=90)
    out["integration"]["mri_policy_get"] = {
        "pass": code == 200,
        "http": code,
        "latency_s": round(dt, 3),
        "name": (payload.get("name") if isinstance(payload, dict) else None),
    }

    # Performance suite
    paths = ["/policies", f"/policies/{mri}", "/observations?latest_only=true", "/health"]
    # health is root not under api/v1 for staging — handle specially
    for path in paths:
        if path == "/health":
            times = []
            codes = []
            root = api.replace("/api/v1", "")
            for _ in range(7):
                c, d, _b = _http_get(root + "/health")
                times.append(d)
                codes.append(c)
            out["performance"]["/health"] = {
                "ok": all(c == 200 for c in codes),
                "p50_s": round(statistics.median(times), 3),
                "p95_s": round(sorted(times)[max(0, int(0.95 * (len(times) - 1)))], 3),
                "mean_s": round(statistics.mean(times), 3),
                "max_s": round(max(times), 3),
            }
        else:
            out["performance"][path] = bench(api, tok, path, repeats=5)

    return out


def critique(demo: Dict[str, Any], stg: Dict[str, Any]) -> Dict[str, Any]:
    findings: List[Dict[str, str]] = []

    def add(sev: str, area: str, msg: str) -> None:
        findings.append({"severity": sev, "area": area, "finding": msg})

    # Systems
    for label in ("web_root", "api_health", "login"):
        d = demo["systems"].get(label, {})
        s = stg["systems"].get(label, {})
        if d.get("pass") and not s.get("pass"):
            add("CRITICAL", "systems", f"Staging {label} FAIL while demo PASS")
        if s.get("pass") and d.get("pass"):
            if (s.get("latency_s") or 0) > (d.get("latency_s") or 0) * 2 + 0.5:
                add("HIGH", "performance", f"Staging {label} much slower than demo ({s.get('latency_s')}s vs {d.get('latency_s')}s)")

    # Integration parity
    dpol = demo["integration"].get("policies_list", {})
    spol = stg["integration"].get("policies_list", {})
    if (spol.get("nine_present") or 0) < 9:
        add("CRITICAL", "integration", f"Staging missing Dec4 nine policies: {spol.get('nine_missing')}")
    if (spol.get("count") or 0) < (dpol.get("count") or 0) * 0.5 and (dpol.get("count") or 0) > 20:
        add("HIGH", "integration", f"Staging policy catalog far thinner than demo ({spol.get('count')} vs {dpol.get('count')})")

    dobs = demo["integration"].get("observations_latest", {})
    sobs = stg["integration"].get("observations_latest", {})
    if (dobs.get("count") or 0) > 0 and (sobs.get("count") or 0) == 0:
        add("CRITICAL", "integration", "Staging has 0 latest observations — Monitoring/Executive room path broken vs demo")
    if not sobs.get("pass"):
        add("CRITICAL", "integration", f"Staging observations endpoint not usable: {sobs}")

    for key in ("executive", "monitoring_policies", "verdicts", "mri_policy_get"):
        d = demo["integration"].get(key, {})
        s = stg["integration"].get(key, {})
        if d.get("pass") and not s.get("pass"):
            add("HIGH", "integration", f"Staging {key} FAIL (http={s.get('http')}) while demo PASS")
        if not d.get("pass") and not s.get("pass"):
            add("MEDIUM", "integration", f"Both envs fail {key} (route mismatch possible): demo={d.get('http')} stg={s.get('http')}")

    # Perf compare shared paths
    for path, sperf in stg.get("performance", {}).items():
        dperf = demo.get("performance", {}).get(path)
        if not dperf or not sperf:
            continue
        if not sperf.get("ok", sperf.get("ok", True)):
            add("HIGH", "performance", f"Staging perf path not OK: {path}")
            continue
        sp95 = sperf.get("p95_s") or 0
        dp95 = dperf.get("p95_s") or 0
        if dp95 > 0 and sp95 > max(dp95 * 2.5, dp95 + 1.0):
            add("HIGH", "performance", f"Staging p95 {path} {sp95}s vs demo {dp95}s (>2.5x)")
        if sp95 > 5:
            add("HIGH", "performance", f"Staging p95 {path} {sp95}s exceeds 5s UX budget")
        if dp95 > 5:
            add("MEDIUM", "performance", f"Demo p95 {path} {dp95}s also exceeds 5s — neither is production-ready")

    # Architecture honesty
    add(
        "INFO",
        "architecture",
        "Staging is alembic 014 + SB Standard + synthetic seed; demo is frozen 012 App Service. Staging must not claim HA/Premium parity.",
    )

    crit = sum(1 for f in findings if f["severity"] == "CRITICAL")
    high = sum(1 for f in findings if f["severity"] == "HIGH")
    if crit:
        verdict = "FAIL"
    elif high:
        verdict = "PASS_WITH_CRITICAL_GAPS"
    else:
        verdict = "PASS"
    return {"verdict": verdict, "critical_count": crit, "high_count": high, "findings": findings}


def to_md(report: Dict[str, Any]) -> str:
    lines = [
        "# Lean staging vs demo — critical systems / integration / performance test",
        "",
        f"**Generated:** {report['generated_at']}",
        f"**Verdict:** **{report['comparison']['verdict']}** "
        f"({report['comparison']['critical_count']} critical, {report['comparison']['high_count']} high)",
        "",
        "## URLs",
        f"- Demo web: `{DEMO_WEB}`",
        f"- Demo API: `{DEMO_API}`",
        f"- Staging web: `{STG_WEB}`",
        f"- Staging API: `{STG_API}`",
        "",
        "## Ruthless findings",
    ]
    for f in report["comparison"]["findings"]:
        lines.append(f"- **{f['severity']}** [{f['area']}] {f['finding']}")
    lines += ["", "## Systems", "", "| Check | Demo | Staging |", "|---|---|---|"]
    for label in sorted(set(report["demo"]["systems"]) | set(report["staging"]["systems"])):
        d = report["demo"]["systems"].get(label, {})
        s = report["staging"]["systems"].get(label, {})
        lines.append(
            f"| {label} | {'PASS' if d.get('pass') else 'FAIL'} {d.get('latency_s')}s | "
            f"{'PASS' if s.get('pass') else 'FAIL'} {s.get('latency_s')}s |"
        )
    lines += ["", "## Integration", "", "| Check | Demo | Staging |", "|---|---|---|"]
    for label in sorted(set(report["demo"]["integration"]) | set(report["staging"]["integration"])):
        d = report["demo"]["integration"].get(label, {})
        s = report["staging"]["integration"].get(label, {})
        lines.append(
            f"| {label} | {'PASS' if d.get('pass') else 'FAIL'} http={d.get('http')} | "
            f"{'PASS' if s.get('pass') else 'FAIL'} http={s.get('http')} |"
        )
    lines += ["", "## Performance (p50 / p95 seconds)", "", "| Path | Demo p50/p95 | Staging p50/p95 |", "|---|---|---|"]
    for path in sorted(set(report["demo"]["performance"]) | set(report["staging"]["performance"])):
        d = report["demo"]["performance"].get(path, {})
        s = report["staging"]["performance"].get(path, {})
        lines.append(
            f"| `{path}` | {d.get('p50_s')}/{d.get('p95_s')} | {s.get('p50_s')}/{s.get('p95_s')} |"
        )
    lines += [
        "",
        "## Bottom line",
        "",
        "Staging is a second environment for enterprise pathing, **not** a drop-in Dec4 room replacement until "
        "observations/Monitoring/Executive parity and latency budgets clear. Demo remains the frozen customer path.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    demo = env_probe("demo", DEMO_API, DEMO_WEB)
    stg = env_probe("staging", STG_API, STG_WEB)
    comparison = critique(demo, stg)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "demo": demo,
        "staging": stg,
        "comparison": comparison,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    OUT_MD.write_text(to_md(report), encoding="utf-8")
    print(json.dumps({"verdict": comparison["verdict"], "critical": comparison["critical_count"], "high": comparison["high_count"], "md": str(OUT_MD)}, indent=2))


if __name__ == "__main__":
    main()
