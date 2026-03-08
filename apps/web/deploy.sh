#!/bin/bash

# HealthForesight Marketing Website Deployment Script
# This script builds and prepares the marketing website for deployment

set -e  # Exit on error

echo "🚀 HealthForesight Marketing Website - Deployment Script"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script from apps/web directory."
    exit 1
fi

echo -e "${BLUE}📦 Step 1: Installing dependencies...${NC}"
npm install

echo -e "${BLUE}🔨 Step 2: Building marketing website...${NC}"
npm run build:marketing

if [ ! -d "dist-marketing" ]; then
    echo "❌ Error: Build failed - dist-marketing directory not found."
    exit 1
fi

echo -e "${GREEN}✅ Build successful!${NC}"
echo ""
echo -e "${YELLOW}📁 Build output: apps/web/dist-marketing${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. For Vercel: Run 'vercel --prod' from this directory"
echo "2. For Netlify: Run 'netlify deploy --prod' from this directory"
echo "3. For manual deployment: Upload 'dist-marketing' folder contents to your hosting"
echo ""
echo -e "${GREEN}✨ Ready to deploy!${NC}"
