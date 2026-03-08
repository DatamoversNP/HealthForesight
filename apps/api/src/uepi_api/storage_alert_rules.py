"""Alert Rules Storage Module - database only"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.models.alert import AlertRule as AlertRuleDB, AlertEvent as AlertEventDB
from uepi_common.models_enhanced import AlertRule, AlertEvent


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


# Alert Rules
def create_alert_rule(
    tenant_id: UUID,
    rule_data: Dict[str, Any]
) -> AlertRule:
    """Create a new alert rule - stored in database"""
    return _create_alert_rule(tenant_id, rule_data)


def _create_alert_rule(
    tenant_id: UUID,
    rule_data: Dict[str, Any]
) -> AlertRule:
    """Create alert rule in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        rule_id = str(_safe_uuid(rule_data.get("rule_id")) or uuid4())
        
        # Store condition in JSONB
        condition_json = {
            "signal_type": rule_data.get("signal_type", "unknown"),
            "threshold": float(rule_data.get("threshold", 0.0)),
            "condition": rule_data.get("condition", "greater_than"),
        }
        
        # Create alert rule in database
        rule_db = AlertRuleDB(
            tenant_id=tenant_id,
            rule_id=rule_id,
            name=rule_data.get("rule_name", f"Rule {rule_id}"),
            description=rule_data.get("description"),
            condition_json=condition_json,
            action=rule_data.get("action", "NOTIFY"),
            action_config_json=rule_data.get("action_config", {}),
            enabled=rule_data.get("enabled", True),
        )
        
        db.add(rule_db)
        db.commit()
        db.refresh(rule_db)
        
        # Return Pydantic model for compatibility
        condition = rule_db.condition_json if rule_db.condition_json else {}
        return AlertRule(
            rule_id=UUID(rule_db.rule_id),
            rule_name=rule_db.name,
            signal_type=condition.get("signal_type", "unknown"),
            threshold=condition.get("threshold", 0.0),
            condition=condition.get("condition", "greater_than"),
            action=rule_db.action,
            enabled=rule_db.enabled,
            created_at=rule_db.created_at,
        )
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create alert rule: {e}")
    finally:
        db.close()


def get_alert_rule(
    tenant_id: UUID,
    rule_id: UUID
) -> Optional[AlertRule]:
    """Get alert rule - from database"""
    return _get_alert_rule(tenant_id, rule_id)


def _get_alert_rule(
    tenant_id: UUID,
    rule_id: UUID
) -> Optional[AlertRule]:
    """Get alert rule from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        rule_db = db.query(AlertRuleDB).filter(
            AlertRuleDB.tenant_id == tenant_id,
            AlertRuleDB.rule_id == str(rule_id)
        ).first()
        
        if not rule_db:
            return None
        
        # Return Pydantic model for compatibility
        condition = rule_db.condition_json if rule_db.condition_json else {}
        return AlertRule(
            rule_id=UUID(rule_db.rule_id),
            rule_name=rule_db.name,
            signal_type=condition.get("signal_type", "unknown"),
            threshold=condition.get("threshold", 0.0),
            condition=condition.get("condition", "greater_than"),
            action=rule_db.action,
            enabled=rule_db.enabled,
            created_at=rule_db.created_at,
        )
        
    except Exception as e:
        print(f"ERROR get_alert_rule (DB): {e}")
        return None
    finally:
        db.close()


def list_alert_rules(
    tenant_id: UUID,
    enabled_only: bool = False
) -> List[AlertRule]:
    """List alert rules - from database"""
    return _list_alert_rules(tenant_id, enabled_only)


def _list_alert_rules(
    tenant_id: UUID,
    enabled_only: bool = False
) -> List[AlertRule]:
    """List alert rules from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        query = db.query(AlertRuleDB).filter(AlertRuleDB.tenant_id == tenant_id)
        
        # Filter by enabled if provided
        if enabled_only:
            query = query.filter(AlertRuleDB.enabled == True)
        
        rules_db = query.all()
        
        # Convert to Pydantic models for compatibility
        result = []
        for rule_db in rules_db:
            condition = rule_db.condition_json if rule_db.condition_json else {}
            result.append(AlertRule(
                rule_id=UUID(rule_db.rule_id),
                rule_name=rule_db.name,
                signal_type=condition.get("signal_type", "unknown"),
                threshold=condition.get("threshold", 0.0),
                condition=condition.get("condition", "greater_than"),
                action=rule_db.action,
                enabled=rule_db.enabled,
                created_at=rule_db.created_at,
            ))
        
        return result
        
    except Exception as e:
        print(f"ERROR list_alert_rules (DB): {e}")
        return []
    finally:
        db.close()


def update_alert_rule(
    tenant_id: UUID,
    rule_id: UUID,
    updates: Dict[str, Any]
) -> Optional[AlertRule]:
    """Update alert rule - stored in database"""
    return _update_alert_rule(tenant_id, rule_id, updates)


def _update_alert_rule(
    tenant_id: UUID,
    rule_id: UUID,
    updates: Dict[str, Any]
) -> Optional[AlertRule]:
    """Update alert rule in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        rule_db = db.query(AlertRuleDB).filter(
            AlertRuleDB.tenant_id == tenant_id,
            AlertRuleDB.rule_id == str(rule_id)
        ).first()
        
        if not rule_db:
            return None
        
        # Update fields
        if "rule_name" in updates or "name" in updates:
            rule_db.name = updates.get("rule_name") or updates.get("name", rule_db.name)
        if "description" in updates:
            rule_db.description = updates.get("description")
        if "action" in updates:
            rule_db.action = updates["action"]
        if "action_config" in updates:
            rule_db.action_config_json = updates["action_config"]
        if "enabled" in updates:
            rule_db.enabled = bool(updates["enabled"])
        
        # Update condition if any condition fields changed
        if any(k in updates for k in ["signal_type", "threshold", "condition"]):
            condition = rule_db.condition_json if rule_db.condition_json else {}
            if "signal_type" in updates:
                condition["signal_type"] = updates["signal_type"]
            if "threshold" in updates:
                condition["threshold"] = float(updates["threshold"])
            if "condition" in updates:
                condition["condition"] = updates["condition"]
            rule_db.condition_json = condition
        
        db.commit()
        db.refresh(rule_db)
        
        # Return Pydantic model
        condition = rule_db.condition_json if rule_db.condition_json else {}
        return AlertRule(
            rule_id=UUID(rule_db.rule_id),
            rule_name=rule_db.name,
            signal_type=condition.get("signal_type", "unknown"),
            threshold=condition.get("threshold", 0.0),
            condition=condition.get("condition", "greater_than"),
            action=rule_db.action,
            enabled=rule_db.enabled,
            created_at=rule_db.created_at,
        )
        
    except Exception as e:
        db.rollback()
        print(f"ERROR update_alert_rule (DB): {e}")
        return None
    finally:
        db.close()


# Alert Events
def create_alert_event(
    tenant_id: UUID,
    event_data: Dict[str, Any]
) -> AlertEvent:
    """Create a new alert event - stored in database"""
    return _create_alert_event(tenant_id, event_data)


def _create_alert_event(
    tenant_id: UUID,
    event_data: Dict[str, Any]
) -> AlertEvent:
    """Create alert event in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        event_id = str(_safe_uuid(event_data.get("event_id")) or uuid4())
        
        # Get rule_id (UUID) from rule_id (string or UUID)
        rule_id_str = str(event_data.get("rule_id", ""))
        rule_id_uuid = None
        if rule_id_str:
            rule = db.query(AlertRuleDB).filter(
                AlertRuleDB.tenant_id == tenant_id,
                AlertRuleDB.rule_id == rule_id_str
            ).first()
            if rule:
                rule_id_uuid = rule.id
        
        # Parse policy_id if provided
        policy_id = None
        if event_data.get("policy_id"):
            policy_id = UUID(event_data["policy_id"]) if isinstance(event_data["policy_id"], str) else event_data["policy_id"]
        
        # Parse dates
        triggered_at = datetime.fromisoformat(event_data["triggered_at"].replace("Z", "+00:00")) if isinstance(event_data.get("triggered_at"), str) else event_data.get("triggered_at", datetime.utcnow())
        resolved_at = datetime.fromisoformat(event_data["resolved_at"].replace("Z", "+00:00")) if isinstance(event_data.get("resolved_at"), str) else event_data.get("resolved_at")
        
        # Create alert event in database
        event_db = AlertEventDB(
            tenant_id=tenant_id,
            rule_id=rule_id_uuid,
            policy_id=policy_id,
            event_id=event_id,
            severity=event_data.get("severity", "MEDIUM"),
            details_json=event_data.get("details", {}),
            triggered_at=triggered_at,
            resolved_at=resolved_at,
            resolved_by_user_id=UUID(event_data["resolved_by_user_id"]) if event_data.get("resolved_by_user_id") else None,
        )
        
        db.add(event_db)
        db.commit()
        db.refresh(event_db)
        
        # Return Pydantic model for compatibility
        # Note: AlertEvent Pydantic model may have different fields, adjust as needed
        return AlertEvent(
            event_id=UUID(event_id),
            rule_id=UUID(rule_id_str) if rule_id_str else None,
            policy_id=policy_id,
            severity=event_db.severity,
            details=event_db.details_json if event_db.details_json else {},
            triggered_at=event_db.triggered_at,
            resolved_at=event_db.resolved_at,
            resolved_by_user_id=event_db.resolved_by_user_id,
        )
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create alert event: {e}")
    finally:
        db.close()


def list_alert_events(
    tenant_id: UUID,
    policy_id: Optional[UUID] = None,
    rule_id: Optional[UUID] = None,
    severity: Optional[str] = None,
    resolved_only: Optional[bool] = None
) -> List[AlertEvent]:
    """List alert events - from database"""
    return _list_alert_events(tenant_id, policy_id, rule_id, severity, resolved_only)


def _list_alert_events(
    tenant_id: UUID,
    policy_id: Optional[UUID] = None,
    rule_id: Optional[UUID] = None,
    severity: Optional[str] = None,
    resolved_only: Optional[bool] = None
) -> List[AlertEvent]:
    """List alert events from database"""
    from uepi_api.database import SessionLocal
    from sqlalchemy import desc
    
    db: Session = SessionLocal()
    try:
        query = db.query(AlertEventDB).filter(AlertEventDB.tenant_id == tenant_id)
        
        # Apply filters
        if policy_id:
            query = query.filter(AlertEventDB.policy_id == policy_id)
        if rule_id:
            # Find rule by rule_id string
            rule = db.query(AlertRuleDB).filter(
                AlertRuleDB.tenant_id == tenant_id,
                AlertRuleDB.rule_id == str(rule_id)
            ).first()
            if rule:
                query = query.filter(AlertEventDB.rule_id == rule.id)
        if severity:
            query = query.filter(AlertEventDB.severity == severity)
        if resolved_only is not None:
            if resolved_only:
                query = query.filter(AlertEventDB.resolved_at.isnot(None))
            else:
                query = query.filter(AlertEventDB.resolved_at.is_(None))
        
        # Sort by triggered_at descending
        events_db = query.order_by(desc(AlertEventDB.triggered_at)).all()
        
        # Convert to Pydantic models
        result = []
        for event_db in events_db:
            # Get rule_id string for compatibility
            rule_id_str = None
            if event_db.rule_id:
                rule = db.query(AlertRuleDB).filter(AlertRuleDB.id == event_db.rule_id).first()
                if rule:
                    rule_id_str = rule.rule_id
            
            result.append(AlertEvent(
                event_id=UUID(event_db.event_id),
                rule_id=UUID(rule_id_str) if rule_id_str else None,
                policy_id=event_db.policy_id,
                severity=event_db.severity,
                details=event_db.details_json if event_db.details_json else {},
                triggered_at=event_db.triggered_at,
                resolved_at=event_db.resolved_at,
                resolved_by_user_id=event_db.resolved_by_user_id,
            ))
        
        return result
        
    except Exception as e:
        print(f"ERROR list_alert_events (DB): {e}")
        return []
    finally:
        db.close()
