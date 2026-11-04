#!/usr/bin/env python3
"""Seed / validate Multiple Procedure Payment Reduction reimbursement vertical.

Uses deterministic known-answer claim lines (not MRI utilization elasticity).
Persists mechanism-specific baseline → prediction → observation → verdict.
Labels all evidence DEMO_SYNTHETIC / Representative Payer.
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

# Load demo env if present
env_path = ROOT / ".env.demo7867"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from uepi_api.services.reimbursement_mppr import (  # noqa: E402
    CALC_VERSION,
    KNOWN_ANSWER_LINES,
    apply_mppr,
    verify_known_answer,
)
from uepi_api.storage_baselines import create_baseline  # noqa: E402
from uepi_api.storage_observations import create_observation  # noqa: E402
from uepi_api.storage_policy_predicted_impact import store_predicted_impact  # noqa: E402
from uepi_api.database import SessionLocal  # noqa: E402
from uepi_api.models.policy import Policy  # noqa: E402
from uepi_api.models.baseline import Baseline  # noqa: E402
from uepi_api.models.observation import Observation  # noqa: E402

TENANT = UUID("00000000-0000-0000-0000-000000000001")
POLICY_NAME = "Multiple Procedure Payment Reduction"
EVIDENCE = ROOT / "docs" / "demo" / "bcbs-nc" / "evidence"


def main() -> int:
    ka = verify_known_answer()
    if not ka["passed"]:
        print("KNOWN_ANSWER_FAILED", json.dumps(ka, indent=2))
        return 2

    result = apply_mppr(KNOWN_ANSWER_LINES)
    totals = result["totals"]

    db = SessionLocal()
    try:
        policy = (
            db.query(Policy)
            .filter(Policy.tenant_id == TENANT, Policy.name == POLICY_NAME)
            .one()
        )
        policy_id = policy.id
        meta = dict(policy.policy_metadata_json or {})
        meta["enterprise_classification"] = {
            **(meta.get("enterprise_classification") or {}),
            "catalog_class": "DEMO_SYNTHETIC",
            "display_label": "Representative Payer Policies",
            "display_label_contextual": "Representative Payer Policies (Blue Cross NC-like)",
            "not_verbatim_bcbsnc_policy": True,
            "mechanism": "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION",
            "lifecycle_validation": "FULLY_VALIDATED_DEMO",
            "calculation_version": CALC_VERSION,
        }
        meta["mppr_demo"] = {
            "calculation_version": CALC_VERSION,
            "known_answer": ka,
            "fixture_line_count": len(KNOWN_ANSWER_LINES),
        }
        policy.policy_metadata_json = meta
        db.add(policy)
        db.commit()
    finally:
        db.close()

    now = datetime.now(timezone.utc)
    baseline_metrics = {
        "mechanism": "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION",
        "calculation_version": CALC_VERSION,
        "catalog_class": "DEMO_SYNTHETIC",
        "total_allowed": totals["baseline_allowed"],
        "total_paid": totals["baseline_paid"],
        "line_count": totals["line_count"],
        "claim_count": totals["claim_count"],
        "multi_procedure_claims": totals["multi_procedure_claims"],
        "volume_units": totals["volume_units"],
        "primary_metric": "allowed_paid_unit_price",
        "not_utilization_model": True,
        "fixture": "KNOWN_ANSWER_LINES",
    }
    baseline_id_str = f"mppr-ka-baseline-{CALC_VERSION}"
    db = SessionLocal()
    try:
        existing_bl = (
            db.query(Baseline)
            .filter(Baseline.tenant_id == TENANT, Baseline.baseline_id == baseline_id_str)
            .first()
        )
        if existing_bl:
            existing_bl.baseline_metrics_json = baseline_metrics
            existing_bl.policy_id = policy_id
            existing_bl.computed_at = now.replace(tzinfo=None)
            db.add(existing_bl)
            db.commit()
            db.refresh(existing_bl)
            baseline = {
                "id": str(existing_bl.id),
                "baseline_id": existing_bl.baseline_id,
                "baseline_metrics": existing_bl.baseline_metrics_json,
            }
        else:
            baseline = None
    finally:
        db.close()

    if baseline is None:
        baseline = create_baseline(
            TENANT,
            {
                "baseline_id": baseline_id_str,
                "policy_id": str(policy_id),
                "baseline_type": "POLICY_SPECIFIC",
                "window_start_date": "2025-01-01T00:00:00+00:00",
                "window_end_date": "2025-12-31T23:59:59+00:00",
                "computed_at": now.isoformat(),
                "version": 1,
                "baseline_metrics": baseline_metrics,
            },
            input_refs={
                "policy_id": str(policy_id),
                "fixture": "KNOWN_ANSWER_LINES",
                "catalog_class": "DEMO_SYNTHETIC",
            },
            config_snapshot={"calculation_version": CALC_VERSION, "secondary_pct": 0.5},
        )

    pred = store_predicted_impact(
        policy_id,
        TENANT,
        {
            "predicted_at": now.isoformat(),
            "prediction_method": "MPPR_PAYMENT_RULE",
            "model_version": CALC_VERSION,
            "confidence": 1.0,
            "metrics": {
                "payment_impact": totals["payment_impact"],
                "payment_impact_pct": totals["payment_impact_pct"],
                "baseline_paid": totals["baseline_paid"],
                "post_policy_paid": totals["post_policy_paid"],
                "volume_effect": 0.0,
                "mix_effect": 0.0,
                "price_effect": totals["reconciliation"]["price_effect"],
                "prediction_method": "MPPR_PAYMENT_RULE",
                # Explicitly absent UM fields — do not invent utilization reduction
                "utilization_change_pct": None,
                "utilization_change_per_1k": None,
            },
            "baseline_reference": {
                "baseline_id": baseline.get("baseline_id") or baseline.get("id"),
                "calculation_version": CALC_VERSION,
            },
            "limitations": [
                "Deterministic synthetic known-answer fixture — not empirical payer outcomes.",
                "Demo MPPR secondary rate 50%; not a published Blue Cross NC schedule.",
            ],
            "warnings": [],
            "model_versions": {"reimbursement_mppr": CALC_VERSION},
        },
    )

    pred_id = pred.get("id") if pred else None
    obs_id = f"mppr-ka-obs-{CALC_VERSION}"
    obs_metrics = {
        "mechanism": "MULTIPLE_PROCEDURE_PAYMENT_REDUCTION",
        "calculation_version": CALC_VERSION,
        "catalog_class": "DEMO_SYNTHETIC",
        "total_paid": totals["post_policy_paid"],
        "baseline_paid": totals["baseline_paid"],
        "payment_impact": totals["payment_impact"],
        "payment_impact_pct": totals["payment_impact_pct"],
        "reconciliation": totals["reconciliation"],
        "volume_units": totals["volume_units"],
        "known_answer_match": True,
    }
    comparisons = {
        "vs_baseline": {
            "payment_delta": -totals["payment_impact"],
            "payment_delta_pct": -totals["payment_impact_pct"],
        },
        "vs_predicted": {"payment_delta": 0.0, "payment_delta_pct": 0.0, "match": True},
    }
    verdict_reason = (
        "Observed post-policy paid matches MPPR known-answer prediction exactly "
        f"({CALC_VERSION}); price effect only; volume held constant."
    )
    db = SessionLocal()
    try:
        existing_obs = (
            db.query(Observation)
            .filter(Observation.tenant_id == TENANT, Observation.observation_id == obs_id)
            .first()
        )
        if existing_obs:
            existing_obs.metrics_json = obs_metrics
            existing_obs.comparisons_json = comparisons
            existing_obs.verdict_status = "ON_TRACK"
            existing_obs.verdict_reason = verdict_reason
            existing_obs.recommendation = (
                "Maintain MPPR demo rule; expand to claims sample after multi-line index available."
            )
            existing_obs.verdict_rule_version = "mppr-demo-v1"
            if pred_id:
                try:
                    existing_obs.prediction_id = UUID(str(pred_id))
                except Exception:
                    pass
            db.add(existing_obs)
            db.commit()
            obs = {"observation_id": existing_obs.observation_id, "id": str(existing_obs.id)}
        else:
            obs = None
    finally:
        db.close()

    if obs is None:
        # Observed = predicted (known-answer post period matches rule exactly)
        obs = create_observation(
            TENANT,
            {
                "observation_id": obs_id,
                "policy_id": str(policy_id),
                "prediction_id": pred_id,
                "baseline_version_id": baseline.get("id"),
                "observation_type": "AD_HOC",
                "observation_period_start": "2026-01-01T00:00:00+00:00",
                "observation_period_end": "2026-03-31T23:59:59+00:00",
                "computed_at": now.isoformat(),
                "metrics_json": obs_metrics,
                "comparisons_json": comparisons,
                "verdict_status": "ON_TRACK",
                "verdict_reason": verdict_reason,
                "recommendation": (
                    "Maintain MPPR demo rule; expand to claims sample after multi-line index available."
                ),
                "verdict_rule_version": "mppr-demo-v1",
            },
            input_refs={
                "policy_id": str(policy_id),
                "calculation_version": CALC_VERSION,
                "fixture": "KNOWN_ANSWER_LINES",
            },
            config_snapshot={"secondary_pct": 0.5},
        )

    whatif = {
        "scenario_name": "MPPR secondary rate 40% vs 50%",
        "calculation_version": CALC_VERSION,
        "base_secondary_pct": 0.5,
        "alt_secondary_pct": 0.4,
        "base": apply_mppr(KNOWN_ANSWER_LINES, secondary_pct=0.5)["totals"],
        "alt": apply_mppr(KNOWN_ANSWER_LINES, secondary_pct=0.4)["totals"],
    }
    whatif["delta_payment_impact"] = round(
        whatif["alt"]["payment_impact"] - whatif["base"]["payment_impact"], 2
    )

    out = {
        "generated_at": now.isoformat(),
        "policy_id": str(policy_id),
        "policy_name": POLICY_NAME,
        "validation_class": "FULLY_VALIDATED_DEMO",
        "known_answer": ka,
        "baseline_id": baseline.get("baseline_id") or baseline.get("id"),
        "predicted_impact_id": pred_id,
        "observation_id": obs.get("observation_id") if obs else None,
        "verdict": "ON_TRACK",
        "what_if": whatif,
        "totals": totals,
        "honesty": {
            "catalog_class": "DEMO_SYNTHETIC",
            "not_blue_cross_nc_proprietary": True,
            "not_mri_utilization_formula": True,
        },
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE / "MPPR_REIMBURSEMENT_VERTICAL.json"
    path.write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({"ok": True, "path": str(path), "payment_impact": totals["payment_impact"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
