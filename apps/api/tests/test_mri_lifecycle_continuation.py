"""API adapter wraps shared MRI lifecycle calculators."""

import importlib.util
import sys
from pathlib import Path

import pytest

_ADAPTER = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "uepi_api"
    / "services"
    / "policy_lifecycle_continuation.py"
)


def _load_adapter():
    # Load file directly to avoid uepi_api.services package side effects.
    spec = importlib.util.spec_from_file_location("policy_lifecycle_continuation", _ADAPTER)
    if spec is None or spec.loader is None:
        pytest.skip("adapter module unavailable")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"adapter import blocked: {exc}")
    return mod


_adapter = _load_adapter()
build_continuation_prediction_from_baseline = _adapter.build_continuation_prediction_from_baseline
build_observation_and_reconciliation = _adapter.build_observation_and_reconciliation
mri_reference_fixture_run = _adapter.mri_reference_fixture_run
whatif_continuation_exposure = _adapter.whatif_continuation_exposure


def test_adapter_continuation_and_unestimated_effect():
    built = build_continuation_prediction_from_baseline(
        eligible_services=14400,
        eligible_member_months=4_800_000,
        total_allowed=11_520_000,
        forecast_member_months_by_month=[405_000] * 12,
        freeze_timestamp="2025-12-31",
    )
    assert built["continuation"]["series"][0]["predicted_allowed"] == 972_000.0
    assert built["policy_effect"]["status"] == "UNESTIMATED"
    assert built["invariants"]["continuation_is_not_policy_effect"] is True


def test_adapter_observation_reconciliation_inconclusive():
    built = build_continuation_prediction_from_baseline(
        eligible_services=14400,
        eligible_member_months=4_800_000,
        total_allowed=11_520_000,
        forecast_member_months_by_month=[405_000],
        freeze_timestamp="2025-12-31",
    )
    result = build_observation_and_reconciliation(
        continuation=built["continuation"],
        month_index=1,
        observed_services=1170,
        observed_allowed=936_000,
        actual_member_months=407_000,
        authorization_events_present=False,
        endpoint_contract=None,
    )
    assert result["reconciliation"]["raw"]["allowed_variance"] == -36_000.0
    assert result["reconciliation"]["exposure_adjusted"]["expected_allowed"] == 976_800.0
    assert result["verdict"]["verdict"] == "INCONCLUSIVE"
    assert result["observations"]["authorization"]["status"] == "NOT_MEASURABLE"


def test_adapter_whatif_and_fixture():
    built = build_continuation_prediction_from_baseline(
        eligible_services=14400,
        eligible_member_months=4_800_000,
        total_allowed=11_520_000,
        forecast_member_months_by_month=[405_000] * 12,
        freeze_timestamp="2025-12-31",
    )
    whatif = whatif_continuation_exposure(
        built["continuation"],
        scenario_member_months=420_000,
        scenario_id="mri-420k",
    )
    assert whatif["scenario_continuation_allowed"] == 1_008_000.0
    fixture = mri_reference_fixture_run()
    assert fixture["acceptance_matrix"]["verdict"] == "INCONCLUSIVE"
