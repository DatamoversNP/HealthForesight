# HealthForesight Website Separation - Migration Guide

## ✅ Status

Base structure created. Need to:
1. Copy all marketing files (pages, components)
2. Copy theme and utilities
3. Update all import paths
4. Test build

## 📋 Manual Steps

Due to file system restrictions, please run these commands manually:

### 1. Create Directory Structure

```bash
cd /Users/nilesh.patil/Downloads/Utilization\ Elastisity\ and\ Policy\ Impact\ Solution/healthforesight-Website
mkdir -p src/{pages,components,theme}
```

### 2. Copy Files

```bash
# Copy pages
cp -r ../apps/web/src/pages/marketing/* src/pages/

# Copy components  
cp -r ../apps/web/src/components/marketing/* src/components/

# Copy theme
cp ../apps/web/src/theme/healthForesightTheme.ts src/theme/

# Copy ErrorBoundary
cp ../apps/web/src/components/ErrorBoundary.tsx src/components/

# Copy CSS files
cp ../apps/web/src/index.css src/
cp ../apps/web/src/marketing-animations.css src/
```

### 3. Update Import Paths

All files need imports updated from:
- `../../theme/` → `../theme/`
- `../../components/marketing/` → `../components/`
- `../../components/ErrorBoundary` → `../components/ErrorBoundary`
- `../pages/marketing/` → `../pages/`

### 4. Update App.tsx imports

Change:
- `./components/marketing/MarketingLayout` → `./components/MarketingLayout`
- `./pages/marketing/HomePage` → `./pages/HomePage`
- etc.

### 5. Install Dependencies

```bash
cd healthforesight-Website
npm install
```

### 6. Test Build

```bash
npm run dev
# Should run on http://localhost:3052
```

## 🎯 Quick Migration Script

Or use this script (run from project root):

```bash
#!/bin/bash
WEBSITE_DIR="healthforesight-Website"
SOURCE_DIR="apps/web/src"

# Create directories
mkdir -p "$WEBSITE_DIR/src/{pages,components,theme}"

# Copy files
cp -r "$SOURCE_DIR/pages/marketing"/* "$WEBSITE_DIR/src/pages/"
cp -r "$SOURCE_DIR/components/marketing"/* "$WEBSITE_DIR/src/components/"
cp "$SOURCE_DIR/theme/healthForesightTheme.ts" "$WEBSITE_DIR/src/theme/"
cp "$SOURCE_DIR/components/ErrorBoundary.tsx" "$WEBSITE_DIR/src/components/"
cp "$SOURCE_DIR/index.css" "$WEBSITE_DIR/src/"
cp "$SOURCE_DIR/marketing-animations.css" "$WEBSITE_DIR/src/"

# Update import paths in all files
find "$WEBSITE_DIR/src" -type f -name "*.tsx" -o -name "*.ts" | xargs sed -i '' 's|../../theme/|../theme/|g'
find "$WEBSITE_DIR/src" -type f -name "*.tsx" -o -name "*.ts" | xargs sed -i '' 's|../../components/marketing/|../components/|g'
find "$WEBSITE_DIR/src" -type f -name "*.tsx" -o -name "*.ts" | xargs sed -i '' 's|../../components/ErrorBoundary|../components/ErrorBoundary|g'
find "$WEBSITE_DIR/src" -type f -name "*.tsx" -o -name "*.ts" | xargs sed -i '' 's|../pages/marketing/|../pages/|g'
find "$WEBSITE_DIR/src" -type f -name "*.tsx" -o -name "*.ts" | xargs sed -i '' 's|./components/marketing/|./components/|g'
find "$WEBSITE_DIR/src" -type f -name "*.tsx" -o -name "*.ts" | xargs sed -i '' 's|./pages/marketing/|./pages/|g'

echo "✅ Files copied and imports updated!"
echo "📦 Run: cd $WEBSITE_DIR && npm install"
```

## 📝 Notes

- All dependencies are self-contained in `package.json`
- No dependency on core application code
- Deployment is simplified to single folder
- All imports must be relative paths within `src/`
