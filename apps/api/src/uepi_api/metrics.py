"""
Prometheus metrics for HealthForesight API
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import REGISTRY

# HTTP Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Database Metrics
db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0]
)

# Business Metrics
policies_total = Gauge(
    'policies_total',
    'Total number of policies',
    ['status']
)

analyses_total = Gauge(
    'analyses_total',
    'Total number of analyses',
    ['status']
)

ingestions_total = Gauge(
    'ingestions_total',
    'Total number of ingestions',
    ['status']
)

# Cache Metrics
cache_requests_total = Counter(
    'cache_requests_total',
    'Total number of cache requests',
    ['cache_name', 'operation', 'hit']
)

# Background Job Metrics
worker_jobs_total = Counter(
    'worker_jobs_total',
    'Total number of worker jobs',
    ['job_type', 'status']
)

worker_job_duration_seconds = Histogram(
    'worker_job_duration_seconds',
    'Worker job duration in seconds',
    ['job_type'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1800.0, 3600.0]
)

