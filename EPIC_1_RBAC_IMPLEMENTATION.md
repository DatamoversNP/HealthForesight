# Epic 1: Role-Based Experience - Implementation Plan

## Overview
Implement role-based access control (RBAC) with persona dashboards and permission-aware UI.

## Data Model Extensions

### New Models (in `models_enhanced.py`)
- `PersonaRole` enum: EXECUTIVE, POLICY_OWNER, ANALYST, OPS_CLINICAL
- `ResourceType` enum: POLICY, ANALYSIS, DECISION, DATASET, MODEL, EXPORT, etc.
- `ActionType` enum: CREATE, READ, UPDATE, DELETE, APPROVE, EXPORT, EXECUTE
- `ResourceScope`: Resource-level access scoping
- `Permission`: Permission definition
- `Role`: Role with permissions
- `UserRole`: User role assignment with resource scopes

## File Storage Extensions

### New Storage Modules Needed
1. `storage_roles.py` - Role definitions
2. `storage_user_roles.py` - User role assignments
3. `storage_permissions.py` - Permission checks

## API Endpoints

### Role Management
- `GET /api/v1/roles` - List all roles
- `GET /api/v1/roles/{role_id}` - Get role details
- `POST /api/v1/roles` - Create role (admin only)
- `PUT /api/v1/roles/{role_id}` - Update role (admin only)

### User Role Assignment
- `GET /api/v1/users/{user_id}/roles` - Get user roles
- `POST /api/v1/users/{user_id}/roles` - Assign roles (admin only)
- `DELETE /api/v1/users/{user_id}/roles/{role_id}` - Remove role (admin only)

### Permission Checks
- `GET /api/v1/permissions/check` - Check if user has permission
- `GET /api/v1/users/{user_id}/permissions` - Get effective permissions

### Persona Dashboards
- `GET /api/v1/dashboards/executive` - Executive dashboard data
- `GET /api/v1/dashboards/policy-owner` - Policy owner dashboard
- `GET /api/v1/dashboards/analyst` - Analyst dashboard
- `GET /api/v1/dashboards/ops-clinical` - Ops/Clinical dashboard

## Frontend Components

### Role Switcher
- Component: `RoleSwitcher.tsx`
- Location: Top navigation bar
- Functionality: Switch between persona views

### Persona Dashboards
- `ExecutiveDashboard.tsx`
- `PolicyOwnerDashboard.tsx`
- `AnalystDashboard.tsx`
- `OpsClinicalDashboard.tsx`

### Permission-Aware Components
- `PermissionGate.tsx` - Wrapper to hide/disable based on permissions
- `usePermissions` hook - React hook for permission checks

## Implementation Steps

1. ✅ Create enhanced data models
2. ⏳ Create file-based storage for roles/permissions
3. ⏳ Extend API endpoints
4. ⏳ Build frontend role switcher
5. ⏳ Build persona dashboards
6. ⏳ Add permission-aware UI components
7. ⏳ Add acceptance tests


