#!/usr/bin/env python3
"""
Ensure ≥1 catalog policy exists for each enterprise PolicyType extension.

Idempotent: skips a type when any policy already has that policy_type.
Does not run baseline / prediction / observation for these stubs.
"""
from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

current_dir = Path(__file__).resolve().parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.database import SessionLocal  # noqa: E402
from uepi_api.models.policy import Policy as PolicyDB  # noqa: E402
from uepi_api.storage_auth import DEFAULT_TENANT_ID  # noqa: E402
from uepi_api.storage_policies import create_policy  # noqa: E402


def _existing_type_and_name_sets(tenant_id) -> tuple[set[str], set[str]]:
    """Lightweight coverage check — avoid full list_policies fan-out on large catalogs."""
    db = SessionLocal()
    try:
        rows = (
            db.query(PolicyDB.policy_type, PolicyDB.name)
            .filter(PolicyDB.tenant_id == tenant_id)
            .all()
        )
        types = {str(t or "").upper() for t, _ in rows}
        names = {str(n or "").strip().lower() for _, n in rows}
        return types, names
    finally:
        db.close()

# Genuinely missing enterprise types (Tier 6) — one illustrative policy each.
ENTERPRISE_TYPE_POLICIES = [
    {
        "policy_type": "MEDICAL_NECESSITY",
        "name": "Outpatient Advanced Imaging Medical Necessity Criteria",
        "description": (
            "Clinical medical-necessity requirements for outpatient MRI/CT/PET. "
            "Catalog coverage for MEDICAL_NECESSITY (distinct from PRIOR_AUTH mechanism)."
        ),
        "owner_role": "UM_LEADER",
        "lever_type": "MEDICAL_NECESSITY",
        "parameters": {"guideline_source": "MCG", "modality": ["MRI", "CT", "PET"]},
    },
    {
        "policy_type": "UTILIZATION_MANAGEMENT",
        "name": "Inpatient Concurrent and Continued-Stay Review Program",
        "description": (
            "UM interventions beyond prior auth: concurrent review, continued-stay, "
            "and retrospective review for inpatient stays."
        ),
        "owner_role": "UM_LEADER",
        "lever_type": "UTILIZATION_MANAGEMENT",
        "parameters": {"review_modes": ["CONCURRENT", "CONTINUED_STAY", "RETROSPECTIVE"]},
    },
    {
        "policy_type": "DRUG_FORMULARY",
        "name": "Commercial Preferred Drug Formulary Design",
        "description": (
            "Preferred/nonpreferred tiers and formulary exclusions for commercial pharmacy benefit."
        ),
        "owner_role": "STRATEGY",
        "lever_type": "DRUG_FORMULARY",
        "parameters": {"tiers": ["PREFERRED", "NONPREFERRED", "EXCLUDED"]},
    },
    {
        "policy_type": "SPECIALTY_PHARMACY",
        "name": "Specialty Drug Site-of-Administration Management",
        "description": (
            "Specialty pharmacy channeling and site-of-administration rules for high-cost therapies."
        ),
        "owner_role": "STRATEGY",
        "lever_type": "SPECIALTY_PHARMACY",
        "parameters": {"channel": "SPECIALTY_PHARMACY", "site_of_admin": ["HOME", "INFUSION_CENTER"]},
    },
    {
        "policy_type": "EXPERIMENTAL_INVESTIGATIONAL",
        "name": "Emerging Treatment Experimental Investigational Exclusion",
        "description": (
            "Coverage restrictions for experimental/investigational treatments pending evidence review."
        ),
        "owner_role": "COMPLIANCE",
        "lever_type": "EXPERIMENTAL_INVESTIGATIONAL",
        "parameters": {"default_coverage": "NONCOVERED", "exception_path": "EXTERNAL_REVIEW"},
    },
    {
        "policy_type": "OUT_OF_NETWORK_COVERAGE",
        "name": "Nonparticipating Provider Exception Coverage Rules",
        "description": (
            "Exceptions and coverage rules when members use nonparticipating / out-of-network providers."
        ),
        "owner_role": "POLICY_ADMIN",
        "lever_type": "OUT_OF_NETWORK_COVERAGE",
        "parameters": {"exception_types": ["NETWORK_ADEQUACY", "CONTINUITY", "EMERGENCY"]},
    },
    {
        "policy_type": "REIMBURSEMENT_METHODOLOGY",
        "name": "Facility Fee Schedule and Bundled Payment Adjustments",
        "description": (
            "Fee schedules, bundled payment rates, and reimbursement adjustments for facility services."
        ),
        "owner_role": "ACTUARIAL",
        "lever_type": "REIMBURSEMENT_METHODOLOGY",
        "parameters": {"methods": ["FEE_SCHEDULE", "BUNDLED", "PERCENT_OF_CHARGE"]},
    },
    {
        "policy_type": "CODING_AND_BILLING",
        "name": "Modifier and Code-Bundling Claim Edit Policy",
        "description": (
            "Modifier rules, code combinations, bundling, and billing edits that drive reimbursement behavior."
        ),
        "owner_role": "COMPLIANCE",
        "lever_type": "CODING_AND_BILLING",
        "parameters": {"edit_types": ["MODIFIER", "NCCI_BUNDLING", "UNBUNDLING"]},
    },
    {
        "policy_type": "CLINICAL_PATHWAY",
        "name": "Oncology Evidence-Based Clinical Pathway",
        "description": (
            "Evidence-based oncology treatment sequences and pathway adherence expectations."
        ),
        "owner_role": "UM_LEADER",
        "lever_type": "CLINICAL_PATHWAY",
        "parameters": {"specialty": "ONCOLOGY", "adherence_target_pct": 80},
    },
    {
        "policy_type": "CONTINUITY_OF_CARE",
        "name": "Provider Network Change Continuity of Care Coverage",
        "description": (
            "Transitional coverage when providers leave the network so members can complete active courses of care."
        ),
        "owner_role": "POLICY_ADMIN",
        "lever_type": "CONTINUITY_OF_CARE",
        "parameters": {"transition_window_days": 90, "eligible": ["ACTIVE_TREATMENT", "PREGNANCY"]},
    },
    {
        "policy_type": "EPISODE_BUNDLED_PAYMENT",
        "name": "Total Joint Replacement Episode Bundled Payment",
        "description": (
            "Episode-based reimbursement rules for elective total joint replacement (facility + professional)."
        ),
        "owner_role": "ACTUARIAL",
        "lever_type": "EPISODE_BUNDLED_PAYMENT",
        "parameters": {"episode": "TJR", "includes": ["FACILITY", "PROFESSIONAL", "POST_ACUTE"]},
    },
    {
        "policy_type": "VALUE_BASED_PAYMENT",
        "name": "Primary Care Shared Savings Quality Incentive Program",
        "description": (
            "Quality incentives and shared-savings / performance-based reimbursement for primary care."
        ),
        "owner_role": "STRATEGY",
        "lever_type": "VALUE_BASED_PAYMENT",
        "parameters": {"model": "SHARED_SAVINGS", "quality_gates": True},
    },
    {
        "policy_type": "PREVENTIVE_SERVICES",
        "name": "ACA Preventive Screening Coverage Requirements",
        "description": (
            "Preventive screening and wellness coverage requirements aligned to USPSTF / ACA mandates."
        ),
        "owner_role": "COMPLIANCE",
        "lever_type": "PREVENTIVE_SERVICES",
        "parameters": {"cost_share": "ZERO", "source": "USPSTF_A_B"},
    },
    {
        "policy_type": "TELEHEALTH_VIRTUAL_CARE",
        "name": "Virtual Visit Eligibility and Reimbursement Rules",
        "description": (
            "Telehealth / virtual care eligibility, modality rules, and reimbursement parity conditions."
        ),
        "owner_role": "POLICY_ADMIN",
        "lever_type": "TELEHEALTH_VIRTUAL_CARE",
        "parameters": {"modalities": ["VIDEO", "AUDIO_ONLY"], "parity": "CONDITIONAL"},
    },
    {
        "policy_type": "POST_ACUTE_CARE",
        "name": "SNF and Home Health Authorization Coverage Rules",
        "description": (
            "Post-acute authorization and coverage for SNF, inpatient rehab, and home health."
        ),
        "owner_role": "UM_LEADER",
        "lever_type": "POST_ACUTE_CARE",
        "parameters": {"settings": ["SNF", "IRF", "HOME_HEALTH"], "requires_auth": True},
    },
]


def main(tenant_id: UUID | None = None) -> int:
    tenant = tenant_id or DEFAULT_TENANT_ID
    present_types, by_name = _existing_type_and_name_sets(tenant)
    print(f"Existing distinct types: {len(present_types)}")

    created = 0
    skipped = 0
    for spec in ENTERPRISE_TYPE_POLICIES:
        ptype = spec["policy_type"]
        name = spec["name"]
        if ptype in present_types:
            print(f"SKIP type already present: {ptype}")
            skipped += 1
            continue
        if name.lower() in by_name:
            print(f"SKIP name already present: {name}")
            skipped += 1
            continue

        payload = {
            "name": name,
            "policy_type": ptype,
            "description": spec["description"],
            "owner_role": spec.get("owner_role") or "POLICY_ADMIN",
            "status": "ACTIVE",
            "scope": {"lob": ["COMMERCIAL"], "markets": ["NC"], "network": ["IN"]},
            "effective_period": {"start_date": "2024-01-01", "end_date": None},
            "enforcement": {
                "mechanism": "SOFT",
                "touchpoint": ["PA_WORKFLOW", "CLAIM_EDIT"],
                "override_allowed": True,
            },
            "policy_levers": [
                {
                    "lever_type": spec["lever_type"],
                    "parameters": spec.get("parameters") or {},
                }
            ],
            "metadata": {
                "catalog_seed": "enterprise_policy_types",
                "analytics_ready": False,
                "note": "Illustrative type coverage; baseline/prediction optional",
            },
        }
        created_policy = create_policy(tenant, payload)
        print(f"CREATED {ptype}: {created_policy.get('name')} ({created_policy.get('id')})")
        created += 1
        present_types.add(ptype)
        by_name.add(name.lower())

    print(f"Done. created={created} skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
