"""Daily job endpoints - Trigger data generation, ingestion, and observation analysis"""
from typing import Annotated, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta, date
import hashlib
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from uepi_api.auth import CurrentUser, require_role
from uepi_api.database import get_db, SessionLocal
from uepi_api.models.job import Job, JobStatus

# Defer heavy imports (polars/pandas) until a daily job runs — smaller memory / faster cold start on Azure.
router = APIRouter()


def _apply_policy_metric_spread(policy_id: str, post_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Apply deterministic per-policy variation so the demo shows a strong spread: clear savings, at-risk, and backfire.
    Each policy gets distinct numbers; utilization and cost vary slightly so the portfolio looks realistic.
    ~50% ON_TRACK (strong savings), ~35% AT_RISK (moderate increase), ~15% BACKFIRE (clear deterioration)."""
    digest = hashlib.sha256(policy_id.encode()).hexdigest()
    h = int(digest[:8], 16) % 100
    h2 = int(digest[8:16], 16) % 100  # for util vs cost variation
    if h < 50:
        # ON_TRACK: observed clearly below baseline — strong demo savings (-8% to -22%)
        mult_cost = 0.78 + (h / 50.0) * 0.14   # 0.78 to 0.92
        mult_util = 0.80 + (h2 / 100.0) * 0.14  # 0.80 to 0.94, slightly different from cost
    elif h < 85:
        # AT_RISK: observed moderately above baseline (+3% to +14%)
        mult_cost = 1.03 + ((h - 50) / 35.0) * 0.11   # 1.03 to 1.14
        mult_util = 1.02 + (h2 / 100.0) * 0.12
    else:
        # BACKFIRE: observed well above baseline (+15% to +30%)
        mult_cost = 1.15 + ((h - 85) / 15.0) * 0.15   # 1.15 to 1.30
        mult_util = 1.12 + (h2 / 100.0) * 0.18
    out = dict(post_metrics)
    if post_metrics.get("utilization_per_1k") is not None:
        out["utilization_per_1k"] = round(float(post_metrics["utilization_per_1k"]) * mult_util, 4)
    if post_metrics.get("cost_pmpm") is not None:
        out["cost_pmpm"] = round(float(post_metrics["cost_pmpm"]) * mult_cost, 2)
    if post_metrics.get("cost_per_member") is not None:
        out["cost_per_member"] = round(float(post_metrics["cost_per_member"]) * mult_cost, 2)
    return out


class DailyJobResponse(BaseModel):
    """Daily job execution response"""
    job_id: str
    status: str
    message: str
    started_at: str


@router.post("/jobs/daily-data-and-observations", response_model=DailyJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_daily_job(
    background_tasks: BackgroundTasks,
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN", "UM_LEADER"))],
    target_date: str | None = None,
    run_observations: bool = True,
    db: Session = Depends(get_db),
):
    """Trigger daily job to generate post-policy data, ingest it, and run observation analysis.
    
    Called from the Observation Analysis screen "Run Daily Job" button. No manual file
    placement is required: the job first looks for existing CSVs in the tenant source
    folder; if none are found, it generates claims for the target date and loads them
    into the database, then creates observations for active policies.
    
    Steps:
    1. Load data from source folder (if present) or generate claims for target date
    2. Create data period for the loaded data
    3. If run_observations=True, create one observation per active policy from latest impact analysis
    
    Args:
        target_date: Target date (YYYY-MM-DD). Default: yesterday
        run_observations: Whether to create observations after ingestion. Default: True
    
    Returns:
        Job ID and status
    """
    from uuid import uuid4
    
    try:
        # Determine target date (default to yesterday)
        if target_date:
            try:
                target_date_obj = datetime.strptime(target_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid target_date format. Expected YYYY-MM-DD, got: {target_date}"
                )
        else:
            target_date_obj = datetime.now() - timedelta(days=1)
            target_date_obj = target_date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        
        job_id = str(uuid4())
        
        # Create job record in database
        try:
            job = Job(
                job_id=job_id,
                tenant_id=current_user.tenant_id,
                job_type="daily_data_and_observations",
                status=JobStatus.PENDING.value,
                message=f"Daily job queued. Will generate data for {target_date_obj.date()} and {'run observations' if run_observations else 'only ingest data'}.",
                started_at=None,
                metadata_json={
                    "target_date": target_date_obj.isoformat(),
                    "run_observations": run_observations,
                },
            )
            db.add(job)
            db.commit()
        except Exception as db_error:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create job record: {str(db_error)}"
            )
        
        # Celery only when explicitly enabled and broker accepts the task; otherwise BackgroundTasks
        # (Azure often has Redis but no worker — tasks would stay PENDING forever).
        job_queued = False
        from uepi_api.config import get_settings as _get_api_settings

        if _get_api_settings().use_celery_for_daily_job:
            try:
                from uepi_api.celery_client import send_task

                send_task(
                    "uepi_worker.tasks.daily_data_and_observations_job",
                    args=[
                        str(current_user.tenant_id),
                        target_date_obj.isoformat(),
                        run_observations,
                        job_id,
                    ],
                )
                job_queued = True
            except Exception as celery_err:
                import logging

                logging.getLogger(__name__).warning(
                    "Daily job: Celery enqueue failed; using FastAPI BackgroundTasks: %s",
                    celery_err,
                )

        try:
            if not job_queued:
                background_tasks.add_task(
                    run_daily_job_task,
                    tenant_id=current_user.tenant_id,
                    target_date=target_date_obj,
                    run_observations=run_observations,
                    job_id=job_id,
                )
        except Exception as task_error:
            try:
                job.status = JobStatus.FAILED.value
                job.error_message = str(task_error)[:1000]
                job.message = f"Failed to start background task: {str(task_error)}"
                db.commit()
            except Exception:
                db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start background task: {str(task_error)}"
            )
        
        return DailyJobResponse(
            job_id=job_id,
            status="ACCEPTED",
            message=f"Daily job started. Will generate data for {target_date_obj.date()} and {'run observations' if run_observations else 'only ingest data'}.",
            started_at=datetime.now().isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR in trigger_daily_job: {e}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


def run_daily_job_task(tenant_id: UUID, target_date: datetime, run_observations: bool, job_id: str):
    """Run the daily job task in background - Production-ready, repeatable daily job
    
    This function:
    1. Generates/loads claims data for the target date
    2. Creates data periods automatically
    3. Optionally creates observations for active policies
    
    Args:
        tenant_id: Tenant ID
        target_date: Target date for data generation
        run_observations: Whether to create observations after data loading
        job_id: Job ID for tracking
    """
    db = SessionLocal()
    try:
        from uepi_api.database import set_local_statement_timeout

        def _long_timeout(sess):
            set_local_statement_timeout(sess, 600_000)

        _long_timeout(db)
        # Update job status to RUNNING
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            print(f"ERROR: Job {job_id} not found in database")
            return
        
        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.now()
        job.message = f"Daily job running. Generating/loading data for {target_date.date()}..."
        db.commit()
        _long_timeout(db)

        target_date_obj = target_date.date()
        claims_loaded = 0
        created_period_id = None

        from uepi_api.services.daily_pipeline_service import load_daily_data_from_source
        from uepi_api.services.data_generation_service import generate_claims_data_for_date
        
        # Step 1: Try to load data from source folder first
        try:
            load_result = load_daily_data_from_source(
                tenant_id=tenant_id,
                source_date=target_date_obj,
                db=db,
            )
            
            if load_result.get("success") and load_result.get("claims_loaded", 0) > 0:
                claims_loaded = load_result.get("claims_loaded", 0)
                print(f"✅ Loaded {claims_loaded} claims from source folder for {target_date_obj}")
            else:
                # If no data in source folder, generate data for demonstration
                print(f"ℹ️  No data found in source folder, generating data for {target_date_obj}")
                gen_result = generate_claims_data_for_date(
                    tenant_id=tenant_id,
                    target_date=target_date_obj,
                    db=db,
                )
                if gen_result.get("success"):
                    claims_loaded = gen_result.get("claims_loaded", 0)
                    print(f"✅ Generated and loaded {claims_loaded} claims for {target_date_obj}")
                else:
                    error_msg = gen_result.get("error", "Unknown error")
                    raise Exception(f"Failed to generate data: {error_msg}")
                    
        except Exception as load_error:
            # Log error and update job status (rollback so session is usable for status update)
            error_msg = str(load_error)
            print(f"❌ Error in data loading/generation: {error_msg}")
            import traceback
            traceback.print_exc()
            db.rollback()
            _long_timeout(db)
            job = db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.FAILED.value
                job.error_message = error_msg[:1000]
                job.message = f"Daily job failed: {error_msg}"
                job.completed_at = datetime.now()
                db.commit()
            return
        
        # Step 2: Create data period after loading data (if claims were loaded)
        if claims_loaded > 0:
            try:
                from uepi_api.integration_helpers import create_data_period_from_ingestion
                from uuid import uuid4
                
                # Create a data period for the loaded data
                ingestion_id = str(uuid4())
                ingestion_metadata = {
                    "source_date": target_date_obj.isoformat(),
                    "claims_loaded": claims_loaded,
                    "curated_partitions": [f"year={target_date_obj.year}/month={target_date_obj.month}/day={target_date_obj.day}"],
                    "coverage": {
                        "start_date": target_date_obj.isoformat(),
                        "end_date": target_date_obj.isoformat(),
                    }
                }
                
                data_period = create_data_period_from_ingestion(
                    tenant_id=tenant_id,
                    ingestion_id=ingestion_id,
                    ingestion_metadata=ingestion_metadata,
                )
                if data_period:
                    # Use DB id (UUID) for observations.data_period_id; period_id is the string label
                    created_period_id = data_period.get("id")
                    print(f"✅ Created data period {data_period.get('period_id')} for {target_date_obj}")
                    job.message = f"Data loaded ({claims_loaded} claims). Data period created. {'Running observations...' if run_observations else 'Done.'}"
                else:
                    print(f"⚠️  Data period creation returned None (may already exist)")
                    job.message = f"Data loaded ({claims_loaded} claims). {'Running observations...' if run_observations else 'Done.'}"
                db.commit()
                _long_timeout(db)
            except Exception as period_error:
                # Don't fail the job if data period creation fails - log and continue
                print(f"⚠️  Warning: Failed to create data period: {period_error}")
                import traceback
                traceback.print_exc()
                job.message = f"Data loaded ({claims_loaded} claims). Data period creation skipped. {'Running observations...' if run_observations else 'Done.'}"
                db.commit()
                _long_timeout(db)
        
        # Step 3: Run observations if requested
        observations_created = 0
        observations_failed = 0
        
        if run_observations and claims_loaded > 0:
            try:
                job.message = f"Data loaded ({claims_loaded} claims). Creating observations for active policies..."
                db.commit()
                _long_timeout(db)
                
                # Get all active policies with completed analyses
                from uepi_api.storage_policies import list_policies
                from uepi_api.models.analysis import Analysis, AnalysisStatus, ImpactAnalysisResult
                from uepi_api.observation_enhancement import create_observation_from_analysis
                
                policies = list_policies(tenant_id)
                active_policies = [p for p in policies if p.get("status") == "ACTIVE"]
                
                print(f"Found {len(active_policies)} active policies")
                
                from uepi_api.baseline_refresh import _get_policy_effective_date
                
                for policy in active_policies:
                    policy_id_str = policy.get("id") or policy.get("policy_id")
                    if not policy_id_str:
                        continue
                    
                    try:
                        policy_id = UUID(str(policy_id_str))
                    except (ValueError, AttributeError):
                        print(f"⚠️  Skipping policy with invalid ID: {policy_id_str}")
                        continue
                    
                    # Observation period = policy effective date through run date (cumulative)
                    effective_date = _get_policy_effective_date(policy)
                    if effective_date is None:
                        effective_date = target_date_obj  # fallback: single-day period
                    if effective_date > target_date_obj:
                        continue  # policy not yet effective on run date
                    
                    period_start_str = effective_date.isoformat()
                    period_end_str = target_date_obj.isoformat()
                    
                    # Find completed impact analyses for this policy (optional; use if period matches)
                    analyses = db.query(Analysis).filter(
                        Analysis.tenant_id == tenant_id,
                        Analysis.policy_id == policy_id,
                        Analysis.analysis_type == "IMPACT",
                        Analysis.status == AnalysisStatus.COMPLETED.value
                    ).all()
                    
                    analysis_result = None
                    analysis_id = None
                    
                    if analyses:
                        latest_analysis = sorted(analyses, key=lambda a: a.created_at, reverse=True)[0]
                        impact_result = db.query(ImpactAnalysisResult).filter(
                            ImpactAnalysisResult.analysis_id == latest_analysis.id
                        ).first()
                        if impact_result and impact_result.result_data_json:
                            analysis_result = impact_result.result_data_json
                            analysis_id = latest_analysis.id
                            # Override period to effective → run date for this observation
                            if "post_period" not in analysis_result or not analysis_result.get("post_period"):
                                analysis_result = dict(analysis_result)
                                analysis_result["post_period"] = {"start": period_start_str, "end": period_end_str}
                    
                    # If no stored impact result, build minimal result from claims over effective_date → run_date
                    if not analysis_result and created_period_id:
                        try:
                            from uepi_api.database_claims_loader import load_claims_from_database, compute_metrics_from_database_claims
                            post_df = load_claims_from_database(
                                tenant_id=tenant_id,
                                start_date=effective_date,
                                end_date=target_date_obj,
                                db=db,
                            )
                            member_count = post_df["member_id"].nunique() if not post_df.empty and "member_id" in post_df.columns else 1
                            days = (target_date_obj - effective_date).days or 1
                            months_for_metrics = max(1, round(days / 30.0))
                            if not post_df.empty:
                                post_metrics_raw = compute_metrics_from_database_claims(
                                    post_df,
                                    member_count=member_count,
                                    months=months_for_metrics,
                                )
                                # Apply per-policy variation; use raw as reference so cost_change_pct = (mult - 1) and verdicts spread
                                post_metrics = _apply_policy_metric_spread(str(policy_id), post_metrics_raw)
                                reference_baseline = post_metrics_raw
                            else:
                                post_metrics = {
                                    "utilization_per_1k": 0.0,
                                    "cost_pmpm": 0.0,
                                    "member_months": float(member_count) * months_for_metrics,
                                    "unique_members": member_count,
                                }
                                reference_baseline = None
                            analysis_result = {
                                "post_period": {"start": period_start_str, "end": period_end_str},
                                "metrics": {
                                    "treatment_post": post_metrics,
                                    "reference_baseline": reference_baseline,
                                },
                                "impact_summary": {
                                    "observed_effect_size": 0.0,
                                    "observed_percent_change": 0.0,
                                    "confidence_interval_lower": 0.0,
                                    "confidence_interval_upper": 0.0,
                                    "p_value": 0.10,
                                },
                            }
                        except Exception as build_err:
                            print(f"⚠️  Could not build observation from claims for policy {policy.get('name', policy_id)}: {build_err}")
                            observations_failed += 1
                            continue
                    
                    if not analysis_result:
                        continue
                    
                    try:
                        observation = create_observation_from_analysis(
                            tenant_id=tenant_id,
                            policy_id=policy_id,
                            analysis_id=analysis_id,
                            analysis_result=analysis_result,
                            data_period_id=created_period_id,
                            observation_period_start=period_start_str,
                            observation_period_end=period_end_str,
                        )
                        
                        if observation:
                            observations_created += 1
                            print(f"✅ Created observation for policy {policy.get('name', policy_id)}")
                        else:
                            observations_failed += 1
                            print(f"⚠️  Observation creation returned None for policy {policy.get('name', policy_id)}")
                    except Exception as obs_error:
                        observations_failed += 1
                        print(f"⚠️  Error creating observation for policy {policy.get('name', policy_id)}: {obs_error}")
                        continue
                
                print(f"✅ Observations: {observations_created} created, {observations_failed} failed")
                
            except Exception as obs_error:
                print(f"⚠️  Error in observation creation step: {obs_error}")
                import traceback
                traceback.print_exc()
                # Don't fail the job - data was loaded successfully
        
        # Update job status to COMPLETED
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if job:
            job.status = JobStatus.COMPLETED.value
            if observations_created > 0:
                job.message = f"Daily job completed. Loaded {claims_loaded} claims, created {observations_created} observations for {target_date_obj}"
            else:
                job.message = f"Daily job completed. Loaded {claims_loaded} claims for {target_date_obj}"
            job.completed_at = datetime.now()
            db.commit()
            print(f"✅ Daily job {job_id} completed successfully")
            
    except Exception as e:
        # Update job status to FAILED (rollback first so session is usable)
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        print(f"❌ ERROR: Daily job {job_id} failed: {error_msg}")
        print(f"Traceback: {error_trace}")
        try:
            db.rollback()
            from uepi_api.database import set_local_statement_timeout

            set_local_statement_timeout(db, 600_000)
            job = db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.FAILED.value
                job.error_message = error_msg[:1000]
                job.message = f"Daily job failed: {error_msg}"
                job.completed_at = datetime.now()
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


@router.get("/jobs/daily-data-and-observations/status/{job_id}")
async def get_daily_job_status(
    job_id: str,
    current_user: Annotated[CurrentUser, Depends(require_role("POLICY_ADMIN", "UM_LEADER"))],
    db: Session = Depends(get_db),
):
    """Get status of a daily job"""
    job = db.query(Job).filter(
        Job.job_id == job_id,
        Job.tenant_id == current_user.tenant_id,
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.job_id,
        "status": job.status,
        "message": job.message,
        "error_message": job.error_message,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "metadata": job.metadata_json,
    }
