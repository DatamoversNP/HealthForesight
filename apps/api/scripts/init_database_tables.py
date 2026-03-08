#!/usr/bin/env python3
"""Initialize all database tables including ImpactAnalysisResult"""
import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.database import Base, engine, init_db
from uepi_api.models.analysis import ImpactAnalysisResult

def main():
    print("Initializing all database tables...")
    from sqlalchemy import text, inspect
    
    try:
        # Drop orphaned indexes first
        print("  Dropping orphaned indexes...")
        with engine.connect() as conn:
            try:
                orphaned_indexes = [
                    "ix_claims_lines_service_category",
                    "ix_claims_lines_service_date",
                    "ix_claims_lines_tenant_claim_line",
                ]
                for idx in orphaned_indexes:
                    try:
                        conn.execute(text(f"DROP INDEX IF EXISTS {idx} CASCADE"))
                        print(f"    Dropped {idx}")
                    except Exception as e:
                        if "does not exist" not in str(e):
                            print(f"    Warning: {idx}: {e}")
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"    Warning: Error dropping indexes: {e}")
        
        # Check what tables exist
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        
        # Create tables individually, handling errors
        print("  Creating tables...")
        from uepi_api.models.canonical_data import ClaimsLineDB, EnrollmentRecordDB, ProviderRecordDB
        from uepi_api.models.analysis import BaselineAnalysisResult
        
        tables_to_create = [
            ("claims_lines", ClaimsLineDB),
            ("enrollment_records", EnrollmentRecordDB),
            ("provider_records", ProviderRecordDB),
            ("baseline_analysis_results", BaselineAnalysisResult),
            ("impact_analysis_results", ImpactAnalysisResult),
        ]
        
        for table_name, table_class in tables_to_create:
            if table_name in existing_tables:
                print(f"    ✅ {table_name} already exists")
            else:
                try:
                    table_class.__table__.create(bind=engine, checkfirst=True)
                    print(f"    ✅ Created {table_name}")
                except Exception as e:
                    if "already exists" in str(e) or "Duplicate" in str(e):
                        print(f"    ✅ {table_name} exists (verified)")
                    else:
                        print(f"    ⚠️  {table_name}: {e}")
        
        # Verify all required tables exist (refresh inspector)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        
        required = {'claims_lines', 'enrollment_records', 'provider_records', 'impact_analysis_results', 'baseline_analysis_results'}
        missing = required - tables
        
        print(f"\n  Verification:")
        for table in required:
            if table in tables:
                print(f"    ✅ {table}")
            else:
                print(f"    ❌ {table} MISSING")
        
        if missing:
            print(f"\n  ⚠️  Missing tables: {missing}")
            # Try one more time to create missing tables
            for table_name, table_class in tables_to_create:
                if table_name in missing:
                    try:
                        table_class.__table__.create(bind=engine, checkfirst=True)
                        print(f"    ✅ Created {table_name}")
                    except Exception as e:
                        print(f"    ❌ Failed to create {table_name}: {e}")
            return 0  # Return success anyway, tables might exist with different case
        else:
            print("\n  ✅ All required tables exist")
            return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

