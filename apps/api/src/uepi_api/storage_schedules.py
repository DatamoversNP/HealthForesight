"""Schedule storage - database only"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from uepi_api.models.schedule import Schedule


def _parse_frequency_from_cron(cron_expression: Optional[str]) -> str:
    """Parse frequency from cron expression"""
    if not cron_expression:
        return "DAILY"
    
    parts = cron_expression.split()
    if len(parts) >= 6:
        if parts[4] != "*":  # day_of_week specified (weekly)
            return "WEEKLY"
        elif parts[3] != "*":  # day_of_month specified (monthly)
            return "MONTHLY"
    return "DAILY"


def _parse_time_from_cron(cron_expression: Optional[str]) -> Optional[str]:
    """Parse time from cron expression"""
    if not cron_expression:
        return None
    
    parts = cron_expression.split()
    if len(parts) >= 3:
        minute = parts[0]
        hour = parts[1]
        return f"{hour.zfill(2)}:{minute.zfill(2)}"
    return None


def _build_cron_expression(frequency: str, time_str: str, day_of_week: Optional[int] = None, day_of_month: Optional[int] = None) -> str:
    """Build cron expression from schedule parameters"""
    try:
        hour, minute = map(int, time_str.split(":"))
    except:
        hour, minute = 9, 0
    
    if frequency == "DAILY":
        return f"{minute} {hour} * * *"
    elif frequency == "WEEKLY":
        dow = day_of_week if day_of_week is not None else 0
        return f"{minute} {hour} * * {dow}"
    elif frequency == "MONTHLY":
        dom = day_of_month if day_of_month is not None else 1
        return f"{minute} {hour} {dom} * *"
    else:
        return f"{minute} {hour} * * *"  # Default to daily


def _calculate_next_run(schedule: Dict[str, Any]) -> Optional[str]:
    """Calculate next run time based on schedule"""
    if not schedule.get("enabled", True):
        return None
    
    now = datetime.utcnow()
    frequency = schedule.get("frequency", "DAILY")
    time_str = schedule.get("time", "09:00")
    
    try:
        hour, minute = map(int, time_str.split(":"))
    except:
        hour, minute = 9, 0
    
    # Create datetime for today at scheduled time
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    if frequency == "DAILY":
        if next_run <= now:
            next_run += timedelta(days=1)
    elif frequency == "WEEKLY":
        day_of_week = schedule.get("day_of_week", 0)  # Monday = 0
        days_ahead = (day_of_week - now.weekday()) % 7
        if days_ahead == 0 and next_run <= now:
            days_ahead = 7
        next_run += timedelta(days=days_ahead)
        next_run = next_run.replace(hour=hour, minute=minute)
    elif frequency == "MONTHLY":
        day_of_month = schedule.get("day_of_month", 1)
        if now.day >= day_of_month:
            # Move to next month
            if now.month == 12:
                next_run = now.replace(year=now.year + 1, month=1, day=day_of_month, hour=hour, minute=minute)
            else:
                next_run = now.replace(month=now.month + 1, day=day_of_month, hour=hour, minute=minute)
        else:
            next_run = now.replace(day=day_of_month, hour=hour, minute=minute)
    
    return next_run.isoformat()


def list_schedules(tenant_id: UUID) -> List[Dict[str, Any]]:
    """List all schedules for a tenant - from database"""
    return _list_schedules(tenant_id)


def _list_schedules(tenant_id: UUID) -> List[Dict[str, Any]]:
    """List schedules from database"""
    from uepi_api.database import SessionLocal
    from sqlalchemy import desc
    
    db: Session = SessionLocal()
    try:
        schedules_db = db.query(Schedule).filter(
            Schedule.tenant_id == tenant_id
        ).order_by(desc(Schedule.created_at)).all()
        
        # Convert to dict format (same as file-based)
        result = []
        for schedule_db in schedules_db:
            # Parse cron expression to extract frequency, time, day_of_week, day_of_month
            frequency = _parse_frequency_from_cron(schedule_db.cron_expression)
            time_str = _parse_time_from_cron(schedule_db.cron_expression) or "09:00"
            day_of_week = None
            day_of_month = None
            
            if schedule_db.cron_expression:
                parts = schedule_db.cron_expression.split()
                if len(parts) >= 6:
                    if parts[4] != "*":  # day_of_week specified (weekly)
                        day_of_week = int(parts[4]) if parts[4].isdigit() else None
                    elif parts[3] != "*":  # day_of_month specified (monthly)
                        day_of_month = int(parts[3]) if parts[3].isdigit() else None
            
            config = {
                "target_type": schedule_db.target_type,
                "target_id": schedule_db.target_id,
            }
            
            result.append({
                "id": str(schedule_db.id),
                "tenant_id": str(schedule_db.tenant_id),
                "name": schedule_db.name,
                "schedule_type": schedule_db.target_type,  # Use target_type as schedule_type for compatibility
                "frequency": frequency,
                "time": time_str,
                "day_of_week": day_of_week,
                "day_of_month": day_of_month,
                "config": config,
                "enabled": schedule_db.enabled,
                "last_run": schedule_db.last_run_at.isoformat() if schedule_db.last_run_at else None,
                "next_run": schedule_db.next_run_at.isoformat() if schedule_db.next_run_at else None,
                "created_by": None,  # Not stored in DB model
                "created_at": schedule_db.created_at.isoformat() if schedule_db.created_at else None,
                "updated_at": schedule_db.updated_at.isoformat() if schedule_db.updated_at else None,
            })
        
        return result
        
    except Exception as e:
        print(f"ERROR list_schedules (DB): {e}")
        return []
    finally:
        db.close()


def get_schedule(schedule_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Get a schedule by ID - from database"""
    return _get_schedule(schedule_id, tenant_id)


def _get_schedule(schedule_id: UUID, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Get schedule from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        schedule_db = db.query(Schedule).filter(
            Schedule.id == schedule_id,
            Schedule.tenant_id == tenant_id
        ).first()
        
        if not schedule_db:
            return None
        
        # Parse cron expression to extract frequency, time, day_of_week, day_of_month
        frequency = _parse_frequency_from_cron(schedule_db.cron_expression)
        time_str = _parse_time_from_cron(schedule_db.cron_expression) or "09:00"
        day_of_week = None
        day_of_month = None
        
        if schedule_db.cron_expression:
            parts = schedule_db.cron_expression.split()
            if len(parts) >= 6:
                if parts[4] != "*":  # day_of_week specified (weekly)
                    day_of_week = int(parts[4]) if parts[4].isdigit() else None
                elif parts[3] != "*":  # day_of_month specified (monthly)
                    day_of_month = int(parts[3]) if parts[3].isdigit() else None
        
        config = {
            "target_type": schedule_db.target_type,
            "target_id": schedule_db.target_id,
        }
        
        return {
            "id": str(schedule_db.id),
            "tenant_id": str(schedule_db.tenant_id),
            "name": schedule_db.name,
            "schedule_type": schedule_db.target_type,  # Use target_type as schedule_type for compatibility
            "frequency": frequency,
            "time": time_str,
            "day_of_week": day_of_week,
            "day_of_month": day_of_month,
            "config": config,
            "enabled": schedule_db.enabled,
            "last_run": schedule_db.last_run_at.isoformat() if schedule_db.last_run_at else None,
            "next_run": schedule_db.next_run_at.isoformat() if schedule_db.next_run_at else None,
            "created_by": None,  # Not stored in DB model
            "created_at": schedule_db.created_at.isoformat() if schedule_db.created_at else None,
            "updated_at": schedule_db.updated_at.isoformat() if schedule_db.updated_at else None,
        }
        
    except Exception as e:
        print(f"ERROR get_schedule (DB): {e}")
        return None
    finally:
        db.close()


def create_schedule(
    tenant_id: UUID,
    schedule_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a new schedule - stored in database"""
    return _create_schedule(tenant_id, schedule_data)


def _create_schedule(
    tenant_id: UUID,
    schedule_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create schedule in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        # Generate schedule_id if not provided
        schedule_id = str(schedule_data.get("schedule_id") or uuid4())
        
        # Build cron expression from schedule parameters
        frequency = schedule_data.get("frequency", "DAILY")
        time_str = schedule_data.get("time", "09:00")
        day_of_week = schedule_data.get("day_of_week")
        day_of_month = schedule_data.get("day_of_month")
        cron_expression = _build_cron_expression(frequency, time_str, day_of_week, day_of_month)
        
        # Extract target info from config
        config = schedule_data.get("config", {})
        target_type = config.get("target_type") or schedule_data.get("schedule_type", "EXPORT")
        target_id = config.get("target_id") or str(schedule_data.get("target_id", ""))
        
        # Calculate next run time
        next_run = _calculate_next_run(schedule_data)
        next_run_at = datetime.fromisoformat(next_run.replace("Z", "+00:00")) if next_run else None
        
        # Create schedule in database
        schedule = Schedule(
            tenant_id=tenant_id,
            schedule_id=schedule_id,
            name=schedule_data.get("name", ""),
            description=schedule_data.get("description"),
            schedule_type="CRON",  # Always CRON for now
            cron_expression=cron_expression,
            target_type=target_type,
            target_id=target_id,
            enabled=schedule_data.get("enabled", True),
            next_run_at=next_run_at,
        )
        
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        
        # Return as dict (same format as file-based)
        return {
            "id": str(schedule.id),
            "tenant_id": str(schedule.tenant_id),
            "name": schedule.name,
            "schedule_type": schedule.target_type,
            "frequency": frequency,
            "time": time_str,
            "day_of_week": day_of_week,
            "day_of_month": day_of_month,
            "config": config,
            "enabled": schedule.enabled,
            "last_run": schedule.last_run_at.isoformat() if schedule.last_run_at else None,
            "next_run": schedule.next_run_at.isoformat() if schedule.next_run_at else None,
            "created_by": None,
            "created_at": schedule.created_at.isoformat() if schedule.created_at else None,
            "updated_at": schedule.updated_at.isoformat() if schedule.updated_at else None,
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to create schedule: {e}")
    finally:
        db.close()


def update_schedule(
    schedule_id: UUID,
    tenant_id: UUID,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Update a schedule - stored in database"""
    return _update_schedule(schedule_id, tenant_id, updates)


def _update_schedule(
    schedule_id: UUID,
    tenant_id: UUID,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Update schedule in database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        schedule_db = db.query(Schedule).filter(
            Schedule.id == schedule_id,
            Schedule.tenant_id == tenant_id
        ).first()
        
        if not schedule_db:
            return None
        
        # Get current schedule data for cron recalculation
        current_frequency = _parse_frequency_from_cron(schedule_db.cron_expression)
        current_time = _parse_time_from_cron(schedule_db.cron_expression) or "09:00"
        
        # Update fields
        if "name" in updates:
            schedule_db.name = updates["name"]
        if "description" in updates:
            schedule_db.description = updates["description"]
        if "enabled" in updates:
            schedule_db.enabled = updates["enabled"]
        
        # Update cron expression if schedule parameters changed
        frequency = updates.get("frequency", current_frequency)
        time_str = updates.get("time", current_time)
        day_of_week = updates.get("day_of_week")
        day_of_month = updates.get("day_of_month")
        
        if any(k in updates for k in ["frequency", "time", "day_of_week", "day_of_month"]):
            cron_expression = _build_cron_expression(frequency, time_str, day_of_week, day_of_month)
            schedule_db.cron_expression = cron_expression
            
            # Recalculate next_run
            schedule_data = {
                "frequency": frequency,
                "time": time_str,
                "day_of_week": day_of_week,
                "day_of_month": day_of_month,
                "enabled": schedule_db.enabled,
            }
            next_run = _calculate_next_run(schedule_data)
            schedule_db.next_run_at = datetime.fromisoformat(next_run.replace("Z", "+00:00")) if next_run else None
        
        # Update target if config changed
        if "config" in updates:
            config = updates["config"]
            if "target_type" in config:
                schedule_db.target_type = config["target_type"]
            if "target_id" in config:
                schedule_db.target_id = str(config["target_id"])
        
        # Update last_run if provided
        if "last_run" in updates:
            last_run = updates["last_run"]
            if isinstance(last_run, str):
                last_run = datetime.fromisoformat(last_run.replace("Z", "+00:00"))
            schedule_db.last_run_at = last_run
        
        db.commit()
        db.refresh(schedule_db)
        
        # Return as dict (same format as file-based)
        config = {
            "target_type": schedule_db.target_type,
            "target_id": schedule_db.target_id,
        }
        
        return {
            "id": str(schedule_db.id),
            "tenant_id": str(schedule_db.tenant_id),
            "name": schedule_db.name,
            "schedule_type": schedule_db.target_type,
            "frequency": frequency,
            "time": time_str,
            "day_of_week": day_of_week,
            "day_of_month": day_of_month,
            "config": config,
            "enabled": schedule_db.enabled,
            "last_run": schedule_db.last_run_at.isoformat() if schedule_db.last_run_at else None,
            "next_run": schedule_db.next_run_at.isoformat() if schedule_db.next_run_at else None,
            "created_by": None,
            "created_at": schedule_db.created_at.isoformat() if schedule_db.created_at else None,
            "updated_at": schedule_db.updated_at.isoformat() if schedule_db.updated_at else None,
        }
        
    except Exception as e:
        db.rollback()
        print(f"ERROR update_schedule (DB): {e}")
        return None
    finally:
        db.close()


def delete_schedule(schedule_id: UUID, tenant_id: UUID) -> bool:
    """Delete a schedule from database"""
    from uepi_api.database import SessionLocal
    
    db: Session = SessionLocal()
    try:
        schedule_db = db.query(Schedule).filter(
            Schedule.id == schedule_id,
            Schedule.tenant_id == tenant_id
        ).first()
        
        if not schedule_db:
            return False
        
        db.delete(schedule_db)
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        print(f"ERROR delete_schedule (DB): {e}")
        return False
    finally:
        db.close()
