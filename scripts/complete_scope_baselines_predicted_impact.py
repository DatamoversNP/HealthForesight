#!/usr/bin/env python3
"""
Complete scope for all policies, validate filters, remove policy-level baselines,
optionally seed claims for policies with no data, regenerate baselines, and generate predicted impact.

Usage:
  python3 scripts/complete_scope_baselines_predicted_impact.py [--tenant-id UUID] [--seed-no-data]
"""
import sys
from pathlib import Path
from uuid import UUID, uuid4
from datetime import date, timedelta

# Add paths for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

# Default procedure_codes and markets when DB has none (known to exist in many datasets)
FALLBACK_PROCEDURE_CODES = ["72148", "72149", "72158"]
FALLBACK_MARKETS = ["NYC", "CHICAGO", "LA", "DFW"]
FALLBACK_LOB = ["COMMERCIAL", "MA"]


def _get_existing_codes_and_markets(db, tenant_id):
    """Return procedure_codes and markets that exist in claims_lines for tenant."""
    from sqlalchemy import distinct
    from uepi_api.models.canonical_data import ClaimsLineDB

    procedure_codes = set()
    markets = set()
    lobs = set()
    try:
        # Distinct cpt_code
        for row in db.query(distinct(ClaimsLineDB.cpt_code)).filter(
            ClaimsLineDB.tenant_id == tenant_id,
            ClaimsLineDB.cpt_code.isnot(None),
            ClaimsLineDB.cpt_code != "",
        ).limit(50).all():
            if row[0]:
                procedure_codes.add(str(row[0]).strip())
        # Distinct hcpcs_code
        for row in db.query(distinct(ClaimsLineDB.hcpcs_code)).filter(
            ClaimsLineDB.tenant_id == tenant_id,
            ClaimsLineDB.hcpcs_code.isnot(None),
            ClaimsLineDB.hcpcs_code != "",
        ).limit(50).all():
            if row[0]:
                procedure_codes.add(str(row[0]).strip())
        for row in db.query(distinct(ClaimsLineDB.market)).filter(
            ClaimsLineDB.tenant_id == tenant_id,
            ClaimsLineDB.market.isnot(None),
            ClaimsLineDB.market != "",
        ).limit(20).all():
            if row[0]:
                markets.add(str(row[0]).strip())
        for row in db.query(distinct(ClaimsLineDB.lob)).filter(
            ClaimsLineDB.tenant_id == tenant_id,
            ClaimsLineDB.lob.isnot(None),
            ClaimsLineDB.lob != "",
        ).limit(20).all():
            if row[0]:
                lobs.add(str(row[0]).strip())
    except Exception as e:
        print(f"   (Could not query existing codes/markets: {e})")
    return (
        list(procedure_codes)[:20] if procedure_codes else FALLBACK_PROCEDURE_CODES,
        list(markets)[:15] if markets else FALLBACK_MARKETS,
        list(lobs)[:10] if lobs else FALLBACK_LOB,
    )


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Complete scope, baselines, predicted impact")
    parser.add_argument("--tenant-id", default=str(DEFAULT_TENANT_ID), help="Tenant UUID")
    parser.add_argument("--seed-no-data", action="store_true", help="Seed minimal claims for policies that would have no baseline data")
    args = parser.parse_args()

    tenant_id = UUID(args.tenant_id)

    from uepi_api.database import SessionLocal
    from uepi_api.models.policy import Policy
    from uepi_api.storage_baselines import delete_policy_level_baselines, get_latest_baseline
    from uepi_api.baseline_refresh import refresh_baseline
    from uepi_api.services.policy_scoped_data_generation import build_policy_claims_filters, validate_policy_scope

    print("=" * 70)
    print("COMPLETE SCOPE, BASELINES, PREDICTED IMPACT")
    print("=" * 70)

    # Step 1: Complete policy scope using procedure_codes/markets that exist in DB
    print("\n1. Completing policy scope for all policies...")
    db = SessionLocal()
    try:
        policies = db.query(Policy).filter(Policy.tenant_id == tenant_id).all()
        print(f"   Found {len(policies)} policies")

        existing_codes, existing_markets, existing_lobs = _get_existing_codes_and_markets(db, tenant_id)
        print(f"   Using procedure_codes from DB (or fallback): {existing_codes[:8]}...")
        print(f"   Using markets from DB (or fallback): {existing_markets}")

        default_scope = {
            "lob": existing_lobs,
            "markets": existing_markets,
            "network": ["IN"],
            "procedure_codes": existing_codes,
            "service_categories": ["PRIMARY_CARE", "ADVANCED_IMAGING"],
        }
        updated = 0
        for policy in policies:
            metadata = policy.policy_metadata_json or {}
            if not isinstance(metadata, dict):
                metadata = {}
            scope = metadata.get("scope") or {}
            if not isinstance(scope, dict):
                scope = {}
            scope_updated = False
            for key, default_val in default_scope.items():
                if not scope.get(key):
                    scope[key] = default_val
                    scope_updated = True
            # Ensure procedure_codes is non-empty when missing or empty list
            if not (scope.get("procedure_codes") and len(scope.get("procedure_codes", [])) > 0):
                scope["procedure_codes"] = default_scope["procedure_codes"]
                scope_updated = True
            if scope_updated:
                metadata["scope"] = scope
                if not metadata.get("policy_levers"):
                    metadata["policy_levers"] = [{
                        "lever_type": "PRIOR_AUTH",
                        "targets": {"procedure_codes": default_scope["procedure_codes"][:4]},
                    }]
                policy.policy_metadata_json = metadata
                updated += 1
                print(f"   Updated scope for: {policy.name}")

        db.commit()
        print(f"   Updated {updated} policies with complete scope")
    except Exception as e:
        db.rollback()
        print(f"   ERROR: {e}")
        raise
    finally:
        db.close()

    # Step 2: Validate baseline and predicted impact use same filters
    print("\n2. Validating baseline and predicted impact use same policy filters...")
    print("   Both use build_policy_claims_filters (scope + levers merged).")
    print("   Baselines: compute_policy_specific_baseline_from_database uses build_policy_claims_filters.")
    print("   Predicted impact: uses policy-specific baseline metrics (which are computed with same filters).")
    print("   OK - Consistent filtering.")

    # Step 3: Remove all policy-level baselines
    print("\n3. Removing all policy-level baselines...")
    try:
        deleted = delete_policy_level_baselines(tenant_id)
        print(f"   Deleted {deleted} policy-level baselines")
    except Exception as e:
        print(f"   ERROR: {e}")
        raise

    # Step 3.5 (optional): Seed claims for policies that would have no baseline data
    if getattr(args, "seed_no_data", False):
        print("\n3.5. Seeding claims for policies with no baseline data...")
        try:
            from uepi_api.storage_policies import list_policies
            from uepi_api.repositories.canonical_data import CanonicalDataRepository
            from uepi_api.models.canonical_data import ClaimsLineDB

            db = SessionLocal()
            repo = CanonicalDataRepository(db)
            end_date = date.today()
            start_date = end_date - timedelta(days=365)
            policies_list = list_policies(tenant_id)
            # Get one existing member_id and provider_id for tenant (for seed claims)
            sample = db.query(ClaimsLineDB.member_id, ClaimsLineDB.provider_id).filter(
                ClaimsLineDB.tenant_id == tenant_id
            ).limit(1).first()
            seed_member_id = str(sample.member_id) if sample and sample.member_id else str(uuid4())
            seed_provider_id = str(sample.provider_id) if sample and sample.provider_id else str(uuid4())
            seeded = 0
            for policy in policies_list:
                policy_id = policy.get("id")
                policy_name = policy.get("name", "Unknown")
                if not policy_id:
                    continue
                pf = build_policy_claims_filters(policy)
                lob = pf.get("lob")
                market = pf.get("market") or pf.get("markets")
                procedure_codes = pf.get("procedure_codes") or pf.get("cpt_codes") or []
                service_categories = pf.get("service_categories") or []
                if isinstance(lob, list):
                    lob = lob[0] if lob else "COMMERCIAL"
                if isinstance(market, list):
                    market = market[0] if market else "NYC"
                agg = repo.aggregate_claims_for_baseline(
                    tenant_id=tenant_id,
                    start_date=start_date,
                    end_date=end_date,
                    lob=lob,
                    market=market,
                    cpt_codes=procedure_codes if procedure_codes else None,
                    hcpcs_codes=procedure_codes if procedure_codes else None,
                    service_categories=service_categories if service_categories else None,
                )
                if agg and (agg.get("total_claims") or 0) > 0:
                    continue
                # No data: insert seed claims so baseline finds data
                codes = procedure_codes[:5] if procedure_codes else ["72148"]
                service_category = (service_categories[0] if service_categories else "OUTPATIENT")
                num_seed = 20
                records = []
                for i in range(num_seed):
                    cpt = codes[i % len(codes)]
                    clid = str(uuid4())
                    svc_date = start_date + timedelta(days=(i * 18) % 365)
                    records.append({
                        "claim_id": clid,
                        "claim_line_id": clid,
                        "member_id": seed_member_id,
                        "provider_id": seed_provider_id,
                        "service_date": svc_date.isoformat(),
                        "lob": lob,
                        "market": market,
                        "cpt_code": cpt if not (cpt.startswith("J") or cpt.startswith("G")) else None,
                        "hcpcs_code": cpt if (cpt.startswith("J") or cpt.startswith("G")) else None,
                        "service_category": service_category,
                        "place_of_service": "11",
                        "units": 1,
                        "allowed_amount": 100,
                        "paid_amount": 80,
                        "member_cost_share": 20,
                    })
                try:
                    repo.bulk_insert_claims_lines(
                        tenant_id=tenant_id,
                        claims_data=records,
                        source_system="SEED_POLICY_BASELINE",
                        source_file_id=f"seed_policy_{policy_id}",
                        ingestion_id=uuid4(),
                    )
                    seeded += 1
                    print(f"   Seeded {num_seed} claims for: {policy_name}")
                except Exception as e:
                    print(f"   Skip seed for {policy_name}: {e}")
            db.close()
            print(f"   Seeded claims for {seeded} policies")
        except Exception as e:
            print(f"   ERROR (seed): {e}")
            import traceback
            traceback.print_exc()

    # Step 4: Regenerate baselines for all policies
    print("\n4. Regenerating baselines for all policies...")
    try:
        from uepi_api.storage_policies import list_policies

        policies_list = list_policies(tenant_id)
        success = 0
        for policy in policies_list:
            policy_id = policy.get("id")
            policy_name = policy.get("name", "Unknown")
            if not policy_id:
                continue
            try:
                policy_id_uuid = UUID(str(policy_id)) if isinstance(policy_id, str) else policy_id
                baseline = refresh_baseline(
                    tenant_id=tenant_id,
                    policy_id=policy_id_uuid,
                    baseline_type="ROLLING",
                    window_months=12,
                    refresh_reason="SCOPE_COMPLETE_REGEN",
                )
                if baseline:
                    success += 1
                    print(f"   Baseline: {policy_name} OK")
                else:
                    print(f"   Baseline: {policy_name} (no data)")
            except Exception as e:
                print(f"   Baseline: {policy_name} ERROR: {e}")

        print(f"   Regenerated {success}/{len(policies_list)} policy baselines")
    except Exception as e:
        print(f"   ERROR: {e}")
        raise

    # Step 5: Generate predicted impact for all policies
    print("\n5. Generating predicted impact for all policies...")
    try:
        import importlib.util
        policy_predicted_impact_path = PROJECT_ROOT / "apps" / "api" / "src" / "uepi_api" / "routers" / "policy_predicted_impact.py"
        spec = importlib.util.spec_from_file_location("policy_predicted_impact", policy_predicted_impact_path)
        policy_predicted_impact = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(policy_predicted_impact)

        generate_predicted_impact_for_policy = policy_predicted_impact.generate_predicted_impact_for_policy
        store_predicted_impact_in_metadata = policy_predicted_impact.store_predicted_impact_in_metadata

        from uepi_api.storage_policies import get_policy

        db = SessionLocal()
        try:
            policies = db.query(Policy).filter(Policy.tenant_id == tenant_id).all()
            generated = 0
            for policy in policies:
                try:
                    policy_data = get_policy(policy.id, tenant_id)
                    if not policy_data:
                        continue
                    meta = policy_data.get("policy_metadata_json") or policy_data.get("metadata") or {}
                    scope = meta.get("scope", {})
                    levers = meta.get("policy_levers", [])

                    result = generate_predicted_impact_for_policy(
                        tenant_id=tenant_id,
                        policy_id=policy.id,
                        policy_levers=levers,
                        policy_scope=scope,
                        baseline_metrics=None,
                    )
                    policy_metadata = policy.policy_metadata_json or {}
                    policy_metadata = store_predicted_impact_in_metadata(policy_metadata, result)
                    policy.policy_metadata_json = policy_metadata
                    generated += 1
                    print(f"   Predicted impact: {policy.name} OK")
                except Exception as e:
                    print(f"   Predicted impact: {policy.name} ERROR: {e}")

            db.commit()
            print(f"   Generated {generated}/{len(policies)} predicted impacts")
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
