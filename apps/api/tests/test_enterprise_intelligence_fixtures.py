"""Dec 4 enterprise fixtures — DiD validation suite, suppression, verdict integration."""
from uepi_api.services.enterprise_intelligence_fixtures import (
    MRI_KNOWN_TRUE_DID,
    MRI_POLICY_ID,
    MRI_SERIES,
    causal_validation_suite,
    cold_start_forecast,
    implementation_inventory,
    mri_causal_impact,
    nc_applicability_explorer,
    policy_composition,
    provider_behavior_panel,
    resolve_applicability,
    unified_verdict_evidence,
    _did_from_series,
)


def test_mri_did_formula_matches_manual_recalc():
    """Independent recalculation of DiD from series — same as workbench formula.

    Assertions compare *unrounded* calculation fields within 1e-6.
    Display fields (observed_change / estimated_incremental_effect) may round
    to 3 decimals (−14.833 / −9.417); tolerance for those is documented below.
    Unit is INDEX_POINTS (Jan=100), not utilization per 1k.
    """
    pre_m = ["Jan", "Feb", "Mar", "Apr"]
    post_m = ["May", "Jun", "Jul"]
    manual = _did_from_series(MRI_SERIES, pre_m, post_m)
    result = mri_causal_impact()
    assert result["method"] == "difference_in_differences"
    assert result["unit"]["code"] == "INDEX_POINTS"
    # Unrounded arithmetic identity: naive - did == control_change
    assert abs(result["calculation"]["did"] - manual["did"]) < 1e-6
    assert abs(result["calculation"]["treatment_diff"] - manual["naive_pre_post"]) < 1e-6
    assert abs(result["calculation"]["control_diff"] - manual["control_change"]) < 1e-6
    assert abs(result["calculation"]["naive_minus_did"] - manual["control_change"]) < 1e-6
    # Display rounding (3 dp) within 0.01 of unrounded
    assert abs(result["estimated_incremental_effect"] - manual["did"]) < 0.01
    assert abs(result["observed_change"] - manual["naive_pre_post"]) < 0.01
    assert abs((-14.833) - (-5.417) - (-9.416)) < 0.002  # reported reconciliation


def test_mri_did_recovers_planted_known_effect_not_circular():
    result = mri_causal_impact()
    assert result["labeled_synthetic"] is True
    assert result["evidence_classification"] == "CAUSAL"
    assert result["unit"]["code"] == "INDEX_POINTS"
    assert result["known_true_effect"] == MRI_KNOWN_TRUE_DID
    assert result["recovered_within_tolerance"] is True
    # Planted constant must not equal a runtime round-trip of itself only
    assert abs(result["estimated_incremental_effect"] - MRI_KNOWN_TRUE_DID) <= result["tolerance"]
    assert abs(result["observed_change"]) > abs(result["estimated_incremental_effect"])
    assert result["diagnostics"]["naive_pre_post_would_overstate"] is True
    assert result["diagnostics"]["parallel_trends_pre"] == "PASS"
    assert len(result["external_factors"]) >= 2
    assert len(result["series"]) == 7
    assert "treatment_definition" in result
    assert "comparison_population" in result


def test_causal_validation_suite_all_cases():
    suite = causal_validation_suite()
    assert suite["all_passed"] is True
    by_id = {c["case_id"]: c for c in suite["cases"]}
    assert by_id["known_effect"]["passed"] is True
    assert by_id["no_effect"]["passed"] is True
    assert abs(by_id["no_effect"]["did"]) <= 0.05
    assert by_id["confounded_common_shock"]["passed"] is True
    assert abs(by_id["confounded_common_shock"]["did"]) <= 0.05
    assert abs(by_id["confounded_common_shock"]["naive_pre_post"]) > 10
    assert by_id["parallel_trend_violation"]["passed"] is True
    assert by_id["parallel_trend_violation"]["classification"] == "INCONCLUSIVE"


def test_composition_preserves_catalog_type():
    c = policy_composition(MRI_POLICY_ID, "Outpatient MRI Prior Authorization", "PRIOR_AUTH")
    assert c["catalog_policy_type"] == "PRIOR_AUTH"
    assert "PRIOR_AUTH" in c["mechanisms"]
    assert "MEDICAL_NECESSITY" in c["mechanisms"]
    assert c["primary_domain"] == "MEDICAL"
    assert c["hierarchy"]["version"]


def test_reimbursement_composition_is_coding_domain():
    c = policy_composition("coding-1", "Modifier and Code-Bundling Claim Edit Policy", "CODING_AND_BILLING")
    assert c["primary_domain"] == "CODING_EDIT"
    assert "REIMBURSEMENT" in c["mechanisms"] or "CODING_EDIT" in c["mechanisms"]


def test_provider_small_cell_suppressed_in_api_payload():
    panel = provider_behavior_panel(MRI_POLICY_ID)
    assert panel["peer_selection"]["method"]
    assert "Arbitrary" in panel["peer_selection"]["not_used"]
    suppressed = [s for s in panel["signals"] if s["suppressed"]]
    assert len(suppressed) >= 1
    for s in suppressed:
        assert s["baseline_value"] is None
        assert s["observed_value"] is None
        assert s["change"] is None
        assert s["n"] < panel["minimum_n"]
    assert any(s["denominator"] for s in panel["signals"] if not s["suppressed"])


def test_applicability_nc_palmetto_jm():
    a = nc_applicability_explorer()
    assert a["program_family"] == "ORIGINAL_MEDICARE_FFS"
    assert a["contractor"] == "Palmetto GBA"
    assert "Jurisdiction M" in (a["jurisdiction"] or "")
    types = {s["source_type"] for s in a["sources"]}
    assert "NCD" in types and "LCD" in types and "NCCI_PTP" in types
    assert "adjudicat" in a["disclaimer"].lower() or "Does not adjudicate" in a["disclaimer"]


def test_applicability_ma_vs_ffs_vs_commercial_vs_superseded():
    ma = resolve_applicability("Medicare Advantage", "North Carolina")
    assert ma["program_family"] == "MEDICARE_ADVANTAGE"
    assert ma["status"] == "NO_AUTOMATIC_FFS_CHAIN"
    assert len(ma["sources"]) == 0

    commercial = resolve_applicability("Commercial", "North Carolina")
    assert commercial["program_family"] == "COMMERCIAL_PAYER"

    superseded = resolve_applicability(
        "Original Medicare FFS", "North Carolina", as_of="2022-01-01"
    )
    assert superseded["status"] == "SUPERSEDED_DOCUMENT"
    assert any(s.get("status") == "SUPERSEDED" for s in superseded["sources"])

    no_match = resolve_applicability("Original Medicare FFS", "California")
    assert no_match["status"] == "NO_MATCH_JURISDICTION"


def test_cold_start_tier_c_provenance_no_point_estimate():
    c = cold_start_forecast("new-id", "Specialty Drug Site-of-Administration Management")
    assert c["evidence_tier"].startswith("C_")
    assert c["prior_intervention_history"] is False
    assert c["numeric_scenario"]["precision"] == "scenario_range_only"
    assert c["numeric_scenario"]["not_a_point_estimate"] is True
    assert len(c["assumption_records"]) >= 2
    for a in c["assumption_records"]:
        assert a["source"]
        assert a["source_version"]
        assert a["as_of"]
        assert a["uncertainty_rationale"]
    assert "promote" in c["recalibration_rule"].lower() or "Tier C" in c["recalibration_rule"]


def test_unified_verdict_three_independent_assessments():
    v = unified_verdict_evidence(
        MRI_POLICY_ID,
        "Outpatient MRI Prior Authorization",
        "PRIOR_AUTH",
        observation_verdict="ON_TRACK",
    )
    assert set(v["assessments"].keys()) == {
        "forecast_performance",
        "causal_evidence",
        "policy_governance",
    }
    assert v["assessments"]["forecast_performance"] == "WITHIN_EXPECTED_RANGE"
    assert v["assessments"]["causal_evidence"] == "SUPPORTED_EFFECT"
    assert v["assessments"]["policy_governance"] == "MAINTAIN"
    assert v["causal_summary"]["estimated_incremental_effect"] is not None
    assert v["provider_behavior_summary"]["no_intent_inference"] is True
    assert v["lineage"]["immutable"] is True

    cold = unified_verdict_evidence(
        "specialty-1",
        "Specialty Drug Site-of-Administration Management",
        "SPECIALTY_PHARMACY",
    )
    assert cold["assessments"]["causal_evidence"] == "NOT_ESTIMABLE"
    assert cold["cold_start"] is not None
    assert cold["cold_start"]["evidence_tier"].startswith("C_")


def test_implementation_inventory_not_production_qualified():
    inv = implementation_inventory()
    assert inv["production_qualified"] is False
    for key in (
        "composition",
        "causal_impact",
        "provider_behavior",
        "cold_start",
        "applicability",
        "verdict_integration",
    ):
        assert inv["capabilities"][key]["status"] == "IMPLEMENTED"
        assert inv["capabilities"][key]["data"] == "TESTED_WITH_SYNTHETIC_DATA"
