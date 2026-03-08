#!/bin/bash
# Convenience script to run observation analysis

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "🔍 Running Observation Analysis"
echo ""

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Virtual environment not found at $VENV_DIR"
    echo "   Run ./start-both-servers.sh first to set up the environment"
    exit 1
fi

# Run the script
cd "$SCRIPT_DIR"
python scripts/load_and_run_observation_analysis.py "$@"
