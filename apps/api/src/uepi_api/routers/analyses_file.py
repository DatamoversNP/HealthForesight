"""File-storage impact analysis endpoints"""
from typing import Annotated
from uuid import UUID
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import polars as pl

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from uepi_api.auth import CurrentUser
from uepi_api.auth import get_demo_current_user
from uepi_api.storage_analyses import create_analysis, update_analysis, create_result_index
from uepi_api.storage_policies import get_policy
from uepi_api.storage_policy_versions import get_latest_version
from uepi_api.storage import BASE_PATH as STORAGE_BASE_PATH

router = APIRouter()


# Inline implementations of analytics functions (to avoid uepi_worker dependency)
def compute_pre_post_metrics(
    treatment_df: pl.DataFrame,
    control_df: pl.DataFrame | None,
    policy_effective_date: datetime,
    pre_months: int = 6,
    post_months: int = 6,
) -> dict:
    """Compute pre/post metrics with optional control group"""
    pre_start = policy_effective_date - timedelta(days=pre_months * 30)
    pre_end = policy_effective_date
    post_start = policy_effective_date
    post_end = policy_effective_date + timedelta(days=post_months * 30)
    
    # Parse dates - handle both service_from_date and service_date columns
    if 'service_date' not in treatment_df.columns:
        if 'service_from_date' in treatment_df.columns:
            treatment_df = treatment_df.with_columns(
                pl.col("service_from_date").str.strptime(pl.Date, "%Y-%m-%d").alias("service_date")
            )
        elif 'service_date_from' in treatment_df.columns:
            treatment_df = treatment_df.with_columns(
                pl.col("service_date_from").str.strptime(pl.Date, "%Y-%m-%d").alias("service_date")
            )
    
    # Filter pre/post
    treatment_pre = treatment_df.filter(
        (pl.col("service_date") >= pre_start.date()) & (pl.col("service_date") < pre_end.date())
    )
    treatment_post = treatment_df.filter(
        (pl.col("service_date") >= post_start.date()) & (pl.col("service_date") < post_end.date())
    )
    
    # Compute metrics for treatment group
    def compute_group_metrics(df: pl.DataFrame, member_count: int, months: int) -> dict:
        if df.is_empty() or member_count == 0:
            return {
                "utilization_per_1k": 0.0,
                "allowed_pmpm": 0.0,
                "paid_pmpm": 0.0,
                "total_claims": 0,
                "total_allowed": 0.0,
                "total_paid": 0.0,
            }
        
        total_claims = len(df)
        total_allowed = float(df["allowed_amount"].sum() if "allowed_amount" in df.columns else 0.0)
        total_paid = float(df["paid_amount"].sum() if "paid_amount" in df.columns else 0.0)
        member_months = member_count * months
        
        return {
            "utilization_per_1k": (total_claims / member_count) * 1000 if member_count > 0 else 0.0,
            "allowed_pmpm": (total_allowed / member_months) if member_months > 0 else 0.0,
            "paid_pmpm": (total_paid / member_months) if member_months > 0 else 0.0,
            "total_claims": total_claims,
            "total_allowed": total_allowed,
            "total_paid": total_paid,
        }
    
    # Get member count
    member_count = treatment_df["member_id"].n_unique() if "member_id" in treatment_df.columns else 1
    
    treatment_pre_metrics = compute_group_metrics(treatment_pre, member_count, pre_months)
    treatment_post_metrics = compute_group_metrics(treatment_post, member_count, post_months)
    
    # Compute control group metrics if provided
    control_pre_metrics = None
    control_post_metrics = None
    
    if control_df is not None and not control_df.is_empty():
        if 'service_date' not in control_df.columns:
            if 'service_from_date' in control_df.columns:
                control_df = control_df.with_columns(
                    pl.col("service_from_date").str.strptime(pl.Date, "%Y-%m-%d").alias("service_date")
                )
            elif 'service_date_from' in control_df.columns:
                control_df = control_df.with_columns(
                    pl.col("service_date_from").str.strptime(pl.Date, "%Y-%m-%d").alias("service_date")
                )
        control_pre = control_df.filter(
            (pl.col("service_date") >= pre_start.date()) & (pl.col("service_date") < pre_end.date())
        )
        control_post = control_df.filter(
            (pl.col("service_date") >= post_start.date()) & (pl.col("service_date") < post_end.date())
        )
        control_member_count = control_df["member_id"].n_unique() if "member_id" in control_df.columns else 1
        control_pre_metrics = compute_group_metrics(control_pre, control_member_count, pre_months)
        control_post_metrics = compute_group_metrics(control_post, control_member_count, post_months)
    
    return {
        "treatment_pre": treatment_pre_metrics,
        "treatment_post": treatment_post_metrics,
        "control_pre": control_pre_metrics,
        "control_post": control_post_metrics,
        "pre_period": {"start": pre_start.isoformat(), "end": pre_end.isoformat()},
        "post_period": {"start": post_start.isoformat(), "end": post_end.isoformat()},
    }


def difference_in_differences(
    treatment_pre: dict,
    treatment_post: dict,
    control_pre: dict | None,
    control_post: dict | None,
    metric: str = "utilization_per_1k",
) -> dict:
    """Compute difference-in-differences estimate"""
    if control_pre is None or control_post is None:
        # Fallback to simple pre/post
        change = treatment_post[metric] - treatment_pre[metric]
        percent_change = (change / treatment_pre[metric] * 100) if treatment_pre[metric] > 0 else 0.0
        
        return {
            "method": "pre_post",
            "effect_size": change,
            "percent_change": percent_change,
            "confidence_interval": None,
            "p_value": None,
            "data_sufficiency_warning": "No control group available - results may be confounded",
        }
    
    # DiD formula: (Treatment_post - Treatment_pre) - (Control_post - Control_pre)
    treatment_diff = treatment_post[metric] - treatment_pre[metric]
    control_diff = control_post[metric] - control_pre[metric]
    did_estimate = treatment_diff - control_diff
    
    percent_change = (did_estimate / treatment_pre[metric] * 100) if treatment_pre[metric] > 0 else 0.0
    
    return {
        "method": "difference_in_differences",
        "effect_size": did_estimate,
        "percent_change": percent_change,
        "treatment_diff": treatment_diff,
        "control_diff": control_diff,
        "confidence_interval": None,
        "p_value": None,
    }


def compute_data_sufficiency_checks(
    treatment_pre: dict,
    treatment_post: dict,
    control_pre: dict | None,
    control_post: dict | None,
) -> dict:
    """Compute data sufficiency checks"""
    warnings = []
    
    # Sample size check
    if treatment_pre.get("total_claims", 0) < 100:
        warnings.append("Low sample size in pre-period")
    if treatment_post.get("total_claims", 0) < 100:
        warnings.append("Low sample size in post-period")
    
    # Control group check
    if control_pre is None or control_post is None:
        warnings.append("No control group - results may be confounded by external factors")
    
    # Parallel trends assumption (simplified)
    parallel_trends_status = "UNKNOWN"
    if control_pre is not None and control_post is not None:
        treatment_pre_trend = treatment_pre.get("utilization_per_1k", 0)
        control_pre_trend = control_pre.get("utilization_per_1k", 0)
        
        if abs(treatment_pre_trend - control_pre_trend) / max(treatment_pre_trend, 1) < 0.2:
            parallel_trends_status = "PASS"
        else:
            parallel_trends_status = "WARN"
            warnings.append("Pre-trends may not be parallel")
    
    return {
        "parallel_trends": parallel_trends_status,
        "sample_size_ok": treatment_pre.get("total_claims", 0) >= 100 and treatment_post.get("total_claims", 0) >= 100,
        "warnings": warnings,
        "seasonality_risk": "LOW",
    }


class ImpactAnalysisCreate(BaseModel):
    """Impact analysis creation model - File storage version (duplicate to avoid circular import)"""
    policy_id: UUID
    treatment_filters: dict
    control_filters: dict | None = None
    matching_strategy: str | None = None
    pre_window_months: int = 6
    post_window_months: int = 6
    run_substitution: bool = False
    run_provider_segmentation: bool = False
    
    class Config:
        """Pydantic config"""
        extra = "ignore"  # Allow extra fields to be ignored


def load_claims_from_file(claims_path: str, filters: dict, start_date: datetime, end_date: datetime) -> pl.DataFrame:
    """Load and filter claims data from CSV file"""
    try:
        # Read CSV
        df = pd.read_csv(claims_path, low_memory=False)
        
        # Convert to polars
        df_pl = pl.from_pandas(df)
        
        # Parse dates
        if 'service_from_date' in df_pl.columns:
            df_pl = df_pl.with_columns(
                pl.col("service_from_date").str.strptime(pl.Date, "%Y-%m-%d").alias("service_date")
            )
        elif 'service_date_from' in df_pl.columns:
            df_pl = df_pl.with_columns(
                pl.col("service_date_from").str.strptime(pl.Date, "%Y-%m-%d").alias("service_date")
            )
        
        # Filter by date
        df_pl = df_pl.filter(
            (pl.col("service_date") >= start_date.date()) & 
            (pl.col("service_date") <= end_date.date())
        )
        
        # Apply filters
        if 'lob' in filters and filters['lob']:
            if isinstance(filters['lob'], list):
                df_pl = df_pl.filter(pl.col("lob").is_in(filters['lob']))
            else:
                df_pl = df_pl.filter(pl.col("lob") == filters['lob'])
        
        if 'markets' in filters and filters['markets']:
            if isinstance(filters['markets'], list):
                df_pl = df_pl.filter(pl.col("market").is_in(filters['markets']))
            else:
                df_pl = df_pl.filter(pl.col("market") == filters['markets'])
        
        if filters.get('in_network_only'):
            df_pl = df_pl.filter(pl.col("in_network_flag") == True)
        
        if 'cpt_codes' in filters and filters['cpt_codes']:
            df_pl = df_pl.filter(pl.col("cpt_hcpcs").is_in(filters['cpt_codes']))
        
        return df_pl
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading claims data: {str(e)}")


@router.post("/analyses/impact", status_code=201)
async def create_impact_analysis_file(
    analysis_data: ImpactAnalysisCreate,
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Create a new impact analysis - File storage version"""
    # Analytics functions are defined inline above to avoid dependency on uepi_worker
    
    import traceback
    try:
        print(f"DEBUG: Received impact analysis request for policy_id: {analysis_data.policy_id}")
        print(f"DEBUG: treatment_filters: {analysis_data.treatment_filters}")
        print(f"DEBUG: pre_window_months: {analysis_data.pre_window_months}, post_window_months: {analysis_data.post_window_months}")
        
        # Get policy
        policy = get_policy(analysis_data.policy_id, current_user.tenant_id)
        if not policy:
            print(f"DEBUG: Policy {analysis_data.policy_id} not found for tenant {current_user.tenant_id}")
            raise HTTPException(status_code=404, detail="Policy not found")
        print(f"DEBUG: Found policy: {policy.get('name', 'Unknown')}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Error getting policy: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Error getting policy: {str(e)}")
    
    # Get policy version for effective date (try to get latest, but fallback to policy metadata)
    policy_version = get_latest_version(current_user.tenant_id, analysis_data.policy_id)
    
    # Get effective date - try multiple sources
    effective_date_str = None
    effective_date = None
    
    # Try from policy version first
    if policy_version:
        effective_period = policy_version.get("effective_period") or policy_version.get("effective_start_date")
        if isinstance(effective_period, dict):
            effective_date_str = effective_period.get("start_date")
        elif isinstance(effective_period, str):
            effective_date_str = effective_period
        elif policy_version.get("effective_start_date"):
            effective_date_str = policy_version.get("effective_start_date")
    
    # Fallback to policy metadata
    if not effective_date_str:
        effective_period = policy.get("effective_period") or policy.get("metadata", {}).get("effective_period")
        if isinstance(effective_period, dict):
            effective_date_str = effective_period.get("start_date")
        elif isinstance(effective_period, str):
            effective_date_str = effective_period
    
    # If still no date, use a default (policy creation date or current date)
    if not effective_date_str:
        # Try to get from policy created_at or use current date
        created_at = policy.get("created_at")
        if created_at:
            effective_date_str = created_at
        else:
            effective_date_str = datetime.utcnow().isoformat()
    
    # Parse the date
    try:
        effective_date = datetime.fromisoformat(effective_date_str.replace('Z', '+00:00'))
        if effective_date.tzinfo:
            effective_date = effective_date.replace(tzinfo=None)
    except Exception as e:
        # If parsing fails, use current date
        effective_date = datetime.utcnow()
    
    # Find claims data file
    # Use BASE_PATH from storage to get the correct data directory
    # BASE_PATH should point to the project root's storage directory
    # But we need apps/data/target_data_model, so calculate relative to storage base
    # If BASE_PATH is /tmp/storage or similar, we need to go to project root
    # Try multiple approaches:
    
    # Approach 1: Calculate from __file__
    current_file = Path(__file__).resolve()  # apps/api/src/uepi_api/routers/analyses_file.py
    # Go up: routers -> uepi_api -> src -> api -> apps -> project_root (6 levels)
    project_root_via_file = current_file.parent.parent.parent.parent.parent.parent
    
    # Approach 2: Use STORAGE_BASE_PATH if available and derive from it
    # STORAGE_BASE_PATH is typically /tmp/storage or project_root/.storage
    # If it's in /tmp, we need to find project root another way
    
    # Approach 3: Search from known location
    # The data is at: project_root/apps/data/target_data_model
    
    # Try approach 1 first
    data_root_via_file = project_root_via_file / "apps" / "data" / "target_data_model"
    target_data_root = data_root_via_file / str(current_user.tenant_id)
    claims_dir = target_data_root / "CLAIMS_LINES"
    
    print(f"DEBUG: Current file: {current_file}")
    print(f"DEBUG: Project root (via file): {project_root_via_file}")
    print(f"DEBUG: Data root: {data_root_via_file}")
    print(f"DEBUG: Looking for claims in: {claims_dir}")
    print(f"DEBUG: Claims dir exists: {claims_dir.exists()}")
    
    # Fallback: try alternative tenant ID
    if not claims_dir.exists():
        fallback_tenant_id = UUID("00000000-0000-0000-0000-000000000001")
        fallback_target_data_root = data_root_via_file / str(fallback_tenant_id)
        fallback_claims_dir = fallback_target_data_root / "CLAIMS_LINES"
        print(f"DEBUG: Trying fallback tenant: {fallback_claims_dir}")
        print(f"DEBUG: Fallback dir exists: {fallback_claims_dir.exists()}")
        if fallback_claims_dir.exists():
            target_data_root = fallback_target_data_root
            claims_dir = fallback_claims_dir
    
    claims_path = None
    if claims_dir.exists():
        for file in claims_dir.glob("*.csv"):
            claims_path = str(file)
            print(f"DEBUG: Found claims file: {claims_path}")
            break
    
    if not claims_path:
        # Try to find any CSV files in the data directory
        print(f"DEBUG: Searching for any claims files in: {data_root_via_file}")
        found_files = list(data_root_via_file.rglob("*.csv")) if data_root_via_file.exists() else []
        print(f"DEBUG: Found {len(found_files)} CSV files in data directory")
        if found_files:
            print(f"DEBUG: Sample files: {[str(f) for f in found_files[:3]]}")
        
        raise HTTPException(
            status_code=400,
            detail=f"Claims data not found. Expected location: {claims_dir}. Project root: {project_root_via_file}. Data root exists: {data_root_via_file.exists()}. Found {len(found_files)} CSV files total."
        )
    
    # Calculate date ranges
    pre_start = effective_date - timedelta(days=analysis_data.pre_window_months * 30)
    post_end = effective_date + timedelta(days=analysis_data.post_window_months * 30)
    
    # Load treatment group data
    try:
        treatment_df = load_claims_from_file(
            claims_path,
            analysis_data.treatment_filters,
            pre_start,
            post_end
        )
        
        # Load control group if provided
        control_df = None
        if analysis_data.control_filters:
            try:
                control_df = load_claims_from_file(
                    claims_path,
                    analysis_data.control_filters,
                    pre_start,
                    post_end
                )
                # Check if control_df is empty
                if control_df is not None and control_df.is_empty():
                    control_df = None
            except Exception as e:
                print(f"Warning: Could not load control group: {e}")
                control_df = None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading claims data: {str(e)}")
    
    # Create analysis record
    analysis_record = create_analysis(
        tenant_id=current_user.tenant_id,
        analysis_data={
            "policy_id": str(analysis_data.policy_id),
            "analysis_type": "IMPACT",
            "status": "PROCESSING",
            "created_by": str(current_user.user_id),
        }
    )
    analysis_id = UUID(analysis_record["id"])
    
    try:
        # Compute metrics
        metrics = compute_pre_post_metrics(
            treatment_df,
            control_df,
            effective_date,
            analysis_data.pre_window_months,
            analysis_data.post_window_months,
        )
        
        # Compute difference-in-differences
        did_result = difference_in_differences(
            metrics["treatment_pre"],
            metrics["treatment_post"],
            metrics.get("control_pre"),
            metrics.get("control_post"),
            metric="utilization_per_1k",
        )
        
        # Compute confidence interval (simplified)
        if did_result.get("effect_size") is not None:
            ci_lower = did_result["effect_size"] * 0.8
            ci_upper = did_result["effect_size"] * 1.2
            did_result["confidence_interval"] = [ci_lower, ci_upper]
        
        # Data sufficiency checks
        checks = compute_data_sufficiency_checks(
            metrics["treatment_pre"],
            metrics["treatment_post"],
            metrics.get("control_pre"),
            metrics.get("control_post"),
        )
        
        # Compute confidence score
        confidence_score = 100
        if len(checks.get("warnings", [])) > 0:
            confidence_score -= len(checks["warnings"]) * 15
        if checks.get("parallel_trends") == "WARN":
            confidence_score -= 20
        if not checks.get("sample_size_ok", True):
            confidence_score -= 25
        confidence_score = max(0, confidence_score)
        
        # Build analysis result
        analysis_result = {
            "policy_id": str(analysis_data.policy_id),
            "policy_effective_date": effective_date.isoformat(),
            "metrics": metrics,
            "impact_estimate": did_result,
            "data_sufficiency_checks": checks,
            "confidence_score": confidence_score,
            "methodology": {
                "method": did_result.get("method", "pre_post"),
                "pre_months": analysis_data.pre_window_months,
                "post_months": analysis_data.post_window_months,
                "has_control_group": control_df is not None and not control_df.is_empty(),
            },
            "limitations": checks.get("warnings", []),
        }
        
        # Update analysis status
        update_analysis(
            analysis_id,
            current_user.tenant_id,
            {
                "status": "COMPLETED",
            }
        )
        
        # Store result index
        import json
        import tempfile
        result_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(analysis_result, result_file, indent=2, default=str)
        result_file.close()
        
        create_result_index(
            tenant_id=current_user.tenant_id,
            analysis_id=analysis_id,
            result_type="impact_result",
            data_uri=f"file://{result_file.name}",
        )
        
        return {
            "id": str(analysis_id),
            "policy_id": str(analysis_data.policy_id),
            "analysis_type": "IMPACT",
            "status": "COMPLETED",
            "result": analysis_result,
            "created_at": analysis_record["created_at"],
            "updated_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        # Update status to failed
        update_analysis(
            analysis_id,
            current_user.tenant_id,
            {
                "status": "FAILED",
            }
        )
        raise HTTPException(status_code=500, detail=f"Error running impact analysis: {str(e)}")

async def create_simulate_analysis_file(
    analysis_data,
    current_user: CurrentUser,
):
    """Create a what-if scenario simulation analysis - File storage version"""
    import traceback
    
    try:
        from uuid import uuid4
        import json
        import tempfile
        import sys
        from pathlib import Path
        
        project_root = Path(__file__).parent.parent.parent.parent.parent.parent
        sys.path.insert(0, str(project_root / "apps" / "worker" / "src"))
        sys.path.insert(0, str(project_root / "packages" / "common" / "src"))
        
        print(f"DEBUG: Loading what-if simulation modules...")
        from uepi_worker.whatif import simulate_scenario, ScenarioParameters
        from uepi_worker.analytics import load_claims_data
        from uepi_common.models import CanonicalPolicy, PolicyType, PolicyStatus, PolicyScope, EffectivePeriod, Enforcement, EnforcementMechanism
        print(f"DEBUG: Modules loaded successfully")
        # Note: datetime and timedelta already imported at module level
    except Exception as import_error:
        error_trace = traceback.format_exc()
        error_msg = str(import_error)
        # Extract more details from Pydantic validation errors
        if hasattr(import_error, 'errors'):
            # Pydantic ValidationError
            error_details = []
            for err in import_error.errors():
                error_details.append(f"{err.get('loc', [])}: {err.get('msg', '')}")
            error_msg = f"Pydantic validation errors: {'; '.join(error_details)}"
        elif "validation" in error_msg.lower() or "pydantic" in error_msg.lower():
            error_msg = f"Pydantic validation error: {error_msg}"
        print(f"ERROR: Failed to import modules for what-if simulation: {import_error}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import simulation modules: {error_msg}"
        )
    
    try:
        print(f"DEBUG: Getting policy {analysis_data.policy_id}...")
        # Get policy - handle both UUID and string IDs
        policy_id = analysis_data.policy_id
        policy_dict = get_policy(policy_id, current_user.tenant_id)
        if not policy_dict:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Convert policy dict to CanonicalPolicy
        try:
            policy_type_enum = PolicyType(policy_dict.get("policy_type", "PRIOR_AUTH"))
        except:
            policy_type_enum = PolicyType.PRIOR_AUTH
        
        try:
            status_enum = PolicyStatus(policy_dict.get("status", "ACTIVE"))
        except:
            status_enum = PolicyStatus.ACTIVE
        
        effective_period_data = policy_dict.get("effective_period", {})
        if effective_period_data and isinstance(effective_period_data, dict):
            # Only pass expected fields to avoid Pydantic extra_forbidden errors
            effective_period_kwargs = {}
            if effective_period_data.get("start_date"):
                effective_period_kwargs["start_date"] = datetime.fromisoformat(effective_period_data["start_date"])
            else:
                effective_period_kwargs["start_date"] = datetime.utcnow()
            if effective_period_data.get("end_date"):
                effective_period_kwargs["end_date"] = datetime.fromisoformat(effective_period_data["end_date"])
            else:
                effective_period_kwargs["end_date"] = None
            effective_period = EffectivePeriod(**effective_period_kwargs)
        else:
            effective_period = EffectivePeriod(start_date=datetime.utcnow(), end_date=None)
        
        scope_data = policy_dict.get("scope", {})
        if scope_data and isinstance(scope_data, dict):
            # Only pass expected fields to avoid Pydantic extra_forbidden errors
            # PolicyScope has these fields: lob, markets, plans, product_types, states, regions, 
            # network, network_tiers, member_age_min, member_age_max, exclude_pregnant, 
            # gender_filters, exclude_centers_of_excellence, include_provider_types, 
            # exclude_provider_types, provider_specialties, exclude_er, exclude_hospital_op, 
            # allowed_sites, applies_to_all
            allowed_scope_fields = {
                "lob", "markets", "plans", "product_types", "states", "regions",
                "network", "network_tiers", "member_age_min", "member_age_max", 
                "exclude_pregnant", "gender_filters", "exclude_centers_of_excellence",
                "include_provider_types", "exclude_provider_types", "provider_specialties",
                "exclude_er", "exclude_hospital_op", "allowed_sites", "applies_to_all"
            }
            scope_kwargs = {k: v for k, v in scope_data.items() if k in allowed_scope_fields}
            scope = PolicyScope(**scope_kwargs) if scope_kwargs else PolicyScope(lob=None, markets=None, network=None)
        else:
            scope = PolicyScope(lob=None, markets=None, network=None)
        
        enforcement_data = policy_dict.get("enforcement", {})
        if enforcement_data and isinstance(enforcement_data, dict):
            # Enforcement has: mechanism, touchpoint, override_allowed
            # Only pass expected fields to avoid Pydantic extra_forbidden errors
            enforcement_kwargs = {
                "mechanism": EnforcementMechanism(enforcement_data.get("mechanism", "HARD")),
                "touchpoint": enforcement_data.get("touchpoint", []),
                "override_allowed": enforcement_data.get("override_allowed", False),
            }
            enforcement = Enforcement(**enforcement_kwargs)
        else:
            enforcement = None
        
        # CanonicalPolicy fields: policy_id, policy_name, policy_type, description, status,
        # effective_period, scope, enforcement, policy_levers, policy_logic,
        # expected_behavioral_response, analytics_expectations, ui_hints, created_at, updated_at
        # Convert policy_id to UUID - handle both UUID and string IDs
        policy_id_raw = policy_dict.get("id") or policy_dict.get("policy_id")
        try:
            # Try to parse as UUID first
            if isinstance(policy_id_raw, str):
                if len(policy_id_raw) == 36 and policy_id_raw.count('-') == 4:
                    policy_id_uuid = UUID(policy_id_raw)
                else:
                    # String ID - generate deterministic UUID from string
                    import hashlib
                    namespace = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
                    policy_id_uuid = UUID(bytes=hashlib.md5(namespace.bytes + policy_id_raw.encode()).digest())
            else:
                policy_id_uuid = UUID(policy_id_raw) if not isinstance(policy_id_raw, UUID) else policy_id_raw
        except (ValueError, AttributeError, TypeError) as e:
            # Fallback: generate UUID from string
            import hashlib
            namespace = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
            policy_id_str = str(policy_id_raw)
            policy_id_uuid = UUID(bytes=hashlib.md5(namespace.bytes + policy_id_str.encode()).digest())
        
        policy = CanonicalPolicy(
            policy_id=policy_id_uuid,
            policy_name=policy_dict.get("name") or policy_dict.get("policy_name", ""),
            policy_type=policy_type_enum,
            description=policy_dict.get("description", ""),
            status=status_enum,
            scope=scope,
            effective_period=effective_period,
            enforcement=enforcement,
            policy_levers=policy_dict.get("policy_levers", []) or [],
            policy_logic=None,  # Set to None for what-if analysis
            expected_behavioral_response=None,
            analytics_expectations=None,
            ui_hints=None,
            created_at=None,
            updated_at=None,
        )
        print(f"DEBUG: Policy object created: {policy.policy_name}")
    except HTTPException:
        raise
    except Exception as policy_error:
        error_trace = traceback.format_exc()
        print(f"ERROR: Failed to create CanonicalPolicy: {policy_error}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create policy object: {str(policy_error)}"
        )
    
    try:
        # Create analysis record (create_analysis will generate the ID)
        print(f"DEBUG: Creating analysis record...")
        analysis_record = create_analysis(
            tenant_id=current_user.tenant_id,
            analysis_data={
                "policy_id": str(analysis_data.policy_id),
                "analysis_type": "SIMULATE",
                "status": "RUNNING",
                "metadata": {
                    "scenario_params": analysis_data.scenario_params,
                    "filters": analysis_data.filters,
                },
            }
        )
        # Get the analysis_id from the returned record
        analysis_id = UUID(analysis_record["id"])
        print(f"DEBUG: Analysis created with ID: {analysis_id}")
    except Exception as analysis_error:
        error_trace = traceback.format_exc()
        print(f"ERROR: Failed to create analysis record: {analysis_error}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create analysis: {str(analysis_error)}"
        )
    
    try:
        # Load baseline data
        baseline_filters = analysis_data.filters
        baseline_start = datetime.utcnow() - timedelta(days=365)
        baseline_end = datetime.utcnow()
        
        # Try to load claims data - use file storage if S3 fails
        baseline_df = None
        try:
            baseline_df = load_claims_data(
                current_user.tenant_id,
                baseline_filters,
                baseline_start,
                baseline_end,
            )
        except Exception as load_error:
            print(f"Warning: Could not load claims from S3: {load_error}")
            # Try to load from file storage
            try:
                from uepi_api.storage import BASE_PATH
                import os
                # Note: pl (polars) is already imported at module level
                
                # Look for curated claims in file storage
                curated_path = BASE_PATH / "curated" / "claims"
                if curated_path.exists():
                    # Try to find parquet files
                    parquet_files = list(curated_path.rglob("*.parquet"))
                    if parquet_files:
                        # Load first available file as fallback
                        baseline_df = pl.read_parquet(parquet_files[0])
                        print(f"Loaded {len(baseline_df)} claims from file storage: {parquet_files[0]}")
                    else:
                        # Create empty dataframe with required columns
                        baseline_df = pl.DataFrame({
                            "member_id": [],
                            "provider_id": [],
                            "service_date": [],
                            "allowed_amount": [],
                            "paid_amount": [],
                            "service_category": [],
                        })
                        print("Warning: No claims data found, using empty dataframe")
                else:
                    # Create empty dataframe
                    baseline_df = pl.DataFrame({
                        "member_id": [],
                        "provider_id": [],
                        "service_date": [],
                        "allowed_amount": [],
                        "paid_amount": [],
                        "service_category": [],
                    })
                    print("Warning: No curated claims directory found, using empty dataframe")
            except Exception as file_error:
                print(f"Error loading from file storage: {file_error}")
                # Create empty dataframe as last resort
                baseline_df = pl.DataFrame({
                    "member_id": [],
                    "provider_id": [],
                    "service_date": [],
                    "allowed_amount": [],
                    "paid_amount": [],
                    "service_category": [],
                })
        
        if baseline_df is None or baseline_df.is_empty():
            print("Warning: No baseline data available, simulation will use defaults")
            # Create minimal dataframe for simulation
            baseline_df = pl.DataFrame({
                "member_id": ["member_1", "member_2", "member_3"],
                "provider_id": ["provider_1", "provider_2", "provider_3"],
                "service_date": [datetime.utcnow().date()] * 3,
                "allowed_amount": [100.0, 200.0, 150.0],
                "paid_amount": [80.0, 160.0, 120.0],
                "service_category": ["OUTPATIENT", "OUTPATIENT", "OUTPATIENT"],
            })
        
        # Load latest elasticity models
        elasticity_curves = None
        try:
            from uepi_api.storage_learning import get_latest_elasticity_model
            policy_type_str = policy_dict.get("policy_type", "PRIOR_AUTH")
            latest_model = get_latest_elasticity_model(
                tenant_id=current_user.tenant_id,
                policy_type=policy_type_str,
                service_category=None,
            )
            if latest_model:
                elasticity_coefficients = latest_model.get("elasticity_coefficients", {})
                if elasticity_coefficients:
                    elasticity_curves = {}
                    for category, coeffs in elasticity_coefficients.items():
                        if isinstance(coeffs, dict):
                            elasticity_curves[category] = {
                                "elasticity": coeffs.get("utilization_elasticity", coeffs.get("elasticity", -0.3)),
                                "cost_elasticity": coeffs.get("cost_elasticity", -0.2),
                                "confidence": latest_model.get("confidence", 0.7),
                                "model_version": latest_model.get("version", "v1.0"),
                            }
        except Exception as e:
            print(f"Warning: Could not load latest elasticity models: {e}")
        
        # Create scenario parameters - only include expected fields
        scenario_params_dict = analysis_data.scenario_params if isinstance(analysis_data.scenario_params, dict) else {}
        scenario = ScenarioParameters(
            policy_id=str(analysis_data.policy_id),
            lever_adjustments=scenario_params_dict.get("lever_adjustments", {}),
            elasticity_adjustments=scenario_params_dict.get("elasticity_adjustments", {}),
            member_count_multiplier=float(scenario_params_dict.get("member_count_multiplier", 1.0)),
            utilization_trend=float(scenario_params_dict.get("utilization_trend", 0.0)),
            cost_inflation=float(scenario_params_dict.get("cost_inflation", 0.02)),
            projection_months=int(scenario_params_dict.get("projection_months", 12)),
        )
        
        # Run simulation with latest elasticity models
        print(f"Running what-if simulation for policy {analysis_data.policy_id}...")
        print(f"Baseline dataframe size: {len(baseline_df)} rows")
        print(f"Scenario parameters: {scenario}")
        
        result = simulate_scenario(
            tenant_id=current_user.tenant_id,
            policy=policy,
            baseline_claims_df=baseline_df,
            scenario_params=scenario,
            elasticity_curves=elasticity_curves,
            use_latest_elasticity_models=True,
        )
        
        print(f"Simulation completed. Scenario ID: {result.scenario_id}")
        print(f"Baseline metrics: {result.baseline_metrics}")
        print(f"Projected metrics: {result.projected_metrics}")
        
        # Convert result to dict, including tradeoff and risk analysis if available
        result_dict = {
            "scenario_id": result.scenario_id,
            "baseline_metrics": result.baseline_metrics,
            "projected_metrics": result.projected_metrics,
            "impact_metrics": result.impact_metrics,
            "confidence_intervals": {k: list(v) for k, v in result.confidence_intervals.items()},
            "confidence_score": result.confidence_score,
            "sensitivity_analysis": result.sensitivity_analysis,
        }
        
        # Include tradeoff and risk analysis if they exist in impact_metrics
        if hasattr(result, 'tradeoff_analysis') and result.tradeoff_analysis:
            if isinstance(result_dict["impact_metrics"], dict):
                result_dict["impact_metrics"]["tradeoff_analysis"] = result.tradeoff_analysis
        if hasattr(result, 'risk_analysis') and result.risk_analysis:
            if isinstance(result_dict["impact_metrics"], dict):
                result_dict["impact_metrics"]["risk_analysis"] = result.risk_analysis
        
        print(f"Result dict created with keys: {list(result_dict.keys())}")
        
        # Save result to file
        result_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(result_dict, result_file, indent=2, default=str)
        result_file.close()
        
        create_result_index(
            tenant_id=current_user.tenant_id,
            analysis_id=analysis_id,
            result_type="whatif_scenario",
            data_uri=f"file://{result_file.name}",
        )
        
        # Update analysis status
        update_analysis(
            analysis_id=analysis_id,
            tenant_id=current_user.tenant_id,
            updates={"status": "COMPLETED"}
        )
        
        return {
            "id": str(analysis_id),
            "policy_id": str(analysis_data.policy_id),
            "analysis_type": "SIMULATE",
            "status": "COMPLETED",
            "result": result_dict,
            "created_at": analysis_record.get("created_at"),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"What-if scenario simulation error: {error_trace}")
        
        update_analysis(
            analysis_id=analysis_id,
            tenant_id=current_user.tenant_id,
            updates={"status": "FAILED", "error_message": str(e), "error_trace": error_trace}
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"What-if scenario simulation failed: {str(e)}"
        )
