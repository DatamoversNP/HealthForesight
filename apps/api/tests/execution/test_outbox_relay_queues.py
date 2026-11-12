"""Unit tests for outbox Service Bus queue mapping (no Azure)."""
from uepi_api.services.execution.outbox_relay import queue_for_workload


def test_interactive_maps_to_interactive_queue():
    assert queue_for_workload("INTERACTIVE") == "interactive"
    assert queue_for_workload("sync") == "interactive"


def test_async_maps_to_policy_analytics_queue():
    assert queue_for_workload("ASYNC_COHORT") == "policy-analytics"
    assert queue_for_workload("OBSERVATION") == "policy-analytics"
    assert queue_for_workload("") == "policy-analytics"
