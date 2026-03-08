"""Data ingestion pipeline"""
from datetime import datetime
from typing import Any
from uuid import UUID
import json

import boto3
import polars as pl
from sqlalchemy.orm import Session

from uepi_worker.config import get_settings
from uepi_common.validators import validate_claims_batch, ClaimsLine

settings = get_settings()


def get_s3_client():
    """Get S3-compatible client"""
    return boto3.client(
        "s3",
        endpoint_url=settings.object_storage.endpoint,
        aws_access_key_id=settings.object_storage.access_key,
        aws_secret_access_key=settings.object_storage.secret_key,
        region_name=settings.object_storage.region,
        use_ssl=settings.object_storage.use_ssl,
    )


def read_manifest(manifest_uri: str) -> dict[str, Any]:
    """Read ingestion manifest from object storage"""
    s3_client = get_s3_client()
    
    # Parse S3 URI: s3://bucket/path or http://endpoint/bucket/path
    if manifest_uri.startswith("s3://"):
        parts = manifest_uri.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
    else:
        # Assume it's a full URL
        raise ValueError("Only s3:// URIs supported for now")
    
    response = s3_client.get_object(Bucket=bucket, Key=key)
    manifest = json.loads(response["Body"].read().decode("utf-8"))
    return manifest


def read_claims_file(file_uri: str) -> list[dict[str, Any]]:
    """Read claims file (CSV or Parquet) from object storage"""
    s3_client = get_s3_client()
    
    # Parse S3 URI
    if file_uri.startswith("s3://"):
        parts = file_uri.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
    else:
        raise ValueError("Only s3:// URIs supported for now")
    
    # Download to temp location
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".parquet" if file_uri.endswith(".parquet") else ".csv") as tmp:
        s3_client.download_fileobj(bucket, key, tmp)
        tmp_path = tmp.name
    
    try:
        # Read based on file extension
        if file_uri.endswith(".parquet"):
            df = pl.read_parquet(tmp_path)
        else:
            df = pl.read_csv(tmp_path)
        
        # Convert to list of dicts
        return df.to_dicts()
    finally:
        os.unlink(tmp_path)


def partition_claims_by_date_lob_market(
    claims: list[ClaimsLine],
    tenant_id: UUID,
) -> dict[str, list[ClaimsLine]]:
    """Partition claims by year/month/lob/market"""
    partitions: dict[str, list[ClaimsLine]] = {}
    
    for claim in claims:
        # Parse service_from_date
        service_date = datetime.strptime(claim.service_from_date, "%Y-%m-%d")
        year = service_date.year
        month = service_date.month
        
        # Create partition key
        partition_key = f"year={year}/month={month:02d}/lob={claim.lob}/market={claim.market}"
        
        if partition_key not in partitions:
            partitions[partition_key] = []
        
        partitions[partition_key].append(claim)
    
    return partitions


def write_partitioned_parquet(
    partitions: dict[str, list[ClaimsLine]],
    tenant_id: UUID,
    bucket: str,
) -> dict[str, str]:
    """Write partitioned Parquet files to object storage"""
    s3_client = get_s3_client()
    written_paths = {}
    
    for partition_key, claims in partitions.items():
        # Convert to Polars DataFrame
        claims_dicts = [claim.model_dump() for claim in claims]
        df = pl.DataFrame(claims_dicts)
        
        # Write to temp Parquet file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".parquet") as tmp:
            df.write_parquet(tmp.name)
            tmp_path = tmp.name
        
        try:
            # Upload to S3
            s3_key = f"{tenant_id}/curated/claims/{partition_key}/data.parquet"
            s3_client.upload_file(tmp_path, bucket, s3_key)
            
            written_paths[partition_key] = f"s3://{bucket}/{s3_key}"
        finally:
            os.unlink(tmp_path)
    
    return written_paths


def ingest_claims(
    tenant_id: UUID,
    manifest_uri: str,
    db: Session,
) -> tuple[dict[str, Any], list[dict]]:
    """Main ingestion function"""
    # Read manifest
    manifest = read_manifest(manifest_uri)
    
    all_valid_claims = []
    all_errors = []
    
    # Process each file in manifest
    for file_entry in manifest.get("files", []):
        file_uri = file_entry["uri"]
        file_type = file_entry.get("type", "claims_lines")
        
        if file_type != "claims_lines":
            continue
        
        # Read file
        try:
            raw_rows = read_claims_file(file_uri)
        except Exception as e:
            all_errors.append({
                "file_uri": file_uri,
                "error": f"Failed to read file: {str(e)}",
            })
            continue
        
        # Validate
        valid_claims, errors = validate_claims_batch(raw_rows)
        all_valid_claims.extend(valid_claims)
        all_errors.extend(errors)
    
    # Partition and write Parquet
    partitions = partition_claims_by_date_lob_market(all_valid_claims, tenant_id)
    bucket = settings.object_storage.bucket
    written_paths = write_partitioned_parquet(partitions, tenant_id, bucket)
    
    # Create dataset records in database
    from uepi_api.models.ingestion import Dataset
    
    dataset_records = []
    for partition_key, s3_uri in written_paths.items():
        # Parse partition key: year=YYYY/month=MM/lob=LOB/market=MARKET
        parts = partition_key.split("/")
        year = int(parts[0].split("=")[1])
        month = int(parts[1].split("=")[1])
        lob = parts[2].split("=")[1]
        market = parts[3].split("=")[1]
        
        dataset = Dataset(
            tenant_id=tenant_id,
            dataset_type="CLAIMS",
            year=year,
            month=month,
            lob=lob,
            market=market,
            record_count=len(partitions[partition_key]),
            data_uri=s3_uri,
        )
        dataset_records.append(dataset)
        db.add(dataset)
    
    db.commit()
    
    return {
        "total_claims": len(all_valid_claims),
        "total_errors": len(all_errors),
        "partitions_created": len(written_paths),
        "dataset_records": [d.id for d in dataset_records],
    }, all_errors

