"""Mechanism registry: dispatch, unsupported reject, no UM contamination."""
from uepi_api.services.analytical_strategy_registry import (
    resolve_mechanism,
    resolve_strategy,
)
from uepi_api.services.reimbursement_whatif import run_reimbursement_whatif
from uepi_api.services.reimbursement_mppr import verify_known_answer as mppr_ka
from uepi_api.services.reimbursement_sos import verify_known_answer as sos_ka


def test_mppr_known_answer():
    assert mppr_ka()["passed"] is True


def test_sos_known_answer():
    assert sos_ka()["passed"] is True


def test_metadata_mechanism_wins_over_name():
    m = resolve_mechanism(
        policy_type="PRIOR_AUTH",
        policy_name="Outpatient MRI Prior Authorization",
        metadata={"enterprise_classification": {"mechanism": "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION"}},
    )
    assert m == "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION"


def test_mri_resolves_to_um():
    assert (
        resolve_mechanism(policy_type="PRIOR_AUTH", policy_name="Outpatient MRI Prior Authorization")
        == "UTILIZATION_MANAGEMENT"
    )


def test_payment_policy_does_not_default_to_um():
    s = resolve_strategy(policy_type="PAYMENT_POLICY", policy_name="Some Payment Rule")
    assert s["calculation_family"] == "REIMBURSEMENT"
    assert s["forbid_utilization_elasticity"] is True


def test_modifier_mechanism_rejected():
    s = resolve_strategy(
        policy_type="CODING_AND_BILLING",
        policy_name="Modifier and Code-Bundling Claim Edit Policy",
        metadata={"enterprise_classification": {"mechanism": "CODING_EDIT_MODIFIER"}},
    )
    assert s["dispatch"] == "REJECTED_UNSUPPORTED"
    assert s["forbid_utilization_elasticity"] is True


def test_mppr_whatif_sign_convention_additional_payer_savings():
    out = run_reimbursement_whatif(
        policy_type="PAYMENT_POLICY",
        policy_name="Multiple Procedure Payment Reduction",
        metadata={"enterprise_classification": {"mechanism": "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION"}},
        policy_id="d0eeb370-df14-4478-8755-dad6c3a35a47",
        scenario_params={"base_secondary_pct": 0.5, "secondary_pct": 0.4},
    )
    assert out["status"] == "completed"
    r = out["result"]
    assert r["impact_metrics"]["delta_payment_impact"] == 120.0
    assert r["impact_metrics"]["delta_payer_savings"] == 120.0
    assert r["impact_metrics"]["delta_provider_payment_change"] == -120.0
    assert r["baseline_metrics"]["utilization_change_per_1k"] is None
    assert r["not_utilization_elasticity"] is True


def test_sos_whatif_hospital_pct_70_increases_payer_savings():
    out = run_reimbursement_whatif(
        policy_type="PAYMENT_POLICY",
        policy_name="Hospital Outpatient Site Differential",
        metadata={
            "enterprise_classification": {"mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL"}
        },
        policy_id=None,
        scenario_params={"base_hospital_pct": 0.80, "hospital_pct": 0.70},
    )
    assert out["status"] == "completed"
    # hospital allowed 1200+900+500=2600; at 80% save 520; at 70% save 780; delta +260
    assert out["result"]["impact_metrics"]["delta_payment_impact"] == 260.0


def test_unenabled_fee_schedule_rejects_without_um_fallback():
    out = run_reimbursement_whatif(
        policy_type="REIMBURSEMENT_METHODOLOGY",
        policy_name="Facility Fee Schedule and Bundled Payment Adjustments",
        metadata={"enterprise_classification": {"mechanism": "FEE_SCHEDULE_UNIT_PRICE"}},
        policy_id=None,
        scenario_params={},
    )
    assert out["status"] == "rejected"
    assert "elasticity" in out["message"].lower() or "engine" in out["message"].lower() or "fee-schedule" in out["message"].lower()


def test_expansion_ptp_fixture_whatif_enabled():
    from uepi_api.services.expansion_demo_scenarios import PTP_POLICY_ID, PTP_NAME

    s = resolve_strategy(
        policy_type="CODING_AND_BILLING",
        policy_name=PTP_NAME,
        metadata={
            "enterprise_classification": {
                "mechanism": "CODING_EDIT_MODIFIER",
                "sub_mechanism": "NCCI_PTP",
                "dec4_expansion": True,
            }
        },
        policy_id=PTP_POLICY_ID,
    )
    assert s["dispatch"] == "ENGINE"
    assert s["mechanism"] == "NCCI_PTP_FIXTURE"
    out = run_reimbursement_whatif(
        policy_type="CODING_AND_BILLING",
        policy_name=PTP_NAME,
        metadata={
            "enterprise_classification": {
                "mechanism": "CODING_EDIT_MODIFIER",
                "sub_mechanism": "NCCI_PTP",
                "dec4_expansion": True,
            }
        },
        policy_id=PTP_POLICY_ID,
        scenario_params={},
    )
    assert out["status"] == "completed"
    # indicator 0 denies modifier bypass → +400 vs indicator 1
    assert out["result"]["impact_metrics"]["delta_payment_impact"] == 400.0


def test_expansion_mue_and_infusion_whatif():
    from uepi_api.services.expansion_demo_scenarios import (
        INFUSION_SOC_POLICY_ID,
        MUE_POLICY_ID,
        MUE_NAME,
        INFUSION_NAME,
    )

    mue = run_reimbursement_whatif(
        policy_type="CODING_AND_BILLING",
        policy_name=MUE_NAME,
        metadata={"enterprise_classification": {"mechanism": "FEE_SCHEDULE_UNIT_PRICE", "dec4_expansion": True}},
        policy_id=MUE_POLICY_ID,
        scenario_params={"base_mue_value": 4, "mue_value": 3},
    )
    assert mue["status"] == "completed"
    assert mue["result"]["impact_metrics"]["delta_payment_impact"] > 0

    inf = run_reimbursement_whatif(
        policy_type="SITE_OF_CARE",
        policy_name=INFUSION_NAME,
        metadata={
            "enterprise_classification": {
                "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
                "dec4_expansion": True,
            }
        },
        policy_id=INFUSION_SOC_POLICY_ID,
        scenario_params={"base_steer_hopd_count": 2, "steer_hopd_count": 3},
    )
    assert inf["status"] == "completed"
    assert inf["result"]["impact_metrics"]["delta_payment_impact"] == 1800.0
