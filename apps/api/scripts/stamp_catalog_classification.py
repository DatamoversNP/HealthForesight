#!/usr/bin/env python3
"""Stamp existing catalog policies with honest classification / provenance gaps.

Additive metadata only. Does not invent BCBS NC source documents or overwrite
analytical evidence. Marks illustrative catalog rows so UI/API cannot imply
authoritative inventory completeness.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT / "packages" / "common" / "src"))

from uepi_api.database import SessionLocal  # noqa: E402
from uepi_api.models.policy import Policy  # noqa: E402

CATALOG = ROOT / "scripts" / "demo" / "catalog" / "bcbs_nc_aligned_policy_catalog.json"
TENANT = UUID("00000000-0000-0000-0000-000000000001")


def main() -> None:
    catalog = json.loads(CATALOG.read_text())
    by_name = {p["name"]: p for p in catalog.get("policies") or []}
    contract = catalog.get("accuracy_contract") or {}

    db = SessionLocal()
    updated = 0
    try:
        policies = db.query(Policy).filter(Policy.tenant_id == TENANT).all()
        for pol in policies:
            meta = dict(pol.policy_metadata_json or {})
            cat = by_name.get(pol.name)
            classification = {
                "data_classification": "illustrative_catalog"
                if cat and cat.get("not_verbatim_bcbsnc_policy")
                else meta.get("data_classification") or "empirical_or_unlabeled",
                "authoritative_source_reconciled": False,
                "not_verbatim_bcbsnc_policy": bool(cat.get("not_verbatim_bcbsnc_policy")) if cat else meta.get("not_verbatim_bcbsnc_policy"),
                "illustrative_standards_aligned": bool(cat.get("illustrative_standards_aligned")) if cat else meta.get("illustrative_standards_aligned"),
                "catalog_accuracy_contract": contract,
                "provenance_status": "MISSING_AUTHORITATIVE_SOURCE",
                "code_sets_status": "MISSING",
                "stamped_at": datetime.utcnow().isoformat() + "Z",
                "stamped_by": "stamp_catalog_classification.py",
            }
            # Preserve existing keys; nest honesty block
            meta["enterprise_classification"] = classification
            if cat:
                meta.setdefault("domain", cat.get("domain"))
                meta.setdefault("subdomain", cat.get("subdomain"))
                meta.setdefault("jurisdiction", cat.get("jurisdiction") or "NC")
                meta.setdefault("standards_basis", cat.get("standards_basis"))
            pol.policy_metadata_json = meta
            pol.updated_at = datetime.utcnow()
            updated += 1
        db.commit()
        print(json.dumps({"updated": updated, "catalog_matched": sum(1 for p in policies if p.name in by_name)}))
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
