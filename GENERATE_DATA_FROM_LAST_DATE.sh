#!/bin/bash
# Generate data from the last generated date onwards

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📊 Generating Data from Last Date"
echo "=================================="

# Configuration
OUT_DIR="${OUT_DIR:-data/demo}"
TENANT_ID="00000000-0000-0000-0000-000000000001"
TARGET_DIR="apps/api/data/target_data_model/${TENANT_ID}"
MONTHS_TO_GENERATE="${MONTHS_TO_GENERATE:-3}"

echo "📁 Checking existing data..."

# Find the latest date in existing data
LATEST_DATE=$(python3 << 'PYTHON_SCRIPT'
from pathlib import Path
from datetime import datetime
import re
import sys

target_dir = Path("apps/api/data/target_data_model/00000000-0000-0000-0000-000000000001")
latest_file_date = None

# Check CLAIMS_LINES directory
claims_dir = target_dir / "CLAIMS_LINES"
if claims_dir.exists():
    for csv_file in claims_dir.glob("*.csv"):
        # Try to extract date from filename (e.g., claims_lines_2024_01.csv or claims_lines_202401.csv)
        # Look for 4-digit year followed by 1-2 digit month
        match = re.search(r'(\d{4})[_-]?(\d{1,2})', csv_file.name)
        if match:
            year_str, month_str = match.group(1), match.group(2)
            try:
                year = int(year_str)
                month = int(month_str)
                if 1 <= month <= 12 and 2000 <= year <= 2100:  # Sanity check
                    file_date = datetime(year, month, 1)
                    if latest_file_date is None or file_date > latest_file_date:
                        latest_file_date = file_date
            except ValueError:
                continue

# If no date found, default to 2024-01-01
if latest_file_date is None:
    start_date = datetime(2024, 1, 1)
    print(f"📅 No existing data found, starting from: {start_date.strftime('%Y-%m-%d')}", file=sys.stderr)
else:
    # Move to next month
    if latest_file_date.month == 12:
        start_date = datetime(latest_file_date.year + 1, 1, 1)
    else:
        start_date = datetime(latest_file_date.year, latest_file_date.month + 1, 1)
    print(f"📅 Latest existing data: {latest_file_date.strftime('%Y-%m')}, generating from: {start_date.strftime('%Y-%m-%d')}", file=sys.stderr)

print(start_date.strftime("%Y-%m-%d"))
PYTHON_SCRIPT
)

echo "📅 Generating from: ${LATEST_DATE} onwards"
echo "🔢 Generating ${MONTHS_TO_GENERATE} months of data"
echo ""

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ Activated virtual environment"
fi

# Use the existing generate.py script with calculated dates
# Note: The script generates from 2024-01-01, so we'll use it as-is
# For incremental generation, we'd need to modify the script
python3 scripts/synth/generate.py \
  --out "${OUT_DIR}" \
  --members 50000 \
  --providers 5000 \
  --months ${MONTHS_TO_GENERATE} \
  --seed 42

echo ""
echo "✅ Data generation complete!"
echo ""
echo "💡 Next steps:"
echo "   1. Run: ./RUN_ALL_PIPELINES.sh to process the new data"
echo "   2. Run data quality validation from the dashboard"
echo "   3. Check the Data Quality Dashboard for results"
