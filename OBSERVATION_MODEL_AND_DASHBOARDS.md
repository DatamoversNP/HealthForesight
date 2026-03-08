# Observation Model: Effective Date → Run Date

## Summary of change

Observations now use **one observation per run**, with period **policy effective date → run date** (cumulative).

- **Before:** One observation per data period (e.g. one day or one month); period = data period dates.
- **After:** Each run creates one observation per policy; period = `observation_period_start` (policy effective date) through `observation_period_end` (run date). Running on Jan 31, Feb 15, Mar 5 gives three observations with windows 30d, 45d, ~64d.

## Code changes

1. **observation_enhancement.create_observation_from_analysis**
   - Added optional `observation_period_start` and `observation_period_end`. When both are provided they override data_period / post_period.

2. **routers/daily_jobs.py**
   - Uses `_get_policy_effective_date(policy)`; skips if effective > run date.
   - Loads claims from `effective_date` to `target_date_obj` (run date).
   - Builds `post_period` and metrics for that range; passes `observation_period_start` / `observation_period_end` into `create_observation_from_analysis`.

3. **routers/observations.py (policy verdicts)**
   - “Latest” observation per policy is chosen by `observation_period_end` descending, then `computed_at`.

4. **routers/dashboard.py (policy-performance)**
   - Added `latest_observation_period_end` to each policy row so UI can show “Through [date]”.

## Affected modules (validated)

| Module | Effect | Change |
|--------|--------|--------|
| **Policy verdict** | Uses latest observation per policy | Sort by `observation_period_end` then `computed_at` so verdict reflects most recent run. |
| **Policy performance (dashboard)** | Aggregates observations per policy | No logic change; now aggregates over multiple runs. Added `latest_observation_period_end`. |
| **Objectives health** | Uses policy performance + observations | No change; benefits from multiple observations and new period semantics. |
| **Evidence pack** | Reads one observation | No change; already uses `observation_period_start` / `observation_period_end` from observation. |
| **Observation Analysis page** | Lists/filters observations | No API change; list now includes multiple observations per policy with growing windows. |

## Other references

- **database_claims_loader.load_claims_for_observation**: Already supports `observation_period_start` / `observation_period_end` for post period; used by the observations router (create from claims) path.
- **Routers/observations create-from-analysis**: Does not pass period overrides; period comes from `data_period_id` or `analysis_result.post_period` (unchanged).
- **Scripts** (e.g. `create_observations_for_all_policies.py`, `run_complete_workflow_internal.py`): Define their own `create_observation_from_analysis` or call the API; no change required for new optional params.

---

# Dashboard suggestions (post–observation model)

## Current dashboards

- **Main dashboard**: Policy performance (avg utilization/cost), top policies, decisions.
- **Policy Verdicts**: One row per policy, verdict + impact + reason (latest observation).
- **Objectives Health**: Strategic objectives A–F, policy-level status, observation/forecast/evidence counts.
- **Observation Analysis**: List observations, run daily job, trends.

## Suggested additional / enhancements

1. **Observation timeline per policy**
   - **What:** One chart per policy (or drill-down): X = run date (`observation_period_end`), Y = utilization or cost (or % change vs baseline). Each point = one observation (effective → run date).
   - **Why:** Shows “how policy is performing over time” as the cumulative window grows (30d, 45d, 64d, …).

2. **“Through date” on cards**
   - **What:** On Policy Verdicts and Policy Performance, show “Through &lt;date&gt;” using `observation_period_end` of the latest observation (or `latest_observation_period_end` from policy-performance API).
   - **Why:** Makes it explicit which run date the verdict/summary is for.

3. **Observations count and run history**
   - **What:** On Observation Analysis or policy detail: table of runs — run date, period (effective → run date), days in period, key metrics. Option to filter by policy.
   - **Why:** Direct view of “one observation per run” and cumulative windows.

4. **Policy effective date in lists**
   - **What:** Show policy effective date next to policy name (in Verdicts, Objectives, Performance) so users see when the observation window starts.
   - **Why:** Clarifies that each observation is “from go-live through run date.”

5. **Cumulative vs single-period toggle (future)**
   - **What:** If you later support both “cumulative from effective” and “single period” (e.g. one month), a dashboard filter or observation type could switch between them.
   - **Why:** Flexibility for different reporting needs without changing the default model.

## Optional API tweaks

- **GET /observations**: Optional query `?policy_id=...&latest_only=true` to return only the latest observation per policy (by `observation_period_end`).
- **GET /dashboard/policy-performance**: Already returns `latest_observation_period_end`; frontend can show “Through &lt;date&gt;” without further API changes.
