#!/bin/bash

# HealthForesight Project Backup Script
# This script creates a complete backup of the project, excluding dependencies
# that can be regenerated (node_modules, __pycache__, venv, etc.)

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="healthforesight-uepi"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="${PROJECT_NAME}_backup_${TIMESTAMP}"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Backup directory - prefer project directory, fallback to home
if [ -w "$CURRENT_DIR" ]; then
    BACKUP_DIR="${CURRENT_DIR}/.backups"
else
    BACKUP_DIR="${HOME}/HealthForesight-Backups"
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}HealthForesight Project Backup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create temporary directory for backup
TEMP_BACKUP_DIR="${BACKUP_DIR}/${BACKUP_NAME}"
mkdir -p "$TEMP_BACKUP_DIR"

echo -e "${YELLOW}Creating backup: ${BACKUP_NAME}${NC}"
echo ""

# Change to project root
cd "$CURRENT_DIR"

# List of directories/files to exclude (can be regenerated)
EXCLUDE_PATTERNS=(
    "node_modules"
    "__pycache__"
    "*.pyc"
    "*.pyo"
    ".pytest_cache"
    ".venv"
    "venv"
    "env"
    ".env.local"
    "dist"
    "dist-docs"
    "build"
    ".next"
    ".turbo"
    ".cache"
    "coverage"
    ".coverage"
    "*.log"
    "*.log.*"
    "logs"
    "api-server.log"
    "web-server.log"
    ".DS_Store"
    "*.swp"
    "*.swo"
    "*~"
    ".idea"
    ".vscode"
    ".cursor"
)

# Build exclude arguments for rsync
RSYNC_EXCLUDES=""
for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    RSYNC_EXCLUDES="${RSYNC_EXCLUDES} --exclude='${pattern}'"
done

# Use rsync to copy files (excluding patterns)
echo -e "${YELLOW}Copying project files...${NC}"
eval rsync -av --progress ${RSYNC_EXCLUDES} \
    --exclude='.git' \
    --exclude='HealthForesight-Backups' \
    --exclude='.backups' \
    --exclude='backup.sh' \
    --exclude='restore.sh' \
    "$CURRENT_DIR/" "$TEMP_BACKUP_DIR/"

# Create a backup info file
cat > "$TEMP_BACKUP_DIR/BACKUP_INFO.txt" <<EOF
HealthForesight Project Backup
==============================

Backup Date: $(date)
Backup Name: ${BACKUP_NAME}
Project Directory: ${CURRENT_DIR}

Contents:
---------
This backup includes:
- All source code (apps/, packages/, scripts/)
- Configuration files (pyproject.toml, package.json, etc.)
- Data files (data/)
- Documentation files (*.md)
- Infrastructure files (infra/)
- All other project files except dependencies

Excluded (can be regenerated):
- node_modules (npm install)
- __pycache__ (Python bytecode)
- venv/.venv (poetry install)
- dist/build directories (npm/pip build)
- Log files
- .git directory (use git clone if needed)

Restoration:
-----------
See RESTORE_INSTRUCTIONS.txt for detailed restoration steps.

Quick restore:
1. Extract this backup to a directory
2. Run: cd <project-dir> && poetry install
3. Run: cd apps/web && npm install
4. Run: ./restore.sh (if available)

EOF

# Create restore instructions
cat > "$TEMP_BACKUP_DIR/RESTORE_INSTRUCTIONS.txt" <<EOF
HealthForesight Project Restoration Guide
==========================================

To restore this backup in Cursor or any IDE:

1. Extract/Restore Files
   ---------------------
   - Extract this backup to your desired location
   - Or copy the entire backup directory to your workspace

2. Install Python Dependencies
   ----------------------------
   cd <project-directory>
   poetry install
   
   OR if poetry is not installed:
   python3 -m pip install -r requirements.txt
   (Note: You may need to create requirements.txt from pyproject.toml)

3. Install Node.js Dependencies
   -----------------------------
   cd apps/web
   npm install

4. Set Up Environment Variables
   -----------------------------
   - Copy .env.example to .env (if it exists)
   - Update .env with your configuration

5. Verify Installation
   --------------------
   - Check that Python dependencies are installed: poetry show
   - Check that Node dependencies are installed: cd apps/web && npm list

6. Start Development Servers
   --------------------------
   - API Server: ./start-api-server.sh
   - Web Server: cd apps/web && npm run dev
   - Or use: ./start-both-servers.sh

7. Open in Cursor
   ---------------
   - Open Cursor
   - File > Open Folder
   - Select the project directory
   - Cursor should detect the project structure

Additional Notes:
----------------
- If you have data files, ensure they are in the data/ directory
- Check that STORAGE_PATH environment variable points to the correct location
- Review any .env files and update configuration as needed

Troubleshooting:
---------------
- If poetry fails, try: pip install poetry
- If npm fails, ensure Node.js v18+ is installed
- For API server issues, check api-server.log
- For web server issues, check the browser console

EOF

# Create a package.json backup check
if [ -f "pyproject.toml" ]; then
    echo "✓ Found pyproject.toml"
fi

if [ -f "apps/web/package.json" ]; then
    echo "✓ Found package.json"
fi

# Create compressed archive
echo ""
echo -e "${YELLOW}Creating compressed archive...${NC}"
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"

# Calculate backup size
BACKUP_SIZE=$(du -sh "${BACKUP_NAME}.tar.gz" | cut -f1)
ARCHIVE_SIZE=$(du -sh "$BACKUP_NAME" | cut -f1)

echo ""
echo -e "${GREEN}✓ Backup completed successfully!${NC}"
echo ""
echo -e "${BLUE}Backup Details:${NC}"
echo "  Name: ${BACKUP_NAME}"
echo "  Location: ${BACKUP_DIR}"
echo "  Archive: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})"
echo "  Uncompressed: ${ARCHIVE_SIZE}"
echo ""
echo -e "${YELLOW}To restore:${NC}"
echo "  1. Extract: tar -xzf ${BACKUP_NAME}.tar.gz"
echo "  2. Follow instructions in: ${BACKUP_NAME}/RESTORE_INSTRUCTIONS.txt"
echo ""
echo -e "${BLUE}To create another backup, run: ./backup.sh${NC}"
