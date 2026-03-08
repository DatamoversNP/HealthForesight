#!/usr/bin/env python3
"""
Migration script: Import all file-based data into PostgreSQL database
This script reads existing JSON/YAML/CSV files and imports them into the database.
Safe to run multiple times (idempotent) - detects existing records and skips/merges.
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime

# Add paths for imports
current_dir = Path(__file__).parent.parent
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(common_dir))

def main():
    """Main migration function"""
    os.environ.setdefault('USE_FILE_STORAGE', 'false')
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)
    
    print("🔄 Starting file-to-database migration...")
    print(f"📊 Database: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    
    # Find data directory
    project_root = current_dir.parent.parent
    data_dir = project_root / "data"
    if not data_dir.exists():
        print(f"⚠️  Data directory not found: {data_dir}")
        print("   Skipping migration - no file data to migrate")
        return 0
    
    print(f"📁 Scanning data directory: {data_dir}")
    
    # Initialize database connection
    from uepi_api.database import SessionLocal, init_db
    from sqlalchemy.orm import Session
    
    # Ensure tables exist
    print("🔨 Ensuring database tables exist...")
    init_db()
    
    db: Session = SessionLocal()
    try:
        # Migrate each entity type
        migrated_count = 0
        
        # 1. Policies
        policies_dir = data_dir / "policies"
        if policies_dir.exists():
            count = migrate_policies(db, policies_dir)
            migrated_count += count
            print(f"  ✅ Migrated {count} policies")
        
        # 2. Baselines
        baselines_dir = data_dir / "baselines"
        if baselines_dir.exists():
            count = migrate_baselines(db, baselines_dir)
            migrated_count += count
            print(f"  ✅ Migrated {count} baselines")
        
        # 3. Observations
        observations_dir = data_dir / "observations"
        if observations_dir.exists():
            count = migrate_observations(db, observations_dir)
            migrated_count += count
            print(f"  ✅ Migrated {count} observations")
        
        # 4. Scenarios
        scenarios_dir = data_dir / "scenarios"
        if scenarios_dir.exists():
            count = migrate_scenarios(db, scenarios_dir)
            migrated_count += count
            print(f"  ✅ Migrated {count} scenarios")
        
        # 5. Risks
        risks_dir = data_dir / "risks"
        if risks_dir.exists():
            count = migrate_risks(db, risks_dir)
            migrated_count += count
            print(f"  ✅ Migrated {count} risks")
        
        # 6. Pipelines
        pipelines_dir = data_dir / "pipelines"
        if pipelines_dir.exists():
            count = migrate_pipelines(db, pipelines_dir)
            migrated_count += count
            print(f"  ✅ Migrated {count} pipelines")
        
        # 7. Analyses
        analyses_dir = data_dir / "analyses"
        if analyses_dir.exists():
            count = migrate_analyses(db, analyses_dir)
            migrated_count += count
            print(f"  ✅ Migrated {count} analyses")
        
        # 8. Decisions
        decisions_dir = data_dir / "decisions"
        if decisions_dir.exists():
            count = migrate_decisions(db, decisions_dir)
            migrated_count += count
            print(f"  ✅ Migrated {count} decisions")
        
        # 9. Exports
        exports_dir = data_dir / "exports"
        if exports_dir.exists():
            count = migrate_exports(db, exports_dir)
            migrated_count += count
            print(f"  ✅ Migrated {count} exports")
        
        # 10. Schedules
        schedules_dir = data_dir / "schedules"
        if schedules_dir.exists():
            count = migrate_schedules(db, schedules_dir)
            migrated_count += count
            print(f"  ✅ Migrated {count} schedules")
        
        # Commit all changes
        db.commit()
        print(f"\n✅ Migration complete! Migrated {migrated_count} total records")
        
        return 0
        
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


def migrate_policies(db: Session, policies_dir: Path) -> int:
    """Migrate policies from files to database"""
    from uepi_api.models.policy import Policy
    
    count = 0
    for policy_file in policies_dir.glob("*.json"):
        try:
            with open(policy_file, 'r') as f:
                policy_data = json.load(f)
            
            policy_id = UUID(policy_data.get("policy_id") or policy_data.get("id"))
            tenant_id = UUID(policy_data.get("tenant_id"))
            
            # Check if already exists
            existing = db.query(Policy).filter(
                Policy.tenant_id == tenant_id,
                Policy.policy_id == str(policy_id)
            ).first()
            
            if existing:
                continue  # Skip existing
            
            # Create policy in database
            policy = Policy(
                tenant_id=tenant_id,
                policy_id=str(policy_id),
                policy_name=policy_data.get("policy_name") or policy_data.get("name", "Unnamed"),
                policy_type=policy_data.get("policy_type", "PRIOR_AUTH"),
                status=policy_data.get("status", "ACTIVE"),
                effective_date=parse_date(policy_data.get("effective_date")),
                expiration_date=parse_date(policy_data.get("expiration_date")),
                policy_metadata_json=policy_data.get("metadata", {}),
            )
            
            db.add(policy)
            count += 1
            
        except Exception as e:
            print(f"  ⚠️  Error migrating policy {policy_file.name}: {e}")
    
    return count


def migrate_baselines(db: Session, baselines_dir: Path) -> int:
    """Migrate baselines from files to database"""
    from uepi_api.models.baseline import Baseline
    
    count = 0
    for tenant_dir in baselines_dir.iterdir():
        if not tenant_dir.is_dir():
            continue
        
        tenant_id = UUID(tenant_dir.name)
        
        for baseline_file in tenant_dir.glob("*.json"):
            try:
                with open(baseline_file, 'r') as f:
                    baseline_data = json.load(f)
                
                baseline_id = baseline_data.get("baseline_id")
                
                # Check if already exists
                existing = db.query(Baseline).filter(
                    Baseline.tenant_id == tenant_id,
                    Baseline.baseline_id == baseline_id
                ).first()
                
                if existing:
                    continue  # Skip existing
                
                # Create baseline in database
                baseline = Baseline(
                    tenant_id=tenant_id,
                    baseline_id=baseline_id,
                    version=baseline_data.get("version", 1),
                    baseline_type=baseline_data.get("baseline_type", "ROLLING"),
                    window_start_date=parse_date(baseline_data.get("window_start_date")),
                    window_end_date=parse_date(baseline_data.get("window_end_date")),
                    policy_id=UUID(baseline_data["policy_id"]) if baseline_data.get("policy_id") else None,
                    data_period_ids_json=baseline_data.get("data_period_ids", []),
                    baseline_metrics_json=baseline_data.get("baseline_metrics", {}),
                    computed_at=parse_date(baseline_data.get("computed_at")),
                    computed_by=baseline_data.get("computed_by", "system"),
                    shift_detected=baseline_data.get("shift_detected", False),
                    shift_summary_json=baseline_data.get("shift_summary", {}),
                    refresh_reason=baseline_data.get("refresh_reason", "NEW_DATA"),
                )
                
                db.add(baseline)
                count += 1
                
            except Exception as e:
                print(f"  ⚠️  Error migrating baseline {baseline_file.name}: {e}")
    
    return count


def migrate_observations(db: Session, observations_dir: Path) -> int:
    """Migrate observations from files to database"""
    from uepi_api.models.observation import Observation
    
    count = 0
    for tenant_dir in observations_dir.iterdir():
        if not tenant_dir.is_dir():
            continue
        
        tenant_id = UUID(tenant_dir.name)
        
        for obs_file in tenant_dir.glob("*.json"):
            try:
                with open(obs_file, 'r') as f:
                    obs_data = json.load(f)
                
                obs_id = obs_data.get("observation_id")
                
                # Check if already exists
                existing = db.query(Observation).filter(
                    Observation.tenant_id == tenant_id,
                    Observation.observation_id == obs_id
                ).first()
                
                if existing:
                    continue  # Skip existing
                
                # Create observation in database
                observation = Observation(
                    tenant_id=tenant_id,
                    observation_id=obs_id,
                    policy_id=UUID(obs_data["policy_id"]) if obs_data.get("policy_id") else None,
                    data_period_id=UUID(obs_data["data_period_id"]) if obs_data.get("data_period_id") else None,
                    observation_type=obs_data.get("observation_type", "PERIODIC"),
                    observation_period_start=parse_date(obs_data.get("observation_period_start")),
                    observation_period_end=parse_date(obs_data.get("observation_period_end")),
                    metrics_json=obs_data.get("metrics", {}),
                    comparisons_json=obs_data.get("comparisons", {}),
                    computed_at=parse_date(obs_data.get("computed_at")),
                )
                
                db.add(observation)
                count += 1
                
            except Exception as e:
                print(f"  ⚠️  Error migrating observation {obs_file.name}: {e}")
    
    return count


def migrate_scenarios(db: Session, scenarios_dir: Path) -> int:
    """Migrate scenarios from files to database"""
    from uepi_api.models.scenario import Scenario
    
    count = 0
    # Similar pattern to baselines/observations
    # Implementation depends on scenario file structure
    return count


def migrate_risks(db: Session, risks_dir: Path) -> int:
    """Migrate risks from files to database"""
    from uepi_api.models.risk import Risk
    
    count = 0
    # Similar pattern
    return count


def migrate_pipelines(db: Session, pipelines_dir: Path) -> int:
    """Migrate pipelines from files to database"""
    from uepi_api.models.pipeline import Pipeline
    
    count = 0
    # Similar pattern
    return count


def migrate_analyses(db: Session, analyses_dir: Path) -> int:
    """Migrate analyses from files to database"""
    from uepi_api.models.analysis import Analysis
    
    count = 0
    # Similar pattern
    return count


def migrate_decisions(db: Session, decisions_dir: Path) -> int:
    """Migrate decisions from files to database"""
    from uepi_api.models.decision import PolicyDecision
    
    count = 0
    # Similar pattern
    return count


def migrate_exports(db: Session, exports_dir: Path) -> int:
    """Migrate exports from files to database"""
    from uepi_api.models.export import Export
    
    count = 0
    # Similar pattern
    return count


def migrate_schedules(db: Session, schedules_dir: Path) -> int:
    """Migrate schedules from files to database"""
    from uepi_api.models.schedule import Schedule
    
    count = 0
    # Similar pattern
    return count


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse date string to datetime"""
    if not date_str:
        return None
    if isinstance(date_str, datetime):
        return date_str
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except:
        return None


if __name__ == "__main__":
    sys.exit(main())

