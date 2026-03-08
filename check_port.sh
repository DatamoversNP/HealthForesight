#!/bin/bash
# Check what's using port 8000
echo "Checking what's using port 8000..."
lsof -i :8000 || echo "No process found on port 8000"

