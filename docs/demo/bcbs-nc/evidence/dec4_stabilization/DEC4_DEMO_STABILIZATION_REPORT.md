# Dec 4 Deployed Demo Stabilization Report

**Status:** `DEMO_FREEZE_BLOCKED` (fixes coded + unit-path verified locally; **not deployed**; awaiting owner approval to promote)  
**Known-answer data modified:** **false** (no observation / mechanical / synthetic fixture rewrites)  
**Architecture migration:** none  

## Deployed revision (baseline — do not lose)

| Surface | Revision |
|---------|----------|
| API image | `healthforesightacr.azurecr.io/healthforesight-api:dec4-freeze-89f742f` |
| Git | `89f742f` · tag `demo-dec4-freeze-2026-11-04` |
| Web | `healthforesight-web.azurewebsites.net` (Running) |
| Demo DB alembic | **012** (unchanged) |

Rollback target if promotion regresses: re-point API container to `:dec4-freeze-89f742f` and redeploy prior web build.

---

## P0-1 — MRI Monitoring `AT_RISK` vs observation `ON_TRACK`

### Root cause

**Data-binding defect**, not two legitimate competing statuses for the same record.

1. Monitoring calls `GET /observations?policy_id=<MRI>&latest_only=true&summary=true&limit=5`.
2. In `storage_observations._list_observations`, **`latest_only` was ignored whenever `policy_id` was set**. Query ordered by `computed_at DESC`.
3. Monthly monitoring fixtures (`obs-mon-20260731-d403f101`, …) were computed more recently → returned first with **`AT_RISK`**.
4. Authoritative demo observation `b227220e-…` has later **`observation_period_end` (2026-08-14)** and **`ON_TRACK`** — same record Policy Verdicts / Observation Analysis use.
5. UI also painted empty **Mechanical** panel under `catalog_monitoring` (MRI correctly has no synthetic KA), which looked like a broken fixture rather than “empirical catalog policy.”

`CATALOG_POLICY` / `NO_SYNTHETIC_KA` chips are **policy-class labels** (honest for MRI). They are **not** observation verdicts. The bug was binding the chip “Observation: …” to the wrong row.

### Fix (minimal)

| File | Change |
|------|--------|
| `apps/api/src/uepi_api/storage_observations.py` | `latest_only` + `policy_id` → single row ordered by `observation_period_end`, then `computed_at`. Policy history also orders by period end. |
| `apps/web/src/components/policy/PolicyMonitoringPanel.tsx` | Client sort by period end; label “Latest observation verdict” + period/id; **do not** render empty mechanical panel for `catalog_monitoring`. |

**Did not:** hardcode `ON_TRACK`; mutate observation rows; invent mechanical KA for MRI.

### Before / after evidence

**Before (live Azure API, 2026-11-05):**

```
GET …/observations?policy_id=d403f101…&latest_only=true&limit=5
→ obs-mon-20260731-d403f101  AT_RISK  period_end=2026-07-31
Hero GET …/observations/b227220e-… → ON_TRACK period_end=2026-08-14
Browser Monitoring chip → AT_RISK
```

**After (code):** same Monitoring query returns latest-by-period row (`b227220e…` / `ON_TRACK` when that remains the max period_end). Unit test: `apps/api/tests/test_list_observations_latest_only_policy.py` (requires project venv / Py≥3.10 for `uepi_common` imports).

---

## P0-2 — Executive dashboard inflated ROI / `NaN%`

### Root causes

1. **`NaN%`:** `ExecutiveDashboardPage` passed `confidence="high"` into `ConfidenceBadge`, which only accepted numeric `score`. `(undefined * 100).toFixed(0)` → **`NaN%`**.
2. **Inflated “% of baseline”:** hardcoded `((abs(impact) / 10_000_000) * 100)` on fabricated dollar impact → **~5256%**.
3. **Fabricated portfolio $:** `dashboard.py` summed `cost_change_pmpm × baseline_member_months` across latest-per-policy observations → **~$525M** “Total Cost Impact”; ROI used **`active_policies × $50,000`** invented implementation cost → **~357% ROI** even with `member_count=0`.

### Fix (minimal)

| File | Change |
|------|--------|
| `apps/api/src/uepi_api/routers/dashboard.py` | Aggregate **PMPM deltas only**; set `roi_estimate_pct`, `annualized_savings`, `implementation_cost`, `payback` to **`null`** with `portfolio_financials_available` / reason when membership/paid baseline missing. |
| `apps/web/src/components/brand/ConfidenceBadge.tsx` | Accept `score` or qualitative `confidence`; never render NaN; show **Unavailable** if invalid. |
| `apps/web/src/pages/persona/ExecutiveDashboardPage.tsx` | Honest cost card units (Σ ΔPMPM); fix What-Changed copy; no hardcoded 10M denominator. |
| `apps/web/src/pages/DashboardPage.tsx` | Show **Unavailable** for null ROI / savings instead of `$0` / `N/A%`. |

**Did not:** invent savings, ROI, or empirical portfolio dollars.

### Before / after (API shape)

**Before:** `total_cost_impact: -525611323.26`, `roi_estimate_pct: 357.6`, `member_count: 0`  
**After (code):** `total_cost_impact` = sum of policy ΔPMPM (`total_cost_impact_unit: pmpm_sum`), `roi_estimate_pct: null`, UI labels Unavailable / Σ ΔPMPM.

---

## P1 — Cold-start

### Measurements (deployed Azure API, already warm App Service)

See `COLD_WARM_TIMINGS.json`.

| Endpoint | First after login | Warm mean (3×) |
|----------|-------------------|----------------|
| `/health` | ~1.0s | ~1.0s |
| `/dashboard/summary` | ~9.1s | ~9.3s |
| MRI observations latest | ~1.5s | ~1.3s |
| `/policy-verdicts` | ~2.2s | ~1.8s |

Dominant delay: **dashboard summary DB aggregation**, not pure App Service cold-start in this sample (instance already warm). True cold start after idle scale-down was not forced (would require stopping the app — out of scope without approval).

### Safe improvement (no SKU change)

| File | Change |
|------|--------|
| `apps/web/src/pages/LoginPage.tsx` | Fire-and-forget `GET …/health` on login mount to reduce first interactive cold hit. |

No App Service plan / SKU changes.

---

## Regression / release checklist

| Gate | Status |
|------|--------|
| Known-answer MRI/MPPR/SOS fixtures rewritten | **No** |
| Alembic past 012 on demo | **No** |
| Unit test for latest_only+policy_id | Added (run in project venv before promote) |
| Isolated staging deploy + 013/014 | **Not run** (staging not approved) |
| Nine frozen workspaces browser | **Pending** after promote |
| Exact MRI/MPPR/SOS KA compare | **Pending** after promote |
| 289 verdicts + 28 what-if | **Pending** after promote |
| Deployed browser room path | **Pending** after promote |
| Production promote | **BLOCKED — need explicit approval** |

---

## Remaining demo risks (even after promote)

1. MRI Monitoring still shows `CATALOG_POLICY` / `NO_SYNTHETIC_KA` by design — narrate as class labels, not verdict.
2. Monthly `obs-mon-*` AT_RISK series still exist in DB; trends views may show them — Monitoring/Verdicts use latest period.
3. Executive portfolio $ ROI remains **Unavailable** until honest membership/paid baseline exists — do not quote ROI on camera.
4. Dashboard summary ~9s — prefetch before room demo.
5. Web + API must promote **together** (API list fix + web badge/panel fixes).

---

## Explicit verdict

**`DEMO_FREEZE_BLOCKED`**

Freeze of known-answer **data** is intact. Stabilization **code is ready** but must not go to the locked Azure demo until you approve promotion and the post-deploy regression list above is green. If anything fails after promote, revert API image to `dec4-freeze-89f742f`.

---

## Approval ask

Reply **approve promote** (API image tag + web App Service) to run: build/push → deploy → nine-policy + 289/28 + room-path browser → flip report to `DEMO_FREEZE_PASS` or revert.
