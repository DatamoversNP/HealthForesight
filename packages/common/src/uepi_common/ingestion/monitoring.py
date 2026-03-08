"""
Monitoring & Observability for Ingestion Pipelines
Provides real-time status, metrics, error tracking, and alerts
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field
import time


class PipelineStatus(str, Enum):
    """Pipeline execution status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PAUSED = "PAUSED"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class PerformanceMetrics(BaseModel):
    """Performance metrics for pipeline execution"""
    pipeline_id: UUID
    run_id: UUID
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    records_processed: int = 0
    records_per_second: Optional[float] = None
    throughput_mb_per_second: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    error_count: int = 0
    warning_count: int = 0


class PipelineAlert(BaseModel):
    """Alert for pipeline issues"""
    alert_id: UUID
    pipeline_id: UUID
    run_id: Optional[UUID] = None
    severity: AlertSeverity
    alert_type: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class PipelineHealth(BaseModel):
    """Pipeline health status"""
    pipeline_id: UUID
    pipeline_name: str
    status: PipelineStatus
    last_run_id: Optional[UUID] = None
    last_run_time: Optional[datetime] = None
    last_successful_run: Optional[datetime] = None
    consecutive_failures: int = 0
    success_rate: float = Field(ge=0.0, le=1.0, description="Success rate (0-1)")
    average_duration_seconds: Optional[float] = None
    data_freshness_hours: Optional[float] = None
    active_alerts: int = 0
    health_score: float = Field(ge=0.0, le=1.0, description="Overall health score (0-1)")


class MonitoringService:
    """Service for monitoring pipeline execution and health"""
    
    def __init__(self):
        """Initialize monitoring service"""
        self.metrics_history: Dict[UUID, List[PerformanceMetrics]] = {}
        self.alerts: List[PipelineAlert] = []
        self.health_status: Dict[UUID, PipelineHealth] = {}
    
    def record_metrics(
        self,
        pipeline_id: UUID,
        run_id: UUID,
        start_time: datetime,
        records_processed: int,
        error_count: int = 0,
        warning_count: int = 0,
        end_time: Optional[datetime] = None,
        data_size_mb: Optional[float] = None,
    ) -> PerformanceMetrics:
        """
        Record performance metrics for a pipeline run
        
        Args:
            pipeline_id: Pipeline identifier
            run_id: Run identifier
            start_time: Start time
            records_processed: Number of records processed
            error_count: Number of errors
            warning_count: Number of warnings
            end_time: End time (if completed)
            data_size_mb: Data size in MB
            
        Returns:
            PerformanceMetrics object
        """
        if end_time:
            duration = (end_time - start_time).total_seconds()
            records_per_second = records_processed / duration if duration > 0 else 0
            throughput = data_size_mb / duration if data_size_mb and duration > 0 else None
        else:
            duration = None
            records_per_second = None
            throughput = None
        
        metrics = PerformanceMetrics(
            pipeline_id=pipeline_id,
            run_id=run_id,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            records_processed=records_processed,
            records_per_second=records_per_second,
            throughput_mb_per_second=throughput,
            error_count=error_count,
            warning_count=warning_count,
        )
        
        # Store in history
        if pipeline_id not in self.metrics_history:
            self.metrics_history[pipeline_id] = []
        self.metrics_history[pipeline_id].append(metrics)
        
        # Keep only last 100 runs
        if len(self.metrics_history[pipeline_id]) > 100:
            self.metrics_history[pipeline_id] = self.metrics_history[pipeline_id][-100:]
        
        return metrics
    
    def create_alert(
        self,
        pipeline_id: UUID,
        severity: AlertSeverity,
        alert_type: str,
        message: str,
        run_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> PipelineAlert:
        """
        Create an alert
        
        Args:
            pipeline_id: Pipeline identifier
            severity: Alert severity
            alert_type: Type of alert
            message: Alert message
            run_id: Associated run ID
            details: Additional details
            
        Returns:
            PipelineAlert object
        """
        from uuid import uuid4
        
        alert = PipelineAlert(
            alert_id=uuid4(),
            pipeline_id=pipeline_id,
            run_id=run_id,
            severity=severity,
            alert_type=alert_type,
            message=message,
            details=details or {},
        )
        
        self.alerts.append(alert)
        
        # Keep only last 1000 alerts
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
        
        return alert
    
    def get_pipeline_health(
        self,
        pipeline_id: UUID,
        pipeline_name: str,
        recent_runs: List[Dict[str, Any]],
    ) -> PipelineHealth:
        """
        Calculate pipeline health status
        
        Args:
            pipeline_id: Pipeline identifier
            pipeline_name: Pipeline name
            recent_runs: List of recent run records
            
        Returns:
            PipelineHealth object
        """
        if not recent_runs:
            return PipelineHealth(
                pipeline_id=pipeline_id,
                pipeline_name=pipeline_name,
                status=PipelineStatus.PENDING,
                success_rate=1.0,
                health_score=1.0,
            )
        
        # Calculate statistics
        completed_runs = [r for r in recent_runs if r.get("status") == "COMPLETED"]
        failed_runs = [r for r in recent_runs if r.get("status") == "FAILED"]
        total_runs = len(recent_runs)
        
        success_rate = len(completed_runs) / total_runs if total_runs > 0 else 1.0
        
        # Consecutive failures
        consecutive_failures = 0
        for run in reversed(recent_runs):
            if run.get("status") == "FAILED":
                consecutive_failures += 1
            else:
                break
        
        # Last run info
        last_run = recent_runs[0] if recent_runs else None
        last_run_id = UUID(last_run["run_id"]) if last_run and "run_id" in last_run else None
        last_run_time = (
            datetime.fromisoformat(last_run["started_at"])
            if last_run and "started_at" in last_run
            else None
        )
        
        # Last successful run
        last_successful = completed_runs[0] if completed_runs else None
        last_successful_run = (
            datetime.fromisoformat(last_successful["completed_at"])
            if last_successful and "completed_at" in last_successful
            else None
        )
        
        # Average duration
        durations = [
            (datetime.fromisoformat(r["completed_at"]) - datetime.fromisoformat(r["started_at"])).total_seconds()
            for r in completed_runs
            if "completed_at" in r and "started_at" in r
        ]
        average_duration = sum(durations) / len(durations) if durations else None
        
        # Data freshness
        data_freshness = None
        if last_successful_run:
            data_freshness = (datetime.utcnow() - last_successful_run).total_seconds() / 3600
        
        # Active alerts
        active_alerts = len([
            a for a in self.alerts
            if a.pipeline_id == pipeline_id and not a.resolved
        ])
        
        # Determine status
        if consecutive_failures >= 3:
            status = PipelineStatus.FAILED
        elif last_run and last_run.get("status") == "RUNNING":
            status = PipelineStatus.RUNNING
        elif last_run and last_run.get("status") == "COMPLETED":
            status = PipelineStatus.COMPLETED
        elif last_run and last_run.get("status") == "FAILED":
            status = PipelineStatus.FAILED
        else:
            status = PipelineStatus.PENDING
        
        # Calculate health score
        health_score = (
            success_rate * 0.4 +
            (1.0 - min(consecutive_failures / 5.0, 1.0)) * 0.3 +
            (1.0 - min(active_alerts / 10.0, 1.0)) * 0.2 +
            (1.0 - min((data_freshness or 0) / 168.0, 1.0)) * 0.1  # 1 week = 168 hours
        )
        
        health = PipelineHealth(
            pipeline_id=pipeline_id,
            pipeline_name=pipeline_name,
            status=status,
            last_run_id=last_run_id,
            last_run_time=last_run_time,
            last_successful_run=last_successful_run,
            consecutive_failures=consecutive_failures,
            success_rate=success_rate,
            average_duration_seconds=average_duration,
            data_freshness_hours=data_freshness,
            active_alerts=active_alerts,
            health_score=health_score,
        )
        
        self.health_status[pipeline_id] = health
        
        return health
    
    def get_recent_alerts(
        self,
        pipeline_id: Optional[UUID] = None,
        severity: Optional[AlertSeverity] = None,
        limit: int = 100,
    ) -> List[PipelineAlert]:
        """
        Get recent alerts
        
        Args:
            pipeline_id: Filter by pipeline ID
            severity: Filter by severity
            limit: Maximum number of alerts to return
            
        Returns:
            List of alerts
        """
        alerts = self.alerts
        
        if pipeline_id:
            alerts = [a for a in alerts if a.pipeline_id == pipeline_id]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        # Sort by created_at descending
        alerts.sort(key=lambda a: a.created_at, reverse=True)
        
        return alerts[:limit]
    
    def get_metrics_history(
        self,
        pipeline_id: UUID,
        limit: int = 50,
    ) -> List[PerformanceMetrics]:
        """
        Get metrics history for a pipeline
        
        Args:
            pipeline_id: Pipeline identifier
            limit: Maximum number of metrics to return
            
        Returns:
            List of performance metrics
        """
        metrics = self.metrics_history.get(pipeline_id, [])
        return metrics[-limit:]
    
    def acknowledge_alert(self, alert_id: UUID) -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_at = datetime.utcnow()
                return True
        return False
    
    def resolve_alert(self, alert_id: UUID) -> bool:
        """Resolve an alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                return True
        return False

