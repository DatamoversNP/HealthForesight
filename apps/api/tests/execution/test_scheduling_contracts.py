"""Unit tests for scheduling contracts (no DB / no Azure)."""
from uepi_common.execution.scheduling import (
    OverlapPolicy,
    ScheduleDefinition,
    ScheduleTriggerKind,
)


def test_calendar_requires_expression():
    s = ScheduleDefinition(
        schedule_id="s1",
        tenant_id="t1",
        job_type="observation",
        target_reference="policy:x",
        schedule_expression="",
        timezone="America/New_York",
        trigger_kind=ScheduleTriggerKind.CALENDAR,
    )
    assert any("schedule_expression" in e for e in s.validate())


def test_data_event_allows_empty_cron():
    s = ScheduleDefinition(
        schedule_id="s2",
        tenant_id="t1",
        job_type="incremental_refresh",
        target_reference="snapshot:v1",
        schedule_expression="",
        timezone="UTC",
        trigger_kind=ScheduleTriggerKind.DATA_EVENT,
        required_data_watermark="claims_snapshot>=v2",
    )
    assert s.validate() == []


def test_overlap_policy_values():
    assert OverlapPolicy.SKIP.value == "SKIP"
