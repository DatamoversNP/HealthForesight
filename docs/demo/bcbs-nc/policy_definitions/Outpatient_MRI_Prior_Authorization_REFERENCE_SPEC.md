# Outpatient MRI Prior Authorization — Reference Policy Specification

| Field | Value |
|---|---|
| Document ID | `HF-RP-UM-MRI-001` |
| Platform policy ID | `d403f101-08dd-45c9-ab83-d42e37c62018` |
| Version | Draft v1.1 (reference-quality specification) |
| Date | 2026-11-03 |
| Intended market | North Carolina commercial products (Representative Payer) |
| Definition status | **DEFINITION_REVIEW_REQUIRED** — not approved for live enforcement |
| Synthetic analytics status | May remain **FULLY_VALIDATED_DEMO** independently |

---

## 0. Confidence statement (read first)

**This document is designed for maximum definitional integrity — not for a claim of empirically verified clinical or legal correctness.**

| Claim type | Confidence |
|---|---|
| Separation of policy / analytics / fixtures | **10/10** (architectural) |
| Explicit classification of every material assertion | **10/10** (architectural) |
| Correction of known Cursor config defects (NC vs NYC/DFW, E/M codes, LCD misuse) | **High** — grounded in live config + CMS Coverage API evidence already in-repo |
| Completeness as an operational clinical decision table | **Not established** — criteria schedule is required and currently **UNRESOLVED** |
| Production-ready, enforceable UM policy | **Not established** — operational activation **PROHIBITED** |

If any later draft claims “10/10 verified industry-standard policy” without attached approved clinical criteria, product schedule, compliance mapping, and source checksums, treat that claim as invalid.

Evidence classification used throughout:

| Tag | Meaning |
|---|---|
| `VERIFIED_SOURCE` | Traceable public source with version/date in this repo or CMS Coverage API snapshot |
| `REPRESENTATIVE_DESIGN` | Industry-aligned design choice for Representative Payer (not BCBS NC verbatim) |
| `SYNTHETIC_FIXTURE` | Deterministic demo/test value; never operative policy |
| `UNRESOLVED` | Must be decided/approved before operational use |
| `CONFIG_DEFECT` | Present in current platform config; must be corrected or quarantined |

---

## 1. Three-layer separation (normative)

| Layer | Purpose | May become operative rules? |
|---|---|---|
| **A. Policy definition** | Who / what / when / where / why / exceptions / decision outcomes | Yes — after approval |
| **B. Analytical assumptions** | Forecast/estimate parameters | **No** — never silently become rules |
| **C. Demonstration fixtures** | Known-answer calculations & workflows | **No** |

The currently configured platform object mixes all three. This specification forbids that.

---

## 2. Policy identity and intent

| Field | Value | Class |
|---|---|---|
| Name | Outpatient MRI Prior Authorization | REPRESENTATIVE_DESIGN |
| Family | Utilization management / prior authorization | REPRESENTATIVE_DESIGN |
| Goal | Prospective clinical review of selected **non-emergent outpatient MRI** requests against an **approved** evidence-based criteria schedule, while protecting access to medically necessary care | REPRESENTATIVE_DESIGN |
| Non-goals | Automatic denial; Medicare FFS claims adjudication; blanket MRI volume reduction; targeting unrelated E/M services; treating synthetic analytics as clinical authority | REPRESENTATIVE_DESIGN |

---

## 3. Applicability and exclusions

### 3.1 Include (`REPRESENTATIVE_DESIGN` pending product schedule)

- Covered **NC commercial** products listed in an approved product applicability schedule (`UNRESOLVED` — schedule not attached).
- Member eligibility and benefits checked as of requested service date.
- Prospective **non-emergent outpatient MRI** services in the approved CPT/HCPCS schedule (`UNRESOLVED` — schedule not approved).
- Network/site rules only after an approved site/network schedule (`UNRESOLVED`).

### 3.2 Explicit corrections to current platform configuration

| Current config | Required treatment | Class |
|---|---|---|
| `jurisdiction: NC` + `markets: NYC, DFW` | Contradictory. Markets must be NC (or removed until product schedule exists). NYC/DFW = **CONFIG_DEFECT** | CONFIG_DEFECT |
| Scope codes `99213`, `99214` | **Not** MRI PA targets. May appear only as contextual utilization covariates, never as authorization targets | CONFIG_DEFECT |
| Scope `72148`, `72149` vs lever `72148`, `72149`, `72158` | Scope and lever must share one approved code schedule; align or fail closed to `MANUAL_SCOPE_REVIEW` | CONFIG_DEFECT |
| Medicare links implying L34425/A56729 govern lumbar MRI | **Forbidden.** L34425/A56729 = orbit/face/neck only (`70540/70542/70543`) | VERIFIED_SOURCE (Coverage API A56729 enrichment + clinical applicability report) |
| Synthetic NCCI PTP pair labeled as CMS authority | Must remain `SYNTHETIC_FIXTURE`; never “authoritative published CMS edit” | SYNTHETIC_FIXTURE |
| `enforcement.override_allowed: false` with no emergency/appeal path | **Invalid** for live UM. Overrides/exceptions required | CONFIG_DEFECT |
| Elasticity `-0.3`, substitution `0.15` as if policy rules | Reclassify to Layer B as `UNESTIMATED` / demo-only until evidence attached | CONFIG_DEFECT |
| `provenance_status: MISSING_AUTHORITATIVE_SOURCE` while Medicare links exist | Distinct meanings: catalog provenance vs linked reference docs. Document both; do not claim reconciled commercial authority | CONFIG_DEFECT |
| Platform v1 and v2 both effective `2024-01-01` | Version collision — unresolved precedence | CONFIG_DEFECT |

### 3.3 Exclude / route separately

Emergency services; urgent/expedited needs; inpatient imaging; out-of-benefit services; products without approved adoption; transition-of-care cases as required by governing rules (`REPRESENTATIVE_DESIGN` + `UNRESOLVED` legal mapping).

**Medicare FFS NCD/LCD rules are not automatically inherited by commercial coverage** (`REPRESENTATIVE_DESIGN`). Any commercial adoption of Medicare criteria must be explicit.

---

## 4. Normative clinical decision model

This section defines **workflow and evidence requirements**. It does **not** invent clinical indications.

**Mandatory before live decisions:** an approved, dated **Clinical Criteria Schedule** with: anatomical region, requested code, indication, symptoms/red flags, prior evaluation, prior conservative management where clinically appropriate, contraindications, modality selection, contrast use, exceptions, documentation, citation, version, approver (`UNRESOLVED`).

| Step | Rule / disposition |
|---|---|
| 1. Eligibility | Confirm member/product, benefit, service date, network status. Unresolved → **pend for verification**, not clinical denial. |
| 2. Applicability | Resolve approved service-code list + outpatient setting. Out of scope → **NOT_APPLICABLE**, not denied. |
| 3. Urgency | Emergency → legally required emergency pathway. Urgent → expedited clinical review under applicable deadlines (`UNRESOLVED` exact clocks). |
| 4. Evidence | Collect only necessary clinical information. Missing → request information with clock tracking. |
| 5. Clinical criteria | Licensed qualified reviewer applies **approved** indication-specific criteria; documents rationale + criteria version. |
| 6. Outcome | Approve; request information; refer to qualified clinician; adverse determination **only** through authorized clinical process with notice and appeal rights. |
| 7. Overrides | Documented clinical exception / medical-director escalation **allowed**. Irreversible hard-coded no-override is prohibited. |

---

## 5. Code-set contract

### 5.1 Current platform candidates (not approved)

| Code | Role in current config | Treatment |
|---|---|---|
| 72148, 72149 | Scope + lever (lumbar MRI without contrast / with contrast) | Candidate lumbar codes — require validation against intended anatomical policy (`UNRESOLVED`) |
| 72158 | Lever only | Candidate lumbar MRI; must be in scope if in lever |
| 99213, 99214 | Scope | **Remove from PA targets** |
| 70540, 70542, 70543 | A56729 article codes | Different anatomical scope (orbit/face/neck); **do not** govern lumbar PA |

### 5.2 Operative rule

No operative code set is approved in this draft.  
Each future code entry must include: code system, code, description, anatomical scope, contrast variant, setting, effective-from/to, policy version, inclusion/exclusion reason, source, reviewer.

**Fail closed** to `MANUAL_SCOPE_REVIEW` on ambiguous mappings — never silently broaden authorization scope.

---

## 6. Medicare authority and rule provenance

| Authority | Jurisdiction | Clinical match to full outpatient MRI PA | Status for this policy |
|---|---|---|---|
| **NCD 220.2** | National | Applicable as national MRI coverage determination for Original Medicare FFS | `VERIFIED_SOURCE` as **reference**; commercial adoption = `UNRESOLVED` |
| **LCD L34425** | Palmetto JM (includes NC) | **PARTIAL** — orbit/face/neck only | Related partial only — **not** lumbar/brain PA authority |
| **Article A56729** | JM article of L34425 | **PARTIAL** — CPT 70540/70542/70543 only | Coding article for that LCD — **not** lumbar PA authority |
| NCCI demo PTP pair | n/a | Coding demo fixture | `SYNTHETIC_FIXTURE` |

Resolution values for any linked rule: `APPLICABLE` / `NOT_APPLICABLE` / `UNRESOLVED`, with `rule_set_id`, evidence, service date, program, jurisdiction.

In-repo evidence: `docs/demo/bcbs-nc/MRI_MEDICARE_CLINICAL_APPLICABILITY.md`, Coverage API catalogs under `data/policy_sources/`.

---

## 7. Enforcement and member safeguards

| Requirement | Class |
|---|---|
| Prospective PA workflow only after formal product adoption | REPRESENTATIVE_DESIGN |
| No automatic clinical denials based solely on utilization forecast or model score | REPRESENTATIVE_DESIGN |
| Emergency / urgent / exception / peer-to-peer / adverse determination / appeals / transition-of-care | REPRESENTATIVE_DESIGN; exact clocks = UNRESOLVED (compliance counsel) |
| Complete decision audit (evidence, criteria version, reviewer role, decision, timestamps, exception basis, communications, appeal outcome) | REPRESENTATIVE_DESIGN |
| Clinical safety and member access override savings targets | REPRESENTATIVE_DESIGN |

**Replace** current `override_allowed: false` before any operational activation.

---

## 8. Analytical lifecycle (Layer B — not policy rules)

| Stage | Spec |
|---|---|
| Baseline | Pre-effective eligible outpatient MRI requests/services; counts, approvals, denials, completion, allowed/paid, imaging per 1,000 eligible member-months; preserve mix and denominators |
| Prediction | Scenario-based changes with intervals and assumptions — not point estimates alone |
| Observation | Post-effective measured metrics; distinguish requests vs performed services; lag and completeness |
| What-if | Sandbox modification of review coverage/ops parameters; **do not** silently alter clinical criteria |
| Causal | Synthetic DiD may demonstrate method (`SYNTHETIC_FIXTURE`). Empirical causal inference requires comparison design, pretrends, concurrent policies, spillover checks, stable cohorts, uncertainty |
| Verdict | Jointly assess access, medical necessity, quality, utilization, spending, evidence strength, unintended effects. **Positive payer savings alone is insufficient** |

Platform synthetic MRI analytics may remain `FULLY_VALIDATED_DEMO` **without** promoting this definition to operational approval.

---

## 9. Assumption registry (Layer B)

| Parameter | Current platform value | Required status |
|---|---|---|
| Utilization elasticity | `-0.3` (“Historical claims analysis”) | **UNESTIMATED** — no inspectable study/cohort/period in config → demo-only until evidence attached |
| Substitution rate | `0.15` | **UNESTIMATED** — not approved |
| Implementation lag | `60` days | EMPIRICAL/OPERATIONAL — requires evidence before treating as real-world claim |
| Baseline effect | Implied volume reduction | No universal reduction target; derive from eligible cohorts only |
| Synthetic known-answer units | Demo lifecycle | Keep strictly separate from real-world effect claims (`SYNTHETIC_FIXTURE`) |

---

## 10. Guardrails and monitoring

Do **not** promote generic `+20%` utilization / `+15%` PMPM / `+10%` ER thresholds to approved safety standards.

Required guardrail families (thresholds = `UNRESOLVED` until owner-approved):

1. **Clinical access** — urgent-review timeliness, time to imaging, avoidable ED visits, delayed diagnoses, appeals/overturns  
2. **Equity** — lawful stratification; suppress small cells  
3. **Operations** — incomplete requests, TAT, denial reasons, peer review, complaints, exceptions  
4. **Finance** — allowed/paid, member OOP, site mix, alternatives, downstream cost; **do not** count denied requests as realized savings  

Trigger ladder: alert → investigation → clinical/compliance review → controlled pause/rollback. Owners + thresholds required before activation.

---

## 11. Data and evidence contract

Required: eligibility/enrollment and member-months; benefit/product; requests and clinical review outcomes; authorization dates; claims/encounters; CPT/HCPCS/ICD/modifiers; provider/site/network; allowed/paid; appeals/complaints; service and processing dates.

Linkage must distinguish **requested / authorized / performed / billed / paid**.  
Every computation preserves cohort, numerator, denominator, units, program, effective date, snapshot, calculation version, source lineage.  
No PHI in demo fixtures.

---

## 12. Version control and change management

Current platform: v1 and v2 share effective start `2024-01-01` → **CONFIG_DEFECT / UNRESOLVED**.

Required for any operative version:

- Immutable version ID  
- Effective and termination dates with no ambiguous overlap  
- `supersedes` link  
- Change rationale  
- Clinical approval + compliance approval  
- Explicit deployment decision  

Store **this specification** separately from the active executable configuration until approved.

---

## 13. Acceptance tests / release gates

1. NC commercial product included; NYC/DFW rejected or corrected.  
2. E/M 99213/99214 not PA targets.  
3. Lumbar MRI codes do **not** inherit L34425/A56729.  
4. Emergency/urgent pathways do not follow hard-stop denial; missing evidence pends with tracked timelines.  
5. Medical exception and appeal pathways exercisable and audited.  
6. Service-date/version boundary tests + source provenance + `rule_set_id` replay pass.  
7. Synthetic MRI known-answer / causal units reconcile independently; never labeled BCBS NC actual.  
8. Cross-policy regression MRI / MPPR / SOS / Objectives Health passes.  
9. Clinical owner + legal/compliance sign-off recorded before operational activation.

---

## 14. Open decisions (blockers to operational use)

1. Approved NC commercial product IDs and geographic market mappings.  
2. Definitive MRI anatomical scope and complete CPT/HCPCS list.  
3. Approved evidence-based clinical criteria + citation/version per indication.  
4. Emergency/urgent/exception/review/appeals rules by product and applicable law.  
5. Whether/how any Medicare NCD/LCD/article rules are adopted for commercial policy.  
6. Clinical/access guardrail thresholds, owners, cadence, rollback authority.  
7. Evidence-backed analytical assumptions and permitted causal claims.  
8. Resolution of v1/v2 effective-date collision and source-classification flags.

---

## 15. Source verification register

| Target | Notes |
|---|---|
| CMS MCD | https://www.cms.gov/medicare-coverage-database/ |
| CMS Coverage API | https://api.coverage.cms.gov/ — local snapshots in `data/policy_sources/` |
| CMS NCCI | Public quarterly files (ACCESS_BLOCKED on demo host for full ZIPs) |
| NC commercial UM regulations / federal requirements | Compliance counsel |
| Formally approved payer clinical criteria | **Required**; not present |

Before any `VERIFIED` promotion: attach document version, URL, retrieval date, checksum, applicable code scope.

---

## 16. Release classification

| Dimension | Status |
|---|---|
| Policy definition | **DEFINITION_REVIEW_REQUIRED** |
| Synthetic analytics lifecycle | May remain **FULLY_VALIDATED_DEMO** independently |
| Source applicability | **PARTIALLY_RECONCILED** / clinical match unverified for full CPT portfolio |
| Operational activation | **PROHIBITED** pending approval |

These are different readiness dimensions. Demo completeness ≠ clinically approved enforcement.

---

## Related artifacts

- Reviewer Word draft: `HealthForesight_MRI_Prior_Authorization_Policy_Definition_v1.docx` (Downloads)  
- Live config export: `Outpatient_MRI_Prior_Authorization.json`  
- Discrepancy report: `Outpatient_MRI_Prior_Authorization_DISCREPANCY_REPORT.md`  
- Clinical applicability: `../MRI_MEDICARE_CLINICAL_APPLICABILITY.md`
