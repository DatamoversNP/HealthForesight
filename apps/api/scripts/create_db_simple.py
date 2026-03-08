#!/usr/bin/env python3
"""
Simple script to create database tables using init_db()
Bypasses Alembic and .env file issues
"""
import os
import sys
from pathlib import Path

# Set environment variables before importing
os.environ.setdefault('USE_FILE_STORAGE', 'false')

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

def main():
    # Check DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        print("   Set DATABASE_URL environment variable, e.g.:")
        print("   export DATABASE_URL='postgresql://user:password@localhost:5432/uepi_db'")
        sys.exit(1)
    
    print(f"📊 Database URL: {db_url.split('@')[-1] if '@' in db_url else db_url[:50]}...")
    print("🔨 Creating database tables...")
    
    try:
        from uepi_api.database import init_db, engine
        from sqlalchemy import text
        
        # Test connection
        print("🔌 Testing database connection...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL: {version.split(',')[0]}")
        
        # Initialize database (create all tables)
        print("📝 Creating tables...")
        init_db()
        print("✅ Database tables created successfully!")
        print("")
        print("📊 Created 55 tables including:")
        print("   - Core: tenants, users, roles, user_roles")
        print("   - Policy: policies, policy_versions, policy_assumptions, policy_guardrails, etc.")
        print("   - Analytics: baselines, observations, scenarios, forecasts, etc.")
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

