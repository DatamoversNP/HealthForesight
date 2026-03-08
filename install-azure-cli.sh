#!/bin/bash
# Install Azure CLI on macOS

set -e

echo "🔧 Installing Azure CLI on macOS"
echo "================================"
echo ""

# Check if already installed
if command -v az &> /dev/null; then
    echo "✅ Azure CLI is already installed!"
    az --version
    exit 0
fi

echo "Select installation method:"
echo "1. Homebrew (Recommended - easiest)"
echo "2. Direct download (macOS installer)"
echo "3. Python pip"
echo ""
read -p "Enter choice [1]: " INSTALL_METHOD
INSTALL_METHOD=${INSTALL_METHOD:-1}

case $INSTALL_METHOD in
    1)
        echo ""
        echo "📦 Installing via Homebrew..."
        
        # Check if Homebrew is installed
        if ! command -v brew &> /dev/null; then
            echo "⚠️  Homebrew not found. Installing Homebrew first..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            
            # Add Homebrew to PATH for Apple Silicon Macs
            if [ -f "/opt/homebrew/bin/brew" ]; then
                echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
                eval "$(/opt/homebrew/bin/brew shellenv)"
            fi
        fi
        
        echo "Installing Azure CLI..."
        brew install azure-cli
        
        echo ""
        echo "✅ Azure CLI installed via Homebrew!"
        ;;
    
    2)
        echo ""
        echo "📦 Installing via macOS installer..."
        
        # Download and run installer
        curl -L https://aka.ms/InstallAzureCLIMacOS | bash
        
        # Add to PATH if needed
        if [ -d "/usr/local/bin" ]; then
            export PATH="/usr/local/bin:$PATH"
        fi
        
        echo ""
        echo "✅ Azure CLI installed via installer!"
        ;;
    
    3)
        echo ""
        echo "📦 Installing via pip..."
        
        # Check if pip is available
        if ! command -v pip3 &> /dev/null; then
            echo "❌ pip3 not found. Please install Python first."
            exit 1
        fi
        
        pip3 install azure-cli
        
        echo ""
        echo "✅ Azure CLI installed via pip!"
        ;;
    
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🔍 Verifying installation..."
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
echo ""


