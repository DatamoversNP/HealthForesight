"""Separate a synthetic payment prediction from the post-policy observation.

The prediction is the payment-engine total. The observation is a later sum of
stored post-policy event rows. Those rows are a labeled synthetic scenario.
They are not claims_lines and they are not real-world evidence.

No endpoint contract is written. Verdicts stay inconclusive.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from uepi_api.models.audit import AuditEvent
from uepi_api.models.observation import Observation
from uepi_api.models.policy import PolicyChangelog
from uepi_api.models.predicted_impact import PolicyPredictedImpact
from uepi_api.services.enrollment_exposure import measured_enrollment_member_months
from uepi_api.services.expansion_demo_scenarios import (
    apply_infusion_soc,
    apply_ncci_mue,
    apply_ncci_ptp,
    apply_therapy_coverage,
)
from uepi_api.services.reimbursement_mppr import apply_mppr
from uepi_api.services.reimbursement_sos import apply_sos
from uepi_api.services.synthetic_payer_integration import POLICY_FACTS, WINDOW_INCLUSIVE_END
from uepi_api.services.synthetic_whatif import CLINICAL_KEYS, load_policy_lines
from uepi_common.synthetic_payer.generate import WINDOW_START
from uepi_common.synthetic_payer.oracle import (
    oracle_infusion_by_claim,
    oracle_mppr,
    oracle_mue,
    oracle_ptp,
    oracle_sos,
    oracle_therapy,
)

SOURCE_LABEL = "SYNTHETIC_POST_POLICY_SCENARIO"
PREDICTION_METHOD = "SYNTHETIC_PAYMENT_ENGINE"
EVIDENCE_CLASS = "SYNTHETIC_ILLUSTRATIVE"

PAYMENT_STEPS = (
    "policy_configuration",
    "population_scope",
    "general_baseline",
    "policy_baseline",
    "predicted_impact",
    "post_policy_events",
    "observation",
    "prediction_observation_reconciliation",
    "verdict",
    "evidence",
    "objectives_health",
    "lifecycle_history",
)


def observe_post_policy_events(events: List[Mapping[str, Any]]) -> Dict[str, Any]:
    """Sum stored event rows. This function does not read a prediction total."""
    observed_allowed = round(sum(float(row["simulated_allowed"]) for row in events), 2)
    observed_plan_paid = round(sum(float(row["simulated_plan_paid"]) for row in events), 2)
    baseline_allowed = round(sum(float(row["baseline_allowed"]) for row in events), 2)
    baseline_plan_paid = round(sum(float(row["baseline_plan_paid"]) for row in events), 2)
    return {
        "event_count": len(events),
        "baseline_allowed": baseline_allowed,
        "observed_allowed": observed_allowed,
        "baseline_plan_paid": baseline_plan_paid,
        "observed_plan_paid": observed_plan_paid,
        "allowed_difference": round(observed_allowed - baseline_allowed, 2),
        "source": "sum_of_synthetic_post_policy_events",
    }


def build_payment_lifecycle(policy_key: str, lines: List[Mapping[str, Any]]) -> Dict[str, Any]:
    """Build a prediction from engine totals and events from engine lines."""
    if policy_key in CLINICAL_KEYS:
        raise ValueError(f"{policy_key} has no payment outcome")
    engine = _engine(policy_key, lines)
    totals = engine["totals"]
    prediction = {
        "baseline_allowed": round(float(totals["baseline_paid"]), 2),
        "predicted_allowed": round(float(totals["post_policy_paid"]), 2),
        "payment_impact_dollars": round(float(totals["payment_impact"]), 2),
        "source": "payment_engine_totals",
        "evidence_class": EVIDENCE_CLASS,
        "real_world_savings": False,
        "confidence_score": None,
        "utilization_change_pct": None,
    }
    by_line = {str(row["claim_line_id"]): row for row in lines}
    events: List[Dict[str, Any]] = []
    for line in engine["lines"]:
        line_id = str(line["claim_line_id"])
        source = by_line[line_id]
        allowed = float(source["allowed_amount"])
        paid = float(source["paid_amount"])
        post = float(line["post_policy_paid"])
        events.append(
            {
                "claim_line_id": line_id,
                "baseline_allowed": round(float(line.get("baseline_paid", allowed)), 2),
                "simulated_allowed": round(post, 2),
                "baseline_plan_paid": round(paid, 2),
                "simulated_plan_paid": round((post * paid / allowed) if allowed else 0.0, 6),
            }
        )
    observation = observe_post_policy_events(events)
    source_allowed = sum(float(row["allowed_amount"]) for row in lines)
    source_paid = sum(float(row["paid_amount"]) for row in lines)
    ratio = (source_paid / source_allowed) if source_allowed else None
    prediction["predicted_plan_paid"] = None if ratio is None else round(prediction["predicted_allowed"] * ratio, 2)
    prediction["baseline_plan_paid"] = None if ratio is None else round(prediction["baseline_allowed"] * ratio, 2)
    oracle = _oracle(policy_key, lines)
    allowed_gap = abs(observation["observed_allowed"] - prediction["predicted_allowed"])
    oracle_gap = abs(prediction["predicted_allowed"] - float(oracle["post_policy_paid"]))
    return {
        "policy_key": policy_key,
        "prediction": prediction,
        "events": events,
        "observation": observation,
        "oracle_post_allowed": round(float(oracle["post_policy_paid"]), 2),
        "oracle_match": oracle_gap < 0.02 and allowed_gap < 0.02,
        "allowed_gap": round(allowed_gap, 4),
        "reconciliation_status": "MATCH" if allowed_gap < 0.02 and oracle_gap < 0.02 else "MISMATCH",
    }


def _engine(policy_key: str, lines: List[Mapping[str, Any]]) -> Dict[str, Any]:
    if policy_key == "mppr":
        return apply_mppr(lines, secondary_pct=0.5)
    if policy_key == "sos":
        return apply_sos(lines, hospital_pct=0.8)
    if policy_key == "ptp":
        return apply_ncci_ptp(lines)
    if policy_key == "mue":
        return apply_ncci_mue(lines, mue_value=4)
    if policy_key == "therapy":
        return apply_therapy_coverage(lines)
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for row in lines:
        grouped.setdefault(str(row.get("claim_id") or ""), []).append(row)
    baseline = post = 0.0
    event_lines: List[Dict[str, Any]] = []
    for claim_lines in grouped.values():
        part = apply_infusion_soc(claim_lines, steer_hopd_count=1, office_allowed=3200.0)
        baseline += part["totals"]["baseline_paid"]
        post += part["totals"]["post_policy_paid"]
        event_lines.extend(part["lines"])
    return {
        "totals": {
            "baseline_paid": round(baseline, 2),
            "post_policy_paid": round(post, 2),
            "payment_impact": round(baseline - post, 2),
        },
        "lines": event_lines,
    }


def _oracle(policy_key: str, lines: List[Mapping[str, Any]]) -> Dict[str, Any]:
    if policy_key == "mppr":
        return oracle_mppr(lines, 0.5)
    if policy_key == "sos":
        return oracle_sos(lines, 0.8)
    if policy_key == "ptp":
        return oracle_ptp(lines)
    if policy_key == "mue":
        return oracle_mue(lines, 4)
    if policy_key == "therapy":
        return oracle_therapy(lines)
    return oracle_infusion_by_claim(lines, office_allowed=3200.0, steer_hopd_count=1)


def ensure_event_table(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS synthetic_post_policy_events (
                id uuid PRIMARY KEY,
                tenant_id uuid NOT NULL,
                policy_id uuid NOT NULL,
                policy_key text NOT NULL,
                claim_line_id text NOT NULL,
                source_label text NOT NULL,
                baseline_allowed double precision NOT NULL,
                simulated_allowed double precision NOT NULL,
                baseline_plan_paid double precision NOT NULL,
                simulated_plan_paid double precision NOT NULL,
                evidence_class text NOT NULL,
                created_at timestamp NOT NULL DEFAULT now()
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_synthetic_post_policy_events_policy
            ON synthetic_post_policy_events (tenant_id, policy_id)
            """
        )
    )
    db.commit()


def persist_synthetic_lifecycle(db: Session, tenant_id: UUID) -> Dict[str, Any]:
    """Write predictions, event rows, observation reconciliation, and audit history."""
    ensure_event_table(db)
    member_months = measured_enrollment_member_months(db, tenant_id, WINDOW_START, WINDOW_INCLUSIVE_END)
    claim_count_before = db.execute(text("SELECT COUNT(*) FROM claims_lines WHERE tenant_id = :t"), {"t": tenant_id}).scalar()
    db.execute(text("DELETE FROM synthetic_post_policy_events WHERE tenant_id = :t"), {"t": tenant_id})
    db.query(PolicyPredictedImpact).filter(
        PolicyPredictedImpact.tenant_id == tenant_id,
        PolicyPredictedImpact.prediction_method == PREDICTION_METHOD,
    ).delete(synchronize_session=False)
    db.commit()

    results = []
    for policy_key, facts in POLICY_FACTS.items():
        policy_id = UUID(_policy_id(policy_key))
        loaded = load_policy_lines(db, tenant_id, policy_key)
        if policy_key in CLINICAL_KEYS:
            results.append(_persist_clinical(db, tenant_id, policy_id, policy_key, facts["name"], len(loaded["lines"])))
            continue
        built = build_payment_lifecycle(policy_key, loaded["lines"])
        if built["reconciliation_status"] != "MATCH":
            raise RuntimeError(f"{policy_key} prediction and observation did not match: {built['allowed_gap']}")
        results.append(
            _persist_payment(db, tenant_id, policy_id, built, member_months, facts["name"])
        )
    claim_count_after = db.execute(text("SELECT COUNT(*) FROM claims_lines WHERE tenant_id = :t"), {"t": tenant_id}).scalar()
    if int(claim_count_after) != int(claim_count_before):
        raise RuntimeError("Lifecycle write changed claims_lines")
    db.commit()
    return {
        "database": db.execute(text("SELECT current_database()")).scalar(),
        "member_months": member_months,
        "claims_unchanged": int(claim_count_after),
        "policies": results,
        "endpoint_contracts_created": 0,
        "verdicts_forced_on_track": 0,
    }


def _policy_id(policy_key: str) -> str:
    from uepi_common.synthetic_payer.generate import POLICIES

    for spec in POLICIES:
        if spec["key"] == policy_key:
            return spec["policy_id"]
    raise KeyError(policy_key)


def _persist_payment(
    db: Session,
    tenant_id: UUID,
    policy_id: UUID,
    built: Dict[str, Any],
    member_months: Optional[float],
    policy_name: str,
) -> Dict[str, Any]:
    prediction = built["prediction"]
    observation_sum = built["observation"]
    difference = observation_sum["allowed_difference"]
    per_mm = None if not member_months else difference / member_months
    prediction_row = PolicyPredictedImpact(
        id=uuid4(),
        tenant_id=tenant_id,
        policy_id=policy_id,
        metrics_json={
            "metrics": {
                **prediction,
                "allowed_difference": difference,
                "cost_change": per_mm,
                "cost_change_pmpm": per_mm,
                "cost_change_kind": "simulated_allowed_difference_per_enrolled_member_month",
                "label": (
                    "Synthetic payment prediction from the engine total. "
                    "Not an observation and not measured savings."
                ),
            }
        },
        model_version="synthetic-payer-v1",
        confidence=None,
        predicted_at=datetime(2026, 11, 6, 12, 0, 0),
        prediction_method=PREDICTION_METHOD,
    )
    db.add(prediction_row)
    db.flush()
    _insert_events(db, tenant_id, policy_id, built["policy_key"], built["events"])
    stored = _sum_events(db, tenant_id, policy_id)
    if abs(stored["observed_allowed"] - prediction["predicted_allowed"]) >= 0.02:
        raise RuntimeError(f"Stored event sum diverged for {built['policy_key']}")
    observation = (
        db.query(Observation)
        .filter(Observation.tenant_id == tenant_id, Observation.policy_id == policy_id)
        .one()
    )
    metrics = dict(observation.metrics_json or {})
    comparisons = dict(observation.comparisons_json or {})
    vs_baseline = dict(comparisons.get("vs_baseline") or {})
    vs_baseline["observed_allowed"] = stored["observed_allowed"]
    vs_baseline["observation_source"] = "sum_of_synthetic_post_policy_events"
    comparisons["vs_baseline"] = vs_baseline
    comparisons["vs_predicted"] = {
        "predicted_allowed": prediction["predicted_allowed"],
        "observed_allowed": stored["observed_allowed"],
        "allowed_difference_vs_prediction": round(stored["observed_allowed"] - prediction["predicted_allowed"], 2),
        "predicted_plan_paid": prediction["predicted_plan_paid"],
        "observed_plan_paid": stored["observed_plan_paid"],
        "plan_paid_gap": round(stored["observed_plan_paid"] - prediction["predicted_plan_paid"], 2),
        "reconciliation_status": "MATCH",
        "oracle_post_allowed": built["oracle_post_allowed"],
        "oracle_match": True,
        "prediction_source": prediction["source"],
        "observation_source": stored["source"],
        "evidence_class": EVIDENCE_CLASS,
        "real_world_evidence": False,
        "label": "Synthetic scenario reconciliation. Not a real-world predicted-versus-observed study.",
    }
    metrics["observation_derived_from"] = SOURCE_LABEL
    metrics["prediction_observation_reconciliation"] = "MATCH"
    metrics["observed_allowed"] = stored["observed_allowed"]
    metrics["predicted_allowed"] = prediction["predicted_allowed"]
    observation.metrics_json = metrics
    observation.comparisons_json = comparisons
    observation.prediction_id = prediction_row.id
    flag_modified(observation, "metrics_json")
    flag_modified(observation, "comparisons_json")
    _history(
        db,
        tenant_id,
        policy_id,
        policy_name,
        "EXECUTED_SIMULATION_ONLY",
        f"Prediction {prediction['predicted_allowed']} reconciled to event sum {stored['observed_allowed']}. Verdict unchanged.",
    )
    return {
        "policy_key": built["policy_key"],
        "status": "EXECUTED_SIMULATION_ONLY",
        "events": stored["event_count"],
        "predicted_allowed": prediction["predicted_allowed"],
        "observed_allowed": stored["observed_allowed"],
        "reconciliation": "MATCH",
        "verdict": observation.verdict_status,
        "prediction_id": str(prediction_row.id),
    }


def _persist_clinical(
    db: Session,
    tenant_id: UUID,
    policy_id: UUID,
    policy_key: str,
    policy_name: str,
    event_count: int,
) -> Dict[str, Any]:
    prediction_row = PolicyPredictedImpact(
        id=uuid4(),
        tenant_id=tenant_id,
        policy_id=policy_id,
        metrics_json={
            "metrics": {
                "outcome_status": "NOT_MEASURABLE",
                "predicted_allowed": None,
                "payment_impact_dollars": None,
                "confidence_score": None,
                "utilization_change_pct": None,
                "evidence_class": EVIDENCE_CLASS,
                "label": "No payment prediction. Source events only. Outcome is not measurable.",
            }
        },
        model_version="synthetic-payer-v1",
        confidence=None,
        predicted_at=datetime(2026, 11, 6, 12, 0, 0),
        prediction_method=PREDICTION_METHOD,
    )
    db.add(prediction_row)
    db.flush()
    observation = (
        db.query(Observation)
        .filter(Observation.tenant_id == tenant_id, Observation.policy_id == policy_id)
        .one()
    )
    comparisons = dict(observation.comparisons_json or {})
    comparisons["vs_predicted"] = {
        "reconciliation_status": "NOT_MEASURABLE",
        "predicted_allowed": None,
        "observed_allowed": None,
        "real_world_evidence": False,
        "label": "No post-policy outcome events were created for this policy.",
    }
    observation.comparisons_json = comparisons
    observation.prediction_id = prediction_row.id
    flag_modified(observation, "comparisons_json")
    _history(
        db,
        tenant_id,
        policy_id,
        policy_name,
        "NOT_MEASURABLE",
        f"{event_count} pre-policy source lines remain. No outcome, contract, or dollar effect was added.",
    )
    return {
        "policy_key": policy_key,
        "status": "NOT_MEASURABLE",
        "events": 0,
        "source_lines": event_count,
        "predicted_allowed": None,
        "observed_allowed": None,
        "reconciliation": "NOT_MEASURABLE",
        "verdict": observation.verdict_status,
        "prediction_id": str(prediction_row.id),
    }


def _insert_events(db: Session, tenant_id: UUID, policy_id: UUID, policy_key: str, events: List[Mapping[str, Any]]) -> None:
    payload = [
        {
            "id": str(uuid4()),
            "tenant_id": str(tenant_id),
            "policy_id": str(policy_id),
            "policy_key": policy_key,
            "claim_line_id": row["claim_line_id"],
            "source_label": SOURCE_LABEL,
            "baseline_allowed": row["baseline_allowed"],
            "simulated_allowed": row["simulated_allowed"],
            "baseline_plan_paid": row["baseline_plan_paid"],
            "simulated_plan_paid": row["simulated_plan_paid"],
            "evidence_class": EVIDENCE_CLASS,
        }
        for row in events
    ]
    db.execute(
        text(
            """
            INSERT INTO synthetic_post_policy_events (
                id, tenant_id, policy_id, policy_key, claim_line_id, source_label,
                baseline_allowed, simulated_allowed, baseline_plan_paid, simulated_plan_paid, evidence_class
            ) VALUES (
                CAST(:id AS uuid), CAST(:tenant_id AS uuid), CAST(:policy_id AS uuid), :policy_key, :claim_line_id, :source_label,
                :baseline_allowed, :simulated_allowed, :baseline_plan_paid, :simulated_plan_paid, :evidence_class
            )
            """
        ),
        payload,
    )


def _sum_events(db: Session, tenant_id: UUID, policy_id: UUID) -> Dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT COUNT(*),
                   COALESCE(SUM(simulated_allowed), 0),
                   COALESCE(SUM(simulated_plan_paid), 0),
                   COALESCE(SUM(baseline_allowed), 0),
                   COALESCE(SUM(baseline_plan_paid), 0)
            FROM synthetic_post_policy_events
            WHERE tenant_id = :tenant_id AND policy_id = :policy_id
            """
        ),
        {"tenant_id": tenant_id, "policy_id": policy_id},
    ).one()
    observed_allowed = round(float(row[1]), 2)
    baseline_allowed = round(float(row[3]), 2)
    return {
        "event_count": int(row[0]),
        "observed_allowed": observed_allowed,
        "observed_plan_paid": round(float(row[2]), 2),
        "baseline_allowed": baseline_allowed,
        "baseline_plan_paid": round(float(row[4]), 2),
        "allowed_difference": round(observed_allowed - baseline_allowed, 2),
        "source": "sql_sum_of_synthetic_post_policy_events",
    }


def _history(db: Session, tenant_id: UUID, policy_id: UUID, policy_name: str, status: str, detail: str) -> None:
    for stage in PAYMENT_STEPS:
        stage_status = status if stage in {"predicted_impact", "post_policy_events", "observation", "prediction_observation_reconciliation"} else _inherited_status(stage, status)
        db.add(
            AuditEvent(
                id=uuid4(),
                tenant_id=tenant_id,
                action="LIFECYCLE_STAGE",
                object_type="POLICY",
                object_id=policy_id,
                diff_summary={"stage": stage, "status": stage_status, "policy_name": policy_name},
                metadata_json={"detail": detail, "evidence_class": EVIDENCE_CLASS},
            )
        )
    db.add(
        PolicyChangelog(
            id=uuid4(),
            tenant_id=tenant_id,
            policy_id=policy_id,
            entry_type="LIFECYCLE",
            description=f"{policy_name}: {status}. {detail}",
            changed_at=datetime.utcnow(),
            changes_json={"status": status, "endpoint_contract_added": False},
        )
    )


def _inherited_status(stage: str, outcome_status: str) -> str:
    if stage == "verdict":
        return "EXECUTED_INCONCLUSIVE_NO_CONTRACT"
    if stage == "objectives_health":
        return "EXECUTED_NO_CONTRACT"
    if stage == "evidence":
        return "READ_TIME_PACK_ONLY"
    if stage == "lifecycle_history":
        return "EXECUTED"
    if stage in {"policy_configuration", "population_scope", "general_baseline", "policy_baseline"}:
        return "EXECUTED" if outcome_status != "NOT_MEASURABLE" or stage != "population_scope" else "EXECUTED_SOURCE_EVENTS_ONLY"
    if outcome_status == "NOT_MEASURABLE" and stage in {
        "predicted_impact",
        "post_policy_events",
        "observation",
        "prediction_observation_reconciliation",
    }:
        return "NOT_MEASURABLE"
    return outcome_status


def lifecycle_report_blob(result: Mapping[str, Any]) -> str:
    return json.dumps(result, indent=2, default=str)
