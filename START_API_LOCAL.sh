#!/bin/bash
# Start API locally for testing

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting API Locally${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if we're in the right directory
if [ ! -d "apps/api" ]; then
    echo -e "${RED}❌ Error: apps/api directory not found${NC}"
    echo "   Please run this script from the project root"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

# Set environment variables
export PYTHONPATH="${PWD}/apps/api/src:${PWD}/packages/common/src:$PYTHONPATH"

# Set STORAGE_PATH to absolute path of data directory
DATA_DIR="${PWD}/data"
if [ ! -d "$DATA_DIR" ]; then
    echo -e "${RED}❌ Data directory not found: $DATA_DIR${NC}"
    exit 1
fi
export STORAGE_PATH="$DATA_DIR"
echo -e "${GREEN}✅ STORAGE_PATH set to: $STORAGE_PATH${NC}"

echo -e "${BLUE}Configuration:${NC}"
echo "   PYTHONPATH: $PYTHONPATH"
echo "   STORAGE_PATH: $STORAGE_PATH"
echo ""

# Check if dependencies are installed
echo -e "${BLUE}Checking dependencies...${NC}"
cd apps/api

if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv .venv
    source .venv/bin/activate
    echo -e "${BLUE}Installing dependencies...${NC}"
    pip install -q -r requirements.txt 2>/dev/null || pip install -q fastapi uvicorn pydantic
else
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        source venv/bin/activate
    fi
fi

echo -e "${GREEN}✅ Dependencies ready${NC}"
echo ""

# Start the API
echo -e "${BLUE}Starting API server...${NC}"
echo -e "${GREEN}API will be available at: http://localhost:8000${NC}"
echo -e "${GREEN}API docs at: http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

cd ../..
python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload
