#!/bin/bash
# Update pipeline tags to make them visible in the frontend
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR" || exit 1

# Set environment
export PYTHONPATH="${SCRIPT_DIR}/apps/api/src:${SCRIPT_DIR}/packages/common/src:${PYTHONPATH}"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"

# Activate venv if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "🔧 Updating pipeline tags..."
echo ""

# Try direct SQL first (most reliable)
echo "Trying direct SQL update..."
python3 apps/api/scripts/fix_pipeline_tags_direct_sql.py

# If that doesn't work, fall back to ORM update
if [ $? -ne 0 ]; then
    echo ""
    echo "Falling back to ORM update..."
    python3 apps/api/scripts/fix_pipeline_tags_simple.py
fi

echo ""
echo "✅ Done! Refresh your web app to see pipelines."

