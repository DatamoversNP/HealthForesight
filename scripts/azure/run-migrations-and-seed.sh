#!/bin/bash
# Script to run database migrations and seed demo data in Kubernetes pod

set -e

NAMESPACE="${NAMESPACE:-uepi-prod}"
API_DEPLOYMENT="${API_DEPLOYMENT:-uepi-api}"

echo "🔍 Finding API pod in namespace: $NAMESPACE"
API_POD=$(kubectl get pod -n "$NAMESPACE" -l app=uepi-api -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -z "$API_POD" ]; then
    echo "❌ API pod not found in namespace $NAMESPACE"
    echo "   Available pods:"
    kubectl get pods -n "$NAMESPACE" 2>&1 || echo "   Namespace $NAMESPACE does not exist"
    exit 1
fi

echo "✅ Found API pod: $API_POD"
echo ""

# Test database connection
echo "🧪 Testing database connection..."
kubectl exec -n "$NAMESPACE" "$API_POD" -- python -c "
import sys
sys.path.insert(0, '/app/src')
sys.path.insert(0, '/app/packages/common/src')
from uepi_api.database import engine
try:
    with engine.connect() as conn:
        result = conn.execute('SELECT 1 as test')
        row = result.fetchone()
        print('✅ Database connection successful!')
        print('Result:', row)
except Exception as e:
    print('❌ Database connection failed:', str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Database connection test failed. Please check the connection string and network configuration."
    exit 1
fi

echo ""
echo "📋 Running Alembic migrations..."
cd "$(dirname "$0")/../.."
kubectl exec -n "$NAMESPACE" "$API_POD" -- bash -c "
    cd /app && \
    export PYTHONPATH=/app/src:/app/packages/common/src && \
    export DATABASE_URL=\"\${DATABASE_URL}\" && \
    alembic upgrade head
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Migrations failed. Please check the logs above."
    exit 1
fi

echo ""
echo "🌱 Seeding demo data..."
# Copy seed script to pod
kubectl cp scripts/dev/seed_demo_data.py "$NAMESPACE/$API_POD:/tmp/seed_demo_data.py"

# Run seed script
kubectl exec -n "$NAMESPACE" "$API_POD" -- bash -c "
    export PYTHONPATH=/app/src:/app/packages/common/src && \
    export DATABASE_URL=\"\${DATABASE_URL}\" && \
    python /tmp/seed_demo_data.py
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Seeding failed. Please check the logs above."
    exit 1
fi

echo ""
echo "✅ Migrations and seeding completed successfully!"
echo ""
echo "🧪 Testing API endpoints..."
echo "   GET /api/v1/policies:"
kubectl exec -n "$NAMESPACE" "$API_POD" -- curl -s -H "Authorization: Bearer dev-token-123" http://localhost:8000/api/v1/policies 2>&1 | head -5
echo ""
echo "   GET /api/v1/ingestions:"
kubectl exec -n "$NAMESPACE" "$API_POD" -- curl -s -H "Authorization: Bearer dev-token-123" http://localhost:8000/api/v1/ingestions 2>&1 | head -5
echo ""
echo "✅ All done! Demo data is now available in the database."

