#!/bin/bash
# Install Node.js and npm on macOS

echo "🔧 Installing Node.js and npm"
echo "==============================="
echo ""

# Check if already installed
if command -v node &> /dev/null && command -v npm &> /dev/null; then
    echo "✅ Node.js and npm are already installed!"
    echo ""
    node --version
    npm --version
    exit 0
fi

echo "Select installation method:"
echo "1. Homebrew (Recommended - easiest)"
echo "2. Official installer (Download from nodejs.org)"
echo "3. nvm - Node Version Manager (Best for managing versions)"
echo ""
read -p "Enter choice [1]: " INSTALL_METHOD
INSTALL_METHOD=${INSTALL_METHOD:-1}

case $INSTALL_METHOD in
    1)
        echo ""
        echo "📦 Installing via Homebrew..."
        
        if ! command -v brew &> /dev/null; then
            echo "⚠️  Homebrew not found. Installing Homebrew first..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        brew install node
        echo ""
        echo "✅ Node.js and npm installed via Homebrew!"
        ;;
    
    2)
        echo ""
        echo "📦 Installing via official installer..."
        echo "   Opening download page..."
        
        # Open download page
        if command -v open &> /dev/null; then
            open "https://nodejs.org/en/download/"
        else
            echo "   Please visit: https://nodejs.org/en/download/"
            echo "   Download and install the macOS installer"
        fi
        
        echo ""
        echo "⚠️  Please download and install Node.js from the browser"
        echo "   Then restart your terminal and verify: node --version"
        exit 0
        ;;
    
    3)
        echo ""
        echo "📦 Installing via nvm (Node Version Manager)..."
        
        # Install nvm
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
        
        # Load nvm
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        
        # Install latest LTS Node.js
        nvm install --lts
        nvm use --lts
        
        echo ""
        echo "✅ Node.js and npm installed via nvm!"
        echo ""
        echo "💡 Add to your ~/.zshrc:"
        echo "   export NVM_DIR=\"\$HOME/.nvm\""
        echo "   [ -s \"\$NVM_DIR/nvm.sh\" ] && \. \"\$NVM_DIR/nvm.sh\""
        ;;
    
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🔍 Verifying installation..."

if command -v node &> /dev/null && command -v npm &> /dev/null; then
    echo "✅ Installation successful!"
    echo ""
    node --version
    npm --version
    echo ""
    echo "📝 Next steps:"
    echo "   You can now run: ./deploy-to-azure-free-tier.sh"
else
    echo "⚠️  Installation may need terminal restart"
    echo ""
    echo "Try:"
    echo "   source ~/.zshrc"
    echo "   node --version"
fi

echo ""


