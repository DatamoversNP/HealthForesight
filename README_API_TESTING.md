# API Testing and Deployment Guide

## Quick Start

### 1. Test API Locally

**Start the API:**
```bash
./start_api_local.sh
```

The API will start on `http://localhost:8000`

**In another terminal, test the API:**
```bash
./test_api_local.sh
```

### 2. Test Specific Endpoints

**Test workspace endpoint:**
```bash
curl http://localhost:8000/api/v1/policies/ST_BIOLOGIC_006/workspace | jq
```

**Test policy list:**
```bash
curl http://localhost:8000/api/v1/policies | jq
```

**Test predicted impact:**
```bash
curl http://localhost:8000/api/v1/policies/ST_BIOLOGIC_006/predicted-impact | jq
```

### 3. Deploy to Azure

Once local testing passes:
```bash
./START_PRODUCTION_BUILD.sh
```

## What the Tests Check

### `test_api_local.sh`
- ✅ API server is running
- ✅ Workspace endpoint returns data
- ✅ Assumptions, guardrails, versions are present
- ✅ Policy list endpoint works
- ✅ Predicted impact endpoint works

### Expected Results

For policy `ST_BIOLOGIC_006`:
- **Assumptions**: 3 items
- **Guardrails**: 3 items  
- **Versions**: 1 item
- **Changelog**: 0 items (OK if empty)

## Troubleshooting

### API won't start
1. Check Python 3 is installed: `python3 --version`
2. Install dependencies: `cd apps/api && pip install -r requirements.txt`
3. Check STORAGE_PATH points to data directory

### API returns empty data
1. Verify policy files exist: `ls -la data/policy_*.json`
2. Check policy file has metadata: `cat data/policy_ST_BIOLOGIC_006.json | jq .metadata`
3. Verify assumptions/guardrails in metadata

### API returns 404
1. Check policy ID is correct
2. Verify policy file exists for that ID
3. Check STORAGE_PATH environment variable

## Manual Testing

### Test workspace data retrieval:
```python
import json
from pathlib import Path

# Load policy
with open('data/policy_ST_BIOLOGIC_006.json', 'r') as f:
    policy = json.load(f)

# Check metadata
metadata = policy.get('metadata', {})
print(f"Assumptions: {len(metadata.get('assumptions', []))}")
print(f"Guardrails: {len(metadata.get('guardrails', []))}")
print(f"Versions: {len(metadata.get('versions', []))}")
```

## Deployment Checklist

Before deploying:
- [ ] API starts locally without errors
- [ ] `test_api_local.sh` passes all checks
- [ ] Workspace endpoint returns data
- [ ] Policy files have embedded metadata
- [ ] No console errors in browser

After deployment:
- [ ] Check Azure logs for errors
- [ ] Verify STORAGE_PATH is set correctly
- [ ] Test workspace endpoint on Azure
- [ ] Check frontend loads data

