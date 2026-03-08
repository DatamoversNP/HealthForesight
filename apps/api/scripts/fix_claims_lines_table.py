#!/usr/bin/env python3
"""Fix claims_lines table by dropping and recreating if needed"""
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
    
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    
    if 'claims_lines' not in existing_tables:
        print("  Table does not exist, creating...")
        
        # Drop all indexes that might be orphaned
        with engine.connect() as conn:
            try:
                indexes_to_drop = [
                    "ix_claims_lines_service_category",
                    "ix_claims_lines_service_date",
                    "ix_claims_lines_tenant_claim_line",
                    "ix_claims_lines_tenant_id",
                ]
                for idx in indexes_to_drop:
                    try:
                        conn.execute(text(f"DROP INDEX IF EXISTS {idx} CASCADE"))
                        print(f"    Dropped index: {idx}")
                    except:
                        pass
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"    Warning: {e}")
        
        # Create table
        try:
            ClaimsLineDB.__table__.create(bind=engine, checkfirst=True)
            print("  ✅ Created claims_lines table")
        except Exception as e:
            if "already exists" in str(e):
                print("  ✅ Table exists")
            else:
                print(f"  ❌ Error: {e}")
                return 1
    else:
        print("  ✅ Table already exists")
    
    # Verify
    inspector = inspect(engine)
    if 'claims_lines' in inspector.get_table_names():
        print("  ✅ Verification: claims_lines table exists")
        return 0
    else:
        print("  ❌ Verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

