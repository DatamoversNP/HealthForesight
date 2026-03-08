# How to Run QA Tests

## Quick Start

### Step 1: Create QA Test Users

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729

# Set Python path
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"

# Create test users
cd apps/api
python3 scripts/create_qa_test_users.py
```

### Step 2: Start API Server

```bash
# In Terminal 1
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"
cd apps/api/src
python3 -m uvicorn uepi_api.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Start Frontend

```bash
# In Terminal 2
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729/apps/web
npm run dev
```

### Step 4: Run QA Tests

**Option A: Backend API Tests (Command Line)**

```bash
# In Terminal 3
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"
cd apps/api
python3 scripts/qa_testing_framework.py
```

**Option B: Frontend UI Tests (Browser)**

1. Open browser: `http://localhost:3050/qa-testing`
2. Click "Run All QA Tests"
3. Review results

**Option C: Browser Automation (Playwright)**

```bash
cd apps/web
npm install playwright  # If not installed
npx playwright install chromium
node scripts/qa-browser-tests.js
```

## QA Test Users

After creating test users, you can log in with:

- **ROLE_PAYER_CMO**: qa.payer.cmo@test.com
- **ROLE_PROVIDER_CFO**: qa.provider.cfo@test.com
- **ROLE_PAYER_UM_LEAD**: qa.payer.um.lead@test.com
- **ROLE_PAYER_ACTUARY**: qa.payer.actuary@test.com
- **ROLE_PAYER_NETWORK_STRATEGY**: qa.payer.network.strategy@test.com
- **ROLE_PAYER_ANALYTICS**: qa.payer.analytics@test.com
- **ROLE_READ_ONLY_EXEC**: qa.readonly.exec@test.com

## Test Coverage

### Functional Tests
- Dashboard access
- Policy management (create/read/update)
- Analysis access
- Decision management
- Conversational AI access
- Permission enforcement

### Technical Tests
- API endpoint responses
- HTTP status codes
- Error handling
- Response formats

### Console Tests
- JavaScript errors
- Network errors
- React warnings
- Performance issues

## Review Results

### Backend Results
- Location: `data/qa_test_results/qa_report_TIMESTAMP.json`
- Contains: Test results, errors, warnings, pass rates

### Frontend Results
- Location: QA Testing page UI (`http://localhost:3050/qa-testing`)
- Contains: Visual test results, error details, pass rates

## Next Steps

1. Review test results
2. Document issues in `QA_CORRECTION_PLAN_TEMPLATE.md`
3. Prioritize fixes
4. Fix issues
5. Re-run tests to verify

