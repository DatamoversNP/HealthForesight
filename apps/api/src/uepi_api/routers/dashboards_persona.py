"""Persona-specific dashboard endpoints"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.storage_policies import list_policies
from uepi_api.storage_observations import list_observations
from uepi_api.storage_analyses import list_analyses

router = APIRouter()


@router.get("/dashboards/executive")
async def get_executive_dashboard(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get executive dashboard data"""
    try:
        # Load policies
        policies = list_policies(current_user.tenant_id)
        
        # Calculate metrics
        active_policies = [p for p in policies if p.get('status') == 'ACTIVE']
        
        # Try to get observations if available
        try:
            from uepi_api.storage_observations import list_observations
            observations = list_observations(current_user.tenant_id)
            total_cost_impact = sum(
                o.get('comparisons', {}).get('vs_baseline', {}).get('change_from_baseline', 0)
                for o in observations
            )
            avg_utilization_change = 0
            if observations:
                total_util = sum(
                    o.get('metrics', {}).get('observed_percent_change', 0)
                    for o in observations
                )
                avg_utilization_change = total_util / len(observations)
        except ImportError:
            # Observations storage not available
            observations = []
            total_cost_impact = 0
            avg_utilization_change = 0
        
        # Get top risks (placeholder - would come from risk analysis)
        top_risks = []
        
        # What changed (placeholder)
        what_changed = []
        
        return {
            "summary": {
                "total_cost_impact": total_cost_impact,
                "avg_utilization_change": avg_utilization_change,
                "active_policies_count": len(active_policies),
                "decisions_pending": 0,  # Placeholder
                "cost_trend": "neutral",
                "utilization_trend": "neutral",
            },
            "top_risks": top_risks,
            "what_changed": what_changed,
            "performance": [],  # Will be populated from policy performance endpoint
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load executive dashboard: {str(e)}")


@router.get("/dashboards/policy-owner")
async def get_policy_owner_dashboard(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get policy owner dashboard data"""
    try:
        policies = list_policies(current_user.tenant_id)
        
        # Policies in flight (DRAFT, PROPOSED)
        policies_in_flight = [
            p for p in policies
            if p.get('status') in ['DRAFT', 'PROPOSED', 'MONITORING', 'ITERATING']
        ]
        
        return {
            "policies_in_flight": policies_in_flight,
            "assumptions_pending": [],  # Placeholder
            "approvals_pending": [],  # Placeholder
            "compliance_signals": [],  # Placeholder
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load policy owner dashboard: {str(e)}")


@router.get("/dashboards/analyst")
async def get_analyst_dashboard(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get analyst dashboard data"""
    try:
        # Try to get analyses if available
        try:
            from uepi_api.storage_analyses import list_analyses
            analyses = list_analyses(current_user.tenant_id)
            # Analysis queue (PENDING, RUNNING)
            analysis_queue = [
                a for a in analyses
                if a.get('status') in ['PENDING', 'RUNNING']
            ]
        except ImportError:
            # Analyses storage not available
            analysis_queue = []
        
        return {
            "analysis_queue": analysis_queue,
            "model_diagnostics": [],  # Placeholder
            "cohort_shortcuts": [],  # Placeholder
            "sensitivity_runs": [],  # Placeholder
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load analyst dashboard: {str(e)}")


@router.get("/dashboards/ops-clinical")
async def get_ops_clinical_dashboard(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Get ops/clinical dashboard data"""
    try:
        # Placeholder data - will be populated when behavioral signals are implemented
        return {
            "provider_behavior_clusters": [],
            "appeals_volume": [],
            "patient_deferral_signals": [],
            "access_risk_flags": [],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load ops/clinical dashboard: {str(e)}")

