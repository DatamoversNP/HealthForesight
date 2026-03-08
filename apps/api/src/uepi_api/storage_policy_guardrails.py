"""Policy guardrails storage - database only"""
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.policy import PolicyGuardrail, Policy
from uepi_common.models_enhanced import PolicyGuardrail as PydanticGuardrail
from sqlalchemy import or_


def create_guardrail(
    tenant_id: UUID,
    policy_id: UUID,
    guardrail_data: Dict[str, Any]
) -> PydanticGuardrail:
    """Create a new policy guardrail - stored in database"""
    return _create_guardrail(tenant_id, policy_id, guardrail_data)


def _create_guardrail(
    tenant_id: UUID,
    policy_id: UUID,
    guardrail_data: Dict[str, Any]
) -> PydanticGuardrail:
    """Create guardrail in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Verify policy exists and convert policy_id if needed
        if isinstance(policy_id, str):
            policy = db.query(Policy).filter(
                Policy.tenant_id == tenant_id,
                or_(
                    Policy.id == policy_id,
                    Policy.policy_metadata_json['policy_id'].astext == policy_id
                )
            ).first()
            if not policy:
                raise ValueError(f"Policy {policy_id} not found")
            policy_id_uuid = policy.id
        else:
            policy_id_uuid = policy_id
            policy = db.query(Policy).filter(
                Policy.id == policy_id_uuid,
                Policy.tenant_id == tenant_id
            ).first()
            if not policy:
                raise ValueError(f"Policy {policy_id} not found")
        
        # Create guardrail in database
        guardrail = PolicyGuardrail(
            tenant_id=tenant_id,
            policy_id=policy_id_uuid,
            metric_name=guardrail_data.get("metric_name", ""),
            threshold_type=guardrail_data.get("threshold_type", "max"),
            threshold_value=float(guardrail_data.get("threshold_value", 0.0)),
            action=guardrail_data.get("action", "alert"),
            description=guardrail_data.get("description", ""),
            triggered=False,
        )
        
        db.add(guardrail)
        db.commit()
        db.refresh(guardrail)
        
        # Return Pydantic model for compatibility
        return PydanticGuardrail(
            metric_name=guardrail.metric_name,
            threshold_type=guardrail.threshold_type,
            threshold_value=guardrail.threshold_value,
            action=guardrail.action,
            description=guardrail.description,
        )
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create guardrail: {e}")
    finally:
        db.close()


def get_guardrails(
    tenant_id: UUID,
    policy_id: UUID | str
) -> List[Dict[str, Any]]:
    """Get all guardrails for a policy - from database"""
    return _get_guardrails(tenant_id, policy_id)


def _get_guardrails(
    tenant_id: UUID,
    policy_id: UUID | str
) -> List[Dict[str, Any]]:
    """Get guardrails from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Convert policy_id to UUID if needed
        if isinstance(policy_id, str):
            try:
                policy_id_uuid = UUID(policy_id)
            except ValueError:
                # Not a UUID, find policy by string ID first
                policy = db.query(Policy).filter(
                    Policy.tenant_id == tenant_id,
                    or_(
                        Policy.id == policy_id,
                        Policy.policy_metadata_json['policy_id'].astext == policy_id
                    )
                ).first()
                if not policy:
                    return []
                policy_id_uuid = policy.id
        else:
            policy_id_uuid = policy_id
        
        # Query guardrails from database
        guardrails = db.query(PolicyGuardrail).filter(
            PolicyGuardrail.tenant_id == tenant_id,
            PolicyGuardrail.policy_id == policy_id_uuid
        ).all()
        
        # Convert to dict format (same as file-based)
        result = []
        for guardrail in guardrails:
            guardrail_dict = {
                "guardrail_id": str(guardrail.id),
                "metric_name": guardrail.metric_name,
                "threshold_type": guardrail.threshold_type,
                "threshold_value": guardrail.threshold_value,
                "action": guardrail.action,
                "description": guardrail.description,
                "triggered": guardrail.triggered,
                "last_checked_at": guardrail.last_checked_at.isoformat() if guardrail.last_checked_at else None,
                "created_at": guardrail.created_at.isoformat() if guardrail.created_at else None,
                "updated_at": guardrail.updated_at.isoformat() if guardrail.updated_at else None,
            }
            result.append(guardrail_dict)
        
        return result
        
    except Exception as e:
        print(f"ERROR get_guardrails (DB): {e}")
        return []
    finally:
        db.close()


def update_guardrail(
    tenant_id: UUID,
    policy_id: UUID,
    guardrail_id: str,
    updates: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Update a policy guardrail - stored in database"""
    return _update_guardrail(tenant_id, policy_id, guardrail_id, updates)


def _update_guardrail(
    tenant_id: UUID,
    policy_id: UUID,
    guardrail_id: str,
    updates: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Update guardrail in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        guardrail_uuid = UUID(guardrail_id)
        guardrail = db.query(PolicyGuardrail).filter(
            PolicyGuardrail.id == guardrail_uuid,
            PolicyGuardrail.tenant_id == tenant_id,
            PolicyGuardrail.policy_id == policy_id
        ).first()
        
        if not guardrail:
            return None
        
        # Update fields
        if "metric_name" in updates:
            guardrail.metric_name = updates["metric_name"]
        if "threshold_type" in updates:
            guardrail.threshold_type = updates["threshold_type"]
        if "threshold_value" in updates:
            guardrail.threshold_value = float(updates["threshold_value"])
        if "action" in updates:
            guardrail.action = updates["action"]
        if "description" in updates:
            guardrail.description = updates["description"]
        if "triggered" in updates:
            guardrail.triggered = bool(updates["triggered"])
        if "last_checked_at" in updates:
            guardrail.last_checked_at = datetime.fromisoformat(updates["last_checked_at"].replace("Z", "+00:00")) if isinstance(updates["last_checked_at"], str) else updates["last_checked_at"]
        
        db.commit()
        db.refresh(guardrail)
        
        # Return as dict (same format as file-based)
        return {
            "guardrail_id": str(guardrail.id),
            "metric_name": guardrail.metric_name,
            "threshold_type": guardrail.threshold_type,
            "threshold_value": guardrail.threshold_value,
            "action": guardrail.action,
            "description": guardrail.description,
            "triggered": guardrail.triggered,
            "last_checked_at": guardrail.last_checked_at.isoformat() if guardrail.last_checked_at else None,
            "created_at": guardrail.created_at.isoformat() if guardrail.created_at else None,
            "updated_at": guardrail.updated_at.isoformat() if guardrail.updated_at else None,
        }
        
    except ValueError:
        # guardrail_id is not a valid UUID, return None
        return None
    except Exception as e:
        db.rollback()
        print(f"ERROR update_guardrail (DB): {e}")
        return None
    finally:
        db.close()


def delete_guardrail(
    tenant_id: UUID,
    policy_id: UUID,
    guardrail_id: str
) -> bool:
    """Delete a policy guardrail - stored in database"""
    return _delete_guardrail(tenant_id, policy_id, guardrail_id)


def _delete_guardrail(
    tenant_id: UUID,
    policy_id: UUID,
    guardrail_id: str
) -> bool:
    """Delete guardrail from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        guardrail_uuid = UUID(guardrail_id)
        guardrail = db.query(PolicyGuardrail).filter(
            PolicyGuardrail.id == guardrail_uuid,
            PolicyGuardrail.tenant_id == tenant_id,
            PolicyGuardrail.policy_id == policy_id
        ).first()
        
        if not guardrail:
            return False
        
        db.delete(guardrail)
        db.commit()
        return True
        
    except ValueError:
        # guardrail_id is not a valid UUID
        return False
    except Exception as e:
        db.rollback()
        print(f"ERROR delete_guardrail (DB): {e}")
        return False
    finally:
        db.close()


def check_guardrails(
    tenant_id: UUID,
    policy_id: UUID,
    metrics: Dict[str, float]
) -> List[Dict[str, Any]]:
    """Check if any guardrails are triggered based on current metrics"""
    guardrails = get_guardrails(tenant_id, policy_id)
    triggered = []
    
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        for guardrail_dict in guardrails:
            guardrail_id = guardrail_dict.get("guardrail_id")
            metric_name = guardrail_dict.get("metric_name")
            threshold_type = guardrail_dict.get("threshold_type", "max")
            threshold_value = guardrail_dict.get("threshold_value", 0.0)
            
            if metric_name not in metrics:
                continue
            
            current_value = metrics[metric_name]
            is_triggered = False
            
            if threshold_type == "max":
                is_triggered = current_value > threshold_value
            elif threshold_type == "min":
                is_triggered = current_value < threshold_value
            elif threshold_type == "change_pct":
                # For change_pct, we'd need baseline value - simplified for now
                is_triggered = abs(current_value) > abs(threshold_value)
            
            # Update guardrail in database
            if guardrail_id:
                try:
                    guardrail_uuid = UUID(guardrail_id)
                    guardrail = db.query(PolicyGuardrail).filter(
                        PolicyGuardrail.id == guardrail_uuid,
                        PolicyGuardrail.tenant_id == tenant_id,
                        PolicyGuardrail.policy_id == policy_id
                    ).first()
                    
                    if guardrail:
                        guardrail.triggered = is_triggered
                        guardrail.last_checked_at = datetime.utcnow()
                        db.commit()
                except (ValueError, Exception) as e:
                    print(f"ERROR updating guardrail {guardrail_id}: {e}")
                    db.rollback()
            
            if is_triggered:
                guardrail_dict["triggered"] = True
                guardrail_dict["current_value"] = current_value
                triggered.append(guardrail_dict)
            else:
                guardrail_dict["triggered"] = False
        
        return triggered
        
    except Exception as e:
        print(f"ERROR check_guardrails (DB): {e}")
        return []
    finally:
        db.close()
