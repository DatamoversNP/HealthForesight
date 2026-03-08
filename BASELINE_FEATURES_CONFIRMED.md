# Baseline Creation Features - Confirmed in Product Code

## ✅ All Features Are Part of the Product Code (Not Scripts)

All the following features are **permanently integrated** into the baseline creation functions in the product codebase:

### 1. ✅ Baselines Use Historical Data Only (Before Policy Activation)

**Location:** `apps/api/src/uepi_api/baseline_refresh.py`

**Implementation:**
- Lines 333-353: For policy-specific baselines, the code automatically adjusts the date window to end **1 day before policy activation**
- Lines 259-298: Fallback path also adjusts dates before activation
- Uses `get_latest_policy_version()` to get `effective_start_date`
- Automatically sets `window_end_date = policy_activation_date - timedelta(days=1)`

**Code:**
```python
# For policy-specific baselines: Adjust window to end BEFORE policy activation
if policy_id:
    latest_version = get_latest_policy_version(policy_id, tenant_id)
    if latest_version and latest_version.get("effective_start_date"):
        policy_activation_date = datetime.fromisoformat(activation_str).date()
        # Ensure baseline window ends BEFORE activation
        if window_end_date >= policy_activation_date:
            window_end_date = policy_activation_date - timedelta(days=1)
```

### 2. ✅ Policy-Specific Baselines Filtered by Policy Scope

**Location:** `apps/api/src/uepi_api/services/database_baseline_computation.py`

**Implementation:**
- Lines 67-235: `compute_policy_specific_baseline_from_database()` function
- Extracts LOB, markets, procedure codes, diagnosis codes, service categories from policy scope
- Filters claims at database level for performance
- Uses `CanonicalDataRepository.get_claims_lines()` with filters

**Code:**
```python
def compute_policy_specific_baseline_from_database(
    tenant_id: UUID,
    policy_id: UUID,
    start_date: date,
    end_date: date,
    policy_scope: Dict[str, Any],
    db: Session,
    policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    # Extracts codes from policy levers
    # Filters by LOB, markets, CPT codes, service categories
    claims_df = repo.get_claims_lines(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        lob=lob_filter,
        market=market_filter,
        cpt_codes=merged_procedure_codes,
        service_categories=merged_service_categories,
    )
```

### 3. ✅ Date Ranges Automatically Adjusted Before Activation

**Location:** `apps/api/src/uepi_api/baseline_refresh.py`

**Implementation:**
- **Main path (lines 333-353):** Adjusts window_end_date before computing baseline
- **Fallback path (lines 259-298):** Also adjusts end_date before computing from database
- Works for both ROLLING and FIXED baseline types
- Automatically recalculates start_date if needed

**Code:**
```python
# For policy-specific baselines: Adjust window to end BEFORE policy activation
if policy_id:
    policy_activation_date = datetime.fromisoformat(activation_str).date()
    if window_end_date >= policy_activation_date:
        window_end_date = policy_activation_date - timedelta(days=1)
        window_end_date_str = window_end_date.isoformat()
        # Recalculate start date if needed
        if baseline_type == "ROLLING":
            window_start_date = window_end_date - timedelta(days=window_months * 30)
```

### 4. ✅ UUID Conversion Bug Fixed

**Location:** `apps/api/src/uepi_api/storage_baselines.py`

**Implementation:**
- Lines 35-55: Handles both UUID objects and strings
- Prevents `'UUID' object has no attribute 'replace'` error
- Works for both `policy_id` and `parent_baseline_id`

**Code:**
```python
# Parse UUIDs - handle both UUID objects and strings
policy_id_value = baseline_data.get("policy_id")
if policy_id_value:
    if isinstance(policy_id_value, UUID):
        policy_id = policy_id_value
    elif isinstance(policy_id_value, str):
        policy_id = UUID(policy_id_value)
    else:
        policy_id = None
else:
    policy_id = None
```

## Product Code Files (Not Scripts)

All features are in these **permanent product files**:

1. **`apps/api/src/uepi_api/baseline_refresh.py`**
   - Main baseline refresh function
   - Activation date adjustment logic
   - Policy scope extraction

2. **`apps/api/src/uepi_api/services/database_baseline_computation.py`**
   - Policy-specific baseline computation
   - Policy scope filtering (LOB, markets, codes)

3. **`apps/api/src/uepi_api/storage_baselines.py`**
   - UUID conversion handling
   - Database persistence

4. **`apps/api/src/uepi_api/routers/baselines.py`**
   - API endpoint that calls `refresh_baseline()`

## How It Works

When a user calls the baseline refresh API endpoint:

1. **API Endpoint:** `POST /api/v1/baselines/refresh`
2. **Router:** `apps/api/src/uepi_api/routers/baselines.py` → `refresh_baseline_route()`
3. **Core Function:** `apps/api/src/uepi_api/baseline_refresh.py` → `refresh_baseline()`
4. **Computation:** `apps/api/src/uepi_api/services/database_baseline_computation.py` → `compute_policy_specific_baseline_from_database()`
5. **Storage:** `apps/api/src/uepi_api/storage_baselines.py` → `create_baseline()`

**All features are automatically applied** - no scripts needed!

## Verification

To verify these features are working:

```bash
# Create a policy-specific baseline via API
curl -X POST http://localhost:8000/api/v1/baselines/refresh \
  -H "Content-Type: application/json" \
  -d '{"policy_id": "your-policy-id", "baseline_type": "ROLLING", "window_months": 12}'
```

The baseline will automatically:
- ✅ Use only historical data (before activation)
- ✅ Filter by policy scope (LOB, markets, codes)
- ✅ Adjust date range to end before activation
- ✅ Handle UUIDs correctly

## Scripts vs Product Code

**Scripts (one-time use):**
- `scripts/fresh_start_workflow.py` - Helper to run workflow
- `scripts/cleanup_db.py` - Cleanup utility
- `scripts/generate_historical_data.py` - Data generation helper

**Product Code (permanent features):**
- All baseline creation logic in `apps/api/src/uepi_api/`
- All features work automatically via API endpoints
- No scripts needed for normal operation
