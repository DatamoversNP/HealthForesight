"""Risk storage - database only"""
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.risk import Risk
from uepi_common.models_enhanced import RiskRegister, RiskDriver


def _driver_probability(driver_data: Dict[str, Any]) -> float:
    p = driver_data.get("probability")
    if p is not None:
        return max(0.0, min(1.0, float(p)))
    uc = float(driver_data.get("uncertainty_contribution", 0.0))
    if uc > 1.0:
        return max(0.0, min(1.0, uc / 100.0))
    return max(0.0, min(1.0, uc))


def _driver_impact_label(driver_data: Dict[str, Any]) -> str:
    explicit = driver_data.get("impact")
    if explicit and isinstance(explicit, str) and explicit.strip():
        return explicit.strip().upper()
    score = float(driver_data.get("impact_score", 0.5))
    if score >= 0.65:
        return "HIGH"
    if score >= 0.35:
        return "MEDIUM"
    return "LOW"


def _safe_uuid(value: Any) -> Optional[UUID]:
    """Safely convert value to UUID"""
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return UUID(value)
        except (ValueError, AttributeError):
            return None
    return None


def create_or_update_risk_register(
    tenant_id: UUID,
    risk_data: Dict[str, Any]
) -> RiskRegister:
    """Create or update a risk register for a policy - stored in database"""
    return _create_or_update_risk_register(tenant_id, risk_data)


def _create_or_update_risk_register(
    tenant_id: UUID,
    risk_data: Dict[str, Any]
) -> RiskRegister:
    """Create or update risk register in database"""
    from uepi_api.database import SessionLocal
    from collections import defaultdict
    
    db: Session = SessionLocal()
    try:
        policy_id = _safe_uuid(risk_data.get("policy_id"))
        if not policy_id:
            raise ValueError("policy_id is required")
        
        # Get existing risks for this policy
        existing_risks = db.query(Risk).filter(
            Risk.tenant_id == tenant_id,
            Risk.policy_id == policy_id
        ).all()
        
        # Create a map of existing risks by driver name
        existing_by_driver = {r.risk_driver: r for r in existing_risks}
        
        # Parse risk drivers from input
        risk_drivers_data = risk_data.get("top_drivers", [])
        overall_risk_score = risk_data.get("overall_risk_score", 0.0)
        
        # Update or create risk records
        for driver_data in risk_drivers_data:
            driver_name = driver_data.get("driver_name", "")
            if not driver_name:
                continue
            
            if driver_name in existing_by_driver:
                # Update existing risk
                risk = existing_by_driver[driver_name]
                if not risk.risk_id:
                    risk.risk_id = str(uuid4())
                risk.risk_score = driver_data.get("impact_score", 0.0)
                risk.probability = _driver_probability(driver_data)
                risk.impact = _driver_impact_label(driver_data)
                risk.description = driver_data.get("mitigation_action")
                risk.owner_user_id = _safe_uuid(driver_data.get("owner"))
                risk.status = risk_data.get("status", "ACTIVE")
            else:
                # Create new risk
                risk_id = driver_data.get("risk_id") or str(uuid4())
                risk = Risk(
                    tenant_id=tenant_id,
                    policy_id=policy_id,
                    risk_id=risk_id,
                    risk_driver=driver_name,
                    risk_score=driver_data.get("impact_score", 0.0),
                    probability=_driver_probability(driver_data),
                    impact=_driver_impact_label(driver_data),
                    description=driver_data.get("mitigation_action"),
                    owner_user_id=_safe_uuid(driver_data.get("owner")),
                    status=risk_data.get("status", "ACTIVE"),
                )
                db.add(risk)
        
        db.commit()
        
        # Return RiskRegister format
        updated_risks = db.query(Risk).filter(
            Risk.tenant_id == tenant_id,
            Risk.policy_id == policy_id
        ).all()
        
        risk_drivers = []
        max_score = 0.0
        last_updated = None
        
        for risk in updated_risks:
            risk_drivers.append(RiskDriver(
                driver_name=risk.risk_driver,
                impact_score=risk.risk_score if risk.risk_score else 0.0,
                uncertainty_contribution=(risk.probability or 0.0) * 100.0,
                mitigation_action=risk.description,
                owner=risk.owner_user_id,
            ))
            max_score = max(max_score, risk.risk_score if risk.risk_score else 0.0)
            if risk.updated_at and (not last_updated or risk.updated_at > last_updated):
                last_updated = risk.updated_at
        
        return RiskRegister(
            policy_id=policy_id,
            top_drivers=risk_drivers,
            overall_risk_score=overall_risk_score or max_score,
            last_updated=last_updated or datetime.utcnow(),
        )
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create/update risk register: {e}")
    finally:
        db.close()


def get_risk_register(
    tenant_id: UUID,
    policy_id: UUID
) -> Optional[RiskRegister]:
    """Get risk register for a policy - from database"""
    return _get_risk_register(tenant_id, policy_id)


def _get_risk_register(
    tenant_id: UUID,
    policy_id: UUID
) -> Optional[RiskRegister]:
    """Get risk register from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Get all risks for this policy
        risks = db.query(Risk).filter(
            Risk.tenant_id == tenant_id,
            Risk.policy_id == policy_id
        ).all()
        
        if not risks:
            return None
        
        # Convert to RiskRegister format
        risk_drivers = []
        overall_risk_score = 0.0
        last_updated = None
        
        for risk in risks:
            risk_drivers.append(RiskDriver(
                driver_name=risk.risk_driver,
                impact_score=risk.risk_score if risk.risk_score else 0.0,
                uncertainty_contribution=(risk.probability or 0.0) * 100.0,
                mitigation_action=risk.description,
                owner=risk.owner_user_id,
            ))
            overall_risk_score = max(overall_risk_score, risk.risk_score if risk.risk_score else 0.0)
            if risk.updated_at and (not last_updated or risk.updated_at > last_updated):
                last_updated = risk.updated_at
        
        return RiskRegister(
            policy_id=policy_id,
            top_drivers=risk_drivers,
            overall_risk_score=overall_risk_score,
            last_updated=last_updated or datetime.utcnow(),
        )
        
    except Exception as e:
        print(f"ERROR get_risk_register (DB): {e}")
        return None
    finally:
        db.close()


def list_risk_registers(
    tenant_id: UUID,
    min_risk_score: Optional[float] = None
) -> List[RiskRegister]:
    """List all risk registers for a tenant - from database"""
    return _list_risk_registers(tenant_id, min_risk_score)


def _list_risk_registers(
    tenant_id: UUID,
    min_risk_score: Optional[float] = None
) -> List[RiskRegister]:
    """List risk registers from database"""
    from uepi_api.database import SessionLocal
    from sqlalchemy import desc
    from collections import defaultdict
    
    db: Session = SessionLocal()
    try:
        query = db.query(Risk).filter(Risk.tenant_id == tenant_id)
        
        # Filter by min_risk_score if provided
        if min_risk_score is not None:
            query = query.filter(Risk.risk_score >= min_risk_score)
        
        # Sort by updated_at descending (newest first)
        risks = query.order_by(desc(Risk.updated_at)).all()
        
        # Group risks by policy_id
        risks_by_policy = defaultdict(list)
        for risk in risks:
            risks_by_policy[risk.policy_id].append(risk)
        
        # Convert to RiskRegister format (one per policy)
        result = []
        for policy_id, policy_risks in risks_by_policy.items():
            risk_drivers = []
            overall_risk_score = 0.0
            last_updated = None
            
            for risk in policy_risks:
                risk_drivers.append(RiskDriver(
                    driver_name=risk.risk_driver,
                    impact_score=risk.risk_score if risk.risk_score else 0.0,
                    uncertainty_contribution=(risk.probability or 0.0) * 100.0,
                    mitigation_action=risk.description,
                    owner=risk.owner_user_id,
                ))
                overall_risk_score = max(overall_risk_score, risk.risk_score if risk.risk_score else 0.0)
                if risk.updated_at and (not last_updated or risk.updated_at > last_updated):
                    last_updated = risk.updated_at
            
            result.append(RiskRegister(
                policy_id=policy_id,
                top_drivers=risk_drivers,
                overall_risk_score=overall_risk_score,
                last_updated=last_updated or datetime.utcnow(),
            ))
        
        # Sort by overall_risk_score descending
        return sorted(result, key=lambda r: r.overall_risk_score, reverse=True)
        
    except Exception as e:
        print(f"ERROR list_risk_registers (DB): {e}")
        return []
    finally:
        db.close()


def update_risk_driver(
    tenant_id: UUID,
    policy_id: UUID,
    driver_name: str,
    updates: Dict[str, Any]
) -> Optional[RiskRegister]:
    """Update a specific risk driver in a risk register"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        risk = db.query(Risk).filter(
            Risk.tenant_id == tenant_id,
            Risk.policy_id == policy_id,
            Risk.risk_driver == driver_name
        ).first()
        
        if not risk:
            return None
        
        # Update fields
        if "impact_score" in updates:
            risk.risk_score = updates["impact_score"]
        if "uncertainty_contribution" in updates:
            risk.probability = _driver_probability(
                {"uncertainty_contribution": updates["uncertainty_contribution"]}
            )
        if "mitigation_action" in updates:
            risk.description = updates["mitigation_action"]
        if "owner" in updates:
            risk.owner_user_id = _safe_uuid(updates["owner"])
        
        db.commit()
        db.refresh(risk)
        
        # Return updated risk register
        return get_risk_register(tenant_id, policy_id)
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to update risk driver: {e}")
    finally:
        db.close()
