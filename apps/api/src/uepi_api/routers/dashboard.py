"""Dashboard API endpoints - Executive dashboard data aggregation - Database-driven, Enterprise-grade"""
from typing import Annotated
from datetime import datetime, timedelta, date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, distinct, desc

from uepi_api.auth import CurrentUser, get_demo_current_user
from uepi_api.database import get_db, set_local_statement_timeout
from uepi_api.models.canonical_data import ClaimsLineDB
from uepi_api.models.policy import Policy
from uepi_api.models.analysis import Analysis
from uepi_api.models.observation import Observation
from uepi_api.storage_observations import list_observations

router = APIRouter()


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    db: Session = Depends(get_db),
):
    """Get executive dashboard summary with key metrics - Database-driven, Enterprise-grade.

    Optimized: uses SQL counts + latest-per-policy observation summaries instead of
    hydrating full policy/analysis/observation lists (same response shape).
    """
    try:
        tenant_id = current_user.tenant_id
        print(f"DEBUG get_dashboard_summary: Loading data for tenant {tenant_id}")

        member_count = 0
        total_claims_count = 0
        total_paid_amount = 0.0
        total_allowed_amount = 0.0
        claims_date_range = {"start": None, "end": None}

        # Prefer general baseline snapshot for portfolio metrics (avoids full claims scans).
        try:
            from uepi_api.storage_baselines import get_latest_baseline

            baseline = get_latest_baseline(tenant_id, policy_id=None)
            if baseline:
                bm = baseline.get("baseline_metrics") or baseline.get("metrics") or {}
                member_count = int(bm.get("unique_members") or bm.get("member_count") or 0)
                total_claims_count = int(bm.get("total_claims") or bm.get("claim_count") or 0)
                total_paid_amount = float(bm.get("total_paid") or bm.get("paid_amount_total") or 0)
                total_allowed_amount = float(bm.get("total_allowed") or bm.get("allowed_amount_total") or 0)
                if baseline.get("window_start_date"):
                    claims_date_range["start"] = str(baseline["window_start_date"])[:10]
                if baseline.get("window_end_date"):
                    claims_date_range["end"] = str(baseline["window_end_date"])[:10]
        except Exception as e:
            print(f"WARNING get_dashboard_summary: baseline portfolio metrics unavailable: {e}")

        # Fallback: bounded claims aggregate (short timeout) only if baseline had no usable counts.
        if total_claims_count <= 0 or member_count <= 0:
            try:
                set_local_statement_timeout(db, 8_000)
                twelve_months_ago = date.today() - timedelta(days=365)
                claims_stats = db.query(
                    func.count(ClaimsLineDB.claim_line_id).label("total_claims"),
                    func.sum(ClaimsLineDB.paid_amount).label("total_paid"),
                    func.sum(ClaimsLineDB.allowed_amount).label("total_allowed"),
                    func.min(ClaimsLineDB.service_date).label("earliest_date"),
                    func.max(ClaimsLineDB.service_date).label("latest_date"),
                ).filter(
                    and_(
                        ClaimsLineDB.tenant_id == tenant_id,
                        ClaimsLineDB.service_date >= twelve_months_ago,
                    )
                ).first()

                if claims_stats:
                    if total_claims_count <= 0:
                        total_claims_count = claims_stats.total_claims or 0
                    if total_paid_amount <= 0:
                        total_paid_amount = float(claims_stats.total_paid or 0)
                    if total_allowed_amount <= 0:
                        total_allowed_amount = float(claims_stats.total_allowed or 0)
                    if not claims_date_range["start"] and claims_stats.earliest_date:
                        claims_date_range["start"] = claims_stats.earliest_date.isoformat()
                    if not claims_date_range["end"] and claims_stats.latest_date:
                        claims_date_range["end"] = claims_stats.latest_date.isoformat()
                # Skip count(distinct member_id) — too expensive on large claim tables.
            except Exception as e:
                print(f"WARNING get_dashboard_summary: Could not load database metrics: {e}")
                try:
                    db.rollback()
                except Exception:
                    pass

        print(
            f"DEBUG get_dashboard_summary: Database metrics - Members: {member_count}, "
            f"Claims: {total_claims_count}, Paid: ${total_paid_amount:,.2f}"
        )

        # ---- Policy counts (no full metadata hydration) ----
        total_policies = 0
        active_policies_count = 0
        policy_name_by_id: dict[str, str] = {}
        try:
            total_policies = (
                db.query(func.count(Policy.id)).filter(Policy.tenant_id == tenant_id).scalar() or 0
            )
            active_policies_count = (
                db.query(func.count(Policy.id))
                .filter(Policy.tenant_id == tenant_id, func.upper(Policy.status) == "ACTIVE")
                .scalar()
                or 0
            )
            # Light name map for top policies (cap rows)
            for pid, pname in (
                db.query(Policy.id, Policy.name)
                .filter(Policy.tenant_id == tenant_id)
                .limit(500)
                .all()
            ):
                policy_name_by_id[str(pid)] = pname or "Unknown"
        except Exception as e:
            print(f"ERROR get_dashboard_summary: Failed to count policies: {e}")

        # ---- Analysis counts + recent activity (limited) ----
        recent_analyses_count = 0
        completed_analyses_count = 0
        recent_activity = []
        try:
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_analyses_count = (
                db.query(func.count(Analysis.id))
                .filter(
                    Analysis.tenant_id == tenant_id,
                    Analysis.created_at >= thirty_days_ago,
                )
                .scalar()
                or 0
            )
            completed_analyses_count = (
                db.query(func.count(Analysis.id))
                .filter(Analysis.tenant_id == tenant_id, Analysis.status == "COMPLETED")
                .scalar()
                or 0
            )
            recent_rows = (
                db.query(Analysis.id, Analysis.analysis_type, Analysis.status, Analysis.created_at)
                .filter(Analysis.tenant_id == tenant_id, Analysis.created_at >= thirty_days_ago)
                .order_by(desc(Analysis.created_at))
                .limit(5)
                .all()
            )
            for row in recent_rows:
                recent_activity.append(
                    {
                        "id": str(row.id),
                        "type": row.analysis_type,
                        "status": row.status,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                    }
                )
        except Exception as e:
            print(f"ERROR get_dashboard_summary: Failed to count analyses: {e}")

        # ---- Latest observations (slim) for impact metrics ----
        observations = []
        total_observations = 0
        try:
            total_observations = (
                db.query(func.count(Observation.id))
                .filter(Observation.tenant_id == tenant_id)
                .scalar()
                or 0
            )
            observations = list_observations(
                tenant_id=tenant_id,
                latest_only=True,
                summary=True,
                limit=200,
            )
        except Exception as e:
            print(f"ERROR get_dashboard_summary: Failed to load observations: {e}")
            observations = []

        # ---- General (pre-policy) baseline ----
        general_baseline = None
        try:
            from uepi_api.storage_baselines import get_latest_baseline

            baseline = get_latest_baseline(tenant_id, policy_id=None)
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

        total_utilization_change = 0.0
        total_utilization_reduction = 0.0
        sum_cost_change_pmpm = 0.0
        n_cost_pmpm = 0
        policy_performance = []

        for obs in observations:
            metrics = obs.get("metrics", {}) or {}
            comparisons = obs.get("comparisons", {}) or {}
            vs_baseline = comparisons.get("vs_baseline", {}) if isinstance(comparisons, dict) else {}
            cost_change_pmpm = None
            if vs_baseline:
                raw = vs_baseline.get("cost_change_pmpm")
                if raw is None:
                    raw = vs_baseline.get("change_from_baseline")
                try:
                    if raw is not None:
                        cost_change_pmpm = float(raw)
                        sum_cost_change_pmpm += cost_change_pmpm
                        n_cost_pmpm += 1
                except (TypeError, ValueError):
                    cost_change_pmpm = None

            utilization_change = None
            if vs_baseline:
                utilization_change = vs_baseline.get("utilization_change_pct")
                if utilization_change is None:
                    utilization_change = vs_baseline.get("change_from_baseline_pct")
            if utilization_change is None:
                utilization_change = metrics.get("observed_percent_change") or metrics.get(
                    "utilization_change_pct", 0
                )
            try:
                utilization_change_f = float(utilization_change or 0)
            except (TypeError, ValueError):
                utilization_change_f = 0.0
            total_utilization_change += utilization_change_f
            if utilization_change_f < 0:
                total_utilization_reduction += abs(utilization_change_f)

            policy_id = obs.get("policy_id")
            if policy_id:
                policy_id_str = str(policy_id)
                policy_performance.append(
                    {
                        "policy_id": policy_id,
                        "policy_name": policy_name_by_id.get(policy_id_str, "Unknown"),
                        "utilization_change_pct": utilization_change_f,
                        # PMPM only — do not multiply by member_months (that fabricated
                        # portfolio "$ savings" and drove inflated ROI on the exec dashboard).
                        "cost_impact": cost_change_pmpm if cost_change_pmpm is not None else 0,
                        "cost_impact_unit": "pmpm",
                        "observation_date": obs.get("computed_at"),
                    }
                )

        if not observations or not policy_performance:
            try:
                from uepi_api.storage_policy_predicted_impact import get_predicted_impact

                sample_policies = (
                    db.query(Policy.id, Policy.name)
                    .filter(Policy.tenant_id == tenant_id)
                    .order_by(desc(Policy.created_at))
                    .limit(10)
                    .all()
                )
                for pid, pname in sample_policies:
                    try:
                        predicted_impact = get_predicted_impact(pid, tenant_id)
                        if not predicted_impact:
                            continue
                        metrics = predicted_impact.get("metrics", {}) or {}
                        utilization_change = metrics.get("utilization_change_pct", 0)
                        cost_change_pmpm = metrics.get("cost_change_pmpm", 0)
                        try:
                            utilization_change_f = float(utilization_change or 0)
                        except (TypeError, ValueError):
                            utilization_change_f = 0.0
                        try:
                            cost_pmpm_f = float(cost_change_pmpm or 0)
                        except (TypeError, ValueError):
                            cost_pmpm_f = 0.0
                        total_utilization_change += utilization_change_f
                        sum_cost_change_pmpm += cost_pmpm_f
                        n_cost_pmpm += 1
                        policy_performance.append(
                            {
                                "policy_id": str(pid),
                                "policy_name": pname or "Unknown",
                                "utilization_change_pct": utilization_change_f,
                                "cost_impact": cost_pmpm_f,
                                "cost_impact_unit": "pmpm",
                                "observation_date": predicted_impact.get("predicted_at"),
                                "is_predicted": True,
                            }
                        )
                    except Exception:
                        continue
            except Exception as e:
                print(f"Warning: Could not load predicted impact fallback: {e}")

        num_data_points = len(observations) if observations else len(
            [p for p in policy_performance if not p.get("is_predicted")]
        )
        if not num_data_points:
            num_data_points = len(policy_performance)
        avg_utilization_change = (
            total_utilization_change / num_data_points if num_data_points > 0 else 0
        )
        avg_cost_impact_pmpm = (
            sum_cost_change_pmpm / n_cost_pmpm if n_cost_pmpm > 0 else 0
        )

        # Do not invent ROI from policies×$50k or Σ(pmpm×member_months).
        portfolio_financials_available = bool(member_count and member_count > 0 and total_paid_amount > 0)
        portfolio_financials_reason = None
        if not portfolio_financials_available:
            portfolio_financials_reason = (
                "Portfolio ROI / annualized $ savings unavailable: membership or paid totals "
                "not present on general baseline. Policy-level PMPM deltas remain available."
            )

        cost_pmpm_current = (total_paid_amount / (member_count * 12)) if member_count > 0 else None
        members_impacted = member_count if member_count > 0 else None

        top_policies = sorted(
            policy_performance,
            key=lambda x: x.get("utilization_change_pct", 0),
        )[:5]

        risk_indicators = []
        if avg_utilization_change < -10:
            risk_indicators.append(
                {
                    "type": "HIGH_UTILIZATION_DROP",
                    "severity": "HIGH",
                    "message": f"Average utilization decreased by {abs(avg_utilization_change):.1f}%",
                }
            )
        if avg_cost_impact_pmpm < -10:
            risk_indicators.append(
                {
                    "type": "HIGH_COST_IMPACT",
                    "severity": "MEDIUM",
                    "message": f"Average policy cost Δ PMPM: ${avg_cost_impact_pmpm:,.2f}",
                }
            )

        return {
            "summary": {
                "active_policies": active_policies_count,
                "total_policies": total_policies,
                "recent_analyses": recent_analyses_count,
                "completed_analyses": completed_analyses_count,
                "total_observations": total_observations,
            },
            "metrics": {
                "avg_utilization_change_pct": round(avg_utilization_change, 2),
                "avg_cost_impact": round(avg_cost_impact_pmpm, 2),
                "avg_cost_impact_unit": "pmpm",
                "total_cost_impact": round(sum_cost_change_pmpm, 2) if n_cost_pmpm else 0,
                "total_cost_impact_unit": "pmpm_sum",
                "portfolio_financials_available": portfolio_financials_available,
                "portfolio_financials_reason": portfolio_financials_reason,
            },
            "business_metrics": {
                "member_count": member_count,
                "total_claims_count": total_claims_count,
                "total_paid_amount": round(total_paid_amount, 2),
                "total_allowed_amount": round(total_allowed_amount, 2),
                "claims_date_range": claims_date_range,
                "cost_pmpm_current": round(cost_pmpm_current, 2) if cost_pmpm_current is not None else None,
                "total_cost_savings": None,
                "annualized_savings": None,
                "savings_pmpm": None,
                "total_utilization_reduction_pct": round(
                    (total_utilization_reduction / num_data_points) if num_data_points else 0, 2
                ),
                "members_impacted": members_impacted,
                "roi_estimate_pct": None,
                "implementation_cost": None,
                "payback_period_months": None,
                "portfolio_financials_available": portfolio_financials_available,
                "portfolio_financials_reason": portfolio_financials_reason,
                "claims_per_member": round(total_claims_count / member_count, 2)
                if member_count > 0
                else None,
                "cost_per_claim": round(total_paid_amount / total_claims_count, 2)
                if total_claims_count > 0
                else None,
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


@router.get("/dashboard/objectives-health")
async def get_objectives_health(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
):
    """Authoritative Objectives Health snapshot (deterministic for fixed data).

    Replaces client-side multi-API aggregation that caused intermittent results
    via silent empty fallbacks, N+1 forecast probes, and predicted-as-observed fill.

    Runs sync DB work in a worker thread so a slow/hung Postgres call cannot
    block the asyncio event loop (and thus /health liveness).
    """
    import asyncio
    from uepi_api.services.objectives_health import load_objectives_health

    tenant_id = current_user.tenant_id
    return await asyncio.to_thread(load_objectives_health, tenant_id)


@router.get("/dashboard/policy-performance")
async def get_policy_performance(
    current_user: Annotated[CurrentUser, Depends(get_demo_current_user)],
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
):
    """Get policy performance metrics (slim: latest obs per policy, no full list hydration)."""
    try:
        tenant_id = current_user.tenant_id

        # Prefer baseline snapshot — never scan claims for distinct members here.
        member_count = 0
        try:
            from uepi_api.storage_baselines import get_latest_baseline

            baseline = get_latest_baseline(tenant_id, policy_id=None)
            if baseline:
                bm = baseline.get("baseline_metrics") or baseline.get("metrics") or {}
                member_count = int(bm.get("unique_members") or bm.get("member_count") or 0)
        except Exception:
            pass
        if not member_count:
            member_count = 10000

        policies = (
            db.query(Policy.id, Policy.name, Policy.status, Policy.policy_metadata_json)
            .filter(Policy.tenant_id == tenant_id)
            .order_by(desc(Policy.created_at))
            .limit(limit)
            .all()
        )

        observations = list_observations(
            tenant_id=tenant_id,
            latest_only=True,
            summary=True,
            limit=min(500, max(limit * 2, 100)),
        )
        obs_by_policy: dict[str, dict] = {}
        for o in observations:
            pid = str(o.get("policy_id") or "")
            if pid and pid not in obs_by_policy:
                obs_by_policy[pid] = o

        performance_data = []
        for policy in policies:
            policy_id = policy.id
            policy_id_str = str(policy_id)
            meta = policy.policy_metadata_json or {}
            eff = meta.get("effective_period") if isinstance(meta, dict) else {}
            policy_effective_date = eff.get("start_date") if isinstance(eff, dict) else None
            obs = obs_by_policy.get(policy_id_str)

            if obs:
                metrics = obs.get("metrics") or {}
                comparisons = obs.get("comparisons") or {}
                vb = comparisons.get("vs_baseline", {}) if isinstance(comparisons, dict) else {}
                avg_utilization_change = float(
                    metrics.get("observed_percent_change", 0)
                    or metrics.get("utilization_change_pct", 0)
                    or 0
                )
                cost_change_pmpm = vb.get("cost_change_pmpm") or vb.get("cost_change")
                if cost_change_pmpm is None and (
                    vb.get("baseline_cost_pmpm") is not None or vb.get("observed_cost_pmpm") is not None
                ):
                    base = float(vb.get("baseline_cost_pmpm") or 0)
                    observed = float(vb.get("observed_cost_pmpm") or 0)
                    cost_change_pmpm = observed - base
                member_months = vb.get("baseline_member_months") or member_count
                avg_cost_impact = float(cost_change_pmpm or 0) * float(member_months or member_count)

                if abs(avg_cost_impact) < 1e-6:
                    try:
                        from uepi_api.storage_policy_predicted_impact import get_predicted_impact

                        predicted_impact = get_predicted_impact(policy_id, tenant_id)
                        if predicted_impact:
                            pm = predicted_impact.get("metrics", {}) or {}
                            cost_change_pmpm = pm.get("cost_change_pmpm") or pm.get("cost_change", 0)
                            avg_cost_impact = float(cost_change_pmpm or 0) * member_count
                    except Exception:
                        pass

                vs_predicted = comparisons.get("vs_predicted", {}) if isinstance(comparisons, dict) else {}
                avg_prediction_accuracy = vs_predicted.get("prediction_accuracy_pct")

                performance_data.append(
                    {
                        "policy_id": policy_id_str,
                        "policy_name": policy.name or "Unknown",
                        "status": policy.status,
                        "observations_count": 1,
                        "avg_utilization_change_pct": round(avg_utilization_change, 2),
                        "avg_cost_impact": round(float(avg_cost_impact or 0), 2),
                        "avg_prediction_accuracy_pct": round(avg_prediction_accuracy, 2)
                        if avg_prediction_accuracy is not None
                        else None,
                        "is_predicted": False,
                        "latest_observation_period_end": obs.get("observation_period_end"),
                        "policy_effective_date": policy_effective_date,
                    }
                )
            else:
                avg_cost_impact = 0.0
                avg_utilization_change = 0.0
                try:
                    from uepi_api.storage_policy_predicted_impact import get_predicted_impact

                    predicted_impact = get_predicted_impact(policy_id, tenant_id)
                    if predicted_impact:
                        metrics = predicted_impact.get("metrics", {}) or {}
                        avg_utilization_change = float(
                            metrics.get("utilization_change_pct", 0)
                            or metrics.get("utilization_change", 0)
                            or metrics.get("utilization_change_per_1k", 0)
                            or 0
                        )
                        cost_change_pmpm = metrics.get("cost_change_pmpm") or metrics.get("cost_change", 0)
                        avg_cost_impact = float(cost_change_pmpm or 0) * member_count
                except Exception:
                    pass
                performance_data.append(
                    {
                        "policy_id": policy_id_str,
                        "policy_name": policy.name or "Unknown",
                        "status": policy.status,
                        "observations_count": 0,
                        "avg_utilization_change_pct": round(avg_utilization_change, 2),
                        "avg_cost_impact": round(avg_cost_impact, 2),
                        "avg_prediction_accuracy_pct": None,
                        "is_predicted": bool(avg_cost_impact != 0 or avg_utilization_change != 0),
                        "latest_observation_period_end": None,
                        "policy_effective_date": policy_effective_date,
                    }
                )

        performance_data.sort(
            key=lambda x: (
                abs(x.get("avg_cost_impact", 0) or 0),
                abs(x.get("avg_utilization_change_pct", 0) or 0),
            ),
            reverse=True,
        )
        return performance_data

    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"Error loading policy performance: {e}")
        return []
