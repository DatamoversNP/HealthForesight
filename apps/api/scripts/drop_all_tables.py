#!/usr/bin/env python3
"""
Drop all tables in uepi_db (use with caution!)
"""
import os
import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

def main():
    # Set environment variables before importing
    os.environ.setdefault('USE_FILE_STORAGE', 'false')
    
    # Check DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        print("   Set DATABASE_URL environment variable")
        sys.exit(1)
    
    # Update DATABASE_URL to point to uepi_db
    from urllib.parse import urlparse, urlunparse
    parsed = urlparse(db_url)
    # Change database name to uepi_db
    uepi_db_url = urlunparse(parsed._replace(path='/uepi_db'))
    
    print(f"⚠️  WARNING: This will drop ALL tables in uepi_db!")
    print(f"📊 Database URL: {uepi_db_url.split('@')[-1] if '@' in uepi_db_url else uepi_db_url[:50]}...")
    
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        sys.exit(0)
    
    try:
        from sqlalchemy import create_engine, text, inspect
        from sqlalchemy.exc import ProgrammingError
        
        # Create engine for uepi_db
        engine = create_engine(uepi_db_url)
        
        print("🔌 Connecting to uepi_db...")
        with engine.connect() as conn:
            # Get all table names
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            if not tables:
                print("✅ No tables found - database is empty")
                return 0
            
            print(f"📋 Found {len(tables)} tables to drop:")
            for table in tables:
                print(f"   - {table}")
            
            print("\n🗑️  Dropping all tables...")
            
            # Drop all tables (CASCADE to handle foreign keys)
            with conn.begin():
                # Drop all tables in reverse dependency order
                for table in reversed(tables):
                    try:
                        conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE;'))
                        print(f"   ✅ Dropped {table}")
                    except Exception as e:
                        print(f"   ⚠️  Error dropping {table}: {e}")
            
            # Verify all tables are dropped
            inspector = inspect(engine)
            remaining = inspector.get_table_names()
            
            if remaining:
                print(f"⚠️  {len(remaining)} tables still exist: {remaining}")
            else:
                print("✅ All tables dropped successfully!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())

