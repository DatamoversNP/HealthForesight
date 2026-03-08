#!/bin/bash

# HealthForesight Project Restore Script
# This script helps restore the project after a backup

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}HealthForesight Project Restore${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if we're in the project directory
if [ ! -f "pyproject.toml" ] && [ ! -f "apps/web/package.json" ]; then
    echo -e "${RED}Error: This doesn't appear to be the project directory.${NC}"
    echo "Please run this script from the project root."
    exit 1
fi

echo -e "${YELLOW}Checking Python environment...${NC}"

# Check for Poetry
if command -v poetry &> /dev/null; then
    echo -e "${GREEN}✓ Poetry found${NC}"
    USE_POETRY=true
else
    echo -e "${YELLOW}⚠ Poetry not found. Install with: pip install poetry${NC}"
    USE_POETRY=false
fi

# Check for Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python found: ${PYTHON_VERSION}${NC}"
else
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Checking Node.js environment...${NC}"

# Check for Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js found: ${NODE_VERSION}${NC}"
else
    echo -e "${RED}✗ Node.js not found. Please install Node.js 18+${NC}"
    exit 1
fi

# Check for npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓ npm found: ${NPM_VERSION}${NC}"
else
    echo -e "${RED}✗ npm not found. Please install npm${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Installing dependencies...${NC}"
echo ""

# Install Python dependencies
if [ "$USE_POETRY" = true ]; then
    echo -e "${BLUE}Installing Python dependencies with Poetry...${NC}"
    poetry install
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ Skipping Poetry install. Please install dependencies manually:${NC}"
    echo "   pip install poetry"
    echo "   poetry install"
fi

# Install Node.js dependencies
echo ""
echo -e "${BLUE}Installing Node.js dependencies...${NC}"
cd apps/web
npm install
cd "$CURRENT_DIR"
echo -e "${GREEN}✓ Node.js dependencies installed${NC}"

# Check for .env file
echo ""
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file found${NC}"
else
    echo -e "${YELLOW}⚠ .env file not found${NC}"
    if [ -f ".env.example" ]; then
        echo "   Copying .env.example to .env..."
        cp .env.example .env
        echo -e "${YELLOW}   Please update .env with your configuration${NC}"
    else
        echo -e "${YELLOW}   Please create a .env file with your configuration${NC}"
    fi
fi

# Check data directory
echo ""
if [ -d "data" ]; then
    echo -e "${GREEN}✓ data/ directory found${NC}"
else
    echo -e "${YELLOW}⚠ data/ directory not found. Creating...${NC}"
    mkdir -p data
fi

echo ""
echo -e "${GREEN}✓ Restore completed successfully!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Update .env file with your configuration"
echo "  2. Start the API server: ./start-api-server.sh"
echo "  3. Start the web server: cd apps/web && npm run dev"
echo "  4. Or start both: ./start-both-servers.sh"
echo ""
echo -e "${BLUE}To open in Cursor:${NC}"
echo "  1. Open Cursor"
echo "  2. File > Open Folder"
echo "  3. Select this directory: ${CURRENT_DIR}"
echo ""
