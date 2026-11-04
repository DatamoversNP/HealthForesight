"""Clinical applicability beyond jurisdiction — codes, service scope, effective dates.

Jurisdiction match ≠ clinical applicability.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

# Representative Outpatient MRI PA service scope (demo policy code set)
MRI_PA_CPT_SCOPE: Set[str] = {
    "70551",
    "70552",
    "70553",  # brain MRI
    "72141",
    "72146",
    "72148",
    "72149",
    "72156",
    "72157",
    "72158",  # spine MRI (illustrative set)
    "73718",
    "73719",
    "73720",
    "73721",  # lower extremity
    "73218",
    "73219",
    "73220",
    "73221",  # upper extremity
}

# A56729 / L34425 documented CPT scope (orbit, face, and/or neck)
L34425_ARTICLE_CPT: Set[str] = {"70540", "70542", "70543"}

NCD_220_2 = {
    "id": "NCD220.2",
    "title": "Magnetic Resonance Imaging",
    "url": "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=177",
    "effective": "2018-04-10",
    "scope": "NATIONAL",
    "covers": "MRI when reasonable and necessary; FDA-approved units; national noncoverage for certain uses",
}


def assess_mri_pa_medicare_clinical_match(
    *,
    source_document_id: str,
    as_of: str = "2024-06-01",
    policy_cpts: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """Independent clinical applicability for Outpatient MRI PA vs a Medicare authority."""
    cpts = policy_cpts or MRI_PA_CPT_SCOPE
    sid = (source_document_id or "").upper()

    if sid in ("NCD220.2", "NCD-220.2", "220.2"):
        return {
            "source_document_id": "NCD220.2",
            "jurisdiction_match": True,  # national
            "clinical_match": "APPLICABLE",
            "effective_match": as_of >= "2018-04-10",
            "code_overlap": sorted(cpts),  # NCD is indication-based, not a CPT list
            "rationale": (
                "NCD 220.2 is the national MRI coverage determination. It applies to MRI services "
                "generally (including outpatient brain/spine MRI in the PA portfolio) subject to "
                "its coverage and noncoverage provisions."
            ),
            "present_as_mri_authority": True,
            "evidence_url": NCD_220_2["url"],
        }

    if sid == "L34425":
        overlap = sorted(cpts & L34425_ARTICLE_CPT)
        return {
            "source_document_id": "L34425",
            "jurisdiction_match": True,  # Palmetto JM includes NC
            "clinical_match": "PARTIAL_SERVICE_SCOPE",
            "effective_match": as_of >= "2015-10-01",
            "lcd_service_scope": "MRI of the orbit, face, and/or neck",
            "lcd_cpt_codes": sorted(L34425_ARTICLE_CPT),
            "policy_cpt_overlap": overlap,
            "rationale": (
                "L34425 is NC/JM-applicable but clinically limited to orbit/face/neck MRI "
                f"(CPT {', '.join(sorted(L34425_ARTICLE_CPT))}). It does NOT cover the broader "
                "Outpatient MRI PA portfolio (e.g., brain 70551–70553, spine MRI). "
                "Do not present as the primary LCD for general outpatient MRI PA."
            ),
            "present_as_mri_authority": False,
            "present_as_related_partial": True,
            "evidence_url": "https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?lcdId=34425",
        }

    if sid == "A56729":
        return {
            "source_document_id": "A56729",
            "jurisdiction_match": True,
            "clinical_match": "PARTIAL_SERVICE_SCOPE",
            "related_lcd": "L34425",
            "article_cpt_codes": sorted(L34425_ARTICLE_CPT),
            "policy_cpt_overlap": sorted(cpts & L34425_ARTICLE_CPT),
            "rationale": (
                "A56729 is the billing/coding article for L34425 (orbit/face/neck). "
                "Codes and ICD guidance apply only to that LCD's service scope."
            ),
            "present_as_mri_authority": False,
            "present_as_related_partial": True,
            "evidence_url": "https://www.cms.gov/medicare-coverage-database/view/article.aspx?articleId=56729",
        }

    if sid.startswith("NCCI-PTP"):
        return {
            "source_document_id": source_document_id,
            "jurisdiction_match": True,  # national coding edits
            "clinical_match": "CODING_RULE_NOT_COVERAGE",
            "rationale": (
                "NCCI PTP is a coding/payment edit, not a medical-necessity or PA coverage authority. "
                "Demo pair is synthetic/illustrative until full quarterly file is reconciled."
            ),
            "present_as_mri_authority": False,
        }

    return {
        "source_document_id": source_document_id,
        "clinical_match": "UNVERIFIED",
        "present_as_mri_authority": False,
        "rationale": "No clinical applicability profile registered for this document.",
    }


def mri_pa_clinical_bundle(as_of: str = "2024-06-01") -> Dict[str, Any]:
    docs = ["NCD220.2", "L34425", "A56729", "NCCI-PTP-PAIR-70553-70551"]
    assessments = [assess_mri_pa_medicare_clinical_match(source_document_id=d, as_of=as_of) for d in docs]
    authorities = [a for a in assessments if a.get("present_as_mri_authority")]
    partial = [a for a in assessments if a.get("present_as_related_partial")]
    return {
        "policy": "Outpatient MRI Prior Authorization",
        "as_of": as_of,
        "primary_medicare_authorities": authorities,
        "related_partial_authorities": partial,
        "assessments": assessments,
        "honesty": {
            "jurisdiction_match_is_not_clinical_match": True,
            "do_not_claim_L34425_as_general_mri_pa_lcd": True,
            "ncd_220_2_is_primary_national_mri_authority": True,
            "no_verified_jm_lcd_for_full_brain_spine_mri_pa_portfolio": True,
        },
        "unresolved": [
            "No Palmetto JM LCD verified that covers the full Outpatient MRI PA CPT portfolio "
            "(brain/spine/extremity). Local medical necessity may rely on NCD 220.2 + claim-level "
            "documentation without a matching body-region LCD.",
        ],
    }
