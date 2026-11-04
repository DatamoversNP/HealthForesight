# HealthForesight — Enterprise Policy Coverage, Lifecycle Completeness & Objective Health

**Mission:** Platform-wide policy coverage and analytical completeness — not demo-specific features.  
**Date:** 2026-11-03  
**Order of work:** (1) Objective Health stability → (2) authoritative inventory → (3) applicability/composition → (4) policy-specific analytical engines → (5) UI readiness states → (6) Dec 4 qualification.

---

## Phase 1 — Objective Health (P0 release blocker)

### Reproduced root causes (code inspection + fixture tests)

| Defect | Evidence | Impact |
|--------|----------|--------|
| Silent multi-API fallbacks | Client `Promise.all([...].catch(() => [] / null))` | Partial failures flipped counts/status without error |
| Dual status engines | Verdicts when present; else `deriveStatus(perf)` heuristics | Same policy could be on_track vs no_data across refreshes |
| Predicted treated as observed | `/dashboard/policy-performance` fills util/cost from predicted impact when `observations_count=0` | Fabricated “health” without observations |
| Nondeterministic forecast probe | Client N+1 `getPolicyPredictedImpact` on `.slice(0,40)` without stable sort | Objective A/F counts changed with catalog order / timeouts |
| Race on remount | No request generation guard | Stale response could overwrite newer snapshot |

### Fix shipped this increment

- Authoritative API: `GET /api/v1/dashboard/objectives-health`
- Pure builder: `services/objectives_health.py` (`calculation_version: objectives-health-v1`)
- Status = same `compute_verdict` as `/policy-verdicts`
- Forecasts = persisted `list_latest_predicted_impacts` only
- UI uses single endpoint; stale-response discard; refresh errors do not wipe prior good data with empty synthetic state
- Regression tests: `apps/api/tests/test_objectives_health_stability.py`

### Stability contract

Same tenant, policy set, observations, predicted impacts, decisions, calculation version → identical snapshot (aside from `generated_at`).

**Browser regression still required before Dec 4 demo-ready claim:** refresh, navigate away/back, concurrent tabs, API delay, restart. Not yet executed in this increment.

---

## Coverage & implementation gap matrix

Statuses: **MISSING** | **SCAFFOLD** | **PARTIAL** | **IMPLEMENTED** | data: **NONE** | **SYNTHETIC** | **REAL** | **PROD_QUALIFIED**

| Area | Status | Data | Gap |
|------|--------|------|-----|
| Objective Health determinism | IMPLEMENTED | REAL inputs when present | Browser gates 1/4/7 PASS; re-smoke PASS after catalog stamp |
| BCNC commercial reimbursement inventory | SCAFFOLD | NONE authoritative | Adapter + inventory tables live; drop-dir INACCESSIBLE until payer export |
| BCNC Medicare reimbursement inventory | SCAFFOLD | NONE | Same — INACCESSIBLE without authorized export |
| BCNC medical / admin / pricing inventory | PARTIAL | Illustrative catalog (244/283 flagged) | **Not** verbatim BCBS NC; stamped `enterprise_classification` |
| CMS NCD inventory (MCD API) | SCAFFOLD | NONE | Adapter supports token + JSONL drop; currently INACCESSIBLE (no token/files) |
| MAC LCD + articles (NC / Palmetto JM) | SCAFFOLD | Illustrative fixtures | Drop-dir adapter ready; live filter not productionized |
| NCCI PTP / MUE versioned files | SCAFFOLD | NONE | Quarterly file drop adapters; MUE never fabricated |
| Inventory reconciliation / completeness manifest | PARTIAL | DB inventory rows | `POST /enterprise/policy-sources/reconcile` + coverage API; complete=false |
| Analytical readiness flags (CONFIGURED→IMPACT_ASSESSABLE) | MISSING | NONE | Independent capability flags needed |
| Policy Analysis Contract (metric/unit/snapshot/calc version) | PARTIAL | MRI path | Not enforced cross-family |
| Reimbursement analytical engine | MISSING | NONE | Must not model as util-reduction by default |
| Coverage (NCD/LCD) analytical engine | SCAFFOLD | Fixtures | Historical policies may be OBSERVATION_READY without IMPACT_ASSESSABLE |
| Causal for all policies | PARTIAL | MRI synthetic DiD | Unsupported → INCONCLUSIVE/NOT_ESTIMABLE, never invent |
| Unified verdict evidence | PARTIAL | Synthetic enterprise tabs | Must reference readiness + real lineage |
| Portfolio coverage view (inventory vs analytical ready) | MISSING | NONE | Numbers must come from reconciled status only |
| UI readiness states (unavailable vs complete) | PARTIAL | Enterprise tabs | Empty dashboards must not look “done” |

### Non-negotiable (enforced in design)

- No fabricated policies, sources, financials, or clinical outcomes
- No silent synthetic-as-empirical
- Public docs ≠ exact plan-specific payment outcomes (BCNC pricing principles)
- Original Medicare LCD/NCCI ≠ automatic commercial or MA applicability
- LLMs assist extraction only; cannot authorize activation/applicability
- Not an unauthorized claims adjudication system
- Preserve existing ingestion, raw tables, policy IDs, lifecycle APIs

---

## Analytical readiness (target model)

Independent flags per policy version:

`CONFIGURED` · `BASELINE_READY` · `FORECAST_READY` · `OBSERVATION_READY` · `IMPACT_ASSESSABLE`

- Reimbursement: primary metrics = unit price, paid/allowed, edit/denial — utilization secondary with separate evidence
- NCD/LCD long in force: may be observation-ready without defensible original causal estimate
- Causal required in the lifecycle UI for every policy: supported, inconclusive, or not estimable — never invented

---

## December 4 experience (target)

Catalog filters: Commercial, MA, Original Medicare, reimbursement, NCD, LCD, NCCI, NC applicability.

Same workspace shell as MRI; mechanism-appropriate engines; explicit missing-evidence messages.

Portfolio coverage table (values from reconciled inventory/jobs only):

| Policy family | Inventory | Baseline | Forecast | Observed |
|---------------|-----------|----------|----------|----------|
| BCNC reimbursement | — | — | — | — |
| BCNC medical | — | — | — | — |
| CMS NCD | — | — | — | — |
| NC-applicable LCD | — | — | — | — |
| NCCI edits | — | — | — | — |

100% catalog ≠ 100% analytical readiness — both measured independently.

---

## Next increments (ordered)

1. Complete Objective Health browser regression + document pass/fail
2. Coverage manifest schema + source adapter interfaces (MCD, NCCI, BCNC published indexes) — discover/reconcile before bulk UI
3. Persist analytical readiness flags on policy versions
4. Reimbursement analysis contract + engine skeleton (no fake numbers)
5. Portfolio coverage API/UI wired to manifest statuses
6. Causal/verdict path for every configured policy with explicit not-estimable

**This increment does not claim inventory completeness or production qualification.**
