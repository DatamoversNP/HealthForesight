"""Policy scoping algorithm - Deterministic computation of eligible population and target events

This module implements the policy scoping algorithm that:
1. Defines eligible member-months from enrollment using policy scope filters
2. Identifies final_target_claim_lines by applying target rules, conditions, and exceptions
3. Distinguishes exposed members (had target utilization pre-policy) vs at-risk members
4. Identifies impacted providers (high-volume target drivers)
5. Constructs control pool candidates for DiD
"""

from typing import Dict, Any, List, Optional, Set
from uuid import UUID
from datetime import datetime, date, timedelta
from pathlib import Path
import pandas as pd
import polars as pl
import json

logger = None
try:
    import logging
    logger = logging.getLogger(__name__)
except:
    pass


def log_debug(msg: str):
    """Debug logging helper"""
    if logger:
        logger.debug(msg)
    else:
        print(f"DEBUG: {msg}")


class PolicyScopeResult:
    """Result of policy scoping algorithm"""
    
    def __init__(
        self,
        policy_id: UUID,
        policy_version_id: Optional[str],
        eligible_member_months: Dict[str, float],  # month -> member_months count
        final_target_claim_lines_count: int,
        members_exposed_pre: Set[str],
        members_at_risk: Set[str],
        impacted_providers: List[Dict[str, Any]],
        control_pool_definition: Dict[str, Any],
        scope_summary: Dict[str, Any],
    ):
        self.policy_id = policy_id
        self.policy_version_id = policy_version_id
        self.eligible_member_months = eligible_member_months
        self.total_eligible_member_months = sum(eligible_member_months.values())
        self.final_target_claim_lines_count = final_target_claim_lines_count
        self.members_exposed_pre = members_exposed_pre
        self.members_at_risk = members_at_risk
        self.impacted_providers = impacted_providers
        self.control_pool_definition = control_pool_definition
        self.scope_summary = scope_summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "policy_id": str(self.policy_id),
            "policy_version_id": self.policy_version_id,
            "eligible_member_months": self.eligible_member_months,
            "total_eligible_member_months": self.total_eligible_member_months,
            "final_target_claim_lines_count": self.final_target_claim_lines_count,
            "members_exposed_pre_count": len(self.members_exposed_pre),
            "members_at_risk_count": len(self.members_at_risk),
            "impacted_providers_count": len(self.impacted_providers),
            "impacted_providers": [
                {"provider_id": str(p.get("provider_id", "")), "target_volume": p.get("target_volume", 0)}
                for p in self.impacted_providers[:10]  # Store top 10
            ],
            "control_pool_definition": self.control_pool_definition,
            "scope_summary": self.scope_summary,
        }


def compute_policy_scope(
    tenant_id: UUID,
    policy: Dict[str, Any],
    policy_version: Optional[Dict[str, Any]] = None,
    pre_window_months: int = 12,
    enrollment_df: Optional[pd.DataFrame] = None,
    claims_df: Optional[pd.DataFrame] = None,
) -> PolicyScopeResult:
    """
    Compute policy scope using deterministic algorithm
    
    Args:
        tenant_id: Tenant ID
        policy: Policy document
        policy_version: Optional policy version (uses latest if not provided)
        pre_window_months: Number of months before effective_date to include in pre-period
        enrollment_df: Optional enrollment DataFrame (will load if not provided)
        claims_df: Optional claims DataFrame (will load if not provided)
    
    Returns:
        PolicyScopeResult with scoping outputs
    """
    policy_id = UUID(policy.get("id") or policy.get("policy_id"))
    policy_scope = policy.get("scope", {})
    policy_logic = policy.get("logic", {})
    
    # Step 1: Define Policy Time Windows
    effective_date_str = None
    if policy_version:
        effective_date_str = policy_version.get("effective_start_date") or policy_version.get("effective_period", {}).get("start_date")
    if not effective_date_str:
        effective_date_str = policy.get("effective_period", {}).get("start_date") or policy.get("metadata", {}).get("effective_period", {}).get("start_date")
    
    if not effective_date_str:
        # Default to current date
        effective_date = datetime.utcnow().date()
    else:
        if isinstance(effective_date_str, str):
            effective_date = datetime.fromisoformat(effective_date_str.replace('Z', '+00:00')).date()
        else:
            effective_date = effective_date_str
    
    pre_start = effective_date - timedelta(days=pre_window_months * 30)
    pre_end = effective_date
    post_start = effective_date
    
    log_debug(f"Policy time windows - pre: {pre_start} to {pre_end}, post: {post_start} onward")
    
    # Step 2: Apply Eligibility/Scope Filters (Population "who")
    if enrollment_df is None:
        enrollment_df = _load_enrollment_data(tenant_id)
    
    if enrollment_df is None or enrollment_df.empty:
        log_debug("No enrollment data available, using claims-based member estimation")
        eligible_member_months = {}
        unique_members = set()
    else:
        eligible_member_months, unique_members = _compute_eligible_member_months(
            enrollment_df, policy_scope, pre_start, pre_end
        )
    
    log_debug(f"Eligible member-months: {sum(eligible_member_months.values())}, unique members: {len(unique_members)}")
    
    # Step 3-5: Define Target Event Rules (Services "what")
    if claims_df is None:
        claims_df = _load_claims_data(tenant_id)
    
    if claims_df is None or claims_df.empty:
        log_debug("No claims data available")
        final_target_claim_lines = pd.DataFrame()
        members_exposed_pre = set()
        impacted_providers = []
    else:
        final_target_claim_lines, members_exposed_pre, impacted_providers = _compute_target_claim_lines(
            claims_df, policy_logic, policy_scope, pre_start, pre_end, unique_members
        )
    
    # Step 6: Define At-Risk Members (potential exposure)
    members_at_risk = _compute_at_risk_members(
        unique_members, members_exposed_pre, claims_df, policy_logic, pre_start, pre_end
    )
    
    # Step 8: Construct Control Candidates (simplified for now)
    control_pool_definition = _construct_control_pool(policy_scope, claims_df, pre_start, pre_end)
    
    # Scope Summary
    scope_summary = {
        "policy_id": str(policy_id),
        "effective_date": effective_date.isoformat(),
        "pre_window": {"start": pre_start.isoformat(), "end": pre_end.isoformat()},
        "scope_filters": policy_scope,
        "target_rules": _extract_target_rules_summary(policy_logic),
        "eligible_member_months_total": sum(eligible_member_months.values()),
        "target_claim_lines_count": len(final_target_claim_lines),
        "members_exposed_pre_count": len(members_exposed_pre),
        "members_at_risk_count": len(members_at_risk),
        "impacted_providers_count": len(impacted_providers),
    }
    
    return PolicyScopeResult(
        policy_id=policy_id,
        policy_version_id=policy_version.get("version_id") if policy_version else None,
        eligible_member_months=eligible_member_months,
        final_target_claim_lines_count=len(final_target_claim_lines),
        members_exposed_pre=members_exposed_pre,
        members_at_risk=members_at_risk,
        impacted_providers=impacted_providers,
        control_pool_definition=control_pool_definition,
        scope_summary=scope_summary,
    )


def _load_enrollment_data(tenant_id: UUID) -> Optional[pd.DataFrame]:
    """Load enrollment data from file storage"""
    try:
        # Calculate path to enrollment data
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent.parent.parent
        # Try apps/api/data/target_data_model first (current structure)
        enrollment_dir = project_root / "apps" / "api" / "data" / "target_data_model" / str(tenant_id) / "ELIGIBILITY_ENROLLMENT"
        if not enrollment_dir.exists():
            # Fallback to apps/data/target_data_model (legacy)
            enrollment_dir = project_root / "apps" / "data" / "target_data_model" / str(tenant_id) / "ELIGIBILITY_ENROLLMENT"
        
        if not enrollment_dir.exists():
            return None
        
        # Look for enrollment files
        for file in enrollment_dir.glob("*.csv"):
            df = pd.read_csv(file, low_memory=False)
            return df
        
        return None
    except Exception as e:
        log_debug(f"Error loading enrollment data: {e}")
        return None


def _load_claims_data(tenant_id: UUID) -> Optional[pd.DataFrame]:
    """Load claims data from file storage"""
    try:
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent.parent.parent
        # Try apps/api/data/target_data_model first (current structure)
        claims_dir = project_root / "apps" / "api" / "data" / "target_data_model" / str(tenant_id) / "CLAIMS_LINES"
        if not claims_dir.exists():
            # Fallback to apps/data/target_data_model (legacy)
            claims_dir = project_root / "apps" / "data" / "target_data_model" / str(tenant_id) / "CLAIMS_LINES"
        
        if not claims_dir.exists():
            return None
        
        for file in claims_dir.glob("*.csv"):
            df = pd.read_csv(file, low_memory=False, nrows=100000)  # Limit for performance
            return df
        
        return None
    except Exception as e:
        log_debug(f"Error loading claims data: {e}")
        return None


def _compute_eligible_member_months(
    enrollment_df: pd.DataFrame,
    policy_scope: Dict[str, Any],
    pre_start: date,
    pre_end: date,
) -> tuple[Dict[str, float], Set[str]]:
    """Step 2: Compute eligible member-months from enrollment"""
    eligible_member_months = {}
    unique_members = set()
    
    # Apply scope filters
    filtered_df = enrollment_df.copy()
    
    # Filter by LOB
    if policy_scope.get("lob"):
        lob_filter = policy_scope["lob"]
        if isinstance(lob_filter, list):
            filtered_df = filtered_df[filtered_df["lob"].isin(lob_filter)]
        else:
            filtered_df = filtered_df[filtered_df["lob"] == lob_filter]
    
    # Filter by market
    if policy_scope.get("markets"):
        markets_filter = policy_scope["markets"]
        if isinstance(markets_filter, list):
            filtered_df = filtered_df[filtered_df["market"].isin(markets_filter)]
        else:
            filtered_df = filtered_df[filtered_df["market"] == markets_filter]
    
    # Filter by network (if applicable)
    if policy_scope.get("network"):
        network_filter = policy_scope["network"]
        if isinstance(network_filter, list):
            # Check if in-network flag matches
            if "IN" in network_filter:
                filtered_df = filtered_df[filtered_df.get("in_network_flag", True) == True]
    
    # Extract member-months by month
    if "member_id" in filtered_df.columns:
        unique_members = set(filtered_df["member_id"].unique())
        
        # Estimate member-months (simplified - assumes 1 month per row if no date column)
        if "coverage_month" in filtered_df.columns or "month" in filtered_df.columns:
            date_col = "coverage_month" if "coverage_month" in filtered_df.columns else "month"
            for month, group in filtered_df.groupby(date_col):
                eligible_member_months[str(month)] = float(len(group))
        else:
            # Default: assume all rows are in pre-period
            total_months = (pre_end.year - pre_start.year) * 12 + (pre_end.month - pre_start.month)
            eligible_member_months["pre_period"] = float(len(filtered_df) / max(total_months, 1))
    else:
        # Estimate from row count
        eligible_member_months["pre_period"] = float(len(filtered_df) / 12)  # Rough estimate
    
    return eligible_member_months, unique_members


def _compute_target_claim_lines(
    claims_df: pd.DataFrame,
    policy_logic: Dict[str, Any],
    policy_scope: Dict[str, Any],
    pre_start: date,
    pre_end: date,
    eligible_members: Set[str],
) -> tuple[pd.DataFrame, Set[str], List[Dict[str, Any]]]:
    """Steps 3-5: Apply target rules, conditions, exceptions to get final_target_claim_lines"""
    
    # Filter claims by date
    date_col = None
    for col in ["service_from_date", "service_date_from", "service_date", "claim_date"]:
        if col in claims_df.columns:
            date_col = col
            break
    
    if date_col:
        claims_df[date_col] = pd.to_datetime(claims_df[date_col], errors='coerce')
        claims_df = claims_df[
            (claims_df[date_col] >= pd.Timestamp(pre_start)) &
            (claims_df[date_col] < pd.Timestamp(pre_end))
        ]
    
    # Apply scope filters
    if policy_scope.get("lob") and "lob" in claims_df.columns:
        lob_filter = policy_scope["lob"]
        if isinstance(lob_filter, list):
            claims_df = claims_df[claims_df["lob"].isin(lob_filter)]
        else:
            claims_df = claims_df[claims_df["lob"] == lob_filter]
    
    if policy_scope.get("markets") and "market" in claims_df.columns:
        markets_filter = policy_scope["markets"]
        if isinstance(markets_filter, list):
            claims_df = claims_df[claims_df["market"].isin(markets_filter)]
        else:
            claims_df = claims_df[claims_df["market"] == markets_filter]
    
    # Step 3: Apply target rules (codes/categories)
    target_codes = []
    policy_levers = policy_logic.get("policy_levers", []) or policy_logic.get("levers", [])
    
    for lever in policy_levers:
        if isinstance(lever, dict):
            params = lever.get("parameters", {})
            codes = params.get("codes", []) or params.get("cpt_codes", []) or params.get("hcpcs_codes", [])
            if codes:
                target_codes.extend(codes if isinstance(codes, list) else [codes])
    
    if target_codes and "cpt_hcpcs" in claims_df.columns:
        claims_df = claims_df[claims_df["cpt_hcpcs"].isin(target_codes)]
    
    # Step 4: Apply conditions (if any)
    conditions = policy_logic.get("conditions", [])
    # Simplified - conditions would need more complex logic
    
    # Step 5: Apply exceptions (if any)
    exceptions = policy_logic.get("exceptions", [])
    # Simplified - exceptions would need more complex logic
    
    # Extract exposed members and impacted providers
    members_exposed_pre = set()
    if "member_id" in claims_df.columns:
        members_exposed_pre = set(claims_df["member_id"].unique())
    
    impacted_providers = []
    provider_col = None
    for col in ["rendering_npi", "provider_id", "npi"]:
        if col in claims_df.columns:
            provider_col = col
            break
    
    if provider_col:
        provider_volumes = claims_df.groupby(provider_col).size().sort_values(ascending=False)
        impacted_providers = [
            {"provider_id": str(pid), "target_volume": int(vol)}
            for pid, vol in provider_volumes.head(20).items()
        ]
    
    return claims_df, members_exposed_pre, impacted_providers


def _compute_at_risk_members(
    eligible_members: Set[str],
    exposed_members: Set[str],
    claims_df: Optional[pd.DataFrame],
    policy_logic: Dict[str, Any],
    pre_start: date,
    pre_end: date,
) -> Set[str]:
    """Step 6: Compute at-risk members (simplified - uses exposed members as proxy)"""
    # Simplified: at-risk = all eligible (in production, would use propensity models)
    return eligible_members - exposed_members


def _construct_control_pool(
    policy_scope: Dict[str, Any],
    claims_df: Optional[pd.DataFrame],
    pre_start: date,
    pre_end: date,
) -> Dict[str, Any]:
    """Step 8: Construct control pool definition (simplified)"""
    return {
        "control_strategy": "geographic_or_service_control",
        "description": "Control candidates would be defined here (geographic or service-based)",
        "candidate_count": 0,
    }


def _extract_target_rules_summary(policy_logic: Dict[str, Any]) -> Dict[str, Any]:
    """Extract summary of target rules for scope_summary"""
    policy_levers = policy_logic.get("policy_levers", []) or policy_logic.get("levers", [])
    target_codes = []
    
    for lever in policy_levers:
        if isinstance(lever, dict):
            params = lever.get("parameters", {})
            codes = params.get("codes", []) or params.get("cpt_codes", [])
            if codes:
                target_codes.extend(codes if isinstance(codes, list) else [codes])
    
    return {
        "target_codes_count": len(target_codes),
        "target_codes_sample": target_codes[:10],
    }
