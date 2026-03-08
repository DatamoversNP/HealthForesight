#!/usr/bin/env python3
"""Load synthetic data directly into database using repository"""
import sys
import pandas as pd
from pathlib import Path
from uuid import uuid4

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.database import SessionLocal
from uepi_api.repositories.canonical_data import CanonicalDataRepository
from uepi_api.storage_auth import DEFAULT_TENANT_ID

def load_claims():
    """Load claims lines"""
    print("\nLoading Claims Lines...")
    source_file = Path("apps/api/data/source_data") / str(DEFAULT_TENANT_ID) / "claims_lines.csv"
    
    if not source_file.exists():
        print(f"  ❌ File not found: {source_file}")
        return False
    
    print(f"  Reading {source_file.name} ({source_file.stat().st_size / (1024*1024):.1f} MB)...")
    
    # Read in chunks to avoid memory issues
    chunk_size = 50000
    total_loaded = 0
    
    db = SessionLocal()
    try:
        repo = CanonicalDataRepository(db)
        
        for chunk_num, chunk_df in enumerate(pd.read_csv(source_file, chunksize=chunk_size), 1):
            print(f"  Processing chunk {chunk_num} ({len(chunk_df):,} records)...")
            
            # Convert to dict format expected by repository
            records = []
            for _, row in chunk_df.iterrows():
                record = {
                    "claim_id": str(row.get("claim_id", "")),
                    "claim_line_id": str(row.get("claim_line_id", "")),
                    "member_id": str(row.get("member_id", "")),
                    "provider_id": str(row.get("provider_id", "")),
                    "service_date": pd.to_datetime(row.get("service_date")).date() if pd.notna(row.get("service_date")) else None,
                    "paid_date": pd.to_datetime(row.get("paid_date")).date() if pd.notna(row.get("paid_date")) else None,
                    "adjudication_date": pd.to_datetime(row.get("adjudication_date")).date() if pd.notna(row.get("adjudication_date")) else None,
                    "lob": str(row.get("lob", "")),
                    "market": str(row.get("market", "")),
                    "cpt_code": str(row.get("cpt_code", "")) if pd.notna(row.get("cpt_code")) else None,
                    "hcpcs_code": str(row.get("hcpcs_code", "")) if pd.notna(row.get("hcpcs_code")) else None,
                    "drg_code": str(row.get("drg_code", "")) if pd.notna(row.get("drg_code")) else None,
                    "icd10_diagnosis_codes": eval(row.get("icd10_diagnosis_codes")) if pd.notna(row.get("icd10_diagnosis_codes")) and str(row.get("icd10_diagnosis_codes")).startswith("[") else None,
                    "icd10_procedure_codes": eval(row.get("icd10_procedure_codes")) if pd.notna(row.get("icd10_procedure_codes")) and str(row.get("icd10_procedure_codes")).startswith("[") else None,
                    "service_category": str(row.get("service_category", "")),
                    "place_of_service": str(row.get("place_of_service", "")),
                    "units": float(row.get("units", 1.0)),
                    "allowed_amount": float(row.get("allowed_amount", 0.0)),
                    "paid_amount": float(row.get("paid_amount", 0.0)),
                    "member_cost_share": float(row.get("member_cost_share", 0.0)),
                    "in_network": bool(row.get("in_network", True)),
                    "requires_prior_auth": bool(row.get("requires_prior_auth", False)),
                    "prior_auth_approved": bool(row.get("prior_auth_approved")) if pd.notna(row.get("prior_auth_approved")) else None,
                    "prior_auth_id": str(row.get("prior_auth_id", "")) if pd.notna(row.get("prior_auth_id")) else None,
                    "facility_type": str(row.get("facility_type", "")) if pd.notna(row.get("facility_type")) else None,
                    "system_affiliation": str(row.get("system_affiliation", "")) if pd.notna(row.get("system_affiliation")) else None,
                    "rendering_provider_id": str(row.get("rendering_provider_id", "")) if pd.notna(row.get("rendering_provider_id")) else None,
                    "billing_provider_id": str(row.get("billing_provider_id", "")) if pd.notna(row.get("billing_provider_id")) else None,
                    "referring_provider_id": str(row.get("referring_provider_id", "")) if pd.notna(row.get("referring_provider_id")) else None,
                    "source_system": str(row.get("source_system", "SYNTHETIC_GENERATOR")),
                    "source_file_id": str(row.get("source_file_id", source_file.name)),
                    "ingestion_id": uuid4(),
                }
                records.append(record)
            
            # Bulk insert
            try:
                repo.bulk_insert_claims_lines(DEFAULT_TENANT_ID, records)
                db.commit()
                total_loaded += len(records)
                print(f"    ✅ Loaded {len(records):,} records (total: {total_loaded:,})")
            except Exception as e:
                db.rollback()
                print(f"    ⚠️  Error loading chunk: {e}")
                # Continue with next chunk
        
        print(f"\n  ✅ Total claims loaded: {total_loaded:,}")
        return total_loaded > 0
        
    except Exception as e:
        db.rollback()
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def load_enrollment():
    """Load enrollment records"""
    print("\nLoading Enrollment Records...")
    source_file = Path("apps/api/data/source_data") / str(DEFAULT_TENANT_ID) / "enrollment.csv"
    
    if not source_file.exists():
        print(f"  ❌ File not found: {source_file}")
        return False
    
    print(f"  Reading {source_file.name}...")
    
    db = SessionLocal()
    try:
        repo = CanonicalDataRepository(db)
        df = pd.read_csv(source_file)
        
        # Deduplicate by member_id + enrollment_month
        df = df.drop_duplicates(subset=["member_id", "enrollment_month"])
        
        records = []
        for _, row in df.iterrows():
            record = {
                "member_id": str(row.get("member_id", "")),
                "enrollment_month": pd.to_datetime(row.get("enrollment_month")).date() if pd.notna(row.get("enrollment_month")) else None,
                "lob": str(row.get("lob", "")),
                "market": str(row.get("market", "")),
                "age_band": str(row.get("age_band", "")) if pd.notna(row.get("age_band")) else None,
                "gender": str(row.get("gender", "")) if pd.notna(row.get("gender")) else None,
                "risk_score": float(row.get("risk_score", 1.0)) if pd.notna(row.get("risk_score")) else None,
                "network_tier": str(row.get("network_tier", "")) if pd.notna(row.get("network_tier")) else None,
                "enrolled_flag": bool(row.get("enrolled_flag", True)),
                "enrollment_start_date": pd.to_datetime(row.get("enrollment_start_date")).date() if pd.notna(row.get("enrollment_start_date")) else None,
                "enrollment_end_date": pd.to_datetime(row.get("enrollment_end_date")).date() if pd.notna(row.get("enrollment_end_date")) else None,
                "product_type": str(row.get("product_type", "")) if pd.notna(row.get("product_type")) else None,
                "segment": str(row.get("segment", "")) if pd.notna(row.get("segment")) else None,
                "source_system": "SYNTHETIC_GENERATOR",
                "source_file_id": source_file.name,
                "ingestion_id": uuid4(),
            }
            records.append(record)
        
        repo.bulk_insert_enrollment_records(DEFAULT_TENANT_ID, records)
        db.commit()
        
        print(f"  ✅ Loaded {len(records):,} enrollment records")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def load_providers():
    """Load provider records"""
    print("\nLoading Provider Records...")
    source_file = Path("apps/api/data/source_data") / str(DEFAULT_TENANT_ID) / "providers.csv"
    
    if not source_file.exists():
        print(f"  ❌ File not found: {source_file}")
        return False
    
    print(f"  Reading {source_file.name}...")
    
    db = SessionLocal()
    try:
        repo = CanonicalDataRepository(db)
        df = pd.read_csv(source_file)
        
        records = []
        for _, row in df.iterrows():
            record = {
                "provider_id": str(row.get("provider_id", "")),
                "npi": str(row.get("npi", "")) if pd.notna(row.get("npi")) else None,
                "provider_type": str(row.get("provider_type", "")),
                "specialty": str(row.get("specialty", "")) if pd.notna(row.get("specialty")) else None,
                "facility_type": str(row.get("facility_type", "")) if pd.notna(row.get("facility_type")) else None,
                "market": str(row.get("market", "")),
                "state": str(row.get("state", "")) if pd.notna(row.get("state")) else None,
                "zip_code": str(row.get("zip_code", "")) if pd.notna(row.get("zip_code")) else None,
                "network_status": str(row.get("network_status", "")),
                "effective_date": pd.to_datetime(row.get("effective_date")).date() if pd.notna(row.get("effective_date")) else None,
                "termination_date": pd.to_datetime(row.get("termination_date")).date() if pd.notna(row.get("termination_date")) else None,
                "system_affiliation": str(row.get("system_affiliation", "")) if pd.notna(row.get("system_affiliation")) else None,
                "system_id": str(row.get("system_id", "")) if pd.notna(row.get("system_id")) else None,
                "provider_name": str(row.get("provider_name", "")) if pd.notna(row.get("provider_name")) else None,
                "tax_id": str(row.get("tax_id", "")) if pd.notna(row.get("tax_id")) else None,
                "source_system": "SYNTHETIC_GENERATOR",
                "source_file_id": source_file.name,
                "ingestion_id": uuid4(),
            }
            records.append(record)
        
        repo.bulk_insert_provider_records(DEFAULT_TENANT_ID, records)
        db.commit()
        
        print(f"  ✅ Loaded {len(records):,} provider records")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def main():
    print("="*60)
    print("LOADING DATA DIRECTLY TO DATABASE")
    print("="*60)
    
    results = {}
    
    # Load claims (this is the big one)
    results['claims'] = load_claims()
    
    # Load enrollment
    results['enrollment'] = load_enrollment()
    
    # Load providers
    results['providers'] = load_providers()
    
    # Verify
    print("\n" + "="*60)
    print("Verification")
    print("="*60)
    
    db = SessionLocal()
    try:
        repo = CanonicalDataRepository(db)
        
        claims_count = repo.count_claims_lines(DEFAULT_TENANT_ID)
        enrollment_count = repo.count_enrollment_records(DEFAULT_TENANT_ID)
        provider_count = repo.count_provider_records(DEFAULT_TENANT_ID)
        
        print(f"  Claims Lines: {claims_count:,}")
        print(f"  Enrollment Records: {enrollment_count:,}")
        print(f"  Provider Records: {provider_count:,}")
        
        if claims_count > 0 or enrollment_count > 0 or provider_count > 0:
            print("\n  ✅ Data successfully loaded into database!")
            return 0
        else:
            print("\n  ⚠️  No data in database")
            return 1
    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(main())

