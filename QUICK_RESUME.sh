#!/bin/bash
# Quick resume script - run this when you come back

echo "=========================================="
echo "  HealthForesight Azure Deployment"
echo "  Quick Resume Script"
echo "=========================================="
echo ""

echo "Step 1: Checking current status..."
./verify_and_stop_all.sh

echo ""
echo "=========================================="
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. If everything is stopped ✅, you can:"
echo "   - Continue with Docker deployment: ./FIX_ACR_SIMPLE.sh"
echo "   - Or review CURRENT_STATUS.md for options"
echo ""
echo "2. If services are running, costs are accruing!"
echo "   - Run: ./STOP_ALL_AZURE_SERVICES.sh"
echo ""
echo "3. Review status document:"
echo "   - cat CURRENT_STATUS.md"
echo ""
echo "=========================================="
