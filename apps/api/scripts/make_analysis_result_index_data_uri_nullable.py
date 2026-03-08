#!/usr/bin/env python3
"""
Make data_uri column nullable in analysis_results_index table
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
    """Make data_uri nullable"""
    db = SessionLocal()
    conn = None
    try:
        conn = engine.connect()
        
        # Check current constraint
        check_sql = text("""
            SELECT 
                column_name, 
                is_nullable,
                data_type
            FROM information_schema.columns 
            WHERE table_name='analysis_results_index' AND column_name='data_uri';
        """)
        result = conn.execute(check_sql)
        row = result.fetchone()
        
        if row:
            is_nullable = row[1] == 'YES'
            if is_nullable:
                print("✅ Column 'data_uri' is already nullable")
                return 0
            else:
                print("Making 'data_uri' column nullable...")
                # Make column nullable
                alter_sql = text("ALTER TABLE analysis_results_index ALTER COLUMN data_uri DROP NOT NULL")
                conn.execute(alter_sql)
                conn.commit()
                print("✅ Successfully made 'data_uri' column nullable")
                return 0
        else:
            print("❌ Column 'data_uri' not found in analysis_results_index table")
            return 1
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error making data_uri nullable: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if conn:
            conn.close()
        db.close()

if __name__ == "__main__":
    sys.exit(main())

