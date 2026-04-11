"""Database-only baseline computation from claims_lines table"""
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import pandas as pd

from uepi_api.repositories.canonical_data import CanonicalDataRepository
from uepi_api.models.canonical_data import ClaimsLineDB
from uepi_api.services.policy_scoped_data_generation import extract_policy_target_codes, build_policy_claims_filters

# When policy scope uses market "ALL", expand to concrete markets present in demo data so the query matches.
DEMO_MARKETS_WHEN_ALL = ["NYC", "CHICAGO", "LA", "DFW"]

# Policy-scoped segmentation uses a bounded claims sample (full tenant load uses all rows already in memory).
_POLICY_BASELINE_SEGMENTATION_ROW_CAP = 100_000
# General baseline: sample for segmentation only (counts come from aggregate).
_GENERAL_BASELINE_SEGMENTATION_ROW_CAP = 100_000


def _baseline_calendar_months_inclusive(start_date: date, end_date: date) -> int:
    """Count of calendar months touched by [start_date, end_date], inclusive.

    Matches baselines already persisted in the DB (e.g. Jan 2023–Dec 2025 → 36).
    The old formula (end.month - start.month) without +1 undercounted by one when
    spanning multiple years (e.g. 35 instead of 36).
    """
    if end_date < start_date:
        return 1
    return max(1, (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1)


def _merge_baseline_segmentation_from_claims_df(metrics: Dict[str, Any], claims_df: pd.DataFrame) -> None:
    """Attach provider_archetypes and patient_segments from a claims DataFrame (in-place)."""
    if claims_df is None or claims_df.empty:
        return
    from uepi_api.baseline_segmentation_from_claims import (
        patient_segments_from_claims_df,
        provider_archetypes_from_claims_df,
    )

    pa = provider_archetypes_from_claims_df(claims_df)
    ps = patient_segments_from_claims_df(claims_df)
    if pa:
        metrics["provider_archetypes"] = pa
    if ps:
        metrics["patient_segments"] = ps


def _expand_all_markets(market_filter: Any) -> Optional[Any]:
    """If market filter is or contains 'ALL', return concrete demo markets list; else return as-is."""
    if market_filter is None:
        return None
    if isinstance(market_filter, list):
        if any(str(m).upper() == "ALL" for m in market_filter if m):
            return DEMO_MARKETS_WHEN_ALL
        return market_filter if market_filter else None
    if str(market_filter).upper() == "ALL":
        return DEMO_MARKETS_WHEN_ALL
    return market_filter


def compute_general_baseline_from_database(
    tenant_id: UUID,
    start_date: date,
    end_date: date,
    db: Session,
) -> Dict[str, Any]:
    """Compute general baseline metrics from database claims_lines table
    
    Returns baseline metrics computed from actual database data only.
    Returns empty dict if no data exists.

    Uses DB aggregates for volumes (same as policy baselines) so counts are not
    truncated by in-memory row caps; optional bounded pull only for segmentation.
    """
    repo = CanonicalDataRepository(db)

    agg = repo.aggregate_claims_for_baseline(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
    )
    if not agg:
        return {}

    unique_members = int(agg["unique_members"])
    total_claims = int(agg["total_claims"])
    total_paid = float(agg["total_paid"])
    total_allowed = float(agg["total_allowed"])

    months = _baseline_calendar_months_inclusive(start_date, end_date)
    member_months = float(unique_members * months) if unique_members > 0 else 0.0

    utilization_per_1k = (total_claims / member_months * 1000) if member_months > 0 else 0.0
    cost_pmpm = (total_paid / member_months) if member_months > 0 else 0.0
    allowed_pmpm = (total_allowed / member_months) if member_months > 0 else 0.0

    out: Dict[str, Any] = {
        "member_months": member_months,
        "unique_members": unique_members,
        "total_claims": total_claims,
        "total_paid": total_paid,
        "total_allowed": total_allowed,
        "util_rate_total_per_1000_mm": float(utilization_per_1k),
        "allowed_pmpm_total": float(allowed_pmpm),
        "paid_pmpm_total": float(cost_pmpm),
        "claims_per_member": (total_claims / unique_members) if unique_members > 0 else 0.0,
        "cost_per_claim": (total_paid / total_claims) if total_claims > 0 else 0.0,
    }
    try:
        seg_df = repo.get_claims_lines(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            limit=_GENERAL_BASELINE_SEGMENTATION_ROW_CAP,
        )
        _merge_baseline_segmentation_from_claims_df(out, seg_df)
    except Exception:
        pass
    return out


def compute_policy_specific_baseline_from_database(
    tenant_id: UUID,
    policy_id: UUID,
    start_date: date,
    end_date: date,
    policy_scope: Dict[str, Any],
    db: Session,
    policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compute policy-specific baseline metrics from database claims_lines table
    
    Filters claims by policy scope (LOB, market, codes, etc.) and computes metrics.
    Extracts procedure codes and diagnosis codes from policy levers if not in policy_scope.
    Returns empty dict if no data exists.
    
    Args:
        tenant_id: Tenant ID
        policy_id: Policy ID
        start_date: Start date for baseline window
        end_date: End date for baseline window
        policy_scope: Policy scope dictionary (from policy.scope)
        db: Database session
        policy: Optional full policy object (used to extract codes from levers)
    """
    repo = CanonicalDataRepository(db)
    
    print(f"🔍 Baseline computation for policy {policy_id}")
    print(f"   Date range: {start_date} to {end_date}")
    print(f"   Tenant ID: {tenant_id}")
    
    # Use shared policy filter helper (consistent with observations, what-if, etc.)
    merged_procedure_codes = []
    merged_diagnosis_codes = []
    merged_service_categories = []
    lob_filter = None
    market_filter = None

    if policy:
        try:
            pf = build_policy_claims_filters(policy)
            merged_procedure_codes = pf.get("procedure_codes") or pf.get("cpt_codes") or []
            merged_service_categories = pf.get("service_categories") or ([pf["service_category"]] if pf.get("service_category") else [])
            merged_diagnosis_codes = pf.get("diagnosis_codes") or []
            lob_filter = pf.get("lob")
            market_filter = pf.get("markets") or pf.get("market")
            print(f"📋 Using merged codes: {len(merged_procedure_codes)} procedure codes, {len(merged_diagnosis_codes)} diagnosis codes, {len(merged_service_categories)} service categories")
        except Exception as e:
            print(f"⚠️  Error building policy filters: {e}")
            # Fallback to scope only
            if policy_scope:
                if policy_scope.get("procedure_codes"):
                    merged_procedure_codes = policy_scope["procedure_codes"] if isinstance(policy_scope["procedure_codes"], list) else [policy_scope["procedure_codes"]]
                if policy_scope.get("diagnosis_codes"):
                    merged_diagnosis_codes = policy_scope["diagnosis_codes"] if isinstance(policy_scope["diagnosis_codes"], list) else [policy_scope["diagnosis_codes"]]
                if policy_scope.get("service_categories"):
                    merged_service_categories = policy_scope["service_categories"] if isinstance(policy_scope["service_categories"], list) else [policy_scope["service_categories"]]
                elif policy_scope.get("service_category"):
                    merged_service_categories = [policy_scope["service_category"]]
                lob_filter = policy_scope.get("lob")
                market_filter = policy_scope.get("markets") or policy_scope.get("market")
    
    # Use aggregate query in DB (no row limit) so baseline scales to production volumes
    procedure_codes_for_query = merged_procedure_codes
    if not procedure_codes_for_query and policy_scope and policy_scope.get("target_codes"):
        target_codes = policy_scope["target_codes"]
        procedure_codes_for_query = target_codes if isinstance(target_codes, list) else [target_codes]
    # Normalize to strings so DB comparison matches (e.g. 72148 vs "72148")
    if procedure_codes_for_query:
        procedure_codes_for_query = [str(c).strip() for c in procedure_codes_for_query if c is not None and str(c).strip()]

    # Expand Market "ALL" to concrete demo markets (NYC, CHICAGO, LA, DFW) so the query matches claims
    market_for_query = _expand_all_markets(market_filter)

    print(f"   🔍 Aggregating in database (scales to any volume):")
    print(f"      LOB: {lob_filter}")
    print(f"      Market: {market_for_query if market_for_query is not None else market_filter}")
    print(f"      CPT codes: {merged_procedure_codes[:5] if merged_procedure_codes else 'None'}...")
    print(f"      Service categories: {merged_service_categories if merged_service_categories else 'None'}")

    agg = repo.aggregate_claims_for_baseline(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        lob=lob_filter,
        market=market_for_query,
        cpt_codes=procedure_codes_for_query if procedure_codes_for_query else None,
        hcpcs_codes=procedure_codes_for_query if procedure_codes_for_query else None,
        service_categories=merged_service_categories if merged_service_categories else None,
        diagnosis_codes=merged_diagnosis_codes if merged_diagnosis_codes else None,
    )

    if not agg:
        # Diagnostic: try count without code filters
        print(f"   ⚠️  No claims found with all filters. Checking without code filters...")
        count_no_codes = repo.count_claims_for_filters(
            tenant_id=tenant_id, start_date=start_date, end_date=end_date,
            lob=lob_filter, market=market_for_query,
        )
        if count_no_codes and count_no_codes > 0:
            print(f"   ℹ️  Found {count_no_codes} claims without procedure/service filters")
        else:
            count_basic = repo.count_claims_for_filters(
                tenant_id=tenant_id, start_date=start_date, end_date=end_date,
            )
            if count_basic and count_basic > 0:
                print(f"   ℹ️  Found {count_basic} claims with tenant+date only")
        print(f"   ⚠️  No claims data found for policy {policy_id} in date range {start_date} to {end_date}.")
        return {}

    total_claims = agg["total_claims"]
    total_paid = agg["total_paid"]
    total_allowed = agg["total_allowed"]
    unique_members = agg["unique_members"]

    print(f"   ✅ Aggregated {total_claims} claims, {unique_members} members (no row limit)")

    months = _baseline_calendar_months_inclusive(start_date, end_date)
    member_months = unique_members * months if unique_members > 0 else 0
    utilization_per_1k = (total_claims / member_months * 1000) if member_months > 0 else 0.0
    cost_pmpm = (total_paid / member_months) if member_months > 0 else 0.0
    allowed_pmpm = (total_allowed / member_months) if member_months > 0 else 0.0

    out = {
        "member_months": float(member_months),
        "unique_members": int(unique_members),
        "total_claims": int(total_claims),
        "total_paid": float(total_paid),
        "total_allowed": float(total_allowed),
        "util_rate_target_per_1000_mm": float(utilization_per_1k),
        "allowed_pmpm_target": float(allowed_pmpm),
        "paid_pmpm_target": float(cost_pmpm),
        "claims_per_member": (total_claims / unique_members) if unique_members > 0 else 0.0,
        "cost_per_claim": (total_paid / total_claims) if total_claims > 0 else 0.0,
        "policy_id": str(policy_id),
    }
    try:
        seg_df = repo.get_claims_lines(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            lob=lob_filter,
            market=market_for_query,
            limit=_POLICY_BASELINE_SEGMENTATION_ROW_CAP,
            cpt_codes=procedure_codes_for_query if procedure_codes_for_query else None,
            hcpcs_codes=procedure_codes_for_query if procedure_codes_for_query else None,
            service_categories=merged_service_categories if merged_service_categories else None,
            diagnosis_codes=merged_diagnosis_codes if merged_diagnosis_codes else None,
        )
        _merge_baseline_segmentation_from_claims_df(out, seg_df)
    except Exception:
        pass
    return out
