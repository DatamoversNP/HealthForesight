#!/bin/bash
# Autonomous overnight watchdog: keeps catalog high-confidence batches running.
set -u
ROOT="/Users/nileshl/Private/HealthForesight"
EVID="$ROOT/docs/demo/bcbs-nc/evidence"
BATCH="$EVID/overnight_batches"
LOG="$BATCH/overnight_watchdog.log"
PIDFILE="$BATCH/overnight.pid"
PY="$EVID/run_overnight_all_policies_high_confidence.py"
START="${1:-1}"
END="${2:-12}"

export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$ROOT"

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) watchdog start batches $START-$END" | tee -a "$LOG"

while true; do
  # stop if all batches completed and no FAIL rows pending re-gate? keep looping FAILs once.
  if [[ -f "$EVID/ALL_POLICIES_HIGH_CONFIDENCE_MASTER_REPORT.json" ]]; then
    DONE=$(python3 - <<'PY'
import json
from pathlib import Path
m=json.loads(Path("docs/demo/bcbs-nc/evidence/ALL_POLICIES_HIGH_CONFIDENCE_MASTER_REPORT.json").read_text())
print(",".join(str(x) for x in sorted(m.get("batches_completed") or [])))
PY
)
  else
    DONE=""
  fi

  # pick first incomplete batch in range
  NEXT=""
  for b in $(seq "$START" "$END"); do
    if [[ ",$DONE," != *",$b,"* ]]; then
      NEXT=$b
      break
    fi
  done

  if [[ -z "$NEXT" ]]; then
    # all batches marked complete — one FAIL re-gate pass then exit
    FAIL_N=$(python3 - <<'PY'
import json
from pathlib import Path
m=json.loads(Path("docs/demo/bcbs-nc/evidence/ALL_POLICIES_HIGH_CONFIDENCE_MASTER_REPORT.json").read_text())
print(sum(1 for r in (m.get("policies") or {}).values() if r.get("confidence")=="FAIL"))
PY
)
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) all batches complete; FAIL count=$FAIL_N" | tee -a "$LOG"
    if [[ "$FAIL_N" -gt 0 ]]; then
      echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) re-gate FAILs force start=$START end=$END" | tee -a "$LOG"
      # force re-run only incomplete confidence via --force would redo HIGH too; instead run batches and skip HIGH
      python3 "$PY" --start "$START" --end "$END" >> "$BATCH/overnight_run.log" 2>&1
      FAIL_N2=$(python3 - <<'PY'
import json
from pathlib import Path
m=json.loads(Path("docs/demo/bcbs-nc/evidence/ALL_POLICIES_HIGH_CONFIDENCE_MASTER_REPORT.json").read_text())
print(sum(1 for r in (m.get("policies") or {}).values() if r.get("confidence")=="FAIL"))
PY
)
      echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) after re-gate FAIL=$FAIL_N2" | tee -a "$LOG"
    fi
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) watchdog exit" | tee -a "$LOG"
    break
  fi

  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) launching batch $NEXT" | tee -a "$LOG"
  python3 "$PY" --batch "$NEXT" >> "$BATCH/overnight_run.log" 2>&1
  RC=$?
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) batch $NEXT exit_code=$RC" | tee -a "$LOG"
  sleep 3
done
