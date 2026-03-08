#!/bin/bash
# Start local development environment

set -e

echo "=== Starting Local Development Environment ==="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "Step 1: Creating data directories..."
mkdir -p data/policies data/metadata data/exports data/cache

echo ""
echo "Step 2: Starting Docker services (Redis, MinIO)..."
docker-compose -f docker-compose.no-db.yml up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

echo ""
echo "Step 3: Checking service health..."
docker-compose -f docker-compose.no-db.yml ps

echo ""
echo "Step 4: Creating MinIO bucket (if needed)..."
docker-compose -f docker-compose.no-db.yml exec -T minio mc alias set local http://localhost:9000 minioadmin minioadmin 2>/dev/null || true
docker-compose -f docker-compose.no-db.yml exec -T minio mc mb local/uepi-data 2>/dev/null || echo "Bucket already exists"

echo ""
echo "=== Local Services Started (No Database) ==="
echo ""
echo "✅ Data directories created: ./data/{policies,metadata,exports,cache}"
echo ""
echo "✅ Redis: localhost:6379 (optional)"
echo ""
echo "✅ MinIO:"
echo "   API: http://localhost:9000"
echo "   Console: http://localhost:9001"
echo "   Username: minioadmin"
echo "   Password: minioadmin"
echo ""
echo "Next steps:"
echo "1. Set up Python environment: cd apps/api && poetry install"
echo "2. Configure environment variables (no DATABASE_URL needed)"
echo "3. Start API: cd apps/api && poetry run uvicorn src.main:app --reload --port 8000"
echo "4. Start Worker: cd apps/worker && poetry run arq src.worker.WorkerSettings"
echo "5. Start Web: cd apps/web && npm install && npm run dev"
echo ""
echo "See LOCAL_DEVELOPMENT_NO_DB.md for detailed instructions"

