# Blue Cross NC — December 4 Enterprise Readiness

Source: post-demo discussion (`Discussion from demo.docx`) + Dec 4 integration/validation gate.  
Date of audit: 2026-11-03 (re-verified against code, not prior completion summaries).

## Questions BCBS NC raised → P0 capabilities

| Question | Product extension | Dec 4 acceptance |
|----------|-------------------|-------------------|
| Policies of different sizes/shapes | Composable policy model (domain + mechanisms + rules + provenance) | Load PA, composite, reimbursement through same lifecycle |
| Did the policy cause the change? | Causal Impact Workbench | Observed vs counterfactual, assumptions, limitations on validated fixture |
| How do providers respond? | Provider Behavior Explorer | Before/after + comparison-adjusted signals; no intent claims |
| New policy / no history? | Cold-start evidence tiers A–D | Tiered forecast; assumptions explicit |
| Reimbursement / NCD / LCD / CCI / NC localization | Applicability Explorer | Palmetto JM + NCD/LCD/article + one NCCI/reimbursement example |
| How do these connect? | Unified verdict evidence | Three independent assessments (forecast / causal / governance) |

## Verified capability matrix (2026-11-03)

Statuses: **IMPLEMENTED** | data: **TESTED_WITH_SYNTHETIC_DATA** | **TESTED_WITH_REAL_DATA** | **PRODUCTION_QUALIFIED**

| Capability | Code status | Data status | Real vs fixture | Notes |
|------------|-------------|-----------------|-----------------|-------|
| Policy Composition | IMPLEMENTED | SYNTHETIC / inferred | Fixture + catalog-type inference | Hierarchy/version present for MRI & coding; not persisted rule engine on all rows |
| Causal Impact (DiD) | IMPLEMENTED | SYNTHETIC | Labeled fixture `bcbs_nc_mri_did_v2` | Unit = INDEX_POINTS (Jan=100). Not util/1k. Not production claims |
| Provider Behavior | IMPLEMENTED | SYNTHETIC | Fixture (behavior_profiles empty) | Peer criteria explicit; API small-cell suppression |
| Cold Start | IMPLEMENTED | SYNTHETIC | Tier C scenario ranges | Assumption records with source/version/date |
| Medicare Applicability | IMPLEMENTED | SYNTHETIC (illustrative IDs) | NC→Palmetto JM example | Distinguishes FFS / MA / commercial; superseded & no-match |
| Verdict integration | IMPLEMENTED | SYNTHETIC | `/verdict-evidence` + workspace tab | Three assessments; not one opaque score |
| **Production qualified** | **NO** | — | — | No complete real-claims causal design; empty behavior store; illustrative CMS sources |

API inventory: `GET /api/v1/enterprise/implementation-inventory`

## Causal methodology validation (MRI fixture)

Formula:

\[
\widehat{\text{DiD}} = (Y_{T,post}-Y_{T,pre})-(Y_{C,post}-Y_{C,pre})
\]

Independent recalculation from `MRI_SERIES` (verified in tests):

| Quantity | Value (index points) |
|----------|----------------------|
| \(Y_{T,pre}\) (Jan–Apr) | 99.5 |
| \(Y_{T,post}\) (May–Jul) | 84.6667 |
| \(Y_{C,pre}\) | 99.75 |
| \(Y_{C,post}\) | 94.3333 |
| Naive pre/post (treatment Δ) | **−14.833** |
| Control Δ | **−5.417** |
| DiD incremental | **−9.417** |
| Naive − DiD | **−5.417** (= control Δ) |
| Planted known true | −9.4167 |
| Recovery within ±0.05 | **PASS** |

**Unit:** indexed utilization (Jan=100). Explicitly **not** utilization per 1,000 member-months.

**Cohorts:** deterministic fixture treatment vs comparison populations with parallel pre-trends by construction.

**Validation suite** (`GET /api/v1/enterprise/causal/validation-suite`):

| Case | Expected | Result |
|------|----------|--------|
| known_effect | Recover ≈ −9.417 | PASS |
| no_effect | DiD ≈ 0 | PASS |
| confounded_common_shock | Naive large, DiD ≈ 0 | PASS |
| parallel_trend_violation | Diagnostic FAIL → INCONCLUSIVE | PASS |

Passing DiD arithmetic **does not** establish causal validity on BCBS NC claims. Identification assumptions must hold on real data.

## Provider behavior validation

- Peer selection: specialty + market + volume quartile (not statewide average).
- Denominators attached per signal.
- `n < 30` → values nullified in **API payload** (not UI-only).
- No intent / circumvention language.
- Gap: `behavior_profiles` empty in demo DB — not TESTED_WITH_REAL_DATA.

## Cold-start validation

- Tier C when no direct intervention history.
- `assumption_records`: source, version, as_of, applicability, uncertainty rationale.
- Scenario range only; `not_a_point_estimate: true`.
- Recalibration rule: do not auto-promote Tier C → empirical forecast.

## Applicability validation

| Query | Status |
|-------|--------|
| Original Medicare FFS + NC | MATCHED_FFS_CHAIN (NCD/LCD/article/NCCI) |
| Medicare Advantage | NO_AUTOMATIC_FFS_CHAIN |
| Commercial | PAYER_POLICY_MATCH |
| as_of before LCD | SUPERSEDED_DOCUMENT |
| Non-NC state | NO_MATCH_JURISDICTION |

Non-adjudication disclaimer retained.

## Unified verdict evidence

`GET /api/v1/enterprise/policies/{id}/verdict-evidence`

Three independent assessments (example MRI + ON_TRACK observation):

| Assessment | Example result |
|------------|----------------|
| forecast_performance | WITHIN_EXPECTED_RANGE |
| causal_evidence | SUPPORTED_EFFECT (synthetic DiD) |
| policy_governance | MAINTAIN |

References composition, causal summary, provider behavior, cold-start (when specialty), applicability. Immutable lineage note preserved.

Workspace tab: **Verdict Evidence**.

## Data / capability feasibility (current demo stack)

| Capability | Available now | Gap | Dec 4 approach |
|------------|---------------|-----|-----------------|
| Policy catalog + types | Strong (31 types; enterprise extensions seeded) | Flat type still primary; multi-mechanism not first-class on all rows | Additive composition metadata + workspace panel |
| Baseline → predict → observe → what-if → verdict | Working for MRI demo path | Observation verdict not yet auto-wired into enterprise evidence | Verdict-evidence API + workspace tab; optional observation_verdict query |
| Causal DiD engine | Exists (`analyses_file`, `analytics/impact.py`) + fixture workbench | Not run on BCBS NC claims aggregates | Fixture-validated Causal Workbench + validation suite |
| Provider behavior store | API exists; `behavior_profiles`/`clusters` empty (0 rows) | No empirical provider signals in demo DB | Deterministic labeled fixture + explorer UI |
| Claims lines | Table present (count times out — large) | Hard to use interactively without aggregates | Prefer aggregates + fixtures; do not invent claim-level “results” |
| Cold-start | Tier model + provenance | Not empirically calibrated | Tier C scenario API |
| Medicare NCD/LCD/NCCI | Explorer implemented | No live CMS MCD ingestion | Illustrative NC/Palmetto JM chain |
| Auth decision logs | Not confirmed in demo DB | Limits “authorization response” behavior | Show as unavailable unless data present |

## Architecture rules (must keep)

- Additive contracts only; keep existing `policy_type` identifiers.
- Never label naive pre/post as causal.
- Never infer provider intent.
- Never auto-adjudicate claims from NCD/LCD text.
- Label synthetic / fixture results explicitly.
- AI remains advisory.
- Do not collapse forecast / causal / governance into one opaque score.
- Do not deploy until local validation passes; preserve existing ingestion/storage.

## Delivery slices

1. Feasibility matrix (this doc) — **updated with verification**
2. Domain contracts + `/api/v1/enterprise/*` fixtures
3. Policy Workspace tabs: Composition, Causal Impact, Cold Start, Applicability, Behavior, **Verdict Evidence**
4. Automated tests: DiD recovery, validation suite, suppression, applicability branches, verdict assessments
5. Remaining for production: real-claims causal design, populated behavior store, authoritative CMS source versions, reimbursement lifecycle end-to-end on non-fixture metrics

## December 4 demo readiness assessment

| Criterion | Ready? |
|-----------|--------|
| MRI as central vertical slice (composition → causal → behavior → verdict) | Yes (synthetic causal/behavior) |
| Show why naive ≠ causal (−14.8 vs −9.4 index points) | Yes — unit = INDEX_POINTS (Jan=100), not absolute util rate |
| Unified verdict evidence contract | Yes (API + workspace tab; synthetic) |
| Objective Health ↔ Policy Verdicts same engine | Unit invariant **PASS**; browser gates 1/4/7 **PASS** (MRI `ON_TRACK` aligned) — see `OBJECTIVES_HEALTH_STABILITY.md` |
| Policy Coverage & Analytical Readiness Reconciliation Gate | Scaffolded (`/enterprise/reconciliation-gate` + unit tests) — not inventory-complete |
| Reimbursement/coding composition path | Composition + commercial applicability only — **not** full reimbursement lifecycle |
| Cold-start specialty path with provenance | Yes (Tier C) |
| NCD/LCD/NCCI NC localization story | Illustrative — not authoritative CMS MCD/NCCI adapters |
| Production / real-claims qualified | **No** |
| Additional disconnected dashboards | **Do not build** |

### Release gates (agreed sequence)

1. **Close Objective Health browser regression** — **DONE** (rows 1/4/7 PASS; evidence under `docs/demo/bcbs-nc/evidence/`).
2. **Authoritative policy ingestion** (CMS MCD, NCCI, Blue Cross NC) — **in progress**. Step-1 audit proves the 283 rows are mostly illustrative (`not_verbatim_bcbsnc_policy`); source adapters + `policy_source_*` tables + reconcile API are live; all families currently **INACCESSIBLE** until authorized exports / `CMS_COVERAGE_API_TOKEN` / NCCI drop files are provided (`docs/demo/bcbs-nc/POLICY_POPULATION_STEP1_AUDIT.md`).
3. **Reimbursement lifecycle** on one real, source-grounded mechanism (rate / util / coding / mix distinguished). **Open** — must not reuse MRI util formulas.

**Dec 4 “demo ready” declaration:** Objective Health stability blocker is closed. **Complete policy population is NOT ready** (0 authoritative source documents ingested). Do not report “all policies loaded.” Next unblockers: payer-authorized BCBS NC exports, CMS MCD token or NCD/LCD JSONL drops, quarterly NCCI files under `data/policy_sources/`.

**Overall:** Foundational enterprise slices are taking shape. Largest remaining gap is breadth of authoritative policy coverage and depth of reimbursement analytics — not more UX. Synthetic MRI causal/verdict story remains valid for capability demonstration only when every synthetic label stays visible.
