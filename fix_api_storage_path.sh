#!/bin/bash
# Fix API storage path issue - ensure API can find policy files

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔧 Fixing API Storage Path${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$PROJECT_ROOT/data"

echo "Project root: $PROJECT_ROOT"
echo "Data directory: $DATA_DIR"
echo ""

# Check if data directory exists
if [ ! -d "$DATA_DIR" ]; then
    echo -e "${RED}❌ Data directory not found: $DATA_DIR${NC}"
    exit 1
fi

# Count policy files
POLICY_COUNT=$(find "$DATA_DIR" -name "policy_*.json" -not -name "valid_policies.json" -not -name "canonical_policies.json" | wc -l | tr -d ' ')
echo -e "${GREEN}✅ Found $POLICY_COUNT policy files in data directory${NC}"
echo ""

# Check if API is running
if ! curl -s -f http://localhost:8000/health > /dev/null 2>&1 && ! curl -s -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  API is not running${NC}"
    echo ""
    echo "To start API with correct STORAGE_PATH:"
    echo "  export STORAGE_PATH=\"$DATA_DIR\""
    echo "  ./start_api_local.sh"
    echo ""
    echo "Or set it in the start script:"
    echo "  STORAGE_PATH=\"$DATA_DIR\" ./start_api_local.sh"
else
    echo -e "${GREEN}✅ API is running${NC}"
    echo ""
    echo "The API should use STORAGE_PATH environment variable."
    echo "If it's not finding files, restart the API with:"
    echo "  export STORAGE_PATH=\"$DATA_DIR\""
    echo "  ./start_api_local.sh"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

