#!/bin/bash
# Check Azure CLI Installation Status

echo "🔍 Checking Azure CLI Installation Status"
echo "=========================================="
echo ""

# Check if az command exists
if command -v az &> /dev/null; then
    echo "✅ Azure CLI is INSTALLED"
    echo ""
    echo "📍 Location: $(which az)"
    echo ""
    echo "📋 Version Information:"
    az --version | head -3
    echo ""
    
    # Check if logged in
    if az account show &>/dev/null; then
        echo "✅ Logged in to Azure"
        echo ""
        echo "📋 Current Subscription:"
        az account show --query "{Name:name, SubscriptionId:id}" -o table
    else
        echo "⚠️  Not logged in to Azure"
        echo ""
        echo "To login, run:"
        echo "  az login"
    fi
else
    echo "❌ Azure CLI is NOT INSTALLED"
    echo ""
    
    # Check common installation locations
    echo "🔍 Checking common installation locations..."
    
    if [ -f "/opt/homebrew/bin/az" ]; then
        echo "  ⚠️  Found in /opt/homebrew/bin/az but not in PATH"
        echo "  Add to PATH: export PATH=\"/opt/homebrew/bin:\$PATH\""
    elif [ -f "/usr/local/bin/az" ]; then
        echo "  ⚠️  Found in /usr/local/bin/az but not in PATH"
        echo "  Add to PATH: export PATH=\"/usr/local/bin:\$PATH\""
    else
        echo "  ❌ Not found in common locations"
    fi
    
    echo ""
    echo "📝 To install Azure CLI, run:"
    echo "  ./install-azure-cli.sh"
    echo ""
    echo "Or install manually:"
    echo "  brew install azure-cli"
    echo "  (if you have Homebrew)"
fi

echo ""


