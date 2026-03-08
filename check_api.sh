#!/bin/bash
# Quick check: is the API responding?
# Usage: ./check_api.sh

set -e
URL="${1:-http://localhost:8000}"
echo "Checking API at $URL ..."
if curl -s -f -m 5 "$URL/health" > /dev/null 2>&1; then
  echo "✅ API is up. Health: $URL/health"
  curl -s "$URL/health" | head -5
  exit 0
fi
if curl -s -f -m 5 "$URL/api/v1/health" > /dev/null 2>&1; then
  echo "✅ API is up. Health: $URL/api/v1/health"
  curl -s "$URL/api/v1/health" | head -5
  exit 0
fi
echo "❌ API is not responding at $URL"
echo "   Start it with: ./start_api_and_worker.sh api"
exit 1
