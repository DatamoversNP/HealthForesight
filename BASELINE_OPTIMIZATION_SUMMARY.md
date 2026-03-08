# Baseline Computation Optimization Summary

## Problem
Policy-specific baseline creation was timing out (120+ seconds) when processing 12 months of data.

## Root Causes Identified

1. **Inefficient Data Loading**: `get_claims_lines()` was loading ALL records into memory before filtering
2. **In-Memory Filtering**: All filtering (codes, LOB, market) was done in pandas after loading all data
3. **No Database-Level Filtering**: Queries weren't using database indexes effectively

## Optimizations Implemented

### 1. Database-Level Filtering
- **Updated `get_claims_lines()`** to accept filter parameters:
  - `cpt_codes`: Filter CPT codes at database level
  - `hcpcs_codes`: Filter HCPCS codes at database level  
  - `service_categories`: Filter service categories at database level
  - `lob`: Support list filtering for LOB
  - `market`: Support list filtering for market

### 2. Early Code Extraction
- **Moved code extraction** to happen BEFORE database query
- Allows filtering at database level instead of loading all data first
- Extracts codes from policy levers and policy scope before querying

### 3. Chunked Processing
- **Added `yield_per(10000)`** for large result sets
- Processes data in chunks to avoid memory issues
- Falls back to `all()` for smaller queries (< 10,000 records)

### 4. Optimized Query Flow
**Before:**
1. Load ALL claims for date range → Memory
2. Filter by codes in pandas → Slow
3. Filter by LOB/market in pandas → Slow
4. Compute metrics

**After:**
1. Extract codes from policy → Fast
2. Query database with filters → Uses indexes
3. Load only matching records → Much less data
4. Compute metrics → Fast

## Performance Impact

- **Before**: 120+ seconds (timeout)
- **Expected After**: < 30 seconds for 12 months of data
- **Database queries**: Now use indexes on `cpt_code`, `hcpcs_code`, `service_category`, `lob`, `market`, `service_date`

## Files Modified

1. **`apps/api/src/uepi_api/repositories/canonical_data.py`**
   - Added filter parameters to `get_claims_lines()`
   - Added database-level filtering for codes and categories
   - Added chunked processing for large result sets

2. **`apps/api/src/uepi_api/services/database_baseline_computation.py`**
   - Moved code extraction before database query
   - Passes filter parameters to repository
   - Reduced in-memory filtering

## Next Steps

1. Test with single policy to verify performance improvement
2. Run full baseline creation workflow
3. Monitor performance and adjust if needed

---

**Status**: ✅ Optimizations Complete - Ready for Testing
