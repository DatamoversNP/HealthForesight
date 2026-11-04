# Reimbursement Mechanism Correctness & Dec 4 Validation

**As of:** 2026-11-03T11:01Z  
**December 4 readiness claim: NOT made** (browser MPPR lifecycle pages pass; portfolio still mostly unvalidated)

## Sign convention (explicit)

| Field | Meaning |
|-------|---------|
| `payment_impact` / `payer_savings` | `baseline_paid − post_policy_paid`. **Positive = payer pays less** (provider receives less). |
| `provider_payment_change` | `−payment_impact` |
| `delta_payment_impact` / `delta_payer_savings` | Incremental **payer savings** vs base scenario. **+$120** for MPPR 50%→40% = additional payer savings, not higher provider payment. |
| `delta_provider_payment_change` | `−delta_payment_impact` (e.g. **−$120**) |

Surfaced in `PAYMENT_SIGN_CONVENTION` (`analytical_strategy_registry.py`), MPPR/SOS engines, and `GET /enterprise/reimbursement/mppr-vertical`.

---

## P0 — MPPR browser + independent finance

### Independent calculations

| Item | Value | Check |
|------|------:|-------|
| Baseline paid | $3,150 | pass |
| Post-policy paid (50% secondary) | $2,550 | pass |
| Payment reduction / payer savings | **$600** | pass |
| Volume / mix effects | $0 | pass |
| What-if secondary 40% post paid | $2,430 | derived |
| Incremental payer savings (50→40) | **+$120** | pass |
| Provider payment change (delta) | **−$120** | pass |
| Utilization metrics | `null` / absent | pass |

### Persisted what-if (API)

- Analysis `d3d3c332-5eb8-4cca-b1d9-1e5c33c83208` → **COMPLETED**
- Engine: `reimbursement_mppr_v1`
- `delta_payment_impact`: **120.0**
- `utilization_change_per_1k`: **null**
- Evidence: `MPPR_WHATIF_PERSISTED.json`

### Browser gates (`http://127.0.0.1:7868`)

Source: `browser_mppr/MPPR_BROWSER_GATES.json` + screenshots

| Step | Result |
|------|--------|
| Login | PASS |
| Policy workspace (MPPR) | PASS |
| Baseline analysis | PASS |
| Predicted impacts | PASS |
| Policy verdicts | PASS |
| What-if scenarios page | PASS |
| Objectives Health | PASS (rechecked) |
| Utilization elasticity label on MPPR pages | **not observed** |

Financial what-if numbers are verified via API persistence (not inferred from green fixtures alone).

---

## P1 — Mechanism registry (name short-circuit removed)

**Module:** `uepi_api/services/analytical_strategy_registry.py` (`analytical-strategy-registry-v1`)  
**Dispatch:** `reimbursement_whatif.py` + `whatif_runner.py`

| Behavior | Status |
|----------|--------|
| Resolve mechanism from versioned metadata (`enterprise_classification.mechanism` / `analytical_strategy`) | Yes |
| Select compatible engine | Yes |
| Validate required claim fields | Yes |
| Reject unsupported (modifiers / denials) | Yes — `REJECTED_UNSUPPORTED` |
| Prevent reimbursement → UM elasticity | Yes — hard fail if engine missing |
| Preserve MRI UM path | Yes — `UTILIZATION_MANAGEMENT` |
| Persist engine + calculation version | Yes — in what-if `result` |

**Regression tests:** `apps/api/tests/test_analytical_strategy_registry.py` — 9/9 PASS (inline runner).

API: `GET /enterprise/analytical-strategies`

---

## P2 — Second reimbursement vertical (site-of-service)

**Policy:** Freestanding Imaging Steerage (`d7441dd9-…`)  
**Mechanism:** `SITE_OF_SERVICE_PAYMENT_DIFFERENTIAL` (`reimbursement-sos-v1`)

| Item | Value |
|------|------:|
| Baseline paid | $4,000 |
| Post (hospital 80%) | $3,480 |
| Payer savings | **$520** |
| What-if hospital 80%→70% incremental savings | **+$260** |

Evidence: `SOS_REIMBURSEMENT_VERTICAL.json`. Modifier/denial mechanisms remain **BLOCKED**.

---

## Updated validation matrix

| Class | N |
|-------|--:|
| FULLY_VALIDATED_DEMO | **3** (MRI, MPPR, SOS) |
| ARTIFACTS_PRESENT_UNVALIDATED | 254 |
| PARTIAL | 11 |
| INAPPLICABLE_STAGE | 11 |
| BLOCKED | 4 |

Artifacts ≠ validated. Do not promote without calculation + workflow verification.

---

## P3 — Portfolio smoke

| Check | Result |
|-------|--------|
| OH API | 200; 283 / on_track 186 / at_risk 79 / no_data 18 |
| OH browser | PASS |
| Manifest v2 / Representative Payer labels | Active |

---

## Unresolved blockers

1. **254** policies still unvalidated for mechanism-specific math.
2. UI does not yet prominently display sign-convention copy on what-if screens (API does).
3. Fee-schedule engine registered but what-if not enabled (rejects without UM fallback).
4. Modifier / denial analytics blocked at schema.
5. Public CMS/NCCI inventory still incomplete (examples only).
6. Background what-if on API host previously failed when `uepi_worker` imported eagerly — fixed for reimbursement path; UM path still needs worker on PATH.

---

## December 4 readiness decision

**Not ready to claim full Dec 4 population readiness.**

**Credible demo scope:** MRI UM lifecycle + MPPR payment vertical (browser + persisted what-if + sign convention) + SOS payment differential known-answer + mechanism registry preventing elasticity contamination.

That is the defensible meeting narrative — not 283 validated policies.
