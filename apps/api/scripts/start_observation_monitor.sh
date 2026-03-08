#!/bin/bash
# Start the observation monitor in the background
# This will automatically create observations when analyses complete

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../../.." && pwd )"
LOG_FILE="/tmp/observation_monitor.log"
PID_FILE="/tmp/observation_monitor.pid"

cd "$PROJECT_ROOT"

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  Monitor is already running (PID: $OLD_PID)"
        echo "   To stop it: kill $OLD_PID"
        echo "   Or run: ./stop_observation_monitor.sh"
        exit 1
    fi
fi

# Start monitor
echo "🚀 Starting observation monitor..."
echo "   Log file: $LOG_FILE"
echo "   This will check every 30 seconds and create observations automatically"
echo "   Press Ctrl+C or run ./stop_observation_monitor.sh to stop"

nohup python3 "$SCRIPT_DIR/monitor_and_create_observations.py" > "$LOG_FILE" 2>&1 &
MONITOR_PID=$!

echo "$MONITOR_PID" > "$PID_FILE"
echo "✅ Monitor started (PID: $MONITOR_PID)"
echo ""
echo "To check status:"
echo "   tail -f $LOG_FILE"
echo ""
echo "To stop:"
echo "   kill $MONITOR_PID"
echo "   Or: ./stop_observation_monitor.sh"
