#!/bin/bash
# Start database and fix connection issues

set -e

echo "================================================================================"
echo "DATABASE SETUP AND FIX"
echo "================================================================================"
echo ""

# Step 1: Check if PostgreSQL container is running
echo "Step 1: Checking PostgreSQL container..."
if docker ps | grep -q uepi-postgres; then
    echo "✅ PostgreSQL container is running"
else
    echo "⚠️  PostgreSQL container is not running"
    echo "   Starting PostgreSQL..."
    docker-compose up -d postgres
    echo "   Waiting for PostgreSQL to be ready..."
    sleep 5
    
    # Wait for health check
    for i in {1..30}; do
        if docker exec uepi-postgres pg_isready -U uepi > /dev/null 2>&1; then
            echo "✅ PostgreSQL is ready!"
            break
        fi
        echo "   Waiting... ($i/30)"
        sleep 1
    done
fi

echo ""
echo "Step 2: Testing database connection..."
python3 scripts/fix_database_connection.py

echo ""
echo "================================================================================"
echo "NEXT STEPS"
echo "================================================================================"
echo ""
echo "If database connection is successful but no data exists:"
echo "1. Run database migrations (if needed)"
echo "2. Import/seed initial data"
echo "3. Restart API server"
echo ""
echo "If database connection failed:"
echo "1. Check docker-compose logs: docker-compose logs postgres"
echo "2. Verify password in config matches docker-compose.yml"
echo "3. Check if port 5432 is available"
echo ""
