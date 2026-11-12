"""Prediction totals and observation sums stay separate functions."""

from uepi_api.services.synthetic_lifecycle import build_payment_lifecycle, observe_post_policy_events


def _lines():
    return [
        {
            "claim_id": "C1",
            "claim_line_id": "L1",
            "cpt_code": "27447",
            "allowed_amount": 1000.0,
            "paid_amount": 800.0,
            "units": 1,
            "place_of_service": "11",
        },
        {
            "claim_id": "C1",
            "claim_line_id": "L2",
            "cpt_code": "64483",
            "allowed_amount": 400.0,
            "paid_amount": 320.0,
            "units": 1,
            "place_of_service": "11",
        },
    ]


def test_observation_sum_matches_prediction_without_reading_it():
    built = build_payment_lifecycle("mppr", _lines())
    summed = observe_post_policy_events(built["events"])
    assert built["prediction"]["source"] == "payment_engine_totals"
    assert summed["source"] == "sum_of_synthetic_post_policy_events"
    assert built["prediction"]["predicted_allowed"] == 1200
    assert summed["observed_allowed"] == 1200
    assert built["reconciliation_status"] == "MATCH"
    assert built["oracle_match"] is True
    assert built["prediction"]["confidence_score"] is None


def test_site_of_service_events_reconcile():
    lines = [
        {
            "claim_id": "S1",
            "claim_line_id": "A",
            "cpt_code": "72148",
            "allowed_amount": 1000.0,
            "paid_amount": 800.0,
            "units": 1,
            "place_of_service": "22",
        }
    ]
    built = build_payment_lifecycle("sos", lines)
    assert built["prediction"]["predicted_allowed"] == 800
    assert built["observation"]["observed_allowed"] == 800
    assert built["observation"]["observed_plan_paid"] == 640


def test_clinical_key_is_rejected():
    try:
        build_payment_lifecycle("mri", _lines())
    except ValueError:
        return
    raise AssertionError("clinical policy must not build a payment lifecycle")
