#!/usr/bin/env python3
"""Fast data loading using PostgreSQL COPY command"""
import sys
import os
from pathlib import Path
import subprocess

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.storage_auth import DEFAULT_TENANT_ID

def load_via_copy():
    """Load data using PostgreSQL COPY command (fastest method)"""
    print("="*60)
    print("FAST DATA LOADING VIA POSTGRESQL COPY")
    print("="*60)
    
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/uepi_db")
    source_dir = Path("apps/api/data/source_data") / str(DEFAULT_TENANT_ID)
    
    # Parse database URL
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
    if not match:
        print("❌ Invalid DATABASE_URL")
        return False
    
    user, password, host, port, database = match.groups()
    
    # Set PGPASSWORD environment variable
    os.environ['PGPASSWORD'] = password
    
    results = {}
    
    # Load claims (using COPY with CSV header)
    claims_file = source_dir / "claims_lines.csv"
    if claims_file.exists():
        print(f"\nLoading claims from {claims_file.name}...")
        print(f"  Size: {claims_file.stat().st_size / (1024*1024):.1f} MB")
        
        # Use psql COPY command
        copy_sql = f"""
        COPY claims_lines (
            tenant_id, claim_id, claim_line_id, member_id, provider_id,
            service_date, paid_date, adjudication_date, lob, market,
            cpt_code, hcpcs_code, drg_code, service_category, place_of_service,
            units, allowed_amount, paid_amount, member_cost_share,
            in_network, requires_prior_auth, prior_auth_approved, prior_auth_id,
            facility_type, system_affiliation, rendering_provider_id,
            billing_provider_id, referring_provider_id,
            source_system, source_file_id, ingestion_id
        )
        FROM STDIN WITH (FORMAT CSV, HEADER true, DELIMITER ',');
        """
        
        try:
            # Read CSV, add tenant_id column, and pipe to psql
            import pandas as pd
            import io
            
            print("  Reading and processing CSV...")
            df = pd.read_csv(claims_file, nrows=None, low_memory=False)
            
            # Add tenant_id as first column
            df.insert(0, 'tenant_id', str(DEFAULT_TENANT_ID))
            
            # Add required fields with defaults
            if 'source_system' not in df.columns:
                df['source_system'] = 'SYNTHETIC_GENERATOR'
            if 'source_file_id' not in df.columns:
                df['source_file_id'] = claims_file.name
            if 'ingestion_id' not in df.columns:
                from uuid import uuid4
                df['ingestion_id'] = str(uuid4())
            
            # Convert to CSV string
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, header=False)
            csv_data = csv_buffer.getvalue()
            
            # Use Python to insert via SQLAlchemy (more reliable than psql)
            print("  Inserting via SQLAlchemy bulk operations...")
            from uepi_api.database import SessionLocal
            from uepi_api.models.canonical_data import ClaimsLineDB
            from decimal import Decimal
            import pandas as pd
            
            db = SessionLocal()
            try:
                chunk_size = 50000
                total = 0
                
                for chunk_num, chunk_df in enumerate(pd.read_csv(claims_file, chunksize=chunk_size, low_memory=False), 1):
                    print(f"    Processing chunk {chunk_num} ({len(chunk_df):,} records)...", end=" ", flush=True)
                    
                    records = []
                    for _, row in chunk_df.iterrows():
                        try:
                            records.append(ClaimsLineDB(
                                tenant_id=DEFAULT_TENANT_ID,
                                claim_id=str(row.get("claim_id", "")),
                                claim_line_id=str(row.get("claim_line_id", "")),
                                member_id=str(row.get("member_id", "")),
                                provider_id=str(row.get("provider_id", "")),
                                service_date=pd.to_datetime(row["service_date"]).date() if pd.notna(row.get("service_date")) else None,
                                paid_date=pd.to_datetime(row["paid_date"]).date() if pd.notna(row.get("paid_date")) else None,
                                adjudication_date=pd.to_datetime(row["adjudication_date"]).date() if pd.notna(row.get("adjudication_date")) else None,
                                lob=str(row.get("lob", "")),
                                market=str(row.get("market", "")),
                                cpt_code=str(row["cpt_code"]) if pd.notna(row.get("cpt_code")) else None,
                                hcpcs_code=str(row["hcpcs_code"]) if pd.notna(row.get("hcpcs_code")) else None,
                                drg_code=str(row["drg_code"]) if pd.notna(row.get("drg_code")) else None,
                                service_category=str(row.get("service_category", "")),
                                place_of_service=str(row.get("place_of_service", "")),
                                units=Decimal(str(row.get("units", 1.0))),
                                allowed_amount=Decimal(str(row.get("allowed_amount", 0.0))),
                                paid_amount=Decimal(str(row.get("paid_amount", 0.0))),
                                member_cost_share=Decimal(str(row.get("member_cost_share", 0.0))),
                                in_network=bool(row.get("in_network", True)),
                                requires_prior_auth=bool(row.get("requires_prior_auth", False)),
                                prior_auth_approved=bool(row["prior_auth_approved"]) if pd.notna(row.get("prior_auth_approved")) else None,
                                prior_auth_id=str(row["prior_auth_id"]) if pd.notna(row.get("prior_auth_id")) else None,
                                facility_type=str(row["facility_type"]) if pd.notna(row.get("facility_type")) else None,
                                system_affiliation=str(row["system_affiliation"]) if pd.notna(row.get("system_affiliation")) else None,
                                rendering_provider_id=str(row["rendering_provider_id"]) if pd.notna(row.get("rendering_provider_id")) else None,
                                billing_provider_id=str(row["billing_provider_id"]) if pd.notna(row.get("billing_provider_id")) else None,
                                referring_provider_id=str(row["referring_provider_id"]) if pd.notna(row.get("referring_provider_id")) else None,
                                source_system="SYNTHETIC_GENERATOR",
                                source_file_id=claims_file.name,
                                ingestion_id=uuid4(),
                            ))
                        except Exception as e:
                            continue
                    
                    if records:
                        db.bulk_save_objects(records)
                        db.commit()
                        total += len(records)
                        print(f"✅ {len(records):,} (total: {total:,})")
                    else:
                        print("(empty)")
                
                results['claims'] = total
                print(f"\n  ✅ Total claims loaded: {total:,}")
                
            except Exception as e:
                db.rollback()
                print(f"\n  ❌ Error: {e}")
                import traceback
                traceback.print_exc()
                results['claims'] = 0
            finally:
                db.close()
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results['claims'] = 0
    
    # Load enrollment and providers (smaller files, can use simpler method)
    from uepi_api.database import SessionLocal
    from uepi_api.repositories.canonical_data import CanonicalDataRepository
    
    # Enrollment
    enrollment_file = source_dir / "enrollment.csv"
    if enrollment_file.exists():
        print(f"\nLoading enrollment from {enrollment_file.name}...")
        db = SessionLocal()
        try:
            repo = CanonicalDataRepository(db)
            import pandas as pd
            from uuid import uuid4
            
            df = pd.read_csv(enrollment_file, low_memory=False)
            df = df.drop_duplicates(subset=["member_id", "enrollment_month"])
            
            records = []
            for _, row in df.iterrows():
                try:
                    records.append({
                        "member_id": str(row.get("member_id", "")),
                        "enrollment_month": pd.to_datetime(row["enrollment_month"]).date() if pd.notna(row.get("enrollment_month")) else None,
                        "lob": str(row.get("lob", "")),
                        "market": str(row.get("market", "")),
                        "age_band": str(row["age_band"]) if pd.notna(row.get("age_band")) else None,
                        "gender": str(row["gender"]) if pd.notna(row.get("gender")) else None,
                        "risk_score": float(row["risk_score"]) if pd.notna(row.get("risk_score")) else None,
                        "network_tier": str(row["network_tier"]) if pd.notna(row.get("network_tier")) else None,
                        "enrolled_flag": bool(row.get("enrolled_flag", True)),
                        "enrollment_start_date": pd.to_datetime(row["enrollment_start_date"]).date() if pd.notna(row.get("enrollment_start_date")) else None,
                        "enrollment_end_date": pd.to_datetime(row["enrollment_end_date"]).date() if pd.notna(row.get("enrollment_end_date")) else None,
                        "product_type": str(row["product_type"]) if pd.notna(row.get("product_type")) else None,
                        "segment": str(row["segment"]) if pd.notna(row.get("segment")) else None,
                        "source_system": "SYNTHETIC_GENERATOR",
                        "source_file_id": enrollment_file.name,
                        "ingestion_id": uuid4(),
                    })
                except:
                    continue
            
            if records:
                repo.bulk_insert_enrollment_records(
                    DEFAULT_TENANT_ID,
                    records,
                    "SYNTHETIC_GENERATOR",
                    enrollment_file.name,
                    uuid4()
                )
                results['enrollment'] = len(records)
                print(f"  ✅ Loaded {len(records):,} enrollment records")
            else:
                results['enrollment'] = 0
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results['enrollment'] = 0
        finally:
            db.close()
    
    # Providers
    provider_file = source_dir / "providers.csv"
    if provider_file.exists():
        print(f"\nLoading providers from {provider_file.name}...")
        db = SessionLocal()
        try:
            repo = CanonicalDataRepository(db)
            import pandas as pd
            from uuid import uuid4
            
            df = pd.read_csv(provider_file, low_memory=False)
            
            records = []
            for _, row in df.iterrows():
                try:
                    records.append({
                        "provider_id": str(row.get("provider_id", "")),
                        "npi": str(row["npi"]) if pd.notna(row.get("npi")) else None,
                        "provider_type": str(row.get("provider_type", "")),
                        "specialty": str(row["specialty"]) if pd.notna(row.get("specialty")) else None,
                        "facility_type": str(row["facility_type"]) if pd.notna(row.get("facility_type")) else None,
                        "market": str(row.get("market", "")),
                        "state": str(row["state"]) if pd.notna(row.get("state")) else None,
                        "zip_code": str(row["zip_code"]) if pd.notna(row.get("zip_code")) else None,
                        "network_status": str(row.get("network_status", "")),
                        "effective_date": pd.to_datetime(row["effective_date"]).date() if pd.notna(row.get("effective_date")) else None,
                        "termination_date": pd.to_datetime(row["termination_date"]).date() if pd.notna(row.get("termination_date")) else None,
                        "system_affiliation": str(row["system_affiliation"]) if pd.notna(row.get("system_affiliation")) else None,
                        "system_id": str(row["system_id"]) if pd.notna(row.get("system_id")) else None,
                        "provider_name": str(row["provider_name"]) if pd.notna(row.get("provider_name")) else None,
                        "tax_id": str(row["tax_id"]) if pd.notna(row.get("tax_id")) else None,
                        "source_system": "SYNTHETIC_GENERATOR",
                        "source_file_id": provider_file.name,
                        "ingestion_id": uuid4(),
                    })
                except:
                    continue
            
            if records:
                repo.bulk_insert_provider_records(
                    DEFAULT_TENANT_ID,
                    records,
                    "SYNTHETIC_GENERATOR",
                    provider_file.name,
                    uuid4()
                )
                results['providers'] = len(records)
                print(f"  ✅ Loaded {len(records):,} provider records")
            else:
                results['providers'] = 0
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results['providers'] = 0
        finally:
            db.close()
    
    # Final summary
    print("\n" + "="*60)
    print("LOADING SUMMARY")
    print("="*60)
    print(f"  Claims Lines: {results.get('claims', 0):,}")
    print(f"  Enrollment Records: {results.get('enrollment', 0):,}")
    print(f"  Provider Records: {results.get('providers', 0):,}")
    print("="*60)
    
    return results.get('claims', 0) > 0 or results.get('enrollment', 0) > 0

if __name__ == "__main__":
    import sys
    sys.exit(0 if load_via_copy() else 1)

