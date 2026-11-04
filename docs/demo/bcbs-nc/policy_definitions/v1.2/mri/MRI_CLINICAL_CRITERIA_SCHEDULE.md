# MRI Clinical Criteria Schedule (v1.2.1 technical closure)

**Policy:** HF-RP-UM-MRI-001  
**Anatomy band (proposed):** Outpatient lumbar spine MRI  
**Approval status:** **NOT APPROVED** — all indication rows are `PROPOSED_REPRESENTATIVE_NOT_APPROVED` unless a future amendment attaches payer/clinical owner sign-off.

## Non-operative lock (normative)

| Rule | Binding |
|---|---|
| `execution_mode` for this schedule | `NON_OPERATIVE` until approval block signed |
| May emit operative `APPROVED` | **No** |
| May emit `ADVERSE_DETERMINATION_ISSUED` | **No** |
| May emit `ADVERSE_REVIEW_REQUIRED` as operative referral | **No** (schedule unsigned) |
| Allowed outcomes while unsigned | `CLINICAL_REVIEW_REQUIRED`, `PENDING_INFORMATION` (admin only), `MANUAL_SCOPE_REVIEW`, `NOT_APPLICABLE` |
| `SYNTHETIC_SIMULATION` | May dry-run proposed rows with annotation `PROPOSED_REPRESENTATIVE_NOT_APPROVED`; **must not** persist as member determination |
| LUMBAR-01 “disposition_if_criteria_met: APPROVED” | **Illustrative proposed target only** — inactive while `payer_rule_status=NOT_ADOPTED` |
| Conservative care / contrast / neurologic gates | Remain `UNRESOLVED`; cannot gate operative approval |

Decision-table enforcement: see `MRI_DECISION_TABLES.json` branches `CL-01` / `CL-02` and invariant that proposed criteria cannot emit operative approval/denial.

## How to read this schedule

| Column | Meaning |
|---|---|
| `evidence_class` | Always `PROPOSED_REPRESENTATIVE_NOT_APPROVED` until signed |
| `public_guidance_anchor` | Where a reviewer must attach/verify licensed or public criteria — **not** reproduced proprietary ACR text |
| `payer_rule_status` | Always `NOT_ADOPTED` in v1.2 / v1.2.1 |
| `operative` | Always `false` until signed |

**Do not** treat these rows as Blue Cross NC medical policy or as CMS-approved commercial criteria.

## Schedule metadata

| Field | Value |
|---|---|
| schedule_id | `MRI-LUMBAR-CRIT-2026-11-DRAFT` |
| schedule_version | `v1.2.1-technical-closure` |
| effective_from | unset (`UNRESOLVED`) |
| supersedes | none |
| clinical_owner | `UNRESOLVED` |
| compliance_owner | `UNRESOLVED` |
| operative | `false` |

## Indication tables (proposed representative — not approved)

### LUMBAR-01 — Low back pain without red flags (non-emergent)

| Field | Value |
|---|---|
| presenting_condition | Non-emergent low back pain |
| clinical_findings_required | Documented history/exam; absence of listed red flags (see LUMBAR-RF) |
| prior_evaluation | Clinically appropriate evaluation documented |
| prior_conservative_care | Duration/type **UNRESOLVED** pending approved criteria citation — **not an active gate** |
| modality | Lumbar MRI without contrast as default candidate; contrast only if indication-specific criteria met (`UNRESOLVED`) |
| documentation | Clinical note, relevant prior imaging results if any, requested CPT |
| contraindications | Device/implant MRI safety unresolved at request time → CLINICAL_REVIEW_REQUIRED |
| exceptions | Red flags → urgent/emergency pathway (not this row); evaluated in `DT-URGENCY` **before** this row |
| disposition_if_criteria_met_proposed | APPROVED *(target after schedule approval only)* |
| disposition_while_unsigned | CLINICAL_REVIEW_REQUIRED |
| disposition_if_incomplete_standard | PENDING_INFORMATION *(only after urgency path clears as STANDARD)* |
| disposition_if_not_met_proposed | ADVERSE_REVIEW_REQUIRED *(referral only; after schedule approval)* — while unsigned: CLINICAL_REVIEW_REQUIRED |
| operative | false |
| evidence_class | PROPOSED_REPRESENTATIVE_NOT_APPROVED |
| public_guidance_anchor | Attach approved payer criteria and/or licensed appropriateness guidance (e.g., ACR Appropriateness Criteria® for low back pain — **do not paste copyrighted criteria here**); cross-check CMS NCD 220.2 for Medicare FFS program context only |
| payer_rule_status | NOT_ADOPTED |

### LUMBAR-02 — Low back pain with neurologic findings (non-emergent)

| Field | Value |
|---|---|
| presenting_condition | Radiculopathy / progressive neurologic symptoms (non-emergent) |
| clinical_findings_required | Focal neurologic findings documented |
| prior_evaluation | Documented |
| prior_conservative_care | Per approved schedule (`UNRESOLVED`) — **not an active gate** |
| modality | Lumbar MRI; contrast per approved indication rules (`UNRESOLVED`) |
| documentation | Neuro exam elements, symptom timeline |
| exceptions | Cauda equina / acute progressive deficit → emergency/urgent pathway (`DT-URGENCY` first) |
| disposition_while_unsigned | CLINICAL_REVIEW_REQUIRED |
| disposition_default_draft | CLINICAL_REVIEW_REQUIRED |
| operative | false |
| evidence_class | PROPOSED_REPRESENTATIVE_NOT_APPROVED |
| public_guidance_anchor | Approved clinical criteria required; NCD 220.2 is program reference for Medicare FFS only |
| payer_rule_status | NOT_ADOPTED |

### LUMBAR-03 — Post-operative / prior lumbar surgery evaluation

| Field | Value |
|---|---|
| presenting_condition | Evaluation after prior lumbar surgery |
| clinical_findings_required | Surgical history + current symptoms |
| modality | Often contrast-capable protocols — **contrast rules UNRESOLVED** |
| disposition_while_unsigned | CLINICAL_REVIEW_REQUIRED |
| disposition_default_draft | CLINICAL_REVIEW_REQUIRED |
| operative | false |
| evidence_class | PROPOSED_REPRESENTATIVE_NOT_APPROVED |
| payer_rule_status | NOT_ADOPTED |

### LUMBAR-RF — Red flags (route off standard pathway)

| Red flag (illustrative list — finalize with clinical owner) | Pathway |
|---|---|
| Suspected cauda equina | Emergency pathway — evaluated **before** conservative-care / routine incomplete-info branches |
| Progressive major motor deficit | Urgent/expedited pathway |
| Suspected infection / malignancy with acute concern | Urgent/emergency per clinical judgment |
| Trauma with unstable features | Emergency pathway |

Exact list and clocks: `UNRESOLVED` (clinical + legal).

**Ordering invariant:** `DT-URGENCY` precedes `DT-EVIDENCE` and `DT-CLINICAL`. A routine incomplete-information branch must not delay emergency escalation.

### Explicit non-coverage of this schedule

| Topic | Rule |
|---|---|
| Orbit/face/neck MRI | **Out of schedule** — do not use L34425/A56729 rows here |
| E/M codes 99213/99214 | **Not imaging criteria** |
| Automatic denial from model score | **Forbidden** |
| Operative approval from this draft | **Forbidden** |

## Approval block (blank)

| Role | Name | Date | Signature |
|---|---|---|---|
| Clinical owner | | | |
| Compliance / legal | | | |
| Product owner | | | |

**Self-approval by engineering is prohibited.**
