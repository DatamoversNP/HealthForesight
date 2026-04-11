#!/usr/bin/env bash
# Run baseline / prediction validation against the same DB as the API.
# Usage: ./scripts/run_validate_baselines.sh [--tenant UUID] [--json] [--env-file PATH]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/apps/api/scripts/validate_baselines_predictions_report.py" "$@"
