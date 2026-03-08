# Pending Product Items & Flow Gaps

## 🔴 Critical Product Flow Gaps

### 1. Automatic Learning Loop (Step 7)
**Status**: ⚠️ Partially Implemented
- ✅ Learning endpoints exist (`/learning/*`)
- ✅ Elasticity model storage implemented
- ❌ **MISSING**: Automatic learning trigger when observations are created
- ❌ **MISSING**: Automatic prediction accuracy recording
- **Impact**: System doesn't automatically improve from observed outcomes

**Files to Fix**:
- `apps/api/src/uepi_api/observation_enhancement.py` - Add automatic learning trigger
- `apps/api/src/uepi_api/routers/daily_jobs.py` - Trigger learning after observation creation

---

### 2. What-If Scenarios Enhancement (Step 8)
**Status**: ⚠️ Basic Implementation
- ✅ Simulation endpoint exists (`/analyses/simulate`)
- ✅ Tradeoff analysis added
- ✅ Risk analysis added
- ⚠️ **UNCLEAR**: Whether latest elasticity models are always used
- ⚠️ **GAP**: May not show tradeoffs and risks clearly in UI
- **Impact**: What-if analysis may not be using latest learned models

**Files to Verify**:
- `apps/api/src/uepi_api/routers/analyses_file.py` - Verify latest elasticity model usage
- `apps/web/src/pages/WhatIfAnalysisPage.tsx` - Verify tradeoff/risk display

---

### 3. Continuous Learning Cycle (Step 9)
**Status**: ❌ Not Fully Automated
- ✅ Daily job infrastructure exists
- ❌ **MISSING**: Automatic learning updates when new observations available
- ❌ **MISSING**: Automatic prediction regeneration when models update
- ❌ **MISSING**: Stale prediction detection and refresh
- **Impact**: Predictions don't automatically refresh when models improve

**Files to Fix**:
- `apps/api/src/uepi_api/learning_loop.py` - Add policy update trigger
- `apps/api/src/uepi_api/routers/policies_file.py` - Add stale prediction handling

---

## 🟡 UI/UX Improvements Needed

### 4. Refresh Indicators Enhancement
**Status**: ⚠️ Basic Implementation
- ✅ `RefreshIndicator` component exists
- ⚠️ **GAP**: May not show all refresh reasons clearly
- ⚠️ **GAP**: Staleness indicators may not be comprehensive
- **Impact**: Users may not know when data/insights are stale

**Enhancements Needed**:
- Show last refresh timestamp prominently
- Display refresh reason (new data, policy change, model update)
- Visual staleness indicators (color-coded badges)
- Auto-refresh suggestions

---

### 5. Clear Separation in UI (Baseline/Predicted/Observed)
**Status**: ✅ Structure Exists
- ✅ Separate tabs/sections exist
- ⚠️ **GAP**: Visual improvements needed for clarity
- ⚠️ **GAP**: Side-by-side comparison views could be better
- **Impact**: Users may struggle to distinguish baseline vs predicted vs observed

**Enhancements Needed**:
- Visual distinction (colors, icons, badges)
- Clear labeling and tooltips
- Improved comparison views

---

## 🟠 Technical Debt & TODOs

### 6. Time Series Data Loading
**Status**: ❌ Not Implemented
- **Location**: `apps/api/src/uepi_api/routers/analyses.py:694`
- **TODO**: "Load timeseries from object storage"
- **Impact**: Time series analysis may not work correctly

---

### 7. Control Group Suggestion Logic
**Status**: ❌ Not Implemented
- **Location**: `apps/api/src/uepi_api/routers/analyses.py:926`
- **TODO**: "Implement control group suggestion logic"
- **Impact**: Users must manually configure control groups

---

### 8. Baseline Metrics Loading
**Status**: ⚠️ Partial
- **Location**: `apps/api/src/uepi_api/routers/policies.py:167,820`
- **TODO**: "Load baseline metrics if available"
- **Impact**: Policy summaries may not show baseline context

---

### 9. Elasticity Data Loading for Predicted Impact
**Status**: ⚠️ Partial
- **Location**: `apps/api/src/uepi_api/routers/policy_predicted_impact.py:33`
- **TODO**: "Load elasticity data if available (from elasticity analyses)"
- **Impact**: Predicted impact may not use latest elasticity models

---

### 10. Signed Download URLs for Exports
**Status**: ❌ Not Implemented
- **Location**: `apps/api/src/uepi_api/routers/exports_db.py.bak:155`
- **TODO**: "Generate signed download URL"
- **Impact**: File exports may not have secure download links

---

### 11. Scheduled Job Registration
**Status**: ⚠️ Partial
- **Location**: `apps/api/src/uepi_api/routers/ingestions.py:438`
- **TODO**: "Register scheduled job with Celery Beat or Kubernetes CronJob"
- **Note**: Schedule executor service exists but may need integration
- **Impact**: Scheduled jobs may not be properly registered with task queue

---

### 12. Analysis Runs Linking (Lineage)
**Status**: ⚠️ Partial
- **Location**: `apps/api/src/uepi_api/routers/data_health.py:219`
- **TODO**: "Add analysis runs linking (Phase 5)"
- **Impact**: Data health may not show complete lineage

---

## 🟢 Production Readiness (Phase 10.5)

### 13. Error Handling & Monitoring
**Status**: ⚠️ Basic
- ⚠️ **GAP**: Comprehensive error tracking
- ⚠️ **GAP**: Application performance monitoring (APM)
- ⚠️ **GAP**: Structured logging
- ⚠️ **GAP**: Error alerting

---

### 14. Performance Optimization
**Status**: ⚠️ Not Optimized
- ⚠️ **GAP**: Query optimization for large datasets
- ⚠️ **GAP**: Caching strategy
- ⚠️ **GAP**: Background job optimization
- ⚠️ **GAP**: API response time optimization

---

### 15. Security & Access Control
**Status**: ⚠️ Basic
- ✅ Authentication exists
- ⚠️ **GAP**: Role-based access control (RBAC) refinement
- ⚠️ **GAP**: API rate limiting
- ⚠️ **GAP**: Input validation hardening
- ⚠️ **GAP**: Security audit logging

---

### 16. Testing & Quality Assurance
**Status**: ⚠️ Partial
- ⚠️ **GAP**: Comprehensive integration tests
- ⚠️ **GAP**: End-to-end (E2E) tests
- ⚠️ **GAP**: Performance/load tests
- ⚠️ **GAP**: Regression test suite

---

### 17. Documentation
**Status**: ⚠️ Partial
- ⚠️ **GAP**: API documentation (OpenAPI/Swagger completion)
- ⚠️ **GAP**: User guide/documentation
- ⚠️ **GAP**: Deployment guide
- ⚠️ **GAP**: Architecture decision records (ADRs)

---

## 📊 Data & Analytics Gaps

### 18. Coverage Data Population
**Status**: ⚠️ Implemented but may need testing
- ✅ Coverage computation from parquet files implemented
- ⚠️ **GAP**: Needs validation with real data
- ⚠️ **GAP**: May need fallback strategies

---

### 19. Lineage Data Population
**Status**: ⚠️ Implemented but needs validation
- ✅ Full lineage tracking implemented
- ⚠️ **GAP**: Needs testing with complete workflows
- ⚠️ **GAP**: Relationship mapping may need refinement

---

## 🔄 Integration Gaps

### 20. Schedule Executor Service Integration
**Status**: ⚠️ Exists but may need refinement
- ✅ Schedule executor service exists
- ⚠️ **GAP**: Proper startup/shutdown integration
- ⚠️ **GAP**: Error handling in background jobs
- ⚠️ **GAP**: Job status tracking and reporting

---

### 21. Notification System Integration
**Status**: ✅ Basic implementation
- ✅ Notification storage and endpoints exist
- ⚠️ **GAP**: Integration with schedule executor
- ⚠️ **GAP**: Email/webhook delivery (if needed)
- ⚠️ **GAP**: Notification preferences

---

## 🎯 Priority Recommendations

### High Priority (Product Flow Critical)
1. **Automatic Learning Loop** - Enables continuous improvement
2. **Continuous Learning Cycle** - Ensures predictions stay current
3. **What-If Scenarios Enhancement** - Critical feature validation

### Medium Priority (UX & Quality)
4. **Refresh Indicators Enhancement** - Better user experience
5. **Clear Separation in UI** - Prevents confusion
6. **Time Series Data Loading** - Feature completeness

### Lower Priority (Polish & Production)
7. **Production Readiness** - Error handling, monitoring, security
8. **Testing & Documentation** - Quality and maintainability
9. **Performance Optimization** - Scalability

---

## 📝 Next Steps Checklist

- [ ] Implement automatic learning trigger in observation creation
- [ ] Verify and enhance what-if scenarios to use latest models
- [ ] Implement automatic prediction regeneration on model updates
- [ ] Enhance refresh indicators with comprehensive staleness tracking
- [ ] Improve UI visual separation of baseline/predicted/observed
- [ ] Implement time series data loading
- [ ] Add control group suggestion logic
- [ ] Complete production readiness items (error handling, monitoring, security)
- [ ] Comprehensive testing suite
- [ ] Complete documentation
