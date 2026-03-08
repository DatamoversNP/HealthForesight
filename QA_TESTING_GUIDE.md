# QA Testing Guide - Role-Based Testing Framework

## Overview

This comprehensive QA testing framework tests the platform from the perspective of different user roles to identify functional, technical, and console issues.

## QA Test Users

The following test users have been created:

1. **ROLE_PAYER_CMO** (qa.payer.cmo@test.com)
   - Roles: EXEC_VIEWER, STRATEGY
   - Tests: Executive dashboard, strategy views, read-only operations

2. **ROLE_PROVIDER_CFO** (qa.provider.cfo@test.com)
   - Roles: EXEC_VIEWER
   - Tests: Executive dashboard, financial views, read-only operations

3. **ROLE_PAYER_UM_LEAD** (qa.payer.um.lead@test.com)
   - Roles: UM_LEADER
   - Tests: Policy creation, UM workflows, decision management

4. **ROLE_PAYER_ACTUARY** (qa.payer.actuary@test.com)
   - Roles: ACTUARIAL
   - Tests: Analysis creation, baseline management, read-only policies

5. **ROLE_PAYER_NETWORK_STRATEGY** (qa.payer.network.strategy@test.com)
   - Roles: STRATEGY
   - Tests: Network strategy views, decision creation, read-only policies

6. **ROLE_PAYER_ANALYTICS** (qa.payer.analytics@test.com)
   - Roles: ACTUARIAL, STRATEGY
   - Tests: Analytics workflows, analysis creation, strategy views

7. **ROLE_READ_ONLY_EXEC** (qa.readonly.exec@test.com)
   - Roles: EXEC_VIEWER
   - Tests: Read-only executive access, dashboard views

## How to Run QA Tests

### Option 1: Backend API Tests (Command Line)

```bash
cd /Users/nilesh/Downloads/uepi-migration-20260123-151729
./apps/api/scripts/run_qa_tests.sh
```

This will:
1. Create QA test users
2. Run API endpoint tests for each role
3. Generate a comprehensive report

### Option 2: Frontend UI Tests (Browser)

1. Start the frontend: `cd apps/web && npm run dev`
2. Navigate to: `http://localhost:3050/qa-testing`
3. Click "Run All QA Tests"
4. Review results in the UI

### Option 3: Manual Testing

1. Use the QA test user emails to log in
2. Test workflows manually from each role's perspective
3. Document issues found

## Test Coverage

### Functional Tests

- **Dashboard Access**: Can each role access their dashboard?
- **Policy Management**: Can roles create/read/update policies as expected?
- **Analysis Access**: Can roles access analyses?
- **Decision Management**: Can roles create/manage decisions?
- **Conversational AI**: Can roles use conversational AI?
- **Permission Checks**: Are permissions correctly enforced?

### Technical Tests

- **API Endpoints**: Do all endpoints respond correctly?
- **Status Codes**: Are correct HTTP status codes returned?
- **Error Handling**: Are errors handled gracefully?
- **Response Format**: Are responses in correct format?

### Console Tests

- **JavaScript Errors**: Are there console errors?
- **Network Errors**: Are there failed API calls?
- **Warnings**: Are there React warnings?
- **Performance**: Are there performance issues?

## Test Results

Test results are saved to:
- **Backend**: `data/qa_test_results/qa_report_TIMESTAMP.json`
- **Frontend**: Displayed in the QA Testing page UI

## Issue Categories

### Critical Issues
- Application crashes
- Permission bypasses
- Data corruption
- Security vulnerabilities

### High Priority Issues
- Broken workflows
- Missing features for roles
- Incorrect data display
- Performance degradation

### Medium Priority Issues
- UI/UX inconsistencies
- Console warnings
- Minor permission issues
- Documentation gaps

### Low Priority Issues
- Cosmetic issues
- Minor UI glitches
- Non-critical warnings

## Correction Plan Template

For each issue found:

1. **Issue ID**: Unique identifier
2. **Role**: Which role encountered the issue
3. **Severity**: Critical/High/Medium/Low
4. **Description**: What went wrong
5. **Steps to Reproduce**: How to reproduce
6. **Expected Behavior**: What should happen
7. **Actual Behavior**: What actually happened
8. **Root Cause**: Why it happened
9. **Fix**: How to fix it
10. **Test**: How to verify the fix

## Next Steps

After running tests:

1. Review the QA report
2. Prioritize issues by severity
3. Create correction plan
4. Fix issues systematically
5. Re-run tests to verify fixes

