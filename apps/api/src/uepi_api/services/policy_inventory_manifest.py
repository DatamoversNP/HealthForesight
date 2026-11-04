"""Policy inventory coverage manifest scaffolding.

Definition of complete: every policy in a declared source/program/jurisdiction/as-of
scope is ingested, excluded-with-reason, inaccessible, or failed.

This module reports honest current state. It does NOT invent inventory counts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID


# Declared source families for Dec 4 platform target (not yet fully ingested)
DECLARED_SOURCE_FAMILIES = [
    {
        "family_id": "bcnc_commercial_reimbursement",
        "label": "Representative Payer commercial reimbursement (Blue Cross NC-like)",
        "display_label_default": "Representative Payer Policies",
        "catalog_class": "DEMO_SYNTHETIC",
        "authority": "Representative Payer (synthetic demo)",
        "program": "COMMERCIAL",
        "adapter_status": "DEMO_SYNTHETIC_CATALOG",
    },
    {
        "family_id": "bcnc_medicare_reimbursement",
        "label": "Representative Payer Medicare reimbursement (Blue Cross NC-like)",
        "display_label_default": "Representative Payer Policies",
        "catalog_class": "DEMO_SYNTHETIC",
        "authority": "Representative Payer (synthetic demo)",
        "program": "MEDICARE_ADVANTAGE_OR_MEDICARE",
        "adapter_status": "DEMO_SYNTHETIC_CATALOG",
    },
    {
        "family_id": "bcnc_medical",
        "label": "Representative Payer medical / UM (Blue Cross NC-like)",
        "display_label_default": "Representative Payer Policies",
        "catalog_class": "DEMO_SYNTHETIC",
        "authority": "Representative Payer (synthetic demo)",
        "program": "COMMERCIAL_AND_MA",
        "adapter_status": "DEMO_SYNTHETIC_CATALOG",
    },
    {
        "family_id": "bcnc_administrative",
        "label": "Representative Payer administrative (Blue Cross NC-like)",
        "display_label_default": "Representative Payer Policies",
        "catalog_class": "DEMO_SYNTHETIC",
        "authority": "Representative Payer (synthetic demo)",
        "program": "OPERATIONAL",
        "adapter_status": "DEMO_SYNTHETIC_CATALOG",
    },
    {
        "family_id": "bcnc_pricing",
        "label": "Representative Payer pricing (Blue Cross NC-like)",
        "display_label_default": "Representative Payer Policies",
        "catalog_class": "DEMO_SYNTHETIC",
        "authority": "Representative Payer (synthetic demo)",
        "program": "PAYMENT",
        "adapter_status": "DEMO_SYNTHETIC_CATALOG",
        "note": "Synthetic pricing exhibits for demo — not plan-specific BCBS NC schedules.",
    },
    {
        "family_id": "cms_ncd",
        "label": "CMS National Coverage Determinations",
        "catalog_class": "AUTHORITATIVE_PUBLIC",
        "authority": "CMS",
        "program": "ORIGINAL_MEDICARE_FFS",
        "adapter_status": "NOT_ATTEMPTED",
        "source_hint": "https://www.cms.gov/medicare-coverage-database",
    },
    {
        "family_id": "mac_lcd_nc",
        "label": "MAC LCDs (NC / Palmetto JM)",
        "catalog_class": "AUTHORITATIVE_PUBLIC",
        "authority": "Palmetto GBA (JM)",
        "program": "ORIGINAL_MEDICARE_FFS",
        "adapter_status": "NOT_ATTEMPTED",
        "jurisdiction": "A/B MAC Jurisdiction M",
    },
    {
        "family_id": "lcd_billing_coding_articles",
        "label": "LCD billing/coding articles",
        "catalog_class": "AUTHORITATIVE_PUBLIC",
        "authority": "MAC",
        "program": "ORIGINAL_MEDICARE_FFS",
        "adapter_status": "NOT_ATTEMPTED",
    },
    {
        "family_id": "ncci_ptp",
        "label": "Medicare NCCI PTP edits",
        "catalog_class": "AUTHORITATIVE_PUBLIC",
        "authority": "CMS NCCI",
        "program": "ORIGINAL_MEDICARE_FFS",
        "adapter_status": "NOT_ATTEMPTED",
        "note": "Quarterly versioned files required; not a handful of examples.",
    },
    {
        "family_id": "ncci_mue",
        "label": "Medicare NCCI MUE edits",
        "catalog_class": "AUTHORITATIVE_PUBLIC",
        "authority": "CMS NCCI",
        "program": "ORIGINAL_MEDICARE_FFS",
        "adapter_status": "NOT_ATTEMPTED",
        "note": "Some MUE values are confidential — must not be fabricated from public subsets.",
    },
]


def _classify_catalog_row(policy: Dict[str, Any]) -> str:
    t = (policy.get("policy_type") or "").upper()
    n = (policy.get("name") or policy.get("policy_name") or "").upper()
    if any(k in t or k in n for k in ("CODING", "REIMBURSEMENT", "MODIFIER", "NCCI", "FEE")):
        return "bcnc_commercial_reimbursement"
    if "ADMIN" in t:
        return "bcnc_administrative"
    if any(k in t for k in ("PRICING", "FEE_SCHEDULE")):
        return "bcnc_pricing"
    if "NCD" in t or "NCD" in n:
        return "cms_ncd"
    if "LCD" in t or "LCD" in n:
        return "mac_lcd_nc"
    return "bcnc_medical"


def build_coverage_manifest(
    *,
    tenant_id: UUID,
    catalog_policies: List[Dict[str, Any]],
    readiness_totals: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """Honest coverage manifest — catalog presence ≠ source completeness."""
    by_family_catalog: Dict[str, int] = {f["family_id"]: 0 for f in DECLARED_SOURCE_FAMILIES}
    unmapped = 0
    for p in catalog_policies:
        fam = _classify_catalog_row(p)
        if fam in by_family_catalog:
            by_family_catalog[fam] += 1
        else:
            unmapped += 1

    families_out = []
    for f in DECLARED_SOURCE_FAMILIES:
        fid = f["family_id"]
        catalog_count = by_family_catalog.get(fid, 0)
        adapter = f["adapter_status"]
        catalog_class = f.get("catalog_class") or "UNKNOWN"
        if adapter == "DEMO_SYNTHETIC_CATALOG":
            inventory_status = "DEMO_SYNTHETIC_CATALOG_PRESENT"
            completeness = "DEMO_INCOMPLETE_NOT_AUTHORITATIVE"
            ingested = catalog_count
            excluded = inaccessible = failed = 0
            discovered = catalog_count
        elif adapter == "NOT_ATTEMPTED":
            inventory_status = "ACQUISITION_NOT_ATTEMPTED"
            completeness = "INCOMPLETE"
            ingested = excluded = inaccessible = failed = 0
            discovered = None
        elif adapter == "NOT_IMPLEMENTED":
            inventory_status = "SOURCE_ADAPTER_MISSING"
            completeness = "INCOMPLETE"
            ingested = excluded = inaccessible = failed = 0
            discovered = None
        elif adapter == "ILLUSTRATIVE_FIXTURE_ONLY":
            inventory_status = "FIXTURE_ONLY_NOT_RECONCILED"
            completeness = "INCOMPLETE"
            ingested = excluded = inaccessible = failed = 0
            discovered = None
        elif adapter == "PARTIAL_CATALOG_SEED":
            inventory_status = "CATALOG_ROWS_PRESENT_UNRECONCILED"
            completeness = "INCOMPLETE"
            ingested = catalog_count
            excluded = inaccessible = failed = 0
            discovered = None
        else:
            inventory_status = "UNKNOWN"
            completeness = "INCOMPLETE"
            ingested = catalog_count
            excluded = inaccessible = failed = 0
            discovered = None

        families_out.append(
            {
                **f,
                "catalog_rows_classified": catalog_count,
                "discovered_from_source": discovered,
                "ingested": ingested,
                "excluded_with_reason": excluded,
                "inaccessible": inaccessible,
                "failed": failed,
                "inventory_status": inventory_status,
                "completeness": completeness,
                "baseline_ready": None,
                "forecast_ready": None,
                "observation_ready": None,
            }
        )

    readiness_totals = readiness_totals or {}
    demo_families = sum(1 for f in families_out if f.get("catalog_class") == "DEMO_SYNTHETIC")
    auth_families = sum(1 for f in families_out if f.get("catalog_class") == "AUTHORITATIVE_PUBLIC")
    return {
        "manifest_version": "policy-inventory-manifest-v2",
        "as_of": datetime.now(timezone.utc).isoformat(),
        "tenant_id": str(tenant_id),
        "definition_of_complete": (
            "Every policy in a declared source, program, jurisdiction, and as-of-date scope "
            "is accounted for as ingested, excluded with a reason, access-blocked, "
            "source-unavailable, or failed. Demo synthetic catalog ≠ authoritative completeness."
        ),
        "complete": False,
        "reason_not_complete": (
            "Authoritative public CMS/NCCI families remain NOT_ATTEMPTED (no exports/API pulls yet). "
            "Representative Payer (Blue Cross NC-like) rows are DEMO_SYNTHETIC only. "
            "Catalog row counts must not be equated with authoritative coverage."
        ),
        "catalog_policy_count": len(catalog_policies),
        "unmapped_catalog_rows": unmapped,
        "catalog_views": {
            "demonstration_policies_default": "Representative Payer Policies",
            "demonstration_policies_contextual": "Representative Payer Policies (Blue Cross NC-like)",
            "authoritative_policies": "Public CMS NCD/LCD/articles/NCCI when acquired",
        },
        "honesty": {
            "representative_payer_is_blue_cross_nc_like_not_verbatim": True,
            "requires_bcbs_nc_authorization": False,
            "demo_synthetic_family_count": demo_families,
            "authoritative_public_family_count": auth_families,
        },
        "families": families_out,
        "analytical_totals_from_persisted_jobs": {
            "inventory_catalog": len(catalog_policies),
            "baseline_ready": readiness_totals.get("baseline_ready"),
            "forecast_ready": readiness_totals.get("forecast_ready"),
            "observation_ready": readiness_totals.get("observation_ready"),
            "impact_assessable": readiness_totals.get("impact_assessable"),
        },
        "licensing_notes": [
            "Do not scrape around access controls or bypass authentication.",
            "Demo does not require Blue Cross NC authorization or proprietary exports.",
            "Representative Payer Policies are synthetic/illustrative — never label as actual Blue Cross NC.",
            "NCCI MUE confidential values must not be invented from public subsets.",
            "CMS MCD API and NCCI downloadable files are the intended authoritative public sources.",
        ],
    }


def load_coverage_manifest(tenant_id: UUID) -> Dict[str, Any]:
    from uepi_api.storage_policies import list_policies
    from uepi_api.services.policy_analytical_readiness import load_portfolio_readiness

    policies = list_policies(tenant_id, summary=True) or []
    readiness = load_portfolio_readiness(tenant_id)
    return build_coverage_manifest(
        tenant_id=tenant_id,
        catalog_policies=policies,
        readiness_totals=readiness.get("totals") or {},
    )
