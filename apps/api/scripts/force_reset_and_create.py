#!/usr/bin/env python3
"""
Force reset database and create all tables - handles all edge cases
This script ensures a completely clean database state before creating tables.
"""
import os
import sys
import time
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

def main():
    os.environ.setdefault('USE_FILE_STORAGE', 'false')
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)
    
    try:
        import psycopg2
        from urllib.parse import urlparse, urlunparse
        from sqlalchemy import create_engine, text, inspect
        
        parsed = urlparse(db_url)
        
        # Extract database name from URL, or default to 'uepi_db'
        db_name = parsed.path.lstrip('/') if parsed.path else 'uepi_db'
        if not db_name or db_name == 'postgres':
            db_name = 'uepi_db'
        
        # Step 1: Connect to postgres database to drop/recreate target database
        print(f"🔄 Step 1: Resetting database '{db_name}'...")
        admin_conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database='postgres',
            user=parsed.username or 'postgres',
            password=parsed.password or ''
        )
        admin_conn.autocommit = True
        admin_cur = admin_conn.cursor()
        
        # Terminate all connections to the target database
        print(f"   Terminating existing connections to '{db_name}'...")
        admin_cur.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = %s
            AND pid <> pg_backend_pid();
        """, (db_name,))
        terminated = admin_cur.rowcount
        if terminated > 0:
            print(f"   ✅ Terminated {terminated} connection(s)")
        
        # Wait a moment for connections to close
        time.sleep(0.5)
        
        # Drop and recreate database
        print(f"   Dropping database '{db_name}'...")
        admin_cur.execute(f"DROP DATABASE IF EXISTS {db_name};")
        print(f"   Creating database '{db_name}'...")
        admin_cur.execute(f"CREATE DATABASE {db_name};")
        admin_cur.close()
        admin_conn.close()
        print(f"✅ Database '{db_name}' reset complete")
        
        # Step 2: Connect to the new database and reset schema
        print("\n🧹 Step 2: Resetting schema...")
        new_path = f"/{db_name}"
        uepi_db_url = urlunparse(parsed._replace(path=new_path))
        
        # Create engine with explicit connection parameters
        engine = create_engine(
            uepi_db_url,
            pool_pre_ping=True,
            echo=False
        )
        
        # Use a single transaction to drop and recreate schema
        with engine.begin() as conn:
            # Drop schema completely
            conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            # Recreate schema
            conn.execute(text("CREATE SCHEMA public"))
            # Grant permissions
            conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
            # Set default privileges
            conn.execute(text("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO postgres"))
            conn.execute(text("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO public"))
        
        print("✅ Schema reset complete")
        
        # Step 3: Verify clean state
        print("\n🔍 Step 3: Verifying clean state...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"   ✅ Connected to PostgreSQL: {version.split(',')[0]}")
            
            # Check that schema is empty
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            table_count = result.scalar()
            if table_count > 0:
                print(f"   ⚠️  Warning: Found {table_count} tables in public schema (expected 0)")
            else:
                print("   ✅ Schema is clean (no tables)")
        
        # Step 4: Import all models to register them
        print("\n📦 Step 4: Loading models...")
        from uepi_api.database import Base
        from uepi_api.models import (
            Tenant, User, Role, AuditEvent, Policy, PolicyVersion, PolicyCodeSet,
            PolicyAssumption, PolicyGuardrail, PolicyChangelog, PolicyPredictedImpact,
            Baseline, Observation, Scenario, ScenarioAccuracy, Pipeline, PipelineRun,
            Risk, Forecast, DataPeriod, ElasticityModel, ModelAccuracyHistory,
            BehaviorProfile, BehaviorCluster, AlertRule, AlertEvent, Comment, Task,
            Approval, ActivityEvent, Evidence, Schedule, ExportTemplate, ExportPack,
            Ingestion, IngestionError, Dataset, Analysis, AnalysisRun, AnalysisResultIndex,
            AnalysisNarrative, AnalysisConfig, Scorecard, ScorecardEntry, Export,
            Cohort, PolicyDecision, DecisionAttachment, DatasetSnapshot, Notification,
            NotificationPreference
        )
        print(f"   ✅ Loaded {len(Base.metadata.tables)} model(s)")
        
        # Step 5: Create all tables in a single transaction
        print("\n🔨 Step 5: Creating tables and indexes...")
        try:
            # Use checkfirst=False to ensure we're creating from scratch
            Base.metadata.create_all(bind=engine, checkfirst=False)
            print("✅ All tables created successfully!")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            # Try to get more details
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        # Step 6: Verify tables were created
        print("\n📊 Step 6: Verifying tables...")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"   ✅ Created {len(tables)} table(s)")
        
        if len(tables) == 0:
            print("   ❌ ERROR: No tables were created!")
            sys.exit(1)
        
        # List first few tables as confirmation
        if len(tables) <= 10:
            for table in sorted(tables):
                print(f"      - {table}")
        else:
            for table in sorted(tables)[:10]:
                print(f"      - {table}")
            print(f"      ... and {len(tables) - 10} more")
        
        print("\n🎉 Database setup complete!")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
