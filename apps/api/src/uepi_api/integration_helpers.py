"""Integration helpers for Phase 1 components"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date

from uepi_api.storage_data_periods import create_data_period, get_latest_baseline_period
from uepi_api.storage_policies import list_policies, get_policy
from uepi_api.storage_policy_versions import create_policy_version, get_latest_version


def determine_baseline_eligibility(
    tenant_id: UUID,
    period_start_date: str,
    period_end_date: str,
) -> tuple[bool, List[str]]:
    """Determine if a data period is baseline-eligible (pre-policy)
    
    A period is baseline-eligible if it ends before any policy's effective start date.
    
    Args:
        tenant_id: Tenant ID
        period_start_date: Period start date (ISO format)
        period_end_date: Period end date (ISO format)
        
    Returns:
        Tuple of (is_baseline_eligible, list of policy_ids effective during this period)
    """
    # Get all policies for the tenant
    policies = list_policies(tenant_id)
    
    policies_effective = []
    period_end = datetime.fromisoformat(period_end_date.replace('Z', '+00:00')).date()
    
    for policy in policies:
        policy_id = policy.get("policy_id") or policy.get("id")
        if not policy_id:
            continue
        
        # Get effective dates from policy
        effective_date_str = None
        logic = policy.get("logic", {})
        metadata = policy.get("metadata", {})
        
        # Check in logic.effective_period or metadata
        effective_period = logic.get("effective_period") or metadata.get("effective_period")
        if effective_period:
            effective_date_str = effective_period.get("start_date")
        
        # Also check at root level
        if not effective_date_str:
            effective_date_str = policy.get("effective_date")
        
        if effective_date_str:
            try:
                # Parse effective date
                if isinstance(effective_date_str, str):
                    effective_date = datetime.fromisoformat(effective_date_str.replace('Z', '+00:00')).date()
                else:
                    effective_date = effective_date_str
                
                # If period ends before policy starts, it's baseline-eligible
                # If period overlaps with policy, policy is effective during this period
                if period_end < effective_date:
                    # Period is before policy - baseline eligible (continue checking other policies)
                    continue
                else:
                    # Policy is effective during this period
                    policies_effective.append(str(policy_id))
            except (ValueError, AttributeError) as e:
                # If we can't parse the date, skip this policy
                print(f"Warning: Could not parse effective date for policy {policy_id}: {e}")
                continue
    
    # Period is baseline-eligible if no policies are effective during it
    is_baseline_eligible = len(policies_effective) == 0
    
    return is_baseline_eligible, policies_effective


def create_data_period_from_ingestion(
    tenant_id: UUID,
    ingestion_id: str,
    ingestion_metadata: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Create a data period from ingestion completion
    
    Args:
        tenant_id: Tenant ID
        ingestion_id: Ingestion ID (as UUID string)
        ingestion_metadata: Ingestion metadata (should contain date range info)
        
    Returns:
        Created data period document or None if creation failed
    """
    try:
        # Extract date range from ingestion metadata
        # Try multiple approaches to get date range:
        # 1. From curated_partitions (list of partition URIs)
        # 2. From coverage metadata (if available)
        # 3. Use current date as fallback
        
        curated_partitions = ingestion_metadata.get("curated_partitions", [])
        coverage = ingestion_metadata.get("coverage", {})
        
        dates = []
        
        # Try to extract from partitions
        if curated_partitions:
            for partition_uri in curated_partitions:
                parts = partition_uri.split("/")
                year = None
                month = None
                for part in parts:
                    if part.startswith("year="):
                        year = int(part.split("=")[1])
                    elif part.startswith("month="):
                        month = int(part.split("=")[1])
                if year and month:
                    # Approximate: use first day of month as start, last day as end
                    from calendar import monthrange
                    last_day = monthrange(year, month)[1]
                    dates.append((date(year, month, 1), date(year, month, last_day)))
        
        # Try to extract from coverage metadata
        if not dates and coverage:
            if "start_date" in coverage and "end_date" in coverage:
                try:
                    start_date_obj = datetime.fromisoformat(coverage["start_date"].replace('Z', '+00:00')).date()
                    end_date_obj = datetime.fromisoformat(coverage["end_date"].replace('Z', '+00:00')).date()
                    dates.append((start_date_obj, end_date_obj))
                except (ValueError, AttributeError):
                    pass
        
        # If we still don't have dates, use current date as fallback (last month)
        if not dates:
            today = date.today()
            # Use previous month as a reasonable default
            if today.month == 1:
                start_date_obj = date(today.year - 1, 12, 1)
                from calendar import monthrange
                end_date_obj = date(today.year - 1, 12, monthrange(today.year - 1, 12)[1])
            else:
                start_date_obj = date(today.year, today.month - 1, 1)
                from calendar import monthrange
                end_date_obj = date(today.year, today.month - 1, monthrange(today.year, today.month - 1)[1])
            dates.append((start_date_obj, end_date_obj))
            print(f"Warning: Using fallback date range for ingestion {ingestion_id}")
        
        # Use min start date and max end date
        start_date = min(d[0] for d in dates)
        end_date = max(d[1] for d in dates)
        
        # Determine baseline eligibility
        is_baseline_eligible, policies_effective = determine_baseline_eligibility(
            tenant_id=tenant_id,
            period_start_date=start_date.isoformat(),
            period_end_date=end_date.isoformat(),
        )
        
        # Determine period type (MONTHLY, QUARTERLY, YEARLY)
        period_type = "MONTHLY"
        days_diff = (end_date - start_date).days
        if days_diff > 90:
            period_type = "QUARTERLY"
        if days_diff > 300:
            period_type = "YEARLY"
        
        # Create data period
        period_data = {
            "period_type": period_type,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "ingestion_id": str(ingestion_id),  # Ensure it's a string
            "data_status": "COMPLETE",
            "baseline_eligible": is_baseline_eligible,
            "policies_effective": policies_effective,
            "metadata": {
                "ingestion_id": str(ingestion_id),
                "curated_partitions_count": len(curated_partitions),
            },
        }
        
        period = create_data_period(tenant_id=tenant_id, period_data=period_data)
        
        # Integration: Trigger baseline refresh if period is baseline-eligible
        if is_baseline_eligible:
            try:
                from uepi_api.baseline_refresh import should_refresh_baseline, refresh_baseline
                should_refresh, reason = should_refresh_baseline(tenant_id=tenant_id)
                if should_refresh:
                    refreshed_baseline = refresh_baseline(
                        tenant_id=tenant_id,
                        policy_id=None,  # General baseline
                        baseline_type="ROLLING",
                        window_months=12,
                        refresh_reason="NEW_DATA",
                    )
                    if refreshed_baseline:
                        print(f"Auto-refreshed baseline {refreshed_baseline.get('baseline_id')} due to new baseline-eligible period")
            except Exception as baseline_error:
                # Don't fail period creation if baseline refresh fails
                print(f"Warning: Failed to refresh baseline after period creation: {baseline_error}")
        
        return period
        
    except Exception as e:
        print(f"Error creating data period from ingestion {ingestion_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def _track_version_changes(old_policy: Dict[str, Any], new_policy: Dict[str, Any]) -> Dict[str, Any]:
    """Track changes between two policy snapshots (simplified diff)"""
    changes = {}
    # Simple diff for now, can be expanded
    for key in new_policy:
        if key not in old_policy:
            changes[key] = {"old": None, "new": new_policy[key]}
        elif new_policy[key] != old_policy[key]:
            changes[key] = {"old": old_policy[key], "new": new_policy[key]}
    for key in old_policy:
        if key not in new_policy:
            changes[key] = {"old": old_policy[key], "new": None}
    return changes


def create_policy_version_on_update(
    tenant_id: UUID,
    policy_id: UUID,
    old_policy: Dict[str, Any],
    new_policy: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Create a policy version when policy is updated
    
    Args:
        tenant_id: Tenant ID
        policy_id: Policy ID
        old_policy: Previous policy state
        new_policy: New policy state
        
    Returns:
        Created policy version document or None if creation failed
    """
    try:
        # Track changes between old and new policy
        changes = _track_version_changes(old_policy, new_policy)
        
        # Only create version if there are significant changes
        # For now, create version if any changes exist
        if not changes:
            return None
        
        # Extract effective dates from new policy
        logic = new_policy.get("logic", {})
        metadata = new_policy.get("metadata", {})
        effective_period = logic.get("effective_period") or metadata.get("effective_period") or {}
        
        effective_start_date = effective_period.get("start_date")
        if isinstance(effective_start_date, str):
            effective_start_date = datetime.fromisoformat(effective_start_date.replace('Z', '+00:00')).isoformat()
        elif effective_start_date:
            effective_start_date = effective_start_date.isoformat() if hasattr(effective_start_date, 'isoformat') else str(effective_start_date)
        else:
            effective_start_date = datetime.utcnow().isoformat()
        
        effective_end_date = effective_period.get("end_date")
        if effective_end_date:
            if isinstance(effective_end_date, str):
                effective_end_date = datetime.fromisoformat(effective_end_date.replace('Z', '+00:00')).isoformat()
            elif hasattr(effective_end_date, 'isoformat'):
                effective_end_date = effective_end_date.isoformat()
            else:
                effective_end_date = str(effective_end_date)
        
        # Create version data
        version_data = {
            "effective_start_date": effective_start_date,
            "effective_end_date": effective_end_date,
            "status": "ACTIVE",
            "change_description": f"Policy updated: {', '.join(list(changes.keys())[:3])}" if changes else "Policy updated",
            "changes_from_previous": changes,
            "policy_snapshot": new_policy,
        }
        
        version = create_policy_version(tenant_id=tenant_id, policy_id=policy_id, version_data=version_data)
        return version
        
    except Exception as e:
        print(f"Error creating policy version for policy {policy_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_initial_policy_version(
    tenant_id: UUID,
    policy_id: UUID,
    policy_data: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Create initial policy version when policy is created
    
    Args:
        tenant_id: Tenant ID
        policy_id: Policy ID
        policy_data: New policy data
        
    Returns:
        Created policy version document or None if creation failed
    """
    try:
        # Extract effective dates from policy
        logic = policy_data.get("logic", {})
        metadata = policy_data.get("metadata", {})
        effective_period = logic.get("effective_period") or metadata.get("effective_period") or {}
        
        effective_start_date = effective_period.get("start_date")
        if isinstance(effective_start_date, str):
            effective_start_date = datetime.fromisoformat(effective_start_date.replace('Z', '+00:00')).isoformat()
        elif effective_start_date:
            effective_start_date = effective_start_date.isoformat() if hasattr(effective_start_date, 'isoformat') else str(effective_start_date)
        else:
            effective_start_date = datetime.utcnow().isoformat()
        
        effective_end_date = effective_period.get("end_date")
        if effective_end_date:
            if isinstance(effective_end_date, str):
                effective_end_date = datetime.fromisoformat(effective_end_date.replace('Z', '+00:00')).isoformat()
            elif hasattr(effective_end_date, 'isoformat'):
                effective_end_date = effective_end_date.isoformat()
            else:
                effective_end_date = str(effective_end_date)
        
        # Create version data
        version_data = {
            "effective_start_date": effective_start_date,
            "effective_end_date": effective_end_date,
            "state": "ACTIVE",  # Use 'state' not 'status'
            "change_summary": "Initial policy version",
            "change_details": {"changes_from_previous": {}, "policy_snapshot": policy_data},
            "created_by": str(tenant_id),  # Use tenant_id as placeholder for created_by
            "created_at": datetime.utcnow().isoformat(),
        }
        
        version = create_policy_version(tenant_id=tenant_id, policy_id=policy_id, version_data=version_data)
        return version
        
    except Exception as e:
        print(f"Error creating initial policy version for policy {policy_id}: {e}")
        import traceback
        traceback.print_exc()
        return None
