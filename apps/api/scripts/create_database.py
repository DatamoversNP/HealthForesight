#!/usr/bin/env python3
"""
Script to create database and run migrations
"""
import os
import sys
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api" / "src"))
sys.path.insert(0, str(project_root / "packages" / "common" / "src"))

from uepi_api.config import get_settings
from uepi_api.database import init_db, engine, Base
from sqlalchemy import text

def create_database():
    """Create database if it doesn't exist and run migrations"""
    settings = get_settings()
    
    # Check if file storage is enabled
    if settings.use_file_storage:
        print("⚠️  File storage is enabled (use_file_storage=True)")
        print("   Set USE_FILE_STORAGE=false to enable database mode")
        print("   Or set DATABASE_URL environment variable")
        return False
    
    # Check database URL
    db_url = settings.database.url
    if not db_url:
        print("❌ DATABASE_URL not set")
        print("   Set DATABASE_URL environment variable, e.g.:")
        print("   export DATABASE_URL='postgresql://user:password@localhost:5432/uepi_db'")
        return False
    
    print(f"📊 Database URL: {db_url.split('@')[-1] if '@' in db_url else db_url[:50]}...")
    
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL: {version.split(',')[0]}")
        
        # Initialize database (create all tables)
        print("\n🔨 Creating database tables...")
        init_db()
        print("✅ Database tables created successfully!")
        
        # Check if Alembic migrations should be run
        print("\n📝 Note: Alembic migrations can be run with:")
        print("   cd apps/api && alembic upgrade head")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)

