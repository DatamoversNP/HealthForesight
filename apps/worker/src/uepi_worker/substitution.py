"""Substitution detection module"""
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import boto3
import polars as pl
import numpy as np

from uepi_worker.config import get_settings
from uepi_worker.analytics import load_claims_data, get_s3_client

settings = get_settings()


# Code group mappings for substitution detection
CODE_GROUPS = {
    "MRI": ["72141", "72142", "72146", "72148", "72141", "72142"],
    "ER_IMAGING": ["70450", "70460", "72141", "70470"],
    "INFUSION": ["96413", "96415", "96417"],
    "PT": ["97110", "97112", "97140"],
    "SPECIALTY_VISIT": ["99213", "99214", "99215"],
    "URGENT_CARE": ["99281", "99282", "99283"],
}

# Site-of-care POS codes
POS_CODES = {
    "OFFICE": ["11"],
    "OUTPATIENT_HOSPITAL": ["22"],
    "EMERGENCY": ["23"],
    "FREESTANDING": ["19"],
    "URGENT_CARE": ["20"],
}


def detect_substitution(
    tenant_id: UUID,
    policy_effective_date: datetime,
    affected_codes: list[str],
    treatment_filters: dict[str, Any],
    pre_months: int = 6,
    post_months: int = 6,
    lag_windows: list[int] = [30, 60, 90],
) -> dict[str, Any]:
    """Detect substitution patterns after policy change"""
    # Load pre and post period data
    pre_start = policy_effective_date - timedelta(days=pre_months * 30)
    pre_end = policy_effective_date
    post_start = policy_effective_date
    post_end = policy_effective_date + timedelta(days=post_months * 30)
    
    # Load all claims in the period
    all_filters = treatment_filters.copy()
    all_df = load_claims_data(tenant_id, all_filters, pre_start, post_end)
    
    if all_df.is_empty():
        return {
            "substitutions": [],
            "warnings": ["No data available for substitution analysis"],
        }
    
    # Parse dates
    all_df = all_df.with_columns(
        pl.col("service_from_date").str.strptime(pl.Date, "%Y-%m-%d").alias("service_date")
    )
    
    # Split pre/post
    pre_df = all_df.filter(
        (pl.col("service_date") >= pre_start.date()) & (pl.col("service_date") < pre_end.date())
    )
    post_df = all_df.filter(
        (pl.col("service_date") >= post_start.date()) & (pl.col("service_date") < post_end.date())
    )
    
    # Compute baseline metrics per code
    pre_metrics = (
        pre_df.group_by("cpt_hcpcs")
        .agg([
            pl.sum("allowed_amount").alias("total_allowed"),
            pl.sum("units").alias("total_units"),
            pl.count().alias("claim_count"),
        ])
        .with_columns([
            (pl.col("total_allowed") / pl.col("claim_count")).alias("avg_allowed_per_claim"),
        ])
    )
    
    post_metrics = (
        post_df.group_by("cpt_hcpcs")
        .agg([
            pl.sum("allowed_amount").alias("total_allowed"),
            pl.sum("units").alias("total_units"),
            pl.count().alias("claim_count"),
        ])
        .with_columns([
            (pl.col("total_allowed") / pl.col("claim_count")).alias("avg_allowed_per_claim"),
        ])
    )
    
    # Join to compute changes
    changes = (
        pre_metrics.join(
            post_metrics,
            on="cpt_hcpcs",
            how="outer",
            suffix="_post",
        )
        .with_columns([
            (pl.col("total_allowed_post").fill_null(0) - pl.col("total_allowed").fill_null(0)).alias("allowed_delta"),
            (pl.col("claim_count_post").fill_null(0) - pl.col("claim_count").fill_null(0)).alias("claim_count_delta"),
            ((pl.col("total_allowed_post").fill_null(0) - pl.col("total_allowed").fill_null(0)) / 
             pl.col("total_allowed").fill_null(1) * 100).alias("allowed_pct_change"),
        ])
        .filter(pl.col("allowed_delta") > 0)  # Only increased services
        .sort("allowed_delta", descending=True)
        .head(20)  # Top 20
    )
    
    # Classify substitutions
    substitutions = []
    for row in changes.iter_rows(named=True):
        code = row["cpt_hcpcs"]
        
        # Check if this is a site-of-care shift
        pre_pos = pre_df.filter(pl.col("cpt_hcpcs") == code)["place_of_service"].mode()
        post_pos = post_df.filter(pl.col("cpt_hcpcs") == code)["place_of_service"].mode()
        
        is_site_of_care_shift = False
        if len(pre_pos) > 0 and len(post_pos) > 0:
            if pre_pos[0] != post_pos[0]:
                is_site_of_care_shift = True
        
        # Check if this is related to affected codes (service substitution)
        is_service_substitution = False
        code_group = None
        for group_name, group_codes in CODE_GROUPS.items():
            if code in group_codes:
                code_group = group_name
                # Check if any affected code is in the same group
                if any(ac in group_codes for ac in affected_codes):
                    is_service_substitution = True
                break
        
        # Compute lag effects
        lag_effects = {}
        for lag_days in lag_windows:
            lag_start = post_start + timedelta(days=lag_days)
            lag_df = post_df.filter(
                (pl.col("service_date") >= lag_start.date()) & 
                (pl.col("service_date") < (lag_start + timedelta(days=30)).date())
            )
            lag_code_df = lag_df.filter(pl.col("cpt_hcpcs") == code)
            lag_effects[f"{lag_days}_day"] = {
                "claim_count": len(lag_code_df),
                "total_allowed": lag_code_df["allowed_amount"].sum() if not lag_code_df.is_empty() else 0,
            }
        
        # Compute confidence score
        confidence_score = 50  # Base
        if is_site_of_care_shift:
            confidence_score += 20
        if is_service_substitution:
            confidence_score += 20
        if row["allowed_pct_change"] > 50:
            confidence_score += 10
        confidence_score = min(100, confidence_score)
        
        substitutions.append({
            "code": code,
            "code_group": code_group,
            "classification": "SITE_OF_CARE_SHIFT" if is_site_of_care_shift else 
                             "SERVICE_SUBSTITUTION" if is_service_substitution else "UNKNOWN",
            "pre_allowed": row.get("total_allowed", 0),
            "post_allowed": row.get("total_allowed_post", 0),
            "allowed_delta": row["allowed_delta"],
            "allowed_pct_change": row["allowed_pct_change"],
            "pre_claim_count": row.get("claim_count", 0),
            "post_claim_count": row.get("claim_count_post", 0),
            "claim_count_delta": row["claim_count_delta"],
            "lag_effects": lag_effects,
            "confidence_score": confidence_score,
        })
    
    # Sort by confidence and magnitude
    substitutions.sort(key=lambda x: (x["confidence_score"], x["allowed_delta"]), reverse=True)
    
    return {
        "substitutions": substitutions[:20],  # Top 20
        "total_substitutions_detected": len(substitutions),
        "policy_effective_date": policy_effective_date.isoformat(),
        "analysis_period": {
            "pre_start": pre_start.isoformat(),
            "pre_end": pre_end.isoformat(),
            "post_start": post_start.isoformat(),
            "post_end": post_end.isoformat(),
        },
    }


def run_substitution_analysis(
    tenant_id: UUID,
    analysis_id: UUID,
    policy_id: UUID,
    policy_effective_date: datetime,
    treatment_filters: dict[str, Any],
    pre_months: int = 6,
    post_months: int = 6,
) -> dict[str, Any]:
    """Run complete substitution analysis"""
    # Get affected codes from policy
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from uepi_api.models.policy import PolicyCodeSet, PolicyVersion
    
    engine = create_engine(settings.database.url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Get latest policy version
        version = db.query(PolicyVersion).filter(
            PolicyVersion.policy_id == policy_id,
            PolicyVersion.tenant_id == tenant_id,
        ).order_by(PolicyVersion.version_number.desc()).first()
        
        if not version:
            return {
                "substitutions": [],
                "warnings": ["Policy version not found"],
            }
        
        # Get code sets for this version
        code_sets = db.query(PolicyCodeSet).filter(
            PolicyCodeSet.version_id == version.id,
            PolicyCodeSet.tenant_id == tenant_id,
        ).all()
        
        affected_codes = [cs.code for cs in code_sets]
    finally:
        db.close()
    
    # Run substitution detection
    result = detect_substitution(
        tenant_id,
        policy_effective_date,
        affected_codes,
        treatment_filters,
        pre_months,
        post_months,
    )
    
    # Add metadata
    result["policy_id"] = str(policy_id)
    result["analysis_id"] = str(analysis_id)
    result["affected_codes"] = affected_codes
    
    return result

