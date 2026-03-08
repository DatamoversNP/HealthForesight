#!/bin/bash
# Check if PostgreSQL is running and start it if needed

echo "================================================================================"
echo "POSTGRESQL SETUP"
echo "================================================================================"
echo ""

# Check if PostgreSQL is already running locally
echo "Step 1: Checking if PostgreSQL is already running..."
if psql -U uepi -d uepi -h localhost -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ PostgreSQL is already running and accessible!"
    echo "   Connection test successful"
    exit 0
fi

# Check if Docker is available
echo "Step 2: Checking Docker availability..."
if command -v docker > /dev/null 2>&1; then
    echo "✅ Docker is installed"
    
    # Try docker compose (V2 - newer)
    if docker compose version > /dev/null 2>&1; then
        echo "✅ Docker Compose V2 is available"
        echo ""
        echo "Starting PostgreSQL with Docker Compose V2..."
        docker compose up -d postgres
        echo ""
        echo "Waiting for PostgreSQL to be ready..."
        sleep 5
        
        # Wait for health check
        for i in {1..30}; do
            if docker exec uepi-postgres pg_isready -U uepi > /dev/null 2>&1; then
                echo "✅ PostgreSQL is ready!"
                exit 0
            fi
            echo "   Waiting... ($i/30)"
            sleep 1
        done
        
    # Try docker-compose (V1 - older)
    elif command -v docker-compose > /dev/null 2>&1; then
        echo "✅ Docker Compose V1 is available"
        echo ""
        echo "Starting PostgreSQL with Docker Compose V1..."
        docker-compose up -d postgres
        echo ""
        echo "Waiting for PostgreSQL to be ready..."
        sleep 5
        
        # Wait for health check
        for i in {1..30}; do
            if docker exec uepi-postgres pg_isready -U uepi > /dev/null 2>&1; then
                echo "✅ PostgreSQL is ready!"
                exit 0
            fi
            echo "   Waiting... ($i/30)"
            sleep 1
        done
        
    else
        echo "⚠️  Docker Compose not found"
        echo ""
        echo "Starting PostgreSQL with docker run..."
        docker run -d \
          --name uepi-postgres \
          -e POSTGRES_USER=uepi \
          -e POSTGRES_PASSWORD=uepi123 \
          -e POSTGRES_DB=uepi \
          -p 5432:5432 \
          -v uepi-postgres-data:/var/lib/postgresql/data \
          postgres:15-alpine
        
        echo ""
        echo "Waiting for PostgreSQL to be ready..."
        sleep 5
        
        for i in {1..30}; do
            if docker exec uepi-postgres pg_isready -U uepi > /dev/null 2>&1; then
                echo "✅ PostgreSQL is ready!"
                exit 0
            fi
            echo "   Waiting... ($i/30)"
            sleep 1
        done
    fi
    
else
    echo "❌ Docker is not installed"
    echo ""
    echo "Options:"
    echo "1. Install Docker Desktop: https://www.docker.com/products/docker-desktop"
    echo "2. Install PostgreSQL locally: brew install postgresql@15"
    echo "3. Use existing PostgreSQL installation"
    echo ""
    echo "If you have PostgreSQL installed locally, you can:"
    echo "  - Create database: createdb uepi"
    echo "  - Create user: psql -c \"CREATE USER uepi WITH PASSWORD 'uepi123';\""
    echo "  - Grant privileges: psql -c \"GRANT ALL PRIVILEGES ON DATABASE uepi TO uepi;\""
    exit 1
fi

echo ""
echo "✅ PostgreSQL should now be running!"
echo "   Test connection: psql -U uepi -d uepi -h localhost -c 'SELECT 1;'"
