"""Tests for data plane - Parquet service + storage abstraction"""
import pytest
from uuid import uuid4
from datetime import date

import polars as pl

from uepi_common.data.parquet_service import ParquetDataService, DataZone
from uepi_common.data_contracts.claims import ClaimsLine, ServiceCategory, PlaceOfService
from uepi_common.storage.local import LocalBlobStorageClient


@pytest.fixture
def storage_client(tmp_path):
    """Create a local storage client for testing"""
    return LocalBlobStorageClient(
        endpoint_url=f"file://{tmp_path}",
        access_key_id="test",
        secret_access_key="test",
        use_ssl=False,
    )


@pytest.fixture
def parquet_service(storage_client):
    """Create ParquetDataService for testing"""
    return ParquetDataService(
        storage_client=storage_client,
        container="test-bucket",
    )


def test_write_partitioned_claims(parquet_service):
    """Test writing partitioned claims data"""
    tenant_id = uuid4()
    
    # Create sample claims data
    claims_data = [
        {
            "claim_id": "CLM-001",
            "claim_line_id": "CLM-001-1",
            "member_id": "MEM-001",
            "provider_id": "PRV-001",
            "service_date": date(2024, 1, 15),
            "paid_date": date(2024, 1, 25),
            "lob": "Commercial",
            "market": "CA",
            "cpt_code": "99213",
            "service_category": ServiceCategory.PRIMARY_CARE,
            "place_of_service": PlaceOfService.OFFICE,
            "units": 1.0,
            "allowed_amount": 150.00,
            "paid_amount": 120.00,
            "member_cost_share": 30.00,
            "in_network": True,
            "requires_prior_auth": False,
        },
        {
            "claim_id": "CLM-002",
            "claim_line_id": "CLM-002-1",
            "member_id": "MEM-002",
            "provider_id": "PRV-002",
            "service_date": date(2024, 1, 20),
            "paid_date": date(2024, 1, 30),
            "lob": "Commercial",
            "market": "CA",
            "cpt_code": "99214",
            "service_category": ServiceCategory.PRIMARY_CARE,
            "place_of_service": PlaceOfService.OFFICE,
            "units": 1.0,
            "allowed_amount": 200.00,
            "paid_amount": 160.00,
            "member_cost_share": 40.00,
            "in_network": True,
            "requires_prior_auth": False,
        },
    ]
    
    # Convert to DataFrame
    df = pl.DataFrame(claims_data)
    
    # Write to CURATED zone with partitioning
    blob_name = parquet_service.write_partitioned_dataframe(
        df=df,
        tenant_id=tenant_id,
        dataset_type="claims_lines",
        zone=DataZone.CURATED,
        partition_by=["year", "month", "lob", "market"],
        partition_values={
            "year": "2024",
            "month": "01",
            "lob": "Commercial",
            "market": "CA",
        },
    )
    
    # Verify blob was created
    assert blob_name is not None
    assert "2024" in blob_name
    assert "Commercial" in blob_name
    assert "CA" in blob_name
    
    # Verify blob exists
    exists = parquet_service.storage_client.blob_exists(
        container=parquet_service.container,
        blob_name=blob_name,
    )
    assert exists


def test_read_partitioned_claims(parquet_service):
    """Test reading partitioned claims data"""
    tenant_id = uuid4()
    
    # Create and write sample data
    claims_data = [
        {
            "claim_id": "CLM-001",
            "claim_line_id": "CLM-001-1",
            "member_id": "MEM-001",
            "provider_id": "PRV-001",
            "service_date": date(2024, 1, 15),
            "lob": "Commercial",
            "market": "CA",
            "cpt_code": "99213",
            "service_category": ServiceCategory.PRIMARY_CARE,
            "place_of_service": PlaceOfService.OFFICE,
            "units": 1.0,
            "allowed_amount": 150.00,
            "paid_amount": 120.00,
            "member_cost_share": 30.00,
            "in_network": True,
            "requires_prior_auth": False,
        },
    ]
    
    df = pl.DataFrame(claims_data)
    
    # Write
    parquet_service.write_partitioned_dataframe(
        df=df,
        tenant_id=tenant_id,
        dataset_type="claims_lines",
        zone=DataZone.CURATED,
        partition_by=["year", "month", "lob", "market"],
        partition_values={
            "year": "2024",
            "month": "01",
            "lob": "Commercial",
            "market": "CA",
        },
    )
    
    # Read back
    read_df = parquet_service.read_partitioned_dataframe(
        tenant_id=tenant_id,
        dataset_type="claims_lines",
        zone=DataZone.CURATED,
        partition_filters={
            "year": "2024",
            "month": "01",
        },
    )
    
    # Verify data
    assert len(read_df) == 1
    assert read_df["claim_id"][0] == "CLM-001"


def test_list_partitions(parquet_service):
    """Test listing available partitions"""
    tenant_id = uuid4()
    
    # Write data to multiple partitions
    for month in ["01", "02"]:
        df = pl.DataFrame([{
            "claim_id": f"CLM-{month}-001",
            "claim_line_id": f"CLM-{month}-001-1",
            "member_id": "MEM-001",
            "provider_id": "PRV-001",
            "service_date": date(2024, int(month), 15),
            "lob": "Commercial",
            "market": "CA",
            "cpt_code": "99213",
            "service_category": ServiceCategory.PRIMARY_CARE,
            "place_of_service": PlaceOfService.OFFICE,
            "units": 1.0,
            "allowed_amount": 150.00,
            "paid_amount": 120.00,
            "member_cost_share": 30.00,
            "in_network": True,
            "requires_prior_auth": False,
        }])
        
        parquet_service.write_partitioned_dataframe(
            df=df,
            tenant_id=tenant_id,
            dataset_type="claims_lines",
            zone=DataZone.CURATED,
            partition_by=["year", "month", "lob", "market"],
            partition_values={
                "year": "2024",
                "month": month,
                "lob": "Commercial",
                "market": "CA",
            },
        )
    
    # List partitions
    partitions = parquet_service.list_partitions(
        tenant_id=tenant_id,
        dataset_type="claims_lines",
        zone=DataZone.CURATED,
    )
    
    # Verify partitions
    assert len(partitions) == 2
    assert {"year": "2024", "month": "01", "lob": "Commercial", "market": "CA"} in partitions
    assert {"year": "2024", "month": "02", "lob": "Commercial", "market": "CA"} in partitions

