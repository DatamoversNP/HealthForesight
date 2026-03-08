#!/bin/bash
# DO THIS NOW - Complete all analyses and create observations

echo "============================================================"
echo "CREATE ALL OBSERVATIONS - DO THIS NOW"
echo "============================================================"
echo ""
echo "STEP 1: Restart your API server"
echo "   - Stop it (Ctrl+C in the terminal where it's running)"
echo "   - Start it again (use your normal startup command)"
echo ""
echo "STEP 2: After restart, run this command:"
echo ""
echo "   curl -X POST http://localhost:8000/api/v1/observations/create-all-from-pending-analyses \\"
echo "     -H 'Authorization: Bearer dev-token-123'"
echo ""
echo "OR run this script again after restarting:"
echo ""
echo "   ./DO_THIS_NOW.sh"
echo ""
echo "============================================================"
echo ""

# Try the endpoint
response=$(curl -s -X POST "http://localhost:8000/api/v1/observations/create-all-from-pending-analyses" \
  -H "Authorization: Bearer dev-token-123" \
  -H "Content-Type: application/json")

if echo "$response" | grep -q "Method Not Allowed\|404\|405"; then
    echo "❌ API server needs to be restarted first!"
    echo ""
    echo "Please:"
    echo "  1. Restart your API server"
    echo "  2. Run this script again"
    exit 1
elif echo "$response" | grep -q "observations_created"; then
    echo "✅ SUCCESS!"
    echo ""
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    echo ""
    echo "🎉 Observations created! Refresh the web page to see them!"
    exit 0
else
    echo "Response:"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
fi
