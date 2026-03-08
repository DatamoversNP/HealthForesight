#!/usr/bin/env python3
"""Print claim counts breakdown per policy (scope + levers) - run locally to see counts."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "common", "src"))

from datetime import date, timedelta
from uuid import UUID

from uepi_api.database import SessionLocal
from uepi_api.models.policy import Policy
from uepi_api.repositories.canonical_data import CanonicalDataRepository
from uepi_api.services.policy_scoped_data_generation import extract_policy_target_codes


def main():
    db = SessionLocal()
    try:
        # Use demo tenant - same as API dev mode
        tenant_id_uuid = UUID("00000000-0000-0000-0000-000000000001")
        repo = CanonicalDataRepository(db)
        end_date = date.today()
        start_date = end_date - timedelta(days=365)

        policies = (
            db.query(Policy)
            .filter(Policy.tenant_id == tenant_id_uuid)
            .order_by(Policy.created_at.desc())
            .limit(50)
            .all()
        )

        print("=" * 100)
        print(f"CLAIM COUNTS BREAKDOWN (tenant={tenant_id_uuid}, dates={start_date}..{end_date})")
        print("=" * 100)
        print()

        for policy in policies:
            meta = getattr(policy, "policy_metadata_json", None) or {}
            scope = meta.get("scope") or {}
            policy_dict = {
                "scope": scope,
                "policy_levers": meta.get("policy_levers", []),
                "logic": meta.get("logic", {}),
                "policy_logic": meta.get("policy_logic", {}),
            }
            try:
                target_codes = extract_policy_target_codes(policy_dict)
            except Exception:
                target_codes = {}

            lever_procedure = list(set(target_codes.get("procedure_codes") or []))
            lever_service = list(set(target_codes.get("service_categories") or []))

            merged_procedure = []
            merged_service = []
            if scope.get("procedure_codes"):
                merged_procedure = (
                    scope["procedure_codes"]
                    if isinstance(scope["procedure_codes"], list)
                    else [scope["procedure_codes"]]
                )
            merged_procedure = list(set(merged_procedure + lever_procedure))
            if scope.get("service_categories"):
                merged_service = (
                    scope["service_categories"]
                    if isinstance(scope["service_categories"], list)
                    else [scope["service_categories"]]
                )
            elif scope.get("service_category"):
                merged_service = [scope["service_category"]]
            merged_service = list(set(merged_service + lever_service))

            lob_filter = scope.get("lob")
            market_filter = scope.get("markets") or scope.get("market")

            c_tenant = repo.count_claims_for_filters(
                tenant_id=tenant_id_uuid,
                start_date=start_date,
                end_date=end_date,
            )
            c_lob_market = repo.count_claims_for_filters(
                tenant_id=tenant_id_uuid,
                start_date=start_date,
                end_date=end_date,
                lob=lob_filter,
                market=market_filter,
            )
            c_plus_cpt = repo.count_claims_for_filters(
                tenant_id=tenant_id_uuid,
                start_date=start_date,
                end_date=end_date,
                lob=lob_filter,
                market=market_filter,
                cpt_codes=merged_procedure if merged_procedure else None,
                hcpcs_codes=merged_procedure if merged_procedure else None,
            )
            c_full = repo.count_claims_for_filters(
                tenant_id=tenant_id_uuid,
                start_date=start_date,
                end_date=end_date,
                lob=lob_filter,
                market=market_filter,
                cpt_codes=merged_procedure if merged_procedure else None,
                hcpcs_codes=merged_procedure if merged_procedure else None,
                service_categories=merged_service if merged_service else None,
            )
            c_current = repo.count_claims_for_filters(
                tenant_id=tenant_id_uuid,
                start_date=start_date,
                end_date=end_date,
                lob=lob_filter,
                market=market_filter,
                cpt_codes=lever_procedure if lever_procedure else None,
                hcpcs_codes=lever_procedure if lever_procedure else None,
                service_categories=lever_service if lever_service else None,
            )

            print(f"Policy: {policy.name or '(unnamed)'} [{str(policy.id)[:8]}...]")
            print(f"  lob={lob_filter}, markets={market_filter}")
            print(f"  procedure: scope={len(scope.get('procedure_codes') or []) if isinstance(scope.get('procedure_codes'), list) else (1 if scope.get('procedure_codes') else 0)}, levers={len(lever_procedure)}, merged={len(merged_procedure)}")
            print(f"  service:   scope={len(scope.get('service_categories') or []) if isinstance(scope.get('service_categories'), list) else (1 if scope.get('service_category') else 0)}, levers={len(lever_service)}, merged={len(merged_service)}")
            print(f"  COUNTS:")
            print(f"    tenant+date only:         {c_tenant:>8}")
            print(f"    + LOB+market:             {c_lob_market:>8}")
            print(f"    + procedure merged:       {c_plus_cpt:>8}")
            print(f"    + service full (scope+levers): {c_full:>8}  <-- full scope")
            print(f"    current endpoint (levers only): {c_current:>8}")
            print()

    finally:
        db.close()


if __name__ == "__main__":
    main()
