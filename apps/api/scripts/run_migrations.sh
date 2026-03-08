#!/bin/bash
# Script to run Alembic migrations

set -e

cd "$(dirname "$0")/.."

echo "🔨 Running Alembic migrations..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set"
    echo "   Set DATABASE_URL environment variable, e.g.:"
    echo "   export DATABASE_URL='postgresql://user:password@localhost:5432/uepi_db'"
    exit 1
fi

# Check if USE_FILE_STORAGE is set to false
if [ "$USE_FILE_STORAGE" != "false" ] && [ -z "$USE_FILE_STORAGE" ]; then
    echo "⚠️  USE_FILE_STORAGE not set to false"
    echo "   Set USE_FILE_STORAGE=false to enable database mode"
    echo "   export USE_FILE_STORAGE=false"
    exit 1
fi

# Run migrations
alembic upgrade head

echo "✅ Migrations completed successfully!"

