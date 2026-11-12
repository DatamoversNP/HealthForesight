"""Execution contracts fail closed and match an independent oracle."""
from uepi_common.policy_execution.engine import execute_configured_policy
from uepi_common.policy_execution.oracle import (
    expected_quantity_from_lines,
    expected_review_from_lines,
)


def _package(**overrides):
    package = {
        "policy_name": "Example review policy",
        "package_version": "v1",
        "_key": "example_review",
        "identity": {"mechanism": "PRIOR_AUTH_UM", "family": "PRIOR_AUTH"},
        "codeset": {
            "status": "CANDIDATE_SCHEDULE",
            "codes": [
                {"code": "72148", "inclusion_status": "CANDIDATE_INCLUDE"},
                {"code": "77049", "inclusion_status": "EXCLUDE"},
            ],
        },
        "rules": [
            {"id": "R1_APPLICABILITY"},
            {"id": "R2_NO_AUTO_DENY"},
        ],
        "levers": [{"parameters": {"codes": ["72148"], "requires_pa": True}}],
    }
    package.update(overrides)
    return package


def test_review_rule_does_not_change_payment_and_matches_oracle():
    lines = [
        {"cpt_code": "72148", "member_id": "m1", "allowed_amount": 100, "paid_amount": 80, "units": 1},
        {"cpt_code": "99213", "member_id": "m2", "allowed_amount": 50, "paid_amount": 40, "units": 1},
        {"hcpcs_code": "72148", "member_id": "m3", "allowed_amount": 25.5, "paid_amount": 20.4, "units": 1},
    ]
    result = execute_configured_policy(_package(), lines)
    expected = expected_review_from_lines(lines, ["72148"])
    assert result["status"] == "EXECUTABLE"
    assert result["mechanism_executed"] is True
    assert result["financial_effect"] is None
    assert result["payment_changed"] is False
    assert result["eligible_line_count"] == expected["eligible_line_count"] == 2
    assert result["eligible_allowed"] == expected["eligible_allowed"] == 125.5
    assert result["eligible_paid"] == expected["eligible_paid"] == 100.4
    assert result["excluded_line_count"] == 1


def test_missing_codes_and_clinical_rules_stay_blocked():
    no_code = _package(codeset={"status": "NOT_APPLICABLE", "codes": [], "not_applicable_reason": "no schedule"})
    blocked = execute_configured_policy(no_code, [{"cpt_code": "72148", "allowed_amount": 10, "paid_amount": 8}])
    assert blocked["status"] == "BLOCKED"
    assert blocked["blocked_reason"] == "NO_CANDIDATE_CODE_IN_PACKAGE"
    assert blocked["eligible_line_count"] is None
    assert blocked["mechanism_executed"] is False

    clinical = _package(identity={"mechanism": "MEDICAL_NECESSITY_COVERAGE", "family": "COVERAGE"})
    clinical_result = execute_configured_policy(clinical, [{"cpt_code": "72148", "allowed_amount": 10, "paid_amount": 8}])
    assert clinical_result["blocked_reason"] == "UNSIGNED_CLINICAL_OR_COVERAGE_AUTHORITY"
    assert clinical_result["financial_effect"] is None


def test_quantity_limit_requires_a_configured_parameter_and_matches_oracle():
    package = _package(identity={"mechanism": "PHARMACY_SPECIALTY", "family": "QUANTITY_LIMIT"})
    missing = execute_configured_policy(package, [{"cpt_code": "72148", "units": 8, "allowed_amount": 80, "paid_amount": 64}])
    assert missing["blocked_reason"] == "MISSING_QUANTITY_LIMIT"
    assert missing["eligible_line_count"] is None

    lines = [
        {"cpt_code": "72148", "member_id": "m1", "units": 8, "allowed_amount": 80, "paid_amount": 64},
        {"cpt_code": "72148", "member_id": "m2", "units": 2, "allowed_amount": 20, "paid_amount": 16},
        {"cpt_code": "99213", "member_id": "m3", "units": 9, "allowed_amount": 90, "paid_amount": 72},
    ]
    result = execute_configured_policy(package, lines, {"quantity_limit_units": 4})
    expected = expected_quantity_from_lines(lines, ["72148"], 4)
    assert result["status"] == "EXECUTABLE"
    assert result["financial_effect"] == expected["financial_effect"] == 40.0
    assert result["exceeds_limit_count"] == expected["exceeds_limit_count"] == 1
    assert result["eligible_allowed_after"] == expected["eligible_allowed_after"] == 60.0
    assert "not a contracted" in result["financial_effect_label"].lower()


def test_second_client_configuration_uses_the_same_engine():
    """A different client policy and population must not require an engine code change."""
    client_b = {
        "policy_name": "Client B visit cap",
        "package_version": "client-b-v1",
        "_key": "client_b_visits",
        "identity": {"mechanism": "BENEFIT_ELIGIBILITY", "family": "QUANTITY_LIMIT"},
        "codeset": {
            "status": "CANDIDATE_SCHEDULE",
            "codes": [{"code": "99213", "inclusion_status": "CANDIDATE_INCLUDE"}],
        },
        "rules": [],
        "levers": [{"parameters": {}}],
    }
    lines = [
        {"cpt_code": "99213", "member_id": "b1", "units": 6, "allowed_amount": 120, "paid_amount": 96},
        {"cpt_code": "99214", "member_id": "b2", "units": 6, "allowed_amount": 150, "paid_amount": 120},
    ]
    result = execute_configured_policy(client_b, lines, {"quantity_limit_units": 3})
    expected = expected_quantity_from_lines(lines, ["99213"], 3)
    assert result["policy_name"] == "Client B visit cap"
    assert result["candidate_codes"] == ["99213"]
    assert result["financial_effect"] == expected["financial_effect"] == 60.0
    assert result["eligible_line_count"] == 1


def test_validated_payment_key_is_not_a_review_or_continuation():
    package = _package(_key="mppr", identity={"mechanism": "PAYMENT_REIMBURSEMENT", "family": "PAYMENT_POLICY"})
    result = execute_configured_policy(package, [{"cpt_code": "27447", "allowed_amount": 1000, "paid_amount": 800}])
    assert result["mechanism"] == "VALIDATED_PAYMENT_ENGINE"
    assert result["mechanism"] != "CONTINUATION_COMPARISON"
    assert result["financial_effect"] is None


def test_payment_family_without_a_parameter_is_blocked():
    package = _package(
        _key="assistant_surgeon",
        identity={"mechanism": "PAYMENT_REIMBURSEMENT", "family": "PAYMENT_POLICY"},
    )
    result = execute_configured_policy(package, [{"cpt_code": "72148", "allowed_amount": 100, "paid_amount": 80}])
    assert result["blocked_reason"] == "MISSING_PAYMENT_PARAMETER"
    assert result["financial_effect"] is None
