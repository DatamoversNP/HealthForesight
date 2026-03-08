#!/bin/bash
# Search logs for specific terms

LOG_DIR="logs"
SEARCH_TERM="${1:-}"

if [ -z "$SEARCH_TERM" ]; then
    echo "Usage: $0 <search_term>"
    echo ""
    echo "Examples:"
    echo "  $0 ST_BIOLOGIC_006    # Search for specific policy"
    echo "  $0 error              # Search for errors"
    echo "  $0 policy_viewed     # Search for actions"
    exit 1
fi

if [ ! -d "$LOG_DIR" ]; then
    echo "❌ Logs directory not found: $LOG_DIR"
    exit 1
fi

echo "🔍 Searching for: $SEARCH_TERM"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Search all log files
for log_file in "$LOG_DIR"/*.log; do
    if [ -f "$log_file" ]; then
        echo "📄 $(basename $log_file):"
        if command -v jq &> /dev/null; then
            grep -h "$SEARCH_TERM" "$log_file" | jq . 2>/dev/null || grep -h "$SEARCH_TERM" "$log_file"
        else
            grep -h "$SEARCH_TERM" "$log_file"
        fi
        echo ""
    fi
done

