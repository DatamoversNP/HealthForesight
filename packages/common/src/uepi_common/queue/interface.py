"""Queue abstraction interface - cloud-portable job queue"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import UUID


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    DEAD_LETTER = "DEAD_LETTER"  # Moved to DLQ after max retries
    CANCELLED = "CANCELLED"


@dataclass
class Job:
    """Job representation"""
    job_id: UUID | str
    job_type: str
    tenant_id: UUID
    payload: dict[str, Any]
    status: JobStatus
    priority: int = 5  # 1 (highest) to 10 (lowest), default 5
    max_retries: int = 3
    retry_count: int = 0
    retry_backoff_seconds: int = 60  # Exponential backoff base
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    result: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None  # Additional job metadata


class QueueError(Exception):
    """Base exception for queue operations"""
    pass


class JobNotFoundError(QueueError):
    """Raised when a job is not found"""
    pass


class QueueClient(ABC):
    """Abstract interface for job queue operations
    
    This interface ensures cloud portability - implementations can use:
    - Redis (MVP - simple, reliable)
    - Azure Service Bus (prod - enterprise features)
    - AWS SQS (prod - if on AWS)
    - RabbitMQ (on-prem)
    
    All implementations must follow this interface exactly.
    """
    
    @abstractmethod
    def enqueue_job(
        self,
        job_type: str,
        tenant_id: UUID,
        payload: dict[str, Any],
        priority: int = 5,
        max_retries: int = 3,
        retry_backoff_seconds: int = 60,
        delay_seconds: int = 0,
        metadata: Optional[dict[str, Any]] = None,
    ) -> UUID:
        """Enqueue a new job
        
        Args:
            job_type: Job type identifier (e.g., 'ingestion', 'impact_analysis')
            tenant_id: Tenant ID for multi-tenancy
            payload: Job payload (must be JSON-serializable)
            priority: Job priority 1-10 (1=highest, 10=lowest, default=5)
            max_retries: Maximum retry attempts (default=3)
            retry_backoff_seconds: Base seconds for exponential backoff (default=60)
            delay_seconds: Delay before job becomes available (default=0)
            metadata: Optional metadata dict
            
        Returns:
            Job ID (UUID)
            
        Raises:
            QueueError: If enqueue fails
        """
        pass
    
    @abstractmethod
    def get_job(
        self,
        job_id: UUID | str,
        tenant_id: UUID,
    ) -> Job:
        """Get job by ID
        
        Args:
            job_id: Job ID
            tenant_id: Tenant ID (for security/isolation)
            
        Returns:
            Job object
            
        Raises:
            JobNotFoundError: If job doesn't exist
            QueueError: If retrieval fails
        """
        pass
    
    @abstractmethod
    def update_job_status(
        self,
        job_id: UUID | str,
        tenant_id: UUID,
        status: JobStatus,
        error_message: Optional[str] = None,
        result: Optional[dict[str, Any]] = None,
    ) -> None:
        """Update job status
        
        Args:
            job_id: Job ID
            tenant_id: Tenant ID
            status: New status
            error_message: Error message (if status is FAILED)
            result: Job result (if status is COMPLETED)
            
        Raises:
            JobNotFoundError: If job doesn't exist
            QueueError: If update fails
        """
        pass
    
    @abstractmethod
    def dequeue_job(
        self,
        queue_name: Optional[str] = None,
        timeout_seconds: int = 5,
    ) -> Optional[Job]:
        """Dequeue next available job (worker operation)
        
        Args:
            queue_name: Optional queue name (default queue if None)
            timeout_seconds: How long to wait for a job (default=5)
            
        Returns:
            Job object or None if no job available
            
        Raises:
            QueueError: If dequeue fails
        """
        pass
    
    @abstractmethod
    def list_jobs(
        self,
        tenant_id: UUID,
        job_type: Optional[str] = None,
        status: Optional[JobStatus] = None,
        limit: int = 100,
    ) -> list[Job]:
        """List jobs for tenant with optional filters
        
        Args:
            tenant_id: Tenant ID
            job_type: Optional job type filter
            status: Optional status filter
            limit: Maximum number of jobs to return
            
        Returns:
            List of Job objects
            
        Raises:
            QueueError: If listing fails
        """
        pass
    
    @abstractmethod
    def cancel_job(
        self,
        job_id: UUID | str,
        tenant_id: UUID,
    ) -> None:
        """Cancel a pending/running job
        
        Args:
            job_id: Job ID
            tenant_id: Tenant ID
            
        Raises:
            JobNotFoundError: If job doesn't exist or already completed
            QueueError: If cancellation fails
        """
        pass
    
    @abstractmethod
    def retry_job(
        self,
        job_id: UUID | str,
        tenant_id: UUID,
    ) -> None:
        """Manually retry a failed job (before max retries)
        
        Args:
            job_id: Job ID
            tenant_id: Tenant ID
            
        Raises:
            JobNotFoundError: If job doesn't exist
            QueueError: If retry fails
        """
        pass
    
    @abstractmethod
    def move_to_dlq(
        self,
        job_id: UUID | str,
        tenant_id: UUID,
        reason: str,
    ) -> None:
        """Move a failed job to Dead Letter Queue
        
        Args:
            job_id: Job ID
            tenant_id: Tenant ID
            reason: Reason for DLQ move
            
        Raises:
            JobNotFoundError: If job doesn't exist
            QueueError: If move fails
        """
        pass
    
    @abstractmethod
    def get_dlq_jobs(
        self,
        tenant_id: UUID,
        limit: int = 100,
    ) -> list[Job]:
        """Get jobs from Dead Letter Queue
        
        Args:
            tenant_id: Tenant ID
            limit: Maximum number of jobs to return
            
        Returns:
            List of Job objects in DLQ
            
        Raises:
            QueueError: If retrieval fails
        """
        pass

