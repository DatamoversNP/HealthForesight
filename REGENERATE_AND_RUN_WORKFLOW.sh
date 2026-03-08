#!/bin/bash
# Comprehensive workflow: Regenerate data, load, baseline, predicted impact, post-policy data, observation
# This script ensures all data has proper dates and supports the full product use case

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"
DATA_DIR="$PROJECT_ROOT/data"
TARGET_DATA_DIR="$PROJECT_ROOT/apps/data/target_data_model"
TENANT_ID="00000000-0000-0000-0000-000000000001"

echo "═══════════════════════════════════════════════════════════════"
echo "🔄 Complete Data Regeneration & Workflow Execution"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Step 1: Clean old data
echo "📋 Step 1: Cleaning old data..."
rm -rf "$DATA_DIR/synthetic"
rm -rf "$TARGET_DATA_DIR/$TENANT_ID"
mkdir -p "$DATA_DIR/synthetic"
mkdir -p "$TARGET_DATA_DIR/$TENANT_ID/CLAIMS_LINES"
echo "✅ Cleaned"

# Step 2: Generate synthetic data (24 months: Jan 2024 - Dec 2025)
echo ""
echo "📊 Step 2: Generating synthetic data (24 months)..."
cd "$PROJECT_ROOT"
python3 -m scripts.synth.generate \
    --out "$DATA_DIR/synthetic" \
    --members 50000 \
    --providers 5000 \
    --months 24 \
    --seed 42

# Step 3: Copy claims data to target_data_model with proper column name
echo ""
echo "📋 Step 3: Loading claims data to target_data_model..."
# Combine all monthly claims files into one
cd "$DATA_DIR/synthetic"
if ls claims_lines_*.csv 1> /dev/null 2>&1; then
    # Combine all CSV files (skip header after first)
    head -1 claims_lines_*.csv | head -1 > "$TARGET_DATA_DIR/$TENANT_ID/CLAIMS_LINES/claims_lines.csv"
    tail -n +2 claims_lines_*.csv >> "$TARGET_DATA_DIR/$TENANT_ID/CLAIMS_LINES/claims_lines.csv"
    
    # Verify the file has dates
    echo "   Verifying claims data..."
    LINE_COUNT=$(wc -l < "$TARGET_DATA_DIR/$TENANT_ID/CLAIMS_LINES/claims_lines.csv" | tr -d ' ')
    echo "   ✅ Created claims file with $LINE_COUNT lines"
    
    # Verify service_from_date column exists and has data
    if grep -q "service_from_date" "$TARGET_DATA_DIR/$TENANT_ID/CLAIMS_LINES/claims_lines.csv"; then
        DATE_COUNT=$(tail -n +2 "$TARGET_DATA_DIR/$TENANT_ID/CLAIMS_LINES/claims_lines.csv" | cut -d',' -f5 | grep -v '^$' | wc -l | tr -d ' ')
        echo "   ✅ Found $DATE_COUNT rows with service_from_date values"
    else
        echo "   ⚠️  Warning: service_from_date column not found!"
    fi
else
    echo "   ⚠️  No claims_lines CSV files found to combine"
fi

# Step 4: Run baseline analysis (via API)
echo ""
echo "📊 Step 4: Running baseline analysis..."
echo "   (This will be triggered via API - you may need to run this manually)"
echo "   POST http://localhost:8000/api/v1/analyses/baseline"
echo "   Body: {\"n_clusters\": 5}"

# Step 5: Generate predicted impact for all policies
echo ""
echo "🎯 Step 5: Generating predicted impact for policies..."
echo "   (This will be triggered via API - you may need to run this manually)"
echo "   POST http://localhost:8000/api/v1/policies/{policy_id}/predicted-impact"
echo "   OR: POST http://localhost:8000/api/v1/policies/predicted-impact/all"

# Step 6: Generate post-policy data (last 5 days)
echo ""
echo "📅 Step 6: Generating post-policy synthetic data (last 5 days)..."
cd "$PROJECT_ROOT"
python3 scripts/generate_post_policy_synthetic_data.py \
    --start-date "2025-12-27" \
    --end-date "2025-12-31" \
    --tenant-id "$TENANT_ID" \
    --output-dir "$TARGET_DATA_DIR/$TENANT_ID/CLAIMS_LINES" \
    --append

# Step 7: Run observation analysis
echo ""
echo "🔍 Step 7: Running observation analysis..."
echo "   (This will be triggered via API - you may need to run this manually)"
echo "   POST http://localhost:8000/api/v1/observations/from-analysis/{analysis_id}"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Workflow Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Next steps (manual via UI or API):"
echo "  1. Run baseline analysis in UI"
echo "  2. Generate predicted impact for policies"
echo "  3. Run observation analysis on post-policy data"
echo ""
echo "Data locations:"
echo "  - Claims: $TARGET_DATA_DIR/$TENANT_ID/CLAIMS_LINES/claims_lines.csv"
echo "  - Synthetic data: $DATA_DIR/synthetic/"
echo ""
