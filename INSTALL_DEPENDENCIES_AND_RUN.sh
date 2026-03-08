#!/bin/bash
# Install dependencies and run data generation

set -e

echo "🔧 Installing Dependencies"
echo "=========================="

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ Activated virtual environment"
else
    echo "⚠️  Virtual environment not found, using system Python"
fi

# Install pandas and polars
echo "📦 Installing pandas..."
pip install pandas || {
    echo "❌ Failed to install pandas. Please run manually:"
    echo "   pip install pandas polars"
    exit 1
}

echo "📦 Installing polars..."
pip install polars || {
    echo "⚠️  Failed to install polars (optional, continuing anyway)"
}

echo ""
echo "✅ Dependencies installed!"
echo ""
echo "🚀 Running data generation..."
echo ""

# Run the generation script
./GENERATE_DATA_FROM_LAST_DATE.sh
