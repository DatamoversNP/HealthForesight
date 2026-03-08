"""Pipeline monitoring and data quality endpoints"""
from typing import Annotated, List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.storage_pipelines import get_pipeline
from uepi_api.storage_pipeline_runs import list_pipeline_runs
from uepi_common.ingestion.monitoring import MonitoringService, AlertSeverity

router = APIRouter()

# Global monitoring service (in production, use dependency injection)
_monitoring_service = MonitoringService()


@router.get("/pipelines/{pipeline_id}/health")
async def get_pipeline_health(
    pipeline_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get pipeline health status"""
    pipeline = get_pipeline(pipeline_id, current_user.tenant_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Get recent runs
    from uepi_api.storage_pipeline_runs import list_pipeline_runs
    recent_runs = list_pipeline_runs(current_user.tenant_id, pipeline_id)[:20]
    
    # Calculate health metrics
    completed_runs = [r for r in recent_runs if r.get("status") == "COMPLETED"]
    failed_runs = [r for r in recent_runs if r.get("status") == "FAILED"]
    
    last_run = recent_runs[0] if recent_runs else None
    last_successful = completed_runs[0] if completed_runs else None
    
    success_rate = len(completed_runs) / len(recent_runs) if recent_runs else 1.0
    avg_time = sum(r.get("metadata", {}).get("metrics", {}).get("execution_time_seconds", 0) for r in completed_runs) / len(completed_runs) if completed_runs else 0.0
    
    # Calculate health score
    health_score = 1.0
    if success_rate < 0.9:
        health_score -= 0.2
    if len(failed_runs) > 0:
        health_score -= 0.1 * min(len(failed_runs), 3) / 3
    
    health_score = max(0.0, min(1.0, health_score))
    
    status_message = "Healthy"
    if success_rate < 0.7:
        status_message = "Unhealthy"
    elif success_rate < 0.9:
        status_message = "Degraded"
    
    return {
        "pipeline_id": str(pipeline_id),
        "last_run_at": last_run.get("started_at") if last_run else None,
        "last_successful_run_at": last_successful.get("completed_at") if last_successful else None,
        "consecutive_failures": len([r for r in recent_runs[:5] if r.get("status") == "FAILED"]),
        "success_rate_24h": success_rate,
        "avg_execution_time_24h": avg_time,
        "data_freshness_hours": None,  # Could calculate from last run
        "overall_health_score": health_score,
        "status_message": status_message,
    }


@router.get("/pipelines/{pipeline_id}/alerts")
async def get_pipeline_alerts(
    pipeline_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get alerts for a pipeline"""
    pipeline = get_pipeline(pipeline_id, current_user.tenant_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    from uepi_api.storage_pipeline_runs import list_pipeline_runs
    runs = list_pipeline_runs(current_user.tenant_id, pipeline_id)[:limit]
    
    alerts = []
    for run in runs:
        if run.get("status") == "FAILED":
            alerts.append({
                "alert_id": str(run.get("run_id", "")),
                "pipeline_id": str(pipeline_id),
                "run_id": str(run.get("run_id", "")),
                "severity": "HIGH",
                "message": f"Pipeline run failed: {run.get('metadata', {}).get('error', 'Unknown error')}",
                "timestamp": run.get("started_at"),
                "is_resolved": False,
            })
        elif run.get("records_failed", 0) > run.get("records_processed", 1) * 0.1:
            alerts.append({
                "alert_id": str(run.get("run_id", "")) + "_quality",
                "pipeline_id": str(pipeline_id),
                "run_id": str(run.get("run_id", "")),
                "severity": "MEDIUM",
                "message": f"High failure rate: {run.get('records_failed')} failed records",
                "timestamp": run.get("started_at"),
                "is_resolved": False,
            })
    
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity]
    
    return alerts


@router.get("/pipelines/{pipeline_id}/metrics")
async def get_pipeline_metrics(
    pipeline_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    limit: int = Query(50, ge=1, le=100),
):
    """Get performance metrics history for a pipeline"""
    pipeline = get_pipeline(pipeline_id, current_user.tenant_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    from uepi_api.storage_pipeline_runs import list_pipeline_runs
    runs = list_pipeline_runs(current_user.tenant_id, pipeline_id)[:limit]
    
    metrics = []
    for run in runs:
        run_metrics = run.get("metadata", {}).get("metrics", {})
        if run_metrics:
            metrics.append({
                "pipeline_id": str(pipeline_id),
                "run_id": str(run.get("run_id", "")),
                "timestamp": run.get("started_at"),
                "records_processed": run.get("records_processed", 0),
                "records_succeeded": run.get("records_succeeded", 0),
                "records_failed": run.get("records_failed", 0),
                "records_duplicated": run.get("records_duplicated", 0),
                "execution_time_seconds": run_metrics.get("execution_time_seconds", 0),
                "throughput_records_per_second": run_metrics.get("throughput_records_per_second", 0),
            })
    
    return metrics


@router.get("/pipelines/{pipeline_id}/runs/{run_id}/quality")
async def get_run_quality_report(
    pipeline_id: UUID,
    run_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get data quality report for a specific run"""
    pipeline = get_pipeline(pipeline_id, current_user.tenant_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Get run details
    from uepi_api.storage_pipeline_runs import get_pipeline_run
    run = get_pipeline_run(run_id, current_user.tenant_id)
    if not run or UUID(run.get("pipeline_id", "")) != pipeline_id:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    
    # Quality report should be stored in run metadata
    quality_report = run.get("metadata", {}).get("quality_report")
    if not quality_report:
        raise HTTPException(status_code=404, detail="Quality report not found for this run")
    
    return quality_report


@router.post("/pipelines/{pipeline_id}/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    pipeline_id: UUID,
    alert_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Acknowledge an alert"""
    pipeline = get_pipeline(pipeline_id, current_user.tenant_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    success = _monitoring_service.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"acknowledged": True}


@router.post("/pipelines/{pipeline_id}/alerts/{alert_id}/resolve")
async def resolve_alert(
    pipeline_id: UUID,
    alert_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Resolve an alert"""
    pipeline = get_pipeline(pipeline_id, current_user.tenant_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    success = _monitoring_service.resolve_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"resolved": True}

