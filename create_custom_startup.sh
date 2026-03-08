#!/bin/bash
# Create a startup.sh file that will be deployed in the ZIP and used by Oryx

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$SCRIPT_DIR/apps/api"

echo "=== Creating Custom startup.sh for Deployment ==="
echo ""

cd "$API_DIR"

echo "1. Creating startup.sh that finds extracted directory..."
cat > startup.sh <<'EOF'
#!/bin/bash
# Custom startup script that finds Oryx extracted directory and adds it to PYTHONPATH

# Find Oryx extracted directory (has antenv and src/uepi_api)
EXTRACTED_DIR=""
for dir in /tmp/*; do
    if [ -d "$dir/antenv" ] && [ -d "$dir/src/uepi_api" ]; then
        EXTRACTED_DIR="$dir"
        break
    fi
done

# If not found, try to find any /tmp directory with src/uepi_api
if [ -z "$EXTRACTED_DIR" ]; then
    for dir in /tmp/8de* /tmp/*; do
        if [ -d "$dir/src/uepi_api" ] 2>/dev/null; then
            EXTRACTED_DIR="$dir"
            break
        fi
    done
fi

# Set PYTHONPATH with extracted directory FIRST (highest priority)
if [ -n "$EXTRACTED_DIR" ] && [ -d "$EXTRACTED_DIR/src/uepi_api" ]; then
    export PYTHONPATH="$EXTRACTED_DIR/src:$EXTRACTED_DIR/packages/common/src:/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"
    cd "$EXTRACTED_DIR"
    echo "[STARTUP] Using extracted directory: $EXTRACTED_DIR"
    echo "[STARTUP] PYTHONPATH: $PYTHONPATH"
    echo "[STARTUP] Checking for uepi_api: $(ls -la src/uepi_api/main.py 2>&1 | head -1)"
else
    export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"
    cd /home/site/wwwroot
    echo "[STARTUP] WARNING: Could not find extracted directory, using fallback"
fi

# Use PORT environment variable (Azure App Service provides this)
PORT=${PORT:-8000}

# Start the application
echo "[STARTUP] Starting uvicorn on port $PORT..."
exec python -m uvicorn uepi_api.main:app --host 0.0.0.0 --port $PORT
EOF

chmod +x startup.sh

echo "   ✅ startup.sh created"
echo ""

echo "2. Verifying startup.sh content..."
head -10 startup.sh
echo ""

echo "3. Next steps:"
echo "   This startup.sh will be included in the ZIP on next deployment."
echo "   Oryx should use this file if it's in the deployment root."
echo ""
echo "   To deploy with this startup.sh, run:"
echo "   cd apps/api"
echo "   zip -r deploy.zip . -x '*.git*' -x '*.venv*' -x '*__pycache__*' -x '*.pyc' -x 'data/*' -x 'target_data_model/*'"
echo "   az webapp deployment source config-zip --resource-group healthforesight-rg --name hf-api8755146 --src deploy.zip"
echo ""
echo "   Or run the verify_and_fix_deployment.sh script which will include this startup.sh"
echo ""
