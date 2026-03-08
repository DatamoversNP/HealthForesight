#!/bin/bash
# Kill process on port 8000
echo "Finding process on port 8000..."
PID=$(lsof -ti :8000)
if [ -z "$PID" ]; then
    echo "No process found on port 8000"
else
    echo "Killing process $PID on port 8000..."
    kill -9 $PID
    sleep 1
    echo "✅ Port 8000 is now free"
fi

