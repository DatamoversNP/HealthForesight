#!/bin/bash
# Complete all analyses and create observations - DO EVERYTHING

echo "============================================================"
echo "COMPLETE ALL ANALYSES AND CREATE OBSERVATIONS"
echo "============================================================"
echo ""
echo "⚠️  IMPORTANT: The API server must be restarted first!"
echo "   Stop the API server (Ctrl+C), then restart it."
echo ""
echo "After restarting, run this script again, or run:"
echo ""
echo "  curl -X POST http://localhost:8000/api/v1/observations/create-all-from-pending-analyses \\"
echo "    -H 'Authorization: Bearer dev-token-123'"
echo ""
echo "This will:"
echo "  1. Complete all 38 pending analyses"
echo "  2. Create observations for all policies"
echo "  3. Observations will appear in UI immediately!"
echo ""
echo "============================================================"

# Try the endpoint
response=$(curl -s -X POST "http://localhost:8000/api/v1/observations/create-all-from-pending-analyses" \
  -H "Authorization: Bearer dev-token-123" \
  -H "Content-Type: application/json")

if echo "$response" | grep -q "Method Not Allowed"; then
    echo ""
    echo "❌ API server needs to be restarted!"
    echo "   The new endpoint is not loaded yet."
    echo ""
    echo "Please:"
    echo "  1. Restart your API server"
    echo "  2. Run this script again"
    exit 1
elif echo "$response" | grep -q "observations_created"; then
    echo ""
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    echo ""
    echo "✅ SUCCESS! Observations created!"
    echo "   Refresh the web page to see them!"
else
    echo ""
    echo "Response:"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
fi
