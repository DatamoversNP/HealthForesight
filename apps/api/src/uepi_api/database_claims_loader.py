"""Database-based claims loader for observations and analyses"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import date, datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session

from uepi_api.repositories.canonical_data import CanonicalDataRepository
from uepi_api.database import SessionLocal
from uepi_api.services.policy_scoped_data_generation import build_policy_claims_filters


def load_claims_from_database(
    tenant_id: UUID,
    start_date: date,
    end_date: date,
    filters: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
) -> pd.DataFrame:
    """Load claims from database for a date range
    
    Args:
        tenant_id: Tenant ID
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        filters: Optional filters dict with keys:
            - lob: Line of business (str or list)
            - market: Market (str or list)
            - service_category: Service category (str or list)
            - cpt_code: CPT code (str or list)
            - in_network: Boolean
            - member_ids: List of member IDs
        db: Optional database session (creates new if not provided)
    
    Returns:
        pandas DataFrame with claims data
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    
    try:
        repository = CanonicalDataRepository(db)
        
        # Get base claims for date range
        # Note: get_claims_lines only supports single lob/market, so we need to handle multiple
        filters = filters or {}
        
        lobs = filters.get('lob', [])
        if isinstance(lobs, str):
            lobs = [lobs]
        if not lobs:
            lobs = [None]  # Get all LOBs
        
        markets = filters.get('markets', filters.get('market', []))
        if isinstance(markets, str):
            markets = [markets]
        if not markets:
            markets = [None]  # Get all markets
        
        cpt_codes = filters.get("cpt_codes") or filters.get("cpt_code")
        if isinstance(cpt_codes, str):
            cpt_codes = [cpt_codes]
        service_cats = filters.get("service_categories") or filters.get("service_category")
        if isinstance(service_cats, str):
            service_cats = [service_cats] if service_cats else None
        diagnosis_codes = filters.get("diagnosis_codes")
        if isinstance(diagnosis_codes, str):
            diagnosis_codes = [diagnosis_codes] if diagnosis_codes else None

        all_dfs = []
        for lob in lobs:
            for market in markets:
                df = repository.get_claims_lines(
                    tenant_id=tenant_id,
                    start_date=start_date,
                    end_date=end_date,
                    lob=lob,
                    market=market,
                    cpt_codes=cpt_codes,
                    hcpcs_codes=cpt_codes,
                    service_categories=service_cats,
                    diagnosis_codes=diagnosis_codes,
                )
                if not df.empty:
                    all_dfs.append(df)
        
        if not all_dfs:
            return pd.DataFrame()
        
        # Combine all dataframes
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # Apply additional filters
        if filters.get('service_category'):
            service_cats = filters['service_category']
            if isinstance(service_cats, str):
                service_cats = [service_cats]
            if 'service_category' in combined_df.columns:
                combined_df = combined_df[combined_df['service_category'].isin(service_cats)]
        
        if filters.get('cpt_code') or filters.get('cpt_codes'):
            cpt_codes = filters.get('cpt_code') or filters.get('cpt_codes', [])
            if isinstance(cpt_codes, str):
                cpt_codes = [cpt_codes]
            if 'cpt_code' in combined_df.columns:
                combined_df = combined_df[combined_df['cpt_code'].isin(cpt_codes)]
        
        if filters.get('in_network') is not None:
            if 'in_network' in combined_df.columns:
                combined_df = combined_df[combined_df['in_network'] == filters['in_network']]
        
        if filters.get('member_ids'):
            if 'member_id' in combined_df.columns:
                combined_df = combined_df[combined_df['member_id'].isin(filters['member_ids'])]
        
        return combined_df
        
    finally:
        if close_db:
            db.close()


def load_claims_for_observation(
    tenant_id: UUID,
    policy_id: UUID,
    policy_effective_date: date,
    pre_months: int = 6,
    post_months: int = 1,
    policy_scope: Optional[Dict[str, Any]] = None,
    policy: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
    observation_period_start: Optional[date] = None,
    observation_period_end: Optional[date] = None,
) -> Dict[str, pd.DataFrame]:
    """Load claims for observation computation (pre and post periods).
    Uses consistent policy filters (scope + levers merged) when policy is provided.

    Args:
        tenant_id: Tenant ID
        policy_id: Policy ID
        policy_effective_date: Policy effective date
        pre_months: Number of months before effective date
        post_months: Number of months after effective date
        policy_scope: Policy scope filters (legacy fallback if policy not provided)
        policy: Full policy dict - when provided, uses build_policy_claims_filters for consistent filtering
        db: Optional database session
        observation_period_start: Optional observation period start date (if provided, use this for post period)
        observation_period_end: Optional observation period end date (if provided, use this for post period)

    Returns:
        Dict with keys:
            - 'pre': DataFrame with pre-period claims
            - 'post': DataFrame with post-period claims
    """
    # If observation period dates are provided, use them for post period
    # Otherwise, calculate from policy effective date
    if observation_period_start and observation_period_end:
        # Use actual observation period for post period
        post_start = observation_period_start
        post_end = observation_period_end
        # Pre period is still relative to policy effective date
        pre_start = policy_effective_date - timedelta(days=pre_months * 30)
        pre_end = policy_effective_date
    else:
        # Calculate date ranges from policy effective date
        pre_start = policy_effective_date - timedelta(days=pre_months * 30)
        pre_end = policy_effective_date
        post_start = policy_effective_date
        post_end = policy_effective_date + timedelta(days=post_months * 30)
    
    # Build filters: use consistent policy filters (scope + levers) when policy provided
    if policy:
        pf = build_policy_claims_filters(policy)
        filters = {}
        if pf.get("lob"):
            filters["lob"] = pf["lob"]
        if pf.get("markets"):
            filters["markets"] = pf["markets"]
        elif pf.get("market"):
            filters["markets"] = [pf["market"]] if isinstance(pf["market"], str) else pf["market"]
        if pf.get("service_categories"):
            filters["service_categories"] = pf["service_categories"]
        elif pf.get("service_category"):
            filters["service_category"] = pf["service_category"]
        if pf.get("cpt_codes"):
            filters["cpt_codes"] = pf["cpt_codes"]
    else:
        filters = {}
        if policy_scope:
            if policy_scope.get("lob"):
                filters["lob"] = policy_scope["lob"]
            if policy_scope.get("markets"):
                filters["markets"] = policy_scope["markets"]
            if policy_scope.get("service_category"):
                filters["service_category"] = policy_scope["service_category"]

    # Load pre-period claims
    pre_df = load_claims_from_database(
        tenant_id=tenant_id,
        start_date=pre_start,
        end_date=pre_end,
        filters=filters,
        db=db,
    )
    
    # Load post-period claims
    post_df = load_claims_from_database(
        tenant_id=tenant_id,
        start_date=post_start,
        end_date=post_end,
        filters=filters,
        db=db,
    )
    
    return {
        'pre': pre_df,
        'post': post_df,
    }


def compute_metrics_from_database_claims(
    claims_df: pd.DataFrame,
    member_count: Optional[int] = None,
    months: int = 1,
) -> Dict[str, Any]:
    """Compute metrics from database claims DataFrame
    
    Args:
        claims_df: DataFrame with claims data
        member_count: Optional member count (will compute if not provided)
        months: Number of months in period
    
    Returns:
        Dict with metrics:
            - utilization_per_1k
            - cost_per_member (paid_pmpm)
            - total_claims
            - total_paid
    """
    if claims_df.empty:
        return {
            "utilization_per_1k": 0.0,
            "cost_per_member": 0.0,
            "cost_pmpm": 0.0,
            "paid_pmpm": 0.0,
            "allowed_pmpm": 0.0,
            "total_claims": 0,
            "total_paid": 0.0,
            "total_allowed": 0.0,
            "member_months": float(member_count * months) if member_count else 0.0,
            "unique_members": int(member_count) if member_count else 0,
        }
    
    # Compute member count if not provided
    if member_count is None:
        if 'member_id' in claims_df.columns:
            member_count = claims_df['member_id'].nunique()
        else:
            member_count = 1
    
    # Compute totals
    total_claims = len(claims_df)
    
    # Get paid amount column (try different names)
    paid_col = None
    for col in ['paid_amount', 'paid_pmpm', 'paid']:
        if col in claims_df.columns:
            paid_col = col
            break
    
    total_paid = 0.0
    if paid_col:
        total_paid = float(claims_df[paid_col].sum())
    
    # Get allowed amount column
    allowed_col = None
    for col in ['allowed_amount', 'allowed']:
        if col in claims_df.columns:
            allowed_col = col
            break
    
    total_allowed = 0.0
    if allowed_col:
        total_allowed = float(claims_df[allowed_col].sum())
    
    # Compute metrics - Industry standard definitions (HEDIS/NQF alignment)
    # Utilization: services per 1,000 member-months (SMPM) - standard healthcare utilization rate
    # PMPM: Per Member Per Month - total $ / member_months (paid = actual spend, allowed = contracted)
    member_months = member_count * months if member_count > 0 else 1

    utilization_per_1k = (total_claims / member_months * 1000) if member_months > 0 else 0.0  # SMPM
    paid_pmpm = (total_paid / member_months) if member_months > 0 else 0.0
    allowed_pmpm = (total_allowed / member_months) if member_months > 0 else 0.0

    return {
        "utilization_per_1k": max(0.0, float(utilization_per_1k)),
        "cost_per_member": float(paid_pmpm),
        "cost_pmpm": float(paid_pmpm),
        "paid_pmpm": float(paid_pmpm),
        "allowed_pmpm": float(allowed_pmpm),
        "total_claims": int(total_claims),
        "total_paid": float(total_paid),
        "total_allowed": float(total_allowed),
        "member_months": float(member_months),
        "unique_members": int(member_count),
    }
