"""Dashboard API endpoints - Executive dashboard data aggregation - Database-driven, Enterprise-grade"""
from typing import Annotated, Optional
from uuid import UUID
from datetime import datetime, timedelta, date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, distinct

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.database import get_db
from uepi_api.storage_policies import list_policies
from uepi_api.storage_analyses import list_analyses
from uepi_api.storage_observations import list_observations
from uepi_api.repositories.canonical_data import CanonicalDataRepository
from uepi_api.models.canonical_data import ClaimsLineDB, EnrollmentRecordDB

router = APIRouter()


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    db: Session = Depends(get_db),
):
    """Get executive dashboard summary with key metrics - Database-driven, Enterprise-grade"""
    try:
        # Load all relevant data with error handling
        print(f"DEBUG get_dashboard_summary: Loading data for tenant {current_user.tenant_id}")
        
        # ========== DATABASE-DRIVEN METRICS ==========
        # Get real member counts, claim volumes, and cost data from database
        repo = CanonicalDataRepository(db)
        member_count = 0
        total_claims_count = 0
        total_paid_amount = 0.0
        total_allowed_amount = 0.0
        claims_date_range = {"start": None, "end": None}
        
        try:
            # Get unique member count from enrollment or claims
            member_count = db.query(func.count(distinct(ClaimsLineDB.member_id))).filter(
                ClaimsLineDB.tenant_id == current_user.tenant_id
            ).scalar() or 0
            
            # Get claims statistics from last 12 months
            twelve_months_ago = date.today() - timedelta(days=365)
            claims_stats = db.query(
                func.count(ClaimsLineDB.claim_line_id).label('total_claims'),
                func.sum(ClaimsLineDB.paid_amount).label('total_paid'),
                func.sum(ClaimsLineDB.allowed_amount).label('total_allowed'),
                func.min(ClaimsLineDB.service_date).label('earliest_date'),
                func.max(ClaimsLineDB.service_date).label('latest_date')
            ).filter(
                and_(
                    ClaimsLineDB.tenant_id == current_user.tenant_id,
                    ClaimsLineDB.service_date >= twelve_months_ago
                )
            ).first()
            
            if claims_stats:
                total_claims_count = claims_stats.total_claims or 0
                total_paid_amount = float(claims_stats.total_paid or 0)
                total_allowed_amount = float(claims_stats.total_allowed or 0)
                if claims_stats.earliest_date:
                    claims_date_range["start"] = claims_stats.earliest_date.isoformat()
                if claims_stats.latest_date:
                    claims_date_range["end"] = claims_stats.latest_date.isoformat()
            
            print(f"DEBUG get_dashboard_summary: Database metrics - Members: {member_count}, Claims: {total_claims_count}, Paid: ${total_paid_amount:,.2f}")
            if total_paid_amount == 0 and member_count == 0:
                print("DEBUG get_dashboard_summary: Actuals will be 0 - no claims/members in DB for cost trend.")
        except Exception as e:
            print(f"WARNING get_dashboard_summary: Could not load database metrics: {e}")
            import traceback
            traceback.print_exc()
        
        # ========== POLICY AND ANALYSIS DATA ==========
        try:
            policies = list_policies(current_user.tenant_id)
            print(f"DEBUG get_dashboard_summary: Loaded {len(policies)} policies")
        except Exception as e:
            print(f"ERROR get_dashboard_summary: Failed to load policies: {e}")
            policies = []
        
        try:
            analyses = list_analyses(current_user.tenant_id)
            print(f"DEBUG get_dashboard_summary: Loaded {len(analyses)} analyses")
        except Exception as e:
            print(f"ERROR get_dashboard_summary: Failed to load analyses: {e}")
            analyses = []
        
        try:
            observations = list_observations(current_user.tenant_id)
            print(f"DEBUG get_dashboard_summary: Loaded {len(observations)} observations")
        except Exception as e:
            print(f"ERROR get_dashboard_summary: Failed to load observations: {e}")
            observations = []
        
        # ========== GENERAL (PRE-POLICY) BASELINE ==========
        general_baseline = None
        try:
            from uepi_api.storage_baselines import get_latest_baseline
            baseline = get_latest_baseline(current_user.tenant_id, policy_id=None)
            if baseline:
                bm = baseline.get("baseline_metrics") or baseline.get("metrics") or {}
                util = (
                    bm.get("util_rate_total_per_1000_mm")
                    or bm.get("util_rate_target_per_1000_mm")
                    or bm.get("utilization_per_1k")
                )
                cost = (
                    bm.get("allowed_pmpm_total")
                    or bm.get("paid_pmpm_total")
                    or bm.get("allowed_pmpm_target")
                    or bm.get("paid_pmpm_target")
                    or bm.get("cost_pmpm")
                )
                if util is not None or cost is not None:
                    general_baseline = {
                        "utilization_per_1k": round(float(util or 0), 2),
                        "cost_pmpm": round(float(cost or 0), 2),
                        "member_months": bm.get("member_months"),
                        "unique_members": bm.get("unique_members"),
                        "window_start": baseline.get("window_start_date"),
                        "window_end": baseline.get("window_end_date"),
                    }
        except Exception as e:
            print(f"WARNING get_dashboard_summary: Could not load general baseline: {e}")
        
        # Calculate key metrics (normalize status for comparison)
        def _norm(s):
            return (s or "").strip().upper()
        active_policies = [p for p in policies if _norm(p.get("status")) == "ACTIVE"]
        total_policies = len(policies)
        
        # Recent analyses (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_analyses = [
            a for a in analyses
            if a.get("created_at") and datetime.fromisoformat(a.get("created_at").replace("Z", "+00:00")) > thirty_days_ago
        ]
        
        # Completed analyses
        completed_analyses = [a for a in analyses if a.get("status") == "COMPLETED"]
        
        # ========== ENTERPRISE-GRADE BUSINESS METRICS ==========
        # Calculate cost impact from observations (database-driven)
        total_cost_impact = 0.0
        total_cost_savings = 0.0  # Negative cost impact = savings
        total_utilization_change = 0.0
        total_utilization_reduction = 0.0  # Only negative changes (reductions)
        policy_performance = []
        annualized_savings = 0.0
        roi_estimate = 0.0
        
        for obs in observations:
            metrics = obs.get("metrics", {})
            comparisons = obs.get("comparisons", {})
            
            # Cost impact (from database observations)
            vs_baseline = comparisons.get("vs_baseline", {})
            if vs_baseline:
                # Use cost_change_pmpm for accurate PMPM calculations
                cost_change_pmpm = vs_baseline.get("cost_change_pmpm", 0) or vs_baseline.get("change_from_baseline", 0)
                # Calculate total impact: PMPM * member_months
                member_months = vs_baseline.get("baseline_member_months") or (member_count * 1)  # Default to 1 month
                cost_change = cost_change_pmpm * member_months
                total_cost_impact += cost_change
                if cost_change < 0:  # Negative = savings
                    total_cost_savings += abs(cost_change)
            
            # Utilization change (from database observations)
            utilization_change = metrics.get("observed_percent_change", 0) or metrics.get("utilization_change_pct", 0)
            total_utilization_change += utilization_change
            if utilization_change < 0:  # Negative = reduction
                total_utilization_reduction += abs(utilization_change)
            
            # Policy performance - handle both UUID and string policy IDs
            policy_id = obs.get("policy_id")
            if policy_id:
                # Try to find policy by matching id or policy_id (handles both UUID and string IDs)
                policy = None
                policy_id_str = str(policy_id)
                for p in policies:
                    p_id = str(p.get("id") or p.get("policy_id", ""))
                    if p_id == policy_id_str:
                        policy = p
                        break
                
                if policy:
                    policy_performance.append({
                        "policy_id": policy_id,
                        "policy_name": policy.get("name") or policy.get("policy_name", "Unknown"),
                        "utilization_change_pct": utilization_change,
                        "cost_impact": cost_change if vs_baseline else 0,
                        "observation_date": obs.get("computed_at"),
                    })
        
        # If no observations, try to use predicted impact data for dashboard
        if not observations or not policy_performance:
            try:
                from uepi_api.storage_policy_predicted_impact import get_predicted_impact
                for policy in policies[:10]:  # Limit to top 10 for performance
                    policy_id = policy.get("id") or policy.get("policy_id")
                    if not policy_id:
                        continue
                    try:
                        predicted_impact = get_predicted_impact(policy_id, current_user.tenant_id)
                        if predicted_impact:
                            metrics = predicted_impact.get("metrics", {})
                            utilization_change = metrics.get("utilization_change_pct", 0)
                            cost_change_pmpm = metrics.get("cost_change_pmpm", 0)
                            # Estimate total cost impact (rough calculation)
                            cost_change = cost_change_pmpm * 10000  # Rough estimate for 10k members
                            
                            total_utilization_change += utilization_change
                            total_cost_impact += cost_change
                            
                            policy_performance.append({
                                "policy_id": str(policy_id),
                                "policy_name": policy.get("name") or policy.get("policy_name", "Unknown"),
                                "utilization_change_pct": utilization_change,
                                "cost_impact": cost_change,
                                "observation_date": predicted_impact.get("predicted_at"),
                                "is_predicted": True,  # Mark as predicted data
                            })
                    except Exception as e:
                        # Skip if predicted impact not available for this policy
                        import traceback
                        print(f"Warning: Could not load predicted impact for policy {policy_id}: {e}")
                        traceback.print_exc()
                        continue
            except Exception as e:
                # If the import itself fails, just continue without predicted impact
                import traceback
                print(f"Warning: Could not import predicted impact storage: {e}")
                traceback.print_exc()
                pass
        
        # ========== CALCULATE ENTERPRISE METRICS ==========
        # Average metrics
        num_data_points = len(observations) if observations else len([p for p in policy_performance if not p.get("is_predicted")])
        if not num_data_points:
            num_data_points = len(policy_performance)  # Use predicted data count
        avg_utilization_change = total_utilization_change / num_data_points if num_data_points > 0 else 0
        avg_cost_impact = total_cost_impact / num_data_points if num_data_points > 0 else 0
        
        # Annualized savings (extrapolate from current savings)
        if total_cost_savings > 0 and num_data_points > 0:
            # Average monthly savings
            avg_monthly_savings = total_cost_savings / num_data_points
            annualized_savings = avg_monthly_savings * 12
        
        # ROI Estimate (simplified: savings / estimated implementation cost)
        # Assume average policy implementation cost of $50k per policy
        implementation_cost = len(active_policies) * 50000 if active_policies else 1
        if annualized_savings > 0:
            roi_estimate = ((annualized_savings - implementation_cost) / implementation_cost) * 100 if implementation_cost > 0 else 0
        
        # Cost per member metrics
        cost_pmpm_current = (total_paid_amount / (member_count * 12)) if member_count > 0 else 0
        savings_pmpm = (annualized_savings / (member_count * 12)) if member_count > 0 else 0
        
        # Member impact (how many members affected by policies)
        members_impacted = member_count  # All members if policies are global, could be refined
        
        # Top performing policies (by utilization reduction)
        top_policies = sorted(
            policy_performance,
            key=lambda x: x.get("utilization_change_pct", 0),
        )[:5]
        
        # Recent activity
        recent_activity = []
        for analysis in recent_analyses[:5]:
            recent_activity.append({
                "id": analysis.get("id"),
                "type": analysis.get("analysis_type"),
                "status": analysis.get("status"),
                "created_at": analysis.get("created_at"),
            })
        
        # Risk indicators
        risk_indicators = []
        if avg_utilization_change < -10:
            risk_indicators.append({
                "type": "HIGH_UTILIZATION_DROP",
                "severity": "HIGH",
                "message": f"Average utilization decreased by {abs(avg_utilization_change):.1f}%",
            })
        if avg_cost_impact < -1000:
            risk_indicators.append({
                "type": "HIGH_COST_IMPACT",
                "severity": "MEDIUM",
                "message": f"Significant cost impact detected: ${abs(avg_cost_impact):,.0f}",
            })
        
        return {
            "summary": {
                "active_policies": len(active_policies),
                "total_policies": total_policies,
                "recent_analyses": len(recent_analyses),
                "completed_analyses": len(completed_analyses),
                "total_observations": len(observations),
            },
            "metrics": {
                "avg_utilization_change_pct": round(avg_utilization_change, 2),
                "avg_cost_impact": round(avg_cost_impact, 2),
                "total_cost_impact": round(total_cost_impact, 2),
            },
            # ========== ENTERPRISE-GRADE BUSINESS METRICS ==========
            "business_metrics": {
                # Database-driven metrics
                "member_count": member_count,
                "total_claims_count": total_claims_count,
                "total_paid_amount": round(total_paid_amount, 2),
                "total_allowed_amount": round(total_allowed_amount, 2),
                "claims_date_range": claims_date_range,
                "cost_pmpm_current": round(cost_pmpm_current, 2),
                
                # Policy impact metrics
                "total_cost_savings": round(total_cost_savings, 2),
                "annualized_savings": round(annualized_savings, 2),
                "savings_pmpm": round(savings_pmpm, 2),
                "total_utilization_reduction_pct": round(total_utilization_reduction, 2),
                "members_impacted": members_impacted,
                
                # ROI and financial metrics
                "roi_estimate_pct": round(roi_estimate, 2),
                "implementation_cost": implementation_cost,
                "payback_period_months": round(implementation_cost / (annualized_savings / 12), 1) if annualized_savings > 0 else None,
                
                # Efficiency metrics
                "claims_per_member": round(total_claims_count / member_count, 2) if member_count > 0 else 0,
                "cost_per_claim": round(total_paid_amount / total_claims_count, 2) if total_claims_count > 0 else 0,
            },
            "top_policies": top_policies,
            "recent_activity": recent_activity,
            "risk_indicators": risk_indicators,
            "general_baseline": general_baseline,
            "last_updated": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        # Return a minimal dashboard response instead of failing completely
        print(f"Error loading dashboard summary: {error_msg}")
        return {
            "summary": {
                "active_policies": 0,
                "total_policies": 0,
                "recent_analyses": 0,
                "completed_analyses": 0,
                "total_observations": 0,
            },
            "metrics": {
                "avg_utilization_change_pct": 0,
                "avg_cost_impact": 0,
                "total_cost_impact": 0,
            },
            "top_policies": [],
            "recent_activity": [],
            "risk_indicators": [],
            "general_baseline": None,
            "last_updated": datetime.utcnow().isoformat(),
            "error": f"Partial data loaded: {error_msg}",
        }


@router.get("/dashboard/policy-performance")
async def get_policy_performance(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
):
    """Get policy performance metrics"""
    try:
        policies = list_policies(current_user.tenant_id)
        observations = list_observations(current_user.tenant_id)
        
        # Member count for cost impact (cost_change_pmpm * member_months)
        member_count = 0
        try:
            member_count = db.query(func.count(distinct(ClaimsLineDB.member_id))).filter(
                ClaimsLineDB.tenant_id == current_user.tenant_id
            ).scalar() or 0
        except Exception:
            pass
        if not member_count:
            member_count = 10000  # Fallback for cost scaling
        
        performance_data = []
        
        for policy in policies[:limit]:
            policy_id = policy.get("id") or policy.get("policy_id")
            policy_id_str = str(policy_id)
            # Match observations by policy_id (handles both UUID and string IDs)
            policy_observations = [
                o for o in observations 
                if str(o.get("policy_id", "")) == policy_id_str
            ]
            
            # If we have observations, use them
            if policy_observations:
                # Aggregate metrics
                total_utilization_change = sum(
                    o.get("metrics", {}).get("observed_percent_change", 0) for o in policy_observations
                )
                avg_utilization_change = total_utilization_change / len(policy_observations)
                
                # Cost impact: use cost_change_pmpm * member_months (change_from_baseline is utilization, not $)
                total_cost_impact = 0.0
                for o in policy_observations:
                    comparisons = o.get("comparisons") or {}
                    vb = comparisons.get("vs_baseline", {}) if isinstance(comparisons, dict) else {}
                    cost_change_pmpm = vb.get("cost_change_pmpm") or vb.get("cost_change")
                    if cost_change_pmpm is None and (vb.get("baseline_cost_pmpm") is not None or vb.get("observed_cost_pmpm") is not None):
                        base = float(vb.get("baseline_cost_pmpm") or 0)
                        obs = float(vb.get("observed_cost_pmpm") or 0)
                        cost_change_pmpm = obs - base
                    member_months = vb.get("baseline_member_months") or (member_count * 1)
                    total_cost_impact += (float(cost_change_pmpm or 0)) * (float(member_months or member_count))
                avg_cost_impact = total_cost_impact / len(policy_observations)
                
                # When observations have no cost in vs_baseline, fall back to predicted impact so chart shows data
                if (avg_cost_impact is None or abs(float(avg_cost_impact or 0)) < 1e-6):
                    try:
                        from uepi_api.storage_policy_predicted_impact import get_predicted_impact
                        predicted_impact = get_predicted_impact(policy_id, current_user.tenant_id)
                        if predicted_impact:
                            pm = predicted_impact.get("metrics", {}) or {}
                            cost_change_pmpm = pm.get("cost_change_pmpm") or pm.get("cost_change", 0)
                            avg_cost_impact = (float(cost_change_pmpm or 0)) * member_count
                    except Exception:
                        pass
                
                # Prediction accuracy
                prediction_accuracies = []
                for obs in policy_observations:
                    comp = obs.get("comparisons", {}) or {}
                    vs_predicted = comp.get("vs_predicted", {}) if isinstance(comp, dict) else {}
                    if vs_predicted:
                        accuracy = vs_predicted.get("prediction_accuracy_pct")
                        if accuracy is not None:
                            prediction_accuracies.append(accuracy)
                
                avg_prediction_accuracy = (
                    sum(prediction_accuracies) / len(prediction_accuracies)
                    if prediction_accuracies else None
                )
                
                # Latest observation period end (run date) for "Through [date]" display
                latest_obs = max(
                    policy_observations,
                    key=lambda o: (o.get("observation_period_end") or "", o.get("computed_at") or ""),
                )
                eff = policy.get("effective_period") or {}
                policy_effective_date = eff.get("start_date") if isinstance(eff, dict) else None
                performance_data.append({
                    "policy_id": policy_id,
                    "policy_name": policy.get("name") or policy.get("policy_name", "Unknown"),
                    "status": policy.get("status"),
                    "observations_count": len(policy_observations),
                    "avg_utilization_change_pct": round(avg_utilization_change, 2),
                    "avg_cost_impact": round(float(avg_cost_impact or 0), 2),
                    "avg_prediction_accuracy_pct": round(avg_prediction_accuracy, 2) if avg_prediction_accuracy else None,
                    "is_predicted": False,
                    "latest_observation_period_end": latest_obs.get("observation_period_end"),
                    "policy_effective_date": policy_effective_date,
                })
            else:
                # No observations - use predicted impact so chart shows data
                avg_cost_impact = 0.0
                avg_utilization_change = 0.0
                try:
                    from uepi_api.storage_policy_predicted_impact import get_predicted_impact
                    predicted_impact = get_predicted_impact(policy_id, current_user.tenant_id)
                    if predicted_impact:
                        metrics = predicted_impact.get("metrics", {}) or {}
                        avg_utilization_change = float(
                            metrics.get("utilization_change_pct", 0) or metrics.get("utilization_change", 0)
                            or metrics.get("utilization_change_per_1k", 0) or 0
                        )
                        cost_change_pmpm = metrics.get("cost_change_pmpm") or metrics.get("cost_change", 0)
                        avg_cost_impact = (float(cost_change_pmpm or 0)) * member_count
                except Exception:
                    pass
                eff = policy.get("effective_period") or {}
                policy_effective_date = eff.get("start_date") if isinstance(eff, dict) else None
                performance_data.append({
                    "policy_id": policy_id,
                    "policy_name": policy.get("name") or policy.get("policy_name", "Unknown"),
                    "status": policy.get("status"),
                    "observations_count": 0,
                    "avg_utilization_change_pct": round(avg_utilization_change, 2),
                    "avg_cost_impact": round(avg_cost_impact, 2),
                    "avg_prediction_accuracy_pct": None,
                    "is_predicted": bool(avg_cost_impact != 0 or avg_utilization_change != 0),
                    "latest_observation_period_end": None,
                    "policy_effective_date": policy_effective_date,
                })
        
        # Sort by cost impact first (so non-zero shows in chart), then by utilization change
        performance_data.sort(
            key=lambda x: (abs(x.get("avg_cost_impact", 0) or 0), abs(x.get("avg_utilization_change_pct", 0) or 0)),
            reverse=True,
        )
        
        return performance_data
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        # Return empty list instead of failing completely
        print(f"Error loading policy performance: {error_msg}")
        return []
