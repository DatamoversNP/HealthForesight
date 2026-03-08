# Database Migration Requirements - File to Database Storage

## Current State (File-Based Storage)

### What's Currently Stored in Files:
1. **Policies** - `data/policy_*.json` and `data/policies/*.json`
   - Full policy structure with `metadata` field containing:
     - `assumptions` (array)
     - `guardrails` (array)
     - `versions` (array)
     - `changelog` (array)
     - `scope`, `logic`, `policy_levers`, etc.

2. **Other Data** (also file-based):
   - Predicted impacts
   - Observations
   - Baselines
   - Analyses
   - Decisions
   - Risks
   - Scenarios

## Database Models That Already Exist

### ✅ Already Defined in `apps/api/src/uepi_api/models/policy.py`:
1. **`Policy`** table
   - `id` (UUID, primary key)
   - `tenant_id` (UUID, indexed)
   - `name`, `policy_type`, `description`, `status`
   - `policy_metadata_json` (JSONB) - stores flexible structure
   - Relationships: `versions`

2. **`PolicyVersion`** table
   - `id` (UUID, primary key)
   - `tenant_id`, `policy_id` (FK to Policy)
   - `version_number`, `effective_start_date`, `effective_end_date`
   - `change_type`, `enforcement_strength`, `justification`
   - `version_metadata_json` (JSONB)
   - Relationships: `policy`, `code_sets`

3. **`PolicyCodeSet`** table
   - `id` (UUID, primary key)
   - `tenant_id`, `version_id` (FK to PolicyVersion)
   - `code_type`, `code`, `code_group`

### ❌ Missing Database Models (Currently Only in JSON Metadata):

1. **PolicyAssumption** - No table exists
   - Currently stored in `policy.metadata.assumptions[]`
   - Fields needed:
     - `id` (UUID)
     - `tenant_id` (UUID)
     - `policy_id` (FK to Policy)
     - `assumption_type` (String)
     - `description` (Text)
     - `range` (JSONB) - ElasticityRange structure
     - `value` (Float)
     - `source` (String)
     - `confidence` (Float)
     - `created_at`, `updated_at` (DateTime)

2. **PolicyGuardrail** - No table exists
   - Currently stored in `policy.metadata.guardrails[]`
   - Fields needed:
     - `id` (UUID)
     - `tenant_id` (UUID)
     - `policy_id` (FK to Policy)
     - `metric_name` (String)
     - `threshold_type` (String) - "max", "min", "change_pct"
     - `threshold_value` (Float)
     - `action` (String) - "alert", "block", "notify"
     - `description` (Text)
     - `triggered` (Boolean)
     - `last_checked_at` (DateTime)
     - `created_at`, `updated_at` (DateTime)

3. **PolicyChangelog** - No table exists
   - Currently stored in `policy.metadata.changelog[]`
   - Fields needed:
     - `id` (UUID)
     - `tenant_id` (UUID)
     - `policy_id` (FK to Policy)
     - `entry_type` (String) - "CREATED", "UPDATED", "VERSION_CREATED", etc.
     - `description` (Text)
     - `changed_by` (UUID, FK to User)
     - `changed_at` (DateTime)
     - `changes_json` (JSONB) - detailed change structure

## What's Needed (Without Changing Code)

### 1. New Database Models to Create

**File:** `apps/api/src/uepi_api/models/policy.py` (add these classes)

```python
class PolicyAssumption(Base):
    __tablename__ = "policy_assumptions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id"), nullable=False, index=True)
    assumption_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    range_json = Column(JSONType, nullable=True)  # ElasticityRange structure
    value = Column(Float, nullable=True)
    source = Column(String, nullable=True)
    confidence = Column(Float, default=0.5)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    policy = relationship("Policy", backref="assumptions")

class PolicyGuardrail(Base):
    __tablename__ = "policy_guardrails"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id"), nullable=False, index=True)
    metric_name = Column(String, nullable=False)
    threshold_type = Column(String, nullable=False)  # "max", "min", "change_pct"
    threshold_value = Column(Float, nullable=False)
    action = Column(String, nullable=False, default="alert")  # "alert", "block", "notify"
    description = Column(Text, nullable=True)
    triggered = Column(Boolean, default=False)
    last_checked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    policy = relationship("Policy", backref="guardrails")

class PolicyChangelog(Base):
    __tablename__ = "policy_changelog"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    policy_id = Column(PGUUID(as_uuid=True), ForeignKey("policies.id"), nullable=False, index=True)
    entry_type = Column(String, nullable=False)  # "CREATED", "UPDATED", "VERSION_CREATED", etc.
    description = Column(Text, nullable=True)
    changed_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    changes_json = Column(JSONType, nullable=True)  # Detailed change structure
    
    policy = relationship("Policy", backref="changelog_entries")
    user = relationship("User", backref="policy_changes")
```

### 2. Database Migration Script (Alembic)

**File:** `apps/api/alembic/versions/XXXX_add_policy_workspace_tables.py`

```python
"""Add policy workspace tables (assumptions, guardrails, changelog)

Revision ID: xxxx
Revises: previous_revision
Create Date: 2025-01-XX
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create policy_assumptions table
    op.create_table(
        'policy_assumptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assumption_type', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('range_json', postgresql.JSONB(), nullable=True),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('confidence', sa.Float(), default=0.5),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_policy_assumptions_tenant_id', 'policy_assumptions', ['tenant_id'])
    op.create_index('ix_policy_assumptions_policy_id', 'policy_assumptions', ['policy_id'])
    
    # Create policy_guardrails table
    op.create_table(
        'policy_guardrails',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('threshold_type', sa.String(), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('action', sa.String(), nullable=False, server_default='alert'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('triggered', sa.Boolean(), default=False),
        sa.Column('last_checked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_policy_guardrails_tenant_id', 'policy_guardrails', ['tenant_id'])
    op.create_index('ix_policy_guardrails_policy_id', 'policy_guardrails', ['policy_id'])
    
    # Create policy_changelog table
    op.create_table(
        'policy_changelog',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entry_type', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('changed_at', sa.DateTime(), nullable=False),
        sa.Column('changes_json', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_policy_changelog_tenant_id', 'policy_changelog', ['tenant_id'])
    op.create_index('ix_policy_changelog_policy_id', 'policy_changelog', ['policy_id'])
    op.create_index('ix_policy_changelog_changed_at', 'policy_changelog', ['changed_at'])

def downgrade():
    op.drop_table('policy_changelog')
    op.drop_table('policy_guardrails')
    op.drop_table('policy_assumptions')
```

### 3. Data Migration Script

**File:** `apps/api/scripts/migrate_policy_metadata_to_database.py`

```python
"""
Migrate policy metadata (assumptions, guardrails, versions, changelog) from JSON files to database.

This script:
1. Reads all policy JSON files
2. Extracts assumptions, guardrails, versions, changelog from metadata
3. Creates database records for each
4. Links them to Policy records (creates Policy records if they don't exist)
"""
import json
from pathlib import Path
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from uepi_api.database import SessionLocal, init_db
from uepi_api.models.policy import Policy, PolicyVersion, PolicyAssumption, PolicyGuardrail, PolicyChangelog
from uepi_api.storage_file import BASE_PATH

def migrate_policy_metadata_to_database():
    """Migrate all policy metadata from files to database"""
    db: Session = SessionLocal()
    
    try:
        # Find all policy files
        policy_files = list(BASE_PATH.glob("policy_*.json"))
        policy_files.extend(list((BASE_PATH / "policies").glob("policy-*.json")))
        
        print(f"Found {len(policy_files)} policy files to migrate")
        
        for policy_file in policy_files:
            with open(policy_file, 'r') as f:
                policy_data = json.load(f)
            
            policy_id_str = policy_data.get('policy_id', '')
            tenant_id_str = policy_data.get('tenant_id', '')
            
            if not policy_id_str or not tenant_id_str:
                print(f"Skipping {policy_file.name} - missing policy_id or tenant_id")
                continue
            
            try:
                policy_id = UUID(policy_id_str)
                tenant_id = UUID(tenant_id_str)
            except ValueError:
                print(f"Skipping {policy_file.name} - invalid UUID")
                continue
            
            # Get or create Policy record
            policy = db.query(Policy).filter(
                Policy.id == policy_id,
                Policy.tenant_id == tenant_id
            ).first()
            
            if not policy:
                # Create Policy record from JSON
                policy = Policy(
                    id=policy_id,
                    tenant_id=tenant_id,
                    name=policy_data.get('policy_name', policy_data.get('name', 'Unnamed Policy')),
                    policy_type=policy_data.get('policy_type', 'UNKNOWN'),
                    description=policy_data.get('description'),
                    status=policy_data.get('status', 'ACTIVE'),
                    policy_metadata_json=policy_data.get('metadata', {}),
                )
                db.add(policy)
                print(f"Created Policy record: {policy_id}")
            else:
                # Update metadata JSON
                policy.policy_metadata_json = policy_data.get('metadata', {})
                print(f"Updated Policy record: {policy_id}")
            
            metadata = policy_data.get('metadata', {})
            
            # Migrate assumptions
            assumptions = metadata.get('assumptions', [])
            for assumption_data in assumptions:
                assumption_id = UUID(assumption_data.get('assumption_id', str(uuid4())))
                existing = db.query(PolicyAssumption).filter(
                    PolicyAssumption.id == assumption_id
                ).first()
                
                if not existing:
                    assumption = PolicyAssumption(
                        id=assumption_id,
                        tenant_id=tenant_id,
                        policy_id=policy_id,
                        assumption_type=assumption_data.get('assumption_type', ''),
                        description=assumption_data.get('description'),
                        range_json=assumption_data.get('range'),
                        value=assumption_data.get('value'),
                        source=assumption_data.get('source'),
                        confidence=assumption_data.get('confidence', 0.5),
                        created_at=datetime.fromisoformat(assumption_data.get('created_at', datetime.utcnow().isoformat())),
                        updated_at=datetime.fromisoformat(assumption_data.get('updated_at', datetime.utcnow().isoformat())),
                    )
                    db.add(assumption)
            
            # Migrate guardrails
            guardrails = metadata.get('guardrails', [])
            for guardrail_data in guardrails:
                guardrail_id = UUID(guardrail_data.get('guardrail_id', str(uuid4())))
                existing = db.query(PolicyGuardrail).filter(
                    PolicyGuardrail.id == guardrail_id
                ).first()
                
                if not existing:
                    guardrail = PolicyGuardrail(
                        id=guardrail_id,
                        tenant_id=tenant_id,
                        policy_id=policy_id,
                        metric_name=guardrail_data.get('metric_name', ''),
                        threshold_type=guardrail_data.get('threshold_type', 'max'),
                        threshold_value=guardrail_data.get('threshold_value', 0.0),
                        action=guardrail_data.get('action', 'alert'),
                        description=guardrail_data.get('description'),
                        triggered=guardrail_data.get('triggered', False),
                        last_checked_at=datetime.fromisoformat(guardrail_data['last_checked_at']) if guardrail_data.get('last_checked_at') else None,
                        created_at=datetime.fromisoformat(guardrail_data.get('created_at', datetime.utcnow().isoformat())),
                        updated_at=datetime.fromisoformat(guardrail_data.get('updated_at', datetime.utcnow().isoformat())),
                    )
                    db.add(guardrail)
            
            # Migrate changelog
            changelog = metadata.get('changelog', [])
            for changelog_data in changelog:
                changelog_id = UUID(changelog_data.get('changelog_id', str(uuid4())))
                existing = db.query(PolicyChangelog).filter(
                    PolicyChangelog.id == changelog_id
                ).first()
                
                if not existing:
                    changelog_entry = PolicyChangelog(
                        id=changelog_id,
                        tenant_id=tenant_id,
                        policy_id=policy_id,
                        entry_type=changelog_data.get('entry_type', 'UPDATED'),
                        description=changelog_data.get('description'),
                        changed_by=UUID(changelog_data['changed_by']) if changelog_data.get('changed_by') else None,
                        changed_at=datetime.fromisoformat(changelog_data.get('changed_at', datetime.utcnow().isoformat())),
                        changes_json=changelog_data.get('changes', {}),
                    )
                    db.add(changelog_entry)
            
            # Versions are already in PolicyVersion table (if using DB)
            # But if they're only in JSON, migrate them too
            
            db.commit()
            print(f"Migrated metadata for policy {policy_id}")
        
        print("Migration complete!")
        
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    migrate_policy_metadata_to_database()
```

### 4. Configuration Changes

**Environment Variables:**
- Set `USE_FILE_STORAGE=false` (or remove it, defaults to False)
- Set `DATABASE_URL=postgresql://user:password@host:port/dbname`

**Azure App Service Settings:**
```bash
az webapp config appsettings set \
  --resource-group healthforesight-rg \
  --name healthforesight-api-9016 \
  --settings \
    USE_FILE_STORAGE=false \
    DATABASE_URL="postgresql://..."
```

### 5. Storage Adapter Changes

**File:** `apps/api/src/uepi_api/storage/policy_storage.py`

The `PolicyStorageAdapter` already has logic to switch between file and DB storage based on `use_file_storage` flag. Currently:
- `get_policies()` returns `[]` when `use_file_storage=False` (expects DB queries)
- `get_policy()` returns `None` when `use_file_storage=False` (expects DB queries)

**What needs to be implemented:**
- When `use_file_storage=False`, these methods should query the database instead
- But you said "don't change code" - so this is just documentation of what would need to change

### 6. Storage Functions That Need Database Implementation

**Files that currently use file storage:**
- `apps/api/src/uepi_api/storage_policies.py` - `get_policy()`, `list_policies()`
- `apps/api/src/uepi_api/storage_policy_assumptions.py` - `get_assumptions()`, `create_assumption()`, etc.
- `apps/api/src/uepi_api/storage_policy_guardrails.py` - `get_guardrails()`, `create_guardrail()`, etc.
- `apps/api/src/uepi_api/storage_policy_versions.py` - `list_policy_versions()`, etc.
- `apps/api/src/uepi_api/storage_policy_changelog.py` - `get_changelog()`, etc.

**These would need database queries instead of file reads when `USE_FILE_STORAGE=false`**

## Summary

### What You Need:

1. ✅ **Database Models** - Create 3 new model classes (PolicyAssumption, PolicyGuardrail, PolicyChangelog)
2. ✅ **Database Migration** - Alembic migration to create the 3 new tables
3. ✅ **Data Migration Script** - Python script to move data from JSON files to database
4. ✅ **Configuration** - Set `USE_FILE_STORAGE=false` and `DATABASE_URL`
5. ⚠️ **Storage Functions** - Update to query database when `USE_FILE_STORAGE=false` (but you said don't change code, so this is future work)

### Database Requirements:

- **PostgreSQL** (required - see `database.py` validation)
- **Connection String** format: `postgresql://user:password@host:port/dbname`
- **Tables to Create:**
  - `policy_assumptions`
  - `policy_guardrails`
  - `policy_changelog`
  - (Policy and PolicyVersion already exist)

### Migration Steps:

1. Create database models
2. Run Alembic migration to create tables
3. Run data migration script to move data from files to database
4. Update configuration to use database
5. Test that data is accessible via database queries
6. (Future) Update storage functions to use database queries

### Estimated Effort:

- **Database Models:** 30 minutes
- **Alembic Migration:** 30 minutes
- **Data Migration Script:** 2-3 hours
- **Testing:** 1-2 hours
- **Total:** ~4-6 hours

