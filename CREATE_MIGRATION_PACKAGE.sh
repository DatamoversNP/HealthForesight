#!/bin/bash
# Create migration package for moving to new system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📦 Creating Migration Package"
echo "============================="
echo ""

# Create timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
PACKAGE_NAME="uepi-migration-${TIMESTAMP}.tar.gz"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📁 Project directory: $SCRIPT_DIR"
echo "📦 Package will be: $PARENT_DIR/$PACKAGE_NAME"
echo ""

# Export requirements
echo "1️⃣  Exporting Python dependencies..."
if [ -d ".venv" ]; then
    source .venv/bin/activate 2>/dev/null || true
    pip freeze > requirements.txt 2>/dev/null || echo "⚠️  Could not export requirements"
    echo "   ✅ Created requirements.txt"
else
    echo "   ⚠️  No virtual environment found"
fi

# Export npm dependencies if frontend exists
if [ -d "apps/web" ]; then
    echo ""
    echo "2️⃣  Exporting Node dependencies..."
    cd apps/web
    npm list --depth=0 > ../../npm-dependencies.txt 2>/dev/null || echo "⚠️  Could not export npm dependencies"
    cd ../..
    echo "   ✅ Created npm-dependencies.txt"
fi

cd "$SCRIPT_DIR"

# Create package
echo ""
echo "3️⃣  Creating migration package..."
echo "   This may take a few minutes..."
echo "   Including:"
echo "   - All source code (apps/, packages/, scripts/)"
echo "   - All data files (data/, apps/api/data/)"
echo "   - All scripts (*.sh files)"
echo "   - All documentation (*.md files)"
echo "   - Configuration files"
echo ""

tar -czf "$PARENT_DIR/$PACKAGE_NAME" \
  --exclude='.venv' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  --exclude='*.log' \
  --exclude='*.tar.gz' \
  --exclude='.DS_Store' \
  --exclude='healthforesight-Website-backup-*.tar.gz' \
  . 2>&1 | grep -v "Removing leading" || true

# Get package size
PACKAGE_SIZE=$(du -h "$PARENT_DIR/$PACKAGE_NAME" | cut -f1)

echo ""
echo "✅ Migration package created!"
echo ""
echo "📦 Package: $PARENT_DIR/$PACKAGE_NAME"
echo "📊 Size: $PACKAGE_SIZE"
echo ""
echo "📋 Next steps:"
echo "   1. Transfer this file to your new Mac"
echo "   2. Extract: tar -xzf $PACKAGE_NAME"
echo "   3. Follow MIGRATE_TO_NEW_SYSTEM.md"
echo ""
