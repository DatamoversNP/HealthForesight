#!/bin/bash
# HealthForesight Website Migration Script
# Copies all marketing files and updates import paths

set -e

WEBSITE_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$WEBSITE_DIR/.." && pwd)"
SOURCE_DIR="$PROJECT_ROOT/apps/web/src"

echo "🚀 Starting HealthForesight Website Migration..."
echo "📁 Website Directory: $WEBSITE_DIR"
echo "📦 Source Directory: $SOURCE_DIR"

# Create directories
echo "📂 Creating directories..."
mkdir -p "$WEBSITE_DIR/src/pages"
mkdir -p "$WEBSITE_DIR/src/components"
mkdir -p "$WEBSITE_DIR/src/theme"

# Copy files
echo "📋 Copying pages..."
if [ -d "$SOURCE_DIR/pages/marketing" ]; then
  cp -r "$SOURCE_DIR/pages/marketing"/* "$WEBSITE_DIR/src/pages/"
  echo "  ✓ Pages copied"
else
  echo "  ✗ Pages directory not found"
fi

echo "📋 Copying components..."
if [ -d "$SOURCE_DIR/components/marketing" ]; then
  cp -r "$SOURCE_DIR/components/marketing"/* "$WEBSITE_DIR/src/components/"
  echo "  ✓ Components copied"
else
  echo "  ✗ Components directory not found"
fi

echo "📋 Copying theme..."
if [ -f "$SOURCE_DIR/theme/healthForesightTheme.ts" ]; then
  cp "$SOURCE_DIR/theme/healthForesightTheme.ts" "$WEBSITE_DIR/src/theme/"
  echo "  ✓ Theme copied"
else
  echo "  ✗ Theme file not found"
fi

echo "📋 Copying ErrorBoundary..."
if [ -f "$SOURCE_DIR/components/ErrorBoundary.tsx" ]; then
  cp "$SOURCE_DIR/components/ErrorBoundary.tsx" "$WEBSITE_DIR/src/components/"
  echo "  ✓ ErrorBoundary copied"
else
  echo "  ✗ ErrorBoundary not found"
fi

echo "📋 Copying CSS files..."
if [ -f "$SOURCE_DIR/index.css" ]; then
  cp "$SOURCE_DIR/index.css" "$WEBSITE_DIR/src/"
  echo "  ✓ index.css copied"
fi

if [ -f "$SOURCE_DIR/marketing-animations.css" ]; then
  cp "$SOURCE_DIR/marketing-animations.css" "$WEBSITE_DIR/src/"
  echo "  ✓ marketing-animations.css copied"
fi

# Update import paths
echo "🔄 Updating import paths..."

# Update theme imports
find "$WEBSITE_DIR/src" -type f \( -name "*.tsx" -o -name "*.ts" \) -exec sed -i '' 's|../../theme/|../theme/|g' {} \;
find "$WEBSITE_DIR/src" -type f \( -name "*.tsx" -o -name "*.ts" \) -exec sed -i '' 's|../../../theme/|../theme/|g' {} \;

# Update component imports (marketing folder removed)
find "$WEBSITE_DIR/src" -type f \( -name "*.tsx" -o -name "*.ts" \) -exec sed -i '' 's|../../components/marketing/|../components/|g' {} \;
find "$WEBSITE_DIR/src" -type f \( -name "*.tsx" -o -name "*.ts" \) -exec sed -i '' 's|../../../components/marketing/|../components/|g' {} \;

# Update ErrorBoundary imports
find "$WEBSITE_DIR/src" -type f \( -name "*.tsx" -o -name "*.ts" \) -exec sed -i '' 's|../../components/ErrorBoundary|../components/ErrorBoundary|g' {} \;
find "$WEBSITE_DIR/src" -type f \( -name "*.tsx" -o -name "*.ts" \) -exec sed -i '' 's|../../../components/ErrorBoundary|../components/ErrorBoundary|g' {} \;

# Update page imports
find "$WEBSITE_DIR/src" -type f \( -name "*.tsx" -o -name "*.ts" \) -exec sed -i '' 's|../pages/marketing/|../pages/|g' {} \;
find "$WEBSITE_DIR/src" -type f \( -name "*.tsx" -o -name "*.ts" \) -exec sed -i '' 's|./pages/marketing/|./pages/|g' {} \;

# Update component imports (remove marketing folder references)
find "$WEBSITE_DIR/src" -type f \( -name "*.tsx" -o -name "*.ts" \) -exec sed -i '' 's|./components/marketing/|./components/|g' {} \;

echo "  ✓ Import paths updated"

echo ""
echo "✅ Migration complete!"
echo ""
echo "📦 Next steps:"
echo "  1. cd $WEBSITE_DIR"
echo "  2. npm install"
echo "  3. npm run dev"
echo ""
