#!/bin/bash
# Start the Celery worker

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

cd "$SCRIPT_DIR"

# Set up Python path
export PYTHONPATH="$SCRIPT_DIR/src:$PROJECT_ROOT/packages/common/src:$PROJECT_ROOT/apps/api/src"

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis is not running!"
    echo "   Please start Redis first:"
    echo "   - macOS: brew services start redis"
    echo "   - Or: redis-server"
    echo ""
    exit 1
fi

echo "✅ Redis is running"
echo "🚀 Starting Celery worker..."
echo ""

# Start Celery worker
celery -A uepi_worker.main.app worker --loglevel=info
