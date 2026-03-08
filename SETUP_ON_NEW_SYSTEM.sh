#!/bin/bash
# Setup project on new Mac system

set -e

echo "🚀 Setting Up Project on New System"
echo "===================================="
echo ""

# Check if we're in the project directory
if [ ! -f "START_API_NOW.sh" ]; then
    echo "❌ Error: Must run from project root directory"
    echo "   Current directory: $(pwd)"
    exit 1
fi

echo "📁 Project directory: $(pwd)"
echo ""

# Step 1: Check Python
echo "1️⃣  Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✅ $PYTHON_VERSION"
else
    echo "   ❌ Python 3 not found!"
    echo "   Install with: brew install python@3.11"
    exit 1
fi

# Step 2: Create virtual environment
echo ""
echo "2️⃣  Setting up virtual environment..."
if [ -d ".venv" ]; then
    echo "   ⚠️  Virtual environment already exists"
    read -p "   Remove and recreate? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .venv
        python3 -m venv .venv
        echo "   ✅ Created new virtual environment"
    else
        echo "   ✅ Using existing virtual environment"
    fi
else
    python3 -m venv .venv
    echo "   ✅ Created virtual environment"
fi

# Step 3: Activate and install dependencies
echo ""
echo "3️⃣  Installing Python dependencies..."
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip --quiet

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "   📦 Installing from requirements.txt..."
    pip install -r requirements.txt
    echo "   ✅ Dependencies installed"
else
    echo "   ⚠️  requirements.txt not found"
    echo "   📦 Installing core dependencies..."
    pip install fastapi uvicorn pydantic pydantic-settings pandas polars sqlalchemy
    echo "   ✅ Core dependencies installed"
fi

# Step 4: Install frontend dependencies (if exists)
if [ -d "apps/web" ]; then
    echo ""
    echo "4️⃣  Installing frontend dependencies..."
    if command -v npm &> /dev/null; then
        cd apps/web
        npm install
        cd ../..
        echo "   ✅ Frontend dependencies installed"
    else
        echo "   ⚠️  npm not found, skipping frontend setup"
        echo "   Install with: brew install node"
    fi
fi

# Step 5: Make scripts executable
echo ""
echo "5️⃣  Making scripts executable..."
find . -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null || true
echo "   ✅ Scripts are executable"

# Step 6: Verify data files
echo ""
echo "6️⃣  Verifying data files..."
if [ -d "data/pipelines" ]; then
    PIPELINE_COUNT=$(find data/pipelines -name "pipeline-*.json" -type f | wc -l | tr -d ' ')
    echo "   ✅ Found $PIPELINE_COUNT pipeline files"
else
    echo "   ⚠️  data/pipelines directory not found"
fi

if [ -d "data" ]; then
    echo "   ✅ Data directory exists"
else
    echo "   ⚠️  Data directory not found - creating..."
    mkdir -p data
fi

# Step 7: Test imports
echo ""
echo "7️⃣  Testing Python imports..."
export PYTHONPATH="$(pwd)/apps/api/src:$(pwd)/packages/common/src:$PYTHONPATH"
python3 -c "import uepi_api; print('   ✅ uepi_api module imports successfully')" || {
    echo "   ❌ Failed to import uepi_api"
    echo "   Check PYTHONPATH and dependencies"
}

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Start API server: ./START_API_NOW.sh"
echo "   2. Verify pipelines: ./FIX_AND_VERIFY_PIPELINES.sh"
echo "   3. Start frontend (if applicable): cd apps/web && npm run dev"
echo ""
