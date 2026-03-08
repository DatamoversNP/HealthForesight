#!/usr/bin/env python3
"""
Add name column to analyses table with unique constraint per tenant and analysis_type
"""
import sys
from pathlib import Path
from sqlalchemy import text

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

from uepi_api.database import engine, SessionLocal

def main():
    """Add name column to analyses table"""
    db = SessionLocal()
    conn = None
    try:
        conn = engine.connect()
        
        # Check if column already exists
        check_sql = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='analyses' AND column_name='name';
        """)
        result = conn.execute(check_sql)
        if result.fetchone():
            print("✅ Column 'name' already exists in analyses table")
            return 0
        
        # Add name column
        print("Adding 'name' column to analyses table...")
        alter_sql = text("ALTER TABLE analyses ADD COLUMN name VARCHAR")
        conn.execute(alter_sql)
        
        # Add unique constraint
        print("Adding unique constraint on (tenant_id, analysis_type, name)...")
        constraint_sql = text("""
            CREATE UNIQUE INDEX uq_analysis_name_per_tenant_type 
            ON analyses(tenant_id, analysis_type, name) 
            WHERE name IS NOT NULL;
        """)
        conn.execute(constraint_sql)
        
        conn.commit()
        print("✅ Successfully added 'name' column and unique constraint")
        return 0
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error adding name column: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if conn:
            conn.close()
        db.close()

if __name__ == "__main__":
    sys.exit(main())

