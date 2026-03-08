#!/bin/bash
# Stop the observation monitor

PID_FILE="/tmp/observation_monitor.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "⚠️  Monitor is not running (no PID file found)"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "⚠️  Monitor is not running (PID $PID not found)"
    rm -f "$PID_FILE"
    exit 1
fi

echo "🛑 Stopping observation monitor (PID: $PID)..."
kill "$PID"
rm -f "$PID_FILE"
echo "✅ Monitor stopped"
