#!/bin/bash
# Fast Azure CLI Installation (Avoids long LLVM compilation)

set -e

echo "🚀 Fast Azure CLI Installation"
echo "=============================="
echo ""
echo "This method avoids the long LLVM compilation by using pre-built binaries."
echo ""

# Check if already installed
if command -v az &> /dev/null; then
    echo "✅ Azure CLI is already installed!"
    az --version
    exit 0
fi

echo "Select fast installation method:"
echo "1. macOS Installer (Recommended - fastest, ~2 minutes)"
echo "2. Python pip (Fast, if you have Python)"
echo "3. Continue with Homebrew (will take 30-60 minutes)"
echo ""
read -p "Enter choice [1]: " INSTALL_METHOD
INSTALL_METHOD=${INSTALL_METHOD:-1}

case $INSTALL_METHOD in
    1)
        echo ""
        echo "📦 Installing via macOS installer (fastest method)..."
        echo "   This downloads pre-built binaries (~2 minutes)"
        echo ""
        
        # Download and run installer
        curl -L https://aka.ms/InstallAzureCLIMacOS | bash
        
        # Add to PATH if needed
        if [ -d "/usr/local/bin" ]; then
            export PATH="/usr/local/bin:$PATH"
        fi
        
        # Also check /usr/local/az/bin
        if [ -d "/usr/local/az/bin" ]; then
            export PATH="/usr/local/az/bin:$PATH"
        fi
        
        echo ""
        echo "✅ Azure CLI installed!"
        ;;
    
    2)
        echo ""
        echo "📦 Installing via pip..."
        
        # Check if pip is available
        if ! command -v pip3 &> /dev/null; then
            echo "❌ pip3 not found. Please install Python first."
            exit 1
        fi
        
        echo "Installing Azure CLI via pip..."
        pip3 install azure-cli
        
        echo ""
        echo "✅ Azure CLI installed via pip!"
        ;;
    
    3)
        echo ""
        echo "📦 Continuing with Homebrew installation..."
        echo "   This will take 30-60 minutes..."
        echo "   Press Ctrl+C to cancel and use a faster method"
        echo ""
        read -p "Continue? (y/n): " CONFIRM
        if [ "$CONFIRM" != "y" ]; then
            echo "Cancelled. Run this script again and choose option 1 or 2."
            exit 0
        fi
        
        brew install azure-cli
        ;;
    
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🔍 Verifying installation..."

# Try to find az in common locations
if command -v az &> /dev/null; then
    az --version
    echo ""
    echo "✅ Azure CLI installation complete!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Login to Azure:"
    echo "   az login"
    echo ""
    echo "2. Run deployment script:"
    echo "   ./deploy-complete-to-azure.sh"
else
    echo "⚠️  Azure CLI installed but not in PATH"
    echo ""
    echo "Try adding to PATH:"
    echo "  export PATH=\"/usr/local/bin:\$PATH\""
    echo "  export PATH=\"/usr/local/az/bin:\$PATH\""
    echo ""
    echo "Or restart your terminal and try again."
fi

echo ""


