"""Worker tasks"""
from uuid import UUID
from typing import Optional
import traceback
import json

from celery import Task
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import boto3

from uepi_worker.main import app
from uepi_worker.config import get_settings
from uepi_worker.whatif import simulate_scenario, ScenarioParameters
from uepi_common.ingestion.processor import IngestionProcessor
from uepi_common.data.parquet_service import ParquetDataService
from uepi_common.data_contracts.manifest import DatasetType, IngestionMode
from uepi_common.storage.factory import create_storage_client

settings = get_settings()

# Database session
engine = create_engine(settings.database.url)
SessionLocal = sessionmaker(bind=engine)


class BaseTask(Task):
    """Base task with error handling"""
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        # TODO: Log to database, send alerts, etc.
        print(f"Task {task_id} failed: {exc}")
        traceback.print_exc()


@app.task(base=BaseTask, bind=True, max_retries=3)
def ingest_job(self, tenant_id: str, manifest_uri: str, ingestion_id: str, dataset_type: str) -> dict:
    """Process ingestion job using IngestionProcessor (Phase 3)
    
    Args:
        tenant_id: Tenant ID
        manifest_uri: URI to ingestion manifest
        ingestion_id: Ingestion record ID
        dataset_type: Dataset type (CLAIMS_LINES, ENROLLMENT, PROVIDERS, BENEFIT_DESIGN)
        
    Returns:
        Dictionary with status, result, error_count
    """
    from datetime import datetime
    db = SessionLocal()
    try:
        from uepi_api.models.ingestion import Ingestion, IngestionError, IngestionStatus, Dataset, IngestionType
        
        # Update ingestion status
        ingestion = db.query(Ingestion).filter(Ingestion.id == UUID(ingestion_id)).first()
        if not ingestion:
            return {"status": "error", "message": "Ingestion not found"}
        
        ingestion.status = IngestionStatus.PROCESSING.value
        ingestion.started_at = datetime.utcnow()
        db.commit()
        
        # Map ingestion type to DatasetType
        dataset_type_enum_map = {
            IngestionType.CLAIMS.value: DatasetType.CLAIMS_LINES,
            IngestionType.ENROLLMENT.value: DatasetType.ENROLLMENT,
            IngestionType.PROVIDERS.value: DatasetType.PROVIDERS,
            IngestionType.BENEFIT_DESIGN.value: DatasetType.BENEFIT_DESIGN,
        }
        dataset_type_enum = dataset_type_enum_map.get(dataset_type, DatasetType.CLAIMS_LINES)
        
        # Create ingestion processor
        storage_client = create_storage_client(settings=settings.object_storage)
        parquet_service = ParquetDataService(
            storage_client=storage_client,
            container=settings.object_storage.bucket_name_or_bucket,
        )
        processor = IngestionProcessor(
            tenant_id=UUID(tenant_id),
            dataset_type=dataset_type_enum,
            parquet_service=parquet_service,
        )
        
        # Read manifest to get file URI and format
        import json
        import tempfile
        import os
        from urllib.parse import urlparse
        
        # Download manifest
        parsed_uri = urlparse(manifest_uri)
        if parsed_uri.scheme == "s3":
            # Extract blob path from S3 URI
            manifest_path = parsed_uri.path.lstrip("/")
            manifest_bytes = storage_client.download_blob(
                container=settings.object_storage.bucket_name_or_bucket,
                blob_name=manifest_path,
            )
            manifest = json.loads(manifest_bytes.decode('utf-8'))
        elif parsed_uri.scheme in ["http", "https"]:
            # HTTP/HTTPS URL - download via requests
            import requests
            response = requests.get(manifest_uri)
            manifest = response.json()
        elif parsed_uri.scheme == "file" or parsed_uri.path:
            # Local file path
            local_path = parsed_uri.path if parsed_uri.scheme == "file" else manifest_uri
            with open(local_path, "r") as f:
                manifest = json.load(f)
        else:
            raise ValueError(f"Unsupported manifest URI scheme: {parsed_uri.scheme}")
        
        # Process each file in manifest
        all_curated_partitions = []
        all_errors = []
        all_warnings = []
        
        for file_entry in manifest.get("source_files", manifest.get("files", [])):
            file_uri = file_entry.get("uri", "")
            file_format = file_entry.get("format", "parquet").lower()
            
            # Download file to temp location if needed
            parsed_file_uri = urlparse(file_uri)
            tmp_path = None
            
            try:
                if parsed_file_uri.scheme == "s3":
                    # Extract blob path from S3 URI
                    blob_path = parsed_file_uri.path.lstrip("/")
                    # Download to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_format}") as tmp:
                        file_bytes = storage_client.download_blob(
                            container=settings.object_storage.bucket_name_or_bucket,
                            blob_name=blob_path,
                        )
                        tmp.write(file_bytes)
                        tmp_path = tmp.name
                elif parsed_file_uri.scheme in ["http", "https"]:
                    # HTTP/HTTPS URL - download via requests
                    import requests
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_format}") as tmp:
                        response = requests.get(file_uri, stream=True)
                        response.raise_for_status()
                        for chunk in response.iter_content(chunk_size=8192):
                            tmp.write(chunk)
                        tmp_path = tmp.name
                elif parsed_file_uri.scheme == "file" or parsed_file_uri.path:
                    # Local file path
                    tmp_path = parsed_file_uri.path if parsed_file_uri.scheme == "file" else file_uri
                else:
                    raise ValueError(f"Unsupported file URI scheme: {parsed_file_uri.scheme}")
                
                # Process file
                result = processor.process_file(
                    file_path=tmp_path,
                    file_format=file_format,
                    ingestion_mode=IngestionMode.MANUAL_UPLOAD,
                    replace_existing=False,
                )
                
                if result["success"]:
                    all_curated_partitions.extend(result.get("curated_partitions", []))
                    all_warnings.extend(result.get("warnings", []))
                    
                    # Create dataset snapshot records for each partition
                    validation_result = result.get("validation_result", {})
                    record_count = validation_result.get("valid_count", 0)
                    
                    for partition_uri in result.get("curated_partitions", []):
                        # Extract partition info from URI
                        # Format: {tenant_id}/curated/{dataset_type}/year={year}/month={month}/lob={lob}/market={market}/data.parquet
                        parts = partition_uri.split("/")
                        partition_values = {}
                        for part in parts:
                            if "=" in part:
                                key, value = part.split("=", 1)
                                partition_values[key] = value
                        
                        # Create or update dataset snapshot
                        existing_dataset = db.query(Dataset).filter(
                            Dataset.tenant_id == UUID(tenant_id),
                            Dataset.dataset_type == dataset_type,
                            Dataset.year == int(partition_values.get("year", 0)),
                            Dataset.month == int(partition_values.get("month", 0)),
                            Dataset.lob == partition_values.get("lob"),
                            Dataset.market == partition_values.get("market"),
                        ).first()
                        
                        if existing_dataset:
                            # Update existing snapshot
                            existing_dataset.record_count = record_count
                            existing_dataset.data_uri = partition_uri
                            existing_dataset.updated_at = datetime.utcnow()
                        else:
                            # Create new snapshot
                            dataset = Dataset(
                                tenant_id=UUID(tenant_id),
                                dataset_type=dataset_type,
                                year=int(partition_values.get("year", 0)),
                                month=int(partition_values.get("month", 0)),
                                lob=partition_values.get("lob"),
                                market=partition_values.get("market"),
                                record_count=record_count,
                                data_uri=partition_uri,
                            )
                            db.add(dataset)
                else:
                    # Validation failed
                    validation_result = result.get("validation_result", {})
                    errors = validation_result.get("errors", [])
                    all_errors.extend(errors)
                    
                    # Save errors to database
                    for error in errors:
                        ingestion_error = IngestionError(
                            tenant_id=UUID(tenant_id),
                            ingestion_id=UUID(ingestion_id),
                            error_type="VALIDATION_ERROR",
                            error_message=str(error.get("message", error)),
                            row_number=error.get("row"),
                            file_path=file_uri,
                        )
                        db.add(ingestion_error)
                
            finally:
                # Clean up temp file only if we created it (not if it was a local path)
                if tmp_path and tmp_path != file_uri and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
        
        # Update ingestion status
        ingestion.status = IngestionStatus.COMPLETED.value if len(all_errors) == 0 else IngestionStatus.FAILED.value
        ingestion.completed_at = datetime.utcnow()
        ingestion.metadata_json = {
            "curated_partitions": all_curated_partitions,
            "record_count": sum(result.get("record_count", 0) for result in [result] if result.get("success")),
            "error_count": len(all_errors),
            "warning_count": len(all_warnings),
        }
        db.commit()
        
        return {
            "status": "completed",
            "ingestion_id": ingestion_id,
            "curated_partitions": all_curated_partitions,
            "error_count": len(all_errors),
            "warning_count": len(all_warnings),
        }
        
    except Exception as e:
        # Update ingestion status to failed
        if 'ingestion' in locals():
            ingestion.status = IngestionStatus.FAILED.value
            ingestion.completed_at = datetime.utcnow()
            db.commit()
            
            # Save error
            ingestion_error = IngestionError(
                tenant_id=UUID(tenant_id),
                ingestion_id=UUID(ingestion_id),
                error_type="PROCESSING_ERROR",
                error_message=str(e),
                file_path=manifest_uri,
            )
            db.add(ingestion_error)
            db.commit()
        
        raise
    finally:
        db.close()


@app.task(base=BaseTask, bind=True, max_retries=3)
def ingest_claims_job(self, tenant_id: str, manifest_uri: str, ingestion_id: str) -> dict:
    """Legacy ingest_claims_job - delegates to ingest_job for CLAIMS dataset type"""
    return ingest_job(self, tenant_id, manifest_uri, ingestion_id, "CLAIMS")


@app.task(base=BaseTask, bind=True, max_retries=3)
def policy_impact_job(
    self,
    tenant_id: str,
    policy_id: str,
    analysis_id: str,
    config: dict,
) -> dict:
    """Run policy impact analysis"""
    db = SessionLocal()
    try:
        from uepi_api.models.analysis import Analysis, AnalysisStatus, AnalysisResultIndex
        from uepi_api.models.policy import Policy, PolicyVersion
        from uepi_worker.impact_analysis import run_policy_impact_analysis
        from uepi_common.data_contracts.claims import ServiceCategory
        from datetime import datetime
        
        # Get analysis
        analysis = db.query(Analysis).filter(Analysis.id == UUID(analysis_id)).first()
        if not analysis:
            return {"status": "error", "message": "Analysis not found"}
        
        analysis.status = AnalysisStatus.RUNNING.value
        db.commit()
        
        # Get policy and effective date
        policy = db.query(Policy).filter(Policy.id == UUID(policy_id)).first()
        if not policy:
            analysis.status = AnalysisStatus.FAILED.value
            if hasattr(Analysis, 'error_message'):
                analysis.error_message = "Policy not found"
            db.commit()
            return {"status": "error", "message": "Policy not found"}
        
        # Get latest policy version
        version = db.query(PolicyVersion).filter(
            PolicyVersion.policy_id == UUID(policy_id)
        ).order_by(PolicyVersion.version_number.desc()).first()
        
        if not version:
            analysis.status = AnalysisStatus.FAILED.value
            if hasattr(Analysis, 'error_message'):
                analysis.error_message = "Policy version not found"
            db.commit()
            return {"status": "error", "message": "Policy version not found"}
        
        effective_date = version.effective_start_date
        if isinstance(effective_date, str):
            effective_date = datetime.fromisoformat(effective_date.replace("Z", "+00:00"))
        
        # Get treatment and control filters from config
        treatment_filters = config.get("treatment_filters", {})
        control_filters = config.get("control_filters")
        
        # Extract service category if specified
        service_category = None
        if "service_category" in treatment_filters:
            try:
                service_category = ServiceCategory(treatment_filters["service_category"])
            except (ValueError, TypeError):
                pass
        
        # Load predicted impact from policy metadata (Stage 3.5)
        predicted_impact = None
        try:
            from uepi_api.routers.policy_predicted_impact import get_predicted_impact_from_metadata
            policy_metadata = policy.policy_metadata_json if hasattr(policy, 'policy_metadata_json') else None
            predicted_impact = get_predicted_impact_from_metadata(policy_metadata)
        except Exception as e:
            # If predicted impact is not available, continue without it
            print(f"Could not load predicted impact for policy {policy_id}: {e}")
            predicted_impact = None
        
        # Load baseline metrics if available (Stage 3)
        # TODO: In full implementation, load baseline from baseline analysis results
        baseline_metrics = None
        
        # Run analysis using new impact analysis engine
        result = run_policy_impact_analysis(
            tenant_id=UUID(tenant_id),
            policy_id=UUID(policy_id),
            policy_effective_date=effective_date,
            treatment_filters=treatment_filters,
            control_filters=control_filters,
            pre_months=config.get("pre_window_months", 6),
            post_months=config.get("post_window_months", 6),
            metric=config.get("metric", "utilization_per_1k"),
            service_category=service_category,
            predicted_impact=predicted_impact,
            baseline_metrics=baseline_metrics,
        )
        
        # Store results in database (primary storage)
        from uepi_api.models.analysis import ImpactAnalysisResult
        
        try:
            # Check if result already exists
            existing_result = db.query(ImpactAnalysisResult).filter(
                ImpactAnalysisResult.analysis_id == UUID(analysis_id)
            ).first()
            
            if existing_result:
                # Update existing result
                existing_result.result_data_json = result
                existing_result.updated_at = datetime.utcnow()
                print(f"Updated existing impact result in database for analysis {analysis_id}")
            else:
                # Create new result
                impact_result = ImpactAnalysisResult(
                    tenant_id=UUID(tenant_id),
                    analysis_id=UUID(analysis_id),
                    policy_id=UUID(policy_id),
                    result_data_json=result,
                    schema_version="1.0",
                )
                db.add(impact_result)
                print(f"Stored impact result in database for analysis {analysis_id}")
            
            # Also create/update result index for backward compatibility
            existing_index = db.query(AnalysisResultIndex).filter(
                AnalysisResultIndex.analysis_id == UUID(analysis_id),
                AnalysisResultIndex.result_type == "SUMMARY"
            ).first()
            
            if not existing_index:
                result_index = AnalysisResultIndex(
                    tenant_id=UUID(tenant_id),
                    analysis_id=UUID(analysis_id),
                    result_type="SUMMARY",
                    data_uri=None,  # NULL indicates stored in database
                    schema_version="1.0",
                )
                db.add(result_index)
                print(f"Created result index entry (database storage)")
            
            # Commit both impact result and index together
            db.commit()
            print(f"✅ Successfully stored impact analysis results in database")
        except Exception as db_error:
            try:
                db.rollback()
            except:
                pass
            print(f"❌ Failed to store impact result in database: {db_error}")
            import traceback
            traceback.print_exc()
            # Continue - results are still returned, just not persisted
        
        # Update analysis status
        analysis.status = AnalysisStatus.COMPLETED.value
        db.commit()
        
        return {
            "status": "completed",
            "analysis_id": analysis_id,
            "result_storage": "database",
        }
    except Exception as e:
        if 'analysis' in locals():
            analysis.status = AnalysisStatus.FAILED.value
            err_msg = str(e)
            if hasattr(Analysis, 'error_message'):
                analysis.error_message = (err_msg[:2000] if len(err_msg) > 2000 else err_msg) or None
            db.commit()
        raise
    finally:
        db.close()


@app.task(base=BaseTask, bind=True, max_retries=3)
def substitution_job(
    self,
    tenant_id: str,
    analysis_id: str,
    policy_id: str,
    policy_effective_date: str,
    treatment_filters: dict,
    pre_months: int = 6,
    post_months: int = 6,
) -> dict:
    """Detect substitution patterns"""
    db = SessionLocal()
    try:
        from uepi_api.models.analysis import Analysis, AnalysisStatus, AnalysisResultIndex
        from uepi_worker.substitution_analysis import run_substitution_analysis
        from datetime import datetime
        
        # Get analysis
        analysis = db.query(Analysis).filter(Analysis.id == UUID(analysis_id)).first()
        if not analysis:
            return {"status": "error", "message": "Analysis not found"}
        
        analysis.status = AnalysisStatus.RUNNING.value
        db.commit()
        
        # Parse effective date
        effective_date = datetime.fromisoformat(policy_effective_date.replace("Z", "+00:00"))
        
        # Run substitution analysis using new engine
        result = run_substitution_analysis(
            tenant_id=UUID(tenant_id),
            analysis_id=UUID(analysis_id),
            policy_id=UUID(policy_id),
            policy_effective_date=effective_date,
            treatment_filters=treatment_filters,
            pre_months=pre_months,
            post_months=post_months,
        )
        
        # Save results to object storage
        s3_client = get_s3_client()
        bucket = settings.object_storage.bucket
        result_key = f"{tenant_id}/results/analyses/{analysis_id}/substitution.json"
        
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            json.dump(result, tmp, indent=2)
            tmp_path = tmp.name
        
        try:
            s3_client.upload_file(tmp_path, bucket, result_key)
        finally:
            os.unlink(tmp_path)
        
        # Create result index
        result_index = AnalysisResultIndex(
            tenant_id=UUID(tenant_id),
            analysis_id=UUID(analysis_id),
            result_type="SUBSTITUTION",
            data_uri=f"s3://{bucket}/{result_key}",
            schema_version="1.0",
        )
        db.add(result_index)
        
        # Update analysis status
        analysis.status = AnalysisStatus.COMPLETED.value
        db.commit()
        
        return {
            "status": "completed",
            "analysis_id": analysis_id,
            "result_uri": f"s3://{bucket}/{result_key}",
        }
    except Exception as e:
        if 'analysis' in locals():
            analysis.status = AnalysisStatus.FAILED.value
            err_msg = str(e)
            if hasattr(Analysis, 'error_message'):
                analysis.error_message = (err_msg[:2000] if len(err_msg) > 2000 else err_msg) or None
            db.commit()
        raise
    finally:
        db.close()


@app.task(base=BaseTask, bind=True, max_retries=3)
def provider_segmentation_job(
    self,
    tenant_id: str,
    analysis_id: str,
    policy_id: str,
    policy_effective_date: str,
    treatment_filters: dict,
    pre_months: int = 6,
    post_months: int = 6,
) -> dict:
    """Segment providers by response pattern"""
    db = SessionLocal()
    try:
        from uepi_api.models.analysis import Analysis, AnalysisStatus, AnalysisResultIndex
        from uepi_worker.provider_segmentation_analysis import run_provider_segmentation_analysis
        from datetime import datetime
        
        # Get analysis
        analysis = db.query(Analysis).filter(Analysis.id == UUID(analysis_id)).first()
        if not analysis:
            return {"status": "error", "message": "Analysis not found"}
        
        analysis.status = AnalysisStatus.RUNNING.value
        db.commit()
        
        # Parse effective date
        effective_date = datetime.fromisoformat(policy_effective_date.replace("Z", "+00:00"))
        
        # Run provider segmentation using new engine
        result = run_provider_segmentation_analysis(
            tenant_id=UUID(tenant_id),
            analysis_id=UUID(analysis_id),
            policy_id=UUID(policy_id),
            policy_effective_date=effective_date,
            treatment_filters=treatment_filters,
            pre_months=pre_months,
            post_months=post_months,
            n_clusters=4,  # Default to 4 archetypes
        )
        
        # Save results to object storage
        s3_client = get_s3_client()
        bucket = settings.object_storage.bucket
        result_key = f"{tenant_id}/results/analyses/{analysis_id}/provider_segmentation.json"
        
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            json.dump(result, tmp, indent=2)
            tmp_path = tmp.name
        
        try:
            s3_client.upload_file(tmp_path, bucket, result_key)
        finally:
            os.unlink(tmp_path)
        
        # Create result index
        result_index = AnalysisResultIndex(
            tenant_id=UUID(tenant_id),
            analysis_id=UUID(analysis_id),
            result_type="PROVIDER_SEGMENTATION",
            data_uri=f"s3://{bucket}/{result_key}",
            schema_version="1.0",
        )
        db.add(result_index)
        
        # Update analysis status
        analysis.status = AnalysisStatus.COMPLETED.value
        db.commit()
        
        return {
            "status": "completed",
            "analysis_id": analysis_id,
            "result_uri": f"s3://{bucket}/{result_key}",
        }
    except Exception as e:
        if 'analysis' in locals():
            analysis.status = AnalysisStatus.FAILED.value
            err_msg = str(e)
            if hasattr(Analysis, 'error_message'):
                analysis.error_message = (err_msg[:2000] if len(err_msg) > 2000 else err_msg) or None
            db.commit()
        raise
    finally:
        db.close()


@app.task(base=BaseTask, bind=True, max_retries=3)
def whatif_scenario_job(
    self,
    tenant_id: str,
    analysis_id: str,
    policy_id: str,
    scenario_params: dict,
    baseline_filters: dict,
) -> dict:
    """Run what-if scenario simulation (delegates to shared runner in API)."""
    from uepi_api.services.whatif_runner import run_whatif_scenario_sync
    db = SessionLocal()
    try:
        return run_whatif_scenario_sync(
            tenant_id=tenant_id,
            analysis_id=analysis_id,
            policy_id=policy_id,
            scenario_params=scenario_params,
            baseline_filters=baseline_filters,
            db=db,
        )
    finally:
        db.close()


@app.task(base=BaseTask, bind=True, max_retries=3)
def elasticity_job(
    self,
    tenant_id: str,
    analysis_id: str,
    policy_id: str,
    service_categories: Optional[list[str]] = None,
) -> dict:
    """Model elasticity curves for a policy"""
    db = SessionLocal()
    try:
        from uepi_api.models.analysis import Analysis, AnalysisStatus, AnalysisResultIndex, ElasticityAnalysisResult
        from uepi_common.analytics.elasticity import ElasticityModeler
        from uepi_common.storage.factory import create_storage_client
        from uepi_common.data.parquet_service import ParquetDataService
        from datetime import datetime
        import json
        import tempfile
        import os
        
        # Get analysis
        analysis = db.query(Analysis).filter(Analysis.id == UUID(analysis_id)).first()
        if not analysis:
            return {"status": "error", "message": "Analysis not found"}
        
        analysis.status = AnalysisStatus.RUNNING.value
        db.commit()

        settings = get_settings()
        # Modeler needs storage_client for init; use no-op when object storage (S3) not configured (DB-only / local)
        try:
            storage_client = create_storage_client(settings=settings.object_storage)
        except Exception:
            from uepi_common.storage.noop import NoOpBlobStorageClient
            storage_client = NoOpBlobStorageClient()
        bucket = getattr(settings.object_storage, "bucket", None) or getattr(settings.object_storage, "bucket_name", None) or "uepi-data"
        modeler = ElasticityModeler(storage_client, bucket)

        result = modeler.estimate_elasticity(
            UUID(tenant_id),
            UUID(policy_id),
            service_categories,
        )
        
        result_dict = {
            "policy_id": str(result.policy_id),
            "service_categories": {
                k: {
                    "service_category": v.service_category,
                    "elasticity_coefficient": v.elasticity_coefficient,
                    "elasticity_function": v.elasticity_function,
                    "threshold_friction": v.threshold_friction,
                    "confidence_score": v.confidence_score,
                    "data_points": v.data_points,
                    "model_version": getattr(v, "model_version", "1.0"),
                    "created_at": v.created_at.isoformat(),
                }
                for k, v in result.service_categories.items()
            },
            "overall_elasticity": result.overall_elasticity,
            "model_quality": result.model_quality,
            "warnings": getattr(result, "warnings", []),
            "created_at": result.created_at.isoformat(),
        }
        
        # Persist to database first (so GET results works without object storage)
        existing = db.query(ElasticityAnalysisResult).filter(
            ElasticityAnalysisResult.analysis_id == UUID(analysis_id),
            ElasticityAnalysisResult.tenant_id == UUID(tenant_id),
        ).first()
        if existing:
            existing.result_data_json = result_dict
            existing.updated_at = datetime.utcnow()
        else:
            db.add(ElasticityAnalysisResult(
                tenant_id=UUID(tenant_id),
                analysis_id=UUID(analysis_id),
                policy_id=UUID(policy_id),
                result_data_json=result_dict,
                schema_version="1.0",
            ))
        # Ensure result index exists (DB storage; data_uri=None)
        idx = db.query(AnalysisResultIndex).filter(
            AnalysisResultIndex.analysis_id == UUID(analysis_id),
            AnalysisResultIndex.result_type == "ELASTICITY",
        ).first()
        if not idx:
            db.add(AnalysisResultIndex(
                tenant_id=UUID(tenant_id),
                analysis_id=UUID(analysis_id),
                result_type="ELASTICITY",
                data_uri=None,
                schema_version="1.0",
            ))
        analysis.status = AnalysisStatus.COMPLETED.value
        db.commit()
        # Optional S3 upload after marking COMPLETED so frontend does not wait on storage
        result_key = f"{tenant_id}/results/analyses/{analysis_id}/elasticity.json"
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
                json.dump(result_dict, tmp, indent=2, default=str)
                tmp_path = tmp.name
            try:
                with open(tmp_path, 'rb') as f:
                    storage_client.upload_blob(
                        container=settings.object_storage.bucket,
                        blob_name=result_key,
                        data=f.read(),
                        content_type="application/json",
                    )
                uri = f"{settings.object_storage.bucket}/{result_key}"
                idx2 = db.query(AnalysisResultIndex).filter(
                    AnalysisResultIndex.analysis_id == UUID(analysis_id),
                    AnalysisResultIndex.result_type == "ELASTICITY",
                ).first()
                if idx2:
                    idx2.data_uri = uri
                    db.commit()
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except Exception as upload_err:
            print(f"Elasticity: optional upload failed (results saved to DB): {upload_err}")
        
        return {
            "status": "completed",
            "analysis_id": analysis_id,
            "model_quality": result.model_quality,
            "overall_elasticity": result.overall_elasticity,
        }
    except Exception as e:
        if 'analysis' in locals():
            analysis.status = AnalysisStatus.FAILED.value
            err_msg = str(e)
            if hasattr(Analysis, 'error_message'):
                analysis.error_message = (err_msg[:2000] if len(err_msg) > 2000 else err_msg) or None
            db.commit()
        raise
    finally:
        db.close()


@app.task(base=BaseTask, bind=True, max_retries=3)
def scorecard_job(
    self,
    tenant_id: str,
    period: str,
    policy_ids: Optional[list[str]] = None,
) -> dict:
    """Generate scorecards for period"""
    db = SessionLocal()
    try:
        from uepi_api.models.scorecard import Scorecard, ScorecardEntry
        from uepi_api.models.policy import Policy
        from uepi_worker.scorecards import ScorecardGenerator
        from uepi_common.storage.factory import create_storage_client
        from uepi_common.data.parquet_service import ParquetDataService
        from datetime import datetime
        import json
        
        settings = get_settings()
        storage_client = create_storage_client(settings=settings.object_storage)
        parquet_service = ParquetDataService(storage_client, settings.object_storage.bucket)
        generator = ScorecardGenerator(storage_client, settings.object_storage.bucket)
        
        # Get policies to generate scorecards for
        if policy_ids:
            policies = db.query(Policy).filter(
                Policy.id.in_([UUID(p_id) for p_id in policy_ids]),
                Policy.tenant_id == UUID(tenant_id),
            ).all()
        else:
            # Generate for all active policies
            policies = db.query(Policy).filter(
                Policy.tenant_id == UUID(tenant_id),
                Policy.status == 'ACTIVE',
            ).all()
        
        generated_scorecards = []
        
        for policy in policies:
            try:
                # Generate scorecard
                scorecard_metrics = generator.generate_scorecard(
                    UUID(tenant_id),
                    policy.id,
                    period,
                )
                
                # Save scorecard to database
                # Check if scorecard already exists for this policy/period
                existing = db.query(Scorecard).filter(
                    Scorecard.policy_id == policy.id,
                    Scorecard.period == period,
                    Scorecard.tenant_id == UUID(tenant_id),
                ).first()
                
                if existing:
                    # Update existing scorecard
                    existing.effectiveness_index = scorecard_metrics.effectiveness_index
                    existing.cost_impact_score = scorecard_metrics.cost_impact_score
                    existing.behavioral_risk_score = scorecard_metrics.behavioral_risk_score
                    existing.access_impact_score = scorecard_metrics.access_impact_score
                    existing.regulatory_defensibility_score = scorecard_metrics.regulatory_defensibility_score
                    existing.updated_at = datetime.utcnow()
                    scorecard = existing
                    
                    # Delete existing entries
                    db.query(ScorecardEntry).filter(
                        ScorecardEntry.scorecard_id == scorecard.id,
                    ).delete()
                else:
                    # Create new scorecard
                    scorecard = Scorecard(
                        tenant_id=UUID(tenant_id),
                        policy_id=policy.id,
                        period=period,
                        effectiveness_index=scorecard_metrics.effectiveness_index,
                        cost_impact_score=scorecard_metrics.cost_impact_score,
                        behavioral_risk_score=scorecard_metrics.behavioral_risk_score,
                        access_impact_score=scorecard_metrics.access_impact_score,
                        regulatory_defensibility_score=scorecard_metrics.regulatory_defensibility_score,
                        weights=json.dumps({
                            "cost_impact": 0.4,
                            "behavioral_risk": 0.3,
                            "access_impact": 0.2,
                            "regulatory_defensibility": 0.1,
                        }),
                    )
                    db.add(scorecard)
                
                db.flush()
                
                # Add entries
                for entry in scorecard_metrics.entries:
                    scorecard_entry = ScorecardEntry(
                        tenant_id=UUID(tenant_id),
                        scorecard_id=scorecard.id,
                        dimension=entry["dimension"],
                        metric_name=entry["metric_name"],
                        metric_value=entry["metric_value"],
                        metric_unit=entry.get("metric_unit"),
                        trend=entry.get("trend"),
                    )
                    db.add(scorecard_entry)
                
                generated_scorecards.append({
                    "policy_id": str(policy.id),
                    "scorecard_id": str(scorecard.id),
                    "period": period,
                    "effectiveness_index": scorecard_metrics.effectiveness_index,
                })
                
            except Exception as e:
                print(f"Failed to generate scorecard for policy {policy.id}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        db.commit()
        
        return {
            "status": "completed",
            "period": period,
            "scorecards_generated": len(generated_scorecards),
            "scorecards": generated_scorecards,
        }
    except Exception as e:
        db.rollback()
        print(f"Scorecard generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


@app.task(base=BaseTask, bind=True, max_retries=3)
def export_pdf_job(
    self,
    tenant_id: str,
    analysis_id: str,
    export_id: str,
) -> dict:
    """Generate PDF export"""
    db = SessionLocal()
    try:
        from uepi_api.models.export import Export, ExportStatus
        from uepi_api.models.analysis import Analysis, AnalysisResultIndex
        from uepi_worker.exports import PDFGenerator, PPTXGenerator
        from uepi_common.storage.factory import create_storage_client
        from uepi_common.data.parquet_service import ParquetDataService
        from datetime import datetime
        import json
        
        # Get export record
        export = db.query(Export).filter(Export.id == UUID(export_id)).first()
        if not export:
            return {"status": "error", "message": "Export not found"}
        
        export.status = ExportStatus.PROCESSING.value
        db.commit()
        
        # Get analysis results
        analysis = db.query(Analysis).filter(Analysis.id == UUID(analysis_id)).first()
        if not analysis:
            export.status = ExportStatus.FAILED.value
            export.error_message = "Analysis not found"
            db.commit()
            return {"status": "error", "message": "Analysis not found"}
        
        # Load analysis results
        result_indices = db.query(AnalysisResultIndex).filter(
            AnalysisResultIndex.analysis_id == UUID(analysis_id),
        ).all()
        
        analysis_results = {}
        settings = get_settings()
        storage_client = create_storage_client(settings=settings.object_storage)
        parquet_service = ParquetDataService(storage_client, settings.object_storage.bucket)
        
        for result_index in result_indices:
            # Load result from storage
            result_key = result_index.data_uri.replace(f"{settings.object_storage.bucket}/", "")
            try:
                result_data = storage_client.download_blob(
                    container=settings.object_storage.bucket,
                    blob_name=result_key,
                )
                if result_data:
                    result_json = json.loads(result_data.decode('utf-8'))
                    analysis_results[result_index.result_type] = result_json
            except Exception as e:
                print(f"Failed to load result {result_index.result_type}: {e}")
        
        # Generate PDF
        pdf_generator = PDFGenerator(storage_client, settings.object_storage.bucket)
        pdf_bytes = pdf_generator.generate_audit_pack_pdf(
            UUID(tenant_id),
            UUID(analysis_id),
            analysis_results,
        )
        
        # Save PDF to storage
        pdf_key = f"{tenant_id}/exports/{export_id}/audit-pack.pdf"
        storage_client.upload_blob(
            container=settings.object_storage.bucket,
            blob_name=pdf_key,
            data=pdf_bytes,
            content_type="application/pdf",
        )
        
        # Update export record
        export.status = ExportStatus.COMPLETED.value
        export.file_uri = f"{settings.object_storage.bucket}/{pdf_key}"
        export.file_size_bytes = len(pdf_bytes)
        export.completed_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": "completed",
            "export_id": export_id,
            "file_uri": export.file_uri,
            "file_size_bytes": export.file_size_bytes,
        }
    except Exception as e:
        if 'export' in locals():
            export.status = ExportStatus.FAILED.value
            export.error_message = str(e)
            db.commit()
        raise
    finally:
        db.close()


@app.task(base=BaseTask, bind=True, max_retries=3)
def export_pptx_job(
    self,
    tenant_id: str,
    analysis_id: str,
    export_id: str,
) -> dict:
    """Generate PPTX export"""
    db = SessionLocal()
    try:
        from uepi_api.models.export import Export, ExportStatus
        from uepi_api.models.analysis import Analysis, AnalysisResultIndex
        from uepi_worker.exports import PDFGenerator, PPTXGenerator
        from uepi_common.storage.factory import create_storage_client
        from uepi_common.data.parquet_service import ParquetDataService
        from datetime import datetime
        import json
        
        # Get export record
        export = db.query(Export).filter(Export.id == UUID(export_id)).first()
        if not export:
            return {"status": "error", "message": "Export not found"}
        
        export.status = ExportStatus.PROCESSING.value
        db.commit()
        
        # Get analysis results
        analysis = db.query(Analysis).filter(Analysis.id == UUID(analysis_id)).first()
        if not analysis:
            export.status = ExportStatus.FAILED.value
            export.error_message = "Analysis not found"
            db.commit()
            return {"status": "error", "message": "Analysis not found"}
        
        # Load analysis results
        result_indices = db.query(AnalysisResultIndex).filter(
            AnalysisResultIndex.analysis_id == UUID(analysis_id),
        ).all()
        
        analysis_results = {}
        settings = get_settings()
        storage_client = create_storage_client(settings=settings.object_storage)
        parquet_service = ParquetDataService(storage_client, settings.object_storage.bucket)
        
        for result_index in result_indices:
            # Load result from storage
            result_key = result_index.data_uri.replace(f"{settings.object_storage.bucket}/", "")
            try:
                result_data = storage_client.download_blob(
                    container=settings.object_storage.bucket,
                    blob_name=result_key,
                )
                if result_data:
                    result_json = json.loads(result_data.decode('utf-8'))
                    analysis_results[result_index.result_type] = result_json
            except Exception as e:
                print(f"Failed to load result {result_index.result_type}: {e}")
        
        # Generate PPTX
        pptx_generator = PPTXGenerator(storage_client, settings.object_storage.bucket)
        pptx_bytes = pptx_generator.generate_presentation_pptx(
            UUID(tenant_id),
            UUID(analysis_id),
            analysis_results,
        )
        
        # Save PPTX to storage
        pptx_key = f"{tenant_id}/exports/{export_id}/presentation.pptx"
        storage_client.upload_blob(
            container=settings.object_storage.bucket,
            blob_name=pptx_key,
            data=pptx_bytes,
            content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        
        # Update export record
        export.status = ExportStatus.COMPLETED.value
        export.file_uri = f"{settings.object_storage.bucket}/{pptx_key}"
        export.file_size_bytes = len(pptx_bytes)
        export.completed_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": "completed",
            "export_id": export_id,
            "file_uri": export.file_uri,
            "file_size_bytes": export.file_size_bytes,
        }
    except Exception as e:
        if 'export' in locals():
            export.status = ExportStatus.FAILED.value
            export.error_message = str(e)
            db.commit()
        raise
    finally:
        db.close()
