#!/bin/bash

# Backup Core Product Before Azure Migration
# Creates a complete copy of the core product code

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${CURRENT_DIR}/.backup-core-product"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="core-product-backup-${TIMESTAMP}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Backing Up Core Product${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Create backup directory
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

echo -e "${YELLOW}Creating complete backup of core product...${NC}"
echo ""

cd "$CURRENT_DIR"

# Copy all core directories and files
echo -e "${BLUE}Copying source code...${NC}"

# Core application directories
DIRS_TO_COPY=(
    "apps"
    "packages"
    "infra"
    "scripts"
    "data"
    "docs"
    "tests"
)

# Core configuration files
FILES_TO_COPY=(
    "pyproject.toml"
    "poetry.lock"
    "Makefile"
    "docker-compose.yml"
    "docker-compose.no-db.yml"
    "README.md"
    "README_AZURE.md"
    ".gitignore"
    "CADDY_DOCKERFILE"
)

# Documentation files (all .md files)
echo -e "${YELLOW}Copying documentation...${NC}"
find . -maxdepth 1 -name "*.md" -type f | while read file; do
    cp "$file" "${BACKUP_DIR}/${BACKUP_NAME}/"
done

# Copy core directories
for dir in "${DIRS_TO_COPY[@]}"; do
    if [ -d "$dir" ]; then
        echo "  Copying $dir/..."
        cp -r "$dir" "${BACKUP_DIR}/${BACKUP_NAME}/"
    fi
done

# Copy core files
for file in "${FILES_TO_COPY[@]}"; do
    if [ -f "$file" ]; then
        echo "  Copying $file..."
        cp "$file" "${BACKUP_DIR}/${BACKUP_NAME}/"
    fi
done

# Copy important scripts
echo -e "${YELLOW}Copying scripts...${NC}"
find . -maxdepth 1 -name "*.sh" -type f | while read file; do
    cp "$file" "${BACKUP_DIR}/${BACKUP_NAME}/"
done

# Create backup info
cat > "${BACKUP_DIR}/${BACKUP_NAME}/BACKUP_INFO.txt" <<EOF
Core Product Backup
===================

Backup Date: $(date)
Backup Name: ${BACKUP_NAME}
Original Directory: ${CURRENT_DIR}

Contents:
---------
This backup includes the complete core product before Azure File Storage migration:
- All source code (apps/, packages/, scripts/)
- Configuration files (pyproject.toml, package.json, etc.)
- Data files (data/)
- Documentation (*.md)
- Infrastructure code (infra/)
- Scripts (start-*.sh, backup-*.sh)

Purpose:
--------
This backup preserves the working file-based system before migrating to Azure File Storage.

To Restore:
-----------
1. Copy this backup to a directory
2. Restore files from this backup
3. Run: poetry install && cd apps/web && npm install

EOF

# Create compressed archive
echo ""
echo -e "${YELLOW}Creating compressed archive...${NC}"
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"

# Calculate sizes
BACKUP_SIZE=$(du -sh "${BACKUP_NAME}.tar.gz" | cut -f1)
ARCHIVE_SIZE=$(du -sh "$BACKUP_NAME" | cut -f1)

echo ""
echo -e "${GREEN}✓ Core product backup completed!${NC}"
echo ""
echo -e "${BLUE}Backup Details:${NC}"
echo "  Name: ${BACKUP_NAME}"
echo "  Location: ${BACKUP_DIR}"
echo "  Archive: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})"
echo "  Uncompressed: ${ARCHIVE_SIZE}"
echo ""
echo -e "${YELLOW}This backup preserves the working file-based system${NC}"
echo -e "${YELLOW}before migrating to Azure File Storage.${NC}"
echo ""
