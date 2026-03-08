#!/bin/bash
# Script to find pg_hba.conf file

echo "🔍 Searching for pg_hba.conf..."
echo ""

# Method 1: Try to query PostgreSQL directly
export PATH="/usr/local/opt/postgresql@15/bin:/opt/homebrew/opt/postgresql@15/bin:$PATH"

if command -v psql &> /dev/null; then
    echo "Method 1: Querying PostgreSQL..."
    PG_HBA=$(psql -U postgres -d postgres -t -c "SHOW hba_file;" 2>/dev/null | xargs)
    if [ -f "$PG_HBA" ]; then
        echo "✅ Found: $PG_HBA"
        echo ""
        exit 0
    fi
fi

# Method 2: Check common Homebrew locations
echo "Method 2: Checking common Homebrew locations..."
for path in \
    "/usr/local/var/postgresql@15/pg_hba.conf" \
    "/opt/homebrew/var/postgresql@15/pg_hba.conf" \
    "/usr/local/var/postgres/pg_hba.conf" \
    "/opt/homebrew/var/postgres/pg_hba.conf" \
    "$(brew --prefix postgresql@15 2>/dev/null)/var/pg_hba.conf" \
    "$(brew --prefix postgresql 2>/dev/null)/var/pg_hba.conf"; do
    if [ -f "$path" ]; then
        echo "✅ Found: $path"
        echo ""
        exit 0
    fi
done

# Method 3: Search in common var directories
echo "Method 3: Searching in common var directories..."
for dir in "/usr/local/var" "/opt/homebrew/var" "/var/lib/postgresql" "/var/lib/postgres"; do
    if [ -d "$dir" ]; then
        FOUND=$(find "$dir" -name "pg_hba.conf" 2>/dev/null | head -1)
        if [ -n "$FOUND" ] && [ -f "$FOUND" ]; then
            echo "✅ Found: $FOUND"
            echo ""
            exit 0
        fi
    fi
done

# Method 4: Check if PostgreSQL is running and get data directory
echo "Method 4: Checking PostgreSQL data directory..."
if command -v psql &> /dev/null; then
    DATA_DIR=$(psql -U postgres -d postgres -t -c "SHOW data_directory;" 2>/dev/null | xargs)
    if [ -n "$DATA_DIR" ] && [ -f "$DATA_DIR/pg_hba.conf" ]; then
        echo "✅ Found: $DATA_DIR/pg_hba.conf"
        echo ""
        exit 0
    fi
fi

# Method 5: Check running PostgreSQL process
echo "Method 5: Checking running PostgreSQL process..."
PG_PID=$(pgrep -f "postgres.*-D" | head -1)
if [ -n "$PG_PID" ]; then
    PG_CMD=$(ps -p "$PG_PID" -o command= 2>/dev/null)
    if echo "$PG_CMD" | grep -q "\-D"; then
        DATA_DIR=$(echo "$PG_CMD" | grep -o "\-D [^ ]*" | cut -d' ' -f2)
        if [ -n "$DATA_DIR" ] && [ -f "$DATA_DIR/pg_hba.conf" ]; then
            echo "✅ Found: $DATA_DIR/pg_hba.conf"
            echo ""
            exit 0
        fi
    fi
fi

echo "❌ Could not find pg_hba.conf automatically"
echo ""
echo "Try these commands manually:"
echo "  export PATH=\"/usr/local/opt/postgresql@15/bin:\$PATH\""
echo "  psql -U postgres -d postgres -c \"SHOW hba_file;\""
echo "  psql -U postgres -d postgres -c \"SHOW data_directory;\""
echo ""
echo "Or check if PostgreSQL is running:"
echo "  brew services list | grep postgresql"
echo "  ps aux | grep postgres"

