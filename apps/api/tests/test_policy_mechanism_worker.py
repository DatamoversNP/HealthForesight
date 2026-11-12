"""Worker retry records a failure instead of fabricating a financial result."""
from uepi_worker.policy_mechanism_execution import run_policy_execution


def test_worker_retry_does_not_fabricate_a_result():
    package = {
        "policy_name": "Retry policy",
        "_key": "retry_policy",
        "identity": {"mechanism": "PRIOR_AUTH_UM", "family": "PRIOR_AUTH"},
        "codeset": {"status": "CANDIDATE_SCHEDULE", "codes": [{"code": "11111", "inclusion_status": "CANDIDATE_INCLUDE"}]},
        "rules": [{"id": "R2_NO_AUTO_DENY"}],
        "levers": [],
    }

    def explode(package, lines, execution_parameters=None):
        raise RuntimeError("warehouse unavailable")

    result = run_policy_execution(package, [], execute=explode)
    assert result["status"] == "FAILED"
    assert result["mechanism_executed"] is False
    assert result["financial_effect"] is None
    assert result["eligible_line_count"] is None
    assert result["attempt"] == 2
    assert result["continuation_used_as_execution"] is False
