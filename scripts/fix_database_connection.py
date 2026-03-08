#!/usr/bin/env python3
"""Fix database connection and verify all modules can access database"""

import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

def check_database_connection():
    """Check if database connection works"""
    try:
        from uepi_api.database import SessionLocal, engine
        from sqlalchemy import text
        
        print("Step 1: Testing database connection...")
        db = SessionLocal()
        try:
            # Test connection
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            print("✅ Database connection successful!")
            
            # Check if tables exist
            print("\nStep 2: Checking database tables...")
            result = db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"✅ Found {len(tables)} tables:")
            for table in tables[:20]:  # Show first 20
                print(f"   - {table}")
            if len(tables) > 20:
                print(f"   ... and {len(tables) - 20} more")
            
            # Check data counts
            print("\nStep 3: Checking data in tables...")
            data_counts = {}
            important_tables = ['policies', 'observations', 'analyses', 'pipelines', 'baselines', 'policy_versions']
            
            for table in important_tables:
                if table in tables:
                    try:
                        result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        data_counts[table] = count
                        status = "✅" if count > 0 else "⚠️ "
                        print(f"{status} {table}: {count} records")
                    except Exception as e:
                        print(f"❌ {table}: Error - {e}")
                        data_counts[table] = 0
                else:
                    print(f"⚠️  {table}: Table does not exist")
                    data_counts[table] = -1
            
            db.close()
            
            # Summary
            print("\n" + "="*80)
            print("SUMMARY")
            print("="*80)
            
            tables_with_data = [t for t, c in data_counts.items() if c > 0]
            tables_empty = [t for t, c in data_counts.items() if c == 0]
            tables_missing = [t for t, c in data_counts.items() if c == -1]
            
            if tables_with_data:
                print(f"\n✅ Tables with data ({len(tables_with_data)}):")
                for table in tables_with_data:
                    print(f"   - {table}: {data_counts[table]} records")
            
            if tables_empty:
                print(f"\n⚠️  Empty tables ({len(tables_empty)}):")
                for table in tables_empty:
                    print(f"   - {table}: No data")
            
            if tables_missing:
                print(f"\n❌ Missing tables ({len(tables_missing)}):")
                for table in tables_missing:
                    print(f"   - {table}: Table does not exist")
            
            return True, data_counts
            
        except Exception as e:
            db.close()
            print(f"❌ Database connection failed: {e}")
            import traceback
            traceback.print_exc()
            return False, {}
    except Exception as e:
        print(f"❌ Failed to import database module: {e}")
        import traceback
        traceback.print_exc()
        return False, {}

def check_config():
    """Check database configuration"""
    print("\n" + "="*80)
    print("DATABASE CONFIGURATION")
    print("="*80)
    
    try:
        from uepi_common.config import DatabaseSettings
        db_settings = DatabaseSettings()
        
        print(f"\nDatabase URL: {db_settings.url}")
        
        # Parse URL to extract components (handle URLs with or without password)
        import re
        # Try with password first
        url_match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_settings.url)
        if url_match:
            user, password, host, port, database = url_match.groups()
            print(f"Host: {host}")
            print(f"Port: {port}")
            print(f"Database: {database}")
            print(f"User: {user}")
            print(f"Password: {'*' * len(password) if password else 'NOT SET (using peer auth)'}")
            print(f"\n✅ URL parsed successfully")
            return True
        else:
            # Try without password (peer authentication)
            url_match = re.match(r'postgresql://([^@]+)@([^:]+):(\d+)/(.+)', db_settings.url)
            if url_match:
                user, host, port, database = url_match.groups()
                print(f"Host: {host}")
                print(f"Port: {port}")
                print(f"Database: {database}")
                print(f"User: {user}")
                print(f"Password: NOT SET (using peer authentication)")
                print(f"\n✅ URL parsed successfully (peer auth)")
                return True
            else:
                print(f"\n⚠️  Could not parse database URL: {db_settings.url}")
                return False
            
    except Exception as e:
        print(f"❌ Error checking config: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*80)
    print("DATABASE CONNECTION DIAGNOSTIC")
    print("="*80)
    print()
    
    # Check config
    config_ok = check_config()
    
    if not config_ok:
        print("\n⚠️  Configuration issue detected. Please fix password in config.")
        return 1
    
    # Check connection
    connection_ok, data_counts = check_database_connection()
    
    if not connection_ok:
        print("\n❌ Database connection failed!")
        print("\nTroubleshooting steps:")
        print("1. Check if PostgreSQL is running: docker-compose ps")
        print("2. Start PostgreSQL: docker-compose up -d postgres")
        print("3. Check database password matches config")
        print("4. Verify database exists: docker-compose exec postgres psql -U uepi -d uepi -c '\\dt'")
        return 1
    
    # Check if data exists
    total_records = sum(c for c in data_counts.values() if c > 0)
    if total_records == 0:
        print("\n⚠️  Database is connected but has no data!")
        print("   You may need to:")
        print("   1. Run database migrations")
        print("   2. Import/seed initial data")
        print("   3. Run data loading scripts")
    else:
        print(f"\n✅ Database is connected and has {total_records} total records")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
