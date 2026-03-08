"""File-based storage for API (minimal viable version)"""
import os
import platform
from pathlib import Path
from typing import Optional, Dict, Any, List
from uuid import UUID

from uepi_common.storage import FileStorage
from uepi_api.config import get_settings

settings = get_settings()

# Base storage path
# IMPORTANT: API server runs from apps/api/src, so we need absolute path to project root
# This file is at: apps/api/src/uepi_api/storage_file.py
# Project root is 4 levels up: apps/api/src/uepi_api -> apps/api/src -> apps/api -> apps -> root
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent

def get_storage_path():
    """Get storage path, preferring env var, then checking writability"""
    if "STORAGE_PATH" in os.environ:
        storage_path = os.environ["STORAGE_PATH"]
        # If relative path, make it absolute relative to project root
        if not os.path.isabs(storage_path):
            storage_path = str(_PROJECT_ROOT / storage_path)
        return storage_path
    
    # Check if we're on Azure App Service (runs from /home/site/wwwroot)
    # On Azure, the deployment root is /home/site/wwwroot
    # File is at: /home/site/wwwroot/src/uepi_api/storage_file.py
    # Going up 3 levels: /home/site/wwwroot/src/uepi_api -> /home/site/wwwroot/src -> /home/site/wwwroot
    if os.path.exists("/home/site/wwwroot"):
        # We're on Azure - use /home/site/wwwroot/data
        return "/home/site/wwwroot/data"
    
    # Check if we're on macOS (Darwin) or if /home is not writable
    if platform.system() == "Darwin" or (os.path.exists("/home") and not os.access("/home", os.W_OK)):
        # Use absolute path to project root / data
        return str(_PROJECT_ROOT / "data")
    # For Linux/Docker, try /home/data if /home exists and is writable
    if os.path.exists("/home") and os.access("/home", os.W_OK):
        return "/home/data"
    # Default to project root / data (absolute path)
    return str(_PROJECT_ROOT / "data")

STORAGE_PATH = get_storage_path()
BASE_PATH = Path(STORAGE_PATH)

# Storage instances
policy_storage = FileStorage(
    base_path=str(BASE_PATH / "policies"),
    file_prefix="policy-"
)

user_storage = FileStorage(
    base_path=str(BASE_PATH / "users"),
    file_prefix="user-"
)

tenant_storage = FileStorage(
    base_path=str(BASE_PATH / "tenants"),
    file_prefix="tenant-"
)

analysis_storage = FileStorage(
    base_path=str(BASE_PATH / "analyses"),
    file_prefix="analysis-"
)

analysis_result_index_storage = FileStorage(
    base_path=str(BASE_PATH / "analysis_result_indices"),
    file_prefix="result-index-"
)

def init_storage():
    """Initialize storage directories"""
    BASE_PATH.mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "policies").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "users").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "tenants").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "exports").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "ingestions").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "pipelines").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "pipeline_runs").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "analyses").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "analysis_result_indices").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "decisions").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "audit_trail").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "evidence").mkdir(parents=True, exist_ok=True)
    # Epic 4: Uncertainty & Risk Visualization
    (BASE_PATH / "forecasts").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "scenarios").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "risks").mkdir(parents=True, exist_ok=True)
    # Epic 5: Behavioral Signal Detection
    (BASE_PATH / "behavior_profiles").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "behavior_clusters").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "alert_rules").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "alert_events").mkdir(parents=True, exist_ok=True)
    # Epic 6: Collaboration Workflows
    (BASE_PATH / "comments").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "tasks").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "approvals").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "activity").mkdir(parents=True, exist_ok=True)
    # Epic 7: Executive Narrative Layer
    (BASE_PATH / "narratives").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "export_templates").mkdir(parents=True, exist_ok=True)
    (BASE_PATH / "export_packs").mkdir(parents=True, exist_ok=True)

