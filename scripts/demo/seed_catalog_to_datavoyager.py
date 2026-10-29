#!/usr/bin/env python3
"""
Upsert the BCBS-NC-aligned illustrative catalog into Data Voyager (or any API base).

Usage:
  export DEMO_API_URL=https://data-voyager.vercel.app/api/v1
  export DEMO_EMAIL=demo@example.com
  export DEMO_PASSWORD='...'
  python3 scripts/demo/build_bcbs_nc_aligned_catalog.py
  python3 scripts/demo/seed_catalog_to_datavoyager.py
  python3 scripts/demo/seed_catalog_to_datavoyager.py --baselines
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "scripts" / "demo" / "catalog" / "bcbs_nc_aligned_policy_catalog.json"


def req(method: str, url: str, token: str | None = None, body: dict | None = None, timeout: int = 120):
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(err)
        except Exception:
            parsed = err
        return e.code, parsed


def login(api: str, email: str, password: str) -> str:
    code, data = req("POST", f"{api}/auth/login", body={"email": email, "password": password})
    if code != 200 or not isinstance(data, dict) or not data.get("access_token"):
        raise SystemExit(f"Login failed ({code}): {data}")
    return data["access_token"]


def existing_by_name(api: str, token: str) -> dict[str, dict]:
    code, data = req("GET", f"{api}/policies?limit=500", token=token)
    if code != 200:
        raise SystemExit(f"List policies failed ({code}): {data}")
    items = data if isinstance(data, list) else (data or {}).get("items") or []
    return {(p.get("name") or "").strip(): p for p in items}


def create_payload(p: dict) -> dict:
    return {
        "name": p["name"],
        "policy_type": p["policy_type"],
        "owner_role": p.get("owner_role") or "UM_LEADER",
        "description": p["description"],
        "status": "ACTIVE",
        "scope": {
            "lob": p.get("lobs") or ["COMMERCIAL"],
            "markets": p.get("markets") or ["NC"],
            "states": ["NC"],
        },
        "effective_period": {
            "start_date": "2024-01-01T00:00:00",
            "end_date": None,
        },
        "ui_hints": {
            "domain": p.get("domain"),
            "subdomain": p.get("subdomain"),
            "illustrative_standards_aligned": True,
            "not_verbatim_bcbsnc_policy": True,
            "catalog_version": "2026.10.29",
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=os.getenv("DEMO_API_URL", "https://data-voyager.vercel.app/api/v1"))
    ap.add_argument("--email", default=os.getenv("DEMO_EMAIL", "demo@example.com"))
    ap.add_argument("--password", default=os.getenv("DEMO_PASSWORD", "Swan@1234"))
    ap.add_argument("--baselines", action="store_true", help="Call /baselines/refresh-all after seed")
    ap.add_argument("--limit", type=int, default=0, help="Seed only first N new policies (0=all)")
    args = ap.parse_args()

    if not CATALOG.exists():
        raise SystemExit(f"Missing catalog {CATALOG}; run build_bcbs_nc_aligned_catalog.py first")

    catalog = json.loads(CATALOG.read_text())
    policies = catalog["policies"]
    print(f"Catalog policies: {len(policies)}")
    print(f"Accuracy: {catalog['accuracy_contract']['claim']}")

    token = login(args.api, args.email, args.password)
    existing = existing_by_name(args.api, token)
    print(f"Existing on site: {len(existing)}")

    created = updated = skipped = failed = 0
    failures = []
    to_process = policies
    if args.limit and args.limit > 0:
        # Prefer creating missing ones first
        missing = [p for p in policies if p["name"].strip() not in existing]
        to_process = missing[: args.limit]
        print(f"Limiting to {len(to_process)} missing policies")

    for i, p in enumerate(to_process, 1):
        name = p["name"].strip()
        if name in existing:
            # Already present — count as skipped (do not duplicate)
            skipped += 1
            if i % 25 == 0:
                print(f"… {i}/{len(to_process)} created={created} skipped={skipped} failed={failed}")
            continue
        code, data = req("POST", f"{args.api}/policies", token=token, body=create_payload(p))
        if code in (200, 201):
            created += 1
            if isinstance(data, dict) and data.get("name"):
                existing[data["name"].strip()] = data
        else:
            failed += 1
            failures.append({"name": name, "code": code, "detail": data})
            print(f"FAIL {name}: {code} {str(data)[:200]}")
        if i % 10 == 0:
            time.sleep(0.2)
        if i % 25 == 0:
            print(f"… {i}/{len(to_process)} created={created} skipped={skipped} failed={failed}")

    print(f"\nDone. created={created} skipped_existing={skipped} failed={failed}")
    if failures:
        Path("/tmp/catalog_seed_failures.json").write_text(json.dumps(failures, indent=2, default=str))
        print("Failures written to /tmp/catalog_seed_failures.json")

    # Re-list coverage
    existing2 = existing_by_name(args.api, token)
    names = {p["name"].strip() for p in policies}
    present = names & set(existing2)
    print(f"Coverage: {len(present)}/{len(names)} catalog names present on site")

    if args.baselines:
        print("Triggering baselines/refresh-all (may take several minutes)…")
        code, data = req(
            "POST",
            f"{args.api}/baselines/refresh-all?baseline_type=ROLLING&window_months=12",
            token=token,
            body=None,
            timeout=600,
        )
        print(f"baselines/refresh-all -> {code}")
        print(json.dumps(data, indent=2, default=str)[:2000] if data else "")


if __name__ == "__main__":
    main()
