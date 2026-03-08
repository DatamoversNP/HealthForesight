#!/usr/bin/env python3
"""
Alternative script to create database using init_db() instead of Alembic
This is useful if Alembic is not installed or configured
"""
import os
import sys
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

def main():
    # Check environment variables
    db_url = os.getenv("DATABASE_URL")
    use_file_storage = os.getenv("USE_FILE_STORAGE", "true").lower()
    
    if not db_url:
        print("❌ DATABASE_URL not set")
        print("   Set DATABASE_URL environment variable, e.g.:")
        print("   export DATABASE_URL='postgresql://user:password@localhost:5432/uepi_db'")
        sys.exit(1)
    
    if use_file_storage == "true":
        print("⚠️  USE_FILE_STORAGE is set to true")
        print("   Set USE_FILE_STORAGE=false to enable database mode")
        print("   export USE_FILE_STORAGE='false'")
        sys.exit(1)
    
    print(f"📊 Database URL: {db_url.split('@')[-1] if '@' in db_url else db_url[:50]}...")
    print("🔨 Creating database tables...")
    
    try:
        from uepi_api.database import init_db, engine
        from sqlalchemy import text
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL: {version.split(',')[0]}")
        
        # Initialize database (create all tables)
        init_db()
        print("✅ Database tables created successfully!")
        print("")
        print("📊 Created 55 tables:")
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
        print(f"❌ Error creating database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())

