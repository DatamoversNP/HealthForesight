"""Independent financial checks for MPPR reimbursement demo (not UM elasticity)."""
from uepi_api.services.reimbursement_mppr import (
    KNOWN_ANSWER_EXPECTED,
    apply_mppr,
    verify_known_answer,
)


def test_mppr_known_answer_passes():
    out = verify_known_answer()
    assert out["passed"] is True
    assert out["checks"]["volume_effect_zero"] is True
    assert out["checks"]["price_equals_impact"] is True


def test_mppr_does_not_use_utilization_fields():
    result = apply_mppr(
        [
            {"claim_id": "X", "claim_line_id": "1", "cpt_code": "10000", "allowed_amount": 200},
            {"claim_id": "X", "claim_line_id": "2", "cpt_code": "10001", "allowed_amount": 100},
        ]
    )
    assert "utilization_change_per_1k" not in result["totals"]
    assert result["totals"]["payment_impact"] == 50.0
    assert result["totals"]["reconciliation"]["volume_effect"] == 0.0
    assert result["mechanism"] == "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION"


def test_single_line_claim_no_reduction():
    result = apply_mppr(
        [{"claim_id": "S", "claim_line_id": "1", "cpt_code": "99213", "allowed_amount": 90}]
    )
    assert result["totals"]["payment_impact"] == 0.0
    assert result["totals"]["secondary_lines_reduced"] == 0


def test_expected_constants_document_demo_math():
    # Guard against silent drift of the published known-answer table
    assert KNOWN_ANSWER_EXPECTED["payment_impact"] == 600.0
    assert KNOWN_ANSWER_EXPECTED["baseline_paid"] == 3150.0
