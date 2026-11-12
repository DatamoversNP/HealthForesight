"""Data-contract and lifecycle checks for every discovered policy."""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from qa.product_agent.oracle import continuation_prediction, money, per_member_month_difference, separate_rollup

TOLERANCE = Decimal("1.00")
RATE_TOLERANCE = Decimal("0.02")


def _num(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _scope(policy: dict) -> dict:
    scope = policy.get("scope")
    return scope if isinstance(scope, dict) else {}


def _policy_key(policy: dict) -> Optional[str]:
    meta = policy.get("metadata") if isinstance(policy.get("metadata"), dict) else {}
    path = str(meta.get("definition_path") or policy.get("definition_path") or "")
    parts = [part for part in path.split("/") if part]
    if len(parts) >= 2 and parts[-1].endswith(".json"):
        return parts[-2]
    return meta.get("policy_key")


def _months(start: Optional[str], end: Optional[str]) -> Optional[int]:
    if not start or not end or len(start) < 7 or len(end) < 7:
        return None
    try:
        sy, sm = int(start[:4]), int(start[5:7])
        ey, em = int(end[:4]), int(end[5:7])
    except ValueError:
        return None
    return (ey - sy) * 12 + (em - sm) + 1


def evaluate_catalog(
    policies: list[dict],
    execution: dict,
    baselines: list[dict],
    observations: list[dict],
    predictions: list[dict],
    claims: dict[str, dict],
    exposure: dict[str, Optional[float]],
) -> tuple[list[dict], list[dict], dict]:
    exec_by_id = {row.get("policy_id"): row for row in execution.get("policies") or []}
    base_by_id: dict[str, dict] = {}
    for row in baselines:
        policy_id = row.get("policy_id")
        if policy_id and policy_id not in base_by_id:
            base_by_id[policy_id] = row
    obs_by_id = {str(row.get("policy_id")): row for row in observations if row.get("policy_id")}
    pred_by_id = {}
    for row in predictions:
        policy_id = str(row.get("policy_id") or "")
        metrics = row.get("metrics") if isinstance(row.get("metrics"), dict) else row
        if policy_id:
            pred_by_id[policy_id] = metrics if isinstance(metrics, dict) else {}

    pre_mm = exposure.get("pre_member_months")
    post_mm = exposure.get("post_member_months")
    matrix = []
    defects = []

    for policy in policies:
        policy_id = str(policy.get("id"))
        execution_row = exec_by_id.get(policy_id) or {}
        baseline = base_by_id.get(policy_id) or {}
        observation = obs_by_id.get(policy_id) or {}
        metrics = baseline.get("baseline_metrics") if isinstance(baseline.get("baseline_metrics"), dict) else {}
        comparisons = observation.get("comparisons") if isinstance(observation.get("comparisons"), dict) else {}
        vs_predicted = comparisons.get("vs_predicted") if isinstance(comparisons.get("vs_predicted"), dict) else {}
        vs_baseline = comparisons.get("vs_baseline") if isinstance(comparisons.get("vs_baseline"), dict) else {}
        pred_metrics = pred_by_id.get(policy_id) or {}
        key = _policy_key(policy) or metrics.get("policy_key")
        claim = claims.get(str(key)) if key else None
        scope = _scope(policy)
        levers = policy.get("policy_levers") or []
        state = execution_row.get("configuration_state") or "NOT_RUN"
        mechanism_executed = bool(execution_row.get("mechanism_executed"))
        baseline_allowed = _num(metrics.get("total_allowed"))
        observed_allowed = _num(vs_predicted.get("observed_allowed"))
        predicted_allowed = _num(pred_metrics.get("predicted_allowed") or vs_predicted.get("frozen_predicted_allowed"))
        expected = None
        prediction_delta = None
        if baseline_allowed is not None and pre_mm and post_mm and state != "PAYMENT_SIMULATION":
            expected_decimal = continuation_prediction(baseline_allowed, pre_mm, post_mm)
            expected = float(expected_decimal) if expected_decimal is not None else None
            if predicted_allowed is not None and expected_decimal is not None:
                prediction_delta = float(money(predicted_allowed) - expected_decimal)
        claim_pre_delta = None
        claim_post_delta = None
        if claim and baseline_allowed is not None:
            claim_pre_delta = float(money(baseline_allowed) - money(claim["pre_allowed"]))
        if claim and observed_allowed is not None:
            claim_post_delta = float(money(observed_allowed) - money(claim["post_allowed"]))

        data_failures = []
        if str(policy.get("policy_type") or "") == "CATALOG_DEFINITION":
            data_failures.append("policy type is still CATALOG_DEFINITION")
        if not (scope.get("lob") or scope.get("states") or scope.get("setting")):
            data_failures.append("scope is empty")
        if not baseline:
            data_failures.append("no baseline")
        if not observation:
            data_failures.append("no observation")
        if predicted_allowed is None and state != "BLOCKED":
            data_failures.append("no frozen prediction")
        verdict = observation.get("verdict_status") or observation.get("historical_verdict_status")
        if observation and not verdict:
            data_failures.append("observation has no verdict")
        if mechanism_executed and state not in {"PAYMENT_SIMULATION", "REVIEW_ONLY", "EXECUTABLE"}:
            data_failures.append("mechanism executed flag disagrees with configuration state")
        if state == "REVIEW_ONLY" and execution_row.get("financial_effect_status") not in {None, "UNAVAILABLE", "NONE", "NOT_APPLICABLE"}:
            if _num(execution_row.get("financial_effect")) not in {None, 0}:
                data_failures.append("review-only policy has a financial effect")
        if state == "BLOCKED" and mechanism_executed:
            data_failures.append("blocked policy is marked executed")

        calculation = "not_applicable"
        if expected is not None and predicted_allowed is not None:
            calculation = "pass" if abs(Decimal(str(prediction_delta or 0))) <= TOLERANCE else "fail"
            if calculation == "fail":
                data_failures.append(f"continuation prediction differs by {prediction_delta}")
        if claim_pre_delta is not None and abs(Decimal(str(claim_pre_delta))) > TOLERANCE:
            calculation = "fail"
            data_failures.append(f"baseline allowed differs from pre-period claims by {claim_pre_delta}")
        if claim_post_delta is not None and abs(Decimal(str(claim_post_delta))) > TOLERANCE:
            calculation = "fail"
            data_failures.append(f"observed allowed differs from post-period claims by {claim_post_delta}")
        if post_mm and observed_allowed is not None and predicted_allowed is not None and state != "PAYMENT_SIMULATION":
            expected_rate = per_member_month_difference(observed_allowed, predicted_allowed, post_mm)
            stored_rate = _num(vs_baseline.get("cost_change_pmpm"))
            if expected_rate is not None and stored_rate is not None:
                if abs(expected_rate - Decimal(str(stored_rate))) > RATE_TOLERANCE:
                    calculation = "fail"
                    data_failures.append("stored per-member-month difference does not match observed minus prediction")

        if state in {"BLOCKED", "AWAITING_CONFIGURATION"}:
            execution_class = "legitimate_gap"
        elif state == "REVIEW_ONLY":
            execution_class = "review_only_not_execution"
        elif state == "PAYMENT_SIMULATION":
            execution_class = "payment_simulation"
        elif state == "EXECUTABLE" and not mechanism_executed:
            execution_class = "executable_engine_missing"
            data_failures.append("contract says executable but no mechanism result is stored")
        else:
            execution_class = state.lower()

        data_result = "fail" if data_failures else "pass"
        if calculation == "not_applicable" and data_result == "pass":
            calculation = "pass" if baseline_allowed is None else calculation
        row = {
            "policy_id": policy_id,
            "name": policy.get("name"),
            "policy_type": policy.get("policy_type"),
            "policy_key": key,
            "configuration_state": state,
            "mechanism": execution_row.get("mechanism"),
            "blocked_reason": execution_row.get("blocked_reason"),
            "required_parameter": execution_row.get("required_parameter"),
            "mechanism_executed": mechanism_executed,
            "execution_class": execution_class,
            "has_scope": bool(scope.get("lob") or scope.get("states") or scope.get("setting")),
            "scope_lob": ",".join(scope.get("lob") or []),
            "scope_states": ",".join(scope.get("states") or []),
            "code_count": len(scope.get("procedure_codes") or []),
            "lever_count": len(levers) if isinstance(levers, list) else 0,
            "baseline_window_start": baseline.get("window_start_date"),
            "baseline_window_end": baseline.get("window_end_date"),
            "baseline_months": _months(str(baseline.get("window_start_date") or ""), str(baseline.get("window_end_date") or "")),
            "observation_period_start": observation.get("observation_period_start"),
            "observation_period_end": observation.get("observation_period_end"),
            "observation_months": _months(str(observation.get("observation_period_start") or ""), str(observation.get("observation_period_end") or "")),
            "baseline_allowed": baseline_allowed,
            "observed_allowed": observed_allowed,
            "predicted_allowed": predicted_allowed,
            "oracle_predicted": expected,
            "prediction_delta": prediction_delta,
            "claim_pre_delta": claim_pre_delta,
            "claim_post_delta": claim_post_delta,
            "verdict": verdict,
            "verdict_reason": observation.get("verdict_reason") or observation.get("screen_verdict_reason"),
            "data_result": data_result,
            "calculation_result": calculation,
            "data_failures": "; ".join(data_failures),
            "browser_result": "not_in_browser_sample",
        }
        matrix.append(row)
        if data_failures:
            defects.append({
                "defect_id": "",
                "severity": "high" if calculation == "fail" else "medium",
                "feature": "policy lifecycle",
                "policy_id": policy_id,
                "expected": "Stored baseline, prediction, observation, and verdict match the source claims and the continuation contract, without claiming an unexecuted mechanism.",
                "actual": "; ".join(data_failures),
                "status": "open",
                "class": "calculation" if calculation == "fail" else "lifecycle",
            })

    rollup_rows = []
    for observation in observations:
        comparisons = observation.get("comparisons") if isinstance(observation.get("comparisons"), dict) else {}
        vs_baseline = comparisons.get("vs_baseline") if isinstance(comparisons.get("vs_baseline"), dict) else {}
        metrics = observation.get("metrics") if isinstance(observation.get("metrics"), dict) else {}
        if metrics.get("denominator_basis") == "ENROLLMENT" and metrics.get("enrolled_rate_status") == "MEASURED":
            rollup_rows.append({
                "cost_change_kind": vs_baseline.get("cost_change_kind"),
                "cost_change": _num(vs_baseline.get("cost_change_pmpm") if vs_baseline.get("cost_change_pmpm") is not None else vs_baseline.get("cost_change")),
            })
    summary = {
        "policy_count": len(matrix),
        "data_pass": sum(1 for row in matrix if row["data_result"] == "pass"),
        "data_fail": sum(1 for row in matrix if row["data_result"] == "fail"),
        "calculation_fail": sum(1 for row in matrix if row["calculation_result"] == "fail"),
        "execution_classes": {},
        "types": {},
        "rollup": separate_rollup(rollup_rows),
        "exposure": exposure,
    }
    for row in matrix:
        summary["execution_classes"][row["execution_class"]] = summary["execution_classes"].get(row["execution_class"], 0) + 1
        summary["types"][row["policy_type"]] = summary["types"].get(row["policy_type"], 0) + 1
    return matrix, defects, summary
