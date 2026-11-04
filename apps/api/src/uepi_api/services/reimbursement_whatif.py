"""Dispatch reimbursement what-if engines via analytical strategy registry."""
from __future__ import annotations

from typing import Any, Dict, Optional

from uepi_api.services.analytical_strategy_registry import (
    PAYMENT_SIGN_CONVENTION,
    resolve_strategy,
)


def run_reimbursement_whatif(
    *,
    policy_type: Optional[str],
    policy_name: Optional[str],
    metadata: Optional[Dict[str, Any]],
    policy_id: Optional[str],
    scenario_params: Dict[str, Any],
) -> Dict[str, Any]:
    """Return completed what-if result_dict or a REJECTED payload."""
    strategy = resolve_strategy(
        policy_type=policy_type,
        policy_name=policy_name,
        metadata=metadata,
        policy_id=policy_id,
    )
    if strategy.get("dispatch") != "ENGINE":
        return {
            "status": "rejected",
            "strategy": strategy,
            "message": strategy.get("reason")
            or strategy.get("notes")
            or "Unsupported analytical mechanism for what-if",
        }
    if strategy.get("calculation_family") != "REIMBURSEMENT":
        return {
            "status": "not_reimbursement",
            "strategy": strategy,
        }

    mechanism = strategy["mechanism"]
    if mechanism == "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION":
        from uepi_api.services.reimbursement_mppr import (
            CALC_VERSION,
            KNOWN_ANSWER_LINES,
            apply_mppr,
        )

        base_pct = float(scenario_params.get("base_secondary_pct", 0.5))
        alt_pct = float(
            scenario_params.get("secondary_pct")
            or scenario_params.get("mppr_secondary_pct")
            or 0.4
        )
        base_tot = apply_mppr(KNOWN_ANSWER_LINES, secondary_pct=base_pct)["totals"]
        alt_tot = apply_mppr(KNOWN_ANSWER_LINES, secondary_pct=alt_pct)["totals"]
        delta = round(alt_tot["payment_impact"] - base_tot["payment_impact"], 2)
        return {
            "status": "completed",
            "strategy": strategy,
            "result": {
                "scenario_id": f"mppr-whatif-{CALC_VERSION}",
                "mechanism": mechanism,
                "engine_id": strategy["engine_id"],
                "calculation_version": CALC_VERSION,
                "registry_version": strategy["registry_version"],
                "catalog_class": "DEMO_SYNTHETIC",
                "not_utilization_elasticity": True,
                "sign_convention": PAYMENT_SIGN_CONVENTION,
                "baseline_metrics": {
                    "total_paid_baseline_window": base_tot["baseline_paid"],
                    "post_policy_paid": base_tot["post_policy_paid"],
                    "payment_impact": base_tot["payment_impact"],
                    "payer_savings": base_tot["payer_savings"],
                    "provider_payment_change": base_tot["provider_payment_change"],
                    "secondary_pct": base_pct,
                    "utilization_change_pct": None,
                    "utilization_change_per_1k": None,
                    "volume_units": base_tot["volume_units"],
                    "reconciliation": base_tot["reconciliation"],
                },
                "projected_metrics": {
                    "post_policy_paid": alt_tot["post_policy_paid"],
                    "payment_impact": alt_tot["payment_impact"],
                    "payer_savings": alt_tot["payer_savings"],
                    "provider_payment_change": alt_tot["provider_payment_change"],
                    "secondary_pct": alt_pct,
                    "utilization_change_pct": None,
                    "utilization_change_per_1k": None,
                    "volume_units": alt_tot["volume_units"],
                    "reconciliation": alt_tot["reconciliation"],
                },
                "impact_metrics": {
                    "delta_payment_impact": delta,
                    "delta_payer_savings": delta,
                    "delta_provider_payment_change": round(-delta, 2),
                    "price_effect_delta": delta,
                    "volume_effect": 0.0,
                    "mix_effect": 0.0,
                },
                "confidence_intervals": {},
                "confidence_score": 1.0,
                "sensitivity_analysis": {
                    "secondary_pct_base": base_pct,
                    "secondary_pct_alt": alt_pct,
                },
                "limitations": [
                    "Deterministic known-answer fixture — not empirical payer claims.",
                    "Does not use utilization elasticity (MRI UM formula).",
                ],
            },
        }

    if mechanism == "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL":
        # Infusion SOC expansion vs freestanding imaging SOS — dispatch by policy identity
        from uepi_api.services.expansion_demo_scenarios import (
            INFUSION_SOC_POLICY_ID,
            INFUSION_KNOWN,
            apply_infusion_soc,
            INFUSION_CALC_VERSION,
            INFUSION_NAME,
        )

        is_infusion = (policy_id == INFUSION_SOC_POLICY_ID) or (
            (policy_name or "").upper().find("INFUSION") >= 0
        )
        if is_infusion:
            base_steer = int(scenario_params.get("base_steer_hopd_count", 2))
            alt_steer = int(
                scenario_params.get("steer_hopd_count")
                or scenario_params.get("infusion_steer_hopd_count")
                or 3
            )
            # Known fixture: 2 of 3 HOPD steered; alt steers all 3 HOPD → +1800 savings
            base_tot = apply_infusion_soc(INFUSION_KNOWN, steer_hopd_count=base_steer)["totals"]
            alt_tot = apply_infusion_soc(INFUSION_KNOWN, steer_hopd_count=alt_steer)["totals"]
            delta = round(alt_tot["payment_impact"] - base_tot["payment_impact"], 2)
            return {
                "status": "completed",
                "strategy": strategy,
                "result": {
                    "scenario_id": f"infusion-soc-whatif-{INFUSION_CALC_VERSION}",
                    "mechanism": mechanism,
                    "sub_mechanism": "INFUSION_SITE_OF_CARE",
                    "engine_id": "reimbursement_infusion_soc_v1",
                    "calculation_version": INFUSION_CALC_VERSION,
                    "registry_version": strategy["registry_version"],
                    "catalog_class": "DEMO_SYNTHETIC",
                    "policy_name": INFUSION_NAME,
                    "not_utilization_elasticity": True,
                    "sign_convention": PAYMENT_SIGN_CONVENTION,
                    "baseline_metrics": {
                        "total_paid_baseline_window": base_tot["baseline_paid"],
                        "post_policy_paid": base_tot["post_policy_paid"],
                        "payment_impact": base_tot["payment_impact"],
                        "payer_savings": base_tot["payer_savings"],
                        "provider_payment_change": base_tot["provider_payment_change"],
                        "steer_hopd_count": base_steer,
                        "episodes_steered": base_tot.get("episodes_steered"),
                    },
                    "projected_metrics": {
                        "post_policy_paid": alt_tot["post_policy_paid"],
                        "payment_impact": alt_tot["payment_impact"],
                        "payer_savings": alt_tot["payer_savings"],
                        "provider_payment_change": alt_tot["provider_payment_change"],
                        "steer_hopd_count": alt_steer,
                        "episodes_steered": alt_tot.get("episodes_steered"),
                    },
                    "impact_metrics": {
                        "delta_payment_impact": delta,
                        "delta_payer_savings": delta,
                        "delta_provider_payment_change": round(-delta, 2),
                        "price_effect_delta": delta,
                        "volume_effect": 0.0,
                        "mix_effect": 0.0,
                    },
                    "confidence_score": 1.0,
                    "limitations": [
                        "Deterministic infusion SOC fixture — not empirical drug-site claims.",
                    ],
                },
            }

        from uepi_api.services.reimbursement_sos import (
            CALC_VERSION,
            KNOWN_ANSWER_LINES,
            apply_sos,
        )

        base_pct = float(scenario_params.get("base_hospital_pct", 0.80))
        alt_pct = float(
            scenario_params.get("hospital_pct")
            or scenario_params.get("sos_hospital_pct")
            or 0.70
        )
        base_tot = apply_sos(KNOWN_ANSWER_LINES, hospital_pct=base_pct)["totals"]
        alt_tot = apply_sos(KNOWN_ANSWER_LINES, hospital_pct=alt_pct)["totals"]
        delta = round(alt_tot["payment_impact"] - base_tot["payment_impact"], 2)
        return {
            "status": "completed",
            "strategy": strategy,
            "result": {
                "scenario_id": f"sos-whatif-{CALC_VERSION}",
                "mechanism": mechanism,
                "engine_id": strategy["engine_id"],
                "calculation_version": CALC_VERSION,
                "registry_version": strategy["registry_version"],
                "catalog_class": "DEMO_SYNTHETIC",
                "not_utilization_elasticity": True,
                "sign_convention": PAYMENT_SIGN_CONVENTION,
                "baseline_metrics": {
                    "post_policy_paid": base_tot["post_policy_paid"],
                    "payment_impact": base_tot["payment_impact"],
                    "payer_savings": base_tot["payer_savings"],
                    "provider_payment_change": base_tot["provider_payment_change"],
                    "hospital_pct": base_pct,
                    "utilization_change_pct": None,
                    "volume_units": base_tot["volume_units"],
                    "reconciliation": base_tot["reconciliation"],
                },
                "projected_metrics": {
                    "post_policy_paid": alt_tot["post_policy_paid"],
                    "payment_impact": alt_tot["payment_impact"],
                    "payer_savings": alt_tot["payer_savings"],
                    "provider_payment_change": alt_tot["provider_payment_change"],
                    "hospital_pct": alt_pct,
                    "utilization_change_pct": None,
                    "volume_units": alt_tot["volume_units"],
                    "reconciliation": alt_tot["reconciliation"],
                },
                "impact_metrics": {
                    "delta_payment_impact": delta,
                    "delta_payer_savings": delta,
                    "delta_provider_payment_change": round(-delta, 2),
                    "price_effect_delta": delta,
                    "volume_effect": 0.0,
                    "mix_effect": 0.0,
                },
                "confidence_intervals": {},
                "confidence_score": 1.0,
                "sensitivity_analysis": {
                    "hospital_pct_base": base_pct,
                    "hospital_pct_alt": alt_pct,
                },
                "limitations": [
                    "Deterministic known-answer fixture — not empirical site differentials.",
                    "Does not use utilization elasticity.",
                ],
            },
        }

    if mechanism == "NCCI_PTP_FIXTURE":
        from uepi_api.services.expansion_demo_scenarios import (
            PTP_CALC_VERSION,
            PTP_KNOWN_LINES,
            apply_ncci_ptp,
        )

        base = apply_ncci_ptp(PTP_KNOWN_LINES, modifier_indicator="1")["totals"]
        # Alt: indicator 0 → no modifier bypass (claim4 column2 also denied) → +400 savings
        alt = apply_ncci_ptp(PTP_KNOWN_LINES, modifier_indicator="0")["totals"]
        delta = round(alt["payment_impact"] - base["payment_impact"], 2)
        return {
            "status": "completed",
            "strategy": strategy,
            "result": {
                "scenario_id": f"ptp-whatif-{PTP_CALC_VERSION}",
                "mechanism": mechanism,
                "engine_id": "reimbursement_ncci_ptp_v1",
                "calculation_version": PTP_CALC_VERSION,
                "registry_version": strategy["registry_version"],
                "catalog_class": "DEMO_SYNTHETIC",
                "not_utilization_elasticity": True,
                "sign_convention": PAYMENT_SIGN_CONVENTION,
                "baseline_metrics": {
                    "total_paid_baseline_window": base["baseline_paid"],
                    "post_policy_paid": base["post_policy_paid"],
                    "payment_impact": base["payment_impact"],
                    "payer_savings": base["payer_savings"],
                    "provider_payment_change": base["provider_payment_change"],
                    "modifier_indicator": "1",
                    "ptp_pairs_hit": base["ptp_pairs_hit"],
                    "ptp_pairs_bypassed_with_modifier": base["ptp_pairs_bypassed_with_modifier"],
                },
                "projected_metrics": {
                    "post_policy_paid": alt["post_policy_paid"],
                    "payment_impact": alt["payment_impact"],
                    "payer_savings": alt["payer_savings"],
                    "provider_payment_change": alt["provider_payment_change"],
                    "modifier_indicator": "0",
                    "ptp_pairs_hit": alt["ptp_pairs_hit"],
                    "ptp_pairs_bypassed_with_modifier": alt["ptp_pairs_bypassed_with_modifier"],
                },
                "impact_metrics": {
                    "delta_payment_impact": delta,
                    "delta_payer_savings": delta,
                    "delta_provider_payment_change": round(-delta, 2),
                    "price_effect_delta": delta,
                    "volume_effect": 0.0,
                    "mix_effect": 0.0,
                },
                "confidence_score": 1.0,
                "limitations": [
                    "Synthetic PTP fixture with modifier-indicator semantics.",
                    "Not reconciled against a full quarterly CMS PTP file (ACCESS_BLOCKED on this host).",
                    "Empirical claims_lines lack modifier column — DESIGN_POSSIBLE_DATA_INSUFFICIENT for production claims.",
                ],
            },
        }

    if mechanism == "FEE_SCHEDULE_UNIT_PRICE":
        from uepi_api.services.expansion_demo_scenarios import (
            MUE_CALC_VERSION,
            MUE_KNOWN_LINES,
            DEMO_MUE_VALUE,
            apply_ncci_mue,
            MUE_POLICY_ID,
            MUE_NAME,
        )

        # Prefer MUE fixture when this is the expansion MUE policy; generic fee schedule otherwise rejects
        is_mue = (policy_id == MUE_POLICY_ID) or (
            (policy_name or "").upper().find("MUE") >= 0
            or (policy_name or "").upper().find("MEDICALLY UNLIKELY") >= 0
        )
        if not is_mue:
            return {
                "status": "rejected",
                "strategy": strategy,
                "message": "Generic fee-schedule what-if not enabled; MUE expansion fixture only.",
            }
        base_mue = int(scenario_params.get("base_mue_value", DEMO_MUE_VALUE))
        alt_mue = int(scenario_params.get("mue_value") or scenario_params.get("alt_mue_value") or 3)
        base_tot = apply_ncci_mue(MUE_KNOWN_LINES, mue_value=base_mue)["totals"]
        alt_tot = apply_ncci_mue(MUE_KNOWN_LINES, mue_value=alt_mue)["totals"]
        delta = round(alt_tot["payment_impact"] - base_tot["payment_impact"], 2)
        return {
            "status": "completed",
            "strategy": strategy,
            "result": {
                "scenario_id": f"mue-whatif-{MUE_CALC_VERSION}",
                "mechanism": mechanism,
                "sub_mechanism": "NCCI_MUE",
                "engine_id": "reimbursement_ncci_mue_v1",
                "calculation_version": MUE_CALC_VERSION,
                "registry_version": strategy["registry_version"],
                "catalog_class": "DEMO_SYNTHETIC",
                "policy_name": MUE_NAME,
                "not_utilization_elasticity": True,
                "sign_convention": PAYMENT_SIGN_CONVENTION,
                "baseline_metrics": {
                    "total_paid_baseline_window": base_tot["baseline_paid"],
                    "post_policy_paid": base_tot["post_policy_paid"],
                    "payment_impact": base_tot["payment_impact"],
                    "payer_savings": base_tot["payer_savings"],
                    "provider_payment_change": base_tot["provider_payment_change"],
                    "mue_value": base_mue,
                    "lines_capped": base_tot.get("lines_capped"),
                },
                "projected_metrics": {
                    "post_policy_paid": alt_tot["post_policy_paid"],
                    "payment_impact": alt_tot["payment_impact"],
                    "payer_savings": alt_tot["payer_savings"],
                    "provider_payment_change": alt_tot["provider_payment_change"],
                    "mue_value": alt_mue,
                    "lines_capped": alt_tot.get("lines_capped"),
                },
                "impact_metrics": {
                    "delta_payment_impact": delta,
                    "delta_payer_savings": delta,
                    "delta_provider_payment_change": round(-delta, 2),
                    "price_effect_delta": delta,
                    "volume_effect": 0.0,
                    "mix_effect": 0.0,
                },
                "confidence_score": 1.0,
                "limitations": [
                    "SYNTHETIC MUE value — not an unpublished CMS confidential figure claimed as authoritative.",
                ],
            },
        }

    # Other reimbursement engines registered but not yet what-if-ready
    return {
        "status": "rejected",
        "strategy": strategy,
        "message": (
            f"Reimbursement mechanism {mechanism} is registered but what-if "
            "known-answer engine is not enabled; refusing UM elasticity fallback."
        ),
    }
