#!/bin/bash

# HealthForesight Marketing Website - Quick Deploy Script
# This script helps you deploy to Vercel

set -e

echo "🚀 HealthForesight Marketing Website - Vercel Deployment"
echo "=================================================="
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from apps/web directory"
    exit 1
fi

# Check if build exists
if [ ! -d "dist-marketing" ]; then
    echo "📦 Building marketing website first..."
    npm run build:marketing
    echo ""
fi

echo "✅ Build ready!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Install Vercel CLI (if not installed):"
echo "   npm install -g vercel"
echo "   OR use npx (no install needed):"
echo "   npx vercel --prod"
echo ""
echo "2. Login to Vercel:"
echo "   vercel login"
echo "   OR"
echo "   npx vercel login"
echo ""
echo "3. Deploy to production:"
echo "   vercel --prod"
echo "   OR"
echo "   npx vercel --prod"
echo ""
echo "🌐 Alternative: Deploy via GitHub"
echo "   1. Push code to GitHub"
echo "   2. Go to https://vercel.com"
echo "   3. Import repository"
echo "   4. Set root: apps/web"
echo "   5. Build: npm run build:marketing"
echo "   6. Output: dist-marketing"
echo ""

# Try to use npx if available
if command -v npx &> /dev/null; then
    echo "💡 Tip: You can use 'npx vercel' without installing globally!"
    echo ""
    read -p "Would you like to deploy now using npx? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚀 Starting deployment..."
        npx vercel --prod
    fi
else
    echo "⚠️  npx not found. Please install Node.js or use 'npm install -g vercel'"
fi
