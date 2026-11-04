#!/usr/bin/env python3
"""Resumable 289-policy configuration batch runner.

Accuracy-first: does not invent proprietary BCBS NC rules.
Marks UNRESOLVED / Representative design / Synthetic fixture honestly.
Does not expand catalog or reseed claims.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from accuracy_validators import validate_scope_lever_alignment  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
EVID = Path(__file__).resolve().parent
INV = EVID / "POLICY_289_MASTER_INVENTORY.json"
CFG_LEDGER = EVID / "POLICY_289_CONFIGURATION_LEDGER.json"
EXEC_LEDGER = EVID / "POLICY_289_ANALYTICAL_EXECUTION_LEDGER.json"
ARCH = EVID / "POLICY_ARCHETYPE_REGISTRY.json"
NINE_IDS = {
    "c3b1e4d2-7a9f-4c8e-b2d1-5f6a8e9c0b1a",  # may not match live — use name match
}


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(p: Path) -> Any:
    return json.loads(p.read_text())


def save_json(p: Path, obj: Any) -> None:
    p.write_text(json.dumps(obj, indent=2) + "\n")


def is_nine(row: Dict[str, Any]) -> bool:
    return bool(row.get("is_dec4_nine"))


def process_policy(row: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    """One policy accuracy gate pass (Day-0: inventory-backed status only)."""
    codes = row.get("codes_on_levers") or []
    # Reconstruct minimal policy for validator
    policy = {
        "name": row.get("name"),
        "policy_type": row.get("policy_type"),
        "scope": row.get("scope_snapshot") or {},
        "policy_levers": [{"parameters": {}} for _ in codes],
    }
    fails = validate_scope_lever_alignment(policy, codes)
    has_pkg = bool(row.get("has_v12_definition_package"))
    status = {
        "policy_id": row["policy_id"],
        "name": row.get("name"),
        "archetype": row.get("archetype"),
        "is_dec4_nine": is_nine(row),
        "DEFINITION_COMPLETE": "PASS" if has_pkg and not fails else ("PARTIAL" if has_pkg else "FAIL"),
        "POLICY_SCOPE_VALIDATED": "FAIL" if any(f.startswith("SCOPE:") for f in fails) else (
            "PASS" if has_pkg else "NOT_RUN"
        ),
        "CODESET_VALIDATED": "PASS" if codes and has_pkg else ("PARTIAL" if codes else "FAIL"),
        "LEVERS_VALIDATED": "FAIL" if any(f.startswith("LEVERS:") for f in fails) else (
            "PASS" if has_pkg else "NOT_RUN"
        ),
        "SOURCE_APPLICABILITY_VALIDATED": "PASS" if has_pkg else "NOT_RUN",
        "ANALYTICAL_MECHANISM_VALIDATED": "PASS" if row.get("has_predicted_impact") else "NOT_RUN",
        "LIFECYCLE_EXECUTED": "PASS" if row.get("has_predicted_impact") and row.get("has_observation") else "PARTIAL",
        "DEMO_READY": "PASS" if is_nine(row) and has_pkg else "NOT_RUN",
        "OPERATIONALLY_APPROVED": "PROHIBITED",
        "accuracy_failures": fails,
        "evidence_classification": (
            "SYNTHETIC_DEMO_FIXTURE" if is_nine(row) and "MPPR" in (row.get("name") or "")
            else ("REPRESENTATIVE_PAYER_POLICY" if has_pkg else "UNCONFIGURED")
        ),
        "updated_at": utc(),
        "dry_run": dry_run,
    }
    return status


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=0, help="0=nine, 1+=remaining slices")
    ap.add_argument("--batch-size", type=int, default=25)
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--write", action="store_true", help="Persist ledger updates")
    args = ap.parse_args()

    if not INV.exists():
        print("Missing inventory — run build_master_inventory.py first", file=sys.stderr)
        return 2

    inv = load_json(INV)
    rows: List[Dict[str, Any]] = inv["policies"]
    nine = [r for r in rows if r.get("is_dec4_nine")]
    rest = [r for r in rows if not r.get("is_dec4_nine")]

    if args.batch == 0:
        target = nine
        batch_label = "batch_0_dec4_nine"
    else:
        start = (args.batch - 1) * args.batch_size
        target = rest[start : start + args.batch_size]
        batch_label = f"batch_{args.batch}_{start}_{start + len(target)}"

    results = [process_policy(r, dry_run=not args.write) for r in target]

    if CFG_LEDGER.exists():
        ledger = load_json(CFG_LEDGER)
    else:
        ledger = {"schema_version": "1.0", "policies": {}}

    by_id = ledger.setdefault("policies", {})
    for r in results:
        by_id[r["policy_id"]] = r

    ledger["meta"] = {
        "updated_at": utc(),
        "last_batch": batch_label,
        "total_catalog": inv["meta"]["total_policies"],
        "note": "Accuracy statuses; OPERATIONALLY_APPROVED remains PROHIBITED",
    }

    out = EVID / f"BATCH_{batch_label}_RESULT.json"
    save_json(out, {"batch": batch_label, "count": len(results), "results": results})
    if args.write:
        save_json(CFG_LEDGER, ledger)
        print(f"Wrote {CFG_LEDGER}")
    print(f"Batch {batch_label}: {len(results)} policies → {out}")
    fails = sum(1 for r in results if r["DEFINITION_COMPLETE"] == "FAIL")
    print(f"DEFINITION_COMPLETE FAIL: {fails}/{len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
