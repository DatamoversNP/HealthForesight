#!/usr/bin/env python3
"""
Demo Day Setup (Option A) – One script to prepare an impactful demo.

1. Ensures demo tenant and user exist (tenant 00000000-0000-0000-0000-000000000001).
2. Ensures at least 3 demo policies exist (creates minimal ones if none).
3. Ensures at least one baseline (creates one with fixed metrics if none).
4. Ensures predicted impact per policy (full Stage 3.5: provider/patient/substitution; use --stub-predicted-impact for minimal).
5. Creates 5 observations with a clear story: 2 ON_TRACK, 2 AT_RISK, 1 BACKFIRE.

Run from repo root:
  python scripts/run_demo_day.py [--tenant-id UUID] [--skip-seed]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


def ensure_tenant_and_user(tenant_id: UUID) -> None:
    """Ensure demo tenant and user exist."""
    from uepi_api.database import SessionLocal
    from uepi_api.models.tenant import Tenant, User

    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            tenant = Tenant(id=tenant_id, name="Demo Tenant", domain="demo")
            db.add(tenant)
            db.flush()
            print("  Created demo tenant")
        user = db.query(User).filter(User.tenant_id == tenant_id).first()
        if not user:
            user_id = tenant_id if tenant_id == DEFAULT_TENANT_ID else uuid4()
            user = User(
                id=user_id,
                tenant_id=tenant_id,
                email="demo@example.com",
                full_name="Demo User",
            )
            db.add(user)
            print("  Created demo user")
        db.commit()
    finally:
        db.close()


def ensure_policies(tenant_id: UUID, min_count: int = 3) -> list:
    """Ensure at least min_count policies; create minimal ones if needed."""
    from uepi_api.storage_policies import list_policies
    from uepi_api.database import SessionLocal
    from uepi_api.models.policy import Policy, PolicyVersion, PolicyCodeSet

    policies = list_policies(tenant_id) or []
    if len(policies) >= min_count:
        return policies

    db = SessionLocal()
    try:
        demo_policies = [
            ("Prior Auth – Outpatient MRI", "PA", ["72141", "72142"]),
            ("Site-of-Care – Infusion", "SITE_OF_CARE", ["96413", "96415"]),
            ("PT Coverage Relaxation", "COVERAGE", ["97110", "97112"]),
            ("Step Therapy – Biologic", "STEP_THERAPY", ["96413"]),
            ("Urgent Care Copay", "BENEFIT", ["99281", "99282"]),
        ]
        effective = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30)
        for name, ptype, codes in demo_policies:
            if db.query(Policy).filter(Policy.tenant_id == tenant_id, Policy.name == name).first():
                continue
            policy = Policy(
                tenant_id=tenant_id,
                name=name,
                policy_type=ptype,
                owner_role="POLICY_ADMIN",
                description=f"Demo policy: {name}",
            )
            db.add(policy)
            db.flush()
            version = PolicyVersion(
                tenant_id=tenant_id,
                policy_id=policy.id,
                version_number=1,
                effective_start_date=effective,
                change_type="NEW",
                enforcement_strength="HARD",
            )
            db.add(version)
            db.flush()
            for code in codes:
                db.add(PolicyCodeSet(
                    tenant_id=tenant_id,
                    version_id=version.id,
                    code=code,
                    code_type="CPT",
                    code_group=ptype,
                ))
            print(f"  Created policy: {name}")
        db.commit()
    finally:
        db.close()
    return list_policies(tenant_id) or []


def ensure_baseline(tenant_id: UUID) -> dict:
    """Ensure at least one baseline; create one with fixed metrics if none."""
    from uepi_api.storage_baselines import get_latest_baseline, create_baseline

    baseline = get_latest_baseline(tenant_id, policy_id=None)
    if baseline:
        return baseline

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    window_end = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    window_start = window_end - timedelta(days=90)
    baseline_data = {
        "window_start_date": window_start.isoformat() + "Z",
        "window_end_date": window_end.isoformat() + "Z",
        "computed_at": now.isoformat() + "Z",
        "baseline_type": "ROLLING",
        "data_period_ids": [],
        "baseline_metrics": {
            "util_rate_total_per_1000_mm": 82.0,
            "utilization_per_1k": 82.0,
            "allowed_pmpm_total": 48.0,
            "cost_pmpm": 48.0,
        },
        "computed_by": "demo_day_setup",
        "refresh_reason": "NEW_DATA",
    }
    result = create_baseline(tenant_id, baseline_data)
    print("  Created demo baseline")
    return get_latest_baseline(tenant_id, policy_id=None) or result


def _baseline_metrics_for_predicted_impact(
    tenant_id: UUID, policy_id: UUID, fallback_baseline: dict
) -> Optional[Dict[str, Any]]:
    """Map stored baseline JSON to PredictedImpactGenerator inputs (same as policies router)."""
    from uepi_api.storage_baselines import get_latest_baseline

    bl = get_latest_baseline(tenant_id, policy_id=policy_id)
    if not bl:
        bl = get_latest_baseline(tenant_id, policy_id=None)
    if not bl:
        bl = fallback_baseline
    if not bl:
        return None
    d = bl.get("baseline_metrics") or bl.get("metrics") or {}
    if not d:
        return None
    mapped = {
        "utilization_per_1k": float(
            d.get("util_rate_target_per_1000_mm")
            or d.get("util_rate_total_per_1000_mm")
            or d.get("utilization_per_1k")
            or 0.0
        ),
        "cost_pmpm": float(
            d.get("allowed_pmpm_target")
            or d.get("allowed_pmpm_total")
            or d.get("allowed_pmpm")
            or d.get("cost_pmpm")
            or 0.0
        ),
        "member_count": int(d.get("unique_members") or 0),
        "member_months": d.get("member_months", 0),
    }
    out = {k: v for k, v in mapped.items() if v is not None and v != 0}
    return out or None


def ensure_predicted_impact(
    tenant_id: UUID,
    policy_id: UUID,
    baseline: dict,
    *,
    regenerate: bool = False,
    stub_only: bool = False,
) -> bool:
    """Ensure predicted impact exists. Default: full Stage 3.5 model (provider/patient/substitution)."""
    from uepi_api.storage_policy_predicted_impact import get_predicted_impact, store_predicted_impact
    from uepi_api.storage_policies import get_policy

    if not regenerate and get_predicted_impact(policy_id, tenant_id):
        return True

    baseline_id = baseline.get("id") or baseline.get("baseline_id")
    if stub_only:
        data = {
            "baseline_id": baseline_id,
            "metrics": {
                "utilization_change_per_1k": -5.0,
                "cost_change_pmpm": -2.0,
                "utilization_change": -5.0,
                "cost_change": -2.0,
                "utilization_change_pct": -5.0,
                "cost_change_pct": -3.0,
                "cost_change_total": -60000.0,
                "confidence_score": 70.0,
                "prediction_method": "demo_stub",
            },
            "model_version": "demo_v1",
            "prediction_method": "demo_stub",
            "confidence": 70.0,
        }
        return bool(store_predicted_impact(policy_id, tenant_id, data))

    policy = get_policy(policy_id, tenant_id)
    if not policy:
        return False
    policy_levers = policy.get("policy_levers") or []
    if not policy_levers:
        return False
    policy_scope = policy.get("scope") or {}

    try:
        from uepi_api.routers.policy_predicted_impact import generate_predicted_impact_for_policy

        baseline_metrics = _baseline_metrics_for_predicted_impact(tenant_id, policy_id, baseline)
        predicted_impact = generate_predicted_impact_for_policy(
            tenant_id=tenant_id,
            policy_id=policy_id,
            policy_levers=policy_levers,
            policy_scope=policy_scope,
            baseline_metrics=baseline_metrics,
        )
        predicted_impact_dict = predicted_impact.model_dump(mode="json")
        enhanced_data = getattr(predicted_impact, "_enhanced_data", None) or {}
        m = predicted_impact_dict.get("metrics") or {}
        stored = store_predicted_impact(
            policy_id=policy_id,
            tenant_id=tenant_id,
            predicted_impact_data={
                "metrics": m,
                "model_version": (predicted_impact_dict.get("model_versions") or {}).get("elasticity", "1.0"),
                "confidence": m.get("confidence_score"),
                "predicted_at": datetime.now(timezone.utc).isoformat(),
                "prediction_method": m.get("prediction_method", "ELASTICITY_MODEL"),
                "baseline_id": str(baseline_id) if baseline_id else None,
                "provider_response": predicted_impact_dict.get("provider_response"),
                "patient_response": predicted_impact_dict.get("patient_response"),
                "substitution_effects": predicted_impact_dict.get("substitution_effects", []),
                "warnings": predicted_impact_dict.get("warnings", []),
                "limitations": predicted_impact_dict.get("limitations", []),
                "baseline_reference": predicted_impact_dict.get("baseline_reference"),
                "model_versions": predicted_impact_dict.get("model_versions", {}),
                "confidence_intervals": enhanced_data.get("confidence_intervals"),
                "ramp_up_projections": enhanced_data.get("ramp_up_projections"),
            },
        )
        return bool(stored)
    except Exception as e:
        print(f"  Full predicted impact failed for {policy_id}, using stub: {e}")
        data = {
            "baseline_id": baseline_id,
            "metrics": {
                "utilization_change_per_1k": -5.0,
                "cost_change_pmpm": -2.0,
                "utilization_change": -5.0,
                "cost_change": -2.0,
                "utilization_change_pct": -5.0,
                "cost_change_pct": -3.0,
                "cost_change_total": -60000.0,
                "confidence_score": 50.0,
                "prediction_method": "demo_fallback",
            },
            "model_version": "demo_v1",
            "prediction_method": "demo_fallback",
            "confidence": 50.0,
        }
        return bool(store_predicted_impact(policy_id, tenant_id, data))


def create_observation_with_verdict(
    tenant_id: UUID,
    policy_id: UUID,
    policy_name: str,
    baseline: dict,
    verdict_kind: str,
) -> bool:
    """Create one observation tuned for ON_TRACK, AT_RISK, or BACKFIRE."""
    from uepi_api.storage_policy_predicted_impact import get_predicted_impact
    from uepi_api.observation_enhancement import enhance_comparisons_with_baseline, enhance_comparisons_with_predicted
    from uepi_api.storage_observations import create_observation

    predicted_impact = get_predicted_impact(policy_id, tenant_id)
    if not predicted_impact or not predicted_impact.get("metrics"):
        return False

    bm = baseline.get("baseline_metrics") or {}
    baseline_util = float(bm.get("util_rate_total_per_1000_mm") or bm.get("utilization_per_1k") or 80.0)
    baseline_cost = float(bm.get("allowed_pmpm_total") or bm.get("cost_pmpm") or 50.0)
    pred_metrics = predicted_impact.get("metrics") or {}
    util_change = float(pred_metrics.get("utilization_change_per_1k") or pred_metrics.get("utilization_change") or -5.0)
    cost_change = float(pred_metrics.get("cost_change_pmpm") or pred_metrics.get("cost_change") or -2.0)
    predicted_util = max(0.0, baseline_util + util_change)
    predicted_cost = max(0.0, baseline_cost + cost_change)

    if verdict_kind == "ON_TRACK":
        factor = 1.0
        behavioral = {}
    elif verdict_kind == "AT_RISK":
        factor = 1.18
        behavioral = {}
    else:
        factor = 1.25
        behavioral = {
            "risk_factors": ["Provider substitution to unmanaged settings", "Patient delay in seeking care"],
            "recommendations": ["Review prior auth criteria", "Monitor ED utilization"],
        }

    observed_util = predicted_util * factor if predicted_util > 0 else baseline_util
    observed_cost = predicted_cost * factor if predicted_cost > 0 else baseline_cost
    metrics = {
        "utilization_per_1k": observed_util,
        "cost_pmpm": observed_cost,
        "cost_per_member": observed_cost,
        "baseline_utilization_per_1k": baseline_util,
        "baseline_cost_pmpm": baseline_cost,
    }
    vs_baseline = enhance_comparisons_with_baseline(tenant_id=tenant_id, observation_metrics=metrics)
    metrics_with_baseline = dict(metrics)
    metrics_with_baseline["baseline_utilization_per_1k"] = vs_baseline.get("baseline_utilization_per_1k")
    metrics_with_baseline["baseline_cost_pmpm"] = vs_baseline.get("baseline_cost_pmpm")
    vs_predicted = enhance_comparisons_with_predicted(
        tenant_id=tenant_id, policy_id=policy_id, observation_metrics=metrics_with_baseline, prediction_id=None
    )
    if not vs_predicted:
        return False

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = now
    observation_data = {
        "observation_id": str(uuid4()),
        "policy_id": str(policy_id),
        "policy_version_id": None,
        "baseline_version_id": baseline.get("id") or baseline.get("baseline_id"),
        "prediction_id": None,
        "analysis_id": None,
        "data_period_id": None,
        "data_period_ids": [],
        "observation_type": "PERIODIC",
        "observation_period_start": start.isoformat() + "Z",
        "observation_period_end": end.isoformat() + "Z",
        "computed_at": now.isoformat() + "Z",
        "metrics": metrics,
        "comparisons": {"vs_baseline": vs_baseline, "vs_predicted": vs_predicted},
        "behavioral_explanation": behavioral,
    }
    try:
        create_observation(tenant_id=tenant_id, observation_data=observation_data)
        acc = vs_predicted.get("prediction_accuracy_pct")
        print(f"  Observation [{verdict_kind}]: {policy_name[:40]}... accuracy={acc}%")
        return True
    except Exception as e:
        print(f"  Error creating observation: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Demo Day setup – tenant, policies, baseline, predicted impact, mixed verdict observations")
    parser.add_argument("--tenant-id", type=str, default=str(DEFAULT_TENANT_ID))
    parser.add_argument("--skip-seed", action="store_true", help="Skip ensuring tenant/policies/baseline/predicted impact; only create observations")
    parser.add_argument(
        "--predicted-all",
        action="store_true",
        help="Write predicted impact for every policy (default: first 5 only)",
    )
    parser.add_argument(
        "--no-observations",
        action="store_true",
        help="Skip creating demo observations (useful before seed_complete_policy_workspace, then run with --skip-seed)",
    )
    parser.add_argument(
        "--regenerate-predicted-impact",
        action="store_true",
        help="Write new predicted impact even if one exists (full Stage 3.5 payload)",
    )
    parser.add_argument(
        "--stub-predicted-impact",
        action="store_true",
        help="Minimal metrics only (no provider/patient/substitution blocks; faster)",
    )
    args = parser.parse_args()
    tenant_id = UUID(args.tenant_id)

    print("=" * 60)
    print("DEMO DAY SETUP")
    print("=" * 60)

    if not args.skip_seed:
        print("\n1. Ensuring tenant and user...")
        ensure_tenant_and_user(tenant_id)

        print("\n2. Ensuring policies...")
        policies = ensure_policies(tenant_id, min_count=3)
        if not policies:
            print("  No policies found; create policies first or run without --skip-seed after seeding.")
            sys.exit(1)

        print("\n3. Ensuring baseline...")
        baseline = ensure_baseline(tenant_id)
        if not baseline:
            print("  No baseline; aborting.")
            sys.exit(1)

        print("\n4. Ensuring predicted impact per policy...")
        pred_targets = policies if args.predicted_all else policies[:5]
        for p in pred_targets:
            pid = UUID(p["id"]) if isinstance(p["id"], str) else p["id"]
            ensure_predicted_impact(
                tenant_id,
                pid,
                baseline,
                regenerate=args.regenerate_predicted_impact,
                stub_only=args.stub_predicted_impact,
            )
    else:
        from uepi_api.storage_baselines import get_latest_baseline
        from uepi_api.storage_policies import list_policies
        policies = list_policies(tenant_id) or []
        baseline = get_latest_baseline(tenant_id, policy_id=None)
        if not policies or not baseline:
            print("  With --skip-seed, need existing policies and baseline. Aborting.")
            sys.exit(1)

    created = 0
    if args.no_observations:
        print("\n5. Skipping observations (--no-observations).")
    else:
        print("\n5. Creating observations (2 ON_TRACK, 2 AT_RISK, 1 BACKFIRE)...")
        verdict_plan = ["ON_TRACK", "ON_TRACK", "AT_RISK", "AT_RISK", "BACKFIRE"]
        for i, p in enumerate(policies[:5]):
            kind = verdict_plan[i] if i < len(verdict_plan) else "ON_TRACK"
            pid = UUID(p["id"]) if isinstance(p["id"], str) else p["id"]
            name = p.get("name", str(pid))
            if create_observation_with_verdict(tenant_id, pid, name, baseline, kind):
                created += 1

    print("\n" + "=" * 60)
    if args.no_observations:
        print("Done (no observations). Re-run with --skip-seed to add demo observations.")
    else:
        print(f"Done. Created {created} demo observations. Use GET /observations and GET /observations/{{id}}/evidence-pack to demo.")
    print("=" * 60)


if __name__ == "__main__":
    main()
