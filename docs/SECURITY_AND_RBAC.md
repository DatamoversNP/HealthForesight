# Security Model and Role-Based Access Control (RBAC)

## Overview

- **Authentication**: Supports both **Active Directory (Azure AD / OIDC)** and **regular (local) users** with email/password.
- **Authorization**: Role-based. Each user has one or more roles; permissions are derived from roles.

## Identity Sources

| Type | How they sign in | Stored in DB |
|------|------------------|--------------|
| **Active Directory (OIDC)** | SSO via Azure AD or another OIDC provider. Frontend sends Bearer token from IdP. | User created/linked on first login; `auth_source=oidc`, `oidc_sub` set. |
| **Local (regular) users** | Email + password. Use `POST /api/v1/auth/login` with `{ "email", "password" }`; use returned `access_token` as Bearer. | Created by admin in User Management; `auth_source=local`, `password_hash` set. |

- **auth_source** on each user: `"oidc"` (e.g. Azure AD) or `"local"`.
- OIDC users cannot have a password set; local users can. Admins can create local users with or without an initial password (set later via Edit user).

## Roles and Permissions

| Role          | Description                    | Key permissions |
|---------------|--------------------------------|-----------------|
| POLICY_ADMIN  | Policy administrator           | Full access: policies, users, tenants, analyses, exports, decisions, scorecards, cohorts |
| UM_LEADER     | Utilization management leader  | Create/read policies, analyses, exports, decisions; read scorecards, cohorts |
| ACTUARIAL     | Actuarial                      | Read policies, analyses, exports, scorecards; create/read/update cohorts |
| STRATEGY      | Strategy                        | Read policies, analyses, exports, decisions, scorecards, cohorts |
| COMPLIANCE    | Compliance                      | Read-only: policies, analyses, exports, decisions, scorecards, cohorts |
| EXEC_VIEWER   | Executive viewer                | Read-only: policies, analyses, exports, decisions, scorecards |

Permissions are defined in the API (`ROLE_PERMISSIONS` in `routers/access.py`). Resource names include: `policies`, `users`, `tenants`, `analyses`, `exports`, `decisions`, `scorecards`, `cohorts`. Actions: `create`, `read`, `update`, `delete`.

## User Management

- **List users**: `GET /api/v1/access/users` — POLICY_ADMIN or UM_LEADER; scoped to current tenant. Response includes `auth_source` (oidc | local).
- **Get user**: `GET /api/v1/access/users/{id}` — Self, or POLICY_ADMIN/UM_LEADER for others in tenant.
- **Create user**: `POST /api/v1/access/users` — POLICY_ADMIN only. Body: `email`, `full_name?`, `role_names?`, `password?`. If `password` is set, user is local and can log in with email/password; otherwise local without password until set via Update.
- **Update user**: `PATCH /api/v1/access/users/{id}` — POLICY_ADMIN only. Body: `full_name?`, `is_active?`, `role_names?`, `password?`. `password` is only allowed for `auth_source=local` users.
- **Assign roles**: `POST /api/v1/access/users/{id}/roles` — POLICY_ADMIN only; body: `{ "user_id", "role_names" }`.

Roles are stored in the `roles` table (seeded at startup) and assigned via `user_roles` (user_id, role name). The demo user is created with POLICY_ADMIN and UM_LEADER.

## Local login (email/password)

- **POST /api/v1/auth/login** — Body: `{ "email": "...", "password": "..." }`. Returns `{ "access_token", "token_type": "bearer", "user_id", "email", "roles" }`. Use `access_token` in the `Authorization: Bearer <token>` header for subsequent requests.
- Only users with `auth_source=local` and a set `password_hash` can use this endpoint. OIDC users receive a 400 telling them to use SSO.

## Endpoint Protection

- Most read endpoints use `get_demo_current_user()` (no DB) for fast demo behavior.
- Write/sensitive endpoints use `verify_token` and/or `require_role("POLICY_ADMIN", ...)` and hit the database when needed.
- **verify_token** accepts: (1) our own JWT (issued after local login), (2) OIDC tokens (Azure AD, etc.), (3) mock/dev tokens in dev mode.
- Permission check: `GET /api/v1/access/check-permission?resource=...&action=...` — returns `has_permission` and `user_roles`.

## Enabling Azure AD (Active Directory)

1. Set environment variables (e.g. `OIDC_ISSUER` to your Azure AD issuer URL, `OIDC_CLIENT_ID` if needed).
2. Configure the frontend to use your IdP (e.g. MSAL) and send the Bearer token to the API.
3. The API validates the token and creates or links the user (`auth_source=oidc`). Assign roles via User Management.

See deployment docs for Azure App Service Authentication (Easy Auth) or OIDC configuration.

## Enabling local (regular) users

1. In Admin → User Management, create a user with email and password (and roles).
2. They sign in via `POST /auth/login` with email/password and use the returned JWT as Bearer for all API calls.
3. Frontend can show a “Sign in with email” form that calls `/auth/login` and stores the token.
