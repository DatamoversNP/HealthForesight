"""Baseline refresh logic - Automatic baseline refresh and shift detection"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

from uepi_api.storage_baselines import (
    create_baseline,
    get_latest_baseline,
    list_baselines,
    update_baseline,
)
from uepi_api.storage_data_periods import (
    get_baseline_eligible_periods,
    list_data_periods,
    get_data_period,
)
from uepi_api.database import SessionLocal

# Avoid spamming "No baseline-eligible periods" when computing many policy baselines
_no_periods_warned: set = set()


def _get_policy_effective_date(policy: Optional[Dict[str, Any]]) -> Optional[date]:
    """Get policy effective date (activation) from policy dict for pre-policy baseline window."""
    if not policy:
        return None
    effective_period = policy.get("effective_period") or policy.get("metadata", {}).get("effective_period")
    if not effective_period:
        return None
    start_str = effective_period.get("start_date") if isinstance(effective_period, dict) else None
    if not start_str:
        return None
    try:
        if isinstance(start_str, date):
            return start_str
        return datetime.fromisoformat(str(start_str).replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        return None


def should_refresh_baseline(
    tenant_id: UUID,
    policy_id: Optional[UUID] = None,
) -> tuple[bool, Optional[str]]:
    """Determine if baseline should be refreshed
    
    Returns:
        Tuple of (should_refresh, reason)
    """
    # Get latest baseline
    latest_baseline = get_latest_baseline(tenant_id=tenant_id, policy_id=policy_id)
    
    # Get baseline-eligible periods
    eligible_periods = get_baseline_eligible_periods(tenant_id)
    
    if not eligible_periods:
        return (False, "No baseline-eligible periods available")
    
    # If no baseline exists, should create one
    if not latest_baseline:
        return (True, "No baseline exists - initial baseline creation")
    
    # Check if there are new periods since last baseline
    latest_baseline_computed_at = latest_baseline.get("computed_at")
    if latest_baseline_computed_at:
        try:
            baseline_time = datetime.fromisoformat(latest_baseline_computed_at.replace('Z', '+00:00'))
            new_periods = [
                p for p in eligible_periods
                if datetime.fromisoformat(p.get("ingestion_timestamp", "").replace('Z', '+00:00')) > baseline_time
            ]
            if new_periods:
                return (True, f"New baseline-eligible periods available ({len(new_periods)} new periods)")
        except (ValueError, AttributeError):
            pass
    
    # Check if baseline is older than refresh threshold (e.g., 90 days)
    if latest_baseline_computed_at:
        try:
            baseline_time = datetime.fromisoformat(latest_baseline_computed_at.replace('Z', '+00:00'))
            if (datetime.utcnow() - baseline_time.replace(tzinfo=None)).days > 90:
                return (True, "Baseline is older than 90 days - refresh recommended")
        except (ValueError, AttributeError):
            pass
    
    return (False, "Baseline is up to date")


def compute_baseline_metrics(
    tenant_id: UUID,
    data_period_ids: List[str],
    window_start_date: str,
    window_end_date: str,
    policy_id: Optional[UUID] = None,
    policy_scope: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """Compute baseline metrics from data periods
    
    Args:
        tenant_id: Tenant ID
        data_period_ids: List of data period IDs
        window_start_date: Window start date (ISO format)
        window_end_date: Window end date (ISO format)
        policy_id: Optional policy ID for policy-specific baseline
        policy_scope: Optional policy scope for filtering
        db: Optional database session (creates new if None)
    
    Returns:
        Dictionary with baseline metrics (empty dict if no data)
    """
    from uepi_api.database import SessionLocal
    
    # Create database session if not provided
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    
    try:
        # Load data periods
        periods = []
        for period_id in data_period_ids:
            period = get_data_period(tenant_id, period_id)
            if period:
                periods.append(period)
        
        if not periods:
            # Return default/empty metrics
            return {
                "total_members": 0,
                "total_claims": 0,
                "total_cost": 0.0,
                "utilization_per_1k": 0.0,
                "cost_per_member": 0.0,
                "cost_per_member_per_month": 0.0,
                "claims_per_member": 0.0,
                "data_periods_count": 0,
            }
        
        # NO MOCK DATA - Compute from database only
        # Parse dates
        if 'T' in window_start_date:
            start_date = datetime.fromisoformat(window_start_date.replace('Z', '+00:00')).date()
        else:
            start_date = datetime.fromisoformat(window_start_date).date()
        end_date = datetime.fromisoformat(window_end_date.replace('Z', '+00:00').replace('T', ' ').split()[0]).date() if 'T' in window_end_date else datetime.fromisoformat(window_end_date).date()
        
        # Use database computation service
        from uepi_api.services.database_baseline_computation import (
            compute_general_baseline_from_database,
            compute_policy_specific_baseline_from_database,
        )
        
        if policy_id and policy_scope:
            # Policy-specific baseline (pass policy for consistent scope+levers filtering)
            from uepi_api.storage_policies import get_policy
            policy_obj = get_policy(policy_id, tenant_id)
            metrics = compute_policy_specific_baseline_from_database(
                tenant_id=tenant_id,
                policy_id=policy_id,
                start_date=start_date,
                end_date=end_date,
                policy_scope=policy_scope,
                db=db,
                policy=policy_obj,
            )
        else:
            # General baseline
            metrics = compute_general_baseline_from_database(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date,
                db=db,
            )
        
        # Add metadata
        if metrics:
            metrics["data_periods_count"] = len(data_period_ids)
            metrics["window_start_date"] = window_start_date
            metrics["window_end_date"] = window_end_date
        
        # Return metrics (empty dict if no data - NO MOCK DATA)
        return metrics
    finally:
        if close_db:
            db.close()


def detect_baseline_shift(
    current_baseline: Dict[str, Any],
    previous_baseline: Dict[str, Any],
) -> Dict[str, Any]:
    """Detect shifts between two baselines
    
    Returns:
        Dictionary with shift detection results
    """
    current_metrics = current_baseline.get("baseline_metrics", {})
    previous_metrics = previous_baseline.get("baseline_metrics", {})
    
    if not current_metrics or not previous_metrics:
        return {
            "shift_detected": False,
            "significant_shift": False,
            "utilization_change_pct": 0.0,
            "cost_change_pct": 0.0,
            "reason": "Insufficient metrics for comparison",
        }
    
    # Compare utilization
    current_util = current_metrics.get("utilization_per_1k", 0.0)
    previous_util = previous_metrics.get("utilization_per_1k", 0.0)
    utilization_change_pct = 0.0
    if previous_util > 0:
        utilization_change_pct = ((current_util - previous_util) / previous_util) * 100
    
    # Compare cost
    current_cost_pmpm = current_metrics.get("cost_per_member_per_month", 0.0)
    previous_cost_pmpm = previous_metrics.get("cost_per_member_per_month", 0.0)
    cost_change_pct = 0.0
    if previous_cost_pmpm > 0:
        cost_change_pct = ((current_cost_pmpm - previous_cost_pmpm) / previous_cost_pmpm) * 100
    
    # Determine if shift is significant (threshold: 5% change)
    significant_shift = abs(utilization_change_pct) > 5.0 or abs(cost_change_pct) > 5.0
    shift_detected = abs(utilization_change_pct) > 0.01 or abs(cost_change_pct) > 0.01  # Any detectable change
    
    return {
        "shift_detected": shift_detected,
        "significant_shift": significant_shift,
        "utilization_change_pct": utilization_change_pct,
        "cost_change_pct": cost_change_pct,
        "current_utilization_per_1k": current_util,
        "previous_utilization_per_1k": previous_util,
        "current_cost_pmpm": current_cost_pmpm,
        "previous_cost_pmpm": previous_cost_pmpm,
    }


def refresh_baseline(
    tenant_id: UUID,
    policy_id: Optional[UUID] = None,
    baseline_type: str = "ROLLING",
    window_months: int = 12,
    refresh_reason: str = "NEW_DATA",
    db: Optional[Session] = None,
) -> Optional[Dict[str, Any]]:
    """Refresh baseline using available baseline-eligible data periods
    
    Args:
        tenant_id: Tenant ID
        policy_id: Optional policy ID for policy-specific baseline
        baseline_type: "ROLLING" or "FIXED"
        window_months: Number of months for rolling window (if ROLLING type)
        refresh_reason: Reason for refresh (NEW_DATA, MANUAL, POLICY_UPDATE, etc.)
    
    Returns:
        Created baseline document or None if refresh failed
    """
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True
    try:
        # Get policy effective date when policy_id is set (for pre-policy baseline window)
        policy_effective_date_iso = None
        policy = None
        if policy_id:
            from uepi_api.storage_policies import get_policy
            policy = get_policy(policy_id, tenant_id)
            eff = _get_policy_effective_date(policy)
            if eff:
                policy_effective_date_iso = eff.isoformat()

        # Get baseline-eligible periods (pre-policy when activation is set)
        eligible_periods = get_baseline_eligible_periods(tenant_id, policy_effective_date=policy_effective_date_iso)
        
        # If no baseline-eligible periods, try to compute baseline directly from database
        # This allows baselines to be created even if data periods haven't been set up yet
        if not eligible_periods:
            tid = str(tenant_id)
            if tid not in _no_periods_warned:
                _no_periods_warned.add(tid)
                print(f"Warning: No baseline-eligible periods available for tenant {tenant_id}")
                print(f"Attempting to compute baseline directly from database data...")
            
            # Compute baseline directly from database using date range
            from datetime import date, timedelta
            from uepi_api.services.database_baseline_computation import (
                compute_general_baseline_from_database,
                compute_policy_specific_baseline_from_database,
            )
            
            # Pre-policy window (before activation) when policy has effective_date; else last 12 months
            eff = _get_policy_effective_date(policy) if policy else None
            if eff:
                end_date = eff - timedelta(days=1)  # day before activation
                start_date = end_date - timedelta(days=365)
                if start_date >= end_date:
                    end_date = date.today()
                    start_date = end_date - timedelta(days=365)
            else:
                end_date = date.today()
                start_date = end_date - timedelta(days=365)

            # Clamp to actual demo data range so baselines find data (historical = 2022-01 to 2025-06)
            DEMO_DATA_START = date(2022, 1, 1)
            DEMO_DATA_END = date(2025, 6, 30)
            start_date = max(start_date, DEMO_DATA_START)
            end_date = min(end_date, DEMO_DATA_END)
            if start_date >= end_date:
                print(f"   Skipping: baseline window would be empty after clamping to data range [{DEMO_DATA_START}, {DEMO_DATA_END}]")
                return None

            try:
                if policy_id:
                    if not policy:
                        from uepi_api.storage_policies import get_policy
                        policy = get_policy(policy_id, tenant_id)
                    policy_scope = policy.get("scope", {}) if policy else {}

                    baseline_metrics = compute_policy_specific_baseline_from_database(
                        tenant_id=tenant_id,
                        policy_id=policy_id,
                        start_date=start_date,
                        end_date=end_date,
                        policy_scope=policy_scope,
                        db=db,
                        policy=policy,
                    )
                else:
                    baseline_metrics = compute_general_baseline_from_database(
                        tenant_id=tenant_id,
                        start_date=start_date,
                        end_date=end_date,
                        db=db,
                    )
                
                # If we have metrics, create baseline
                if baseline_metrics and len(baseline_metrics) > 0:
                    print(f"Computed baseline metrics directly from database")
                    # Create baseline with computed metrics
                    baseline_data = {
                        "baseline_type": baseline_type,
                        "window_start_date": start_date.isoformat(),
                        "window_end_date": end_date.isoformat(),
                        "data_period_ids": [],  # Empty since we computed directly
                        "baseline_metrics": baseline_metrics,
                        "refresh_reason": refresh_reason,
                        "policy_id": policy_id,
                    }
                    input_refs = {"policy_id": str(policy_id) if policy_id else None, "data_period_ids": []}
                    config_snapshot = {"window_start_date": baseline_data["window_start_date"], "window_end_date": baseline_data["window_end_date"]}
                    baseline = create_baseline(tenant_id=tenant_id, baseline_data=baseline_data, input_refs=input_refs, config_snapshot=config_snapshot)
                    return baseline
                else:
                    print(f"No data found in database for baseline computation")
                    return None
            except Exception as e:
                print(f"Error computing baseline from database: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        # Sort periods by end_date (most recent first)
        eligible_periods.sort(key=lambda p: p.get("end_date", ""), reverse=True)
        
        # Determine window dates
        if baseline_type == "ROLLING":
            # Use last N months of data
            if eligible_periods:
                latest_end_date = datetime.fromisoformat(eligible_periods[0].get("end_date", "").replace('Z', '+00:00')).date()
                window_end_date = latest_end_date
                window_start_date = window_end_date - timedelta(days=window_months * 30)
                window_start_date_str = window_start_date.isoformat()
                window_end_date_str = window_end_date.isoformat()
            else:
                return None
        else:  # FIXED
            # Use all available periods
            if eligible_periods:
                window_start_date = datetime.fromisoformat(eligible_periods[-1].get("start_date", "").replace('Z', '+00:00')).date()
                window_end_date = datetime.fromisoformat(eligible_periods[0].get("end_date", "").replace('Z', '+00:00')).date()
                window_start_date_str = window_start_date.isoformat()
                window_end_date_str = window_end_date.isoformat()
            else:
                return None
        
        # Filter periods to window
        window_periods = [
            p for p in eligible_periods
            if (p.get("start_date") <= window_end_date_str and
                p.get("end_date") >= window_start_date_str)
        ]
        
        if not window_periods:
            print(f"Warning: No periods in window for baseline refresh")
            return None
        
        data_period_ids = [p.get("period_id") for p in window_periods]
        
        # Get policy scope if policy_id is provided
        policy_scope = None
        if policy_id:
            from uepi_api.storage_policies import get_policy
            policy = get_policy(policy_id, tenant_id)
            if policy:
                policy_scope = policy.get("scope", {})
        
        # Compute baseline metrics
        baseline_metrics = compute_baseline_metrics(
            tenant_id=tenant_id,
            data_period_ids=data_period_ids,
            window_start_date=window_start_date_str,
            window_end_date=window_end_date_str,
            policy_id=policy_id,
            policy_scope=policy_scope,
            db=db,
        )
        
        # Get previous baseline for versioning and shift detection
        previous_baseline = get_latest_baseline(tenant_id=tenant_id, policy_id=policy_id)
        next_version = 1
        parent_baseline_id = None
        shift_summary = {}
        
        if previous_baseline:
            next_version = previous_baseline.get("version", 0) + 1
            parent_baseline_id = previous_baseline.get("baseline_id")
            
            # Detect shift
            # Note: We'll create a temporary current baseline dict for comparison
            temp_current = {
                "baseline_metrics": baseline_metrics,
            }
            shift_result = detect_baseline_shift(temp_current, previous_baseline)
            shift_summary = shift_result
        
        # Create new baseline
        baseline_data = {
            "version": next_version,
            "baseline_type": baseline_type,
            "window_start_date": window_start_date_str,
            "window_end_date": window_end_date_str,
            "data_period_ids": data_period_ids,
            "baseline_metrics": baseline_metrics,
            "computed_by": "system",
            "parent_baseline_id": parent_baseline_id,
            "policy_id": str(policy_id) if policy_id else None,
            "shift_detected": shift_summary.get("shift_detected", False),
            "shift_summary": shift_summary,
            "refresh_reason": refresh_reason,
        }
        
        input_refs = {"policy_id": baseline_data.get("policy_id"), "parent_baseline_id": baseline_data.get("parent_baseline_id"), "data_period_ids": baseline_data.get("data_period_ids", [])}
        config_snapshot = {"window_start_date": baseline_data.get("window_start_date"), "window_end_date": baseline_data.get("window_end_date")}
        baseline = create_baseline(tenant_id=tenant_id, baseline_data=baseline_data, input_refs=input_refs, config_snapshot=config_snapshot)
        
        return baseline
        
    except Exception as e:
        print(f"Error refreshing baseline for tenant {tenant_id}: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if should_close_db and db:
            db.close()