# Product Uplift Implementation Roadmap

## Overview

This document provides a structured, incremental approach to implementing all 7 epics for enterprise product uplift.

## Phase 1: Foundation (Week 1-2)

### Task 1.1: Enhanced Data Models ✅
- [x] Create `models_enhanced.py` with all new models
- [ ] Update existing models to include new fields
- [ ] Add migration utilities for existing data

### Task 1.2: RBAC File Storage ✅
- [x] Create `storage_roles.py`
- [x] Create `storage_user_roles.py`
- [ ] Create `storage_permissions.py` (permission checking utilities)
- [ ] Add to `init_storage()`

### Task 1.3: RBAC API Endpoints
- [ ] Create/update `/api/v1/roles` endpoints
- [ ] Create/update `/api/v1/users/{user_id}/roles` endpoints
- [ ] Create `/api/v1/permissions/check` endpoint
- [ ] Update auth middleware to use file-based RBAC

### Task 1.4: Policy Lifecycle Storage
- [ ] Create `storage_policy_versions.py`
- [ ] Create `storage_policy_assumptions.py`
- [ ] Create `storage_policy_guardrails.py`
- [ ] Create `storage_policy_changelog.py`
- [ ] Update `storage_policies.py` to support lifecycle states

## Phase 2: Core Features (Week 3-4)

### Task 2.1: Policy Lifecycle API & UI
- [ ] Policy workspace API endpoints
- [ ] Policy versioning API
- [ ] Policy workspace UI (tabs: Overview, Scope, Assumptions, Monitoring, Versions, Decisions, Evidence)
- [ ] State promotion workflow UI

### Task 2.2: Decision Audit Trail
- [ ] Create `storage_decisions.py`
- [ ] Create `storage_audit_trail.py`
- [ ] Decision API endpoints
- [ ] Audit trail visualization UI
- [ ] Reproducibility feature (pin inputs)

### Task 2.3: Uncertainty Visualization
- [ ] Update predicted impact models to include distributions
- [ ] Update API to return confidence intervals
- [ ] Fan chart components
- [ ] Sensitivity panel UI
- [ ] Risk register component

## Phase 3: Advanced Features (Week 5-6)

### Task 3.1: Role-Based Dashboards
- [ ] Executive dashboard API
- [ ] Policy Owner dashboard API
- [ ] Analyst dashboard API
- [ ] Ops/Clinical dashboard API
- [ ] Dashboard UI components
- [ ] Role switcher component

### Task 3.2: Behavioral Signal Detection
- [ ] Create `storage_behavior_signals.py`
- [ ] Signal detection algorithms
- [ ] Provider behavior classification API
- [ ] Behavior dashboard UI
- [ ] Alert system

### Task 3.3: Collaboration Workflows
- [ ] Create `storage_comments.py`
- [ ] Create `storage_tasks.py`
- [ ] Create `storage_approvals.py`
- [ ] Create `storage_activity.py`
- [ ] Collaboration UI components
- [ ] Notification system

### Task 3.4: Executive Narrative Layer
- [ ] Narrative generation logic
- [ ] Export template system
- [ ] Board/Regulator/Provider pack generators
- [ ] Narrative mode UI toggle
- [ ] Export UI

## Phase 4: Polish (Week 7-8)

### Task 4.1: Responsive UI
- [ ] Desktop layout (12-col grid)
- [ ] Tablet layout (collapsible nav)
- [ ] Mobile layout (hamburger nav)
- [ ] Responsive charts

### Task 4.2: Accessibility
- [ ] WCAG 2.1 AA compliance
- [ ] Keyboard navigation
- [ ] Screen reader support
- [ ] Focus management

### Task 4.3: Testing & Documentation
- [ ] Unit tests for new models
- [ ] Integration tests for APIs
- [ ] E2E tests for workflows
- [ ] API documentation
- [ ] User guides

## Quick Start: Begin with Epic 1

To start implementing, begin with:

1. **RBAC Foundation** (Epic 1, Part 1)
   - File storage modules ✅
   - API endpoints (next)
   - Frontend role switcher

2. **Policy Lifecycle** (Epic 2)
   - Extend policy storage
   - Add versioning
   - Build workspace UI

3. **Decision Audit** (Epic 3)
   - Decision storage
   - Audit trail
   - Export packs

Continue in recommended order from the master plan.


