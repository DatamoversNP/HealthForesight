#!/bin/bash
# Quick script to run the observation fix

cd /Users/nilesh/Downloads/uepi-migration-20260123-151729

echo "Running observation creation script..."
echo ""

python3 scripts/create_observations_from_claims_data.py

echo ""
echo "Done! Check the results above."
