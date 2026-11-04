"""Representative Payer (Blue Cross NC-like) demo catalog adapters.

This is a **demonstration** environment. These families are synthetic / illustrative
payer configurations modeled on realistic commercial and Medicare health-plan
operations. They are **not** verbatim Blue Cross NC proprietary policies and do
**not** require Blue Cross NC authorization or exports.

Prefer product label: "Representative Payer Policies".
Contextual label: "Representative Payer Policies (Blue Cross NC-like)".
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from uepi_api.services.policy_sources.base import AdapterResult, SourceDocumentRecord
from uepi_api.services.policy_sources.file_drop import load_family_from_drop


_FAMILIES = {
    "bcnc_commercial_reimbursement": "PAYMENT_POLICY|REIMBURSEMENT|CODING|FEE|BUNDLE|MPPR|NCCI",
    "bcnc_medicare_reimbursement": "MEDICARE|MA|PAYMENT",
    "bcnc_medical": "PRIOR_AUTH|STEP_THERAPY|SITE_OF_CARE|COVERAGE|CLINICAL|UM|QUANTITY|MEDICAL",
    "bcnc_administrative": "ADMINISTRATIVE|REFERRAL|NETWORK|ACCESS|PROVIDER_ELIGIBILITY|BENEFIT|COST_SHARING",
    "bcnc_pricing": "PRICING|FEE_SCHEDULE|COST_SHARING",
    "payer_adaptations": "ADAPT|COMPOSITE",
}


def _catalog_path() -> Path:
    return Path(__file__).resolve().parents[6] / "scripts" / "demo" / "catalog" / "bcbs_nc_aligned_policy_catalog.json"


def _load_demo_catalog_docs(family_id: str) -> List[SourceDocumentRecord]:
    path = _catalog_path()
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    policies = data.get("policies") or []
    hint = _FAMILIES.get(family_id, "")
    keys = [k for k in hint.split("|") if k]
    docs: List[SourceDocumentRecord] = []
    for p in policies:
        if not p.get("not_verbatim_bcbsnc_policy") and not p.get("illustrative_standards_aligned"):
            continue
        ptype = (p.get("policy_type") or "").upper()
        name = (p.get("name") or "").upper()
        domain = (p.get("domain") or "").upper()
        blob = f"{ptype} {name} {domain}"
        if keys and not any(k in blob for k in keys):
            continue
        docs.append(
            SourceDocumentRecord(
                family_id=family_id,
                authority="Representative Payer (synthetic demo)",
                source_document_id=f"demo-catalog:{family_id}:{p.get('name')}",
                title=str(p.get("name")),
                source_version=str(data.get("catalog_version") or "demo"),
                source_url=None,
                program=",".join(p.get("lobs") or []) or None,
                jurisdiction=p.get("jurisdiction") or "NC",
                state="NC",
                raw_payload={
                    "catalog_class": "DEMO_SYNTHETIC",
                    "not_verbatim_bcbsnc_policy": True,
                    "illustrative_standards_aligned": True,
                    "display_label": "Representative Payer Policies (Blue Cross NC-like)",
                    "policy_type": p.get("policy_type"),
                    "domain": p.get("domain"),
                    "subdomain": p.get("subdomain"),
                    "accuracy_contract": data.get("accuracy_contract"),
                },
            )
        )
    return docs


def discover_bcbs_family(family_id: str) -> AdapterResult:
    """Discover representative-payer demo catalog rows (optional file-drop override)."""
    drop = load_family_from_drop(family_id, authority="Representative Payer (synthetic demo)")
    if drop.discovered:
        drop.acquisition_state = "RECONCILED"
        drop.adapter_status = "DEMO_SYNTHETIC_CATALOG"
        drop.notes = (
            (drop.notes or "")
            + " | File-drop used for representative payer configs (not BCBS NC proprietary)."
        )
        drop.scope = {
            **(drop.scope or {}),
            "catalog_class": "DEMO_SYNTHETIC",
            "display_label_default": "Representative Payer Policies",
            "display_label_contextual": "Representative Payer Policies (Blue Cross NC-like)",
        }
        return drop

    docs = _load_demo_catalog_docs(family_id)
    if docs:
        return AdapterResult(
            family_id=family_id,
            adapter_status="DEMO_SYNTHETIC_CATALOG",
            acquisition_state="DEMO_SYNTHETIC_CATALOG",
            discovered=docs,
            notes=(
                f"Loaded {len(docs)} illustrative catalog definitions for {family_id}. "
                "These are Blue Cross NC-like representative payer policies — not verbatim BCBS NC."
            ),
            scope={
                "catalog_class": "DEMO_SYNTHETIC",
                "catalog_path": str(_catalog_path()),
                "display_label_default": "Representative Payer Policies",
                "display_label_contextual": "Representative Payer Policies (Blue Cross NC-like)",
                "requires_bcbs_nc_authorization": False,
            },
        )

    return AdapterResult(
        family_id=family_id,
        adapter_status="SOURCE_UNAVAILABLE",
        acquisition_state="SOURCE_UNAVAILABLE",
        notes="No representative-payer demo catalog or drop files found for this family",
        scope={
            "catalog_class": "DEMO_SYNTHETIC",
            "requires_bcbs_nc_authorization": False,
        },
    )
