#!/usr/bin/env python3
"""
Completely reset the uepi_db database by dropping and recreating it
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
    
    print(f"⚠️  WARNING: This will DROP and RECREATE the entire 'uepi_db' database!")
    print(f"📊 Database URL: {db_url.split('@')[-1] if '@' in db_url else db_url[:50]}...")
    
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        sys.exit(0)
    
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Parse connection string
        parsed = urlparse(db_url)
        
        # Connect to postgres database to drop and recreate uepi_db
        print("🔌 Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database='postgres',  # Connect to default database
            user=parsed.username or 'postgres',
            password=parsed.password or ''
        )
        conn.autocommit = True  # Required for DROP DATABASE
        cur = conn.cursor()
        
        # Terminate all connections to uepi_db first
        print("🔌 Terminating connections to uepi_db...")
        try:
            cur.execute("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = 'uepi_db'
                AND pid <> pg_backend_pid();
            """)
        except Exception as e:
            print(f"   ⚠️  Warning: {e}")
        
        # Drop database
        print("🗑️  Dropping database 'uepi_db'...")
        cur.execute("DROP DATABASE IF EXISTS uepi_db;")
        print("✅ Database dropped")
        
        # Create database
        print("🔨 Creating database 'uepi_db'...")
        cur.execute("CREATE DATABASE uepi_db;")
        print("✅ Database created")
        
        cur.close()
        conn.close()
        
        print("")
        print("✅ Database reset complete!")
        print("   Now run: python3 scripts/create_db_direct.py")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())

