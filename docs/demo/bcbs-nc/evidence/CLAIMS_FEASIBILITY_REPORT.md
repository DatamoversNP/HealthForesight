# Claims Feasibility Report — 3.5M Demo Lines

**Generated:** 2026-11-03T09:27:12Z  
**Table:** `claims_lines`  
**Row count:** 3,505,919  
**Machine-readable:** `CLAIMS_FEASIBILITY_REPORT.json`

## Provenance / synthetic classification

| Signal | Result |
|--------|--------|
| `source_system` (2% sample) | Dominantly `DATA_GENERATOR`; also `Q1_2026_DEMO`, `synthetic_historical_loader`, `MONDAY_DEMO_5` |
| Classification | **DEMO / SYNTHETIC** analytical substrate |
| Must not claim | Actual Blue Cross NC claims or outcomes |
| Known-answer workflows | Supported when labeled synthetic and independently validated |

Enrollment: `enrollment_records` ≈ **43,200** rows with member-month grain columns (`enrollment_month`, `lob`, `market`, `enrolled_flag`, start/end dates).

---

## Available columns (37)

`id`, `tenant_id`, `claim_id`, `claim_line_id`, `member_id`, `provider_id`, `service_date`, `paid_date`, `adjudication_date`, `lob`, `market`, `cpt_code`, `hcpcs_code`, `drg_code`, `icd10_diagnosis_codes`, `icd10_procedure_codes`, `service_category`, `place_of_service`, `units`, `allowed_amount`, `paid_amount`, `member_cost_share`, `in_network`, `requires_prior_auth`, `prior_auth_approved`, `prior_auth_id`, `facility_type`, `system_affiliation`, `rendering_provider_id`, `billing_provider_id`, `referring_provider_id`, `source_system`, `source_file_id`, `ingestion_id`, `record_hash`, `created_at`, `updated_at`

---

## Date / member / provider coverage

| Metric | Value |
|--------|-------|
| Service date min–max | **2023-01-01** → **2026-10-29** |
| 2% TABLESAMPLE | n=68,945; members≈11,942; providers≈423 |
| Pre/post history | Multi-year span — sufficient for demo DiD / MRI-style windows when policy effective dates align |

---

## Field completeness (2% sample null rates)

| Field | Null % | Implication |
|-------|-------:|-------------|
| `cpt_code`, `units`, `allowed_amount`, `paid_amount`, `place_of_service`, `lob`, `market`, `paid_date`, `in_network`, `requires_prior_auth` | ~0% | Strong for UM / reimbursement demos |
| `hcpcs_code` | ~1% | Mostly present |
| `facility_type` | ~0.6% | Usable |
| `icd10_diagnosis_codes` | **~98.7%** | Diagnosis-driven eligibility weak |
| `prior_auth_id` | **100%** | Auth ID join empty despite flag columns |
| `prior_auth_approved` | **~99.5%** | Sparse PA outcomes |
| `adjudication_date` | **100%** | No adjudication lag analysis |
| `drg_code` | **100%** | Inpatient DRG mechanisms blocked |

---

## Mechanism → data eligibility matrix

| Mechanism | Required fields (core) | Schema eligible? | Population / quality gate | Verdict |
|-----------|------------------------|------------------|---------------------------|---------|
| Utilization / UM | CPT, service_date, member_id, units, allowed, paid | Yes | Densely populated | **Feasible** for synthetic UM baselines |
| Reimbursement / pricing | CPT, units, allowed, paid, POS, lob | Yes | Densely populated | **Feasible** for labeled synthetic reimbursement |
| Coding edits (basic) | CPT/HCPCS, units | Yes | Present | Partial — **no modifiers** |
| NCCI PTP / modifier analytics | modifier(s) | **No columns** | — | **Blocked at schema** |
| Prior auth workflow | PA flags + id + approved | Columns exist | IDs/outcomes nearly empty | **Structurally present, analytically thin** |
| Provider behavior | provider / rendering / billing IDs | Yes | ~423 providers in sample | **Feasible** for demo peer panels |
| Enrollment denominators | member-months | Via `enrollment_records` | 43.2k rows | **Feasible** if joined carefully |
| Denials / adjustments | denial_reason, adjustment_amount, claim_status | **Missing** | — | **Blocked** |
| Claim maturity / reversals / replacements | claim_status, replacement_claim_id, void_indicator | **Missing** | — | **Blocked** — do not treat lines as final paid without maturity model |

---

## Policy-to-data eligibility (demo implications)

| Policy pattern | Can run synthetic lifecycle? | Caveat |
|----------------|------------------------------|--------|
| MRI / imaging UM (CPT + dates + $) | **Yes** — protect existing demo | Label synthetic; keep illustrative provenance |
| Commercial reimbursement exhibits | **Yes** on allowed/paid | Not BCBS NC fee schedules |
| Diagnosis-gated coverage | **Weak** | ICD sparse |
| NCCI PTP pair / modifier edits | **No** until modifiers (+ edit files) | Acquire NCCI + extend schema |
| Denial-pattern baselines | **No** | Need denial/adjustment/status |
| True empirical BCBS NC outcomes | **No** | Wrong data class entirely |

**Rule:** Do not calculate policy effects from insufficient fields. Synthetic claims may support a full calculation **workflow** if results are labeled synthetic and independently validated.

---

## Recommendations before mass baseline/forecast generation

1. Keep using the 3.5M lines for **Representative Payer** known-answer demos (MRI + selected reimbursement).
2. Do **not** mass-generate baselines for hundreds of new policies until mechanism × field gates pass per policy.
3. Extend schema only when needed: modifiers, claim_status / replacement, denial/adjustment — then backfill synthetic known answers.
4. Keep enrollment join for rate denominators; document grain.
5. Acquire CMS/NCCI **policy** sources separately; claims feasibility ≠ policy authority.
