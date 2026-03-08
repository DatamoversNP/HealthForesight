#!/bin/bash
# Find Node.js/npm installation
echo "🔍 Searching for Node.js and npm..."
echo ""

# Check common installation locations
LOCATIONS=(
    "/usr/local/bin"
    "/opt/homebrew/bin"
    "/usr/bin"
    "$HOME/.nvm/versions"
    "$HOME/.nodejs"
    "/Applications"
)

FOUND=false

for loc in "${LOCATIONS[@]}"; do
    if [ -d "$loc" ]; then
        if [ -f "$loc/node" ] || [ -f "$loc/npm" ]; then
            echo "✅ Found in: $loc"
            if [ -f "$loc/node" ]; then
                echo "   Node.js: $loc/node"
            fi
            if [ -f "$loc/npm" ]; then
                echo "   npm: $loc/npm"
            fi
            FOUND=true
        fi
    fi
done

# Check if installed via nvm
if [ -d "$HOME/.nvm" ]; then
    echo "✅ Found nvm installation in: $HOME/.nvm"
    echo "   Try: source ~/.nvm/nvm.sh"
    FOUND=true
fi

# Check if installed via Homebrew
if command -v brew &> /dev/null; then
    BREW_NODE=$(brew --prefix node 2>/dev/null)
    if [ -n "$BREW_NODE" ]; then
        echo "✅ Node.js installed via Homebrew"
        echo "   Location: $BREW_NODE"
        FOUND=true
    fi
fi

if [ "$FOUND" = false ]; then
    echo "❌ Node.js/npm not found in common locations"
    echo ""
    echo "To install Node.js:"
    echo "  1. Visit: https://nodejs.org/ and download the LTS version"
    echo "  2. Or use Homebrew: brew install node"
    echo "  3. Or use nvm: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
fi

echo ""
echo "Current PATH:"
echo "$PATH" | tr ':' '\n' | grep -E "(node|npm|nvm)" || echo "  (no node-related paths found)"

