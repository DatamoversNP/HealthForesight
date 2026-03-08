#!/bin/bash
# Script to create .env file for LOCAL development

echo "Creating .env file for local development..."

# Try to detect local PostgreSQL setup
if command -v psql &> /dev/null; then
    # Check if we can connect as postgres user
    if psql -U postgres -d postgres -c "SELECT 1;" &> /dev/null; then
        echo "✅ Detected local PostgreSQL with 'postgres' user"
        DB_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"
    elif psql -U $(whoami) -d postgres -c "SELECT 1;" &> /dev/null; then
        echo "✅ Detected local PostgreSQL with '$(whoami)' user"
        DB_URL="postgresql://$(whoami)@localhost:5432/uepi_db"
    else
        echo "⚠️  Could not auto-detect PostgreSQL setup, using default"
        DB_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"
    fi
else
    echo "⚠️  psql not found, using default configuration"
    DB_URL="postgresql://postgres:postgres@localhost:5432/uepi_db"
fi

# Create .env file
cat > .env << EOF
# Database Configuration for LOCAL Development
# This file is automatically loaded by pydantic-settings
# DO NOT commit this file to version control (it's in .gitignore)

# PostgreSQL connection string for local development
DATABASE_URL=${DB_URL}

# Connection pool settings (optional)
# DATABASE_POOL_SIZE=10
# DATABASE_MAX_OVERFLOW=20
# DATABASE_ECHO=false
EOF

echo ""
echo "✅ Created .env file with:"
echo "   DATABASE_URL=${DB_URL}"
echo ""
echo "📝 If this doesn't match your setup, edit .env and update DATABASE_URL"
echo "   Common options:"
echo "   - Local PostgreSQL: postgresql://postgres:postgres@localhost:5432/uepi_db"
echo "   - Docker Compose: postgresql://uepi:uepi123@localhost:5432/uepi"
echo "   - Homebrew (no password): postgresql://$(whoami)@localhost:5432/uepi_db"
