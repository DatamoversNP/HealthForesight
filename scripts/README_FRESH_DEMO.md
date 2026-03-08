# Fresh Demo Setup Scripts

**Single script for a full fresh demo:** `run_fresh_demo_setup.py`.  
These scripts implement the **Fresh Demo Setup** (see `FRESH_DEMO_SETUP_PLAN.md`). Run all from the **repository root**.

## Quick start

```bash
# Full fresh demo (clean → 3x claims → load → baselines → predicted impact → observation-period → observations)
python3 scripts/run_fresh_demo_setup.py
```

Data coverage is **~3×** (1.5–3 claims per member per month, cap 150k/month) for a realistic picture. Historical and observation-period data are **policy-aligned** (LOB, market, CPT from your policies) so baselines and predicted impact use relevant claims.

Requires:

- PostgreSQL running and reachable (connection via env / `apps/api` config).
- Demo tenant `00000000-0000-0000-0000-000000000001` (created automatically by Phase 1 if needed; policies are created separately or by `run_demo_day.py`).
- **Phase 1b** runs `alembic upgrade head` from `apps/api` so that `analytics_runs` and `baselines.analytics_run_id` exist. If you run a single phase (e.g. `--phase 4`) without a full run, ensure migrations are applied: `cd apps/api && alembic upgrade head`.

## Scripts (by phase)

| Phase | Script | Description |
|-------|--------|-------------|
| 1 | `fresh_demo_clean.py` | Remove all raw + derived data for demo tenant. Use `--dry-run` to preview. |
| 1b | `alembic upgrade head` (from `apps/api`) | Create `analytics_runs` table and `baselines.analytics_run_id` / `observations.analytics_run_id` columns. |
| 2 | `generate_24mo_historical_demo_data.py` | Generate historical CSVs (default 2022-01-01 to 2025-06-30) for 1000 members (~3× claim volume, policy-aligned). Baseline windows are clamped to this range so policies find data. |
| 3 | `load_fresh_demo_historical.py` | Load historical CSVs into DB (default: `.../historical`). |
| 3b | `set_demo_policy_effective_dates.py` | Set all policy effective dates to **July 2025** so baseline = pre go-live, observations = post go-live. |
| 4 | `run_baseline_and_predicted_impact.py` | Baseline refresh + predicted impact for all policies. |
| 5 | `generate_observation_period_demo_data.py` | Generate July 2025–present CSVs (same 1000 members). |
| 6 | `load_fresh_demo_historical.py --input-dir .../observation_period --skip-providers` | Load observation-period data (skips providers to avoid duplicate-key errors). |
| 7 | `create_observations_per_month.py` | One observation per policy per month (mixed verdicts). |

## Run a single phase

```bash
python3 scripts/run_fresh_demo_setup.py --phase 2
python3 scripts/run_fresh_demo_setup.py --phase 7
python3 scripts/run_fresh_demo_setup.py --phase 3b   # only set policy effective dates to July 2025
```

Phases 1, 1b, 2, 3, 3b, 4, 5, 6, 7 correspond to the table above.

## Dry-run (Phase 1 only)

```bash
python3 scripts/run_fresh_demo_setup.py --dry-run
```

Prints what would be deleted; no DB changes.

## Custom tenant

```bash
python3 scripts/run_fresh_demo_setup.py --tenant-id YOUR-TENANT-UUID
```

## After running

- Reload **Policy Verdicts** and **Dashboard** in the UI.
- Use **Objectives Health** and observation evidence packs as in `DEMO_DAY_README.md`.
