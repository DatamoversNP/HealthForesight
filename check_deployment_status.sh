#!/bin/bash
# Check if deployment completed and test the app

APP_NAME="hf-api8755146"
RESOURCE_GROUP="healthforesight-rg"

echo "=== Checking Deployment Status ==="
echo ""

# Wait a bit more for startup
echo "Waiting 30 more seconds for app to fully start..."
sleep 30

echo ""
echo "1. Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_NAME.azurewebsites.net/health 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ SUCCESS! App is responding!"
    echo ""
    echo "   Health check response:"
    curl -s https://$APP_NAME.azurewebsites.net/health
    echo ""
else
    echo "   ⚠️  HTTP Status: $HTTP_CODE"
    echo ""
    
    if [ "$HTTP_CODE" = "503" ] || [ "$HTTP_CODE" = "502" ]; then
        echo "   App might still be starting. Wait a bit more and try again."
    elif [ "$HTTP_CODE" = "500" ]; then
        echo "   App is running but has an error. Check logs:"
        echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
    else
        echo "   App not responding yet. Check logs:"
        echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
    fi
fi

echo ""
echo "2. Check app state:"
APP_STATE=$(az webapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query state -o tsv 2>/dev/null || echo "unknown")
echo "   App State: $APP_STATE"

echo ""
echo "=== Status Check Complete ==="
echo ""
echo "If the app is still not working, run:"
echo "  ./fix_final.sh"
echo ""
echo "Or check logs:"
echo "  az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
