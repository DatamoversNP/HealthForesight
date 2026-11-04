#!/usr/bin/env python3
"""Seed Site-of-Service payment differential vertical (known-answer).

Policy: Freestanding Imaging Steerage — analytical mechanism stamped as
SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL (payment price effect, not UM elasticity).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT / "packages" / "common" / "src"))
env_path = ROOT / ".env.demo7867"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from uepi_api.services.reimbursement_sos import (  # noqa: E402
    CALC_VERSION,
    KNOWN_ANSWER_LINES,
    apply_sos,
    verify_known_answer,
)
from uepi_api.storage_baselines import create_baseline  # noqa: E402
from uepi_api.storage_observations import create_observation  # noqa: E402
from uepi_api.models.policy import Policy  # noqa: E402
from uepi_api.models.baseline import Baseline  # noqa: E402
from uepi_api.models.observation import Observation  # noqa: E402
from uepi_api.models.predicted_impact import PolicyPredictedImpact  # noqa: E402
from uepi_api.database import SessionLocal  # noqa: E402

TENANT = UUID("00000000-0000-0000-0000-000000000001")
POLICY_ID = UUID("d7441dd9-3bfe-405e-ae6c-0377204bbb7e")
POLICY_NAME = "Freestanding Imaging Steerage"
EVIDENCE = ROOT / "docs" / "demo" / "bcbs-nc" / "evidence"


def main() -> int:
    ka = verify_known_answer()
    if not ka["passed"]:
        print("FAILED", ka)
        return 2
    totals = apply_sos(KNOWN_ANSWER_LINES)["totals"]
    now = datetime.now(timezone.utc)

    db = SessionLocal()
    try:
        policy = db.query(Policy).filter(Policy.id == POLICY_ID, Policy.tenant_id == TENANT).one()
        meta = dict(policy.policy_metadata_json or {})
        meta["enterprise_classification"] = {
            **(meta.get("enterprise_classification") or {}),
            "catalog_class": "DEMO_SYNTHETIC",
            "display_label": "Representative Payer Policies",
            "not_verbatim_bcbsnc_policy": True,
            "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
            "lifecycle_validation": "FULLY_VALIDATED_DEMO",
            "calculation_version": CALC_VERSION,
        }
        meta["analytical_strategy"] = {
            "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
            "engine_id": "reimbursement_sos_v1",
            "calculation_version": CALC_VERSION,
            "registry_version": "analytical-strategy-registry-v1",
        }
        policy.policy_metadata_json = meta
        db.add(policy)
        db.commit()
    finally:
        db.close()

    # Also ensure MPPR metadata has strategy stamp
    db = SessionLocal()
    try:
        mppr = (
            db.query(Policy)
            .filter(Policy.name == "Multiple Procedure Payment Reduction", Policy.tenant_id == TENANT)
            .one()
        )
        m = dict(mppr.policy_metadata_json or {})
        m["enterprise_classification"] = {
            **(m.get("enterprise_classification") or {}),
            "mechanism": "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION",
            "catalog_class": "DEMO_SYNTHETIC",
            "lifecycle_validation": "FULLY_VALIDATED_DEMO",
        }
        m["analytical_strategy"] = {
            "mechanism": "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION",
            "engine_id": "reimbursement_mppr_v1",
            "calculation_version": "reimbursement-mppr-v1",
            "registry_version": "analytical-strategy-registry-v1",
        }
        mppr.policy_metadata_json = m
        db.add(mppr)
        db.commit()
    finally:
        db.close()

    baseline_metrics = {
        "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
        "calculation_version": CALC_VERSION,
        "catalog_class": "DEMO_SYNTHETIC",
        "total_allowed": totals["baseline_allowed"],
        "total_paid": totals["baseline_paid"],
        "hospital_lines": totals["hospital_lines"],
        "freestanding_lines": totals["freestanding_lines"],
        "volume_units": totals["volume_units"],
        "primary_metric": "allowed_paid_unit_price",
        "not_utilization_model": True,
        "sign_convention": "payment_impact = payer_savings (positive = payer pays less)",
        "fixture": "KNOWN_ANSWER_LINES",
    }
    bid = f"sos-ka-baseline-{CALC_VERSION}"
    db = SessionLocal()
    try:
        existing = db.query(Baseline).filter(Baseline.baseline_id == bid, Baseline.tenant_id == TENANT).first()
        if existing:
            existing.baseline_metrics_json = baseline_metrics
            existing.policy_id = POLICY_ID
            existing.computed_at = now.replace(tzinfo=None)
            db.add(existing)
            db.commit()
            db.refresh(existing)
            baseline = {"id": str(existing.id), "baseline_id": existing.baseline_id}
        else:
            baseline = None
    finally:
        db.close()
    if baseline is None:
        baseline = create_baseline(
            TENANT,
            {
                "baseline_id": bid,
                "policy_id": str(POLICY_ID),
                "baseline_type": "POLICY_SPECIFIC",
                "window_start_date": "2025-01-01T00:00:00+00:00",
                "window_end_date": "2025-12-31T23:59:59+00:00",
                "computed_at": now.isoformat(),
                "baseline_metrics": baseline_metrics,
            },
            input_refs={"fixture": "KNOWN_ANSWER_LINES", "calculation_version": CALC_VERSION},
            config_snapshot={"hospital_pct": 0.8},
        )

    db = SessionLocal()
    try:
        pred = (
            db.query(PolicyPredictedImpact)
            .filter(
                PolicyPredictedImpact.policy_id == POLICY_ID,
                PolicyPredictedImpact.prediction_method == "SOS_PAYMENT_RULE",
            )
            .order_by(PolicyPredictedImpact.predicted_at.desc())
            .first()
        )
        metrics = {
            "metrics": {
                "payment_impact": totals["payment_impact"],
                "payer_savings": totals["payer_savings"],
                "provider_payment_change": totals["provider_payment_change"],
                "payment_impact_pct": totals["payment_impact_pct"],
                "baseline_paid": totals["baseline_paid"],
                "post_policy_paid": totals["post_policy_paid"],
                "volume_effect": 0.0,
                "mix_effect": 0.0,
                "price_effect": totals["reconciliation"]["price_effect"],
                "prediction_method": "SOS_PAYMENT_RULE",
                "utilization_change_pct": None,
                "utilization_change_per_1k": None,
            },
            "sign_convention": {
                "payment_impact": "Payer savings; positive = payer pays less",
            },
            "model_versions": {"reimbursement_sos": CALC_VERSION},
            "limitations": ["Synthetic known-answer; not empirical site differentials."],
        }
        if pred:
            pred.metrics_json = metrics
            pred.model_version = CALC_VERSION
            pred.confidence = 1.0
            db.add(pred)
            db.commit()
            db.refresh(pred)
        else:
            pred = PolicyPredictedImpact(
                tenant_id=TENANT,
                policy_id=POLICY_ID,
                metrics_json=metrics,
                model_version=CALC_VERSION,
                confidence=1.0,
                predicted_at=now.replace(tzinfo=None),
                prediction_method="SOS_PAYMENT_RULE",
            )
            db.add(pred)
            db.commit()
            db.refresh(pred)
        pred_id = str(pred.id)
    finally:
        db.close()

    obs_id = f"sos-ka-obs-{CALC_VERSION}"
    obs_metrics = {
        "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
        "calculation_version": CALC_VERSION,
        "total_paid": totals["post_policy_paid"],
        "baseline_paid": totals["baseline_paid"],
        "payment_impact": totals["payment_impact"],
        "payer_savings": totals["payer_savings"],
        "provider_payment_change": totals["provider_payment_change"],
        "reconciliation": totals["reconciliation"],
        "known_answer_match": True,
        "utilization_unchanged": True,
    }
    db = SessionLocal()
    try:
        obs = db.query(Observation).filter(Observation.observation_id == obs_id).first()
        if obs:
            obs.metrics_json = obs_metrics
            obs.verdict_status = "ON_TRACK"
            obs.verdict_reason = (
                f"SOS known-answer match ({CALC_VERSION}); payer savings "
                f"${totals['payment_impact']}; volume held constant."
            )
            obs.prediction_id = UUID(pred_id)
            db.add(obs)
            db.commit()
        else:
            obs = None
    finally:
        db.close()
    if obs is None:
        create_observation(
            TENANT,
            {
                "observation_id": obs_id,
                "policy_id": str(POLICY_ID),
                "prediction_id": pred_id,
                "baseline_version_id": baseline.get("id"),
                "observation_type": "AD_HOC",
                "observation_period_start": "2026-01-01T00:00:00+00:00",
                "observation_period_end": "2026-03-31T23:59:59+00:00",
                "computed_at": now.isoformat(),
                "metrics_json": obs_metrics,
                "comparisons_json": {
                    "vs_predicted": {"payment_delta": 0.0, "match": True},
                    "vs_baseline": {"payment_delta": -totals["payment_impact"]},
                },
                "verdict_status": "ON_TRACK",
                "verdict_reason": f"SOS known-answer match ({CALC_VERSION})",
                "verdict_rule_version": "sos-demo-v1",
            },
        )

    whatif = {
        "base_hospital_pct": 0.80,
        "alt_hospital_pct": 0.70,
        "base": apply_sos(KNOWN_ANSWER_LINES, hospital_pct=0.80)["totals"],
        "alt": apply_sos(KNOWN_ANSWER_LINES, hospital_pct=0.70)["totals"],
    }
    whatif["delta_payment_impact"] = round(
        whatif["alt"]["payment_impact"] - whatif["base"]["payment_impact"], 2
    )

    out = {
        "generated_at": now.isoformat(),
        "policy_id": str(POLICY_ID),
        "policy_name": POLICY_NAME,
        "validation_class": "FULLY_VALIDATED_DEMO",
        "mechanism": "SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL",
        "known_answer": ka,
        "predicted_impact_id": pred_id,
        "baseline_id": baseline.get("baseline_id"),
        "observation_id": obs_id,
        "verdict": "ON_TRACK",
        "what_if": whatif,
        "totals": totals,
        "sign_convention": {
            "payment_impact": "Payer savings; positive = payer pays less",
            "delta_payment_impact": "Additional payer savings vs base scenario",
        },
        "honesty": {
            "catalog_class": "DEMO_SYNTHETIC",
            "not_utilization_elasticity": True,
        },
    }
    path = EVIDENCE / "SOS_REIMBURSEMENT_VERTICAL.json"
    path.write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({"ok": True, "path": str(path), "payment_impact": totals["payment_impact"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
