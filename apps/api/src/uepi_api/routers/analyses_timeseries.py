"""Item 6: Time Series Data Loading from object storage"""
from typing import Dict, Any, List
from uuid import UUID
from pathlib import Path
import json

from uepi_api.storage_analyses import get_result_index, list_result_indices


def load_timeseries_from_storage(
    tenant_id: UUID,
    analysis_id: UUID,
) -> List[Dict[str, Any]]:
    """Load time series data from analysis results
    
    Args:
        tenant_id: Tenant ID
        analysis_id: Analysis ID
        
    Returns:
        List of time series data points
    """
    try:
        # Look for time series result index
        result_indices = list_result_indices(analysis_id, tenant_id, result_type="TIMESERIES")
        
        if not result_indices:
            # Try alternative result types
            result_indices = list_result_indices(analysis_id, tenant_id, result_type="timeseries")
        
        if not result_indices:
            return []
        
        timeseries_data = []
        
        for result_index in result_indices:
            data_uri = result_index.get("data_uri", "")
            
            if data_uri.startswith("file://"):
                # Load from local file
                file_path = Path(data_uri.replace("file://", ""))
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            timeseries_data.extend(data)
                        elif isinstance(data, dict) and "data" in data:
                            timeseries_data.extend(data["data"])
                        elif isinstance(data, dict) and "timeseries" in data:
                            timeseries_data.extend(data["timeseries"])
            elif data_uri.startswith("s3://"):
                # Load from S3 (if available)
                try:
                    import boto3
                    from uepi_api.config import get_settings
                    settings = get_settings()
                    
                    s3_client = boto3.client(
                        "s3",
                        endpoint_url=settings.object_storage.endpoint,
                        aws_access_key_id=settings.object_storage.access_key,
                        aws_secret_access_key=settings.object_storage.secret_key,
                    )
                    
                    # Parse S3 URI
                    uri_parts = data_uri.replace("s3://", "").split("/", 1)
                    bucket = uri_parts[0]
                    key = uri_parts[1] if len(uri_parts) > 1 else ""
                    
                    # Download and parse
                    response = s3_client.get_object(Bucket=bucket, Key=key)
                    data = json.loads(response['Body'].read())
                    if isinstance(data, list):
                        timeseries_data.extend(data)
                    elif isinstance(data, dict) and "data" in data:
                        timeseries_data.extend(data["data"])
                except Exception as e:
                    print(f"Warning: Could not load timeseries from S3: {e}")
        
        return timeseries_data
    
    except Exception as e:
        print(f"Error loading timeseries data: {e}")
        import traceback
        traceback.print_exc()
        return []
