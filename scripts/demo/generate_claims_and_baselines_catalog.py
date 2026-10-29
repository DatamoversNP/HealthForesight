#!/usr/bin/env python3
"""
Generate policy-scoped claims for the Blues/NC-aligned catalog, then refresh baselines.

Designed for meaningful rolling baselines without 365-day explosion:
  - 6 service dates across the last ~14 months
  - modest member_count / claims_per_member per date
  - concurrent workers

Usage:
  python3 scripts/demo/generate_claims_and_baselines_catalog.py
  python3 scripts/demo/generate_claims_and_baselines_catalog.py --workers 4 --member-count 180
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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "scripts" / "demo" / "catalog" / "bcbs_nc_aligned_policy_catalog.json"
LOG = Path("/tmp/catalog_claims_baseline_run.jsonl")

# Dates inside typical demo claims window / rolling baseline
DEFAULT_DATES = [
    "2025-04-15",
    "2025-07-15",
    "2025-10-15",
    "2026-01-15",
    "2026-04-15",
    "2026-07-15",
]


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
    code, data = http("GET", f"{api}/policies?limit=500", token=token, timeout=120)
    if code != 200:
        raise SystemExit(f"List policies failed: {code} {data}")
    return data if isinstance(data, list) else (data or {}).get("items") or []


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=os.getenv("DEMO_API_URL", "https://data-voyager.vercel.app/api/v1"))
    ap.add_argument("--email", default=os.getenv("DEMO_EMAIL", "demo@example.com"))
    ap.add_argument("--password", default=os.getenv("DEMO_PASSWORD", "Swan@1234"))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--member-count", type=int, default=180)
    ap.add_argument("--claims-per-member", type=float, default=2.0)
    ap.add_argument("--limit-policies", type=int, default=0, help="0=all catalog policies")
    ap.add_argument("--skip-claims", action="store_true")
    ap.add_argument("--skip-baselines", action="store_true")
    args = ap.parse_args()

    catalog = json.loads(CATALOG.read_text())
    catalog_names = {p["name"].strip() for p in catalog["policies"]}
    print(f"Catalog size: {len(catalog_names)}", flush=True)

    token = login(args.api, args.email, args.password)
    live = list_policies(args.api, token)
    # Map catalog names -> ids (prefer ACTIVE)
    by_name: dict[str, dict] = {}
    for p in live:
        n = (p.get("name") or "").strip()
        if n not in catalog_names:
            continue
        prev = by_name.get(n)
        if not prev or (p.get("status") == "ACTIVE" and prev.get("status") != "ACTIVE"):
            by_name[n] = p

    missing = sorted(catalog_names - set(by_name))
    print(f"Matched on site: {len(by_name)}  missing: {len(missing)}", flush=True)
    if missing[:5]:
        print(" missing sample:", missing[:5], flush=True)

    targets = list(by_name.values())
    if args.limit_policies:
        targets = targets[: args.limit_policies]
    print(f"Will process {len(targets)} policies × {len(DEFAULT_DATES)} dates", flush=True)

    LOG.write_text("")
    claims_ok = claims_fail = claims_loaded = 0

    if not args.skip_claims:
        jobs = []
        for p in targets:
            for d in DEFAULT_DATES:
                jobs.append((p["id"], p.get("name"), d))

        print(f"Submitting {len(jobs)} generation jobs with {args.workers} workers…", flush=True)
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {
                ex.submit(
                    generate_one,
                    args.api,
                    token,
                    pid,
                    d,
                    args.member_count,
                    args.claims_per_member,
                ): (name, d)
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
                with LOG.open("a") as f:
                    f.write(json.dumps(row, default=str) + "\n")
                done += 1
                if row.get("success"):
                    claims_ok += 1
                    claims_loaded += int(row.get("claims_loaded") or 0)
                else:
                    claims_fail += 1
                    if claims_fail <= 15:
                        print(f"FAIL {name} @ {d}: {row.get('http')} {str(row.get('error'))[:160]}", flush=True)
                if done % 25 == 0 or done == len(jobs):
                    elapsed = time.time() - t0
                    rate = done / elapsed if elapsed else 0
                    eta = (len(jobs) - done) / rate if rate else 0
                    print(
                        f"… {done}/{len(jobs)} ok={claims_ok} fail={claims_fail} "
                        f"claims={claims_loaded:,} elapsed={elapsed/60:.1f}m eta={eta/60:.1f}m",
                        flush=True,
                    )
        print(
            f"Claims phase done. ok={claims_ok} fail={claims_fail} claims_loaded={claims_loaded:,}",
            flush=True,
        )

    if not args.skip_baselines:
        print("Refreshing baselines (refresh-all)…", flush=True)
        # re-login in case token aged
        token = login(args.api, args.email, args.password)
        t0 = time.time()
        code, data = http(
            "POST",
            f"{args.api}/baselines/refresh-all?baseline_type=ROLLING&window_months=12",
            token=token,
            body={},
            timeout=900,
        )
        print(f"baselines/refresh-all -> {code} in {time.time()-t0:.1f}s", flush=True)
        out = Path("/tmp/catalog_baselines_refresh.json")
        out.write_text(json.dumps(data, indent=2, default=str))
        if isinstance(data, dict):
            print(
                f"policy_baselines={len(data.get('policy_baselines') or [])} "
                f"errors={len(data.get('errors') or [])} general={bool(data.get('general_baseline'))}",
                flush=True,
            )

        # Coverage check: baselines with policy_id
        code, bals = http("GET", f"{args.api}/baselines", token=token, timeout=180)
        if code == 200 and isinstance(bals, list):
            with_pid = {str(b.get("policy_id")) for b in bals if b.get("policy_id")}
            target_ids = {str(p["id"]) for p in targets}
            print(
                f"Baseline coverage: {len(with_pid & target_ids)}/{len(target_ids)} catalog policies have a baseline row",
                flush=True,
            )


if __name__ == "__main__":
    main()
