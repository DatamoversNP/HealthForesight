# Objective Health — Stability Defect Report (Phase 1)

**Date:** 2026-11-03  
**Status:** Root causes fixed; unit invariants pass; **browser gates 1 / 4 / 7 PASS** — Objective Health stability blocker **CLOSED** for Dec 4 demo readiness sequencing. Inventory expansion remains deferred pending reimbursement lifecycle work.

## Reported symptom

Objectives Health produced different results at different times for the same user/session context without an identifiable configuration change.

## Root causes (reproduced via code path analysis)

1. **Silent empty fallbacks** — client swallowed per-endpoint failures into `[]` / `null`, so a flaky `/policy-verdicts` call switched the page onto a different status engine without surfacing an error.
2. **Dual status derivation** — when verdicts were missing, client used `deriveStatus(policy-performance)`; when present, used verdicts. Those sources disagree (and performance fills predicted metrics when observations are absent).
3. **Predicted-as-observed** — `/dashboard/policy-performance` injects predicted util/cost when `observations_count=0`, which Objective Health previously treated as real health signal.
4. **Nondeterministic forecast probing** — N+1 `getPolicyPredictedImpact` on an unsorted `.slice(0, 40)` candidate set; timeouts/order changed Objective A/F counts.
5. **Stale response races** — remount/refresh without generation guards could apply an older response after a newer one.
6. **Operational wedge (found during live rehearsal)** — `list_policies()` hydrated every policy with assumptions/guardrails/versions/changelog (**~4 Azure round-trips × 283 policies**). Sync work inside `async` handlers blocked the event loop so even `/health` hung during DNS/DB stalls.

## Fix

| Layer | Change |
|-------|--------|
| API | `GET /api/v1/dashboard/objectives-health` — single authoritative snapshot |
| Service | `objectives_health.py` — pure builder; `calculation_version: objectives-health-v1` |
| Status | Same `compute_verdict` as `/policy-verdicts` |
| Forecasts | Persisted `list_latest_predicted_impacts` only |
| UI | Single fetch; stale discard; refresh errors keep prior good snapshot |
| Perf | `list_policies(..., summary=True)` for OH, Policy Verdicts, coverage, readiness, reconciliation |
| Isolation | `asyncio.to_thread` for OH / PV inputs / coverage / readiness; lazy extended routes off event loop |
| Health | `/live` (liveness, no DB) + `/ready` (Postgres in worker thread, 6s timeout); `pool_timeout=10` |
| Tests | `test_objectives_health_stability.py` (determinism, no predicted-as-on_track, OH↔verdicts invariant) |

## Stability contract

For the same tenant, persisted policies, observations, predicted impacts, decisions, and calculation version:

- Snapshot equality holds aside from `generated_at`
- Refresh does not invent empty/synthetic health
- Pending/failed secondary coverage loads do not fabricate inventory completeness
- **Invariant:** for the same policy, data snapshot, and calculation version, Objective Health status maps 1:1 from `compute_verdict` (Policy Verdicts engine). Forecast availability never becomes observed performance.

## Unit regression

| Test | Result |
|------|--------|
| `test_snapshot_is_deterministic_across_builds` | PASS |
| `test_refresh_equivalence_ignoring_timestamp` | PASS |
| `test_no_observation_never_inherits_predicted_as_on_track` | PASS |
| `test_objectives_health_verdicts_match_compute_verdict_invariant` | PASS |
| Offline suite (enterprise + reconciliation) | **17/17 PASS** |

## Browser regression checklist (Dec 4 gate)

Executed 2026-11-03 ~07:51–08:01 UTC against Data Voyager `:7868` → API `:7867` → Azure Postgres. Evidence: `docs/demo/bcbs-nc/evidence/OBJECTIVES_HEALTH_BROWSER_GATES.json`.

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Load page twice → identical summary/strategic counts | **PASS** | API OH×2 equal aside from `generated_at` (`283/186/79/18`). Browser refresh: snap `1:29:25 PM` → `1:29:55 PM`, same counts, chip `4 of 6`, calc `objectives-health-v1` |
| 4 | Two concurrent tabs | **PASS** | Tabs `229ce0` + `01d689` both `283/186/79/18`; no contradictory status; independent snapshots |
| 7 | Align one policy row with Policy Verdicts | **PASS** | **Outpatient MRI Prior Authorization** — OH `On track` / API `ON_TRACK`; PV `Saving / on track` |

Preflight after recovery: `/api/v1/health` (liveness) 200 in ~1ms; `/api/v1/ready` `database=connected`; DB-backed `policies?limit=5` 200.

### Operational note

Stale API pid **68082** required an authorized `kill -9` then `./docs/demo/bcbs-nc/local_demo/start_demo7867.sh`. Agent sandbox could not signal that process until elevated approval.

## Dec 4 gate (Objective Health)

| Gate | Status |
|------|--------|
| Code path uses single verdict engine | **Met** |
| Forecast ≠ observed | **Met** |
| Browser rows 1 / 4 / 7 | **Met** |
| Inventory expansion before OH close | **Deferred** (still deferred — do not expand Medicare/reimbursement inventory yet) |
