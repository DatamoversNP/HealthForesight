#!/usr/bin/env bash
# =============================================================================
# Production-like pipeline for Azure (demo / client-style operations)
#
# Uses the same frequencies we recommend:
#   Daily:  POST /jobs/daily-data-and-observations (ingest path + data period + observations)
#   Weekly: POST /baselines/refresh-all + best-effort POST /learning/update-elasticity per policy
#
# Modes:
#   backfill  — run daily job for each calendar day from --from through --to (inclusive), and
#               run refresh-all every BASELINE_EVERY_N days (default 7) and at the end.
#   daily     — one run with API default target date (yesterday) unless --date is set.
#   weekly    — refresh-all + elasticity updates only (for a weekly cron, e.g. Sunday).
#
# Prerequisites:
#   - API deployed; JWT from a user with POLICY_ADMIN or UM_LEADER
#   - Optional: Celery worker + Redis so daily jobs are not tied to the API web worker
#   - For real claims: drop files under data/source_data/<tenant-id>/daily/YYYY-MM-DD/ on the API host
#     (or mount Azure Files there). If no files exist, the job generates synthetic claims (demo).
#
# Examples:
#   export API_JWT='eyJhbGciOi...'
#   export API_BASE_URL='https://healthforesight-api.azurewebsites.net'
#
#   # Historical catch-up: 2026-04-01 through today (UTC), then schedule "daily" from tomorrow
#   ./scripts/azure/production-like-pipeline.sh backfill --from 2026-04-01
#
#   # Cron after daily ETL (yesterday’s data); default API target_date = yesterday
#   0 6 * * * API_JWT=... API_BASE_URL=... /path/to/production-like-pipeline.sh daily
#
# JWT expiry: default API tokens are short-lived (~30 min). Long backfills will hit 401 while polling.
# Fix (pick one):
#   - export PIPELINE_LOGIN_EMAIL='demo@example.com' PIPELINE_LOGIN_PASSWORD='...'
#     The script re-logins before each daily trigger and after any 401 while polling.
#   - Or raise jwt_expiration_minutes on the API for an automation user.
#
# macOS Python SSL: login uses curl (not urllib) so certs match the system store. If you still see
# SSL errors with curl, install certs (e.g. Python.org installer “Install Certificates.command”) or
# last resort: PIPELINE_CURL_INSECURE=1 (not for production).
#
#   # Weekly window (baselines + elasticity), e.g. Sunday 03:00
#   0 3 * * 0 API_JWT=... /path/to/production-like-pipeline.sh weekly
#
# Web App proxy: set API_BASE_URL to https://healthforesight-web.azurewebsites.net and paths still use /api/v1
# (same-origin proxy). Prefer direct API URL for long-running refresh-all.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

API_BASE_URL="${API_BASE_URL:-https://healthforesight-api.azurewebsites.net}"
API_ROOT="${API_BASE_URL%/}/api/v1"
BASELINE_EVERY_N="${BASELINE_EVERY_N:-7}"
JOB_POLL_SEC="${JOB_POLL_SEC:-10}"
JOB_TIMEOUT_SEC="${JOB_TIMEOUT_SEC:-3600}"
RUN_OBSERVATIONS="${RUN_OBSERVATIONS:-true}"

refresh_api_jwt() {
  if [[ -z "${PIPELINE_LOGIN_EMAIL:-}" || -z "${PIPELINE_LOGIN_PASSWORD:-}" ]]; then
    return 1
  fi
  export API_ROOT PIPELINE_LOGIN_EMAIL PIPELINE_LOGIN_PASSWORD
  local body
  body=$(python3 -c "import json,os; print(json.dumps({'email':os.environ['PIPELINE_LOGIN_EMAIL'],'password':os.environ['PIPELINE_LOGIN_PASSWORD']}))") || return 1
  local curl_k=""
  if [[ "${PIPELINE_CURL_INSECURE:-}" == "1" ]]; then
    curl_k="-k"
  fi
  local code
  code=$(curl -sS $curl_k -o /tmp/hf-pipe-login.json -w '%{http_code}' \
    -X POST "${API_ROOT}/auth/login" \
    -H 'Content-Type: application/json' \
    -d "$body" \
    --max-time 90 || echo "000")
  code="${code//$'\r'/}"
  if [[ "$code" != "200" ]]; then
    echo "❌ login HTTP $code" >&2
    head -c 800 /tmp/hf-pipe-login.json >&2 2>/dev/null || true
    return 1
  fi
  local new_tok
  new_tok=$(python3 -c "import json; print(json.load(open('/tmp/hf-pipe-login.json'))['access_token'])") || return 1
  API_JWT="$new_tok"
  export API_JWT
  echo "   🔑 Refreshed API_JWT (login)" >&2
  return 0
}

require_jwt() {
  if [[ -z "${API_JWT:-}" ]]; then
    if refresh_api_jwt; then
      return 0
    fi
    echo "❌ Set API_JWT, or PIPELINE_LOGIN_EMAIL + PIPELINE_LOGIN_PASSWORD (POLICY_ADMIN / UM_LEADER)." >&2
    exit 1
  fi
}

curl_api() {
  curl -sS -H "Authorization: Bearer ${API_JWT}" -H "Content-Type: application/json" "$@"
}

poll_daily_job() {
  local job_id="$1"
  local deadline=$(( $(date +%s) + JOB_TIMEOUT_SEC ))
  local pending_polls=0
  while true; do
    local now
    now=$(date +%s)
    if (( now > deadline )); then
      echo "❌ Job $job_id timed out after ${JOB_TIMEOUT_SEC}s" >&2
      return 1
    fi
    local body code
    code=$(curl -sS -o /tmp/hf-daily-job-status.json -w '%{http_code}' \
      -H "Authorization: Bearer ${API_JWT}" \
      "${API_ROOT}/jobs/daily-data-and-observations/status/${job_id}" || echo "000")
    code="${code//$'\r'/}"
    code="${code//$'\n'/}"
    if [[ "$code" == "401" ]]; then
      echo "   HTTP 401 while polling (JWT usually expired)." >&2
      if refresh_api_jwt; then
        echo "   Retrying status with new token..." >&2
        sleep 2
        continue
      fi
      echo "❌ Still unauthorized. Set a fresh API_JWT or PIPELINE_LOGIN_EMAIL + PIPELINE_LOGIN_PASSWORD." >&2
      head -c 800 /tmp/hf-daily-job-status.json >&2 2>/dev/null || true
      return 1
    fi
    if [[ "$code" != "200" ]]; then
      echo "   status HTTP $code — retry..." >&2
      sleep "$JOB_POLL_SEC"
      continue
    fi
    local st
    st=$(python3 -c "import json; print(json.load(open('/tmp/hf-daily-job-status.json')).get('status',''))" 2>/dev/null || echo "")
    if [[ "$st" == "COMPLETED" ]]; then
      echo "   ✅ job $job_id COMPLETED"
      return 0
    fi
    if [[ "$st" == "FAILED" ]]; then
      echo "❌ job $job_id FAILED:" >&2
      cat /tmp/hf-daily-job-status.json >&2
      return 1
    fi
    if [[ "$st" == "PENDING" ]]; then
      pending_polls=$((pending_polls + 1))
      if (( pending_polls == 18 )); then
        echo "   ⚠️  Still PENDING after ~3 min: tasks were likely stuck in Celery with no worker." >&2
        echo "      Redeploy API (daily job now defaults to inline BackgroundTasks) or run uepi_worker + Redis." >&2
      fi
    else
      pending_polls=0
    fi
    echo "   ... status=$st (poll in ${JOB_POLL_SEC}s)"
    sleep "$JOB_POLL_SEC"
  done
}

trigger_daily_for_date() {
  local d="$1"
  if [[ -n "${PIPELINE_LOGIN_EMAIL:-}" && -n "${PIPELINE_LOGIN_PASSWORD:-}" ]]; then
    refresh_api_jwt || return 1
  fi
  local qs="run_observations=${RUN_OBSERVATIONS}"
  if [[ -n "$d" ]]; then
    qs="${qs}&target_date=${d}"
  fi
  echo ">>> Daily pipeline POST target_date=${d:-<api default: yesterday>}"
  local code body
  code=$(curl -sS -o /tmp/hf-daily-trigger.json -w '%{http_code}' \
    -X POST \
    -H "Authorization: Bearer ${API_JWT}" \
    -H "Content-Type: application/json" \
    "${API_ROOT}/jobs/daily-data-and-observations?${qs}" || echo "000")
  if [[ "$code" != "202" && "$code" != "200" ]]; then
    echo "❌ trigger returned HTTP $code" >&2
    cat /tmp/hf-daily-trigger.json >&2
    return 1
  fi
  local job_id
  job_id=$(python3 -c "import json; print(json.load(open('/tmp/hf-daily-trigger.json'))['job_id'])")
  poll_daily_job "$job_id"
}

run_refresh_all() {
  if [[ -n "${PIPELINE_LOGIN_EMAIL:-}" && -n "${PIPELINE_LOGIN_PASSWORD:-}" ]]; then
    refresh_api_jwt || true
  fi
  echo ">>> POST baselines/refresh-all (ROLLING 12m) ..."
  local code
  code=$(curl -sS -o /tmp/hf-refresh-all.json -w '%{http_code}' \
    -X POST \
    -H "Authorization: Bearer ${API_JWT}" \
    -H "Content-Type: application/json" \
    --max-time 600 \
    "${API_ROOT}/baselines/refresh-all?baseline_type=ROLLING&window_months=12" || echo "000")
  if [[ "$code" != "200" ]]; then
    echo "❌ refresh-all HTTP $code" >&2
    head -c 2500 /tmp/hf-refresh-all.json >&2 || true
    return 1
  fi
  echo "   ✅ refresh-all OK"
}

run_elasticity_batch() {
  echo ">>> Learning: update-elasticity per policy (errors ignored if no observations) ..."
  local curl_k=""
  [[ "${PIPELINE_CURL_INSECURE:-}" == "1" ]] && curl_k="-k"
  curl -sS $curl_k -o /tmp/hf-policies.json --max-time 120 \
    -H "Authorization: Bearer ${API_JWT}" \
    "${API_ROOT}/policies" || {
    echo "   ⚠️  could not GET /policies (skip elasticity batch)" >&2
    return 0
  }
  export API_ROOT API_JWT PIPELINE_CURL_INSECURE
  python3 <<'PY'
import json, os, subprocess, urllib.parse

root = os.environ["API_ROOT"]
jwt = os.environ["API_JWT"]
curl_prefix = ["curl", "-sS"] + (["-k"] if os.environ.get("PIPELINE_CURL_INSECURE") == "1" else [])

with open("/tmp/hf-policies.json") as f:
    policies = json.load(f)

ok = skip = 0
for p in policies:
    pid = p.get("id")
    pt = str(p.get("policy_type") or "PRIOR_AUTH")
    q = urllib.parse.urlencode({"policy_id": str(pid), "policy_type": pt})
    url = f"{root}/learning/update-elasticity?{q}"
    cmd = curl_prefix + [
        "-o", "/dev/null",
        "-w", "%{http_code}",
        "-X", "POST",
        "-H", f"Authorization: Bearer {jwt}",
        "--max-time", "120",
        url,
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=130)
        code = (out.stdout or "").strip()
        if code in ("200", "201"):
            ok += 1
        else:
            skip += 1
    except Exception:
        skip += 1

print(f"   elasticity updates: {ok} ok, {skip} skipped/failed")
PY
}

cmd_daily() {
  require_jwt
  local d="${1:-}"
  if [[ -n "$d" ]]; then
    trigger_daily_for_date "$d"
  else
    trigger_daily_for_date ""
  fi
}

cmd_weekly() {
  require_jwt
  run_refresh_all
  run_elasticity_batch
}

cmd_backfill() {
  require_jwt
  local FROM_DATE="2026-04-01"
  local TO_DATE=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --from) FROM_DATE="$2"; shift 2 ;;
      --to)   TO_DATE="$2"; shift 2 ;;
      *) echo "Unknown arg: $1" >&2; exit 1 ;;
    esac
  done
  if [[ -z "$TO_DATE" ]]; then
    TO_DATE=$(python3 -c "import datetime; print(datetime.date.today().isoformat())")
  fi
  python3 <<_PY_VALIDATE
import datetime
import sys
a = datetime.date.fromisoformat("${FROM_DATE}")
b = datetime.date.fromisoformat("${TO_DATE}")
if a > b:
    print("ERROR: --from must be <= --to (today=%s)" % b, file=sys.stderr)
    sys.exit(1)
_PY_VALIDATE
  echo "=============================================="
  echo "Backfill daily pipeline: $FROM_DATE .. $TO_DATE (UTC dates)"
  echo "API_ROOT=$API_ROOT"
  echo "Baseline refresh every $BASELINE_EVERY_N day(s) + final refresh"
  echo "=============================================="

  local days
  days=$(python3 <<_PY_DAYS
import datetime
a = datetime.date.fromisoformat("${FROM_DATE}")
b = datetime.date.fromisoformat("${TO_DATE}")
if a > b:
    raise SystemExit("from > to")
d = a
while d <= b:
    print(d.isoformat())
    d += datetime.timedelta(days=1)
_PY_DAYS
)

  local i=0
  while IFS= read -r day; do
    [[ -z "$day" ]] && continue
    i=$((i + 1))
    echo ""
    echo "---------- Day $i: $day ----------"
    trigger_daily_for_date "$day"
    if (( i % BASELINE_EVERY_N == 0 )); then
      run_refresh_all || true
    fi
  done <<< "$days"

  echo ""
  echo ">>> Final baseline refresh after backfill"
  run_refresh_all || true
  run_elasticity_batch || true
  echo ""
  echo "✅ Backfill complete."
  echo "Schedule daily: 0 6 * * * API_JWT=... $0 daily"
  echo "Schedule weekly: 0 3 * * 0 API_JWT=... $0 weekly"
}

usage() {
  sed -n '2,38p' "$0" | sed 's/^# \{0,1\}//'
}

main() {
  local sub="${1:-}"
  shift || true
  case "$sub" in
    backfill) cmd_backfill "$@" ;;
    daily)    cmd_daily "$@" ;;
    weekly)   cmd_weekly ;;
    ""|-h|--help|help) usage; exit 0 ;;
    *) echo "Unknown command: $sub" >&2; usage >&2; exit 1 ;;
  esac
}

main "$@"
