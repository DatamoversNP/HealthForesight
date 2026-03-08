#!/bin/bash
# Script to install dependencies and create database

set -e

echo "🔧 Setting up database..."

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Please run this script from apps/api directory"
    exit 1
fi

# Install psycopg2-binary if not installed
echo "📦 Installing psycopg2-binary..."
pip3 install psycopg2-binary

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set"
    echo "   Set DATABASE_URL environment variable, e.g.:"
    echo "   export DATABASE_URL='postgresql://user:password@localhost:5432/uepi_db'"
    exit 1
fi

# Check if USE_FILE_STORAGE is set to false
if [ "$USE_FILE_STORAGE" != "false" ]; then
    echo "⚠️  USE_FILE_STORAGE not set to false"
    echo "   Setting USE_FILE_STORAGE=false..."
    export USE_FILE_STORAGE="false"
fi

echo "✅ Dependencies installed"
echo ""
echo "🔨 Creating database tables..."

# Run Alembic migrations (recommended)
if command -v alembic &> /dev/null; then
    echo "📝 Running Alembic migrations..."
    alembic upgrade head
    echo "✅ Database tables created via Alembic!"
else
    echo "⚠️  Alembic not found, using init_db()..."
    python3 -c "
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, '../../packages/common/src')
from uepi_api.database import init_db
init_db()
print('✅ Database tables created!')
"
fi

echo ""
echo "🎉 Database setup complete!"

