#!/bin/bash
# Complete Product Flow: Generate Data, Ingest, Test
# This script runs the complete end-to-end product flow

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

TENANT_ID="00000000-0000-0000-0000-000000000001"

echo "=========================================="
echo "COMPLETE PRODUCT FLOW: Generate & Test"
echo "=========================================="
echo ""

# Step 1: Generate and ingest all data
echo "Step 1: Generating and ingesting all data..."
python3 scripts/run_complete_product_flow.py \
    --tenant-id "$TENANT_ID" \
    --member-count 100 \
    --months 36 \
    --observation-days 30

if [ $? -ne 0 ]; then
    echo "❌ Data generation/ingestion failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ DATA GENERATION AND INGESTION COMPLETE"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Start API server:"
echo "     cd apps/api && python -m uvicorn uepi_api.main:app --reload"
echo ""
echo "  2. Start frontend:"
echo "     cd apps/web && npm run dev"
echo ""
echo "  3. Access the application:"
echo "     http://localhost:3050"
echo ""
echo "  4. Verify dashboards show real data from:"
echo "     - Policies with lifecycle data"
echo "     - Observations"
echo "     - Predicted impacts"
echo "     - Target data model (claims, enrollment, providers)"
echo ""
echo "All data is stored in files - no hardcoded values in code."
echo ""


