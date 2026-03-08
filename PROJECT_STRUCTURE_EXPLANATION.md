# Project Structure Explanation

## Overview

This is a **microservices architecture** with separate services for API, Worker, and Web frontend.

## Directory Structure

```
Utilization Elastisity and Policy Impact Solution/
├── apps/                          # Main application services
│   ├── api/                       # FastAPI backend service (Python)
│   │   ├── src/uepi_api/         # API source code
│   │   │   ├── main.py           # FastAPI app entry point
│   │   │   ├── routers/          # API endpoints (policies, analyses, etc.)
│   │   │   ├── storage/          # File-based storage adapters
│   │   │   └── models/           # Database models
│   │   └── Dockerfile            # Docker image for API
│   │
│   ├── worker/                   # Background job processor (Python/Celery)
│   │   └── src/uepi_worker/     # Worker source code
│   │
│   └── web/                      # React frontend (TypeScript)
│       ├── src/                  # React source code
│       │   ├── pages/           # Page components
│       │   ├── components/      # Reusable components
│       │   └── lib/             # Utilities (API client, etc.)
│       └── package.json         # Node.js dependencies
│
├── packages/
│   └── common/                   # Shared Python code used by API and Worker
│       └── src/uepi_common/     # Common models, config, utilities
│
├── scripts/                      # Utility scripts
│   └── dev/                     # Development scripts (seed data, etc.)
│
├── data/                         # Data files (JSON, etc.)
│   └── policies_*.json          # Policy data files
│
├── docker-compose.yml           # Docker Compose config (for local dev)
├── Makefile                     # Common build/run commands
└── README.md                    # Project documentation
```

## How Services Work Together

### 1. **API Service** (`apps/api/`)
- **Technology**: Python + FastAPI
- **Purpose**: REST API that handles HTTP requests from the frontend
- **Runs on**: Port 8000 (http://localhost:8000)
- **Entry point**: `apps/api/src/uepi_api/main.py`
- **Key features**:
  - Policy management endpoints
  - Analysis creation endpoints
  - Authentication
  - File-based storage (when database not available)

### 2. **Worker Service** (`apps/worker/`)
- **Technology**: Python + Celery
- **Purpose**: Background job processing (long-running analyses)
- **Runs on**: Redis queue
- **Key features**:
  - Impact analysis calculations
  - Data processing
  - Async tasks

### 3. **Web Frontend** (`apps/web/`)
- **Technology**: React + TypeScript + Material-UI
- **Purpose**: User interface
- **Runs on**: Port 3050 (http://localhost:3050)
- **Entry point**: `apps/web/src/main.tsx`
- **Key features**:
  - Policy Catalog page
  - Analysis workspace
  - Dashboard
  - UI for all features

## How to Run Services

### Development Mode (Current Setup)

The services can run in different ways:

1. **Directly** (what you're likely using):
   - API: `cd apps/api && uvicorn uepi_api.main:app --reload --port 8000`
   - Web: `cd apps/web && npm run dev`
   - Worker: `cd apps/worker && celery -A uepi_worker worker`

2. **Via Docker Compose** (if Docker is running):
   - `make dev` or `docker-compose up`

3. **Via Makefile**:
   - `make dev` - starts all services

## File Storage vs Database

The system supports **two storage modes**:

1. **Database mode** (PostgreSQL): Full SQLAlchemy models
2. **File storage mode** (JSON files): When database not available

Currently, you're using **file storage mode**, which is why:
- Policies are stored in JSON files (`data/policies_*.json`)
- The API looks for files in `/tmp/policies_*.json`
- No database connection required

## Current Issue: API Server Restart

The API server needs to be restarted because we:
1. Added a new `get_policy()` method to the storage adapter
2. Made changes to `apps/api/src/uepi_api/storage/policy_storage.py`

To restart the API:
1. Find the terminal/process running the API
2. Stop it (Ctrl+C or kill process)
3. Restart: `cd apps/api && uvicorn uepi_api.main:app --reload --port 8000`

## Code Flow: Predicted Impact Feature

1. **Frontend** (`apps/web/src/pages/PolicyCatalogPage.tsx`):
   - User clicks Psychology icon (🧠)
   - Calls API: `GET /api/v1/policies/{id}/predicted-impact`

2. **API** (`apps/api/src/uepi_api/routers/policies.py`):
   - Endpoint: `get_policy_predicted_impact()`
   - Calls storage: `storage.get_policy(tenant_id, policy_id)`

3. **Storage** (`apps/api/src/uepi_api/storage/policy_storage.py`):
   - Reads from file: `/tmp/policies_{tenant_id}.json`
   - Returns policy data with `predicted_impact` field

4. **Response**: JSON with predicted impact metrics

## Why Files Are in Different Locations

- **`data/policies_*.json`**: Your source of truth (created by scripts)
- **`/tmp/policies_*.json`**: Where API reads from (copied from data/)
- This is a temporary workaround for file-based storage
