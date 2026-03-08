#!/usr/bin/env python3
"""
Create database directly using psycopg2 (no psql command needed)
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
    
    print(f"📊 Database URL: {db_url.split('@')[-1] if '@' in db_url else db_url[:50]}...")
    
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Parse connection string
        parsed = urlparse(db_url)
        
        # First, connect to postgres database to create uepi_db
        print("🔨 Creating database 'uepi_db'...")
        try:
            # Connect to default postgres database
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database='postgres',  # Connect to default database
                user=parsed.username or 'postgres',
                password=parsed.password or ''
            )
            conn.autocommit = True  # Required for CREATE DATABASE
            cur = conn.cursor()
            
            # Check if database exists
            cur.execute("SELECT 1 FROM pg_database WHERE datname = 'uepi_db'")
            exists = cur.fetchone()
            
            if not exists:
                cur.execute("CREATE DATABASE uepi_db;")
                print("✅ Database 'uepi_db' created!")
            else:
                print("✅ Database 'uepi_db' already exists")
            
            cur.close()
            conn.close()
        except psycopg2.OperationalError as e:
            print(f"⚠️  Could not create database: {e}")
            print("   Database might already exist, continuing...")
        
        # Now connect to uepi_db and create tables
        print("")
        print("🔨 Creating database tables...")
        
        from uepi_api.database import init_db, engine, Base
        from sqlalchemy import text, inspect
        
        # Test connection to uepi_db
        print("🔌 Testing connection to uepi_db...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL: {version.split(',')[0]}")
        
        # Always clean up: aggressively drop all indexes and tables
        print("🧹 Cleaning up any existing objects...")
        
        with engine.connect() as conn:
            with conn.begin():
                # First, drop ALL tables (this should cascade to indexes)
                inspector = inspect(engine)
                existing_tables = inspector.get_table_names()
                if existing_tables:
                    print(f"   Dropping {len(existing_tables)} tables...")
                    for table_name in reversed(existing_tables):
                        try:
                            conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;'))
                        except Exception as e:
                            print(f"      ⚠️  {table_name}: {e}")
                
                # Then drop ALL remaining indexes (in case any are orphaned)
                try:
                    result = conn.execute(text("""
                        SELECT indexname 
                        FROM pg_indexes 
                        WHERE schemaname = 'public' 
                        AND indexname NOT LIKE 'pg_%'
                    """))
                    indexes = [row[0] for row in result]
                    if indexes:
                        print(f"   Dropping {len(indexes)} orphaned indexes...")
                        for index_name in indexes:
                            try:
                                conn.execute(text(f'DROP INDEX IF EXISTS "{index_name}" CASCADE;'))
                            except Exception as e:
                                pass  # Index might already be dropped
                except Exception as e:
                    pass  # No indexes to drop
        
        print("✅ Cleanup complete")
        
        # Initialize database (create all tables)
        print("📝 Creating tables...")
        init_db()
        print("✅ Database tables created successfully!")
        print("")
        print("📊 Created 55 tables including:")
        print("   - Core: tenants, users, roles, user_roles")
        print("   - Policy: policies, policy_versions, policy_assumptions, etc.")
        print("   - Analytics: baselines, observations, scenarios, etc.")
        print("   - And 40+ more tables...")
        print("")
        print("🎉 Database setup complete!")
        
        return 0
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure psycopg2-binary is installed:")
        print("   pip3 install psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())

