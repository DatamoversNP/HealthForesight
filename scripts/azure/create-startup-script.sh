#!/bin/bash
# Create a startup.sh script that will be deployed with the app

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Creating startup.sh script..."

cat > "$PROJECT_ROOT/apps/api/startup.sh" << 'EOF'
#!/bin/bash
# Startup script for Azure App Service
# Finds the code location and starts uvicorn with correct Python

# First, check if Oryx extracted to /tmp (this happens during build)
EXTRACTED_DIR=""
for dir in /tmp/8de* /tmp/*; do
    if [ -d "$dir/src/uepi_api" ] 2>/dev/null || [ -d "$dir/uepi_api" ] 2>/dev/null; then
        EXTRACTED_DIR="$dir"
        break
    fi
done

# If Oryx extracted directory found, use it
if [ -n "$EXTRACTED_DIR" ] && [ -d "$EXTRACTED_DIR/src/uepi_api" ]; then
    export PYTHONPATH="$EXTRACTED_DIR/src:$EXTRACTED_DIR/packages/common/src:$PYTHONPATH"
    cd "$EXTRACTED_DIR/src"
    echo "Using Oryx extracted directory: $EXTRACTED_DIR/src"
elif [ -n "$EXTRACTED_DIR" ] && [ -d "$EXTRACTED_DIR/uepi_api" ]; then
    export PYTHONPATH="$EXTRACTED_DIR:$EXTRACTED_DIR/packages/common/src:$PYTHONPATH"
    cd "$EXTRACTED_DIR"
    echo "Using Oryx extracted directory: $EXTRACTED_DIR"
else
    # Fallback to /home/site/wwwroot
    cd /home/site/wwwroot
    
    # Find uepi_api directory
    UEPI_DIR=$(find . -maxdepth 3 -type d -name "uepi_api" 2>/dev/null | head -1 | xargs dirname)
    COMMON_DIR=$(find . -maxdepth 3 -type d -path "*/packages/common/src" 2>/dev/null | head -1)
    
    # Set PYTHONPATH
    if [ -n "$UEPI_DIR" ] && [ -d "$UEPI_DIR/uepi_api" ]; then
        export PYTHONPATH="$UEPI_DIR:${COMMON_DIR}:$PYTHONPATH"
        cd "$UEPI_DIR"
        echo "Found uepi_api at: $UEPI_DIR"
    elif [ -d "src/uepi_api" ]; then
        export PYTHONPATH="/home/site/wwwroot/src:${COMMON_DIR}:$PYTHONPATH"
        cd src
        echo "Using src/uepi_api"
    else
        export PYTHONPATH="/home/site/wwwroot/src:/home/site/wwwroot/packages/common/src:$PYTHONPATH"
        cd /home/site/wwwroot/src 2>/dev/null || cd /home/site/wwwroot
        echo "Using fallback paths"
    fi
fi

# Use Oryx virtual environment Python if available
# Check both /home/site/wwwroot/antenv and extracted directory antenv
if [ -n "$EXTRACTED_DIR" ] && [ -f "$EXTRACTED_DIR/antenv/bin/python" ]; then
    PYTHON_CMD="$EXTRACTED_DIR/antenv/bin/python"
    echo "Using Oryx virtual environment Python from extracted directory"
elif [ -n "$EXTRACTED_DIR" ] && [ -f "$EXTRACTED_DIR/antenv/bin/python3" ]; then
    PYTHON_CMD="$EXTRACTED_DIR/antenv/bin/python3"
    echo "Using Oryx virtual environment Python3 from extracted directory"
elif [ -f "/home/site/wwwroot/antenv/bin/python" ]; then
    PYTHON_CMD="/home/site/wwwroot/antenv/bin/python"
    echo "Using Oryx virtual environment Python"
elif [ -f "/home/site/wwwroot/antenv/bin/python3" ]; then
    PYTHON_CMD="/home/site/wwwroot/antenv/bin/python3"
    echo "Using Oryx virtual environment Python3"
else
    PYTHON_CMD="python3"
    echo "Using system Python3, installing dependencies..."
    REQ_FILE=$(find /home/site/wwwroot -name "requirements.txt" 2>/dev/null | head -1)
    if [ -z "$REQ_FILE" ] && [ -n "$EXTRACTED_DIR" ]; then
        REQ_FILE=$(find "$EXTRACTED_DIR" -name "requirements.txt" 2>/dev/null | head -1)
    fi
    if [ -n "$REQ_FILE" ]; then
        python3 -m pip install --user -r "$REQ_FILE" > /tmp/pip-install.log 2>&1
    else
        python3 -m pip install --user uvicorn fastapi pydantic pydantic-settings > /tmp/pip-install.log 2>&1
    fi
fi

# Use PORT environment variable (Azure provides this)
PORT=${PORT:-8000}
echo "Starting uvicorn with PYTHONPATH=$PYTHONPATH using $PYTHON_CMD on port $PORT"

# Start uvicorn (use exec to replace shell process)
exec $PYTHON_CMD -m uvicorn uepi_api.main:app --host 0.0.0.0 --port $PORT
EOF

chmod +x "$PROJECT_ROOT/apps/api/startup.sh"
echo "✅ startup.sh created at apps/api/startup.sh"

