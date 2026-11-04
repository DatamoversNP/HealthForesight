# Step 1 — Database-backed audit of the current 283 policies

**Generated:** 2026-11-03 (live Azure Postgres via demo7867 stack)  
**Artifacts:**  
- `docs/demo/bcbs-nc/evidence/POLICY_INVENTORY_283_AUDIT.json` (full per-policy rows)  
- `docs/demo/bcbs-nc/evidence/POLICY_INVENTORY_283_AUDIT.csv`

## Verdict (non-negotiable)

**The 283 catalog rows are not the requested authoritative BCBS NC + Medicare + NCCI policy universe.**

They are predominantly an **illustrative Blues/NC-aligned demo catalog** seeded from `scripts/demo/catalog/bcbs_nc_aligned_policy_catalog.json` (244 policies explicitly tagged `not_verbatim_bcbsnc_policy: true` with an accuracy contract that forbids claiming verbatim Blue Cross NC text).

Having baseline / prediction / observation **rows** for many of these policies proves the **platform lifecycle plumbing** works on demo claims. It does **not** prove:

- authoritative source ingestion,
- reconciled inventory completeness,
- BCBS NC proprietary policy fidelity,
- CMS NCD/LCD/article population,
- quarterly NCCI PTP/MUE population,
- or mechanism-correct reimbursement analytics (vs MRI-style util formulas reused on payment policies).

## Quantitative snapshot (tenant `00000000-0000-0000-0000-000000000001`)

| Metric | Count |
|--------|------:|
| Policies in DB | 283 |
| Claims lines available | 3,505,919 |
| With baseline artifact | 257 |
| With predicted impact artifact | 268 |
| With observation artifact | 265 |
| Verdict-ready (latest observation has verdict_status) | 265 |
| Baseline + prediction + observation present | 257 |
| Policy versions present | 47 |
| Code sets attached | **0** |
| Source organization / document URL / provenance in metadata | **0** |

### Lifecycle buckets

| Bucket | Count |
|--------|------:|
| Full baseline+predict+observe artifacts | 257 |
| Predict+observe, no baseline | 8 |
| Predict only | 3 |
| Catalog only (no analytical artifacts) | 15 |

### Named Medicare / edit artifacts in catalog titles

| Pattern | Count |
|---------|------:|
| Name contains NCD | 1 |
| Name contains LCD | 1 |
| Name contains NCCI | 1 |
| Name contains MUE | 1 |
| Name contains “reimburs” | 1 |

Heuristic family tagging (type/name keywords only — **not** reconciled source inventory): ~19 payment/reimbursement-typed rows; medical/UM-typed rows dominate; **CMS adapter status remains NOT_IMPLEMENTED / fixture-only**.

## Requested universe vs what exists

| Policy family | Required | Discovered (authoritative) | Ingested | Configured w/ provenance | Baselined (eligible) | Predicted | Observed | Verdict-ready | Blocked |
|---------------|----------|------------------------------|----------|---------------------------|----------------------|-----------|----------|---------------|---------|
| BCBS NC reimbursement (all published accessible) | Complete inventory + lifecycle | **0 reconciled** (19 illustrative payment-named rows) | No | No | Demo artifacts only | Demo | Demo | Demo | No BCBS NC source adapter; proprietary text not public |
| BCBS NC medical / UM | Complete | **0 reconciled** (illustrative PA/UM catalog) | Partial seed | No provenance | Demo | Demo | Demo | Demo | Same |
| BCBS NC admin / pricing | Complete | **0 reconciled** | No | No | Demo | Demo | Demo | Demo | Same |
| CMS NCD (in-scope) | All applicable versions | **0** (1 illustrative name) | No | No | — | — | — | — | MCD API requires auth token; public MCD downloads 403 from this host |
| MAC LCD (NC / Palmetto JM) | NC-relevant + history | **0** (1 illustrative name) | No | Fixture-only | — | — | — | — | Same |
| Billing/coding articles | Linked articles | **0** | No | Fixture-only | — | — | — | — | Same |
| NCCI PTP quarterly | All applicable edits | **0** (1 illustrative “NCCI and MUE…” policy) | No | No | — | — | — | — | No quarterly file ingest; CMS site 403 here |
| NCCI MUE | Available unit edits | **0** | No | No | — | — | — | — | Confidential MUE handling + no ingest |
| Other Medicare payment rules | MPPR, global, fee schedule, etc. | Illustrative names only (e.g. MPPR row) | No | No | Demo util-style metrics risk | Demo | Demo | Demo | Need payment-semantics engine |
| Payer-specific adaptations | Verified BCBS NC adopt/modify/exception | **0** | No | No | — | — | — | — | Requires payer-authorized mapping |

## Critical examples

| Policy | What DB shows | What it is **not** |
|--------|---------------|--------------------|
| Outpatient MRI Prior Authorization | PRIOR_AUTH; baseline/predict/observe present; OH/PV `ON_TRACK` | Not a verbatim Blue Cross NC medical policy; metadata still carries non-NC markets in some fields; analytics run on **demo** claims |
| NCCI and MUE Claims Edit Policy | PAYMENT_POLICY with demo lifecycle artifacts | Not a quarterly CMS NCCI PTP/MUE release ingest |
| Multiple Procedure Payment Reduction | PAYMENT_POLICY with demo artifacts | Not proven to use MPPR payment semantics vs util-change formulas |

Source catalog contract (`bcbs_nc_aligned_policy_catalog.json`):

> *“Not claiming: Verbatim Blue Cross NC medical policies… Proprietary BCBS NC policy text is not publicly reproducible at 100% fidelity.”*

## Missing capabilities (implementation backlog started after this audit)

1. Authoritative source adapters + reconciled inventory tables (BCBS NC authorized export, CMS MCD, NCCI files).
2. Persist provenance (source org, document id, URL, version, as-of) on every ingested policy version.
3. Code sets / rule structures per mechanism (currently **0** code-set rows).
4. Mechanism-specific baseline/prediction/observation engines (reimbursement ≠ MRI util).
5. Explicit `NOT_YET_OBSERVABLE` / `INSUFFICIENT_DATA` / `UNSUPPORTED_SEMANTICS` readiness — never silent synthetic-as-empirical.
6. Coverage dashboard fed by reconciled inventory, not catalog heuristics.
7. Re-run Objective Health browser gates after catalog expansion.

## Data dependency (explicit)

Public CMS / BCBS NC **documents supply rules**. Empirical baselines and observations require payer historical claims, enrollment, payment, authorization, and policy-effective-date data. This environment has **3.5M demo/synthetic-oriented claims lines** — usable for plumbing and labeled synthetic scenarios, **not** for claiming actual Blue Cross NC financial experience.

## December 4 readiness (after Step 1)

| Gate | Status |
|------|--------|
| Objective Health browser stability | **PASS** (prior milestone) |
| Authoritative comprehensive inventory | **FAIL** |
| Seven representative real-source lifecycle demos | **FAIL** (MRI path is demo/illustrative + synthetic causal fixtures) |
| Overall Dec 4 “complete policy population” | **NOT READY** |
