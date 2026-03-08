#!/bin/bash
# Setup Azure CLI PATH

echo "🔧 Setting up Azure CLI PATH"
echo "============================"
echo ""

# Find Azure CLI installation
AZ_PATH=""

# Check common locations
if [ -f "/Library/Frameworks/Python.framework/Versions/3.13/bin/az" ]; then
    AZ_PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin"
elif [ -f "/usr/local/bin/az" ]; then
    AZ_PATH="/usr/local/bin"
elif [ -f "/opt/homebrew/bin/az" ]; then
    AZ_PATH="/opt/homebrew/bin"
elif [ -d "$HOME/Library/Python" ]; then
    for PYTHON_DIR in "$HOME/Library/Python"/*/bin; do
        if [ -f "$PYTHON_DIR/az" ]; then
            AZ_PATH="$PYTHON_DIR"
            break
        fi
    done
fi

if [ -z "$AZ_PATH" ]; then
    echo "❌ Azure CLI not found. Please install it first."
    echo "   Run: pip3 install azure-cli"
    exit 1
fi

echo "✅ Found Azure CLI at: $AZ_PATH/az"
echo ""

# Add to PATH for current session
export PATH="$AZ_PATH:$PATH"

# Verify it works
if command -v az &> /dev/null; then
    echo "✅ Azure CLI is now accessible!"
    echo ""
    az --version | head -3
    echo ""
    
    # Add to shell profile
    SHELL_PROFILE=""
    if [ -f "$HOME/.zshrc" ]; then
        SHELL_PROFILE="$HOME/.zshrc"
    elif [ -f "$HOME/.bash_profile" ]; then
        SHELL_PROFILE="$HOME/.bash_profile"
    elif [ -f "$HOME/.profile" ]; then
        SHELL_PROFILE="$HOME/.profile"
    fi
    
    if [ -n "$SHELL_PROFILE" ]; then
        # Check if already added
        if ! grep -q "$AZ_PATH" "$SHELL_PROFILE" 2>/dev/null; then
            echo "📝 Adding to $SHELL_PROFILE..."
            echo "" >> "$SHELL_PROFILE"
            echo "# Azure CLI" >> "$SHELL_PROFILE"
            echo "export PATH=\"$AZ_PATH:\$PATH\"" >> "$SHELL_PROFILE"
            echo "✅ Added to $SHELL_PROFILE"
            echo ""
            echo "💡 Restart your terminal or run:"
            echo "   source $SHELL_PROFILE"
        else
            echo "✅ Already in $SHELL_PROFILE"
        fi
    fi
    
    echo ""
    echo "📝 Next steps:"
    echo "1. Login to Azure:"
    echo "   az login"
    echo ""
    echo "2. Run deployment:"
    echo "   ./deploy-complete-to-azure.sh"
else
    echo "⚠️  Azure CLI found but not accessible. Try:"
    echo "   export PATH=\"$AZ_PATH:\$PATH\""
    echo "   az --version"
fi

echo ""


