# Deferred Traceability Integration Tasks

These tasks are tracked for later implementation but are deferred in favor of Phase 2 (Baseline Refresh System).

## Remaining Tasks

### Task 3: Add Traceability to Predicted Impact Generation
**Priority**: Medium  
**Status**: Deferred  
**Estimated Time**: 1 hour

**Description**:  
Add traceability metadata when predicted impacts are generated. Link predictions to:
- Policy version used
- Baseline version used
- Data period used

**Integration Points**:
- `apps/api/src/uepi_api/routers/policy_predicted_impact.py` - When generating predicted impact
- `apps/api/src/uepi_api/routers/policies_file.py` - Predicted impact generation endpoints

**Implementation Notes**:
- Use `uepi_api.traceability.add_traceability()` function
- Store traceability metadata with predicted impact records
- Link to policy_version_id and baseline_version_id

---

### Task 4: Add Traceability to Baseline Analyses
**Priority**: Medium  
**Status**: Deferred  
**Estimated Time**: 1-2 hours

**Description**:  
Add traceability metadata to baseline analyses. Link baselines to:
- Data periods used
- Policy versions (if policy-specific baseline)
- Baseline version

**Integration Points**:
- `apps/api/src/uepi_api/baseline_refresh.py` - When creating baselines (Phase 2)
- `apps/api/src/uepi_api/routers/baselines.py` - Baseline creation endpoints (Phase 2)

**Implementation Notes**:
- Use `uepi_api.traceability.add_traceability()` function
- Link baseline to data_period_ids used
- Link to policy_id/policy_version_id if policy-specific

---

### Task 5: Add Traceability to Observed Impacts
**Priority**: Low  
**Status**: Deferred  
**Estimated Time**: 1-2 hours

**Description**:  
Add traceability metadata to observed impact analyses. Link observations to:
- Data periods used
- Policy version
- Baseline version
- Predicted impact version

**Integration Points**:
- `apps/api/src/uepi_api/routers/analyses.py` - Impact analysis creation
- `apps/worker/src/uepi_worker/impact_analysis.py` - When computing observed impacts

**Implementation Notes**:
- Use `uepi_api.traceability.add_traceability()` function
- Link observation to data_period_id, policy_version_id, baseline_version_id, prediction_id
- Store traceability in analysis result metadata

---

## When to Implement

These tasks can be implemented:
- After Phase 2 (Baseline Refresh System) is complete
- As part of Phase 3 (Observed Impact Enhancement)
- When traceability becomes a priority requirement

The traceability framework (`apps/api/src/uepi_api/traceability.py`) is already in place from Phase 1, so these integrations will be straightforward.
