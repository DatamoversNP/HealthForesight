# Quick Start - Test & Deploy

## Step 1: Start API Locally
```bash
./start_api_local.sh
```
API will run on: http://localhost:8000

## Step 2: Test API (in another terminal)
```bash
./test_api_local.sh
```

Expected output:
- ✅ API is running
- ✅ Assumptions: 3
- ✅ Guardrails: 3
- ✅ Versions: 1

## Step 3: Deploy to Azure
```bash
./START_PRODUCTION_BUILD.sh
```

## Quick Manual Test
```bash
curl http://localhost:8000/api/v1/policies/ST_BIOLOGIC_006/workspace | python3 -m json.tool
```

## Troubleshooting

**API won't start?**
- Check Python: `python3 --version`
- Install deps: `cd apps/api && pip install -r requirements.txt`

**No data in response?**
- Check files: `ls -la data/policy_*.json`
- Verify metadata: `cat data/policy_ST_BIOLOGIC_006.json | grep -A 5 assumptions`
