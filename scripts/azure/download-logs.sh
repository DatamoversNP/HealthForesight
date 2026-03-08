#!/bin/bash
# Download logs instead of streaming

RESOURCE_GROUP="${RESOURCE_GROUP:-healthforesight-rg}"
API_APP_NAME="${API_APP_NAME:-healthforesight-api-9016}"

echo "Downloading API logs..."
az webapp log download \
  --resource-group $RESOURCE_GROUP \
  --name $API_APP_NAME \
  --log-file api-logs.zip

if [ -f api-logs.zip ]; then
    echo ""
    echo "Extracting logs..."
    unzip -o api-logs.zip -d api-logs 2>/dev/null || true
    
    echo ""
    echo "Recent application logs:"
    find api-logs -name "*.log" -type f | head -5 | while read logfile; do
        echo ""
        echo "=== $logfile (last 30 lines) ==="
        tail -30 "$logfile" 2>/dev/null || cat "$logfile" 2>/dev/null | tail -30
    done
    
    echo ""
    echo "Logs saved to: api-logs/"
    echo "To view all logs: find api-logs -name '*.log' -exec tail -50 {} \;"
else
    echo "Failed to download logs"
fi

