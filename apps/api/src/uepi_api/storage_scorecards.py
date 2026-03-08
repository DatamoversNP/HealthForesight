"""Scorecard file storage operations - database only"""
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from uepi_api.models.scorecard import Scorecard as ScorecardDB, ScorecardEntry as ScorecardEntryDB
from sqlalchemy import desc


def generate_scorecard_from_predicted_impact(
    policy_id: UUID | str,
    predicted_impact: Dict[str, Any],
    period: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a scorecard from predicted impact data"""
    if period is None:
        # Generate period from current date (e.g., "2026-Q1")
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        period = f"{now.year}-Q{quarter}"
    
    # Extract metrics from predicted impact
    # Predicted impact can have different structures:
    # 1. Old format: predicted_impact.projected_impact.cost_savings
    # 2. New format: predicted_impact.metrics.cost_change_total, etc.
    projected = predicted_impact.get("projected_impact", {})
    metrics = predicted_impact.get("metrics", {})
    
    # Try new format first (metrics), fallback to old format (projected_impact)
    if metrics:
        cost_savings = {
            "total_savings_pct": abs(metrics.get("cost_change_pct", 0)) if metrics.get("cost_change_pct", 0) < 0 else 0
        }
        utilization_change = {
            "percent_change": metrics.get("utilization_change_pct", 0)
        }
        behavioral_response = {
            "defer_rate": abs(metrics.get("utilization_change_pct", 0)) * 0.1 if metrics.get("utilization_change_pct", 0) < 0 else 0
        }
    else:
        # Old format
        cost_savings = projected.get("cost_savings", {})
        utilization_change = projected.get("utilization_change", {})
        behavioral_response = projected.get("behavioral_response", {})
    
    # Calculate effectiveness index (0-100 composite score)
    # Components:
    # - Cost impact: 30%
    # - Behavioral risk: 25%
    # - Access impact: 25%
    # - Regulatory defensibility: 20%
    
    # Cost impact score (0-100): Higher is better (more savings, lower costs)
    cost_savings_pct = cost_savings.get("total_savings_pct", 0)
    cost_impact_score = min(100, max(0, 50 + (cost_savings_pct * 2)))  # 0% savings = 50, 25% savings = 100
    
    # Behavioral risk score (0-100): Lower risk = higher score
    defer_rate = behavioral_response.get("defer_rate", 0)
    behavioral_risk_score = min(100, max(0, 100 - (defer_rate * 200)))  # 0% defer = 100, 0.5% defer = 0
    
    # Access impact score (0-100): Based on substitution effects and access changes
    substitution_score = 80  # Default - would be calculated from substitution effects
    access_impact_score = substitution_score
    
    # Regulatory defensibility score (0-100): Based on policy type and evidence
    confidence = predicted_impact.get("confidence_score", 50)
    regulatory_defensibility_score = min(100, confidence + 20)  # Boost based on confidence
    
    # Weighted effectiveness index
    weights = {
        "cost_impact": 0.30,
        "behavioral_risk": 0.25,
        "access_impact": 0.25,
        "regulatory_defensibility": 0.20,
    }
    
    effectiveness_index = (
        cost_impact_score * weights["cost_impact"] +
        behavioral_risk_score * weights["behavioral_risk"] +
        access_impact_score * weights["access_impact"] +
        regulatory_defensibility_score * weights["regulatory_defensibility"]
    )
    
    # Create scorecard entry
    scorecard = {
        "id": str(uuid4()),
        "policy_id": str(policy_id),
        "period": period,
        "effectiveness_index": round(effectiveness_index, 2),
        "cost_impact_score": round(cost_impact_score, 2),
        "behavioral_risk_score": round(behavioral_risk_score, 2),
        "access_impact_score": round(access_impact_score, 2),
        "regulatory_defensibility_score": round(regulatory_defensibility_score, 2),
        "weights": weights,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "entries": [
            {
                "dimension": "COST",
                "metric_name": "Cost Savings %",
                "metric_value": cost_savings_pct,
                "metric_unit": "percent",
                "trend": "DOWN" if cost_savings_pct > 0 else "STABLE",
            },
            {
                "dimension": "BEHAVIORAL",
                "metric_name": "Defer Rate",
                "metric_value": defer_rate,
                "metric_unit": "percent",
                "trend": "UP" if defer_rate > 0 else "STABLE",
            },
            {
                "dimension": "ACCESS",
                "metric_name": "Utilization Change %",
                "metric_value": utilization_change.get("percent_change", 0),
                "metric_unit": "percent",
                "trend": "DOWN" if utilization_change.get("percent_change", 0) < 0 else "UP",
            },
        ],
    }
    
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
            # Update existing scorecard
            existing.effectiveness_index = scorecard.get("effectiveness_index", 0)
            existing.cost_impact_score = scorecard.get("cost_impact_score", 0)
            existing.behavioral_risk_score = scorecard.get("behavioral_risk_score", 0)
            existing.access_impact_score = scorecard.get("access_impact_score", 0)
            existing.regulatory_defensibility_score = scorecard.get("regulatory_defensibility_score", 0)
            existing.weights = scorecard.get("weights", {})
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
                effectiveness_index=scorecard.get("effectiveness_index", 0),
                cost_impact_score=scorecard.get("cost_impact_score", 0),
                behavioral_risk_score=scorecard.get("behavioral_risk_score", 0),
                access_impact_score=scorecard.get("access_impact_score", 0),
                regulatory_defensibility_score=scorecard.get("regulatory_defensibility_score", 0),
                weights=scorecard.get("weights", {}),
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
            "entries": [
                {
                    "dimension": entry.dimension,
                    "metric_name": entry.metric_name,
                    "metric_value": entry.metric_value,
                    "metric_unit": entry.metric_unit,
                    "trend": entry.trend,
                }
                for entry in entries_db
            ],
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
                "entries": [
                    {
                        "dimension": entry.dimension,
                        "metric_name": entry.metric_name,
                        "metric_value": entry.metric_value,
                        "metric_unit": entry.metric_unit,
                        "trend": entry.trend,
                    }
                    for entry in entries_db
                ],
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR list_scorecards (DB): {e}")
        return []
    finally:
        db.close()
