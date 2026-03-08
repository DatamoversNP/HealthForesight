# Timestamp and Versioning Verification

## ✅ All Database Models Include Proper Timestamps

### Base Attributes in All Models:

1. **`created_at`** - `DateTime, default=datetime.utcnow, nullable=False, index=True`
   - Automatically set when record is created
   - Indexed for time-based queries
   - Always present (not nullable)

2. **`updated_at`** - `DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False`
   - Automatically set when record is created
   - Automatically updated when record is modified (via SQLAlchemy `onupdate`)
   - Always present (not nullable)

### Versioning Support:

1. **Baseline Model:**
   - `version` - `Integer, nullable=False, default=1` - Tracks baseline version number

2. **Pipeline Model:**
   - `version` - `String, nullable=True, default="1.0"` - Tracks pipeline version

3. **PolicyVersion Model (existing):**
   - `version_number` - `Integer, nullable=False` - Tracks policy version

### Additional Timestamp Fields (where applicable):

1. **PolicyChangelog:**
   - `changed_at` - When the change occurred (indexed)

2. **Scenario:**
   - `completed_at` - When scenario completed (indexed)

3. **PipelineRun:**
   - `started_at` - When run started (indexed)
   - `ended_at` - When run ended (indexed)

4. **Risk:**
   - `mitigated_at` - When risk was mitigated (indexed)

5. **AlertEvent:**
   - `triggered_at` - When alert was triggered (indexed)
   - `resolved_at` - When alert was resolved (indexed)

6. **Task:**
   - `due_date` - Task due date (indexed)
   - `completed_at` - When task was completed (indexed)

7. **Approval:**
   - `requested_at` - When approval was requested (indexed)
   - `approved_at` - When approval was granted (indexed)

8. **Baseline:**
   - `computed_at` - When baseline was computed (indexed)

9. **Observation:**
   - `computed_at` - When observation was computed (indexed)

10. **PolicyPredictedImpact:**
    - `predicted_at` - When prediction was made (indexed)

11. **ElasticityModel:**
    - `trained_at` - When model was trained (indexed)

12. **ModelAccuracyHistory:**
    - `evaluation_date` - When evaluation was performed (indexed)

13. **BehaviorProfile:**
    - `detected_at` - When behavior was detected (indexed)

14. **Schedule:**
    - `last_run_at` - Last time schedule ran (indexed)
    - `next_run_at` - Next scheduled run time (indexed)

## Storage Functions Ensure Timestamps

### All Database Storage Functions:

1. **Create Operations:**
   - `created_at` automatically set by SQLAlchemy `default=datetime.utcnow`
   - `updated_at` automatically set by SQLAlchemy `default=datetime.utcnow`
   - No manual timestamp setting needed

2. **Update Operations:**
   - `updated_at` automatically updated by SQLAlchemy `onupdate=datetime.utcnow`
   - No manual timestamp update needed

3. **Return Format:**
   - All database functions return timestamps as ISO format strings (same as file-based)
   - Example: `created_at.isoformat() if created_at else None`

## Verification Checklist

- ✅ All 18 models have `created_at` with `default=datetime.utcnow`
- ✅ All 18 models have `updated_at` with `onupdate=datetime.utcnow`
- ✅ All timestamps are properly indexed where needed
- ✅ Storage functions preserve timestamp format (ISO strings)
- ✅ Version fields included where applicable (Baseline, Pipeline, PolicyVersion)
- ✅ Additional timestamp fields for business logic (completed_at, triggered_at, etc.)

## Example Model Structure:

```python
class ExampleModel(Base):
    __tablename__ = "example"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Business fields...
    
    # Timestamps (ALWAYS PRESENT)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Version (where applicable)
    version = Column(Integer, nullable=False, default=1)  # or String for semantic versioning
```

## Summary

**All models and storage functions properly handle:**
- ✅ Creation timestamps (automatic)
- ✅ Update timestamps (automatic)
- ✅ Version tracking (where applicable)
- ✅ Business-specific timestamps (completed_at, triggered_at, etc.)
- ✅ Consistent ISO format in API responses

