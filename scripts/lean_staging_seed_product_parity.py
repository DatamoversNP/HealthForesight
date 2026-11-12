#!/usr/bin/env python3
"""Seed lean staging DB with users + Dec4 nine policies + demo-comparable synthetic data.

Refuses demo / non-hfleanstg DATABASE_URL. Never touches healthforesight-rg.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from uuid import UUID

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "apps" / "api" / "src"), str(REPO / "packages" / "common" / "src")]

TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
POLICY_DEFS = REPO / "docs" / "demo" / "bcbs-nc" / "policy_definitions"

NINE_JSON = [
    "Outpatient_MRI_Prior_Authorization.json",
    "Multiple_Procedure_Payment_Reduction.json",
    "Freestanding_Imaging_Steerage.json",
    "NCCI_Procedure-to-Procedure_Bundling.json",
    "NCCI_Medically_Unlikely_Units.json",
    "Outpatient_Therapy_Coverage_and_Payment.json",
    "Infusion_Site-of-Care_Optimization.json",
    "NCD_220_2_MRI_Coverage_Change_Study.json",
    "LCD_L34425_NC_MRI_Coverage_Criteria.json",
]


def _assert_staging_db() -> str:
    url = os.environ.get("DATABASE_URL") or ""
    if not url:
        raise SystemExit("DATABASE_URL required")
    bad = ("healthforesight-db", "healthforesight-rg", "uepiadmin@")
    if any(b in url for b in bad) or "hfleanstg" not in url:
        raise SystemExit(f"Refusing non-staging DATABASE_URL host (need hfleanstg): {url.split('@')[-1][:80]}")
    return url


def seed_users() -> None:
    import importlib.util

    path = REPO / "scripts" / "seed_users.py"
    spec = importlib.util.spec_from_file_location("seed_users_mod", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    mod.seed_users()
    print("USERS_PASS")


def upsert_policy_from_json(db, payload: Dict[str, Any]) -> str:
    from uepi_api.models.policy import Policy

    pid = UUID(str(payload["policy_id"]))
    meta = payload.get("metadata") or payload.get("policy_metadata_json") or {}
    if isinstance(meta, dict) and "enterprise_classification" not in meta:
        meta = {
            **meta,
            "enterprise_classification": {
                "catalog_class": "DEMO_SYNTHETIC",
                "representative_payer": True,
                "lean_staging_seed": True,
            },
            "display_label": "Representative Payer Policies",
        }
    now = datetime.utcnow()
    pol = db.query(Policy).filter(Policy.id == pid).one_or_none()
    if pol is None:
        pol = Policy(
            id=pid,
            tenant_id=TENANT_ID,
            name=payload.get("name") or "Unnamed",
            policy_type=payload.get("policy_type") or "OTHER",
            status=payload.get("status") or "ACTIVE",
            description=payload.get("description"),
            policy_metadata_json=meta,
            created_at=now,
            updated_at=now,
        )
        db.add(pol)
        status = "created"
    else:
        pol.name = payload.get("name") or pol.name
        pol.policy_type = payload.get("policy_type") or pol.policy_type
        pol.status = payload.get("status") or pol.status
        pol.description = payload.get("description") or pol.description
        existing = dict(pol.policy_metadata_json or {})
        existing.update(meta)
        pol.policy_metadata_json = existing
        pol.updated_at = now
        status = "updated"
    return f"{pid}:{status}:{pol.name}"


def seed_nine_policies() -> List[str]:
    from uepi_api.database import SessionLocal

    results = []
    db = SessionLocal()
    try:
        for name in NINE_JSON:
            path = POLICY_DEFS / name
            if not path.exists():
                raise FileNotFoundError(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            results.append(upsert_policy_from_json(db, payload))
        db.commit()
    finally:
        db.close()

    # Complete expansion workspace fields (assumptions/guardrails/codes) without
    # colliding frozen IDs — upserts the six expansion IDs already in the nine.
    from uepi_api.services.expansion_demo_scenarios import seed_expansion_policies

    exp = seed_expansion_policies(TENANT_ID)
    print("NINE_POLICIES", len(results), results)
    print("EXPANSION", exp.get("created") if isinstance(exp, dict) else exp)
    return results


def seed_synthetic_q1_light() -> None:
    """Demo-comparable claims + weekly observations (smaller than full demo defaults)."""
    import importlib.util

    sys.argv = [
        "seed_q1_2026_observations_demo.py",
        "--tenant-id",
        str(TENANT_ID),
        "--purge",
        "--clear-all-observations-first",
        "--members",
        "800",
        "--providers",
        "40",
        "--base-claims-per-day",
        "4",
    ]
    path = REPO / "scripts" / "seed_q1_2026_observations_demo.py"
    spec = importlib.util.spec_from_file_location("seed_q1_mod", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    mod.main()
    print("Q1_SYNTHETIC_PASS")


def verify_counts() -> Dict[str, int]:
    from uepi_api.database import SessionLocal
    from uepi_api.models.policy import Policy
    from uepi_api.models.observation import Observation
    from uepi_api.models.canonical_data import ClaimsLineDB
    from uepi_api.models.tenant import User

    db = SessionLocal()
    try:
        out = {
            "policies": db.query(Policy).filter(Policy.tenant_id == TENANT_ID).count(),
            "users": db.query(User).filter(User.tenant_id == TENANT_ID).count(),
            "observations": db.query(Observation).filter(Observation.tenant_id == TENANT_ID).count(),
            "claims": db.query(ClaimsLineDB).filter(ClaimsLineDB.tenant_id == TENANT_ID).count(),
        }
    finally:
        db.close()
    print("COUNTS", out)
    if out["policies"] < 9:
        raise SystemExit(f"expected >=9 policies, got {out['policies']}")
    if out["users"] < 1:
        raise SystemExit("expected seeded users")
    return out


def main() -> None:
    _assert_staging_db()
    # Ensure get_settings / SessionLocal see DATABASE_URL
    seed_users()
    seed_nine_policies()
    seed_synthetic_q1_light()
    verify_counts()
    print("LEAN_STAGING_PRODUCT_SEED_PASS")


if __name__ == "__main__":
    main()
