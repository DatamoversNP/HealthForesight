#!/usr/bin/env python3
"""
List all existing pipelines in the database
"""
import sys
from pathlib import Path
from uuid import UUID

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from uepi_api.storage_pipelines import list_pipelines

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

def list_all_pipelines():
    """List all existing pipelines"""
    print("=" * 80)
    print("EXISTING PIPELINES IN DATABASE")
    print("=" * 80)
    print(f"Tenant ID: {DEFAULT_TENANT_ID}")
    print()
    
    pipelines = list_pipelines(DEFAULT_TENANT_ID)
    
    if not pipelines:
        print("No pipelines found in database.")
        return
    
    print(f"📊 Found {len(pipelines)} pipelines:\n")
    
    for i, pipeline in enumerate(pipelines, 1):
        name = pipeline.get("pipeline_name") or pipeline.get("name") or "Unknown"
        pipeline_id = pipeline.get("pipeline_id") or "N/A"
        target_model = pipeline.get("target_model") or "N/A"
        status = pipeline.get("status") or "N/A"
        
        print(f"{i:2d}. {name}")
        print(f"     ID: {pipeline_id}")
        print(f"     Target: {target_model}")
        print(f"     Status: {status}")
        print()
    
    print("=" * 80)
    print(f"Total: {len(pipelines)} pipelines")

if __name__ == "__main__":
    list_all_pipelines()

