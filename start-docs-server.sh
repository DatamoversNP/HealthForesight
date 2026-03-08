#!/bin/bash
# Start Documentation Portal Server on port 3051

cd "$(dirname "$0")/apps/web"

echo "🚀 Starting Documentation Portal on port 3051..."
echo "📚 Access documentation at: http://localhost:3051"
echo ""
echo "Starting Vite dev server..."

# Use the docs config which sets port to 3051
npm run dev:docs
