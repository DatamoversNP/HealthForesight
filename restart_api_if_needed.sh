#!/bin/bash
# Restart API if it's not running

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}🔍 Checking API Status${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if API is responding
if curl -s --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API is running and responding${NC}"
    echo "   Health check: http://localhost:8000/health"
    exit 0
fi

echo -e "${YELLOW}⚠️  API is not responding${NC}"
echo ""

# Check if port is in use but not responding
if lsof -ti:8000 > /dev/null 2>&1; then
    echo -e "${YELLOW}Port 8000 is in use but API not responding${NC}"
    echo -e "${YELLOW}Stopping existing process...${NC}"
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

echo -e "${BLUE}🚀 Starting API server...${NC}"
echo ""

# Start API using the local start script
cd "$SCRIPT_DIR"
./start_api_local.sh

