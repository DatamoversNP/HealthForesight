#!/bin/bash
# Generate All Synthetic Data - Complete Workflow
# This script generates all synthetic data needed for a fully functional system

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Generating All Synthetic Data"
echo "=========================================="
echo ""

# Step 1: Generate policies with lifecycle data
echo "Step 1: Generating policies with lifecycle data..."
python3 scripts/generate_complete_payer_synthetic_data.py --tenant-id 00000000-0000-0000-0000-000000000001
echo ""

# Step 2: Generate observations from synthetic data
echo "Step 2: Generating observations from synthetic data..."
python3 scripts/generate_observations_from_synthetic_data.py --tenant-id 00000000-0000-0000-0000-000000000001 --days 30
echo ""

# Step 3: Generate comprehensive source data (if needed)
if [ ! -d "data/source_data/synthetic" ] || [ -z "$(ls -A data/source_data/synthetic 2>/dev/null)" ]; then
    echo "Step 3: Generating comprehensive source data..."
    python3 scripts/generate_all_comprehensive_synthetic.py --count 100 --months 36
    echo ""
fi

echo "=========================================="
echo "✅ All Synthetic Data Generation Complete!"
echo "=========================================="
echo ""
echo "Generated data includes:"
echo "  - Policies with full lifecycle management"
echo "  - Policy versions, assumptions, guardrails, changelogs"
echo "  - Predicted impacts"
echo "  - Observations from synthetic claims"
echo "  - Source data (members, providers, claims)"
echo ""
echo "All data is stored in files - no hardcoded values in code."
echo ""


