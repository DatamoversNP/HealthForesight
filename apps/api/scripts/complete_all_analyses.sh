#!/bin/bash
# Complete all pending analyses and create observations

echo "🚀 Completing all pending analyses..."
echo ""

# Call the API endpoint
response=$(curl -s -X POST "http://localhost:8000/api/v1/analyses/complete-all-pending" \
  -H "Authorization: Bearer dev-token-123" \
  -H "Content-Type: application/json")

echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"

echo ""
echo "✅ Done! Monitor will create observations automatically."
echo "   Check status: cd apps/api/scripts && ./check_status.sh"
echo "   Watch monitor: tail -f /tmp/observation_monitor.log"
