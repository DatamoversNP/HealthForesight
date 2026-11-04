#!/usr/bin/env python3
"""
Product-aligned demo seed (CLI):

  1) One GENERAL + one POLICY_SPECIFIC baseline analysis per catalog policy
     Window: 2025-01-01 .. 2025-12-31 (named like the UI)
  2) Generate predicted impact after baselines
  3) One observation daily-job per quarter in 2026 (4 dates)

JWT expires during long runs — re-login on demand (not every poll tick).
Job status polls reuse the token for up to 20 minutes to avoid overloading App Service.

Usage:
  python3 scripts/demo/seed_named_baselines_2025_quarterly_obs.py --phase baselines
  python3 scripts/demo/seed_named_baselines_2025_quarterly_obs.py --phase baselines --skip-existing
  python3 scripts/demo/seed_named_baselines_2025_quarterly_obs.py --limit-policies 5 --phase baselines
  python3 scripts/demo/seed_named_baselines_2025_quarterly_obs.py --phase observations --obs-dates 2026-04-15,2026-07-15,2026-10-15
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "scripts" / "demo" / "catalog" / "bcbs_nc_aligned_policy_catalog.json"

WINDOW_START = "2025-01-01"
WINDOW_END = "2025-12-31"
WINDOW_TAG = f"{WINDOW_START}_{WINDOW_END}"
QUARTERLY_OBS_DATES = ["2026-01-15", "2026-04-15", "2026-07-15", "2026-10-15"]


def http(method: str, url: str, token: str | None = None, body: dict | None = None, timeout: int = 300):
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        return e.code, parsed
    except Exception as e:
        return 0, str(e)


class AuthSession:
    """Login with retries; optional per-request refresh (avoid during status polls)."""

    def __init__(self, api: str, email: str, password: str):
        self.api = api
        self.email = email
        self.password = password
        self.token = ""
        self.refresh()

    def refresh(self, attempts: int = 8) -> str:
        last: object = None
        for i in range(attempts):
            code, data = http(
                "POST",
                f"{self.api}/auth/login",
                body={"email": self.email, "password": self.password},
                timeout=90,
            )
            if code == 200 and isinstance(data, dict) and data.get("access_token"):
                self.token = data["access_token"]
                print(f"  (token refreshed {datetime.utcnow().strftime('%H:%M:%S')}Z)", flush=True)
                return self.token
            last = (code, data)
            wait = min(60, 5 * (i + 1))
            print(f"  login retry {i+1}/{attempts} -> {code}; sleep {wait}s", flush=True)
            time.sleep(wait)
        raise SystemExit(f"Login failed after {attempts} tries: {last}")

    def request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        timeout: int = 300,
        *,
        refresh: bool = True,
    ):
        url = path if path.startswith("http") else f"{self.api}{path}"
        last_code, last_data = 0, None
        for attempt in range(4):
            if refresh or not self.token:
                try:
                    self.refresh()
                except SystemExit:
                    if attempt == 3:
                        raise
                    time.sleep(20)
                    continue
            code, data = http(method, url, token=self.token, body=body, timeout=timeout)
            last_code, last_data = code, data
            # Success or hard client/server business error — don't retry forever
            if code in (200, 201, 202, 400, 404, 422):
                return code, data
            if code == 401:
                print("  401 — re-login and retry…", flush=True)
                refresh = True
                continue
            # 0 = connection reset/timeout; 502/503/504 = gateway overload
            if code in (0, 502, 503, 504) or code >= 500:
                wait = min(90, 15 * (attempt + 1))
                print(
                    f"  transient {code} attempt {attempt+1}/4; sleep {wait}s — {str(data)[:100]}",
                    flush=True,
                )
                time.sleep(wait)
                continue
            return code, data
        return last_code, last_data


def wait_ping(api: str, tries: int = 18) -> None:
    for i in range(tries):
        code, data = http("GET", f"{api}/ping", timeout=20)
        if code == 200:
            print(f"API ok: {data}", flush=True)
            return
        print(f"  ping {i+1}/{tries} -> {code} {str(data)[:80]}", flush=True)
        time.sleep(10)
    raise SystemExit("API not healthy. Restart App Service first.")


def catalog_targets(session: AuthSession, limit: int = 0) -> list[dict]:
    catalog = json.loads(CATALOG.read_text())
    names = {p["name"].strip() for p in catalog["policies"]}
    code, data = session.request("GET", "/policies?limit=500", timeout=180)
    if code != 200:
        raise SystemExit(f"List policies failed: {code} {data}")
    live = data if isinstance(data, list) else (data or {}).get("items") or []
    by_name: dict[str, dict] = {}
    for p in live:
        n = (p.get("name") or "").strip()
        if n not in names or p.get("status") == "RETIRED":
            continue
        prev = by_name.get(n)
        if not prev or (p.get("status") == "ACTIVE" and prev.get("status") != "ACTIVE"):
            by_name[n] = p
    targets = list(by_name.values())
    if limit:
        targets = targets[:limit]
    print(f"Catalog matched: {len(targets)} / {len(names)}", flush=True)
    return targets


def existing_baseline_analysis_names(session: AuthSession) -> set[str]:
    """Names of BASELINE analyses already created for this window tag."""
    code, data = session.request("GET", "/analyses?limit=500&analysis_type=BASELINE", timeout=180)
    if code != 200:
        # fallback without filter
        code, data = session.request("GET", "/analyses?limit=500", timeout=180)
    items = data if isinstance(data, list) else (data or {}).get("items") or []
    names = set()
    for a in items:
        if (a.get("analysis_type") or "").upper() not in ("BASELINE", ""):
            # if filter unsupported, keep all that look like ours
            pass
        n = a.get("name") or ""
        if WINDOW_TAG in n or (WINDOW_START in n and WINDOW_END in n):
            names.add(n)
        # also match policy label prefix for skip-existing by policy name
        if " Baseline " in n:
            names.add(n)
    return names


def policies_already_done(session: AuthSession, targets: list[dict]) -> set[str]:
    """Return set of policy ids that already have a named baseline analysis for this window."""
    code, data = session.request("GET", "/analyses?limit=500", timeout=180)
    items = data if isinstance(data, list) else (data or {}).get("items") or []
    done_ids: set[str] = set()
    done_names: set[str] = set()
    for a in items:
        n = a.get("name") or ""
        if WINDOW_TAG not in n and not (WINDOW_START in n and WINDOW_END in n):
            continue
        if a.get("policy_id"):
            done_ids.add(str(a["policy_id"]))
        # parse "Name Baseline 2025-01-01_2025-12-31 ..."
        if " Baseline " in n:
            done_names.add(n.split(" Baseline ")[0].strip())
    id_by_name = {(p.get("name") or "")[:50]: str(p["id"]) for p in targets}
    for label, pid in id_by_name.items():
        if label in done_names:
            done_ids.add(pid)
    return done_ids


def create_baseline(session: AuthSession, *, name: str, baseline_type: str, policy_id: str | None) -> dict:
    body = {
        "name": name,
        "baseline_type": baseline_type,
        "start_date": WINDOW_START,
        "end_date": WINDOW_END,
        "n_clusters": 5,
    }
    if policy_id:
        body["policy_id"] = policy_id
    t0 = time.time()
    code, data = session.request("POST", "/analyses/baseline", body=body, timeout=900)
    return {
        "name": name,
        "http": code,
        "ok": code in (200, 201) and isinstance(data, dict) and bool(data.get("id")),
        "id": (data or {}).get("id") if isinstance(data, dict) else None,
        "elapsed_s": round(time.time() - t0, 1),
        "error": None if code in (200, 201) else data,
    }


def phase_baselines(session: AuthSession, targets: list[dict], skip_existing: bool) -> None:
    print("\n=== Named baselines (UI-style analyses) ===", flush=True)
    print(f"  Window: {WINDOW_START} .. {WINDOW_END}", flush=True)
    suffix = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    already = policies_already_done(session, targets) if skip_existing else set()
    if skip_existing:
        print(f"  skip-existing: {len(already)} policies already have a {WINDOW_TAG} analysis", flush=True)

    gen_name = f"General Baseline {WINDOW_TAG} {suffix}"
    # skip general if any general for this window exists
    if skip_existing and any("General Baseline" in n and WINDOW_TAG in n for n in existing_baseline_analysis_names(session)):
        print("  GENERAL skipped (already exists for window)", flush=True)
    else:
        gen = create_baseline(session, name=gen_name, baseline_type="GENERAL", policy_id=None)
        print(f"  GENERAL -> http={gen['http']} ok={gen['ok']} {gen['elapsed_s']}s", flush=True)

    ok = fail = skipped = 0
    t0 = time.time()
    for i, p in enumerate(targets, 1):
        pid = str(p["id"])
        label = (p.get("name") or pid)[:50]
        if skip_existing and pid in already:
            skipped += 1
            if i % 25 == 0 or i == len(targets):
                print(
                    f"  … {i}/{len(targets)} ok={ok} fail={fail} skip={skipped} elapsed={(time.time()-t0)/60:.1f}m",
                    flush=True,
                )
            continue
        name = f"{label} Baseline {WINDOW_TAG} {suffix}"
        row = create_baseline(session, name=name, baseline_type="POLICY_SPECIFIC", policy_id=pid)
        # One more full retry on connection/gateway failure
        if not row["ok"] and row["http"] in (0, 502, 503, 504):
            print(f"  retry once after transient {row['http']} for {label}…", flush=True)
            time.sleep(30)
            row = create_baseline(session, name=name, baseline_type="POLICY_SPECIFIC", policy_id=pid)
        if row["ok"]:
            ok += 1
            print(f"  OK [{i}/{len(targets)}] {label} ({row['elapsed_s']}s)", flush=True)
        else:
            fail += 1
            print(f"  FAIL [{i}/{len(targets)}] {label}: {row['http']} {str(row.get('error'))[:160]}", flush=True)
        time.sleep(2)
    print(f"Baselines done. ok={ok} fail={fail} skipped={skipped} (+ general)", flush=True)


def phase_predicted(session: AuthSession) -> None:
    print("\n=== Predicted impact (force regenerate) ===", flush=True)
    t0 = time.time()
    code, data = session.request(
        "POST", "/policies/generate-predicted-impact?force=true", body={}, timeout=2400
    )
    print(f"  -> {code} in {(time.time()-t0)/60:.1f}m", flush=True)
    if isinstance(data, dict):
        print(
            f"  total={data.get('total_policies')} generated={data.get('generated')} "
            f"skipped={data.get('skipped')} errors={data.get('errors')}",
            flush=True,
        )
    else:
        print(f"  body: {str(data)[:300]}", flush=True)


def wait_job(session: AuthSession, job_id: str, timeout_s: int = 7200) -> dict | None:
    """Poll status without re-login every tick (that overloads App Service during long jobs).

    Never raises on login failure during poll — the job may still finish server-side.
    """
    t0 = time.time()
    last = ""
    last_refresh = 0.0
    while time.time() - t0 < timeout_s:
        # Refresh token at most every 20 minutes during long observation jobs
        need_refresh = (time.time() - last_refresh) > 20 * 60 or not session.token
        try:
            code, data = session.request(
                "GET",
                f"/jobs/daily-data-and-observations/status/{job_id}",
                timeout=45,
                refresh=need_refresh,
            )
        except SystemExit as e:
            print(f"    … login unavailable during poll ({e}); sleep 120s — job may still run", flush=True)
            time.sleep(120)
            continue
        if need_refresh and code in (200, 201):
            last_refresh = time.time()
        if code == 200 and isinstance(data, dict):
            st = (data.get("status") or "").upper()
            msg = str(data.get("message") or "")[:120]
            if msg != last:
                print(f"    … {st}: {msg}", flush=True)
                last = msg
            if st in ("COMPLETED", "FAILED", "CANCELLED"):
                return data
        elif code == 0:
            print(f"    … poll soft-fail: {str(data)[:80]}", flush=True)
            time.sleep(60)
            continue
        time.sleep(45)
    return None


def observation_end_counts(session: AuthSession) -> dict[str, int]:
    """API caps limit at 500; page if needed. Prefer latest_only for skip checks."""
    counts: dict[str, int] = {}
    # latest_only keeps response small and is enough to know which quarter ends exist
    code, data = session.request(
        "GET", "/observations?latest_only=true&limit=500", timeout=180, refresh=True
    )
    if code != 200 or not isinstance(data, list):
        print(f"  warn: could not list observations ({code}) {str(data)[:120]}", flush=True)
        return counts
    for o in data:
        end = str(o.get("observation_period_end") or "")[:10]
        if end:
            counts[end] = counts.get(end, 0) + 1
    return counts


def phase_observations(session: AuthSession, dates: list[str], *, skip_existing: bool) -> None:
    print("\n=== Quarterly observations (one job per quarter) ===", flush=True)
    print(f"  Dates: {dates}", flush=True)
    existing = observation_end_counts(session) if skip_existing else {}
    if skip_existing:
        print(f"  existing ends: {dict(sorted(existing.items()))}", flush=True)
    for d in dates:
        print(f"\n  target_date={d}", flush=True)
        if skip_existing and existing.get(d, 0) >= 200:
            print(f"    skip — already have {existing[d]} observations ending {d}", flush=True)
            continue
        # Cool-down so App Service can breathe between heavy quarter jobs
        code, data = session.request(
            "POST",
            f"/jobs/daily-data-and-observations?target_date={d}&run_observations=true",
            body={},
            timeout=120,
        )
        print(f"    enqueue -> {code} {str(data)[:180]}", flush=True)
        if code not in (200, 202) or not isinstance(data, dict):
            print("    enqueue failed — waiting 3m then stop further quarters", flush=True)
            time.sleep(180)
            break
        job_id = data.get("job_id") or data.get("id")
        if not job_id:
            continue
        result = wait_job(session, job_id, timeout_s=9000)
        if result:
            print(f"    finished: {result.get('status')} {str(result.get('message') or '')[:140]}", flush=True)
            if (result.get("status") or "").upper() != "COMPLETED":
                print("    non-COMPLETED — stop further quarters", flush=True)
                break
        else:
            print("    still running after wait — stop further quarters", flush=True)
            break
        print("    cool-down 90s before next quarter…", flush=True)
        time.sleep(90)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=os.getenv("DEMO_API_URL", "https://healthforesight-api.azurewebsites.net/api/v1"))
    ap.add_argument("--email", default=os.getenv("DEMO_EMAIL", "demo@example.com"))
    ap.add_argument("--password", default=os.getenv("DEMO_PASSWORD", "Swan@1234"))
    ap.add_argument("--phase", default="baselines,predicted,observations")
    ap.add_argument("--limit-policies", type=int, default=0)
    ap.add_argument(
        "--skip-existing",
        action="store_true",
        help=f"Skip policies that already have a Baseline analysis for {WINDOW_TAG}; also skip obs dates with ≥200 rows",
    )
    ap.add_argument(
        "--obs-dates",
        default="",
        help="Comma-separated observation target dates (default: all quarterly dates)",
    )
    args = ap.parse_args()
    phases = {p.strip() for p in args.phase.split(",") if p.strip()}
    obs_dates = (
        [d.strip() for d in args.obs_dates.split(",") if d.strip()]
        if args.obs_dates.strip()
        else list(QUARTERLY_OBS_DATES)
    )

    print("=" * 72, flush=True)
    print("Named baselines 2025 + predicted + quarterly 2026 observations", flush=True)
    print(f"  API: {args.api}", flush=True)
    print(f"  Window: {WINDOW_START} .. {WINDOW_END}", flush=True)
    print(f"  Quarters: {obs_dates}", flush=True)
    print(f"  Phases: {sorted(phases)}", flush=True)
    print("=" * 72, flush=True)

    wait_ping(args.api)
    session = AuthSession(args.api, args.email, args.password)
    targets = catalog_targets(session, args.limit_policies)
    if not targets and "baselines" in phases:
        raise SystemExit("No catalog policies matched.")

    if "baselines" in phases:
        phase_baselines(session, targets, skip_existing=args.skip_existing)

    if "predicted" in phases:
        phase_predicted(session)

    if "observations" in phases:
        phase_observations(session, obs_dates, skip_existing=args.skip_existing)

    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
