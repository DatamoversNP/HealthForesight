#!/bin/bash

# Simple script to install Python dependencies for the API
# This is needed even for file-based storage - the API code needs these packages

echo "🔧 Installing Python dependencies for API server..."
echo "This is needed even with file-based storage (the API code needs these packages)"
echo ""

# Check Python version
PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi

echo "✅ Python found: $($PYTHON_CMD --version)"
echo ""

# Install minimal dependencies needed for file-based API
echo "📦 Installing packages (this may take a minute)..."
$PYTHON_CMD -m pip install --user --quiet fastapi uvicorn[standard] pydantic pydantic-settings python-jose httpx boto3 2>&1 | grep -v "Requirement already satisfied" | grep -E "(Installing|Successfully|ERROR)" || echo "✅ Installation complete"

echo ""
echo "✅ Dependencies installed!"
echo ""
echo "Now you can start the API with:"
echo "  ./restart-api.sh"
echo ""
