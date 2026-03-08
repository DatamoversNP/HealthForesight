#!/bin/bash
# Download logs and check for errors

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Downloading and Checking Logs ==="
echo ""

echo "1. Downloading logs..."
az webapp log download \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --log-file ./logs.zip \
    --output none 2>&1 | grep -v "NotOpenSSLWarning" || true

if [ -f ./logs.zip ]; then
    echo "   ✅ Logs downloaded"
    
    echo ""
    echo "2. Extracting logs..."
    unzip -q ./logs.zip -d ./logs_extracted 2>/dev/null || true
    
    if [ -d ./logs_extracted ]; then
        echo "   ✅ Logs extracted"
        
        echo ""
        echo "3. Checking for errors..."
        echo ""
        grep -r -i "error\|exception\|traceback\|failed\|cannot\|module" ./logs_extracted 2>/dev/null | head -30 || echo "   No obvious errors found"
        
        echo ""
        echo "4. Checking for startup messages..."
        echo ""
        grep -r -i "uvicorn\|started\|ready\|application" ./logs_extracted 2>/dev/null | tail -20 || echo "   No startup messages found"
        
        echo ""
        echo "5. Recent log entries..."
        echo ""
        find ./logs_extracted -name "*.log" -type f -exec tail -10 {} \; 2>/dev/null | head -30
        
        # Cleanup
        rm -rf ./logs_extracted ./logs.zip 2>/dev/null || true
    else
        echo "   ⚠️  Could not extract logs"
    fi
else
    echo "   ⚠️  Could not download logs"
    echo "   Try checking logs in Azure Portal:"
    echo "   https://portal.azure.com -> App Service -> Log stream"
fi

echo ""
echo "=== Complete ==="
