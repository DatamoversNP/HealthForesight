# MRI Operational Requirements Matrix (NC commercial)

**Policy:** HF-RP-UM-MRI-001 v1.2.1 technical closure  
**Status:** DEFINITION_REVIEW_REQUIRED — clocks and legal mappings are **UNRESOLVED** until compliance counsel + product owner attach product-specific values.

| Requirement | Representative design | Product-specific value | Regulatory mapping | Status |
|---|---|---|---|---|
| Eligible products | NC commercial products on approved schedule | `UNRESOLVED` product IDs | State/federal UM rules as applicable | UNRESOLVED |
| Geographic markets | NC only | Must not be NYC/DFW | — | CONFIG_DEFECT in live config |
| Member eligibility check | As of service date | `UNRESOLVED` system of record | — | REPRESENTATIVE_DESIGN |
| Benefit check | Covered imaging benefit required | `UNRESOLVED` | — | REPRESENTATIVE_DESIGN |
| Standard review timeline | Prospective non-emergent PA | `UNRESOLVED` calendar days | Map to applicable NC/federal rules | UNRESOLVED |
| Urgent / expedited pathway | **Separate** from emergency; evaluated in `DT-URGENCY` before routine evidence | `UNRESOLVED` definition + clock | Map to governing law | UNRESOLVED |
| Emergency pathway | No standard hard-stop PA denial; **before** PENDING_INFORMATION / conservative-care gates | Follow legally required emergency processing | Map to governing law | UNRESOLVED |
| Qualified reviewer | Licensed clinician per role matrix | `UNRESOLVED` credential matrix | — | UNRESOLVED |
| Peer-to-peer | Offered where product requires | `UNRESOLVED` | — | UNRESOLVED |
| Adverse review referral | Outcome `ADVERSE_REVIEW_REQUIRED` — permission/referral into adverse process, **not** a final denial | `UNRESOLVED` intake SLA | — | REPRESENTATIVE_DESIGN |
| Issued adverse determination | Outcome `ADVERSE_DETERMINATION_ISSUED` requires `reviewer_id`, `notice_ref`, `appeal_rights_ref`, `decided_at`, `audit_packet_id` | `UNRESOLVED` templates + retention | Map to notice/appeal rules | UNRESOLVED |
| Member notice of adverse determination | Required content/elements for **issued** determinations only | `UNRESOLVED` templates | Map to notice rules | UNRESOLVED |
| Provider notice | Required for issued determinations | `UNRESOLVED` | — | UNRESOLVED |
| Appeals | Exercisable, audited after issued determination | `UNRESOLVED` levels/timelines | Map to appeal rules | UNRESOLVED |
| Continuity of care / transition | Preserve where required | `UNRESOLVED` | — | UNRESOLVED |
| Missing information pend | PENDING_INFORMATION + clock — **only after** urgency clears as STANDARD | `UNRESOLVED` | — | REPRESENTATIVE_DESIGN |
| Ambiguous code mapping | MANUAL_SCOPE_REVIEW; no auto deny/PA | — | Preserve member protections | REPRESENTATIVE_DESIGN |
| Audit retention | Full decision packet for every issued determination and exception | `UNRESOLVED` retention period | — | REPRESENTATIVE_DESIGN |
| Proposed clinical schedule | Non-operative until signed | — | — | PROPOSED_REPRESENTATIVE_NOT_APPROVED |

## Outcome vocabulary (ops-facing)

| Outcome | Meaning |
|---|---|
| `ADVERSE_REVIEW_REQUIRED` | Case referred for authorized adverse-determination review — **not** a completed denial |
| `ADVERSE_DETERMINATION_ISSUED` | Completed adverse determination with authorized reviewer, notices, appeals, timestamps, audit |

Deprecated label `ADVERSE_DETERMINATION_AUTHORIZED` is **retired** in v1.2.1 (ambiguous between permission and completion).

## Guardrail metric families (thresholds unapproved)

| Family | Example metrics | Approved threshold |
|---|---|---|
| Clinical access | Urgent TAT, time-to-imaging, avoidable ED, delayed diagnosis signals, appeal overturn rate | UNRESOLVED |
| Operations | Incomplete requests, standard TAT, denial reason mix, exception frequency | UNRESOLVED |
| Equity | Lawful stratification; small-cell suppression | UNRESOLVED |
| Finance | Allowed/paid, member OOP, site mix, downstream cost; denied ≠ savings | UNRESOLVED |

**Do not invent approved numeric thresholds. Do not self-approve clinical, legal, product, or guardrail values.**
