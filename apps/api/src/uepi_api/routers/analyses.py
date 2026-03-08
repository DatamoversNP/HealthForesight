"""Analysis endpoints"""
from typing import Annotated
from uuid import UUID
import os
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from uepi_api.auth import CurrentUser, verify_token, get_demo_current_user
from uepi_api.database import get_db
from uepi_api.models.analysis import Analysis, AnalysisStatus, AnalysisType
from datetime import datetime, date, timedelta
from uepi_common.models import FilterSpec

router = APIRouter()


class ImpactAnalysisCreate(BaseModel):
    """Impact analysis creation model"""
    policy_id: UUID | str  # Accept both UUID and string IDs
    treatment_filters: dict  # FilterSpec
    control_filters: dict | None = None  # FilterSpec (optional)
    matching_strategy: str | None = None
    pre_window_months: int = 6
    post_window_months: int = 6
    run_substitution: bool = False
    run_provider_segmentation: bool = False
    run_substitution: bool = False
    run_provider_segmentation: bool = False


class SimulateAnalysisCreate(BaseModel):
    """Simulation analysis creation model"""
    policy_id: UUID | str  # Accept both UUID and string IDs
    scenario_params: dict
    filters: dict  # FilterSpec


class ElasticityAnalysisCreate(BaseModel):
    """Elasticity analysis creation model"""
    policy_id: UUID | str  # Accept both UUID and string IDs
    service_categories: list[str] | None = None  # Optional list of service categories to model


class BaselineAnalysisCreate(BaseModel):
    """Baseline analysis creation model"""
    name: str  # Required unique name for the analysis
    start_date: str | None = None  # ISO date string, optional
    end_date: str | None = None  # ISO date string, optional
    group_by: list[str] | None = None  # e.g., ["lob", "market"]
    n_clusters: int = 5  # Number of provider archetypes
    baseline_type: str = "GENERAL"  # "GENERAL" or "POLICY_SPECIFIC"
    policy_id: UUID | str | None = None  # Required if baseline_type is "POLICY_SPECIFIC"
    
    @classmethod
    def validate_n_clusters(cls, v):
        """Ensure n_clusters is an integer, converting from float if needed"""
        if v is None:
            return 5
        # Convert to int (handles float inputs like 5.0 -> 5)
        return int(float(v))  # Convert to float first to handle strings, then to int


@router.get("/analyses")
async def list_analyses(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    analysis_type: str | None = Query(None),
):
    """List all analyses for the current tenant (capped for performance)."""
    try:
        query = db.query(Analysis).filter(Analysis.tenant_id == current_user.tenant_id)

        if analysis_type:
            query = query.filter(Analysis.analysis_type == analysis_type)

        analyses = query.order_by(Analysis.created_at.desc()).offset(skip).limit(limit).all()
        
        return [
            {
                "id": str(a.id),
                "name": a.name,
                "policy_id": str(a.policy_id) if a.policy_id else None,
                "analysis_type": a.analysis_type,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "updated_at": a.updated_at.isoformat() if a.updated_at else None,
            }
            for a in analyses
        ]
    except Exception as e:
        # Handle database/model initialization errors gracefully
        import traceback
        print(f"Database query failed in list_analyses: {e}")
        traceback.print_exc()
        return []


@router.post("/analyses/impact", status_code=201)
async def create_impact_analysis(
    analysis_data: ImpactAnalysisCreate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Create a new impact analysis - Database-only"""
        
        # Database version (existing code)
    try:
        # Verify policy exists and belongs to tenant
        from uepi_api.models.policy import Policy, PolicyVersion
        
        policy = db.query(Policy).filter(
            Policy.id == analysis_data.policy_id,
            Policy.tenant_id == current_user.tenant_id,
        ).first()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Get policy version for effective date
        version = db.query(PolicyVersion).filter(
            PolicyVersion.policy_id == analysis_data.policy_id,
            PolicyVersion.tenant_id == current_user.tenant_id,
        ).order_by(PolicyVersion.version_number.desc()).first()
        
        if not version:
            raise HTTPException(status_code=404, detail="Policy version not found. Please ensure the policy has at least one version.")
        
        analysis = Analysis(
            tenant_id=current_user.tenant_id,
            policy_id=analysis_data.policy_id,
            analysis_type=AnalysisType.IMPACT.value,
            status=AnalysisStatus.PENDING.value,
            created_by=current_user.user_id,
        )
        db.add(analysis)
        db.flush()
        
        # Create analysis config
        from uepi_api.models.analysis import AnalysisConfig
        
        config = AnalysisConfig(
            tenant_id=current_user.tenant_id,
            analysis_id=analysis.id,
            treatment_filters=analysis_data.treatment_filters,
            control_filters=analysis_data.control_filters,
            matching_strategy=analysis_data.matching_strategy,
            pre_window_months=analysis_data.pre_window_months,
            post_window_months=analysis_data.post_window_months,
        )
        db.add(config)
        db.commit()
        db.refresh(analysis)
        
        # Trigger worker jobs (send by name so API does not need uepi_worker on PYTHONPATH)
        try:
            from uepi_api.celery_client import send_task
            
            # Main impact analysis
            send_task(
                "uepi_worker.tasks.policy_impact_job",
                args=[
                    str(current_user.tenant_id),
                    str(analysis_data.policy_id),
                    str(analysis.id),
                    {
                        "treatment_filters": analysis_data.treatment_filters,
                        "control_filters": analysis_data.control_filters,
                        "matching_strategy": analysis_data.matching_strategy,
                        "pre_window_months": analysis_data.pre_window_months,
                        "post_window_months": analysis_data.post_window_months,
                    },
                ],
            )
            
            # Optional: substitution detection
            if analysis_data.run_substitution:
                send_task(
                    "uepi_worker.tasks.substitution_job",
                    args=[
                        str(current_user.tenant_id),
                        str(analysis.id),
                        str(analysis_data.policy_id),
                        version.effective_start_date.isoformat(),
                        analysis_data.treatment_filters,
                        analysis_data.pre_window_months,
                        analysis_data.post_window_months,
                    ],
                )
            
            # Optional: provider segmentation
            if analysis_data.run_provider_segmentation:
                send_task(
                    "uepi_worker.tasks.provider_segmentation_job",
                    args=[
                        str(current_user.tenant_id),
                        str(analysis.id),
                        str(analysis_data.policy_id),
                        version.effective_start_date.isoformat(),
                        analysis_data.treatment_filters,
                        analysis_data.pre_window_months,
                        analysis_data.post_window_months,
                    ],
                )
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to trigger analysis jobs: {e}")
            import traceback
            traceback.print_exc()
        
        return {
            "id": str(analysis.id),
            "policy_id": str(analysis.policy_id) if analysis.policy_id else None,
            "status": analysis.status,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create impact analysis: {str(e)}")


@router.post("/analyses/simulate", status_code=201)
async def create_simulate_analysis(
    analysis_data: SimulateAnalysisCreate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Create a what-if scenario simulation analysis.
    Uses consistent policy filters (scope + levers merged) for baseline claims loading."""
    from uepi_api.models.policy import Policy
    from uepi_api.services.policy_scoped_data_generation import build_policy_claims_filters

    policy = db.query(Policy).filter(
        Policy.id == analysis_data.policy_id,
        Policy.tenant_id == current_user.tenant_id,
    ).first()

    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    # Build consistent policy filters (scope + levers merged) for what-if baseline
    meta = getattr(policy, "policy_metadata_json", None) or {}
    policy_dict = {
        "scope": meta.get("scope", {}),
        "policy_levers": meta.get("policy_levers", []),
        "logic": meta.get("logic", {}),
        "policy_logic": meta.get("policy_logic", {}),
    }
    baseline_filters = build_policy_claims_filters(policy_dict)
    # Convert to format worker expects: lob, markets, cpt_codes, diagnosis_codes (same scope as baseline/predicted impact)
    worker_filters = {
        "lob": baseline_filters.get("lob"),
        "markets": baseline_filters.get("markets") or ([baseline_filters["market"]] if baseline_filters.get("market") else None),
        "market": baseline_filters.get("market"),
        "cpt_codes": baseline_filters.get("cpt_codes") or baseline_filters.get("procedure_codes"),
        "service_categories": baseline_filters.get("service_categories"),
        "diagnosis_codes": baseline_filters.get("diagnosis_codes"),
    }
    worker_filters = {k: v for k, v in worker_filters.items() if v is not None}

    analysis = Analysis(
        tenant_id=current_user.tenant_id,
        policy_id=analysis_data.policy_id,
        analysis_type=AnalysisType.SIMULATE.value,
        status=AnalysisStatus.PENDING.value,
        created_by=current_user.user_id,
    )
    db.add(analysis)
    db.flush()

    # Create analysis config for simulation
    from uepi_api.models.analysis import AnalysisConfig

    config = AnalysisConfig(
        tenant_id=current_user.tenant_id,
        analysis_id=analysis.id,
        treatment_filters=worker_filters or analysis_data.filters,
        control_filters=None,
        matching_strategy=None,
        pre_window_months=0,
        post_window_months=0,
    )
    db.add(config)
    db.commit()
    db.refresh(analysis)

    # Trigger what-if scenario job - use consistent policy filters
    try:
        from uepi_api.celery_client import send_task
        send_task(
            "uepi_worker.tasks.whatif_scenario_job",
            args=[
                str(current_user.tenant_id),
                str(analysis.id),
                str(analysis_data.policy_id),
                analysis_data.scenario_params,
                worker_filters or analysis_data.filters,
            ],
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to trigger what-if scenario job: {e}")
    
    return {
        "id": analysis.id,
        "policy_id": analysis.policy_id,
        "status": analysis.status,
        "created_at": analysis.created_at.isoformat(),
    }


@router.get("/analyses/{analysis_id}")
async def get_analysis(
    analysis_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Get analysis by ID"""
        
        # Database version
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id,
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    out = {
        "id": analysis.id,
        "policy_id": analysis.policy_id,
        "analysis_type": analysis.analysis_type,
        "status": analysis.status,
        "created_at": analysis.created_at.isoformat(),
        "updated_at": analysis.updated_at.isoformat(),
    }
    if getattr(analysis, "error_message", None):
        out["error_message"] = analysis.error_message
    return out


@router.get("/analyses/{analysis_id}/results")
async def get_analysis_results(
    analysis_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
    result_type: str | None = Query(None),
):
    """Get analysis results"""
        
        # Database version
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id,
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Get results from database (primary) or object storage (fallback)
    from uepi_api.models.analysis import (
        AnalysisResultIndex,
        BaselineAnalysisResult,
        ImpactAnalysisResult,
        WhatIfScenarioResult,
        ElasticityAnalysisResult,
    )
    from uepi_api.config import get_settings
    try:
        import boto3
    except (ImportError, PermissionError, OSError):
        boto3 = None  # Optional - only needed for S3 storage
    import json
    
    results = {}
    
    # Check for database-stored results first
    # 1. Baseline results
    if not result_type or result_type == "BASELINE_SUMMARY":
        baseline_result = db.query(BaselineAnalysisResult).filter(
            BaselineAnalysisResult.analysis_id == analysis_id,
            BaselineAnalysisResult.tenant_id == current_user.tenant_id,
        ).first()
        if baseline_result:
            results["BASELINE_SUMMARY"] = baseline_result.result_data_json
    
    # 2. Impact results
    if not result_type or result_type == "SUMMARY":
        impact_result = db.query(ImpactAnalysisResult).filter(
            ImpactAnalysisResult.analysis_id == analysis_id,
            ImpactAnalysisResult.tenant_id == current_user.tenant_id,
        ).first()
        if impact_result:
            results["SUMMARY"] = impact_result.result_data_json
    
    # 3. What-if scenario results
    if not result_type or result_type in ["WHATIF_SCENARIO", "whatif_scenario"]:
        whatif_result = db.query(WhatIfScenarioResult).filter(
            WhatIfScenarioResult.analysis_id == analysis_id,
            WhatIfScenarioResult.tenant_id == current_user.tenant_id,
        ).first()
        if whatif_result:
            results["whatif_scenario"] = whatif_result.result_data_json
            results["WHATIF_SCENARIO"] = whatif_result.result_data_json

    # 4. Elasticity results
    if not result_type or result_type == "ELASTICITY":
        elasticity_result = db.query(ElasticityAnalysisResult).filter(
            ElasticityAnalysisResult.analysis_id == analysis_id,
            ElasticityAnalysisResult.tenant_id == current_user.tenant_id,
        ).first()
        if elasticity_result:
            results["ELASTICITY"] = elasticity_result.result_data_json
    
    # If no database results found, check result index for object storage (backward compatibility)
    if not results:
        query = db.query(AnalysisResultIndex).filter(
            AnalysisResultIndex.analysis_id == analysis_id,
            AnalysisResultIndex.tenant_id == current_user.tenant_id,
        )
        
        if result_type:
            query = query.filter(AnalysisResultIndex.result_type == result_type)
        
        result_indices = query.all()
        
        if result_indices and boto3:
            # Load results from object storage (fallback for old data)
            settings = get_settings()
            s3_client = boto3.client(
                "s3",
                endpoint_url=settings.object_storage.endpoint,
                aws_access_key_id=settings.object_storage.access_key,
                aws_secret_access_key=settings.object_storage.secret_key,
                region_name=settings.object_storage.region,
                use_ssl=settings.object_storage.use_ssl,
            )
            
            for result_index in result_indices:
                # Skip if data_uri is None (indicates database storage)
                if not result_index.data_uri:
                    continue
                
                # Parse S3 URI: "s3://bucket/key" or "bucket/key"
                uri = result_index.data_uri.strip()
                if uri.startswith("s3://"):
                    parts = uri.replace("s3://", "", 1).split("/", 1)
                    bucket = parts[0]
                    key = parts[1] if len(parts) > 1 else ""
                elif "/" in uri:
                    bucket, key = uri.split("/", 1)
                else:
                    continue
                
                try:
                    # Download and parse JSON
                    import tempfile
                    import os
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
                        s3_client.download_fileobj(bucket, key, tmp)
                        tmp_path = tmp.name
                    
                    try:
                        with open(tmp_path, 'r') as f:
                            results[result_index.result_type] = json.load(f)
                    finally:
                        os.unlink(tmp_path)
                except Exception as e:
                    results[result_index.result_type] = {"error": f"Failed to load: {str(e)}"}
    
    if not results:
        out = {
            "analysis_id": str(analysis_id),
            "status": analysis.status,
            "results": None,
        }
        if getattr(analysis, "error_message", None):
            out["error_message"] = analysis.error_message
        return out
    
    out = {
        "analysis_id": str(analysis_id),
        "status": analysis.status,
        "results": results,
    }
    if getattr(analysis, "error_message", None):
        out["error_message"] = analysis.error_message
    return out


@router.get("/analyses/{analysis_id}/method-checks")
async def get_method_checks(
    analysis_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Get method checks for analysis (Phase 5: Method Checks)
    
    Returns:
    - Pre-trends check (parallel trends assumption)
    - Control balance check (covariate balance)
    - Seasonality check (seasonal patterns)
    - Sample size adequacy
    """
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id,
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Load from results
    results_response = await get_analysis_results(analysis_id, current_user, db, result_type="SUMMARY")
    
    if not results_response.get("results"):
        return {
            "analysis_id": str(analysis_id),
            "method_checks": {
                "pre_trends": {"parallel_trends": "UNKNOWN"},
                "sample_size_ok": False,
                "warnings": ["Analysis results not yet available"],
            },
        }
    
    results = results_response["results"]
    
    # Extract method checks from new structure
    method_checks = results.get("method_checks", {})
    
    # If using old structure, convert it
    if not method_checks and "data_sufficiency_checks" in results:
        # Legacy format - convert to new format
        old_checks = results["data_sufficiency_checks"]
        method_checks = {
            "pre_trends": {
                "parallel_trends": old_checks.get("parallel_trends", "WARN"),
                "warning": old_checks.get("parallel_trends_warning"),
            },
            "sample_size_ok": old_checks.get("sample_size_ok", False),
            "min_sample_size": old_checks.get("min_sample_size", 1000),
            "actual_sample_size": old_checks.get("actual_sample_size", 0),
            "warnings": old_checks.get("warnings", []),
        }
    
    return {
        "analysis_id": str(analysis_id),
        "method_checks": method_checks,
    }


@router.get("/analyses/{analysis_id}/trust-panel")
async def get_analysis_trust_panel(
    analysis_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Get trust panel for analysis (Phase 5: Trust Panel)
    
    Returns:
    - Confidence score (overall + components)
    - Data sufficiency assessment
    - Validation checks (pre-trends, control balance, seasonality, sample size, significance)
    - Methodology information
    - Limitations and caveats
    - Data used (window, filters, etc.)
    """
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id,
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Load from results
    results_response = await get_analysis_results(analysis_id, current_user, db, result_type="SUMMARY")
    
    if not results_response.get("results"):
        return {
            "analysis_id": str(analysis_id),
            "trust_panel": {
                "confidence_score": {
                    "overall_score": 0.0,
                    "category": "UNKNOWN",
                    "components": {},
                },
                "data_sufficiency": {
                    "sufficient": False,
                    "warnings": ["Analysis results not yet available"],
                },
                "validation_checks": [],
                "methodology": {},
                "limitations": ["Analysis in progress"],
            },
        }
    
    results = results_response["results"]
    
    # Extract trust panel from new structure
    trust_panel = results.get("trust_panel", {})
    
    # If using old structure, build trust panel from available data
    if not trust_panel:
        # Legacy format - build trust panel from available data
        impact_result = results.get("impact_estimate", results.get("impact_result", {}))
        method_checks = results.get("method_checks", results.get("data_sufficiency_checks", {}))
        confidence_score = results.get("confidence_score", results.get("summary", {}).get("confidence_score", 70.0))
        
        trust_panel = {
            "confidence_score": {
                "overall_score": confidence_score,
                "category": "HIGH" if confidence_score >= 80 else "MEDIUM" if confidence_score >= 60 else "LOW",
                "components": {
                    "method_confidence": 90.0 if impact_result.get("method") == "difference_in_differences" else 70.0,
                    "data_quality_score": 85.0,
                    "sample_size_score": min(100.0, (method_checks.get("actual_sample_size", 0) / 1000) * 100),
                    "control_group_score": 90.0 if method_checks.get("has_control_group") else 0.0,
                    "methodology_score": 85.0,
                },
            },
            "data_sufficiency": {
                "sufficient": method_checks.get("sample_size_ok", False),
                "min_sample_size": method_checks.get("min_sample_size", 1000),
                "actual_sample_size": method_checks.get("actual_sample_size", 0),
                "data_window_months": results.get("methodology", {}).get("pre_months", 6) + results.get("methodology", {}).get("post_months", 6),
                "coverage_score": 0.8,
                "missing_data_flags": [],
            },
            "validation_checks": [
                {
                    "check_name": "Parallel Trends",
                    "passed": method_checks.get("pre_trends", {}).get("parallel_trends") == "PASS",
                    "message": method_checks.get("pre_trends", {}).get("warning"),
                    "severity": "WARNING" if method_checks.get("pre_trends", {}).get("parallel_trends") == "WARN" else "ERROR" if method_checks.get("pre_trends", {}).get("parallel_trends") == "FAIL" else "INFO",
                },
                {
                    "check_name": "Sample Size",
                    "passed": method_checks.get("sample_size_ok", False),
                    "message": f"Sample size: {method_checks.get('actual_sample_size', 0)} (minimum: {method_checks.get('min_sample_size', 1000)})",
                    "severity": "WARNING" if not method_checks.get("sample_size_ok", False) else "INFO",
                },
            ],
            "methodology": results.get("methodology", {}),
            "limitations": results.get("limitations", method_checks.get("warnings", [])),
            "data_used": {},
            "model_version": "1.0.0",
        }
    
    return {
        "analysis_id": str(analysis_id),
        "trust_panel": trust_panel,
    }


@router.get("/analyses/{analysis_id}/timeseries")
async def get_timeseries(
    analysis_id: UUID,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Get time series data for analysis"""
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id,
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Load from results if available
    results_response = await get_analysis_results(analysis_id, current_user, db, result_type="SUMMARY")
    if results_response.get("results") and "SUMMARY" in results_response["results"]:
        summary = results_response["results"]["SUMMARY"]
        timeseries = summary.get("timeseries", [])
        return {
            "analysis_id": str(analysis_id),
            "data": timeseries,
        }
    
    # Item 6: Load timeseries from object storage
        # Database mode - placeholder
    return {
        "analysis_id": str(analysis_id),
        "data": [],
    }


@router.post("/analyses/elasticity", status_code=201)
async def create_elasticity_analysis(
    analysis_data: ElasticityAnalysisCreate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Create elasticity modeling analysis - Database-only"""
        
        # Database version (original code)
    from uepi_api.models.policy import Policy, PolicyVersion
    
    policy = db.query(Policy).filter(
        Policy.id == analysis_data.policy_id,
        Policy.tenant_id == current_user.tenant_id,
    ).first()
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    analysis = Analysis(
        tenant_id=current_user.tenant_id,
        policy_id=analysis_data.policy_id,
        analysis_type=AnalysisType.ELASTICITY.value,
        status=AnalysisStatus.PENDING.value,
        created_by=current_user.user_id,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    # Trigger elasticity job (send by name so API does not need uepi_worker on PYTHONPATH)
    try:
        from uepi_api.celery_client import send_task
        send_task(
            "uepi_worker.tasks.elasticity_job",
            args=[
                str(current_user.tenant_id),
                str(analysis.id),
                str(analysis_data.policy_id),
                analysis_data.service_categories if hasattr(analysis_data, 'service_categories') else None,
            ],
        )
    except Exception as e:
        print(f"Failed to trigger elasticity job: {e}")
    
    return {
        "id": analysis.id,
        "policy_id": analysis.policy_id,
        "status": analysis.status,
        "created_at": analysis.created_at.isoformat(),
    }


@router.get("/analyses/suggest-controls")
async def suggest_control_groups(
    policy_id: UUID,
    treatment_filters: dict,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Suggest control groups for DiD analysis"""
    # Item 7: Implement control group suggestion logic
        
    suggested_controls = []
    
    return {
        "suggested_controls": suggested_controls,
        "count": len(suggested_controls),
    }


@router.post("/analyses/baseline", status_code=201)
async def create_baseline_analysis(
    analysis_data: BaselineAnalysisCreate,
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Create baseline utilization and behavior profiling analysis (Stage 3)"""
    from datetime import date
    from pathlib import Path
        
    # Check for required dependencies BEFORE importing BaselineAnalysisEngine
    missing_deps = []
    try:
        import scipy
    except ImportError as e:
        missing_deps.append(f"scipy ({str(e)})")
    
    try:
        import sklearn
    except ImportError as e:
        missing_deps.append(f"scikit-learn ({str(e)})")
    
    try:
        import statsmodels
    except ImportError as e:
        missing_deps.append(f"statsmodels ({str(e)})")
    
    # Try to import BaselineAnalysisEngine - this might also fail if dependencies are missing
    try:
        from uepi_common.analytics.baseline import BaselineAnalysisEngine
    except ImportError as e:
        # If import fails, add to missing deps or provide clear error
        import_error_msg = str(e)
        if "cannot import name" in import_error_msg.lower() or "No module named" in import_error_msg:
            missing_deps.append(f"baseline module dependency issue: {import_error_msg}")
        else:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to import BaselineAnalysisEngine: {import_error_msg}"
            )
    
    if missing_deps:
        raise HTTPException(
            status_code=503,
            detail=f"Missing required dependencies: {', '.join(missing_deps)}. Please install them: pip install scipy scikit-learn statsmodels"
        )
    
    # Database mode
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database session is not available. Please ensure the database is configured and running."
        )
    
    try:
        # Check if name already exists for this tenant and analysis type
        existing = db.query(Analysis).filter(
            Analysis.tenant_id == current_user.tenant_id,
            Analysis.analysis_type == "BASELINE",
            Analysis.name == analysis_data.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Analysis with name '{analysis_data.name}' already exists. Please choose a unique name."
            )
        
        # Extract baseline_type and policy_id from analysis_data
        baseline_type = getattr(analysis_data, 'baseline_type', 'GENERAL')
        policy_id = getattr(analysis_data, 'policy_id', None)
        
        # Validate policy_id is provided for POLICY_SPECIFIC baselines
        if baseline_type == "POLICY_SPECIFIC" and not policy_id:
            raise HTTPException(
                status_code=400,
                detail="policy_id is required when baseline_type is POLICY_SPECIFIC"
            )
        
        # Determine policy_id based on baseline_type
        analysis_policy_id = None
        policy_scope = None
        if baseline_type == "POLICY_SPECIFIC" and policy_id:
            # Convert policy_id to UUID if it's a string
            from uuid import UUID
            try:
                analysis_policy_id = UUID(str(policy_id)) if policy_id else None
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid policy_id format: {policy_id}"
                )
            
            # Fetch policy to get its scope
            from uepi_api.storage_policies import get_policy
            policy = get_policy(analysis_policy_id, current_user.tenant_id)
            if policy:
                policy_scope = policy.get("scope", {})
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Policy with ID {analysis_policy_id} not found"
                )
        
        analysis = Analysis(
            tenant_id=current_user.tenant_id,
            policy_id=analysis_policy_id,  # Set policy_id for policy-specific baselines
            analysis_type="BASELINE",
            name=analysis_data.name,
            status=AnalysisStatus.PENDING.value,
            created_by=current_user.user_id,
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        analysis_id = analysis.id
    except Exception as db_error:
        db.rollback()
        import traceback
        error_trace = traceback.format_exc()
        print(f"Database error in create_baseline_analysis: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create analysis record: {str(db_error)}"
        )
    
    try:
        # Load data from database instead of files
        from uepi_api.repositories.canonical_data import CanonicalDataRepository
        
        repository = CanonicalDataRepository(db)
        
        # Parse dates
        start_date = None
        end_date = None
        if analysis_data.start_date:
            try:
                start_date = date.fromisoformat(analysis_data.start_date)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid start_date format: {analysis_data.start_date}")
        if analysis_data.end_date:
            try:
                end_date = date.fromisoformat(analysis_data.end_date)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid end_date format: {analysis_data.end_date}")
        
        # Load claims data from database
        print(f"Loading claims data from database for tenant {current_user.tenant_id}")
        claims_df = repository.get_claims_lines(
            tenant_id=current_user.tenant_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        if claims_df is None or len(claims_df) == 0:
            raise HTTPException(
                status_code=400,
                detail=f"No claims data found in database for tenant {current_user.tenant_id}. Please run pipelines to load data first."
            )
        
        print(f"Loaded {len(claims_df):,} claims records from database")
        
        # Infer start_date/end_date from claims if not provided (required for baseline window_start_date/window_end_date)
        if (start_date is None or end_date is None) and len(claims_df) > 0:
            try:
                import pandas as pd
                date_col = "service_date" if "service_date" in claims_df.columns else None
                if date_col:
                    ser = pd.to_datetime(claims_df[date_col], errors="coerce").dropna()
                    if len(ser) > 0:
                        if start_date is None:
                            start_date = ser.min().date() if hasattr(ser.min(), "date") else date.fromisoformat(str(ser.min())[:10])
                        if end_date is None:
                            end_date = ser.max().date() if hasattr(ser.max(), "date") else date.fromisoformat(str(ser.max())[:10])
            except Exception as e:
                print(f"Warning: Could not infer dates from claims: {e}")
            if start_date is None:
                start_date = date.today() - timedelta(days=365)
            if end_date is None:
                end_date = date.today()
        
        # Load enrollment data from database
        enrollment_df = None
        try:
            enrollment_df = repository.get_enrollment_records(
                tenant_id=current_user.tenant_id,
                start_month=start_date,
                end_month=end_date,
            )
            if enrollment_df is not None and len(enrollment_df) > 0:
                print(f"Loaded {len(enrollment_df):,} enrollment records from database")
        except Exception as e:
            print(f"Warning: Could not load enrollment data: {e}")
        
        # Load provider data from database
        provider_df = None
        try:
            provider_df = repository.get_provider_records(
                tenant_id=current_user.tenant_id,
            )
            if provider_df is not None and len(provider_df) > 0:
                print(f"Loaded {len(provider_df):,} provider records from database")
                # Ensure system_affiliation column exists (fill with None if missing)
                if 'system_affiliation' not in provider_df.columns:
                    provider_df['system_affiliation'] = None
                    print("Warning: system_affiliation column not found in provider data, adding as None")
        except Exception as e:
            print(f"Warning: Could not load provider data: {e}")
        
        # Save DataFrames to temporary files for BaselineAnalysisEngine (it expects file paths)
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            claims_path = os.path.join(tmpdir, "claims.csv")
            claims_df.to_csv(claims_path, index=False)
            
            enrollment_path = None
            if enrollment_df is not None and len(enrollment_df) > 0:
                enrollment_path = os.path.join(tmpdir, "enrollment.csv")
                enrollment_df.to_csv(enrollment_path, index=False)
            
            provider_path = None
            if provider_df is not None and len(provider_df) > 0:
                provider_path = os.path.join(tmpdir, "providers.csv")
                provider_df.to_csv(provider_path, index=False)
            
            # Run baseline analysis
            try:
                print(f"Starting baseline analysis with {len(claims_df):,} claims from database")
                # Get n_clusters from request, default to 5
                n_clusters = 5
                if hasattr(analysis_data, 'n_clusters') and analysis_data.n_clusters is not None:
                    try:
                        raw_value = analysis_data.n_clusters
                        print(f"Raw n_clusters value: {raw_value}, type: {type(raw_value)}")
                        n_clusters = int(float(raw_value))
                        if n_clusters < 1:
                            n_clusters = 5
                    except (ValueError, TypeError) as e:
                        print(f"Error converting n_clusters to int: {e}")
                        n_clusters = 5
                n_clusters = int(n_clusters)
                print(f"Using n_clusters: {n_clusters}")
                
                engine = BaselineAnalysisEngine(n_clusters=n_clusters)
                result = engine.run_baseline_analysis(
                    tenant_id=current_user.tenant_id,
                    claims_data_path=claims_path,
                    enrollment_data_path=enrollment_path,
                    provider_data_path=provider_path,
                    member_data_path=None,  # Not available in database yet
                    network_data_path=None,  # Not available in database yet
                    market_events_path=None,  # Not available in database yet
                    start_date=start_date,
                    end_date=end_date,
                )
                print(f"Baseline analysis completed successfully. Result keys: {list(result.model_dump().keys()) if hasattr(result, 'model_dump') else 'N/A'}")
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as engine_error:
                import traceback
                engine_trace = traceback.format_exc()
                print(f"BaselineAnalysisEngine error: {engine_trace}")
                print(f"Engine error type: {type(engine_error).__name__}")
                print(f"Engine error message: {str(engine_error)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to run baseline analysis engine: {str(engine_error)} (Type: {type(engine_error).__name__})"
                )
        
        # Convert result to dict for JSON response
        def convert_to_dict(obj):
            """Convert Pydantic models and datetimes to dict"""
            if hasattr(obj, 'model_dump'):
                return obj.model_dump(mode='json')
            elif hasattr(obj, 'dict'):
                return obj.dict()
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, date):
                return obj.isoformat()
            elif isinstance(obj, (list, tuple)):
                return [convert_to_dict(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_to_dict(v) for k, v in obj.items()}
            return obj
        
        result_dict = convert_to_dict(result)
        
        # Generate data-driven narratives for provider archetypes
        try:
            from uepi_api.narrative_generator import BaselineNarrativeGenerator
            narrative_gen = BaselineNarrativeGenerator()
            
            # Generate archetype narratives
            provider_archetypes = result_dict.get("provider_archetypes", [])
            if provider_archetypes:
                archetype_narratives = narrative_gen.generate_archetype_narratives(provider_archetypes)
                result_dict["archetype_narratives"] = archetype_narratives
                print(f"Generated narratives for {len(archetype_narratives)} provider archetypes")
            
            # Generate baseline summary
            baseline_summary = narrative_gen.generate_baseline_summary(
                benchmarks=result_dict.get("benchmarks", []),
                provider_archetypes=provider_archetypes,
                patient_segments=result_dict.get("patient_segments", []),
                time_series=result_dict.get("time_series", []),
            )
            result_dict["baseline_summary_narrative"] = baseline_summary
            print("Generated baseline summary narrative")
        except Exception as narrative_error:
            print(f"Warning: Failed to generate narratives: {narrative_error}")
            import traceback
            traceback.print_exc()
            # Continue without narratives - not critical
        
        # Store results directly in database (primary storage)
        # Downsample time_series so the JSON fits and INSERT does not hit statement timeout (~190MB -> ~2MB)
        _MAX_TIME_SERIES_POINTS = 2000
        result_for_db = dict(result_dict)  # shallow copy
        ts = result_for_db.get("time_series") or []
        if len(ts) > _MAX_TIME_SERIES_POINTS:
            step = max(1, len(ts) // _MAX_TIME_SERIES_POINTS)
            result_for_db["time_series"] = [ts[i] for i in range(0, len(ts), step)][:_MAX_TIME_SERIES_POINTS]
            print(f"Downsampled time_series for DB storage: {len(ts)} -> {len(result_for_db['time_series'])} points")
        from uepi_api.models.analysis import BaselineAnalysisResult, AnalysisResultIndex
        try:
            # Optional: allow longer INSERT for large JSONB (if DB has statement_timeout)
            try:
                db.execute(text("SET LOCAL statement_timeout = '600000'"))  # 10 min for large JSONB insert
            except Exception:
                pass
            # Check if result already exists (shouldn't, but handle gracefully)
            existing_result = db.query(BaselineAnalysisResult).filter(
                BaselineAnalysisResult.analysis_id == analysis_id
            ).first()
            
            if existing_result:
                # Update existing result
                existing_result.result_data_json = result_for_db
                existing_result.updated_at = datetime.utcnow()
                print(f"Updated existing baseline result in database for analysis {analysis_id}")
            else:
                # Create new result
                baseline_result = BaselineAnalysisResult(
                    tenant_id=current_user.tenant_id,
                    analysis_id=analysis_id,
                    result_data_json=result_for_db,
                    schema_version="1.0",
                )
                db.add(baseline_result)
                print(f"Stored baseline result in database for analysis {analysis_id}")
            
            # Also create/update result index for backward compatibility (optional, can point to DB)
            # Check if index already exists
            existing_index = db.query(AnalysisResultIndex).filter(
                AnalysisResultIndex.analysis_id == analysis_id,
                AnalysisResultIndex.result_type == "BASELINE_SUMMARY"
            ).first()
            
            if not existing_index:
                result_index = AnalysisResultIndex(
                    tenant_id=current_user.tenant_id,
                    analysis_id=analysis_id,
                    result_type="BASELINE_SUMMARY",
                    data_uri=None,  # NULL indicates stored in database
                    schema_version="1.0",
                )
                db.add(result_index)
                print(f"Created result index entry (database storage)")
            
            # Commit both baseline result and index together in one transaction
            db.commit()
            print(f"✅ Successfully stored baseline analysis results in database")
        except Exception as db_error:
            # Rollback on any error
            try:
                db.rollback()
            except:
                pass
            print(f"❌ Failed to store baseline result in database: {db_error}")
            import traceback
            traceback.print_exc()
            # Continue - results are still in response, just not persisted
        
        # Extract comprehensive baseline metrics using metric dictionary and policy scoping
        from uepi_api.baseline_metrics_computation import compute_baseline_metrics_from_analysis_result
        
        # Check if policy-scoped baseline is requested
        policy_id = analysis_data.policy_id if hasattr(analysis_data, 'policy_id') and analysis_data.policy_id else None
        policy = None
        if policy_id:
            from uepi_api.storage_policies import get_policy
            policy = get_policy(policy_id, current_user.tenant_id)
        
        baseline_metrics = compute_baseline_metrics_from_analysis_result(
            result_dict=result_dict,
            tenant_id=current_user.tenant_id,
            policy_id=policy_id,
            policy=policy,
            start_date=start_date,
            end_date=end_date,
        )
        
        print(f"DEBUG: Computed baseline metrics (using metric dictionary): {list(baseline_metrics.keys())}")
        
        # Create baseline record if we have metrics
        if baseline_metrics:
            try:
                from uepi_api.storage_baselines import create_baseline
                
                # Determine date range from analysis (required by baselines table NOT NULL)
                window_start = start_date.isoformat() if start_date else (date.today() - timedelta(days=365)).isoformat()
                window_end = end_date.isoformat() if end_date else date.today().isoformat()
                
                baseline_record = create_baseline(
                    tenant_id=current_user.tenant_id,
                    baseline_data={
                        "baseline_type": "ROLLING",
                        "window_start_date": window_start,
                        "window_end_date": window_end,
                        "baseline_metrics": baseline_metrics,
                        "computed_at": datetime.utcnow().isoformat(),
                        "computed_by": "baseline_analysis",
                        "metadata": {
                            "analysis_id": str(analysis_id),
                            "source": "baseline_analysis",
                            "benchmarks_count": len(result_dict.get("benchmarks", [])),
                            "time_series_points": len(result_dict.get("time_series", [])),
                        },
                    }
                )
                print(f"DEBUG: Created baseline record: {baseline_record.get('baseline_id')}")
            except Exception as baseline_error:
                print(f"WARNING: Failed to create baseline record: {baseline_error}")
                import traceback
                traceback.print_exc()
        
        # Update analysis status to COMPLETED
        # Ensure session is in a good state before committing
        try:
            # Refresh analysis to ensure it's in the session
            db.refresh(analysis)
            analysis.status = AnalysisStatus.COMPLETED.value
            db.commit()
        except Exception as status_error:
            # If commit fails due to rollback, rollback and retry
            try:
                db.rollback()
                # Re-query the analysis
                analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
                if analysis:
                    analysis.status = AnalysisStatus.COMPLETED.value
                    db.commit()
            except Exception as retry_error:
                print(f"Failed to update analysis status: {retry_error}")
                db.rollback()
        
        return {
            "id": str(analysis.id),
            "name": analysis.name,
            "status": analysis.status,
            "created_at": analysis.created_at.isoformat(),
            "result": result_dict,
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Baseline analysis error: {error_trace}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        
        # Update analysis status to FAILED
        if analysis_id and db:
            try:
                # Query analysis again to update status
                analysis_obj = db.query(Analysis).filter(Analysis.id == analysis_id).first()
                if analysis_obj:
                    analysis_obj.status = AnalysisStatus.FAILED.value
                    db.commit()
            except Exception as db_error:
                print(f"Failed to update analysis status: {db_error}")
                if db:
                    db.rollback()
        
        # Provide more detailed error message
        error_detail = str(e)
        error_type = type(e).__name__
        full_error_trace = error_trace if 'error_trace' in locals() else str(e)
        
        # Log full error for debugging
        print(f"FULL ERROR DETAIL: {error_detail}")
        print(f"FULL ERROR TYPE: {error_type}")
        print(f"FULL TRACEBACK: {full_error_trace}")
        
        # Provide helpful error messages for common issues
        if "ModuleNotFoundError" in error_type or "ImportError" in error_type:
            # Extract module name from error if possible
            import_match = None
            if "No module named" in error_detail:
                # Extract module name: "No module named 'X'"
                import re
                match = re.search(r"No module named ['\"]([^'\"]+)['\"]", error_detail)
                if match:
                    import_match = match.group(1)
            elif "cannot import name" in error_detail:
                # Extract from: "cannot import name 'X' from 'Y'"
                import re
                match = re.search(r"cannot import name ['\"]([^'\"]+)['\"]", error_detail)
                if match:
                    import_match = match.group(1)
            
            if import_match:
                # Map common import names to package names
                package_map = {
                    "scipy": "scipy",
                    "sklearn": "scikit-learn",
                    "statsmodels": "statsmodels",
                    "statsmodels.tsa.seasonal": "statsmodels",
                }
                package_name = package_map.get(import_match, import_match)
                error_detail = f"Missing dependency: {package_name} (cannot import '{import_match}'). Please install: pip install {package_name}"
            else:
                error_detail = f"Missing dependency: {error_detail}. Please ensure all required packages are installed: pip install scipy scikit-learn statsmodels"
        elif "FileNotFoundError" in error_type or "No such file" in error_detail:
            error_detail = f"Data file not found: {error_detail}. Please check that data files are in the correct location."
        elif "KeyError" in error_type:
            error_detail = f"Missing required column in data: {error_detail}. Please verify data file format."
        elif "completed_at" in error_detail.lower():
            error_detail = "Database schema error - please check server logs"
        
        raise HTTPException(
            status_code=500, 
            detail=f"Baseline analysis failed: {error_detail}",
            headers={"X-Error-Type": error_type}
        )


class GenerateAllBaselinesResponse(BaseModel):
    """Response for generate-all full baseline analyses"""
    analyses_created: list = []  # [{"id": str, "name": str, "status": str}, ...]
    errors: list = []  # [{"name": str, "detail": str}, ...]


@router.post("/analyses/baseline/generate-all", status_code=200, response_model=GenerateAllBaselinesResponse)
async def generate_all_full_baseline_analyses(
    current_user: Annotated[CurrentUser, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    """Create full baseline analyses (with all 5 tabs: time series, benchmarks, archetypes, segments, confounders) for general + every policy. Same as running 'Run Baseline Analysis' for each scope in one go."""
    from uepi_api.storage_policies import list_policies

    # Reuse same dependency checks as create_baseline_analysis
    missing_deps = []
    try:
        import scipy
    except ImportError:
        missing_deps.append("scipy")
    try:
        import sklearn
    except ImportError:
        missing_deps.append("scikit-learn")
    try:
        import statsmodels
    except ImportError:
        missing_deps.append("statsmodels")
    try:
        from uepi_common.analytics.baseline import BaselineAnalysisEngine
    except ImportError as e:
        missing_deps.append(str(e))
    if missing_deps:
        raise HTTPException(
            status_code=503,
            detail=f"Missing dependencies: {', '.join(missing_deps)}. Install: pip install scipy scikit-learn statsmodels",
        )
    if db is None:
        raise HTTPException(status_code=503, detail="Database session not available.")

    suffix = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    created = []
    errors = []

    # 1) General baseline (full analysis)
    name_general = f"General Baseline {suffix}"
    try:
        payload = BaselineAnalysisCreate(
            name=name_general,
            baseline_type="GENERAL",
            policy_id=None,
            n_clusters=5,
        )
        result = await create_baseline_analysis(payload, current_user, db)
        created.append({"id": result["id"], "name": result["name"], "status": result["status"]})
    except HTTPException as e:
        detail = e.detail
        errors.append({"name": name_general, "detail": detail if isinstance(detail, str) else str(detail)})
    except Exception as e:
        errors.append({"name": name_general, "detail": str(e)})

    # 2) One full baseline analysis per policy
    policies = list_policies(current_user.tenant_id) or []
    for p in policies:
        policy_id = p.get("id") or p.get("policy_id")
        policy_name = (p.get("name") or p.get("policy_name") or str(policy_id))[:50]
        name_policy = f"{policy_name} Baseline {suffix}"
        if not policy_id:
            errors.append({"name": name_policy, "detail": "Policy has no id"})
            continue
        try:
            payload = BaselineAnalysisCreate(
                name=name_policy,
                baseline_type="POLICY_SPECIFIC",
                policy_id=policy_id,
                n_clusters=5,
            )
            result = await create_baseline_analysis(payload, current_user, db)
            created.append({"id": result["id"], "name": result["name"], "status": result["status"]})
        except HTTPException as e:
            detail = e.detail
            errors.append({"name": name_policy, "detail": detail if isinstance(detail, str) else str(detail)})
        except Exception as e:
            errors.append({"name": name_policy, "detail": str(e)})

    return GenerateAllBaselinesResponse(analyses_created=created, errors=errors)


@router.post("/analyses/complete-all-pending", status_code=200)
async def complete_all_pending_analyses(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    db: Session = Depends(get_db),
):
    """Complete all pending impact analyses with mock results - for testing/development"""
    from uepi_api.models.analysis import ImpactAnalysisResult
    
    # Get all pending impact analyses
    pending = db.query(Analysis).filter(
        Analysis.tenant_id == current_user.tenant_id,
        Analysis.analysis_type == "IMPACT",
        Analysis.status == AnalysisStatus.PENDING.value
    ).all()
    
    if not pending:
        return {"message": "No pending analyses found", "completed": 0}
    
    # Create mock result
    mock_result = {
        "impact_summary": {
            "observed_effect_size": -0.15,
            "observed_percent_change": -15.0,
            "confidence_interval_lower": -0.20,
            "confidence_interval_upper": -0.10,
            "p_value": 0.01,
        },
        "pre_period": {"start": "2024-06-01", "end": "2024-11-30", "utilization_per_1k": 125.5, "cost_per_member": 45.2},
        "post_period": {"start": "2024-12-01", "end": "2024-12-31", "utilization_per_1k": 106.7, "cost_per_member": 38.4},
        "method_checks": {"pre_trends_parallel": True, "control_balance": True, "seasonality_risk": "LOW"},
        "trust_panel": {"confidence_score": 0.85, "data_sufficiency": "SUFFICIENT"},
    }
    
    completed = 0
    for analysis in pending:
        # Create result if not exists
        existing = db.query(ImpactAnalysisResult).filter(
            ImpactAnalysisResult.analysis_id == analysis.id
        ).first()
        
        if not existing:
            result = ImpactAnalysisResult(
                tenant_id=current_user.tenant_id,
                analysis_id=analysis.id,
                policy_id=analysis.policy_id,
                result_data_json=mock_result,
                schema_version="1.0",
            )
            db.add(result)
        
        # Update status
        analysis.status = AnalysisStatus.COMPLETED.value
        completed += 1
    
    db.commit()
    
    return {
        "message": f"Completed {completed} analyses",
        "completed": completed,
        "total": len(pending)
    }


@router.get("/analyses/{analysis_id}/baseline")
async def get_baseline_analysis(
    analysis_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    db: Session = Depends(get_db),
):
    """Get baseline analysis results - optimized for fast retrieval (DB only; no file/S3 fallback)."""
    # Get analysis record (simple query)
    analysis = db.query(Analysis).filter(
        Analysis.id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id,
        Analysis.analysis_type == "BASELINE",
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Baseline analysis not found")
    
    analysis_status = analysis.status
    analysis_created_at = analysis.created_at.isoformat()
    
    # Load results from database (primary source) - optimized query
    result_data = None
    from uepi_api.models.analysis import BaselineAnalysisResult
    
    try:
        # Direct query - get the full object for faster retrieval
        baseline_result = db.query(BaselineAnalysisResult).filter(
            BaselineAnalysisResult.analysis_id == analysis_id,
            BaselineAnalysisResult.tenant_id == current_user.tenant_id,
        ).first()
        
        if baseline_result:
            # Results stored in database - result_data_json is already a dict from JSONB
            result_data = baseline_result.result_data_json
            print(f"✅ Loaded baseline results from database for analysis {analysis_id} (size: {len(str(result_data)) if result_data else 0} chars)")
        else:
            # No DB result: return quickly. File/S3 fallback skipped to avoid 10–20s blocking on missing/slow paths.
            print(f"No baseline result in database for analysis {analysis_id}")
    except Exception as e:
        import traceback
        print(f"Error loading baseline results: {e}")
        traceback.print_exc()
        result_data = None
    
    return {
        "id": str(analysis_id),
        "name": analysis.name if analysis and analysis.name else None,
        "status": analysis_status,
        "created_at": analysis_created_at,
        "result": result_data,
    }
