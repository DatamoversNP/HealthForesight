#!/usr/bin/env python3
"""
Phase 3: Load historical demo data from CSVs (from Phase 2 output) into PostgreSQL.

Reads claims_lines.csv, enrollment.csv, providers.csv from --input-dir and bulk inserts
via CanonicalDataRepository. Use after Phase 1 (clean) and Phase 2 (generate).

Run from repo root:
  python3 scripts/load_fresh_demo_historical.py --input-dir data/source_data/00000000-0000-0000-0000-000000000001/historical
"""
import argparse
import ast
import sys
from pathlib import Path
from uuid import UUID, uuid4
from datetime import date
from decimal import Decimal

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
CHUNK_SIZE = 25_000


def parse_date(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        return date.fromisoformat(v[:10])
    return None


def _safe_list(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if not s or s == "nan":
        return None
    if s.startswith("["):
        try:
            return ast.literal_eval(s)
        except Exception:
            return None
    return None


def _normalize_code(val):
    """Normalize CPT/HCPCS so 72148.0 from pandas becomes '72148' for DB filter match."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, float):
        if val != val:  # NaN
            return None
        val = int(val) if val == int(val) else val
    s = str(val).strip()
    if not s or s.lower() == "nan":
        return None
    return s


def main():
    parser = argparse.ArgumentParser(description="Load historical demo CSVs into database")
    parser.add_argument("--input-dir", type=str, default=None, help="Directory containing claims_lines.csv, enrollment.csv, providers.csv")
    parser.add_argument("--tenant-id", type=str, default=str(DEFAULT_TENANT_ID))
    parser.add_argument("--skip-providers", action="store_true", help="Skip loading providers (use when they were already loaded, e.g. observation-period load)")
    args = parser.parse_args()
    tenant_id = UUID(args.tenant_id)
    input_dir = Path(args.input_dir) if args.input_dir else PROJECT_ROOT / "data" / "source_data" / args.tenant_id / "historical"
    if not input_dir.exists():
        print(f"Error: input dir not found: {input_dir}")
        sys.exit(1)

    from uepi_api.database import SessionLocal
    from uepi_api.repositories.canonical_data import CanonicalDataRepository

    ingestion_id = uuid4()
    source_system = "FRESH_DEMO_HISTORICAL"
    db = SessionLocal()
    repo = CanonicalDataRepository(db)

    print("=" * 60)
    print("PHASE 3: Load historical data into DB")
    print("=" * 60)
    print(f"Input: {input_dir}")
    print(f"Tenant: {tenant_id}")
    print()

    # 1. Claims
    claims_file = input_dir / "claims_lines.csv"
    if claims_file.exists():
        print("1. Loading claims_lines...")
        total = 0
        for chunk_num, chunk in enumerate(pd.read_csv(claims_file, chunksize=CHUNK_SIZE), 1):
            records = []
            for _, row in chunk.iterrows():
                records.append({
                    "claim_id": str(row.get("claim_id", "")),
                    "claim_line_id": str(row.get("claim_line_id", "")),
                    "member_id": str(row.get("member_id", "")),
                    "provider_id": str(row.get("provider_id", "")),
                    "service_date": parse_date(row.get("service_date")),
                    "paid_date": parse_date(row.get("paid_date")),
                    "adjudication_date": parse_date(row.get("adjudication_date")),
                    "lob": str(row.get("lob", "")),
                    "market": str(row.get("market", "")),
                    "cpt_code": _normalize_code(row.get("cpt_code")),
                    "hcpcs_code": _normalize_code(row.get("hcpcs_code")),
                    "drg_code": str(row.get("drg_code")) if pd.notna(row.get("drg_code")) else None,
                    "icd10_diagnosis_codes": _safe_list(row.get("icd10_diagnosis_codes")),
                    "icd10_procedure_codes": _safe_list(row.get("icd10_procedure_codes")),
                    "service_category": str(row.get("service_category", "")),
                    "place_of_service": str(row.get("place_of_service", "11")),
                    "units": float(row.get("units", 1)),
                    "allowed_amount": float(row.get("allowed_amount", 0)),
                    "paid_amount": float(row.get("paid_amount", 0)),
                    "member_cost_share": float(row.get("member_cost_share", 0)),
                    "in_network": bool(row.get("in_network", True)) if isinstance(row.get("in_network"), bool) else str(row.get("in_network", "true")).lower() in ("true", "1", "yes"),
                    "requires_prior_auth": bool(row.get("requires_prior_auth", False)) if isinstance(row.get("requires_prior_auth"), bool) else str(row.get("requires_prior_auth", "false")).lower() in ("true", "1", "yes"),
                    "prior_auth_approved": None if pd.isna(row.get("prior_auth_approved")) else bool(row.get("prior_auth_approved")),
                    "prior_auth_id": str(row.get("prior_auth_id")) if pd.notna(row.get("prior_auth_id")) else None,
                    "facility_type": str(row.get("facility_type")) if pd.notna(row.get("facility_type")) else None,
                    "system_affiliation": str(row.get("system_affiliation")) if pd.notna(row.get("system_affiliation")) else None,
                    "rendering_provider_id": str(row.get("rendering_provider_id")) if pd.notna(row.get("rendering_provider_id")) else None,
                    "billing_provider_id": str(row.get("billing_provider_id")) if pd.notna(row.get("billing_provider_id")) else None,
                    "referring_provider_id": str(row.get("referring_provider_id")) if pd.notna(row.get("referring_provider_id")) else None,
                })
            n = repo.bulk_insert_claims_lines(tenant_id, records, source_system, claims_file.name, ingestion_id)
            total += n
            print(f"   Chunk {chunk_num}: {n:,} rows (total {total:,})")
        print(f"   Done. Total claims_lines: {total:,}")
    else:
        print("1. claims_lines.csv not found; skip.")

    # 2. Enrollment
    enrollment_file = input_dir / "enrollment.csv"
    if enrollment_file.exists():
        print("2. Loading enrollment_records...")
        total = 0
        for chunk_num, chunk in enumerate(pd.read_csv(enrollment_file, chunksize=CHUNK_SIZE), 1):
            records = []
            for _, row in chunk.iterrows():
                records.append({
                    "member_id": str(row.get("member_id", "")),
                    "enrollment_month": parse_date(row.get("enrollment_month")),
                    "lob": str(row.get("lob", "")),
                    "market": str(row.get("market", "")),
                    "age_band": str(row.get("age_band", "")),
                    "gender": str(row.get("gender", "")),
                    "risk_score": float(row.get("risk_score", 0)),
                    "network_tier": str(row.get("network_tier", "")),
                    "enrolled_flag": bool(row.get("enrolled_flag", True)) if isinstance(row.get("enrolled_flag"), bool) else str(row.get("enrolled_flag", "true")).lower() in ("true", "1", "yes"),
                    "enrollment_start_date": parse_date(row.get("enrollment_start_date")),
                    "enrollment_end_date": parse_date(row.get("enrollment_end_date")),
                    "product_type": str(row.get("product_type")) if pd.notna(row.get("product_type")) else None,
                    "segment": str(row.get("segment")) if pd.notna(row.get("segment")) else None,
                })
            n = repo.bulk_insert_enrollment_records(tenant_id, records, source_system, enrollment_file.name, ingestion_id)
            total += n
            print(f"   Chunk {chunk_num}: {n:,} rows (total {total:,})")
        print(f"   Done. Total enrollment_records: {total:,}")
    else:
        print("2. enrollment.csv not found; skip.")

    # 3. Providers (optional – skip if --skip-providers, e.g. observation-period reuses same providers)
    provider_file = input_dir / "providers.csv"
    if args.skip_providers:
        print("3. Skipping providers (--skip-providers).")
    elif provider_file.exists():
        try:
            from uepi_api.models.canonical_data import ProviderRecordDB
            df = pd.read_csv(provider_file)
            # If repository has bulk_insert_provider_records use it; else skip (baseline may not require providers table)
            if hasattr(repo, "bulk_insert_provider_records"):
                records = []
                for _, row in df.iterrows():
                    records.append({
                        "provider_id": str(row.get("provider_id", "")),
                        "npi": str(row.get("npi")) if pd.notna(row.get("npi")) else None,
                        "provider_type": str(row.get("provider_type", "")),
                        "specialty": str(row.get("specialty")) if pd.notna(row.get("specialty")) else None,
                        "facility_type": str(row.get("facility_type")) if pd.notna(row.get("facility_type")) else None,
                        "market": str(row.get("market", "")),
                        "state": str(row.get("state")) if pd.notna(row.get("state")) else None,
                        "zip_code": str(row.get("zip_code")) if pd.notna(row.get("zip_code")) else None,
                        "network_status": str(row.get("network_status", "")),
                        "effective_date": parse_date(row.get("effective_date")),
                        "termination_date": parse_date(row.get("termination_date")),
                        "system_affiliation": str(row.get("system_affiliation")) if pd.notna(row.get("system_affiliation")) else None,
                        "system_id": str(row.get("system_id")) if pd.notna(row.get("system_id")) else None,
                        "provider_name": str(row.get("provider_name")) if pd.notna(row.get("provider_name")) else None,
                        "tax_id": str(row.get("tax_id")) if pd.notna(row.get("tax_id")) else None,
                    })
                n = repo.bulk_insert_provider_records(tenant_id, records, source_system, provider_file.name, ingestion_id)
                print(f"3. Loaded {n:,} provider_records")
            else:
                print("3. providers.csv present but no bulk_insert_provider_records; skip.")
        except Exception as e:
            print(f"3. Skip providers: {e}")
    else:
        print("3. providers.csv not found; skip.")

    db.close()
    print()
    print("=" * 60)
    print("Phase 3 complete. Next: Phase 4 (baseline refresh + predicted impact).")
    print("=" * 60)


if __name__ == "__main__":
    main()
