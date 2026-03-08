#!/bin/bash
# Run QA Tests - Comprehensive role-based testing

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
cd "$PROJECT_ROOT"

echo "═══════════════════════════════════════════════════════════════"
echo "QA Testing Framework - Role-Based Testing"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Step 1: Create QA test users
echo "📝 Step 1: Creating QA test users..."
cd "$PROJECT_ROOT/apps/api"
export PYTHONPATH="$PROJECT_ROOT/apps/api/src:$PROJECT_ROOT/packages/common/src:$PYTHONPATH"
python3 scripts/create_qa_test_users.py

echo ""
echo "✅ QA test users created"
echo ""

# Step 2: Run QA tests
echo "🧪 Step 2: Running QA tests..."
echo ""
python3 scripts/qa_testing_framework.py

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ QA Testing Complete"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📊 Check the QA report in: data/qa_test_results/"
echo ""

