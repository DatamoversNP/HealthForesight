#!/usr/bin/env python3
"""
Baseline through Dec 31 2025 + 2026 YTD monthly observations for the catalog portfolio.

Timeline (demo narrative):
  - Policies effective 2026-01-01
  - Pre-policy baseline window uses claims through 2025-12-31
  - 2026-01-01 .. today: monthly claim points + daily-job observation analyses

Phases:
  1) Set catalog policies effective_period.start = 2026-01-01
  2) Generate policy-scoped claims on monthly mid-month dates in 2025 (baseline era)
  3) Generate policy-scoped claims on monthly mid-month dates in 2026 YTD (observation era)
  4) Refresh-all baselines (requires API with DEMO_DATA_END=2025-12-31)
  5) Trigger daily-data-and-observations for each 2026 month-end (or mid-month)

Usage:
  python3 scripts/demo/seed_baseline_2025_obs_2026.py
  python3 scripts/demo/seed_baseline_2025_obs_2026.py --phase effective,claims-2025
  python3 scripts/demo/seed_baseline_2025_obs_2026.py --phase claims-2026,baselines,observations
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "scripts" / "demo" / "catalog" / "bcbs_nc_aligned_policy_catalog.json"
LOG = Path("/tmp/seed_baseline_2025_obs_2026.jsonl")

EFFECTIVE_START = "2026-01-01"
EFFECTIVE_PERIOD = {"start_date": EFFECTIVE_START, "end_date": None}
TODAY = date.today()

# Mid-month anchors keep volume manageable while covering the full eras.
BASELINE_DATES = [f"2025-{m:02d}-15" for m in range(1, 13)]  # through Dec 31 era
# Quarterly + latest (monthly × 244 daily-jobs is too heavy on Azure BackgroundTasks)
_OBS_CANDIDATES = ["2026-01-15", "2026-04-15", "2026-07-15", "2026-10-15"]
OBS_DATES = [d for d in _OBS_CANDIDATES if date.fromisoformat(d) <= TODAY]
if TODAY.year == 2026:
    latest = TODAY.isoformat()
    if latest not in OBS_DATES and TODAY.month >= 10:
        OBS_DATES.append(latest)


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


def login(api: str, email: str, password: str) -> str:
    code, data = http("POST", f"{api}/auth/login", body={"email": email, "password": password})
    if code != 200 or not isinstance(data, dict) or not data.get("access_token"):
        raise SystemExit(f"Login failed ({code}): {data}")
    return data["access_token"]


def list_policies(api: str, token: str) -> list[dict]:
    code, data = http("GET", f"{api}/policies?limit=500", token=token, timeout=180)
    if code != 200:
        raise SystemExit(f"List policies failed: {code} {data}")
    return data if isinstance(data, list) else (data or {}).get("items") or []


def catalog_targets(api: str, token: str, limit: int = 0) -> list[dict]:
    catalog = json.loads(CATALOG.read_text())
    catalog_names = {p["name"].strip() for p in catalog["policies"]}
    live = list_policies(api, token)
    by_name: dict[str, dict] = {}
    for p in live:
        n = (p.get("name") or "").strip()
        if n not in catalog_names:
            continue
        if p.get("status") == "RETIRED":
            continue
        prev = by_name.get(n)
        if not prev or (p.get("status") == "ACTIVE" and prev.get("status") != "ACTIVE"):
            by_name[n] = p
    targets = list(by_name.values())
    if limit:
        targets = targets[:limit]
    print(f"Catalog matched: {len(targets)} / {len(catalog_names)}", flush=True)
    return targets


def set_effective_dates(api: str, token: str, targets: list[dict]) -> None:
    # Prefer bulk endpoint (requires API with force_effective_start support)
    code, data = http(
        "POST",
        f"{api}/policies/complete-configurations?force_effective_start={EFFECTIVE_START}",
        token=token,
        body={},
        timeout=600,
    )
    if code == 200 and isinstance(data, dict) and data.get("forced_effective"):
        print(
            f"Bulk effective via complete-configurations: forced={data.get('forced_effective')} "
            f"updated={data.get('updated')} skipped={data.get('skipped')}",
            flush=True,
        )
        return
    print(
        f"Bulk force_effective_start unavailable ({code}); falling back to per-policy PUT "
        f"(needs API PUT JSONB fix). detail={str(data)[:160]}",
        flush=True,
    )

    ok = fail = 0
    for i, p in enumerate(targets, 1):
        pid = p["id"]
        # PUT uses PolicyCreate — send required fields + preserve scope/levers when present
        body: dict = {
            "name": p.get("name") or "Unnamed",
            "policy_type": p.get("policy_type") or "PRIOR_AUTH",
            "owner_role": p.get("owner_role"),
            "description": p.get("description"),
            "status": p.get("status") or "ACTIVE",
            "effective_period": EFFECTIVE_PERIOD,
        }
        for key in ("scope", "enforcement", "policy_levers", "expected_behavioral_response", "analytics_expectations", "ui_hints", "policy_logic"):
            if p.get(key) is not None:
                body[key] = p[key]
        code, data = http("PUT", f"{api}/policies/{pid}", token=token, body=body, timeout=120)
        if code in (200, 201):
            # Verify persistence (live API historically ignored in-place JSONB mutates)
            _, got = http("GET", f"{api}/policies/{pid}", token=token, timeout=60)
            ep = (got or {}).get("effective_period") if isinstance(got, dict) else None
            start = (ep or {}).get("start_date") if isinstance(ep, dict) else None
            if start and str(start).startswith(EFFECTIVE_START):
                ok += 1
            else:
                fail += 1
                if fail <= 5:
                    print(f"  PUT ok but effective not persisted for {p.get('name')}: {ep}", flush=True)
        else:
            fail += 1
            if fail <= 10:
                print(f"  FAIL effective {p.get('name')}: {code} {str(data)[:200]}", flush=True)
        if i % 50 == 0 or i == len(targets):
            print(f"  effective put {i}/{len(targets)} ok={ok} fail={fail}", flush=True)
    print(f"Effective dates -> {EFFECTIVE_START}: ok={ok} fail={fail}", flush=True)


def generate_one(api: str, token: str, policy_id: str, target_date: str, member_count: int, cpm: float):
    url = f"{api}/data/generate-claims/policy-scoped?policy_id={policy_id}"
    body = {"target_date": target_date, "member_count": member_count, "claims_per_member": cpm}
    t0 = time.time()
    code, data = http("POST", url, token=token, body=body, timeout=300)
    return {
        "policy_id": policy_id,
        "date": target_date,
        "http": code,
        "elapsed_s": round(time.time() - t0, 2),
        "claims_loaded": (data or {}).get("claims_loaded") if isinstance(data, dict) else None,
        "success": code in (200, 201) and isinstance(data, dict) and data.get("success"),
        "error": None if code in (200, 201) else data,
    }


def generate_claims(
    api: str,
    token: str,
    targets: list[dict],
    dates: list[str],
    workers: int,
    member_count: int,
    cpm: float,
    label: str,
) -> None:
    jobs = [(p["id"], p.get("name"), d) for p in targets for d in dates]
    print(f"\n=== Claims ({label}): {len(targets)} policies × {len(dates)} dates = {len(jobs)} jobs ===", flush=True)
    print(f"  Dates: {dates}", flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    ok = fail = loaded = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {
            ex.submit(generate_one, api, token, pid, d, member_count, cpm): (name, d)
            for pid, name, d in jobs
        }
        done = 0
        for fut in as_completed(futs):
            name, d = futs[fut]
            try:
                row = fut.result()
            except Exception as e:
                row = {"success": False, "error": str(e), "date": d, "policy_name": name}
            row["policy_name"] = name
            row["phase"] = label
            with LOG.open("a") as f:
                f.write(json.dumps(row, default=str) + "\n")
            done += 1
            if row.get("success"):
                ok += 1
                loaded += int(row.get("claims_loaded") or 0)
            else:
                fail += 1
                if fail <= 12:
                    print(f"  FAIL {name} @ {d}: {row.get('http')} {str(row.get('error'))[:140]}", flush=True)
            if done % 50 == 0 or done == len(jobs):
                elapsed = time.time() - t0
                rate = done / elapsed if elapsed else 0
                eta = (len(jobs) - done) / rate if rate else 0
                print(
                    f"  … {done}/{len(jobs)} ok={ok} fail={fail} claims={loaded:,} "
                    f"elapsed={elapsed/60:.1f}m eta={eta/60:.1f}m",
                    flush=True,
                )
    print(f"Claims ({label}) done. ok={ok} fail={fail} claims_loaded={loaded:,}", flush=True)


def refresh_baselines(api: str, token: str, targets: list[dict]) -> None:
    print("\n=== Refresh baselines (ROLLING 12m) ===", flush=True)
    t0 = time.time()
    code, data = http(
        "POST",
        f"{api}/baselines/refresh-all?baseline_type=ROLLING&window_months=12",
        token=token,
        body={},
        timeout=1200,
    )
    print(f"refresh-all -> {code} in {time.time()-t0:.1f}s", flush=True)
    Path("/tmp/seed_baselines_refresh.json").write_text(json.dumps(data, indent=2, default=str))
    if isinstance(data, dict):
        print(
            f"  policy_baselines={len(data.get('policy_baselines') or [])} "
            f"errors={len(data.get('errors') or [])} general={bool(data.get('general_baseline'))}",
            flush=True,
        )
        errs = data.get("errors") or []
        if errs[:5]:
            print("  sample errors:", errs[:5], flush=True)

    code, bals = http("GET", f"{api}/baselines", token=token, timeout=180)
    if code == 200 and isinstance(bals, list):
        with_pid = {str(b.get("policy_id")) for b in bals if b.get("policy_id")}
        target_ids = {str(p["id"]) for p in targets}
        print(
            f"  Coverage: {len(with_pid & target_ids)}/{len(target_ids)} catalog policies have baseline rows",
            flush=True,
        )


def wait_job(api: str, token: str, job_id: str, timeout_s: int = 180) -> dict | None:
    """Poll briefly; daily jobs over large portfolios can run long in Azure BackgroundTasks."""
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        code, data = http(
            "GET",
            f"{api}/jobs/daily-data-and-observations/status/{job_id}",
            token=token,
            timeout=60,
        )
        if code == 200 and isinstance(data, dict):
            st = (data.get("status") or "").upper()
            if st in ("COMPLETED", "FAILED", "CANCELLED"):
                return data
        time.sleep(10)
    return None


def run_observations(api: str, token: str, dates: list[str]) -> None:
    print("\n=== Observation analyses (daily job per interval) ===", flush=True)
    print(f"  Target dates: {dates}", flush=True)
    for d in dates:
        print(f"\n  Daily job target_date={d} …", flush=True)
        code, data = http(
            "POST",
            f"{api}/jobs/daily-data-and-observations?target_date={d}&run_observations=true",
            token=token,
            body={},
            timeout=120,
        )
        print(f"    enqueue -> {code} {str(data)[:200]}", flush=True)
        if code not in (200, 202) or not isinstance(data, dict):
            continue
        job_id = data.get("job_id") or data.get("id")
        if not job_id:
            continue
        result = wait_job(api, token, job_id)
        if result:
            print(
                f"    job {job_id}: status={result.get('status')} msg={str(result.get('message') or '')[:180]}",
                flush=True,
            )
        else:
            print(f"    job {job_id}: still running after wait window", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=os.getenv("DEMO_API_URL", "https://data-voyager.vercel.app/api/v1"))
    ap.add_argument("--email", default=os.getenv("DEMO_EMAIL", "demo@example.com"))
    ap.add_argument("--password", default=os.getenv("DEMO_PASSWORD", "Swan@1234"))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--member-count", type=int, default=160)
    ap.add_argument("--claims-per-member", type=float, default=2.0)
    ap.add_argument("--limit-policies", type=int, default=0)
    ap.add_argument(
        "--phase",
        default="effective,claims-2025,claims-2026,baselines,observations",
        help="Comma list: effective,claims-2025,claims-2026,baselines,observations",
    )
    args = ap.parse_args()
    phases = {p.strip() for p in args.phase.split(",") if p.strip()}

    print("=" * 72, flush=True)
    print("Baseline ≤2025-12-31  |  Observations 2026 YTD monthly", flush=True)
    print(f"  API: {args.api}", flush=True)
    print(f"  Effective: {EFFECTIVE_START}", flush=True)
    print(f"  Baseline dates ({len(BASELINE_DATES)}): {BASELINE_DATES}", flush=True)
    print(f"  Obs dates ({len(OBS_DATES)}): {OBS_DATES}", flush=True)
    print(f"  Phases: {sorted(phases)}", flush=True)
    print("=" * 72, flush=True)

    token = login(args.api, args.email, args.password)
    targets = catalog_targets(args.api, token, args.limit_policies)
    if not targets:
        raise SystemExit("No catalog policies matched on site.")

    LOG.write_text("")

    if "effective" in phases:
        print("\n=== Set effective dates ===", flush=True)
        set_effective_dates(args.api, token, targets)
        token = login(args.api, args.email, args.password)

    if "claims-2025" in phases:
        generate_claims(
            args.api, token, targets, BASELINE_DATES, args.workers, args.member_count, args.claims_per_member, "2025-baseline"
        )
        token = login(args.api, args.email, args.password)

    if "claims-2026" in phases:
        generate_claims(
            args.api, token, targets, OBS_DATES, args.workers, args.member_count, args.claims_per_member, "2026-obs"
        )
        token = login(args.api, args.email, args.password)

    if "baselines" in phases:
        refresh_baselines(args.api, token, targets)
        token = login(args.api, args.email, args.password)

    if "observations" in phases:
        run_observations(args.api, token, OBS_DATES)

    print("\nDone.", flush=True)
    print(
        "Note: baselines need API DEMO_DATA_END=2025-12-31 deployed. "
        "If coverage is low, rebuild/redeploy API then re-run --phase baselines,observations.",
        flush=True,
    )


if __name__ == "__main__":
    main()
