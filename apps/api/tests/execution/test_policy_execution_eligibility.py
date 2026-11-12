"""Fail-closed claims execution eligibility after 250-policy remediation."""
from uepi_api.services.policy_execution_eligibility import claims_execution_allowed
from uepi_api.services.policy_scoped_data_generation import build_policy_claims_filters


def test_blocked_remediation_clears_code_filters():
    policy = {
        "id": "00000000-0000-0000-0000-000000000099",
        "name": "Example",
        "scope": {"procedure_codes": ["72148"], "lob": ["COMMERCIAL"], "markets": ["NC"]},
        "policy_levers": [{"lever_type": "PRIOR_AUTH", "targets": {"codes": ["72148"]}}],
        "policy_metadata_json": {
            "scope": {"procedure_codes": ["72148"], "lob": ["COMMERCIAL"], "markets": ["NC"]},
            "policy_levers": [{"lever_type": "PRIOR_AUTH", "targets": {"codes": ["72148"]}}],
            "remediation": {
                "register_status": "BLOCK_CLAIMS_EXECUTION_PENDING_REMAP",
                "execution_eligibility": "BLOCKED",
                "code_mapping_state": "UNVERIFIED_CODE_MAPPING",
                "claims_execution_blocked": True,
            },
        },
    }
    allowed, reason = claims_execution_allowed(policy)
    assert allowed is False
    assert "blocked" in reason
    pf = build_policy_claims_filters(policy)
    assert pf["claims_execution_blocked"] is True
    assert pf["procedure_codes"] is None
    assert pf["cpt_codes"] is None


def test_legacy_policy_without_remediation_still_allowed():
    policy = {
        "scope": {"procedure_codes": ["72148"]},
        "policy_levers": [],
        "policy_metadata_json": {"scope": {"procedure_codes": ["72148"]}},
    }
    allowed, reason = claims_execution_allowed(policy)
    assert allowed is True
    assert reason == "no_remediation_envelope"
    pf = build_policy_claims_filters(policy)
    assert pf.get("claims_execution_blocked") is False
    assert "72148" in (pf.get("procedure_codes") or [])
