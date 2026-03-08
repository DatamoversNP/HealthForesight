#!/bin/bash
# Stop app to save costs, then provide a final fix

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Stopping App to Save Costs ==="
echo ""

echo "1. Stopping app..."
az webapp stop \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

echo "   ✅ App stopped - costs paused"
echo ""

echo "=== Root Cause Analysis ==="
echo ""
echo "The issue: Oryx extracts files to /tmp/XXX but PYTHONPATH doesn't include it"
echo ""
echo "The real problem: Even when we set PYTHONPATH in the startup command,"
echo "Oryx runs FIRST and sets its own PYTHONPATH, which overrides ours."
echo ""
echo "=== Solution: Use App Settings for PYTHONPATH ==="
echo ""
echo "The key insight: We need to ensure the extracted directory path is in PYTHONPATH"
echo "BEFORE Oryx runs, or we need to copy files to /home/site/wwwroot after extraction."
echo ""
echo "Let's try a different approach: Deploy with a .deployment file that tells"
echo "Oryx where to put files, OR use a post-build script."
echo ""

echo "2. Checking if we can see what's actually in the deployment..."
echo "   (This helps diagnose the real issue)"
echo ""

echo "=== Next Steps ==="
echo ""
echo "Option 1: Fix the ZIP structure to ensure files are in the right place"
echo "Option 2: Use Azure App Service's post-deployment hook"
echo "Option 3: Copy files after Oryx extracts them"
echo ""
echo "The simplest fix: Let's verify the ZIP has the correct structure,"
echo "then redeploy with a post-extraction script that copies files to the right location."
echo ""

echo "App is stopped. Costs are paused. We can fix this properly now."
