#!/bin/bash
# Direct Azure CLI Installation for macOS
# Uses Homebrew with a workaround or pip

set -e

echo "🚀 Azure CLI Installation for macOS"
echo "===================================="
echo ""

# Check if already installed
if command -v az &> /dev/null; then
    echo "✅ Azure CLI is already installed!"
    az --version
    exit 0
fi

echo "Installation methods:"
echo "1. Python pip (Recommended - fastest, ~2-3 minutes)"
echo "2. Homebrew (will take 30-60 minutes for LLVM compilation)"
echo ""
read -p "Enter choice [1]: " INSTALL_METHOD
INSTALL_METHOD=${INSTALL_METHOD:-1}

case $INSTALL_METHOD in
    1)
        echo ""
        echo "📦 Installing via pip..."
        
        # Check Python
        if ! command -v python3 &> /dev/null; then
            echo "❌ python3 not found. Installing Python..."
            if command -v brew &> /dev/null; then
                brew install python3
            else
                echo "❌ Please install Python first: https://www.python.org/downloads/"
                exit 1
            fi
        fi
        
        echo "Python version: $(python3 --version)"
        echo ""
        echo "Installing Azure CLI via pip..."
        echo "This will take 2-3 minutes..."
        
        pip3 install --upgrade pip
        pip3 install azure-cli
        
        # Add to PATH if installed in user directory
        if [ -d "$HOME/Library/Python" ]; then
            PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
            if [ -d "$HOME/Library/Python/$PYTHON_VERSION/bin" ]; then
                export PATH="$HOME/Library/Python/$PYTHON_VERSION/bin:$PATH"
                echo ""
                echo "⚠️  Add to your ~/.zshrc or ~/.bash_profile:"
                echo "   export PATH=\"\$HOME/Library/Python/$PYTHON_VERSION/bin:\$PATH\""
            fi
        fi
        
        echo ""
        echo "✅ Azure CLI installed via pip!"
        ;;
    
    2)
        echo ""
        echo "📦 Installing via Homebrew..."
        echo "⚠️  This will take 30-60 minutes due to LLVM compilation"
        echo ""
        read -p "Continue? (y/n): " CONFIRM
        if [ "$CONFIRM" != "y" ]; then
            echo "Cancelled."
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

# Check multiple locations
FOUND=false

if command -v az &> /dev/null; then
    FOUND=true
elif [ -f "/usr/local/bin/az" ]; then
    export PATH="/usr/local/bin:$PATH"
    FOUND=true
elif [ -f "/opt/homebrew/bin/az" ]; then
    export PATH="/opt/homebrew/bin:$PATH"
    FOUND=true
elif [ -d "$HOME/Library/Python" ]; then
    for PYTHON_DIR in "$HOME/Library/Python"/*/bin; do
        if [ -f "$PYTHON_DIR/az" ]; then
            export PATH="$PYTHON_DIR:$PATH"
            FOUND=true
            break
        fi
    done
fi

if [ "$FOUND" = true ]; then
    echo "✅ Azure CLI found!"
    echo ""
    az --version
    echo ""
    echo "✅ Installation complete!"
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
    echo "Try these commands to add to PATH:"
    echo ""
    
    if [ -d "$HOME/Library/Python" ]; then
        for PYTHON_DIR in "$HOME/Library/Python"/*/bin; do
            if [ -f "$PYTHON_DIR/az" ]; then
                echo "export PATH=\"$PYTHON_DIR:\$PATH\""
                echo ""
                echo "Add this to ~/.zshrc:"
                echo "echo 'export PATH=\"$PYTHON_DIR:\$PATH\"' >> ~/.zshrc"
                echo "source ~/.zshrc"
            fi
        done
    fi
    
    echo ""
    echo "Or restart your terminal and try:"
    echo "  az --version"
fi

echo ""


