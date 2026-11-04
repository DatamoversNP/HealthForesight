"""Deterministic Dec 4 enterprise fixtures + validation scenarios.

Labeled synthetic where empirical causal/provider grain is not demo-ready.
DiD arithmetic is independent of planted known effects (recovery is a real check).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

MRI_POLICY_ID = "d403f101-08dd-45c9-ab83-d42e37c62018"
# Prefer validated MPPR payment vertical over modifier/coding (claims lack modifiers).
MPPR_POLICY_ID = "d0eeb370-df14-4478-8755-dad6c3a35a47"
SOS_POLICY_ID = "d7441dd9-3bfe-405e-ae6c-0377204bbb7e"
REIMBURSEMENT_POLICY_NAME = "Multiple Procedure Payment Reduction"
REIMBURSEMENT_POLICY_TYPE = "PAYMENT_POLICY"

# Expansion demo IDs (uuid5) — imported lazily to avoid circular imports at module load.
def _expansion_ids() -> Dict[str, str]:
    from uepi_api.services.expansion_demo_scenarios import (
        INFUSION_SOC_POLICY_ID,
        LCD_COVERAGE_POLICY_ID,
        MUE_POLICY_ID,
        NCD_COVERAGE_POLICY_ID,
        PTP_POLICY_ID,
        THERAPY_POLICY_ID,
    )

    return {
        "ptp": PTP_POLICY_ID,
        "mue": MUE_POLICY_ID,
        "therapy": THERAPY_POLICY_ID,
        "infusion": INFUSION_SOC_POLICY_ID,
        "ncd": NCD_COVERAGE_POLICY_ID,
        "lcd": LCD_COVERAGE_POLICY_ID,
    }
NEW_POLICY_NAME = "Specialty Drug Site-of-Administration Management"
MIN_PROVIDER_N = 30

# Indexed utilization (Jan=100). Unit is index points, NOT util/1k member-months.
# Intervention intensifies after April. Planted incremental DiD target ≈ -9.417
# because control also declines (~ -5.417) while treatment declines more (~ -14.833).
MRI_SERIES = [
    {"month": "Jan", "policy_population": 100.0, "comparison_population": 100.0},
    {"month": "Feb", "policy_population": 102.0, "comparison_population": 101.0},
    {"month": "Mar", "policy_population": 99.0, "comparison_population": 100.0},
    {"month": "Apr", "policy_population": 97.0, "comparison_population": 98.0},
    {"month": "May", "policy_population": 88.0, "comparison_population": 96.0},
    {"month": "Jun", "policy_population": 84.0, "comparison_population": 94.0},
    {"month": "Jul", "policy_population": 82.0, "comparison_population": 93.0},
]
MRI_KNOWN_TRUE_DID = -9.4167  # planted; must match DiD on MRI_SERIES within tolerance


def _difference_in_differences(
    treatment_pre: dict,
    treatment_post: dict,
    control_pre: Optional[dict],
    control_post: Optional[dict],
    metric: str = "utilization_per_1k",
) -> dict:
    if control_pre is None or control_post is None:
        change = treatment_post[metric] - treatment_pre[metric]
        return {
            "method": "pre_post",
            "effect_size": change,
            "percent_change": (change / treatment_pre[metric] * 100) if treatment_pre[metric] else 0.0,
            "treatment_diff": change,
            "control_diff": None,
        }
    treatment_diff = treatment_post[metric] - treatment_pre[metric]
    control_diff = control_post[metric] - control_pre[metric]
    did_estimate = treatment_diff - control_diff
    return {
        "method": "difference_in_differences",
        "effect_size": did_estimate,
        "percent_change": (did_estimate / treatment_pre[metric] * 100) if treatment_pre[metric] else 0.0,
        "treatment_diff": treatment_diff,
        "control_diff": control_diff,
    }


def _avg(series: List[dict], key: str, months: List[str]) -> float:
    vals = [r[key] for r in series if r["month"] in months]
    return sum(vals) / len(vals)


def _did_from_series(series: List[dict], pre_m: List[str], post_m: List[str]) -> dict:
    treatment_pre = {"utilization_per_1k": _avg(series, "policy_population", pre_m), "total_claims": 1200}
    treatment_post = {"utilization_per_1k": _avg(series, "policy_population", post_m), "total_claims": 1100}
    control_pre = {"utilization_per_1k": _avg(series, "comparison_population", pre_m), "total_claims": 1400}
    control_post = {"utilization_per_1k": _avg(series, "comparison_population", post_m), "total_claims": 1350}
    did = _difference_in_differences(treatment_pre, treatment_post, control_pre, control_post)
    return {
        "treatment_pre": treatment_pre["utilization_per_1k"],
        "treatment_post": treatment_post["utilization_per_1k"],
        "control_pre": control_pre["utilization_per_1k"],
        "control_post": control_post["utilization_per_1k"],
        "naive_pre_post": did["treatment_diff"],
        "control_change": did["control_diff"],
        "did": did["effect_size"],
        "method": did["method"],
        "sample_sizes": {
            "treatment_pre_claims": treatment_pre["total_claims"],
            "treatment_post_claims": treatment_post["total_claims"],
            "control_pre_claims": control_pre["total_claims"],
            "control_post_claims": control_post["total_claims"],
        },
    }


def _pre_trend_gap(series: List[dict], pre_m: List[str]) -> float:
    """Mean absolute gap between arms in pre period (index points)."""
    gaps = [
        abs(r["policy_population"] - r["comparison_population"])
        for r in series
        if r["month"] in pre_m
    ]
    return sum(gaps) / len(gaps) if gaps else 0.0


def implementation_inventory() -> Dict[str, Any]:
    """Step 1 — honest inventory of real vs fixture-backed."""
    return {
        "as_of": "2026-11-03",
        "capabilities": {
            "composition": {
                "status": "IMPLEMENTED",
                "data": "TESTED_WITH_SYNTHETIC_DATA",
                "notes": "Inferred composition from catalog type + known demo policies; not yet persisted rule hierarchy / versioned applicability on every row.",
                "code": [
                    "apps/api/src/uepi_api/services/enterprise_intelligence_fixtures.py::policy_composition",
                    "apps/web/src/components/policy/EnterpriseIntelligencePanels.tsx::PolicyCompositionPanel",
                ],
            },
            "causal_impact": {
                "status": "IMPLEMENTED",
                "data": "TESTED_WITH_SYNTHETIC_DATA",
                "notes": "DiD arithmetic + known-effect / no-effect / confounded / parallel-trend-violation fixtures. Not production-qualified on real payer claims (demo uses labeled synthetic series).",
                "code": [
                    "enterprise_intelligence_fixtures.py::mri_causal_impact",
                    "enterprise_intelligence_fixtures.py::causal_validation_suite",
                ],
            },
            "provider_behavior": {
                "status": "IMPLEMENTED",
                "data": "TESTED_WITH_SYNTHETIC_DATA",
                "notes": "behavior_profiles table empty in demo DB; explorer uses labeled fixture with peer criteria + small-cell suppression.",
                "code": ["enterprise_intelligence_fixtures.py::provider_behavior_panel"],
            },
            "cold_start": {
                "status": "IMPLEMENTED",
                "data": "TESTED_WITH_SYNTHETIC_DATA",
                "notes": "Tier C scenario ranges with assumption provenance objects; not empirically calibrated.",
                "code": ["enterprise_intelligence_fixtures.py::cold_start_forecast"],
            },
            "applicability": {
                "status": "IMPLEMENTED",
                "data": "TESTED_WITH_SYNTHETIC_DATA",
                "notes": "NC/Palmetto JM illustrative chain; distinguishes FFS vs MA vs commercial; no-match and superseded paths. Not live CMS MCD ingestion.",
                "code": ["enterprise_intelligence_fixtures.py::resolve_applicability"],
            },
            "verdict_integration": {
                "status": "IMPLEMENTED",
                "data": "TESTED_WITH_SYNTHETIC_DATA",
                "notes": "Unified verdict-evidence contract references composition/causal/behavior/cold-start/applicability; three independent assessments.",
                "code": ["enterprise_intelligence_fixtures.py::unified_verdict_evidence"],
            },
        },
        "production_qualified": False,
        "reason_not_production_qualified": "No complete real-claims causal design, empty behavior store, illustrative Medicare sources.",
    }


def policy_composition(policy_id: str, policy_name: str | None = None, catalog_type: str | None = None) -> Dict[str, Any]:
    name = policy_name or "Policy"
    ctype = (catalog_type or "").upper()
    exp = _expansion_ids()

    # Exact-ID branches first — never inherit MRI lumbar clinical composition by name alone
    # for expansion / payment policies.
    if policy_id == MRI_POLICY_ID:
        return {
            "policy_id": policy_id,
            "policy_name": name or "Outpatient MRI Prior Authorization",
            "primary_domain": "MEDICAL",
            "mechanisms": ["PRIOR_AUTH", "MEDICAL_NECESSITY", "CLINICAL_CRITERIA", "SITE_OF_CARE"],
            "service_scope": ["Advanced Imaging", "Outpatient MRI"],
            "authority": "Payer medical policy",
            "source_provenance": "Representative Payer Policies (Blue Cross NC-like) — demo synthetic",
            "lob": ["COMMERCIAL", "MA"],
            "jurisdiction": "NC",
            "hierarchy": {
                "family": "Advanced Imaging UM",
                "version": "2024.1",
                "effective_start": "2024-01-01",
                "rules": [
                    {"rule_id": "mri-pa-1", "text": "PA required for outpatient MRI", "version": "2024.1"},
                    {"rule_id": "mri-mn-1", "text": "Medical necessity criteria", "version": "2024.1"},
                    {"rule_id": "mri-soc-1", "text": "Preferred freestanding site", "version": "2024.1"},
                ],
            },
            "notes": "One policy, multiple mechanisms — not forced into a single flat type. v1.2.1 lumbar design is proposed definition only; frozen analytics retain pre-migration framing.",
            "catalog_policy_type": ctype or "PRIOR_AUTH",
            "implementation_class": "FIXTURE_BACKED_COMPOSITION",
            "definition_status": "DEFINITION_REVIEW_REQUIRED",
            "operational_activation": "PROHIBITED",
        }
    if policy_id == MPPR_POLICY_ID or (
        "Multiple Procedure Payment Reduction" in name and "NCCI" not in name.upper()
    ):
        return {
            "policy_id": policy_id,
            "policy_name": name or REIMBURSEMENT_POLICY_NAME,
            "primary_domain": "REIMBURSEMENT",
            "mechanisms": ["MPPR", "PAYMENT_REDUCTION", "PRICE_EFFECT"],
            "service_scope": ["Multi-procedure same-session claims"],
            "authority": "Representative Payer (Blue Cross NC-like)",
            "source_provenance": "DEMO_SYNTHETIC known-answer payment rule (reimbursement-mppr-v1)",
            "lob": ["COMMERCIAL", "MA"],
            "jurisdiction": "NC",
            "hierarchy": {
                "family": "Payment edits / MPPR",
                "version": "reimbursement-mppr-v1",
                "effective_start": "2025-01-01",
                "rules": [
                    {
                        "rule_id": "mppr-sec-50",
                        "text": "Secondary procedures paid at 50% of allowed; primary 100%",
                        "version": "reimbursement-mppr-v1",
                    }
                ],
            },
            "notes": "Payment impact = price effect; volume held constant. Not utilization elasticity. Deterministic payment ≠ causal estimate.",
            "catalog_policy_type": ctype or "PAYMENT_POLICY",
            "implementation_class": "VALIDATED_DEMO_CALCULATION",
            "definition_status": "DEFINITION_REVIEW_REQUIRED",
            "operational_activation": "PROHIBITED",
        }
    if policy_id == SOS_POLICY_ID or "Freestanding Imaging Steerage" in name:
        return {
            "policy_id": policy_id,
            "policy_name": name or "Freestanding Imaging Steerage",
            "primary_domain": "REIMBURSEMENT",
            "mechanisms": ["SITE_OF_CARE", "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL"],
            "service_scope": ["Outpatient imaging site of service"],
            "authority": "Representative Payer (Blue Cross NC-like)",
            "source_provenance": "DEMO_SYNTHETIC known-answer (reimbursement-sos-v1)",
            "lob": ["COMMERCIAL"],
            "jurisdiction": "NC",
            "hierarchy": {
                "family": "Imaging site steerage",
                "version": "reimbursement-sos-v1",
                "rules": [
                    {"rule_id": "sos-fs-pref", "text": "Prefer freestanding when clinically appropriate", "version": "reimbursement-sos-v1"}
                ],
            },
            "notes": "Payer savings from site differential; access guardrails required. Deterministic payment ≠ causal estimate.",
            "catalog_policy_type": ctype or "SITE_OF_CARE",
            "implementation_class": "VALIDATED_DEMO_CALCULATION",
            "definition_status": "DEFINITION_REVIEW_REQUIRED",
            "operational_activation": "PROHIBITED",
        }
    if policy_id == exp["ptp"]:
        return {
            "policy_id": policy_id,
            "policy_name": name,
            "primary_domain": "CODING_EDIT",
            "mechanisms": ["CODING_EDIT", "NCCI_PTP"],
            "service_scope": ["Synthetic PTP pair 70553/70551"],
            "authority": "DEMO_SYNTHETIC — not CMS quarterly PTP file",
            "source_provenance": "SYNTHETIC_FIXTURE NCCI-PTP-PAIR-70553-70551",
            "lob": ["COMMERCIAL"],
            "jurisdiction": "NC",
            "hierarchy": {"family": "NCCI PTP demo", "version": "demo-synthetic", "rules": []},
            "notes": "Do not claim authoritative CMS quarterly edit or empirical PTP accuracy without modifiers.",
            "catalog_policy_type": ctype or "CODING_AND_BILLING",
            "implementation_class": "VALIDATED_DEMO_CALCULATION",
            "catalog_class": "DEMO_SYNTHETIC",
            "definition_status": "DEFINITION_REVIEW_REQUIRED",
            "operational_activation": "PROHIBITED",
        }
    if policy_id == exp["mue"]:
        return {
            "policy_id": policy_id,
            "policy_name": name,
            "primary_domain": "CODING_EDIT",
            "mechanisms": ["CODING_EDIT", "NCCI_MUE"],
            "service_scope": ["Synthetic MUE unit cap on 97110"],
            "authority": "DEMO_SYNTHETIC — not published/confidential CMS MUE",
            "source_provenance": "SYNTHETIC_FIXTURE NCCI-MUE-97110-DEMO value=4",
            "lob": ["COMMERCIAL"],
            "jurisdiction": "NC",
            "hierarchy": {"family": "NCCI MUE demo", "version": "demo-synthetic", "rules": []},
            "notes": "MUE threshold is synthetic for demo; not an authoritative CMS value.",
            "catalog_policy_type": ctype or "CODING_AND_BILLING",
            "implementation_class": "VALIDATED_DEMO_CALCULATION",
            "catalog_class": "DEMO_SYNTHETIC",
            "definition_status": "DEFINITION_REVIEW_REQUIRED",
            "operational_activation": "PROHIBITED",
        }
    if policy_id == exp["therapy"]:
        return {
            "policy_id": policy_id,
            "policy_name": name,
            "primary_domain": "COVERAGE",
            "mechanisms": ["COVERAGE_DETERMINATION", "PAYMENT"],
            "service_scope": ["Outpatient PT 97110/97140"],
            "authority": "Representative Payer + LCD L34428 reference link",
            "source_provenance": "DEMO_SYNTHETIC coverage-therapy-v1",
            "lob": ["COMMERCIAL"],
            "jurisdiction": "NC",
            "hierarchy": {"family": "OP Therapy", "version": "coverage-therapy-v1", "rules": []},
            "notes": "Mechanical KA $80. Coverage what-if may be NOT_SUPPORTED_FOR_THIS_MECHANISM.",
            "catalog_policy_type": ctype or "COVERAGE",
            "implementation_class": "VALIDATED_DEMO_CALCULATION",
            "definition_status": "DEFINITION_REVIEW_REQUIRED",
            "operational_activation": "PROHIBITED",
        }
    if policy_id == exp["infusion"]:
        return {
            "policy_id": policy_id,
            "policy_name": name,
            "primary_domain": "REIMBURSEMENT",
            "mechanisms": ["SITE_OF_CARE", "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL"],
            "service_scope": ["Specialty infusion site of care"],
            "authority": "Representative Payer",
            "source_provenance": "DEMO_SYNTHETIC reimbursement-infusion-soc-v1",
            "lob": ["COMMERCIAL"],
            "jurisdiction": "NC",
            "hierarchy": {"family": "Infusion SOC", "version": "reimbursement-infusion-soc-v1", "rules": []},
            "notes": "Mechanical KA $3600; product codeset may be empty until product schedule resolved.",
            "catalog_policy_type": ctype or "SITE_OF_CARE",
            "implementation_class": "VALIDATED_DEMO_CALCULATION",
            "definition_status": "DEFINITION_REVIEW_REQUIRED",
            "operational_activation": "PROHIBITED",
        }
    if policy_id == exp["ncd"]:
        return {
            "policy_id": policy_id,
            "policy_name": name,
            "primary_domain": "COVERAGE_STUDY",
            "mechanisms": ["NCD_STUDY", "SOURCE_PROVENANCE"],
            "service_scope": ["MRI under NCD 220.2 FFS reference"],
            "authority": "CMS NCD 220.2 (FFS) — commercial inheritance unsigned",
            "source_provenance": "PROVENANCE_VALIDATED Coverage API / MCD",
            "lob": ["MEDICARE_FFS_REFERENCE"],
            "jurisdiction": "National",
            "hierarchy": {"family": "NCD study", "version": "NCD220.2", "rules": []},
            "notes": "PROVENANCE_ONLY — do not manufacture financial baseline or causal estimate.",
            "catalog_policy_type": ctype or "COVERAGE_STUDY",
            "implementation_class": "PROVENANCE_STUDY",
            "study_class": "PROVENANCE_ONLY",
            "definition_status": "DEFINITION_REVIEW_REQUIRED",
            "operational_activation": "PROHIBITED",
        }
    if policy_id == exp["lcd"]:
        return {
            "policy_id": policy_id,
            "policy_name": name,
            "primary_domain": "COVERAGE_STUDY",
            "mechanisms": ["LCD_STUDY", "SOURCE_PROVENANCE"],
            "service_scope": ["Orbit/face/neck MRI 70540/70542/70543 only"],
            "authority": "Palmetto JM LCD L34425 / article A56729",
            "source_provenance": "PROVENANCE_VALIDATED — PARTIAL clinical match; never lumbar authority",
            "lob": ["MEDICARE_FFS_REFERENCE"],
            "jurisdiction": "JM / NC",
            "hierarchy": {"family": "LCD study", "version": "L34425", "rules": []},
            "notes": "PROVENANCE_ONLY — never apply orbit/face/neck rules to lumbar MRI. No manufactured financial impact.",
            "catalog_policy_type": ctype or "COVERAGE_STUDY",
            "implementation_class": "PROVENANCE_STUDY",
            "study_class": "PROVENANCE_ONLY",
            "definition_status": "DEFINITION_REVIEW_REQUIRED",
            "operational_activation": "PROHIBITED",
        }
    # Name heuristics (non-MRI-ID) — avoid labeling unrelated policies as MRI PA
    if "Outpatient MRI Prior Authorization" in name:
        return policy_composition(MRI_POLICY_ID, name, catalog_type)
    if "NCCI" in name.upper() or "CODING" in ctype or "Modifier" in name:
        return {
            "policy_id": policy_id,
            "policy_name": name,
            "primary_domain": "CODING_EDIT",
            "mechanisms": ["CODING_EDIT", "REIMBURSEMENT"],
            "service_scope": ["Claim edits", "Modifiers", "Bundling"],
            "authority": "Payer reimbursement / coding guidance",
            "source_provenance": "Payer coding & billing policy (demo)",
            "lob": ["COMMERCIAL"],
            "jurisdiction": "NC",
            "hierarchy": {
                "family": "Claims Payment Edits",
                "version": "2024.2",
                "effective_start": "2024-01-01",
                "rules": [
                    {"rule_id": "edit-mod", "text": "Modifier rules", "version": "2024.2"},
                    {"rule_id": "edit-bundle", "text": "NCCI-style bundling", "version": "2024.2"},
                ],
            },
            "notes": "Reimbursement/coding family — measured on unit price, edit rates, coding response.",
            "catalog_policy_type": ctype or "CODING_AND_BILLING",
            "implementation_class": "FIXTURE_BACKED_COMPOSITION",
        }
    if "FORMULARY" in ctype or "SPECIALTY" in ctype or "Specialty Drug" in name:
        return {
            "policy_id": policy_id,
            "policy_name": name,
            "primary_domain": "PHARMACY",
            "mechanisms": ["COVERAGE", "SITE_OF_CARE", "QUANTITY_LIMIT"],
            "service_scope": ["Specialty drugs", "Site of administration"],
            "authority": "Payer pharmacy benefit",
            "source_provenance": "Pharmacy benefit design (demo)",
            "lob": ["COMMERCIAL"],
            "jurisdiction": "NC",
            "hierarchy": {"family": "Specialty Pharmacy", "version": "1.0", "rules": []},
            "notes": "Pharmacy domain — cold-start candidate when no prior intervention history.",
            "catalog_policy_type": ctype or "SPECIALTY_PHARMACY",
            "implementation_class": "FIXTURE_BACKED_COMPOSITION",
        }
    return {
        "policy_id": policy_id,
        "policy_name": name,
        "primary_domain": "MEDICAL",
        "mechanisms": [ctype] if ctype else ["COMPOSITE"],
        "service_scope": [],
        "authority": "Payer policy",
        "source_provenance": "Catalog record",
        "lob": ["COMMERCIAL"],
        "jurisdiction": "NC",
        "hierarchy": {"family": name, "version": "1", "rules": []},
        "notes": "Composition inferred from catalog type; extend via metadata for production.",
        "catalog_policy_type": ctype or None,
        "implementation_class": "INFERRED_FROM_CATALOG_TYPE",
    }


def mri_causal_impact() -> Dict[str, Any]:
    """Known-effect DiD fixture with explicit units, cohorts, formula breakdown."""
    pre_m = ["Jan", "Feb", "Mar", "Apr"]
    post_m = ["May", "Jun", "Jul"]
    calc = _did_from_series(MRI_SERIES, pre_m, post_m)
    incremental = calc["did"]
    observed_change = calc["naive_pre_post"]
    expected_without = calc["control_change"]
    tolerance = 0.05
    recovered = abs(incremental - MRI_KNOWN_TRUE_DID) <= tolerance
    pre_gap = _pre_trend_gap(MRI_SERIES, pre_m)
    parallel = "PASS" if pre_gap < 3.0 else "FAIL"

    return {
        "policy_id": MRI_POLICY_ID,
        "fixture_id": "bcbs_nc_mri_did_v2",
        "labeled_synthetic": True,
        "implementation_class": "TESTED_WITH_SYNTHETIC_DATA",
        "method": calc["method"],
        "formula": "(Y_T,post - Y_T,pre) - (Y_C,post - Y_C,pre)",
        "unit": {
            "code": "INDEX_POINTS",
            "description": "Indexed outpatient MRI utilization with Jan=100. Not utilization per 1,000 member-months.",
            "scale_note": "Absolute index-point changes; percentage change is relative to treatment pre mean.",
        },
        "periods": {
            "pre": pre_m,
            "post": post_m,
            "intervention_timing": "Intensification after April (May–Jul post window)",
        },
        "outcome": "Indexed outpatient MRI utilization",
        "denominator": "Eligible commercial membership index (synthetic)",
        "treatment_definition": {
            "label": "Policy population",
            "definition": "Members subject to outpatient MRI prior authorization intensification",
            "selection": "Deterministic fixture cohort T",
        },
        "comparison_population": {
            "label": "Comparison population",
            "definition": "Matched imaging-eligible members not under the MRI PA intensification",
            "selection": "Deterministic fixture cohort C with parallel pre-trends by construction",
        },
        "calculation": {
            # Full-precision arithmetic (independent of display rounding below)
            "Y_T_pre": calc["treatment_pre"],
            "Y_T_post": calc["treatment_post"],
            "Y_C_pre": calc["control_pre"],
            "Y_C_post": calc["control_post"],
            "treatment_diff": observed_change,
            "control_diff": expected_without,
            "did": incremental,
            "naive_minus_did": observed_change - incremental,
        },
        "observed_change": round(observed_change, 3),
        "expected_change_without_policy": round(expected_without, 3),
        "estimated_incremental_effect": round(incremental, 3),
        "uncertainty_interval": {
            "lower": round(incremental - 1.5, 3),
            "upper": round(incremental + 1.5, 3),
            "level": 0.95,
            "note": "Illustrative interval under fixture assumptions — not bootstrap CI from claims.",
        },
        "diagnostics": {
            "parallel_trends_pre": parallel,
            "pre_period_mean_abs_gap_index_points": round(pre_gap, 3),
            "sample_size_ok": True,
            "sample_sizes": calc["sample_sizes"],
            "contamination_risk": "LOW",
            "naive_pre_post_would_overstate": True,
            "naive_pre_post_change": round(observed_change, 3),
            "treatment_diff": round(observed_change, 4),
            "control_diff": round(expected_without, 4),
            "identification_assumptions": [
                "Parallel trends in absence of treatment (supported in pre window of this fixture)",
                "No anticipation effects in Apr",
                "Stable cohort composition",
                "Comparison group untreated by the MRI PA intensification",
            ],
        },
        "external_factors": [
            {
                "factor_id": "seasonality",
                "name": "Seasonal imaging volume",
                "category": "SEASONALITY",
                "timing": "Ongoing",
                "plausible_direction": "Mild decline into summer",
                "evidence_status": "REGISTERED",
            },
            {
                "factor_id": "network",
                "name": "Freestanding imaging capacity expansion",
                "category": "NETWORK",
                "timing": "Q2",
                "plausible_direction": "Site-of-care shift; volume ambiguous",
                "evidence_status": "REGISTERED",
            },
            {
                "factor_id": "benefit",
                "name": "Advanced imaging cost-share change",
                "category": "BENEFIT_DESIGN",
                "timing": "Jan",
                "plausible_direction": "Downward utilization pressure",
                "evidence_status": "REGISTERED",
            },
        ],
        "evidence_classification": "CAUSAL",
        "limitations": [
            "Synthetic indexed series constructed to demonstrate DiD vs naive pre/post.",
            "Synthetic claims only; do not treat as empirical Blue Cross NC (or any real payer) effect.",
            "Passing DiD arithmetic recovery ≠ causal validity on real data.",
            "Confidence interval is illustrative under fixture assumptions.",
        ],
        "series": MRI_SERIES,
        "known_true_effect": MRI_KNOWN_TRUE_DID,
        "recovered_within_tolerance": recovered,
        "tolerance": tolerance,
    }


def causal_validation_suite() -> Dict[str, Any]:
    """Independent scenarios: known-effect, no-effect, confounded, parallel-trend violation."""
    pre_m = ["Jan", "Feb", "Mar", "Apr"]
    post_m = ["May", "Jun", "Jul"]

    # 1) Known effect — MRI series
    known = _did_from_series(MRI_SERIES, pre_m, post_m)
    known_ok = abs(known["did"] - MRI_KNOWN_TRUE_DID) <= 0.05

    # 2) No effect — both arms identical
    no_effect_series = [
        {"month": m, "policy_population": v, "comparison_population": v}
        for m, v in [
            ("Jan", 100), ("Feb", 101), ("Mar", 100), ("Apr", 99),
            ("May", 95), ("Jun", 94), ("Jul", 93),
        ]
    ]
    no_effect = _did_from_series(no_effect_series, pre_m, post_m)
    no_effect_ok = abs(no_effect["did"]) <= 0.05

    # 3) Confounded — common shock; naive looks large, DiD ~0
    confounded_series = [
        {"month": m, "policy_population": t, "comparison_population": c}
        for m, t, c in [
            ("Jan", 100, 100), ("Feb", 100, 100), ("Mar", 100, 100), ("Apr", 100, 100),
            ("May", 80, 80), ("Jun", 78, 78), ("Jul", 76, 76),
        ]
    ]
    conf = _did_from_series(confounded_series, pre_m, post_m)
    conf_ok = abs(conf["did"]) <= 0.05 and abs(conf["naive_pre_post"]) > 10

    # 4) Parallel trend violation — diverging pre trends → FAIL diagnostic
    diverge_series = [
        {"month": m, "policy_population": t, "comparison_population": c}
        for m, t, c in [
            ("Jan", 100, 100), ("Feb", 110, 100), ("Mar", 120, 100), ("Apr", 130, 100),
            ("May", 125, 98), ("Jun", 120, 96), ("Jul", 115, 94),
        ]
    ]
    diverge = _did_from_series(diverge_series, pre_m, post_m)
    pre_gap = _pre_trend_gap(diverge_series, pre_m)
    parallel_fail = pre_gap >= 3.0

    return {
        "unit": "INDEX_POINTS (Jan=100)",
        "cases": [
            {
                "case_id": "known_effect",
                "passed": known_ok,
                "did": round(known["did"], 4),
                "naive_pre_post": round(known["naive_pre_post"], 4),
                "expected_did": MRI_KNOWN_TRUE_DID,
                "classification_if_assumptions_hold": "CAUSAL",
            },
            {
                "case_id": "no_effect",
                "passed": no_effect_ok,
                "did": round(no_effect["did"], 4),
                "naive_pre_post": round(no_effect["naive_pre_post"], 4),
                "expected_did": 0.0,
                "classification_if_assumptions_hold": "CAUSAL_NULL",
            },
            {
                "case_id": "confounded_common_shock",
                "passed": conf_ok,
                "did": round(conf["did"], 4),
                "naive_pre_post": round(conf["naive_pre_post"], 4),
                "note": "Naive pre/post overstates; DiD near zero when shock is common.",
                "classification": "DESCRIPTIVE_IF_USING_PREPOST_ONLY",
            },
            {
                "case_id": "parallel_trend_violation",
                "passed": parallel_fail,
                "did": round(diverge["did"], 4),
                "pre_period_mean_abs_gap": round(pre_gap, 3),
                "required_action": "Do not label CAUSAL; return INCONCLUSIVE",
                "classification": "INCONCLUSIVE",
            },
        ],
        "all_passed": known_ok and no_effect_ok and conf_ok and parallel_fail,
    }


def _suppress_signal(raw: dict) -> dict:
    """Small-cell suppression applies to API payload, not only UI."""
    out = dict(raw)
    if out.get("n", 0) < MIN_PROVIDER_N:
        out["suppressed"] = True
        out["baseline_value"] = None
        out["observed_value"] = None
        out["change"] = None
        out["peer_adjusted_change"] = None
        out["interpretation"] = f"Suppressed — n={raw.get('n')} below minimum {MIN_PROVIDER_N}."
    return out


def provider_behavior_panel(policy_id: str) -> Dict[str, Any]:
    exp = _expansion_ids()
    if policy_id != MRI_POLICY_ID:
        reason = "Provider-behavior grain not demo-ready for this mechanism"
        if policy_id in exp.values():
            reason = "Expansion/synthetic mechanism — MRI provider-behavior fixture must not be reused"
        elif policy_id in (MPPR_POLICY_ID, SOS_POLICY_ID):
            reason = "Payment/site differential policies use mechanical payment panels, not MRI behavior fixtures"
        return {
            "policy_id": policy_id,
            "labeled_synthetic": False,
            "implementation_class": "NOT_AVAILABLE_FOR_THIS_POLICY",
            "signals": [],
            "suppressed_count": 0,
            "empty_reason": reason,
            "notes": "Do not display MRI imaging behavior as validated results for other policies.",
        }
    raw_signals = [
        {
            "provider_id": "prov-img-01",
            "provider_name": "Triangle Imaging Group",
            "signal": "SITE_OF_CARE_MIX",
            "baseline_value": 0.42,
            "observed_value": 0.54,
            "change": 0.12,
            "peer_adjusted_change": 0.09,
            "unit": "share_hospital_outpatient",
            "denominator": "MRI professional+facility claims for provider's attributed imaging episodes",
            "n": 420,
            "suppressed": False,
            "interpretation": "Observed hospital-outpatient imaging share rose 12 pp (9 pp vs peers). Observed practice-pattern change — not proof of intent.",
        },
        {
            "provider_id": "prov-img-02",
            "provider_name": "Piedmont Radiology Associates",
            "signal": "UTILIZATION_PER_1K",
            "baseline_value": 118.0,
            "observed_value": 96.0,
            "change": -22.0,
            "peer_adjusted_change": -14.0,
            "unit": "mri_per_1k_attributed_members",
            "denominator": "Attributed commercial members × 1,000",
            "n": 380,
            "suppressed": False,
            "interpretation": "Observed MRI utilization declined; peer-adjusted decline is smaller, consistent with partial common trends.",
        },
        {
            "provider_id": "prov-img-03",
            "provider_name": "Coastal Ortho (small cell)",
            "signal": "UTILIZATION_PER_1K",
            "baseline_value": 140.0,
            "observed_value": 90.0,
            "change": -50.0,
            "peer_adjusted_change": -40.0,
            "unit": "mri_per_1k_attributed_members",
            "denominator": "Attributed commercial members × 1,000",
            "n": 8,
            "suppressed": False,
            "interpretation": "Would display raw values without suppression — must be suppressed.",
        },
    ]
    return {
        "policy_id": policy_id,
        "labeled_synthetic": True,
        "implementation_class": "TESTED_WITH_SYNTHETIC_DATA",
        "peer_selection": {
            "method": "Specialty + market + volume quartile",
            "criteria": [
                "Same specialty taxonomy (radiology / advanced imaging)",
                "Same NC metro market cluster",
                "Same pre-period MRI volume quartile",
                "Exclude providers with concurrent unrelated UM pilots (fixture flag)",
            ],
            "not_used": "Arbitrary statewide provider average",
        },
        "minimum_n": MIN_PROVIDER_N,
        "signals": [_suppress_signal(s) for s in raw_signals],
        "caveats": [
            "Demo fixture. Empiric panels require provider-grain claims aggregates (behavior_profiles currently empty).",
            "Do not infer circumvention or motivation from site-of-care or volume shifts alone.",
            "Authorization-response metrics require PA decision logs (not loaded in this fixture).",
            "Suppression applied in API response, not only UI.",
        ],
    }


def cold_start_forecast(policy_id: str, policy_name: str) -> Dict[str, Any]:
    assumptions = [
        {
            "assumption_id": "cs-a1",
            "text": "Specialty channeling reduces HOPD administration share by 10–20% over 6 months",
            "source": "Internal pharmacy strategy assumption (demo)",
            "source_version": "2024.Q1",
            "as_of": "2024-01-15",
            "applicability": "Commercial NC specialty therapies with viable home/infusion alternatives",
            "uncertainty_rationale": "Range from analog site-of-care programs; not calibrated to this exact formulary set",
            "tier_contribution": "C",
        },
        {
            "assumption_id": "cs-a2",
            "text": "No concurrent formulary redesign for the same therapies",
            "source": "Policy change calendar (demo)",
            "source_version": "2024.Q1",
            "as_of": "2024-01-15",
            "applicability": "Must be revalidated if formulary P&T changes",
            "uncertainty_rationale": "If violated, scenario ranges are not identifiable",
            "tier_contribution": "C",
        },
        {
            "assumption_id": "cs-a3",
            "text": "Member access to home/infusion sites remains adequate in NC metro markets",
            "source": "Network adequacy snapshot (demo)",
            "source_version": "2023.12",
            "as_of": "2023-12-01",
            "applicability": "Metro NC; rural access may differ",
            "uncertainty_rationale": "Access constraints can mute site-of-care shift",
            "tier_contribution": "C",
        },
    ]
    return {
        "policy_id": policy_id,
        "policy_name": policy_name,
        "evidence_tier": "C_ASSUMPTION_DRIVEN",
        "tier_selection_reason": "Service baseline exists; no direct historical exposure to this exact specialty administration intervention. Analogs are mechanism-similar only (Tier B support), so primary output remains Tier C scenarios.",
        "baseline_available": True,
        "prior_intervention_history": False,
        "assumptions": [a["text"] for a in assumptions],  # backward-compatible strings
        "assumption_records": assumptions,
        "analog_policies": [
            {
                "name": "Specialty Tier Coinsurance Design",
                "tier": "B",
                "why": "Related pharmacy cost-share — not identical intervention",
            },
            {
                "name": "Site-of-care policies for infusion",
                "tier": "B",
                "why": "Related mechanism — transportability limited",
            },
        ],
        "directional_forecast": "Directional decline in high-cost site share; magnitude not empirically calibrated for this exact intervention.",
        "numeric_scenario": {
            "metric": "hopd_admin_share",
            "baseline": 0.55,
            "scenario_low": 0.44,
            "scenario_high": 0.50,
            "precision": "scenario_range_only",
            "not_a_point_estimate": True,
        },
        "recalibration_rule": "Do not promote Tier C scenarios to empirically validated forecasts solely because observations arrive; require Tier A/B evidence or explicit recalibration decision with new version.",
        "uncertainty_note": "Tier C: service baseline exists; no direct historical exposure. Effect not estimable as a point forecast.",
        "provenance": [
            "Service baseline from specialty drug claims aggregates (demo)",
            "Assumption records with source/version/date below",
            "Analogs selected by mechanism similarity, not identical intervention",
        ],
        "implementation_class": "TESTED_WITH_SYNTHETIC_DATA",
        "labeled_synthetic": True,
    }


def resolve_applicability(
    program: str = "Original Medicare FFS",
    state: str = "North Carolina",
    service_category: Optional[str] = "Advanced imaging / MRI",
    as_of: str = "2024-06-01",
) -> Dict[str, Any]:
    prog = (program or "").lower()
    st = (state or "").lower()

    base_disclaimer = (
        "Applicability explorer only. Does not adjudicate claims or issue coverage denials. "
        "AI remains advisory; deterministic source rules govern applicability."
    )

    # Explicit program family distinction
    if "advantage" in prog or prog.strip() in {"ma", "medicare advantage"}:
        return {
            "query": {"program": program, "state": state, "service_category": service_category, "as_of": as_of},
            "program_family": "MEDICARE_ADVANTAGE",
            "program": "Medicare Advantage",
            "state": state,
            "contractor": None,
            "jurisdiction": None,
            "sources": [],
            "conflicts": [],
            "unresolved_questions": [
                "MA plans may use their own criteria; Original Medicare NCD/LCD do not automatically bind MA benefit design.",
                "Resolve plan-specific medical policy and CMS MA coverage requirements separately.",
            ],
            "status": "NO_AUTOMATIC_FFS_CHAIN",
            "disclaimer": base_disclaimer + " MA ≠ Original Medicare FFS.",
        }

    if "commercial" in prog or "bcbs" in prog:
        return {
            "query": {"program": program, "state": state, "service_category": service_category, "as_of": as_of},
            "program_family": "COMMERCIAL_PAYER",
            "program": "Commercial payer medical/reimbursement policy",
            "state": state,
            "contractor": None,
            "jurisdiction": state,
            "sources": [
                {
                    "source_type": "PAYER_MEDICAL_POLICY",
                    "identifier": "REP-PAYER-demo-MRI-PA",
                    "title": "Outpatient MRI Prior Authorization (Representative Payer demo)",
                    "authority": "Representative Payer (Blue Cross NC-like)",
                    "effective_date": "2024-01-01",
                    "status": "ACTIVE",
                }
            ],
            "conflicts": [],
            "unresolved_questions": [
                "Commercial policy is distinct from CMS NCD/LCD and NCCI.",
            ],
            "status": "PAYER_POLICY_MATCH",
            "disclaimer": base_disclaimer,
        }

    # Original Medicare FFS
    if st not in ("north carolina", "nc"):
        return {
            "query": {"program": program, "state": state, "service_category": service_category, "as_of": as_of},
            "program_family": "ORIGINAL_MEDICARE_FFS",
            "program": "Original Medicare Part A/B FFS",
            "state": state,
            "contractor": None,
            "jurisdiction": None,
            "sources": [],
            "conflicts": [],
            "unresolved_questions": [
                f"No demo localization mapping for state={state}. Shipped example is NC → Palmetto GBA JM.",
            ],
            "status": "NO_MATCH_JURISDICTION",
            "disclaimer": base_disclaimer,
        }

    # Superseded document example when as_of before current LCD
    if as_of < "2023-03-01":
        return {
            "query": {"program": program, "state": state, "service_category": service_category, "as_of": as_of},
            "program_family": "ORIGINAL_MEDICARE_FFS",
            "program": "Original Medicare Part A/B FFS",
            "state": "North Carolina",
            "contractor": "Palmetto GBA",
            "jurisdiction": "A/B MAC Jurisdiction M (JM)",
            "sources": [
                {
                    "source_type": "LCD",
                    "identifier": "LCD-demo-JM-MRI-OLD",
                    "title": "MRI — Jurisdiction M (superseded)",
                    "authority": "Palmetto GBA (JM)",
                    "effective_date": "2021-01-01",
                    "status": "SUPERSEDED",
                    "superseded_by": "LCD-demo-JM-MRI",
                }
            ],
            "conflicts": ["Requested as_of precedes current LCD effective date — show superseded status, do not invent coverage."],
            "unresolved_questions": ["Confirm which LCD version applied on the claim date of service."],
            "status": "SUPERSEDED_DOCUMENT",
            "disclaimer": base_disclaimer,
        }

    return {
        "query": {"program": program, "state": state, "service_category": service_category, "as_of": as_of},
        "program_family": "ORIGINAL_MEDICARE_FFS",
        "program": "Original Medicare Part A/B FFS",
        "state": "North Carolina",
        "contractor": "Palmetto GBA",
        "jurisdiction": "A/B MAC Jurisdiction M (JM)",
        "sources": [
            {
                "source_type": "NCD",
                "identifier": "NCD220.2",
                "title": "Magnetic Resonance Imaging",
                "authority": "CMS",
                "effective_date": "2018-04-10",
                "status": "ACTIVE",
                "verified": True,
                "url": "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=177",
                "scope": "NATIONAL",
            },
            {
                "source_type": "LCD",
                "identifier": "L34425",
                "title": "Magnetic Resonance Imaging of the Orbit, Face, and/or Neck",
                "authority": "Palmetto GBA (JM)",
                "effective_date": "2015-10-01",
                "status": "ACTIVE",
                "verified": True,
                "clinical_match": "PARTIAL_SERVICE_SCOPE",
                "related_article": "A56729",
                "url": "https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?lcdId=34425",
                "states": ["NC", "SC", "VA", "WV"],
                "cpt_codes": ["70540", "70542", "70543"],
                "note": (
                    "JM/NC jurisdiction OK, but clinically limited to orbit/face/neck. "
                    "Not primary LCD for general Outpatient MRI PA (brain/spine)."
                ),
            },
            {
                "source_type": "BILLING_CODING_ARTICLE",
                "identifier": "A56729",
                "title": "Billing and Coding: Magnetic Resonance Imaging of the Orbit, Face, and/or Neck",
                "authority": "Palmetto GBA (JM)",
                "effective_date": "2019-07-25",
                "status": "ACTIVE",
                "verified": True,
                "clinical_match": "PARTIAL_SERVICE_SCOPE",
                "related_lcd": "L34425",
                "url": "https://www.cms.gov/medicare-coverage-database/view/article.aspx?articleId=56729",
            },
            {
                "source_type": "LCD",
                "identifier": "L35175",
                "title": "MRI and CT Scans of the Head and Neck (Noridian J-F)",
                "authority": "Noridian Healthcare Solutions (J-F)",
                "status": "NOT_APPLICABLE_OTHER_JURISDICTION",
                "verified": True,
                "nc_applicable": False,
                "note": "Retained as negative control — must not be treated as NC/JM applicable.",
            },
        ],
        "excluded_sources": [
            {
                "identifier": "L35175",
                "reason": "Wrong MAC jurisdiction (Noridian J-F, not Palmetto JM / NC)",
            }
        ],
        "conflicts": [],
        "unresolved_questions": [
            "Does this NCD/LCD chain apply unchanged to Medicare Advantage plan criteria? (No — resolve MA separately.)",
            "Commercial Representative Payer medical policy may differ from FFS — resolve payer policy separately.",
            "L34425 is body-region specific (orbit/face/neck); broader outpatient MRI PA may need additional authorities.",
        ],
        "status": "MATCHED_FFS_CHAIN",
        "disclaimer": base_disclaimer
        + " NC → Palmetto GBA JM localization verified for L34425/A56729; NCD 220.2 is national.",
    }


def nc_applicability_explorer() -> Dict[str, Any]:
    return resolve_applicability()


def unified_verdict_evidence(
    policy_id: str,
    policy_name: str | None = None,
    catalog_type: str | None = None,
    observation_verdict: str | None = None,
) -> Dict[str, Any]:
    """Connect enterprise tabs into one verdict evidence contract (three independent assessments)."""
    composition = policy_composition(policy_id, policy_name, catalog_type)
    is_mri = policy_id == MRI_POLICY_ID or "MRI" in (policy_name or "").upper()
    is_specialty = "SPECIALTY" in (catalog_type or "").upper() or "Specialty Drug" in (policy_name or "")
    is_coding = "CODING" in (catalog_type or "").upper() or "Modifier" in (policy_name or "")

    causal = mri_causal_impact() if is_mri else {
        "policy_id": policy_id,
        "method": "descriptive",
        "evidence_classification": "INCONCLUSIVE",
        "estimated_incremental_effect": None,
        "limitations": ["No validated comparison design for this policy yet."],
        "labeled_synthetic": False,
        "implementation_class": "NOT_ESTIMABLE",
    }
    behavior = provider_behavior_panel(policy_id)
    cold = cold_start_forecast(policy_id, policy_name or composition["policy_name"]) if is_specialty else None
    applicability = (
        resolve_applicability("Original Medicare FFS", "North Carolina")
        if is_mri
        else resolve_applicability("Commercial", "North Carolina")
        if is_coding or True
        else None
    )

    # Forecast performance from observation verdict when present
    ov = (observation_verdict or "").upper()
    if ov in ("ON_TRACK",):
        forecast_performance = "WITHIN_EXPECTED_RANGE"
    elif ov in ("AT_RISK", "BACKFIRE"):
        forecast_performance = "OUTSIDE_RANGE"
    elif ov in ("UNKNOWN", "INCONCLUSIVE", ""):
        forecast_performance = "NOT_MEASURABLE" if is_specialty else "NOT_MEASURABLE"
    else:
        forecast_performance = "NOT_MEASURABLE"

    if is_mri and causal.get("evidence_classification") == "CAUSAL" and causal.get("recovered_within_tolerance"):
        causal_evidence = "SUPPORTED_EFFECT"
    elif is_specialty:
        causal_evidence = "NOT_ESTIMABLE"
    else:
        causal_evidence = "INCONCLUSIVE"

    if causal_evidence == "SUPPORTED_EFFECT" and forecast_performance == "OUTSIDE_RANGE":
        governance = "INVESTIGATE"
    elif forecast_performance == "WITHIN_EXPECTED_RANGE":
        governance = "MAINTAIN"
    elif is_specialty:
        governance = "MAINTAIN"  # monitor cold-start
    else:
        governance = "CONSIDER_ADJUSTMENT"

    result: Dict[str, Any] = {
        "policy_id": policy_id,
        "policy_name": composition["policy_name"],
        "policy_version": composition.get("hierarchy", {}).get("version"),
        "implementation_inventory_ref": "/api/v1/enterprise/implementation-inventory",
        "assessments": {
            "forecast_performance": forecast_performance,
            "causal_evidence": causal_evidence,
            "policy_governance": governance,
        },
        "assessment_note": "Three independent assessments — not collapsed into one success score.",
        "composition": composition,
        "causal_summary": {
            "method": causal.get("method"),
            "unit": causal.get("unit"),
            "observed_change": causal.get("observed_change"),
            "expected_change_without_policy": causal.get("expected_change_without_policy"),
            "estimated_incremental_effect": causal.get("estimated_incremental_effect"),
            "evidence_classification": causal.get("evidence_classification"),
            "external_factor_count": len(causal.get("external_factors") or []),
            "labeled_synthetic": causal.get("labeled_synthetic"),
            "limitations": causal.get("limitations"),
        },
        "provider_behavior_summary": {
            "signal_count": len([s for s in behavior.get("signals", []) if not s.get("suppressed")]),
            "suppressed_count": len([s for s in behavior.get("signals", []) if s.get("suppressed")]),
            "peer_selection": behavior.get("peer_selection"),
            "labeled_synthetic": behavior.get("labeled_synthetic"),
            "no_intent_inference": True,
        },
        "cold_start": cold,
        "applicability_summary": {
            "program_family": (applicability or {}).get("program_family"),
            "status": (applicability or {}).get("status"),
            "contractor": (applicability or {}).get("contractor"),
            "jurisdiction": (applicability or {}).get("jurisdiction"),
            "source_count": len((applicability or {}).get("sources") or []),
        },
        "financial_vs_verdict": {
            "note": (
                "Positive payer savings is a financial outcome metric only; "
                "it does not automatically imply overall policy success when "
                "access, utilization, behavior, or evidence sufficiency raise concerns."
            ),
            "payer_savings_positive_sign": "payer pays less (provider paid less, ceteris paribus)",
        },
        "decision_options": [
            "Maintain current policy settings",
            "Investigate external factors and provider heterogeneity",
            "Consider adjustment to PA criteria or site-of-care rules",
            "Escalate for clinical/network review",
        ],
        "lineage": {
            "composition_fixture": composition.get("implementation_class"),
            "causal_fixture": causal.get("fixture_id") or causal.get("implementation_class"),
            "immutable": True,
            "note": "Evidence references are additive; do not rewrite historical observation verdicts in place.",
        },
    }
    if is_mri:
        try:
            from uuid import UUID

            from uepi_api.database import SessionLocal
            from uepi_api.models.policy import Policy
            from uepi_api.services.medicare_rules import applicable_medicare_rules_for_policy

            db = SessionLocal()
            try:
                row = db.query(Policy).filter(Policy.id == UUID(policy_id)).first()
                tenant_id = row.tenant_id if row else None
            finally:
                db.close()
            if tenant_id is not None:
                medicare = applicable_medicare_rules_for_policy(
                    tenant_id,
                    UUID(policy_id),
                    program="Original Medicare FFS",
                    state="North Carolina",
                    as_of="2024-06-01",
                )
                result["medicare_rule_set"] = medicare.get("rule_set")
                result["medicare_linked_count"] = len(medicare.get("linked_source_rules") or [])
                result["lineage"]["medicare_rule_set_id"] = (medicare.get("rule_set") or {}).get(
                    "rule_set_id"
                )
                result["lineage"]["analytics_guidance"] = medicare.get("analytics_guidance")
        except Exception as exc:  # noqa: BLE001 — never break verdict on medicare attach
            result["medicare_rule_set_error"] = str(exc)[:200]
    return result
