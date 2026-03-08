# System Initialization Guide

## Overview

This guide explains the comprehensive system initialization that sets up the entire UEPI system end-to-end, including database setup, policy seeding, pipeline creation, source data directories, and baseline analysis.

## Architecture Decisions

### Target Data Model Storage

The **target data model** (processed healthcare data) is stored in **blob storage** (local filesystem for development, Azure Blob Storage for production). This decision was made because:

1. **Large Dataset Size**: Healthcare claims and enrollment data can be very large (GBs to TBs)
2. **Performance**: Blob storage is optimized for large file reads/writes
3. **Cost Efficiency**: Blob storage is more cost-effective than database storage for large datasets
4. **Scalability**: Blob storage scales better for time-series data

**Location:**
- Development: `data/target_data_model/{tenant_id}/`
- Production: Azure Blob Storage container

**Database Role:**
- Stores metadata about the data (ingestions, analyses, baselines, etc.)
- Stores configuration (policies, pipelines, schedules)
- Stores business logic entities (decisions, observations, etc.)

### Source Data Drop Location

Source data files are organized in a structured directory:

```
data/source_data/
  {tenant_id}/
    historical/          # One-time historical data loads
    daily/               # Daily incremental loads
      YYYY-MM-DD/        # Date-based subdirectories
```

This structure supports:
- **Historical Loads**: One-time bulk data imports
- **Daily Loads**: Incremental daily data processing
- **Date-based Organization**: Easy tracking and processing of daily files

## Initialization Script

### Location
`apps/api/scripts/initialize_system.py`

### What It Does

1. **Database Setup**
   - Ensures demo tenant and user exist
   - Creates all database tables
   - Verifies table creation

2. **Policy Seeding**
   - Loads predefined policies from `seed_policies.py`
   - Creates policies in database
   - Skips existing policies (idempotent)

3. **Pipeline Seeding**
   - Loads pipeline definitions from `data/pipelines/*.json`
   - Creates pipelines in database
   - Supports all dataset types (CLAIMS_LINES, MEMBER_MASTER, etc.)

4. **Source Data Directories**
   - Creates `data/source_data/{tenant_id}/historical/`
   - Creates `data/source_data/{tenant_id}/daily/`
   - Creates README with usage instructions

5. **Baseline Analysis**
   - Checks if target data model exists
   - Verifies claims data is available
   - Provides instructions for running baseline

6. **System Verification**
   - Verifies database connection
   - Checks policies count
   - Checks pipelines count
   - Verifies source data directories
   - Verifies target data model

### Usage

```bash
# Activate virtual environment
source .venv/bin/activate

# Set environment variables
export DATABASE_URL="postgresql://postgres@localhost:5432/uepi_db"
export LOG_LEVEL="DEBUG"
export USE_FILE_STORAGE="false"

# Run initialization
python apps/api/scripts/initialize_system.py
```

## Startup Script

### Location
`start_system.sh`

### What It Does

1. **Environment Setup**
   - Activates virtual environment
   - Sets default DATABASE_URL if not provided
   - Sets LOG_LEVEL to DEBUG
   - Sets USE_FILE_STORAGE to false

2. **System Initialization**
   - Runs `initialize_system.py`
   - Handles initialization errors gracefully

3. **API Server Startup**
   - Checks if API server is already running
   - Starts API server on port 8000
   - Waits for server to be ready
   - Provides health check URLs

### Usage

```bash
# Make executable (first time only)
chmod +x start_system.sh

# Run startup script
./start_system.sh
```

## Debug Logging

### Configuration

Debug logging is enabled by default via the `LOG_LEVEL` environment variable:

```bash
export LOG_LEVEL="DEBUG"
```

### Log Files

Logs are written to multiple locations:

1. **Console**: Real-time output with detailed formatting
2. **logs/api.log**: All application logs (JSON format)
3. **logs/errors.log**: Error logs only (JSON format)
4. **logs/actions.log**: User action logs (JSON format)
5. **logs/requests.log**: HTTP request logs (JSON format)
6. **system_init.log**: System initialization logs
7. **api-server.log**: API server startup logs

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General informational messages
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

## Complete Workflow

### 1. Initial Setup (First Time)

```bash
# 1. Set up database
export DATABASE_URL="postgresql://postgres@localhost:5432/uepi_db"

# 2. Run initialization
./start_system.sh
```

### 2. Generate Target Data Model (If Needed)

If target data model doesn't exist:

```bash
# Generate synthetic data and load to target data model
python scripts/regenerate_complete_workflow.py
```

### 3. Run Baseline Analysis

After target data model is ready:

**Option A: Via UI**
1. Open http://localhost:3050/baseline-analysis
2. Click "Run Analysis"
3. Wait for completion

**Option B: Via API**
```bash
curl -X POST http://localhost:8000/api/v1/analyses/baseline \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev-token-123" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2025-12-31",
    "n_clusters": 5
  }'
```

### 4. Load Source Data

**Historical Load:**
```bash
# Place files in historical directory
cp source_data.csv data/source_data/00000000-0000-0000-0000-000000000001/historical/

# Run pipeline ingestion via API or UI
```

**Daily Load:**
```bash
# Create date directory
mkdir -p data/source_data/00000000-0000-0000-0000-000000000001/daily/2026-01-15

# Place daily files
cp daily_data.csv data/source_data/00000000-0000-0000-0000-000000000001/daily/2026-01-15/

# Run pipeline ingestion via API or UI
```

## Verification Checklist

After initialization, verify:

- [ ] Database tables created (check logs)
- [ ] Policies created (check API: GET /api/v1/policies)
- [ ] Pipelines created (check API: GET /api/v1/pipelines)
- [ ] Source data directories exist
- [ ] Target data model exists (or instructions provided)
- [ ] API server running (http://localhost:8000/health)
- [ ] Debug logging enabled (check logs/api.log)

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
psql -U postgres -d uepi_db -c "SELECT 1"

# Verify DATABASE_URL
echo $DATABASE_URL
```

### Missing Target Data Model

```bash
# Generate target data model
python scripts/regenerate_complete_workflow.py
```

### API Server Not Starting

```bash
# Check logs
tail -f api-server.log

# Check port availability
lsof -i :8000

# Kill existing server
lsof -ti:8000 | xargs kill
```

### Policies Not Loading

```bash
# Check seed_policies.py exists
ls -la apps/api/scripts/seed_policies.py

# Check database
psql -U postgres -d uepi_db -c "SELECT COUNT(*) FROM policies;"
```

## Next Steps

After successful initialization:

1. **Start Web UI** (if needed):
   ```bash
   cd apps/web && npm run dev
   ```

2. **Access Application**:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Web UI: http://localhost:3050

3. **Run Baseline Analysis** (if target data model exists)

4. **Load Source Data** (historical or daily)

5. **Create Policies** (if not using predefined)

6. **Run Pipelines** to process source data

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    Source Data Layer                        │
│  data/source_data/{tenant_id}/                             │
│    ├── historical/  (one-time loads)                      │
│    └── daily/YYYY-MM-DD/  (daily incremental)             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Pipeline Layer                            │
│  Database: pipelines table                                  │
│  - Field mappings                                            │
│  - Transformations                                           │
│  - Deduplication                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Target Data Model (Blob Storage)                │
│  data/target_data_model/{tenant_id}/                        │
│    ├── CLAIMS_LINES/                                        │
│    ├── MEMBER_MASTER/                                       │
│    ├── PROVIDER_MASTER/                                     │
│    └── ...                                                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Database (Metadata & Configuration)            │
│  - Policies                                                  │
│  - Pipelines                                                 │
│  - Baselines                                                 │
│  - Analyses                                                  │
│  - Observations                                              │
│  - Decisions                                                 │
└─────────────────────────────────────────────────────────────┘
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres@localhost:5432/uepi_db` | PostgreSQL connection string |
| `LOG_LEVEL` | `DEBUG` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `USE_FILE_STORAGE` | `false` | Use file storage (legacy, should be false) |

## Support

For issues or questions:
1. Check logs: `tail -f logs/api.log`
2. Check initialization log: `tail -f system_init.log`
3. Verify database: `psql -U postgres -d uepi_db`
4. Check API health: `curl http://localhost:8000/health`

