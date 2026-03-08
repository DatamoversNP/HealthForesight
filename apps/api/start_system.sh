#!/bin/bash
# Convenience script to start system from apps/api directory
# This script calls the main startup script from project root

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"
exec ./start_system.sh

