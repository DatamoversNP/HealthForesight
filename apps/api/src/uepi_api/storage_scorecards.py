"""Scorecard file storage operations - database only"""
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from uepi_api.models.scorecard import Scorecard as ScorecardDB, ScorecardEntry as ScorecardEntryDB
from sqlalchemy import desc


def _trend_from_number(value: Optional[float], *, positive_means: str, negative_means: str, zero_means: str = "STABLE") -> str:
    if value is None:
        return "UNAVAILABLE"
    if value > 0:
        return positive_means
    if value < 0:
        return negative_means
    return zero_means


def _weights_for_persist(scorecard: Dict[str, Any]) -> Dict[str, Any]:
    """Persist index_status in weights JSON (no schema migration)."""
    weights = dict(scorecard.get("weights") or {})
    meta = dict(weights.get("_meta") or {})
    for key in ("index_status", "index_reason", "policy_effect_status"):
        if scorecard.get(key) is not None:
            meta[key] = scorecard.get(key)
    if meta:
        weights["_meta"] = meta
    return weights


def _status_fields_from_row(weights: Optional[Dict[str, Any]], entries: List[Dict[str, Any]], effectiveness_index: Optional[float]) -> Dict[str, Any]:
    """Read index_status from weights._meta, with inference for legacy rows."""
    w = weights or {}
    meta = w.get("_meta") if isinstance(w.get("_meta"), dict) else {}
    index_status = meta.get("index_status")
    index_reason = meta.get("index_reason")
    policy_effect_status = meta.get("policy_effect_status")
    if not index_status:
        descriptive_entry = any(
            "descriptive" in str(e.get("metric_name") or "").lower() for e in entries
        )
        if effectiveness_index is None:
            index_status = "UNAVAILABLE"
        elif descriptive_entry:
            index_status = "DESCRIPTIVE_ONLY"
            index_reason = (
                "Index from observed-vs-baseline descriptive % only. "
                "Not attributed policy-effect savings; not an authoritative KPI."
            )
        else:
            index_status = "AVAILABLE"
    return {
        "index_status": index_status,
        "index_reason": index_reason,
        "policy_effect_status": policy_effect_status,
    }


def generate_scorecard_from_predicted_impact(
    policy_id: UUID | str,
    predicted_impact: Dict[str, Any],
    period: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a scorecard from predicted impact data.

    Prefer attributed effect % when present. Otherwise use measured
    vs-baseline descriptive % (OBSERVED_VS_BASELINE_NOT_ATTRIBUTED) and mark
    the index DESCRIPTIVE_ONLY — never invent attributed savings.
    """
    if period is None:
        # Generate period from current date (e.g., "2026-Q1")
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        period = f"{now.year}-Q{quarter}"
    
    # Extract metrics from predicted impact
    # Predicted impact can have different structures:
    # 1. Old format: predicted_impact.projected_impact.cost_savings
    # 2. New format: predicted_impact.metrics.cost_change_total, etc.
    projected = predicted_impact.get("projected_impact", {}) or {}
    metrics = predicted_impact.get("metrics", {}) or {}
    
    descriptive_only = False
    # Try new format first (metrics), fallback to old format (projected_impact)
    if metrics:
        cost_pct = metrics.get("cost_change_pct")
        util_pct = metrics.get("utilization_change_pct")
        measured_cost_pct = metrics.get("measured_vs_baseline_cost_change_pct")
        measured_util_pct = metrics.get("measured_vs_baseline_utilization_change_pct")
        # Payment-rule engines store payer savings as payment_impact(_pct), not
        # attributed cost_change_pct. Map to descriptive cost decrease.
        payment_impact_pct = metrics.get("payment_impact_pct")
        if payment_impact_pct is None:
            baseline_paid = metrics.get("baseline_paid")
            payment_impact = metrics.get("payment_impact")
            try:
                if baseline_paid is not None and float(baseline_paid) != 0 and payment_impact is not None:
                    payment_impact_pct = (float(payment_impact) / float(baseline_paid)) * 100.0
            except (TypeError, ValueError):
                payment_impact_pct = None
        if cost_pct is None and util_pct is None and (
            measured_cost_pct is not None or measured_util_pct is not None
        ):
            descriptive_only = True
            cost_pct = measured_cost_pct
            util_pct = measured_util_pct
        elif (
            cost_pct is None
            and util_pct is None
            and measured_cost_pct is None
            and measured_util_pct is None
            and payment_impact_pct is not None
        ):
            descriptive_only = True
            # Positive payment_impact = payer savings → descriptive cost decrease
            cost_pct = -abs(float(payment_impact_pct))
            util_pct = 0.0  # payment engines hold volume constant
        # Negative cost % → savings magnitude for the cost component.
        # Descriptive path also scores cost increases (lower cost_impact_score).
        if cost_pct is not None and cost_pct < 0:
            cost_savings = {"total_savings_pct": abs(cost_pct)}
        elif descriptive_only and cost_pct is not None:
            cost_savings = {"total_savings_pct": None, "cost_increase_pct": abs(cost_pct)}
        else:
            cost_savings = {"total_savings_pct": None}
        utilization_change = {
            "percent_change": util_pct
        }
        # util_pct is percent points (e.g. -20). Defer fraction = |pct|/100 when util falls.
        # Descriptive util increases → defer_rate 0 (no deferral risk from reduction).
        if util_pct is not None and util_pct < 0:
            behavioral_response = {"defer_rate": abs(util_pct) / 100.0}
        elif descriptive_only and util_pct is not None:
            behavioral_response = {"defer_rate": 0.0}
        else:
            behavioral_response = {"defer_rate": None}
    else:
        # Old format
        cost_savings = projected.get("cost_savings", {}) or {}
        utilization_change = projected.get("utilization_change", {}) or {}
        behavioral_response = projected.get("behavioral_response", {}) or {}
    
    policy_effect_status = (
        predicted_impact.get("policy_effect_status")
        or metrics.get("policy_effect_status")
        or predicted_impact.get("status")
    )
    predicted_allowed = metrics.get("predicted_allowed")
    if predicted_allowed is None:
        predicted_allowed = metrics.get("predicted_allowed_amount")
    if predicted_allowed is None:
        predicted_allowed = projected.get("predicted_allowed")

    # Calculate effectiveness index (0-100 composite score)
    # Components:
    # - Cost impact: 30%
    # - Behavioral risk: 25%
    # - Access impact: 25%
    # - Regulatory defensibility: 20%
    
    # Cost impact score (0-100): Higher is better (more savings, lower costs)
    cost_savings_pct = cost_savings.get("total_savings_pct")
    cost_increase_pct = cost_savings.get("cost_increase_pct")
    if cost_savings_pct is not None:
        cost_impact_score = min(100, max(0, 50 + (cost_savings_pct * 2)))
    elif cost_increase_pct is not None:
        cost_impact_score = min(100, max(0, 50 - (cost_increase_pct * 2)))
    else:
        cost_impact_score = None
    
    # Behavioral risk score (0-100): Lower deferral risk = higher score.
    # defer_rate is a fraction in [0, 1] (e.g. 0.20 for a 20% util drop).
    defer_rate = behavioral_response.get("defer_rate")
    behavioral_risk_score = (
        None if defer_rate is None else min(100, max(0, 100 - (defer_rate * 100)))
    )
    
    # Access impact when utilization change is present (legacy constant 80).
    util_pct_value = utilization_change.get("percent_change")
    access_impact_score = 80 if util_pct_value is not None else None
    
    # Regulatory defensibility score (0-100): Based on policy type and evidence
    confidence = predicted_impact.get("confidence_score")
    if confidence is None and isinstance(metrics, dict):
        confidence = metrics.get("confidence_score")
    # Accept 0-1 confidence and scale to 0-100 before +20 boost.
    if confidence is not None and confidence <= 1:
        confidence = confidence * 100
    regulatory_defensibility_score = None if confidence is None else min(100, confidence + 20)

    if not policy_effect_status and not descriptive_only:
        policy_effect_status = "UNESTIMATED"
    
    # Weighted effectiveness index
    weights = {
        "cost_impact": 0.30,
        "behavioral_risk": 0.25,
        "access_impact": 0.25,
        "regulatory_defensibility": 0.20,
    }

    if descriptive_only:
        # No attributed confidence — score cost/behavioral/access only and renormalize.
        partial = {
            "cost_impact": cost_impact_score,
            "behavioral_risk": behavioral_risk_score,
            "access_impact": access_impact_score,
        }
        present = {k: v for k, v in partial.items() if v is not None}
        if len(present) >= 2:
            wsum = sum(weights[k] for k in present)
            effectiveness_index = sum(present[k] * (weights[k] / wsum) for k in present)
            index_status = "DESCRIPTIVE_ONLY"
            index_reason = (
                "Index from observed-vs-baseline descriptive % only. "
                "Not attributed policy-effect savings; not an authoritative KPI."
            )
        else:
            effectiveness_index = None
            index_status = "UNAVAILABLE"
            index_reason = "Measured descriptive % insufficient to form a descriptive index."
    else:
        component_scores = (
            cost_impact_score,
            behavioral_risk_score,
            access_impact_score,
            regulatory_defensibility_score,
        )
        if any(score is None for score in component_scores):
            effectiveness_index = None
            index_status = "UNAVAILABLE"
            index_reason = (
                "Attributed cost/utilization percent changes and confidence are missing; "
                "index not computed."
            )
        else:
            effectiveness_index = (
                cost_impact_score * weights["cost_impact"] +
                behavioral_risk_score * weights["behavioral_risk"] +
                access_impact_score * weights["access_impact"] +
                regulatory_defensibility_score * weights["regulatory_defensibility"]
            )
            index_status = "AVAILABLE"
            index_reason = None
    
    # Create scorecard entry
    scorecard = {
        "id": str(uuid4()),
        "policy_id": str(policy_id),
        "period": period,
        "effectiveness_index": None if effectiveness_index is None else round(effectiveness_index, 2),
        "cost_impact_score": None if cost_impact_score is None else round(cost_impact_score, 2),
        "behavioral_risk_score": None if behavioral_risk_score is None else round(behavioral_risk_score, 2),
        "access_impact_score": None if access_impact_score is None else round(access_impact_score, 2),
        "regulatory_defensibility_score": None if regulatory_defensibility_score is None else round(regulatory_defensibility_score, 2),
        "weights": weights,
        "policy_effect_status": policy_effect_status,
        "index_status": index_status,
        "index_reason": index_reason,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "entries": [
            {
                "dimension": "COST",
                "metric_name": "Cost Savings % (descriptive)" if descriptive_only else "Cost Savings %",
                "metric_value": cost_savings_pct,
                "metric_unit": "percent",
                "trend": _trend_from_number(cost_savings_pct, positive_means="DOWN", negative_means="UP"),
            },
            {
                "dimension": "BEHAVIORAL",
                "metric_name": "Defer Rate",
                "metric_value": None if defer_rate is None else defer_rate * 100.0,
                "metric_unit": "percent",
                "trend": _trend_from_number(defer_rate, positive_means="UP", negative_means="DOWN"),
            },
            {
                "dimension": "ACCESS",
                "metric_name": "Utilization Change %",
                "metric_value": util_pct_value,
                "metric_unit": "percent",
                "trend": _trend_from_number(util_pct_value, positive_means="UP", negative_means="DOWN"),
            },
        ],
    }
    if predicted_allowed is not None:
        scorecard["entries"].append(
            {
                "dimension": "COST",
                "metric_name": "Predicted Allowed $ (unattributed scope)",
                "metric_value": predicted_allowed,
                "metric_unit": "currency",
                "trend": "UNAVAILABLE",
            }
        )
    
    return scorecard


def save_scorecard(scorecard: Dict[str, Any], tenant_id: UUID) -> None:
    """Save scorecard to database"""
    _save_scorecard(scorecard, tenant_id)


def _save_scorecard(scorecard: Dict[str, Any], tenant_id: UUID) -> None:
    """Save scorecard to database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Parse policy_id
        policy_id = UUID(scorecard["policy_id"]) if isinstance(scorecard["policy_id"], str) else scorecard["policy_id"]
        
        # Check if scorecard already exists
        existing = db.query(ScorecardDB).filter(
            ScorecardDB.tenant_id == tenant_id,
            ScorecardDB.policy_id == policy_id,
            ScorecardDB.period == scorecard["period"]
        ).first()
        
        if existing:
            # Update existing scorecard — preserve nulls (do not coerce to 0)
            existing.effectiveness_index = scorecard.get("effectiveness_index")
            existing.cost_impact_score = scorecard.get("cost_impact_score")
            existing.behavioral_risk_score = scorecard.get("behavioral_risk_score")
            existing.access_impact_score = scorecard.get("access_impact_score")
            existing.regulatory_defensibility_score = scorecard.get("regulatory_defensibility_score")
            existing.weights = _weights_for_persist(scorecard)
            scorecard_id = existing.id
            
            # Delete existing entries
            db.query(ScorecardEntryDB).filter(ScorecardEntryDB.scorecard_id == scorecard_id).delete()
        else:
            # Create new scorecard
            scorecard_id = uuid4()
            scorecard_db = ScorecardDB(
                tenant_id=tenant_id,
                id=scorecard_id,
                policy_id=policy_id,
                period=scorecard["period"],
                effectiveness_index=scorecard.get("effectiveness_index"),
                cost_impact_score=scorecard.get("cost_impact_score"),
                behavioral_risk_score=scorecard.get("behavioral_risk_score"),
                access_impact_score=scorecard.get("access_impact_score"),
                regulatory_defensibility_score=scorecard.get("regulatory_defensibility_score"),
                weights=_weights_for_persist(scorecard),
            )
            db.add(scorecard_db)
        
        # Create scorecard entries
        for entry_data in scorecard.get("entries", []):
            entry_db = ScorecardEntryDB(
                tenant_id=tenant_id,
                scorecard_id=scorecard_id,
                dimension=entry_data.get("dimension", ""),
                metric_name=entry_data.get("metric_name", ""),
                metric_value=entry_data.get("metric_value", 0),
                metric_unit=entry_data.get("metric_unit"),
                trend=entry_data.get("trend"),
            )
            db.add(entry_db)
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"ERROR save_scorecard (DB): {e}")
        raise
    finally:
        db.close()


def get_scorecard(policy_id: UUID | str, period: str, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Get scorecard for a specific policy and period - from database"""
    return _get_scorecard(policy_id, period, tenant_id)


def _get_scorecard(policy_id: UUID | str, period: str, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Get scorecard from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Parse policy_id
        policy_id_uuid = UUID(policy_id) if isinstance(policy_id, str) else policy_id
        
        scorecard_db = db.query(ScorecardDB).filter(
            ScorecardDB.tenant_id == tenant_id,
            ScorecardDB.policy_id == policy_id_uuid,
            ScorecardDB.period == period
        ).first()
        
        if not scorecard_db:
            return None
        
        # Get entries
        entries_db = db.query(ScorecardEntryDB).filter(
            ScorecardEntryDB.scorecard_id == scorecard_db.id
        ).all()
        
        entries = [
            {
                "dimension": entry.dimension,
                "metric_name": entry.metric_name,
                "metric_value": entry.metric_value,
                "metric_unit": entry.metric_unit,
                "trend": entry.trend,
            }
            for entry in entries_db
        ]
        status = _status_fields_from_row(
            scorecard_db.weights if scorecard_db.weights else {},
            entries,
            scorecard_db.effectiveness_index,
        )
        # Return as dict (same format as file-based)
        return {
            "id": str(scorecard_db.id),
            "policy_id": str(scorecard_db.policy_id),
            "period": scorecard_db.period,
            "effectiveness_index": scorecard_db.effectiveness_index,
            "cost_impact_score": scorecard_db.cost_impact_score,
            "behavioral_risk_score": scorecard_db.behavioral_risk_score,
            "access_impact_score": scorecard_db.access_impact_score,
            "regulatory_defensibility_score": scorecard_db.regulatory_defensibility_score,
            "weights": scorecard_db.weights if scorecard_db.weights else {},
            "created_at": scorecard_db.created_at.isoformat() if scorecard_db.created_at else None,
            "updated_at": scorecard_db.updated_at.isoformat() if scorecard_db.updated_at else None,
            "entries": entries,
            **status,
        }
        
    except Exception as e:
        print(f"ERROR get_scorecard (DB): {e}")
        return None
    finally:
        db.close()


def list_scorecards(
    tenant_id: UUID,
    policy_ids: Optional[List[UUID | str]] = None,
    period: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List scorecards - from database"""
    return _list_scorecards(tenant_id, policy_ids, period)


def _list_scorecards(
    tenant_id: UUID,
    policy_ids: Optional[List[UUID | str]] = None,
    period: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List scorecards from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(ScorecardDB).filter(ScorecardDB.tenant_id == tenant_id)
        
        # Filter by policy_ids if provided
        if policy_ids:
            policy_ids_uuid = [UUID(pid) if isinstance(pid, str) else pid for pid in policy_ids]
            query = query.filter(ScorecardDB.policy_id.in_(policy_ids_uuid))
        
        # Filter by period if provided
        if period:
            query = query.filter(ScorecardDB.period == period)
        
        # Sort by period descending (most recent first)
        scorecards_db = query.order_by(desc(ScorecardDB.period)).all()
        
        # Convert to dict format (same as file-based)
        result = []
        for scorecard_db in scorecards_db:
            # Get entries
            entries_db = db.query(ScorecardEntryDB).filter(
                ScorecardEntryDB.scorecard_id == scorecard_db.id
            ).all()
            
            entries = [
                {
                    "dimension": entry.dimension,
                    "metric_name": entry.metric_name,
                    "metric_value": entry.metric_value,
                    "metric_unit": entry.metric_unit,
                    "trend": entry.trend,
                }
                for entry in entries_db
            ]
            status = _status_fields_from_row(
                scorecard_db.weights if scorecard_db.weights else {},
                entries,
                scorecard_db.effectiveness_index,
            )
            result.append({
                "id": str(scorecard_db.id),
                "policy_id": str(scorecard_db.policy_id),
                "period": scorecard_db.period,
                "effectiveness_index": scorecard_db.effectiveness_index,
                "cost_impact_score": scorecard_db.cost_impact_score,
                "behavioral_risk_score": scorecard_db.behavioral_risk_score,
                "access_impact_score": scorecard_db.access_impact_score,
                "regulatory_defensibility_score": scorecard_db.regulatory_defensibility_score,
                "weights": scorecard_db.weights if scorecard_db.weights else {},
                "created_at": scorecard_db.created_at.isoformat() if scorecard_db.created_at else None,
                "updated_at": scorecard_db.updated_at.isoformat() if scorecard_db.updated_at else None,
                "entries": entries,
                **status,
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR list_scorecards (DB): {e}")
        return []
    finally:
        db.close()
