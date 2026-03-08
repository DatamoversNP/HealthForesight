#!/usr/bin/env python3
"""Fix claims_lines table by dropping all orphaned objects and recreating"""
import sys
from pathlib import Path
from sqlalchemy import text, inspect

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.database import engine
from uepi_api.models.canonical_data import ClaimsLineDB

def main():
    print("Fixing claims_lines table...")
    
    with engine.connect() as conn:
        try:
            # First, check if table exists
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            if 'claims_lines' in existing_tables:
                print("  ✅ Table already exists")
                return 0
            
            print("  Table does not exist, cleaning up and creating...")
            
            # Drop ALL indexes that might be related to claims_lines
            print("  Dropping orphaned indexes...")
            indexes_to_drop = [
                "ix_claims_lines_service_category",
                "ix_claims_lines_service_date",
                "ix_claims_lines_tenant_claim_line",
                "ix_claims_lines_tenant_id",
                "ix_claims_lines_member_id",
                "ix_claims_lines_provider_id",
                "ix_claims_lines_claim_id",
            ]
            
            for idx in indexes_to_drop:
                try:
                    conn.execute(text(f"DROP INDEX IF EXISTS {idx} CASCADE"))
                    print(f"    Dropped: {idx}")
                except Exception as e:
                    if "does not exist" not in str(e):
                        print(f"    Warning: {idx}: {e}")
            
            # Also try to drop the table if it exists (shouldn't, but just in case)
            try:
                conn.execute(text("DROP TABLE IF EXISTS claims_lines CASCADE"))
                print("    Dropped existing table (if any)")
            except:
                pass
            
            conn.commit()
            
            # Get all indexes from the model definition
            all_indexes = []
            for idx in ClaimsLineDB.__table_args__:
                if hasattr(idx, 'name'):
                    all_indexes.append(idx.name)
            
            # Drop all indexes one more time after table drop
            for idx_name in all_indexes:
                try:
                    conn.execute(text(f"DROP INDEX IF EXISTS {idx_name} CASCADE"))
                except:
                    pass
            
            # Also drop unique constraint
            try:
                conn.execute(text("DROP INDEX IF EXISTS uq_claims_lines_tenant_claim_line CASCADE"))
            except:
                pass
            
            conn.commit()
            
            # Now create the table using raw SQL to avoid index issues
            print("  Creating claims_lines table structure...")
            # Create table without indexes first
            create_table_sql = text("""
                CREATE TABLE IF NOT EXISTS claims_lines (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL,
                    claim_id VARCHAR NOT NULL,
                    claim_line_id VARCHAR NOT NULL,
                    member_id VARCHAR NOT NULL,
                    provider_id VARCHAR NOT NULL,
                    service_date DATE NOT NULL,
                    paid_date DATE,
                    adjudication_date DATE,
                    lob VARCHAR NOT NULL,
                    market VARCHAR NOT NULL,
                    cpt_code VARCHAR,
                    hcpcs_code VARCHAR,
                    drg_code VARCHAR,
                    icd10_diagnosis_codes VARCHAR[],
                    icd10_procedure_codes VARCHAR[],
                    service_category VARCHAR NOT NULL,
                    place_of_service VARCHAR NOT NULL,
                    units NUMERIC(10, 2) NOT NULL,
                    allowed_amount NUMERIC(12, 2) NOT NULL,
                    paid_amount NUMERIC(12, 2) NOT NULL,
                    member_cost_share NUMERIC(12, 2) NOT NULL DEFAULT 0,
                    in_network BOOLEAN NOT NULL DEFAULT TRUE,
                    requires_prior_auth BOOLEAN NOT NULL DEFAULT FALSE,
                    prior_auth_approved BOOLEAN,
                    prior_auth_id VARCHAR,
                    facility_type VARCHAR,
                    system_affiliation VARCHAR,
                    rendering_provider_id VARCHAR,
                    billing_provider_id VARCHAR,
                    referring_provider_id VARCHAR,
                    source_system VARCHAR NOT NULL,
                    source_file_id VARCHAR NOT NULL,
                    ingestion_id UUID NOT NULL,
                    record_hash VARCHAR,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_claims_lines_tenant_claim_line UNIQUE (tenant_id, claim_line_id)
                )
            """)
            conn.execute(create_table_sql)
            conn.commit()
            print("  ✅ Table structure created")
            
            # Now create indexes separately with IF NOT EXISTS
            print("  Creating indexes...")
            indexes_sql = [
                "CREATE INDEX IF NOT EXISTS ix_claims_lines_tenant_claim_line ON claims_lines (tenant_id, claim_line_id)",
                "CREATE INDEX IF NOT EXISTS ix_claims_lines_tenant_member ON claims_lines (tenant_id, member_id)",
                "CREATE INDEX IF NOT EXISTS ix_claims_lines_tenant_provider ON claims_lines (tenant_id, provider_id)",
                "CREATE INDEX IF NOT EXISTS ix_claims_lines_service_date ON claims_lines (service_date)",
                "CREATE INDEX IF NOT EXISTS ix_claims_lines_lob_market ON claims_lines (lob, market)",
                "CREATE INDEX IF NOT EXISTS ix_claims_lines_service_category ON claims_lines (service_category)",
                "CREATE INDEX IF NOT EXISTS ix_claims_lines_tenant_id ON claims_lines (tenant_id)",
                "CREATE INDEX IF NOT EXISTS ix_claims_lines_claim_id ON claims_lines (claim_id)",
                "CREATE INDEX IF NOT EXISTS ix_claims_lines_member_id ON claims_lines (member_id)",
                "CREATE INDEX IF NOT EXISTS ix_claims_lines_provider_id ON claims_lines (provider_id)",
                "CREATE INDEX IF NOT EXISTS ix_claims_lines_record_hash ON claims_lines (record_hash) WHERE record_hash IS NOT NULL",
            ]
            
            for idx_sql in indexes_sql:
                try:
                    conn.execute(text(idx_sql))
                except Exception as e:
                    if "already exists" not in str(e) and "Duplicate" not in str(e):
                        print(f"    Warning creating index: {e}")
            
            conn.commit()
            print("  ✅ Indexes created")
            
            print("  ✅ Created claims_lines table")
            
            # Verify
            inspector = inspect(engine)
            if 'claims_lines' in inspector.get_table_names():
                print("  ✅ Verification: claims_lines table exists")
                
                # Check indexes
                indexes = inspector.get_indexes('claims_lines')
                print(f"  ✅ Table has {len(indexes)} indexes")
                return 0
            else:
                print("  ❌ Verification failed: table not found")
                return 1
                
        except Exception as e:
            conn.rollback()
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == "__main__":
    sys.exit(main())

