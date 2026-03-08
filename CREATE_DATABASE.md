# Database Creation Guide

## Status

✅ **Database models created**: 55 tables defined in SQLAlchemy models  
✅ **Alembic migrations created**: Migration file `001_add_file_storage_tables.py` exists  
⚠️  **Database not yet created**: Tables need to be created in PostgreSQL

## Prerequisites

1. **PostgreSQL installed and running**
   - Local: `postgresql://user:password@localhost:5432/uepi_db`
   - Azure: PostgreSQL Flexible Server connection string

2. **Environment variables set**:
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/uepi_db"
   export USE_FILE_STORAGE="false"  # Enable database mode
   ```

## Option 1: Using Alembic Migrations (Recommended)

Alembic migrations are the recommended way to create and manage database schema:

```bash
# 1. Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/uepi_db"
export USE_FILE_STORAGE="false"

# 2. Navigate to API directory
cd apps/api

# 3. Run migrations
alembic upgrade head
```

This will:
- Create all 55 tables
- Set up indexes and foreign keys
- Track migration history

## Option 2: Using init_db() Function

For quick setup without migration tracking:

```bash
# 1. Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/uepi_db"
export USE_FILE_STORAGE="false"

# 2. Run Python script
cd apps/api
python3 -c "
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, '../../packages/common/src')
from uepi_api.database import init_db
init_db()
print('✅ Database tables created!')
"
```

## Option 3: Using the Helper Script

```bash
# 1. Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/uepi_db"
export USE_FILE_STORAGE="false"

# 2. Run script
cd apps/api/scripts
python3 create_database.py
```

## Verify Database Creation

After running migrations, verify tables were created:

```bash
# Connect to PostgreSQL
psql -U user -d uepi_db

# List all tables
\dt

# Count tables (should be 55)
SELECT count(*) FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
```

## All Tables Created

The following 55 tables will be created:

### Core (4)
- tenants, users, roles, user_roles

### Policy (7)
- policies, policy_versions, policy_code_sets, policy_assumptions, policy_guardrails, policy_changelog, policy_predicted_impacts

### Analytics (6)
- baselines, observations, scenarios, scenario_accuracy, forecasts, data_periods

### Pipeline (2)
- pipelines, pipeline_runs

### Risk (1)
- risks

### Learning (2)
- elasticity_models, model_accuracy_history

### Behavior (2)
- behavior_profiles, behavior_clusters

### Alert (2)
- alert_rules, alert_events

### Collaboration (4)
- comments, tasks, approvals, activity_events

### Evidence & Scheduling (2)
- evidence, schedules

### Export (3)
- exports, export_templates, export_packs

### Ingestion (3)
- ingestions, ingestion_errors, datasets

### Analysis (5)
- analyses, analysis_configs, analysis_runs, analysis_results_index, analysis_narratives

### Scorecard (2)
- scorecards, scorecard_entries

### Decision (2)
- policy_decisions, decision_attachments

### Cohort (1)
- cohorts

### Notification (2)
- notifications, notification_preferences

### Lineage (1)
- dataset_snapshots

### Conversational AI (4)
- conversations, conversation_messages, conversation_artifacts, conversation_audit_logs

### Audit (1)
- audit_events

## Troubleshooting

### Error: "File storage is enabled"
- Set `USE_FILE_STORAGE=false` environment variable
- Or set `use_file_storage: false` in config

### Error: "DATABASE_URL not set"
- Set `DATABASE_URL` environment variable with PostgreSQL connection string
- Format: `postgresql://user:password@host:port/database`

### Error: "ModuleNotFoundError: No module named 'uepi_common'"
- Make sure Python path includes `packages/common/src`
- Or install the package: `pip install -e packages/common`

### Error: "Connection refused"
- Ensure PostgreSQL is running
- Check connection string (host, port, credentials)
- Verify network access to database server

## Next Steps

After creating the database:

1. **Seed initial data** (optional):
   ```bash
   python scripts/dev/seed_demo_data.py
   ```

2. **Verify dual-mode storage**:
   - Set `USE_FILE_STORAGE=false` to use database
   - Set `USE_FILE_STORAGE=true` to use file storage
   - All 32 storage files support both modes

3. **Run application**:
   ```bash
   cd apps/api
   uvicorn uepi_api.main:app --reload
   ```

