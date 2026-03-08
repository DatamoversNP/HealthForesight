#!/usr/bin/env python3
"""
Phase 1 & 2: Data Foundation and Predicted Impact
- Phase 1.1: Generate claims for demo policies (10-15 policies, multiple dates)
- Phase 1.2: Refresh baseline (general and verify structure)
- Phase 2.1: Regenerate predicted impact for all policies with levers
- Phase 2.2: Metrics structure is verified/fixed in storage_policy_predicted_impact.py
"""
import os
import sys
from pathlib import Path
from datetime import date, timedelta
import requests

# API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
HEADERS = {
    "Authorization": "Bearer dev-token-123",
    "Content-Type": "application/json",
}


def get_policies():
    """Get all policies"""
    try:
        r = requests.get(f"{API_BASE_URL}/policies", headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, list) else data.get("items", [])
    except Exception as e:
        print(f"❌ Error fetching policies: {e}")
        return []


def generate_claims_for_date(target_date: date, member_count: int = 5000, claims_per_member: float = 2.0):
    """Generate general claims for a date"""
    try:
        r = requests.post(
            f"{API_BASE_URL}/data/generate-claims",
            headers=HEADERS,
            json={
                "target_date": target_date.isoformat(),
                "member_count": member_count,
                "claims_per_member": claims_per_member,
            },
            timeout=180,
        )
        if r.status_code in (200, 201):
            result = r.json()
            return result.get("claims_generated", 0), result.get("claims_loaded", 0), None
        return 0, 0, r.text[:200]
    except Exception as e:
        return 0, 0, str(e)[:200]


def generate_policy_scoped_claims(policy_id: str, target_date: date, member_count: int = 10000):
    """Generate policy-scoped claims for a policy"""
    try:
        r = requests.post(
            f"{API_BASE_URL}/data/generate-claims/policy-scoped",
            headers=HEADERS,
            params={"policy_id": policy_id},
            json={
                "target_date": target_date.isoformat(),
                "member_count": member_count,
                "claims_per_member": 2.5,
            },
            timeout=120,
        )
        if r.status_code in (200, 201):
            result = r.json()
            return result.get("claims_generated", 0), result.get("claims_loaded", 0), None
        return 0, 0, r.text[:200]
    except Exception as e:
        return 0, 0, str(e)[:200]


def refresh_baseline(policy_id: str = None):
    """Refresh baseline (general or policy-specific)"""
    try:
        payload = {
            "baseline_type": "ROLLING",
            "window_months": 12,
            "refresh_reason": "MANUAL",
        }
        if policy_id:
            payload["policy_id"] = policy_id
        r = requests.post(
            f"{API_BASE_URL}/baselines/refresh",
            headers=HEADERS,
            json=payload,
            timeout=60,
        )
        if r.status_code in (200, 201):
            return r.json(), None
        return None, r.text[:300]
    except Exception as e:
        return None, str(e)[:200]


def get_latest_baseline(policy_id: str = None):
    """Get latest baseline"""
    try:
        params = {}
        if policy_id:
            params["policy_id"] = policy_id
        r = requests.get(
            f"{API_BASE_URL}/baselines/latest",
            headers=HEADERS,
            params=params or None,
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return None


def regenerate_predicted_impact_all(force: bool = True):
    """Regenerate predicted impact for all policies with levers"""
    try:
        r = requests.post(
            f"{API_BASE_URL}/policies/generate-predicted-impact",
            headers=HEADERS,
            params={"force": str(force).lower()},
            timeout=300,
        )
        if r.status_code == 200:
            return r.json(), None
        return None, r.text[:300]
    except Exception as e:
        return None, str(e)[:200]


def main():
    print("\n" + "=" * 60)
    print("Phase 1 & 2: Data Foundation and Predicted Impact")
    print("=" * 60)

    # Phase 1.1: Claims data
    print("\n📋 Phase 1.1: Claims Data")
    print("-" * 40)
    policies = get_policies()
    if not policies:
        print("❌ No policies found")
        sys.exit(1)
    print(f"   Found {len(policies)} policies")

    # Generate claims for first of each month for past 12 months (for baseline)
    today = date.today()
    unique_dates = []
    for i in range(12):
        # Go back i months
        y, m = today.year, today.month
        m -= i
        while m <= 0:
            m += 12
            y -= 1
        unique_dates.append(date(y, m, 1))

    total_generated = 0
    total_loaded = 0
    for i, d in enumerate(unique_dates):
        gen, loaded, err = generate_claims_for_date(d)
        if err:
            print(f"   ⚠️  {d}: {err}")
        else:
            total_generated += gen
            total_loaded += loaded
            print(f"   [{i+1}/{len(unique_dates)}] {d}: {gen} generated, {loaded} loaded")

    # Generate policy-scoped claims for 10-15 demo policies (if general claims weren't enough)
    demo_policies = [p for p in policies if p.get("policy_metadata_json", {}).get("policy_levers")][:15]
    if total_loaded == 0 and demo_policies:
        print("   No general claims - trying policy-scoped for demo policies...")
        for i, p in enumerate(demo_policies[:10]):
            pid = p.get("id") or p.get("policy_id")
            gen, loaded, err = generate_policy_scoped_claims(pid, today - timedelta(days=30))
            if loaded:
                total_loaded += loaded
                print(f"   Policy {p.get('name', 'Unknown')[:40]}: {loaded} loaded")

    print(f"   ✅ Total claims: {total_generated} generated, {total_loaded} loaded")

    # Phase 1.2: Baseline
    print("\n📊 Phase 1.2: Baseline Refresh")
    print("-" * 40)
    baseline, err = refresh_baseline()
    if err:
        print(f"   ⚠️  General baseline refresh failed: {err}")
        print("   (Baseline requires claims in DB for last 12 months)")
    else:
        metrics = baseline.get("baseline_metrics", {}) or baseline.get("metrics", {})
        util = metrics.get("util_rate_total_per_1000_mm") or metrics.get("utilization_per_1k", 0)
        cost = metrics.get("allowed_pmpm_total") or metrics.get("cost_pmpm", 0)
        print(f"   ✅ Baseline refreshed: util={util:.1f}/1K, cost=${cost:.2f} PMPM")

    # Verify baseline structure
    latest = get_latest_baseline()
    if latest:
        m = latest.get("baseline_metrics", {}) or latest.get("metrics", {})
        has_util = bool(m.get("util_rate_total_per_1000_mm") or m.get("utilization_per_1k"))
        has_cost = bool(m.get("allowed_pmpm_total") or m.get("cost_pmpm"))
        print(f"   Structure check: util_rate={'✓' if has_util else '✗'}, allowed_pmpm={'✓' if has_cost else '✗'}")

    # Phase 2.1: Predicted impact
    print("\n📈 Phase 2.1: Predicted Impact Regeneration")
    print("-" * 40)
    result, err = regenerate_predicted_impact_all(force=True)
    if err:
        print(f"   ❌ Error: {err}")
    else:
        print(f"   ✅ Generated: {result.get('generated', 0)}, Skipped: {result.get('skipped', 0)}, Errors: {result.get('errors', 0)}")
        if result.get("details"):
            for d in result["details"][:5]:
                icon = "✅" if d.get("status") == "generated" else "⏭️" if d.get("status") == "skipped" else "❌"
                print(f"      {icon} {d.get('policy_name', 'Unknown')[:50]}: {d.get('status', '?')}")

    print("\n" + "=" * 60)
    print("Phase 1 & 2 complete. Phase 2.2 metrics mapping is in storage_policy_predicted_impact.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
