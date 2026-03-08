#!/bin/bash
# Script to configure PostgreSQL authentication for local development

set -e

echo "🔧 Configuring PostgreSQL authentication..."

# Find PostgreSQL data directory - try multiple locations
PG_DATA=""
for path in "/usr/local/var/postgresql@15" "/opt/homebrew/var/postgresql@15" "$(brew --prefix postgresql@15)/var" 2>/dev/null; do
    if [ -d "$path" ]; then
        PG_DATA="$path"
        break
    fi
done

# If still not found, try to get from PostgreSQL
if [ -z "$PG_DATA" ] || [ ! -f "$PG_DATA/pg_hba.conf" ]; then
    # Try to find using psql if available
    export PATH="/usr/local/opt/postgresql@15/bin:$PATH"
    if command -v psql &> /dev/null; then
        PG_HBA_PATH=$(psql -U postgres -d postgres -t -c "SHOW hba_file;" 2>/dev/null | xargs)
        if [ -f "$PG_HBA_PATH" ]; then
            PG_HBA="$PG_HBA_PATH"
            PG_DATA=$(dirname "$PG_HBA_PATH")
        fi
    fi
fi

# Final check - use common locations
if [ -z "$PG_HBA" ] || [ ! -f "$PG_HBA" ]; then
    for path in "/usr/local/var/postgresql@15/pg_hba.conf" "/opt/homebrew/var/postgresql@15/pg_hba.conf"; do
        if [ -f "$path" ]; then
            PG_HBA="$path"
            PG_DATA=$(dirname "$path")
            break
        fi
    done
fi

echo "📝 PostgreSQL data directory: $PG_DATA"
echo "📝 Config file: $PG_HBA"

# Check if file exists
if [ ! -f "$PG_HBA" ]; then
    echo "❌ pg_hba.conf not found"
    echo ""
    echo "Please find it manually:"
    echo "  export PATH=\"/usr/local/opt/postgresql@15/bin:\$PATH\""
    echo "  psql -U postgres -d postgres -c \"SHOW hba_file;\""
    echo ""
    echo "Or edit manually at one of these locations:"
    echo "  /usr/local/var/postgresql@15/pg_hba.conf"
    echo "  /opt/homebrew/var/postgresql@15/pg_hba.conf"
    exit 1
fi

# Backup original
cp "$PG_HBA" "$PG_HBA.backup"
echo "✅ Backup created: $PG_HBA.backup"

# Check if trust authentication already configured
if grep -q "127.0.0.1/32.*trust" "$PG_HBA"; then
    echo "✅ Trust authentication already configured for IPv4"
else
    echo "📝 Adding trust authentication for local connections..."
    
    # Add trust lines at the beginning (before other rules)
    {
        echo "# Trust authentication for local development (added by setup script)"
        echo "host    all             all             127.0.0.1/32            trust"
        echo "host    all             all             ::1/128                 trust"
        echo ""
        cat "$PG_HBA.backup"
    } > "$PG_HBA"
    
    echo "✅ Trust authentication configured"
fi

# Restart PostgreSQL
echo ""
echo "🔄 Restarting PostgreSQL..."
brew services restart postgresql@15

echo ""
echo "✅ Configuration complete!"
echo ""
echo "Now try connecting:"
echo "  export DATABASE_URL=\"postgresql://postgres@localhost:5432/postgres\""
echo "  export USE_FILE_STORAGE=\"false\""
echo "  python3 scripts/create_db_direct.py"

