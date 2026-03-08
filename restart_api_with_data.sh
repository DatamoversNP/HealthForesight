#!/bin/bash
# Restart API with correct STORAGE_PATH to find policy files

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔄 Restarting API with Correct Storage Path${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Get absolute path to data directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$PROJECT_ROOT/data"

if [ ! -d "$DATA_DIR" ]; then
    echo -e "${RED}❌ Data directory not found: $DATA_DIR${NC}"
    exit 1
fi

# Count policy files
POLICY_COUNT=$(find "$DATA_DIR" -maxdepth 1 -name "policy_*.json" -not -name "valid_policies.json" -not -name "canonical_policies.json" 2>/dev/null | wc -l | tr -d ' ')
echo -e "${GREEN}✅ Found $POLICY_COUNT policy files${NC}"
echo ""

# Kill existing API if running
echo -e "${BLUE}Stopping existing API...${NC}"
pkill -f "uvicorn.*uepi_api.main" 2>/dev/null || true
sleep 2

# Set environment and start
echo -e "${BLUE}Starting API with STORAGE_PATH=$DATA_DIR${NC}"
echo ""

export PYTHONPATH="$PROJECT_ROOT/apps/api/src:$PROJECT_ROOT/packages/common/src:$PYTHONPATH"
export STORAGE_PATH="$DATA_DIR"

cd "$PROJECT_ROOT"

echo -e "${GREEN}Environment:${NC}"
echo "   PYTHONPATH: $PYTHONPATH"
echo "   STORAGE_PATH: $STORAGE_PATH"
echo ""
echo -e "${GREEN}Starting API server...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

cd apps/api
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

cd ../..
python3 -m uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload

