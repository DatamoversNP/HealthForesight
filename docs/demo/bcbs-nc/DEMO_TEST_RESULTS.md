# DEMO_TEST_RESULTS — Blue Cross NC executive demo path

**Test window:** 2026-11-01  
**UI:** https://data-voyager.vercel.app  
**API:** https://healthforesight-api.azurewebsites.net/api/v1  
**Login used:** `admin@healthforesight.com` (seed user)  
**Hero policy:** Outpatient MRI Prior Authorization — `d403f101-08dd-45c9-ab83-d42e37c62018`

A successful HTTP status alone is **not** treated as pass. Pass requires visible/correct UI or verified payload fields.

---

## Demo route map (Phase 1 + Phase 3)

| # | Module | Exact URL | Record ID | Data source | Expected visible metrics | User action | Verification | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | Executive Dashboard | `/dashboard/executive` | n/a | `/dashboard/summary`, policy-performance | Portfolio pulse, active policies | Open after login; switch persona if needed | Page title Executive Dashboard; metrics render | **PASS** (UI loaded). **WARN:** absolute $ totals look portfolio-inflated — do not quote on camera |
| 2 | Policy selection / objectives | `/policies/workspace/d403f101-08dd-45c9-ab83-d42e37c62018` | policy `d403f101-…` | `/policies/{id}` | Name, PRIOR_AUTH, ACTIVE, description | Open Overview; optional Scope/Levers | Heading “Outpatient MRI Prior Authorization” visible | **PASS**. Soft fail: empty formal objectives metadata — use description |
| 3 | Policy-specific baseline | `/baseline-analysis` | baseline `9f996021-60b9-4252-8e84-cacac048cca8` | `/baselines?policy_id=` | Policy baseline 2025 window; claims/members | Select MRI policy baseline (not General) | UI showed “Outpatient MRI Prior Authorization Baseline 2025-01-01_2025-12-31…” | **PASS** |
| 4 | Predicted impact | `/predicted-impacts` | predicted-impact for MRI | `/policies/{id}/predicted-impact` | ~−14.4% util, ~−13% cost | Find MRI row | “Outpatient MRI Prior Authorization” + many −14.4% cells present | **PASS** (payload + UI). **WARN:** page N+1 loads slowly |
| 5 | Observation analysis | `/observation-analysis?observation=b227220e-f9e0-45a6-8938-d55aad1fe25d` | obs `b227220e-…` | `/observations/{id}` | ~442.2 per 1k; vs baseline % | Deep-link observation | MRI name + 442.2 per 1K visible | **PASS**. **WARN:** absolute denominators ≠ policy baseline members |
| 6 | What-If (safe) | `/whatif/scenarios` | analysis `f73e506f-ace5-4815-aefb-979367621212` | `/analyses?analysis_type=SIMULATE` + results | Completed scenario list / open results | Prefer completed run | Scenario runs page loads with Open links | **PASS** (list). Live re-run **not** required for READY if completed open works |
| 7 | Policy verdicts (climax) | `/policy-verdicts` | obs `b227220e-…` | `/policy-verdicts` (post `latest_only` deploy) | Verdict **ON_TRACK** / Saving / on track | Search MRI | API + UI: ON_TRACK, util −10.1%, cost −12.5% | **PASS** (verified 2026-11-01 after deploy) |
| 8 | Close | `/dashboard/executive` | n/a | same as #1 | Calm end frame | Return | Loads | **PASS** |

---

## API probes (supporting)

| Check | Result |
|---|---|
| Login | 200 ~1.5–2s |
| Policies include MRI | PASS (among 268) |
| Policy-specific baselines for MRI | 3 rows; canonical 2024-12-31→2025-12-31 |
| Predicted impact JSON | PASS — ELASTICITY_MODEL, util −14.4%, cost −13.0%, substitution block |
| Observations for MRI | 28 rows; latest `b227220e` ON_TRACK |
| `/policy-verdicts` MRI row | **PASS — ON_TRACK** after `verdicts-latest-*` deploy |
| `/observations?latest_only=true&limit=500` includes MRI | PASS — proves fix approach |
| Completed What-If for MRI | PASS — `f73e506f-…`, `95283231-…` |
| Failed historical What-If | `PRIOR AUTH` enum errors (pre-normalize); avoid those IDs |

---

## Console / network notes (browser)

- Login and executive path completed without hard navigation failure.
- Predicted Impacts is heavy (per-policy fetches) — allow load time in rehearsal; do not spam Refresh.
- No separate full CDP console harvest attached to this report; re-run with DevTools open before recording day.

---

## Defects found

| ID | Severity | Defect | Evidence | Fix status |
|---|---|---|---|---|
| D1 | **Blocker (resolved)** | Policy verdicts omit policies whose observations fall outside first 500 by `computed_at` | Pre: MRI UNKNOWN. Post-deploy: MRI ON_TRACK | **Fixed + deployed** (`latest_only=True` in `list_policy_verdicts_route`; image `verdicts-latest-*`) |
| D2 | High (narration) | Absolute denominators inconsistent across baseline vs latest observation | Baseline 2,382 members vs obs 13,997; util levels 217 vs 491 | No product change in this phase — director board restricts narration to % changes |
| D3 | Medium | Formal objectives empty on policy metadata | `policy_metadata_json` empty | Soft — use workspace description/scope |
| D4 | Medium | Policy scope markets NYC/DFW | Scope JSON | Soft — illustrative disclaimer |
| D5 | Medium | Executive dashboard absolute $ figures unreliable for client quote | UI showed ~$525M total cost impact | Soft — do not read absolute $ aloud |
| D6 | Low | Predicted Impacts overview slow | N+1 `getPolicyPredictedImpact` | Soft — filter quickly to MRI |

---

## Defects fixed in this session (with test evidence)

| Fix | Change | Test evidence | Deployed? |
|---|---|---|---|
| D1 verdicts truncation | `list_observations(..., latest_only=True, summary=True, limit=500)` in verdicts route | Post-deploy probe: MRI `ON_TRACK`, obs `b227220e-…`, util −10.06%, cost −12.48% | **Yes** |

No other product modules built. No schema/ingestion changes.

---

## Rehearsal status

| Rehearsal | Timed path | Result |
|---|---|---|
| #1 | 270.4s (4:30) | **PASSED** — all 8 beats OK; MRI verdict Saving / on track |
| #2 | 279.8s (4:40) | **PASSED** — all 8 beats OK; predicted via overview or catalog dialog fallback |
| Method | Playwright against data-voyager.vercel.app; login+prefetch outside clock | Artifacts: `/tmp/bcbs_nc_rehearsals.json` |

Note: Predicted Impacts overview search can be flaky under load — director board should prefer Search policies… for MRI, with Policy Catalog → Predicted Impact dialog as fallback (validated in rehearsal #2).

---

## READY?

**YES — for recording against current Azure API + Data Voyager**, with caveats in DEMO_DATA_VALIDATION.md (speak % changes only; illustrative data; prefer completed What-If if live simulate is slow).
