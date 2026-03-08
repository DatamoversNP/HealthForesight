#!/bin/bash
# Comprehensive System Startup Script
# Initializes system and starts the application

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 UEPI System Startup${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}📦 Activating virtual environment...${NC}"
source .venv/bin/activate

# Check and install dependencies
echo -e "${BLUE}📦 Checking dependencies...${NC}"
if ! python -c "import psycopg2" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  psycopg2-binary not found. Installing...${NC}"
    pip install psycopg2-binary
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ psycopg2-binary installed${NC}"
    else
        echo -e "${RED}❌ Failed to install psycopg2-binary. Please install manually:${NC}"
        echo -e "${YELLOW}   pip install psycopg2-binary${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Dependencies check passed${NC}"
fi

# Check if DATABASE_URL is set, and ensure it points to uepi_db
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⚠️  DATABASE_URL not set. Using default PostgreSQL connection.${NC}"
    export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"
elif [[ "$DATABASE_URL" != *"/uepi_db"* ]] && [[ "$DATABASE_URL" == *"/postgres"* ]]; then
    # If DATABASE_URL points to 'postgres', update it to 'uepi_db'
    echo -e "${YELLOW}⚠️  DATABASE_URL points to 'postgres'. Updating to 'uepi_db'.${NC}"
    export DATABASE_URL="${DATABASE_URL%/postgres}/uepi_db"
fi

# Set debug logging
export LOG_LEVEL="${LOG_LEVEL:-DEBUG}"
export USE_FILE_STORAGE="false"

echo -e "${BLUE}🔧 Configuration:${NC}"
echo "   DATABASE_URL: $DATABASE_URL"
echo "   LOG_LEVEL: $LOG_LEVEL"
echo "   USE_FILE_STORAGE: $USE_FILE_STORAGE"
echo ""

# Step 1: Initialize system
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 1: Initializing System${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

if [ -f "apps/api/scripts/initialize_system.py" ]; then
    echo -e "${BLUE}📋 Running system initialization...${NC}"
    python apps/api/scripts/initialize_system.py
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ System initialization complete${NC}"
    else
        echo -e "${YELLOW}⚠️  System initialization had warnings. Continuing...${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Initialization script not found. Skipping...${NC}"
fi

echo ""

# Step 2: Start API server
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 2: Starting API Server${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

# Check if API server is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  API server already running on port 8000${NC}"
    read -p "Kill existing server and restart? (y/n): " KILL_SERVER
    if [ "$KILL_SERVER" = "y" ] || [ "$KILL_SERVER" = "Y" ]; then
        echo -e "${BLUE}🛑 Stopping existing server...${NC}"
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        sleep 2
    else
        echo -e "${GREEN}✅ Using existing API server${NC}"
        echo ""
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}🎉 System Ready!${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "API Server: http://localhost:8000"
        echo "API Docs: http://localhost:8000/docs"
        echo "Health Check: http://localhost:8000/health"
        echo ""
        echo "To start the web UI:"
        echo "  cd apps/web && npm run dev"
        echo ""
        exit 0
    fi
fi

# Start API server
echo -e "${BLUE}🚀 Starting API server...${NC}"
cd apps/api

# Set PYTHONPATH to include src directory and common package so uvicorn can find modules
export PYTHONPATH="${SCRIPT_DIR}/apps/api/src:${SCRIPT_DIR}/packages/common/src:${PYTHONPATH}"

# Ensure all environment variables are set for the background process
export DATABASE_URL="${DATABASE_URL}"
export LOG_LEVEL="${LOG_LEVEL}"
export USE_FILE_STORAGE="${USE_FILE_STORAGE}"

# Start server in background with proper environment
(
    export PYTHONPATH="${SCRIPT_DIR}/apps/api/src:${SCRIPT_DIR}/packages/common/src:${PYTHONPATH}"
    export DATABASE_URL="${DATABASE_URL}"
    export LOG_LEVEL="${LOG_LEVEL}"
    export USE_FILE_STORAGE="${USE_FILE_STORAGE}"
    cd "${SCRIPT_DIR}/apps/api"
    nohup uvicorn uepi_api.main:app --host 0.0.0.0 --port 8000 --reload > "${SCRIPT_DIR}/api-server.log" 2>&1
) &
API_PID=$!

# Wait for server to start
echo -e "${BLUE}⏳ Waiting for API server to start...${NC}"
# Give server time to initialize (database connection, module loading, etc.)
sleep 3

MAX_WAIT=45
for i in $(seq 1 $MAX_WAIT); do
    # Check if process is still running
    if ! kill -0 $API_PID 2>/dev/null; then
        echo -e "${RED}❌ API server process died${NC}"
        echo -e "${YELLOW}Check logs: tail -f api-server.log${NC}"
        exit 1
    fi
    
    # Check if port is listening
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        # Port is listening, check health endpoint
        if curl -s -f -m 2 http://127.0.0.1:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ API server is responding!${NC}"
            break
        fi
    fi
    
    # Show progress every 5 seconds
    if [ $((i % 5)) -eq 0 ]; then
        echo -e "${YELLOW}   Still waiting... (${i}s / ${MAX_WAIT}s)${NC}"
    fi
    
    if [ $i -eq $MAX_WAIT ]; then
        # Check if server process is still running
        if kill -0 $API_PID 2>/dev/null; then
            echo -e "${YELLOW}⚠️  Health check timeout, but server process is running${NC}"
            echo -e "${YELLOW}Server may still be initializing. Check manually:${NC}"
            echo -e "${YELLOW}  curl http://localhost:8000/health${NC}"
            echo -e "${YELLOW}  tail -f api-server.log${NC}"
            # Don't exit - server might be working, just slow to respond
        else
            echo -e "${RED}❌ API server process died${NC}"
            echo -e "${YELLOW}Check logs: tail -f api-server.log${NC}"
            exit 1
        fi
        break
    fi
    sleep 1
done

cd "$SCRIPT_DIR"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 System Ready!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "API Server: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Health Check: http://localhost:8000/health"
echo ""
echo "Logs:"
echo "  API Server: tail -f api-server.log"
echo "  System Init: tail -f system_init.log"
echo "  Application: tail -f logs/api.log"
echo ""
echo "To start the web UI:"
echo "  cd apps/web && npm run dev"
echo ""
echo "Source Data Locations:"
echo "  Historical: data/source_data/00000000-0000-0000-0000-000000000001/historical/"
echo "  Daily: data/source_data/00000000-0000-0000-0000-000000000001/daily/YYYY-MM-DD/"
echo ""
echo "To stop the API server:"
echo "  kill $API_PID"
echo "  or: lsof -ti:8000 | xargs kill"
echo ""

