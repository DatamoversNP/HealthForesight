"""Shared types and declared scopes for policy source adapters."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SourceDocumentRecord:
    family_id: str
    authority: str
    source_document_id: str
    title: str
    source_version: Optional[str] = None
    source_url: Optional[str] = None
    program: Optional[str] = None
    jurisdiction: Optional[str] = None
    state: Optional[str] = None
    effective_start: Optional[datetime] = None
    effective_end: Optional[datetime] = None
    document_relationships: Optional[Dict[str, Any]] = None
    raw_payload: Optional[Dict[str, Any]] = None
    content_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        for k in ("effective_start", "effective_end"):
            if d.get(k) is not None:
                d[k] = d[k].isoformat()
        return d


@dataclass
class AdapterResult:
    family_id: str
    adapter_status: str
    acquisition_state: str = "NOT_ATTEMPTED"
    discovered: List[SourceDocumentRecord] = field(default_factory=list)
    excluded: List[Dict[str, Any]] = field(default_factory=list)
    inaccessible: List[Dict[str, Any]] = field(default_factory=list)
    failed: List[Dict[str, Any]] = field(default_factory=list)
    notes: str = ""
    scope: Dict[str, Any] = field(default_factory=dict)


def declared_scopes() -> List[Dict[str, Any]]:
    """Declared inventory scopes for Dec 4 enterprise demo coverage.

    Payer families are **Representative Payer (Blue Cross NC-like)** demonstration
    catalogs — not verbatim Blue Cross NC proprietary sources.
    CMS NCD/LCD/article/NCCI families remain authoritative public Medicare sources.
    """
    return [
        {
            "family_id": "bcnc_commercial_reimbursement",
            "label": "Representative Payer commercial reimbursement (Blue Cross NC-like)",
            "display_label_default": "Representative Payer Policies",
            "catalog_class": "DEMO_SYNTHETIC",
            "authority": "Representative Payer (synthetic demo)",
            "program": "COMMERCIAL",
            "requires": "Demo synthetic catalog + mechanism configs — not BCBS NC proprietary exports",
        },
        {
            "family_id": "bcnc_medicare_reimbursement",
            "label": "Representative Payer Medicare reimbursement (Blue Cross NC-like)",
            "display_label_default": "Representative Payer Policies",
            "catalog_class": "DEMO_SYNTHETIC",
            "authority": "Representative Payer (synthetic demo)",
            "program": "MEDICARE_ADVANTAGE_OR_MEDICARE",
            "requires": "Demo synthetic MA/Medicare payment policy configs",
        },
        {
            "family_id": "bcnc_medical",
            "label": "Representative Payer medical / UM policies (Blue Cross NC-like)",
            "display_label_default": "Representative Payer Policies",
            "catalog_class": "DEMO_SYNTHETIC",
            "authority": "Representative Payer (synthetic demo)",
            "program": "COMMERCIAL_AND_MA",
            "requires": "Illustrative standards-aligned catalog (already seeded)",
        },
        {
            "family_id": "bcnc_administrative",
            "label": "Representative Payer administrative policies (Blue Cross NC-like)",
            "display_label_default": "Representative Payer Policies",
            "catalog_class": "DEMO_SYNTHETIC",
            "authority": "Representative Payer (synthetic demo)",
            "program": "OPERATIONAL",
            "requires": "Demo synthetic administrative policy configs",
        },
        {
            "family_id": "bcnc_pricing",
            "label": "Representative Payer pricing policies (Blue Cross NC-like)",
            "display_label_default": "Representative Payer Policies",
            "catalog_class": "DEMO_SYNTHETIC",
            "authority": "Representative Payer (synthetic demo)",
            "program": "PAYMENT",
            "requires": "Demo synthetic fee/pricing exhibits — not plan-specific BCBS NC schedules",
        },
        {
            "family_id": "cms_ncd",
            "label": "CMS National Coverage Determinations",
            "catalog_class": "AUTHORITATIVE_PUBLIC",
            "authority": "CMS",
            "requires": "CMS MCD API token and/or NCD export drop files",
            "program": "ORIGINAL_MEDICARE_FFS",
            "endpoint_hint": "https://www.cms.gov/medicare-coverage-database / api.coverage.cms.gov",
        },
        {
            "family_id": "mac_lcd_nc",
            "label": "MAC LCDs (NC / Palmetto JM)",
            "catalog_class": "AUTHORITATIVE_PUBLIC",
            "authority": "Palmetto GBA (JM)",
            "requires": "CMS MCD LCD export for Jurisdiction M",
            "jurisdiction": "A/B MAC Jurisdiction M",
            "state": "NC",
            "program": "ORIGINAL_MEDICARE_FFS",
            "endpoint_hint": "https://www.cms.gov/medicare-coverage-database",
        },
        {
            "family_id": "lcd_billing_coding_articles",
            "label": "LCD billing/coding articles",
            "catalog_class": "AUTHORITATIVE_PUBLIC",
            "authority": "MAC",
            "requires": "Linked article export from MCD",
            "program": "ORIGINAL_MEDICARE_FFS",
        },
        {
            "family_id": "ncci_ptp",
            "label": "Medicare NCCI PTP edits",
            "catalog_class": "AUTHORITATIVE_PUBLIC",
            "authority": "CMS NCCI",
            "requires": "Quarterly PTP edit files in drop directory",
            "endpoint_hint": "https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits",
        },
        {
            "family_id": "ncci_mue",
            "label": "Medicare NCCI MUE edits",
            "catalog_class": "AUTHORITATIVE_PUBLIC",
            "authority": "CMS NCCI",
            "requires": "MUE release files; confidential values must not be fabricated",
        },
        {
            "family_id": "medicare_other_payment",
            "label": "Other Medicare payment rules (MPPR, global, fee schedule, modifiers, POS)",
            "catalog_class": "AUTHORITATIVE_PUBLIC",
            "authority": "CMS",
            "requires": "PFS / OPPS / MPPR / global surgery source files",
        },
        {
            "family_id": "payer_adaptations",
            "label": "Illustrative payer adaptations of Medicare/industry rules (Blue Cross NC-like)",
            "display_label_default": "Representative Payer Policies",
            "catalog_class": "DEMO_SYNTHETIC",
            "authority": "Representative Payer (synthetic demo)",
            "requires": "Synthetic adopt/modify/exception mappings — not actual BCBS NC adaptations",
        },
    ]
