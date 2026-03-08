#!/bin/bash
# Script to set up PostgreSQL user and database for local development

set -e

echo "🔧 Setting up PostgreSQL for local development..."

# Get current username
USERNAME=$(whoami)
DB_NAME="uepi_db"

echo "📝 Username: $USERNAME"
echo "📝 Database: $DB_NAME"

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "❌ PostgreSQL is not running"
    echo "   Start it with: brew services start postgresql@15"
    exit 1
fi

echo "✅ PostgreSQL is running"

# Try to connect as current user
echo ""
echo "🔍 Checking if user '$USERNAME' exists in PostgreSQL..."

# Try to create user if it doesn't exist (this will fail if user exists, which is fine)
psql -U postgres -d postgres -c "CREATE USER $USERNAME WITH CREATEDB;" 2>/dev/null || echo "   User already exists or using postgres user"

# Set password for user (or create with password)
echo ""
echo "🔐 Setting up authentication..."

# Option 1: Try to set password (if user exists)
psql -U postgres -d postgres -c "ALTER USER $USERNAME WITH PASSWORD '';" 2>/dev/null || true

# Option 2: Configure trust authentication for local connections
PG_HBA_PATH=$(psql -U postgres -d postgres -t -c "SHOW hba_file;" | xargs)
if [ -f "$PG_HBA_PATH" ]; then
    echo "📝 PostgreSQL config file: $PG_HBA_PATH"
    echo "   You may need to edit this file to allow passwordless connections"
    echo "   Add this line for local connections:"
    echo "   host    all             all             127.0.0.1/32            trust"
    echo "   host    all             all             ::1/128                 trust"
fi

# Create database
echo ""
echo "📊 Creating database '$DB_NAME'..."
psql -U postgres -d postgres -c "CREATE DATABASE $DB_NAME OWNER $USERNAME;" 2>/dev/null || {
    echo "   Database might already exist, continuing..."
}

echo ""
echo "✅ Setup complete!"
echo ""
echo "Try connecting with:"
echo "  export DATABASE_URL=\"postgresql://$USERNAME@localhost:5432/$DB_NAME\""
echo ""
echo "If that doesn't work, try with postgres user:"
echo "  export DATABASE_URL=\"postgresql://postgres@localhost:5432/$DB_NAME\""
echo ""
echo "Or set a password and use:"
echo "  export DATABASE_URL=\"postgresql://$USERNAME:yourpassword@localhost:5432/$DB_NAME\""

