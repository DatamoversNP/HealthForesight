"""Redis queue implementation - for MVP and development"""
import json
import time
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID, uuid4

import redis
from redis.exceptions import RedisError

from uepi_common.queue.interface import (
    QueueClient,
    Job,
    JobStatus,
    QueueError,
    JobNotFoundError,
)


class RedisQueueClient(QueueClient):
    """Redis-based queue implementation using Redis Lists + Hashes
    
    Architecture:
    - Jobs stored in Redis Hash: job:{job_id} -> JSON payload
    - Pending jobs in Redis List: queue:{queue_name}:pending
    - DLQ jobs in Redis List: queue:{queue_name}:dlq
    - Sorted sets for priority: queue:{queue_name}:priority (score=priority, member=job_id)
    
    This implementation uses Redis for simplicity and reliability in MVP.
    For production scale, consider Azure Service Bus or AWS SQS, but Redis
    works well for moderate load (< 100k jobs/day).
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_queue: str = "default",
        dlq_suffix: str = "dlq",
    ):
        """Initialize Redis queue client
        
        Args:
            redis_url: Redis connection URL
            default_queue: Default queue name
            dlq_suffix: Suffix for DLQ queue name
        """
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=False)
            self.default_queue = default_queue
            self.dlq_suffix = dlq_suffix
        except Exception as e:
            raise QueueError(f"Failed to connect to Redis: {e}") from e
    
    def _job_key(self, job_id: UUID | str) -> str:
        """Get Redis key for job hash"""
        return f"job:{job_id}"
    
    def _queue_key(self, queue_name: str, suffix: str = "pending") -> str:
        """Get Redis key for queue list"""
        return f"queue:{queue_name}:{suffix}"
    
    def _priority_key(self, queue_name: str) -> str:
        """Get Redis key for priority sorted set"""
        return f"queue:{queue_name}:priority"
    
    def _serialize_job(self, job: Job) -> bytes:
        """Serialize job to JSON bytes"""
        job_dict = {
            "job_id": str(job.job_id),
            "job_type": job.job_type,
            "tenant_id": str(job.tenant_id),
            "payload": job.payload,
            "status": job.status.value,
            "priority": job.priority,
            "max_retries": job.max_retries,
            "retry_count": job.retry_count,
            "retry_backoff_seconds": job.retry_backoff_seconds,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
            "result": job.result,
            "metadata": job.metadata or {},
        }
        return json.dumps(job_dict).encode('utf-8')
    
    def _deserialize_job(self, data: bytes) -> Job:
        """Deserialize job from JSON bytes"""
        job_dict = json.loads(data.decode('utf-8'))
        return Job(
            job_id=UUID(job_dict["job_id"]) if isinstance(job_dict["job_id"], str) else job_dict["job_id"],
            job_type=job_dict["job_type"],
            tenant_id=UUID(job_dict["tenant_id"]),
            payload=job_dict["payload"],
            status=JobStatus(job_dict["status"]),
            priority=job_dict.get("priority", 5),
            max_retries=job_dict.get("max_retries", 3),
            retry_count=job_dict.get("retry_count", 0),
            retry_backoff_seconds=job_dict.get("retry_backoff_seconds", 60),
            created_at=datetime.fromisoformat(job_dict["created_at"]) if job_dict.get("created_at") else None,
            started_at=datetime.fromisoformat(job_dict["started_at"]) if job_dict.get("started_at") else None,
            completed_at=datetime.fromisoformat(job_dict["completed_at"]) if job_dict.get("completed_at") else None,
            error_message=job_dict.get("error_message"),
            result=job_dict.get("result"),
            metadata=job_dict.get("metadata"),
        )
    
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
        """Enqueue job to Redis"""
        try:
            job_id = uuid4()
            queue_name = self.default_queue
            
            job = Job(
                job_id=job_id,
                job_type=job_type,
                tenant_id=tenant_id,
                payload=payload,
                status=JobStatus.PENDING,
                priority=priority,
                max_retries=max_retries,
                retry_backoff_seconds=retry_backoff_seconds,
                created_at=datetime.utcnow(),
                metadata=metadata,
            )
            
            # Store job in hash
            job_key = self._job_key(job_id)
            self.redis_client.set(job_key, self._serialize_job(job))
            
            if delay_seconds > 0:
                # Delayed job - use sorted set with score = current_time + delay
                delay_key = f"queue:{queue_name}:delayed"
                available_at = time.time() + delay_seconds
                self.redis_client.zadd(delay_key, {str(job_id): available_at})
            else:
                # Immediate job - add to priority queue
                priority_key = self._priority_key(queue_name)
                self.redis_client.zadd(priority_key, {str(job_id): priority})
                
                # Also add to pending list (for dequeue)
                pending_key = self._queue_key(queue_name, "pending")
                self.redis_client.lpush(pending_key, str(job_id))
            
            return job_id
            
        except RedisError as e:
            raise QueueError(f"Failed to enqueue job: {e}") from e
        except Exception as e:
            raise QueueError(f"Unexpected error enqueueing job: {e}") from e
    
    def get_job(
        self,
        job_id: UUID | str,
        tenant_id: UUID,
    ) -> Job:
        """Get job from Redis"""
        try:
            job_key = self._job_key(job_id)
            data = self.redis_client.get(job_key)
            
            if not data:
                raise JobNotFoundError(f"Job {job_id} not found")
            
            job = self._deserialize_job(data)
            
            # Verify tenant_id matches (security check)
            if job.tenant_id != tenant_id:
                raise QueueError(f"Job {job_id} belongs to different tenant")
            
            return job
            
        except JobNotFoundError:
            raise
        except RedisError as e:
            raise QueueError(f"Failed to get job: {e}") from e
        except Exception as e:
            raise QueueError(f"Unexpected error getting job: {e}") from e
    
    def update_job_status(
        self,
        job_id: UUID | str,
        tenant_id: UUID,
        status: JobStatus,
        error_message: Optional[str] = None,
        result: Optional[dict[str, Any]] = None,
    ) -> None:
        """Update job status in Redis"""
        try:
            job = self.get_job(job_id, tenant_id)
            
            job.status = status
            if error_message:
                job.error_message = error_message
            if result:
                job.result = result
            
            if status == JobStatus.RUNNING and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.DEAD_LETTER]:
                job.completed_at = datetime.utcnow()
            
            # Update job in Redis
            job_key = self._job_key(job_id)
            self.redis_client.set(job_key, self._serialize_job(job))
            
            # Remove from pending queue if completed/failed
            if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.DEAD_LETTER]:
                queue_name = self.default_queue
                pending_key = self._queue_key(queue_name, "pending")
                priority_key = self._priority_key(queue_name)
                self.redis_client.lrem(pending_key, 0, str(job_id))
                self.redis_client.zrem(priority_key, str(job_id))
            
        except JobNotFoundError:
            raise
        except RedisError as e:
            raise QueueError(f"Failed to update job status: {e}") from e
        except Exception as e:
            raise QueueError(f"Unexpected error updating job status: {e}") from e
    
    def dequeue_job(
        self,
        queue_name: Optional[str] = None,
        timeout_seconds: int = 5,
    ) -> Optional[Job]:
        """Dequeue next job from Redis (blocking)"""
        try:
            queue_name = queue_name or self.default_queue
            pending_key = self._queue_key(queue_name, "pending")
            
            # Move delayed jobs that are now available to pending queue
            self._move_delayed_jobs(queue_name)
            
            # Blocking pop from pending queue
            result = self.redis_client.brpop(pending_key, timeout=timeout_seconds)
            
            if not result:
                return None
            
            _, job_id_str = result
            job_id = UUID(job_id_str.decode('utf-8') if isinstance(job_id_str, bytes) else job_id_str)
            
            # Get job details
            job_key = self._job_key(job_id)
            job_data = self.redis_client.get(job_key)
            
            if not job_data:
                # Job was deleted, skip
                return None
            
            job = self._deserialize_job(job_data)
            
            # Update status to RUNNING
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            self.redis_client.set(job_key, self._serialize_job(job))
            
            # Remove from priority queue
            priority_key = self._priority_key(queue_name)
            self.redis_client.zrem(priority_key, str(job_id))
            
            return job
            
        except RedisError as e:
            raise QueueError(f"Failed to dequeue job: {e}") from e
        except Exception as e:
            raise QueueError(f"Unexpected error dequeuing job: {e}") from e
    
    def _move_delayed_jobs(self, queue_name: str) -> None:
        """Move delayed jobs that are now available to pending queue"""
        try:
            delay_key = f"queue:{queue_name}:delayed"
            pending_key = self._queue_key(queue_name, "pending")
            priority_key = self._priority_key(queue_name)
            current_time = time.time()
            
            # Get jobs that are now available (score <= current_time)
            available_jobs = self.redis_client.zrangebyscore(
                delay_key,
                min=0,
                max=current_time,
                withscores=False,
            )
            
            for job_id_bytes in available_jobs:
                job_id_str = job_id_bytes.decode('utf-8') if isinstance(job_id_bytes, bytes) else job_id_bytes
                
                # Get job to get priority
                job_key = self._job_key(job_id_str)
                job_data = self.redis_client.get(job_key)
                
                if job_data:
                    job = self._deserialize_job(job_data)
                    # Add to priority queue and pending list
                    self.redis_client.zadd(priority_key, {job_id_str: job.priority})
                    self.redis_client.lpush(pending_key, job_id_str)
                
                # Remove from delayed queue
                self.redis_client.zrem(delay_key, job_id_str)
                
        except RedisError:
            # Ignore errors in delayed job processing
            pass
    
    def list_jobs(
        self,
        tenant_id: UUID,
        job_type: Optional[str] = None,
        status: Optional[JobStatus] = None,
        limit: int = 100,
    ) -> list[Job]:
        """List jobs for tenant"""
        try:
            # Scan for all job keys (this is inefficient for large scale, but works for MVP)
            # In production, maintain an index by tenant_id
            job_keys = []
            cursor = 0
            
            while True:
                cursor, keys = self.redis_client.scan(cursor, match="job:*", count=100)
                job_keys.extend(keys)
                if cursor == 0:
                    break
            
            jobs = []
            for job_key_bytes in job_keys[:limit * 2]:  # Fetch more to filter
                try:
                    job_data = self.redis_client.get(job_key_bytes)
                    if not job_data:
                        continue
                    
                    job = self._deserialize_job(job_data)
                    
                    # Filter by tenant_id
                    if job.tenant_id != tenant_id:
                        continue
                    
                    # Filter by job_type
                    if job_type and job.job_type != job_type:
                        continue
                    
                    # Filter by status
                    if status and job.status != status:
                        continue
                    
                    jobs.append(job)
                    
                    if len(jobs) >= limit:
                        break
                        
                except Exception:
                    # Skip invalid jobs
                    continue
            
            return jobs
            
        except RedisError as e:
            raise QueueError(f"Failed to list jobs: {e}") from e
        except Exception as e:
            raise QueueError(f"Unexpected error listing jobs: {e}") from e
    
    def cancel_job(
        self,
        job_id: UUID | str,
        tenant_id: UUID,
    ) -> None:
        """Cancel a job"""
        try:
            job = self.get_job(job_id, tenant_id)
            
            if job.status in [JobStatus.COMPLETED, JobStatus.DEAD_LETTER]:
                raise QueueError(f"Cannot cancel job {job_id} with status {job.status}")
            
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            
            job_key = self._job_key(job_id)
            self.redis_client.set(job_key, self._serialize_job(job))
            
            # Remove from queues
            queue_name = self.default_queue
            pending_key = self._queue_key(queue_name, "pending")
            priority_key = self._priority_key(queue_name)
            self.redis_client.lrem(pending_key, 0, str(job_id))
            self.redis_client.zrem(priority_key, str(job_id))
            
        except JobNotFoundError:
            raise
        except RedisError as e:
            raise QueueError(f"Failed to cancel job: {e}") from e
        except Exception as e:
            raise QueueError(f"Unexpected error cancelling job: {e}") from e
    
    def retry_job(
        self,
        job_id: UUID | str,
        tenant_id: UUID,
    ) -> None:
        """Retry a failed job"""
        try:
            job = self.get_job(job_id, tenant_id)
            
            if job.status != JobStatus.FAILED:
                raise QueueError(f"Can only retry failed jobs, job {job_id} has status {job.status}")
            
            if job.retry_count >= job.max_retries:
                raise QueueError(f"Job {job_id} has exceeded max retries ({job.max_retries})")
            
            # Reset job for retry
            job.retry_count += 1
            job.status = JobStatus.PENDING
            job.error_message = None
            job.started_at = None
            job.completed_at = None
            
            # Calculate backoff delay (exponential)
            delay = job.retry_backoff_seconds * (2 ** (job.retry_count - 1))
            
            # Re-enqueue with delay
            queue_name = self.default_queue
            job_key = self._job_key(job_id)
            self.redis_client.set(job_key, self._serialize_job(job))
            
            delay_key = f"queue:{queue_name}:delayed"
            available_at = time.time() + delay
            self.redis_client.zadd(delay_key, {str(job_id): available_at})
            
        except (JobNotFoundError, QueueError):
            raise
        except RedisError as e:
            raise QueueError(f"Failed to retry job: {e}") from e
        except Exception as e:
            raise QueueError(f"Unexpected error retrying job: {e}") from e
    
    def move_to_dlq(
        self,
        job_id: UUID | str,
        tenant_id: UUID,
        reason: str,
    ) -> None:
        """Move job to Dead Letter Queue"""
        try:
            job = self.get_job(job_id, tenant_id)
            
            job.status = JobStatus.DEAD_LETTER
            job.completed_at = datetime.utcnow()
            if job.error_message:
                job.error_message = f"{job.error_message}; DLQ Reason: {reason}"
            else:
                job.error_message = f"DLQ Reason: {reason}"
            
            # Update job
            job_key = self._job_key(job_id)
            self.redis_client.set(job_key, self._serialize_job(job))
            
            # Move to DLQ list
            queue_name = self.default_queue
            dlq_key = self._queue_key(queue_name, self.dlq_suffix)
            self.redis_client.lpush(dlq_key, str(job_id))
            
            # Remove from pending/priority queues
            pending_key = self._queue_key(queue_name, "pending")
            priority_key = self._priority_key(queue_name)
            self.redis_client.lrem(pending_key, 0, str(job_id))
            self.redis_client.zrem(priority_key, str(job_id))
            
        except JobNotFoundError:
            raise
        except RedisError as e:
            raise QueueError(f"Failed to move job to DLQ: {e}") from e
        except Exception as e:
            raise QueueError(f"Unexpected error moving job to DLQ: {e}") from e
    
    def get_dlq_jobs(
        self,
        tenant_id: UUID,
        limit: int = 100,
    ) -> list[Job]:
        """Get jobs from Dead Letter Queue"""
        try:
            queue_name = self.default_queue
            dlq_key = self._queue_key(queue_name, self.dlq_suffix)
            
            # Get job IDs from DLQ
            job_ids = self.redis_client.lrange(dlq_key, 0, limit - 1)
            
            jobs = []
            for job_id_bytes in job_ids:
                try:
                    job_id_str = job_id_bytes.decode('utf-8') if isinstance(job_id_bytes, bytes) else job_id_bytes
                    job = self.get_job(job_id_str, tenant_id)
                    if job.status == JobStatus.DEAD_LETTER:
                        jobs.append(job)
                except (JobNotFoundError, QueueError):
                    # Skip invalid jobs
                    continue
            
            return jobs
            
        except RedisError as e:
            raise QueueError(f"Failed to get DLQ jobs: {e}") from e
        except Exception as e:
            raise QueueError(f"Unexpected error getting DLQ jobs: {e}") from e

