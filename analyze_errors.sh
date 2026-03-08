#!/bin/bash
# Analyze errors from logs and update error tracker

echo "═══════════════════════════════════════════════════════════════"
echo "🔍 Analyzing Errors from Logs"
echo "═══════════════════════════════════════════════════════════════"
echo ""

LOG_DIR="logs"
ERROR_COUNT=0
CRITICAL_COUNT=0
HIGH_COUNT=0
MEDIUM_COUNT=0

# Check if logs directory exists
if [ ! -d "$LOG_DIR" ]; then
    echo "❌ Logs directory not found: $LOG_DIR"
    echo "   Start the API to generate logs: ./start_api_local.sh"
    exit 1
fi

echo "📊 Analyzing log files..."
echo ""

# Analyze errors.log
if [ -f "$LOG_DIR/errors.log" ]; then
    echo "1️⃣ Analyzing errors.log..."
    ERROR_LINES=$(wc -l < "$LOG_DIR/errors.log" | tr -d ' ')
    echo "   Total log entries: $ERROR_LINES"
    
    # Extract unique error types
    echo ""
    echo "   Top error types:"
    grep -o '"error_type":"[^"]*"' "$LOG_DIR/errors.log" 2>/dev/null | \
        sort | uniq -c | sort -rn | head -10 || echo "   (No error types found)"
    
    # Extract error messages
    echo ""
    echo "   Recent error messages:"
    tail -20 "$LOG_DIR/errors.log" 2>/dev/null | \
        grep -o '"error_message":"[^"]*"' | \
        head -5 | sed 's/"error_message":"\(.*\)"/      - \1/' || \
        echo "   (No recent errors)"
    
    ERROR_COUNT=$((ERROR_COUNT + ERROR_LINES))
else
    echo "1️⃣ errors.log not found"
fi

echo ""

# Analyze api.log for errors
if [ -f "$LOG_DIR/api.log" ]; then
    echo "2️⃣ Analyzing api.log for errors..."
    API_ERRORS=$(grep -i "error\|exception\|failed\|traceback" "$LOG_DIR/api.log" 2>/dev/null | wc -l | tr -d ' ')
    echo "   Error entries found: $API_ERRORS"
    
    if [ "$API_ERRORS" -gt 0 ]; then
        echo ""
        echo "   Recent errors:"
        grep -i "error\|exception\|failed" "$LOG_DIR/api.log" 2>/dev/null | \
            tail -5 | head -3 || echo "   (No recent errors)"
    fi
    
    ERROR_COUNT=$((ERROR_COUNT + API_ERRORS))
else
    echo "2️⃣ api.log not found"
fi

echo ""

# Analyze requests.log for failed requests
if [ -f "$LOG_DIR/requests.log" ]; then
    echo "3️⃣ Analyzing requests.log for failed requests..."
    FAILED_REQUESTS=$(grep -i '"status_code":[4-5][0-9][0-9]' "$LOG_DIR/requests.log" 2>/dev/null | wc -l | tr -d ' ')
    echo "   Failed requests (4xx/5xx): $FAILED_REQUESTS"
    
    if [ "$FAILED_REQUESTS" -gt 0 ]; then
        echo ""
        echo "   Recent failed requests:"
        grep -i '"status_code":[4-5][0-9][0-9]' "$LOG_DIR/requests.log" 2>/dev/null | \
            tail -5 | head -3 || echo "   (No recent failed requests)"
    fi
else
    echo "3️⃣ requests.log not found"
fi

echo ""

# Check for common error patterns
echo "4️⃣ Checking for common error patterns..."

# Network errors
NETWORK_ERRORS=$(grep -i "network\|connection\|refused\|timeout" "$LOG_DIR"/*.log 2>/dev/null | wc -l | tr -d ' ')
if [ "$NETWORK_ERRORS" -gt 0 ]; then
    echo "   ⚠️  Network errors found: $NETWORK_ERRORS"
    HIGH_COUNT=$((HIGH_COUNT + 1))
fi

# Import errors
IMPORT_ERRORS=$(grep -i "import.*error\|module.*not.*found\|no.*module" "$LOG_DIR"/*.log 2>/dev/null | wc -l | tr -d ' ')
if [ "$IMPORT_ERRORS" -gt 0 ]; then
    echo "   ⚠️  Import errors found: $IMPORT_ERRORS"
    MEDIUM_COUNT=$((MEDIUM_COUNT + 1))
fi

# Validation errors
VALIDATION_ERRORS=$(grep -i "validation\|invalid\|bad.*request" "$LOG_DIR"/*.log 2>/dev/null | wc -l | tr -d ' ')
if [ "$VALIDATION_ERRORS" -gt 0 ]; then
    echo "   ⚠️  Validation errors found: $VALIDATION_ERRORS"
    MEDIUM_COUNT=$((MEDIUM_COUNT + 1))
fi

# 500 errors
SERVER_ERRORS=$(grep -i '"status_code":5[0-9][0-9]' "$LOG_DIR"/*.log 2>/dev/null | wc -l | tr -d ' ')
if [ "$SERVER_ERRORS" -gt 0 ]; then
    echo "   ⚠️  Server errors (5xx) found: $SERVER_ERRORS"
    CRITICAL_COUNT=$((CRITICAL_COUNT + 1))
fi

# 404 errors
NOT_FOUND_ERRORS=$(grep -i '"status_code":404' "$LOG_DIR"/*.log 2>/dev/null | wc -l | tr -d ' ')
if [ "$NOT_FOUND_ERRORS" -gt 0 ]; then
    echo "   ⚠️  Not found errors (404) found: $NOT_FOUND_ERRORS"
    MEDIUM_COUNT=$((MEDIUM_COUNT + 1))
fi

echo ""

# Summary
echo "═══════════════════════════════════════════════════════════════"
echo "📊 Error Summary"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Total error entries: $ERROR_COUNT"
echo "Critical errors: $CRITICAL_COUNT"
echo "High severity: $HIGH_COUNT"
echo "Medium severity: $MEDIUM_COUNT"
echo ""

# Generate error report
REPORT_FILE="ERROR_ANALYSIS_REPORT_$(date +%Y%m%d_%H%M%S).txt"
{
    echo "Error Analysis Report"
    echo "Generated: $(date)"
    echo ""
    echo "Total Errors: $ERROR_COUNT"
    echo "Critical: $CRITICAL_COUNT"
    echo "High: $HIGH_COUNT"
    echo "Medium: $MEDIUM_COUNT"
    echo ""
    echo "Network Errors: $NETWORK_ERRORS"
    echo "Import Errors: $IMPORT_ERRORS"
    echo "Validation Errors: $VALIDATION_ERRORS"
    echo "Server Errors (5xx): $SERVER_ERRORS"
    echo "Not Found (404): $NOT_FOUND_ERRORS"
    echo ""
    echo "Full report saved to: $REPORT_FILE"
} > "$REPORT_FILE"

echo "✅ Error analysis complete!"
echo "📄 Full report saved to: $REPORT_FILE"
echo ""
echo "💡 Next steps:"
echo "   1. Review the report: cat $REPORT_FILE"
echo "   2. Check specific errors: ./view_logs.sh error"
echo "   3. Search for patterns: ./search_logs.sh 'error_pattern'"
echo "   4. Update ERROR_TRACKER.md with new errors"
echo ""

