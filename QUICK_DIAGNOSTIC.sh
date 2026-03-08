#!/bin/bash
# Quick diagnostic script to check database connection issues

echo "=========================================="
echo "Database Connection Diagnostic"
echo "=========================================="
echo ""

echo "1. Checking if PostgreSQL is running..."
if pgrep -x "postgres" > /dev/null; then
    echo "   ✅ PostgreSQL process is running"
else
    echo "   ❌ PostgreSQL process is NOT running"
    echo "   → This is likely the problem!"
    echo "   → Start PostgreSQL: docker-compose up -d postgres"
    echo "   → OR: brew services start postgresql@15"
fi
echo ""

echo "2. Checking if port 5432 is listening..."
if lsof -i :5432 > /dev/null 2>&1; then
    echo "   ✅ Port 5432 is listening"
    lsof -i :5432 | head -3
else
    echo "   ❌ Port 5432 is NOT listening"
    echo "   → PostgreSQL might not be running or listening on different port"
fi
echo ""

echo "3. Testing database connection..."
export PGPASSWORD=postgres
if psql -h localhost -U postgres -d uepi_db -c "SELECT 1;" > /dev/null 2>&1; then
    echo "   ✅ Database connection successful!"
    echo "   → Connection string is correct"
    echo "   → Database is accessible"
else
    echo "   ❌ Database connection FAILED"
    echo "   → Check connection string in packages/common/src/uepi_common/config.py"
    echo "   → Current: postgresql://postgres:postgres@localhost:5432/uepi_db"
    echo "   → Try manually: psql -h localhost -U postgres -d uepi_db"
fi
echo ""

echo "4. Checking database tables..."
if psql -h localhost -U postgres -d uepi_db -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" > /dev/null 2>&1; then
    TABLE_COUNT=$(psql -h localhost -U postgres -d uepi_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)
    echo "   ✅ Found $TABLE_COUNT tables in database"
else
    echo "   ⚠️  Could not check tables (connection issue)"
fi
echo ""

echo "=========================================="
echo "Summary"
echo "=========================================="
echo "If PostgreSQL is not running, that's why you're getting timeouts."
echo "The timeouts have NOTHING to do with data volume - it's a connection issue."
echo ""
echo "Next steps:"
echo "1. Start PostgreSQL (if not running)"
echo "2. Restart API server"
echo "3. Refresh frontend"
