"""API routers"""
# Core routers (always available)
from . import (
    analyses,
    auth,
    decisions,
    exports,
    lineage,
    notifications,
    policies,
    policy_import,
    scorecards,
    admin,
    access,
    data_health,
)

# Optional routers (may have dependencies like boto3)
try:
    from . import datasets
except (ImportError, PermissionError, OSError):
    datasets = None  # Use datasets_file instead

# Optional routers (may have dependencies)
try:
    from . import cohorts
except (ImportError, PermissionError, OSError):
    cohorts = None

# Optional imports (may fail if dependencies not available)
# ingestions router requires boto3 which may have permission issues
# We use ingestions_file instead for file storage
ingestions = None
try:
    from . import ingestions
except (ImportError, PermissionError, OSError):
    pass  # ingestions router not available - use ingestions_file instead

# Optional routers (may have dependencies like polars)
pipeline_monitoring = None
try:
    from . import pipeline_monitoring
except (ImportError, PermissionError, OSError):
    pass  # pipeline_monitoring router not available

# File-based routers (only when USE_FILE_STORAGE is enabled)
try:
    from . import policies_file
except ImportError:
    policies_file = None

__all__ = [
    "analyses",
    "auth",
    "cohorts",
    "decisions",
    "exports",
    "ingestions",
    "lineage",
    "notifications",
    "policies",
    "policies_file",
    "policy_import",
    "scorecards",
    "admin",
    "access",
    "datasets",
    "data_health",
]
