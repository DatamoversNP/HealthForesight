# Demo Day Setup (Option A)

One script and one story for an impactful demo: **policies with mixed verdicts** (ON_TRACK, AT_RISK, BACKFIRE) so you can show lineage, evidence packs, and verdicts in one flow.

## Quick start

From the **repo root** (with API env and DB available):

```bash
python scripts/run_demo_day.py
```

Options:

- `--tenant-id UUID` – Default: `00000000-0000-0000-0000-000000000001`
- `--skip-seed` – Only create observations; assume tenant, policies, baseline, and predicted impact already exist

## What the script does

1. **Ensures demo tenant and user** – Creates tenant and one user for the demo tenant if missing.
2. **Ensures policies** – If the tenant has fewer than 3 policies, creates 5 minimal demo policies (e.g. Prior Auth MRI, Site-of-Care Infusion, PT Coverage, Step Therapy, Urgent Care Copay).
3. **Ensures baseline** – If no baseline exists, creates one with fixed utilization and cost metrics.
4. **Ensures predicted impact** – For each policy, if there is no predicted impact, creates a minimal one (e.g. −5 util, −2 cost).
5. **Creates 5 observations** with a clear story:
   - **2 ON_TRACK** – Observed ≈ predicted (~100% accuracy).
   - **2 AT_RISK** – Observed worse than predicted (e.g. ~82% accuracy).
   - **1 BACKFIRE** – Observed worse + behavioral risk factors (e.g. substitution, delay).

## Demo story to tell

1. **List observations** – `GET /api/v1/observations` (or use the UI). Show a mix of verdicts: ON_TRACK, AT_RISK, BACKFIRE.
2. **Evidence pack** – For an AT_RISK or BACKFIRE observation, call `GET /api/v1/observations/{observation_id}/evidence-pack` to show baseline vs predicted vs observed and the verdict reason + recommendation.
3. **Lineage** – Each observation has `analytics_run_id`; use `GET /api/v1/runs/{run_id}` to show run type, input_refs, and output_refs.
4. **Audit** – Run completed/failed events are logged; you can tie runs to audit trail for governance.

## If you already have data

To only add the mixed verdict observations (no tenant/policies/baseline/predicted impact creation):

```bash
python scripts/run_demo_day.py --skip-seed
```

Requires at least one baseline and at least one policy with predicted impact for the given tenant.

## First-policy ROI (prescribed path)

To show value on **one policy** and get a single verdict + recommendation:

1. Run `python3 scripts/run_demo_day.py` so you have at least one policy with an observation.
2. Open **Policy Verdicts** in the UI (nav: Policy Verdicts). You see each policy’s verdict, cost impact, confidence, reason, and recommendation.
3. Click **View evidence** for a row (or go to Observation Analysis and open that observation). Use **Download evidence pack** to get the one-page executive summary (verdict, savings, confidence, reason, recommendation).

That’s the “first 60-day proof” path: one flow → one verdict + recommendation.

## Day-one path to first value

1. **Database:** `cd apps/api && alembic upgrade head`
2. **Demo data:** From repo root, `python3 scripts/run_demo_day.py`
3. **First value:** Open **Policy Verdicts** in the app (or `GET /api/v1/policy-verdicts`). You immediately see which policies are saving money and which are backfiring.

For full onboarding (your data, your policies), use ingestion and pipelines; the script above is the minimal path to first value in one view.

## Troubleshooting

- **No policies / no baseline** – Run without `--skip-seed` so the script creates demo policies and a baseline.
- **Database not ready** – Ensure the API’s DB is up and migrations applied (`cd apps/api && alembic upgrade head`).
- **Import errors** – Run from repo root so `apps/api/src` and `packages/common/src` are on the path (the script adds them).
