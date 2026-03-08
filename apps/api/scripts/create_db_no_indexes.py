#!/usr/bin/env python3
"""
Create fresh database and tables WITHOUT indexes
"""
import os
import sys
from pathlib import Path

current_dir = Path(__file__).parent.parent
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
        from urllib.parse import urlparse
        
        parsed = urlparse(db_url)
        
        # Step 1: Drop and recreate database
        print("🔄 Resetting database...")
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database='postgres',
            user=parsed.username or 'postgres',
            password=parsed.password or ''
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        cur.execute("""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = 'uepi_db'
            AND pid <> pg_backend_pid();
        """)
        
        cur.execute("DROP DATABASE IF EXISTS uepi_db;")
        cur.execute("CREATE DATABASE uepi_db;")
        cur.close()
        conn.close()
        print("✅ Database created")
        
        # Step 2: Create tables without indexes
        print("\n🔨 Creating tables (no indexes)...")
        uepi_db_url = f"{db_url.rsplit('/', 1)[0]}/uepi_db"
        from sqlalchemy import create_engine, text
        
        engine = create_engine(uepi_db_url)
        
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        
        # Import all models
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
        
        # Create tables only (skip indexes)
        with engine.begin() as conn:
            for table in Base.metadata.sorted_tables:
                # Temporarily remove indexes
                original_indexes = list(table.indexes)
                table.indexes.clear()
                
                # Remove index=True from columns
                for column in table.columns:
                    if hasattr(column, 'index') and column.index:
                        column.index = False
                
                # Create table
                from sqlalchemy.schema import CreateTable
                create_ddl = CreateTable(table)
                conn.execute(text(str(create_ddl.compile(dialect=engine.dialect))))
                print(f"  ✅ Created {table.name}")
                
                # Restore indexes (for next iteration, though we won't use them)
                table.indexes.update(original_indexes)
        
        print("\n✅ All tables created (no indexes)")
        
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📊 Created {len(tables)} tables")
        print("🎉 Database setup complete!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
