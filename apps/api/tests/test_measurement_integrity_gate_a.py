"""Synthetic Gate A checks. No database, no production fixtures, no demo payment engines."""
import inspect
from datetime import date
from uuid import uuid4

from uepi_api.baseline_metrics_computation import compute_baseline_metrics_from_analysis_result
from uepi_api.learning_loop import calculate_prediction_accuracy
from uepi_api.observation_enhancement import (
    extract_behavioral_explanation_from_analysis_result,
    extract_metrics_from_analysis_result,
)
from uepi_api.routers import analyses as analyses_router
from uepi_api.routers import observations as observations_router
from uepi_api.storage_scorecards import generate_scorecard_from_predicted_impact
from uepi_api.verdict import VERDICT_RULE_VERSION, compute_verdict, endpoint_contract_from_policy
from uepi_common.analytics.impact import ImpactAnalysisEngine, ImpactResult, _relative_percent
from uepi_common.analytics.predicted_impact import PredictedImpactGenerator
from uepi_common.metrics.measurement_integrity import (
    annotate_claimant_exposure,
    authoritative_measure_label,
    enrolled_rate,
    presents_as_enrolled,
)
from uepi_common.metrics.unified_measures import normalize_to_canonical_key


def test_claimant_rates_are_not_labeled_as_enrolled_utilization_or_pmpm():
    labeled = annotate_claimant_exposure(
        {"utilization_per_1k": 1035.15, "cost_pmpm": 75.0, "allowed_pmpm": 100.0},
        unique_members=908,
    )
    assert labeled["denominator_basis"] == "CLAIMANT_MONTHS"
    assert labeled["enrolled_rate_status"] == "NOT_MEASURABLE"
    assert enrolled_rate(labeled) is False
    for key in ("utilization_per_1k", "cost_pmpm", "allowed_pmpm"):
        label = authoritative_measure_label(key, labeled)
        assert presents_as_enrolled(label) is False
        assert "not enrolled" in label
    # A payload with no basis flag is also not enrolled.
    assert presents_as_enrolled(authoritative_measure_label("utilization_per_1k", {})) is False
    assert presents_as_enrolled(authoritative_measure_label("cost_pmpm", None)) is False


def test_empty_claimant_denominator_nulls_rates():
    labeled = annotate_claimant_exposure(
        {"utilization_per_1k": 10, "cost_pmpm": 5, "member_months": 1},
        unique_members=0,
    )
    assert labeled["utilization_per_1k"] is None
    assert labeled["cost_pmpm"] is None
    assert labeled["member_months"] is None
    assert labeled["measurement_status"] == "NOT_MEASURABLE"
    assert labeled["measurement_reason"] == "EMPTY_DENOMINATOR"


def test_paid_alias_does_not_become_allowed():
    assert normalize_to_canonical_key("cost_pmpm") == "paid_pmpm_total"
    assert normalize_to_canonical_key("allowed_pmpm") != "paid_pmpm_total"
    metrics = extract_metrics_from_analysis_result(
        {"post_period": {"allowed_pmpm": 100.0, "utilization_per_1k": 120.0}}
    )
    assert "cost_pmpm" not in metrics
    assert metrics["allowed_pmpm"] == 100.0
    paid = extract_metrics_from_analysis_result(
        {"post_period": {"cost_pmpm": 75.0, "cost_pmpm_meaning": "PAID"}}
    )
    assert paid["cost_pmpm"] == 75.0
    assert paid["cost_pmpm_meaning"] == "PAID"


def test_annualization_identity_stays_and_is_labeled_claimant_based():
    metrics = compute_baseline_metrics_from_analysis_result(
        {
            "benchmarks": [
                {"metric_name": "member_months", "metric_value": 1200, "unit": "count"},
                {"metric_name": "cost_pmpm", "metric_value": 100.0, "unit": "PMPM"},
            ]
        },
        tenant_id=uuid4(),
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 1),
    )
    assert metrics["allowed_total_annualized"] == 120000
    assert metrics["annualization_basis"] == "CLAIMANT_MONTHS"
    assert "not enrolled" in metrics["annualization_label"].lower()


def test_percent_change_is_unavailable_when_baseline_is_not_positive():
    assert _relative_percent(-15, 100) == -15
    assert _relative_percent(0, 100) == 0
    assert _relative_percent(10, 0) is None
    assert _relative_percent(10, None) is None
    result = ImpactResult(
        method="pre_post",
        effect_size=10,
        percent_change=None,
        confidence_interval=(1.0, 2.0),
        p_value=0.01,
    )
    payload = result.to_dict()
    assert payload["percent_change"] is None
    assert payload["change_status"] == "UNAVAILABLE"
    assert payload["p_value"] is None
    assert payload["confidence_interval"]["level"] is None
    assert payload["uncertainty_status"] == "UNVERIFIED_INFERENTIAL"
    assert payload["resample_grain"] == "CLAIM_LINE"
    assert "not inferential" in payload["uncertainty_label"]
    assert ImpactAnalysisEngine._compute_p_value(None, 1, 0, 1) is None
    bootstrap = inspect.getsource(ImpactAnalysisEngine._bootstrap_pre_post_ci)
    assert "else 1" in bootstrap


def test_prediction_lookup_keeps_known_percent_and_nulls_confidence_and_levels():
    generator = PredictedImpactGenerator(uuid4())
    result = generator.generate_predicted_impact(
        policy_id=uuid4(),
        policy_levers=[{
            "lever_type": "PRIOR_AUTH",
            "enforcement_strength": "HARD",
            "parameters": {"codes": ["72148"]},
        }],
        baseline_metrics=None,
        elasticity_data=None,
    )
    metrics = result.metrics
    assert metrics.prediction_method == "SIMULATION_LOOKUP"
    assert metrics.evidence_class == "SIMULATION_ONLY"
    assert metrics.confidence_score is None
    assert metrics.utilization_change_per_1k is None
    assert metrics.cost_change_pmpm is None
    assert metrics.cost_change_total is None
    assert round(metrics.utilization_change_pct, 2) == -25.2
    assert round(metrics.cost_change_pct, 2) == -22.68
    assert result.provider_response.confidence_score is None
    caller = generator.generate_predicted_impact(
        policy_id=uuid4(),
        policy_levers=[{"lever_type": "PRIOR_AUTH", "enforcement_strength": "HARD"}],
        baseline_metrics={"utilization_per_1k": 120, "cost_pmpm": 75, "member_count": 10},
        elasticity_data={"overall_elasticity": -0.35},
    )
    assert caller.metrics.prediction_method == "CALLER_ELASTICITY"
    assert caller.metrics.confidence_score is None
    assert caller.metrics.utilization_change_per_1k is not None


def test_learning_accuracy_is_unavailable_at_predicted_zero_and_keeps_the_known_case():
    unavailable = calculate_prediction_accuracy(0, -8)
    assert unavailable["prediction_accuracy_pct"] is None
    assert unavailable["accuracy_status"] == "UNAVAILABLE"
    assert unavailable["within_range"] is None
    known = calculate_prediction_accuracy(-10, -8)
    assert known["prediction_error_pct"] == 20
    assert known["prediction_accuracy_pct"] == 80
    assert known["within_range"] is False


def test_verdict_requires_an_endpoint_contract_and_accepts_one_endpoint():
    comparisons = {
        "vs_baseline": {"utilization_change_pct": -25.0, "cost_change_pct": 4.0}
    }
    status, reason, _ = compute_verdict(comparisons, {})
    assert status == "INCONCLUSIVE"
    assert "not a verdict" in reason
    one = [{"metric_id": "utilization_per_1k", "direction": "decrease"}]
    status, reason, _ = compute_verdict(comparisons, {}, required_endpoints=one)
    assert status == "ON_TRACK"
    assert "cost" not in reason.lower() or "utilization_per_1k" in reason
    missed, reason, _ = compute_verdict(
        {"vs_baseline": {"utilization_change_pct": 4.0}},
        {},
        required_endpoints=one,
    )
    assert missed == "AT_RISK"
    backfire, _, _ = compute_verdict(
        {"vs_baseline": {"utilization_change_pct": 4.0}},
        {"actionable_insights": ["review"]},
        required_endpoints=one,
    )
    assert backfire == "BACKFIRE"
    monitor, _, _ = compute_verdict(
        comparisons,
        {},
        required_endpoints=[{"metric_id": "utilization_per_1k", "direction": "monitor_only"}],
    )
    assert monitor == "INCONCLUSIVE"
    missing, _, _ = compute_verdict(
        {"vs_baseline": {}},
        {},
        required_endpoints=one,
    )
    assert missing == "INCONCLUSIVE"
    policy = {"metadata": {"measurement": {"required_endpoints": one}}}
    assert endpoint_contract_from_policy(policy) == one
    assert endpoint_contract_from_policy({}) is None
    assert VERDICT_RULE_VERSION == "v1.1-endpoints"


def test_read_time_verdict_route_recomputes_without_writing_history():
    source = inspect.getsource(observations_router.list_policy_verdicts_route)
    assert "endpoint_contract_from_policy" in source
    assert "verdict_is_recomputed" in source
    assert "historical_verdict_status" in source
    assert "db.commit" not in source
    assert "db.add" not in source
    mock = inspect.getsource(analyses_router.complete_all_pending_analyses)
    assert '"p_value": 0.01' not in mock
    assert '"p_value": None' in mock
    observations_mock = inspect.getsource(observations_router.create_all_observations_from_pending_analyses)
    assert '"p_value": 0.01' not in observations_mock


def test_narrative_without_a_contract_is_not_a_performance_claim():
    explanation = extract_behavioral_explanation_from_analysis_result(
        {
            "impact_estimate": {
                "effect_size": -0.2,
                "percent_change": -25.0,
                "p_value": 0.01,
                "confidence_interval": [-0.3, -0.1],
            }
        }
    )
    text = str(explanation)
    assert "INCONCLUSIVE" in text
    assert "excellent performance" not in text.lower()
    assert "statistically significant" not in text.lower()
    assert "95% confidence" not in text.lower()
    assert "95% ci" not in text.lower()


def test_missing_metrics_are_not_filled_with_zero_or_a_fake_interval():
    metrics = extract_metrics_from_analysis_result({"impact_estimate": {"p_value": None}})
    assert metrics.get("utilization_per_1k") is None
    assert metrics.get("observed_percent_change") is None
    assert metrics.get("p_value") is None
    assert "confidence_interval" not in metrics


def test_scorecard_does_not_invent_confidence():
    card = generate_scorecard_from_predicted_impact(
        uuid4(),
        {"metrics": {"utilization_change_pct": -25.2, "cost_change_pct": -22.68, "confidence_score": None}},
    )
    assert card["regulatory_defensibility_score"] is None
    assert card["effectiveness_index"] is None
