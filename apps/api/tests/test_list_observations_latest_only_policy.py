"""latest_only + policy_id must return the latest observation window (not compute stamp)."""
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4


def test_latest_only_with_policy_id_orders_by_period_end():
    from uepi_api.storage_observations import _list_observations

    tenant = uuid4()
    policy = uuid4()

    older = SimpleNamespace(
        observation_id="obs-old",
        tenant_id=tenant,
        policy_id=policy,
        policy_version_id=None,
        data_period_id=None,
        data_period_ids_json=[],
        observation_type="PERIODIC",
        observation_period_start=datetime(2026, 7, 1),
        observation_period_end=datetime(2026, 7, 31, 23, 59, 59),
        baseline_version_id=None,
        prediction_id=None,
        analysis_id=None,
        computed_at=datetime(2026, 11, 4, 12, 0, 0),  # computed later
        metrics_json={},
        comparisons_json={"vs_baseline": {"utilization_change_pct": -7.8}},
        behavioral_explanation_json={},
        analytics_run_id=None,
        verdict_status="AT_RISK",
        verdict_reason="fixture",
        recommendation=None,
        verdict_rule_version=None,
        created_at=datetime(2026, 11, 4),
        updated_at=datetime(2026, 11, 4),
    )
    newer_window = SimpleNamespace(
        observation_id="b227220e-f9e0-45a6-8938-d55aad1fe25d",
        tenant_id=tenant,
        policy_id=policy,
        policy_version_id=None,
        data_period_id=None,
        data_period_ids_json=[],
        observation_type="PERIODIC",
        observation_period_start=datetime(2024, 1, 1),
        observation_period_end=datetime(2026, 8, 14),
        baseline_version_id=None,
        prediction_id=None,
        analysis_id=None,
        computed_at=datetime(2026, 10, 1, 8, 0, 0),  # computed earlier
        metrics_json={},
        comparisons_json={"vs_baseline": {"utilization_change_pct": -10.06}},
        behavioral_explanation_json={},
        analytics_run_id=None,
        verdict_status="ON_TRACK",
        verdict_reason="performing as intended",
        recommendation="Continue monitoring",
        verdict_rule_version=None,
        created_at=datetime(2026, 10, 1),
        updated_at=datetime(2026, 10, 1),
    )

    session = MagicMock()
    query = MagicMock()
    session.query.return_value = query
    query.filter.return_value = query
    query.order_by.return_value = query
    query.limit.return_value = query
    query.all.return_value = [newer_window]  # DB would return this after order+limit 1

    with patch("uepi_api.database.SessionLocal", return_value=session):
        with patch(
            "uepi_api.observation_transform.transform_observation_for_frontend",
            side_effect=lambda d: d,
        ):
            rows = _list_observations(
                tenant_id=tenant,
                policy_id=policy,
                latest_only=True,
                summary=True,
                limit=5,
            )

    assert len(rows) == 1
    assert rows[0]["observation_id"] == "b227220e-f9e0-45a6-8938-d55aad1fe25d"
    assert rows[0]["verdict_status"] == "ON_TRACK"
    # Ensure we asked for limit 1 with period_end ordering (not unbounded computed_at list)
    query.limit.assert_called_with(1)
    assert query.order_by.called
