#!/bin/bash
# Monitor deployment status and image pulls

NAMESPACE="healthforesight-prod"
CHECK_INTERVAL=30
MAX_CHECKS=20

echo "=== Deployment Monitoring ==="
echo "Namespace: $NAMESPACE"
echo "Check interval: ${CHECK_INTERVAL}s"
echo "Max checks: $MAX_CHECKS"
echo "Start time: $(date)"
echo ""

for i in $(seq 1 $MAX_CHECKS); do
    echo "--- Check $i/$MAX_CHECKS at $(date) ---"
    
    # Pod status
    echo ""
    echo "Pod Status:"
    kubectl get pods -n $NAMESPACE 2>&1 | head -15
    
    # Check for successful image pulls
    echo ""
    echo "Recent successful image pulls:"
    kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' 2>&1 | \
        grep -i "pulled\|started" | \
        grep -i "uepiregistry61380\|healthforesight" | \
        tail -5 || echo "  No successful pulls yet"
    
    # Check for errors
    echo ""
    echo "Recent errors:"
    kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' 2>&1 | \
        grep -i "error\|failed\|unauthorized" | \
        tail -3 || echo "  No recent errors"
    
    # Count running pods
    RUNNING=$(kubectl get pods -n $NAMESPACE --no-headers 2>&1 | grep -c "Running" || echo "0")
    TOTAL=$(kubectl get pods -n $NAMESPACE --no-headers 2>&1 | wc -l | tr -d ' ')
    
    echo ""
    echo "Summary: $RUNNING/$TOTAL pods running"
    
    if [ "$RUNNING" -gt 0 ] && [ "$RUNNING" -eq "$TOTAL" ]; then
        echo ""
        echo "✅ All pods are running!"
        break
    fi
    
    if [ $i -lt $MAX_CHECKS ]; then
        echo ""
        echo "Waiting ${CHECK_INTERVAL}s before next check..."
        sleep $CHECK_INTERVAL
    fi
done

echo ""
echo "=== Final Status ==="
kubectl get pods -n $NAMESPACE 2>&1
echo ""
echo "End time: $(date)"

