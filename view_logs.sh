#!/bin/bash
# View logs without jq (works on macOS without additional tools)

LOG_DIR="logs"

if [ ! -d "$LOG_DIR" ]; then
    echo "❌ Logs directory not found: $LOG_DIR"
    echo "   The API needs to be running to generate logs."
    echo "   Start the API with: ./start_api_local.sh"
    exit 1
fi

# Check which log file to view
LOG_TYPE="${1:-api}"

case "$LOG_TYPE" in
    api|all)
        LOG_FILE="$LOG_DIR/api.log"
        ;;
    error|errors)
        LOG_FILE="$LOG_DIR/errors.log"
        ;;
    action|actions)
        LOG_FILE="$LOG_DIR/actions.log"
        ;;
    request|requests)
        LOG_FILE="$LOG_DIR/requests.log"
        ;;
    *)
        echo "Usage: $0 [api|error|action|request]"
        echo ""
        echo "Examples:"
        echo "  $0 api      # View all API logs"
        echo "  $0 error    # View errors only"
        echo "  $0 action   # View user actions"
        echo "  $0 request  # View HTTP requests"
        exit 1
        ;;
esac

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo "   The API needs to be running to generate logs."
    echo "   Start the API with: ./start_api_local.sh"
    exit 1
fi

echo "📋 Viewing: $LOG_FILE"
echo "   Press Ctrl+C to stop"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if jq is available
if command -v jq &> /dev/null; then
    # Use jq for pretty formatting
    tail -f "$LOG_FILE" | jq .
else
    # Without jq, just show raw JSON (one per line)
    tail -f "$LOG_FILE"
fi

