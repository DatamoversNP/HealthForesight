#!/bin/bash
# Run pipeline fix from any directory

# Get the script directory (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Run the fix script
./FIX_AND_VERIFY_PIPELINES.sh
