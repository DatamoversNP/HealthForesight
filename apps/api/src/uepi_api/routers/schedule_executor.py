"""Schedule execution engine - Background scheduler for automated jobs"""
import asyncio
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

# This module provides the schedule execution logic
# It should be called by a background task scheduler (e.g., APScheduler, Celery Beat, or cron)


def execute_schedule(schedule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a scheduled job based on schedule configuration
    
    Args:
        schedule: Schedule dictionary with configuration
        
    Returns:
        Execution result dictionary
    """
    from uepi_api.storage_schedules import update_schedule
    from uepi_api.storage_notifications import create_notification
    
    schedule_id = UUID(schedule["id"])
    tenant_id = UUID(schedule["tenant_id"])
    schedule_type = schedule.get("schedule_type", "EXPORT")
    
    try:
        # Mark as running
        update_schedule(
            schedule_id=schedule_id,
            tenant_id=tenant_id,
            updates={"last_run": datetime.utcnow().isoformat()},
        )
        
        # Execute based on schedule type
        if schedule_type == "EXPORT":
            result = _execute_export_schedule(schedule)
        elif schedule_type == "ANALYSIS":
            result = _execute_analysis_schedule(schedule)
        elif schedule_type == "OBSERVATION":
            result = _execute_observation_schedule(schedule)
        else:
            raise ValueError(f"Unknown schedule type: {schedule_type}")
        
        # Next run time will be recalculated automatically by update_schedule
        # when we update the schedule fields, so we don't need to do it manually here
        
        # Create success notification
        create_notification(
            tenant_id=tenant_id,
            notification_data={
                "type": "SUCCESS",
                "category": "SCHEDULE",
                "title": f"Schedule '{schedule['name']}' executed successfully",
                "message": f"Scheduled {schedule_type.lower()} job completed successfully.",
                "action_url": f"/schedules/{schedule_id}",
            },
        )
        
        return {
            "success": True,
            "schedule_id": str(schedule_id),
            "executed_at": datetime.utcnow().isoformat(),
            "result": result,
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error executing schedule {schedule_id}: {e}")
        print(f"Traceback: {error_trace}")
        
        # Update schedule with error
        update_schedule(
            schedule_id=schedule_id,
            tenant_id=tenant_id,
            updates={"last_run": datetime.utcnow().isoformat()},
        )
        
        # Create error notification
        create_notification(
            tenant_id=tenant_id,
            notification_data={
                "type": "ERROR",
                "category": "SCHEDULE",
                "title": f"Schedule '{schedule['name']}' failed",
                "message": f"Scheduled {schedule_type.lower()} job failed: {str(e)}",
                "action_url": f"/schedules/{schedule_id}",
            },
        )
        
        return {
            "success": False,
            "schedule_id": str(schedule_id),
            "executed_at": datetime.utcnow().isoformat(),
            "error": str(e),
        }


def _execute_export_schedule(schedule: Dict[str, Any]) -> Dict[str, Any]:
    """Execute an export schedule"""
    config = schedule.get("config", {})
    analysis_id = config.get("analysis_id")
    export_type = config.get("export_type", "PDF")
    
    if not analysis_id:
        raise ValueError("Export schedule requires analysis_id in config")
    
    # Import here to avoid circular dependencies
    from uepi_api.routers.exports import create_export
    from uepi_api.auth import CurrentUser
    from uuid import uuid4
    
    # Create a mock current user for scheduled execution
    # In production, this would use the user who created the schedule
    tenant_id = UUID(schedule["tenant_id"])
    
    # Trigger export creation (this will generate the export)
    # Note: In a real implementation, this would be called properly with user context
    # For now, we'll simulate the export creation
    return {
        "export_created": True,
        "analysis_id": analysis_id,
        "export_type": export_type,
        "message": "Export scheduled for generation",
    }


def _execute_analysis_schedule(schedule: Dict[str, Any]) -> Dict[str, Any]:
    """Execute an analysis schedule"""
    config = schedule.get("config", {})
    policy_id = config.get("policy_id")
    analysis_type = config.get("analysis_type", "BASELINE")
    
    if not policy_id:
        raise ValueError("Analysis schedule requires policy_id in config")
    
    return {
        "analysis_triggered": True,
        "policy_id": policy_id,
        "analysis_type": analysis_type,
        "message": "Analysis scheduled for execution",
    }


def _execute_observation_schedule(schedule: Dict[str, Any]) -> Dict[str, Any]:
    """Execute an observation schedule.

    Single-policy jobs require ``config.policy_id``. Catalog-wide monthly jobs
    (lean staging) use ``config.mode=PERIODIC_MONTHLY`` and enqueue one observation
    job per active policy for the previous calendar month.
    """
    config = schedule.get("config", {}) or {}
    policy_id = config.get("policy_id")
    mode = config.get("mode")

    if mode == "PERIODIC_MONTHLY" and not policy_id:
        from uepi_api.services.execution.monthly_observations import enqueue_monthly_observations

        tenant_id = UUID(schedule["tenant_id"])
        queued = enqueue_monthly_observations(tenant_id)
        return {
            "observation_triggered": True,
            "mode": "PERIODIC_MONTHLY",
            "queued": queued,
            "message": "Monthly observation jobs enqueued for active policies",
        }

    if not policy_id:
        raise ValueError("Observation schedule requires policy_id in config")

    return {
        "observation_triggered": True,
        "policy_id": policy_id,
        "message": "Observation analysis scheduled for execution",
    }


def get_due_schedules() -> List[Dict[str, Any]]:
    """
    Get all schedules that are due for execution.

    Database schedules are the source of truth (lean staging and production).
    Legacy JSON files under STORAGE_PATH/schedules are included only when a
    schedule id is not already returned from the database.
    """
    from uepi_api.database import SessionLocal
    from uepi_api.models.schedule import Schedule

    due_schedules: List[Dict[str, Any]] = []
    seen: set[str] = set()
    now = datetime.utcnow()
    grace = now + timedelta(minutes=1)

    db = SessionLocal()
    try:
        rows = (
            db.query(Schedule)
            .filter(Schedule.enabled.is_(True))
            .filter(Schedule.next_run_at.isnot(None))
            .filter(Schedule.next_run_at <= grace)
            .all()
        )
        for row in rows:
            item = _schedule_row_to_dict(row)
            seen.add(item["id"])
            due_schedules.append(item)
    except Exception as e:
        print(f"Error loading due schedules from database: {e}")
    finally:
        db.close()

    STORAGE_PATH = os.getenv("STORAGE_PATH", "./data")
    schedules_base = Path(STORAGE_PATH) / "schedules"
    if not schedules_base.exists():
        return due_schedules

    for tenant_dir in schedules_base.iterdir():
        if not tenant_dir.is_dir():
            continue
        for schedule_file in tenant_dir.glob("*.json"):
            try:
                with open(schedule_file, "r") as f:
                    schedule = json.load(f)
                if not schedule.get("enabled", True):
                    continue
                sid = str(schedule.get("id") or "")
                if sid and sid in seen:
                    continue
                next_run_str = schedule.get("next_run")
                if not next_run_str:
                    continue
                next_run = datetime.fromisoformat(next_run_str.replace("Z", "+00:00"))
                if next_run <= grace:
                    due_schedules.append(schedule)
            except Exception as e:
                print(f"Error loading schedule {schedule_file}: {e}")
                continue

    return due_schedules


def _schedule_row_to_dict(row: Any) -> Dict[str, Any]:
    """Map a Schedule ORM row into the dict shape execute_schedule expects."""
    from uepi_api.storage_schedules import _parse_frequency_from_cron, _parse_time_from_cron

    frequency = _parse_frequency_from_cron(row.cron_expression)
    time_str = _parse_time_from_cron(row.cron_expression) or "09:00"
    day_of_week = None
    day_of_month = None
    if row.cron_expression:
        parts = row.cron_expression.split()
        if len(parts) >= 5:
            if parts[4] != "*":
                day_of_week = int(parts[4]) if parts[4].isdigit() else None
            elif parts[2] != "*":
                day_of_month = int(parts[2]) if parts[2].isdigit() else None
    return {
        "id": str(row.id),
        "tenant_id": str(row.tenant_id),
        "name": row.name,
        "schedule_type": row.target_type or "EXPORT",
        "frequency": frequency,
        "time": time_str,
        "day_of_week": day_of_week,
        "day_of_month": day_of_month,
        "config": {
            "target_type": row.target_type,
            "target_id": row.target_id,
            "mode": (row.description or "") if (row.description or "").startswith("PERIODIC_") else (
                "PERIODIC_MONTHLY" if (row.target_type or "") == "OBSERVATION" and not row.target_id else None
            ),
        },
        "enabled": row.enabled,
        "last_run": row.last_run_at.isoformat() if row.last_run_at else None,
        "next_run": row.next_run_at.isoformat() if row.next_run_at else None,
    }


def run_schedule_executor():
    """
    Main function to run the schedule executor
    This should be called periodically (e.g., every minute) by a background task
    """
    due_schedules = get_due_schedules()
    
    results = []
    for schedule in due_schedules:
        try:
            result = execute_schedule(schedule)
            results.append(result)
        except Exception as e:
            print(f"Failed to execute schedule {schedule.get('id')}: {e}")
            results.append({
                "success": False,
                "schedule_id": schedule.get("id"),
                "error": str(e),
            })
    
    return results
