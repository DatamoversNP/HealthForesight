# Cross-Policy Causal Feasibility Report

**Service:** `causal-feasibility-v1`  
**API:** `GET /api/v1/enterprise/policies/{id}/causal-feasibility`

## Design principle

Causal impact is **eligible across all policy domains**; **estimation is selective**.

Statuses:

| Status | Meaning |
|---|---|
| CAUSAL_ESTIMATE_SUPPORTED | Defensible design + fixture/known-answer estimate emitted |
| CAUSAL_DESIGN_POSSIBLE_DATA_INSUFFICIENT | Design exists; demo data inadequate |
| DESCRIPTIVE_ONLY | Report observed/mechanical change; no causal claim |
| NOT_IDENTIFIABLE | No credible design for this intervention yet |

## Sample results (live API 2026-11-03)

| Policy | Mechanism | Status |
|---|---|---|
| Outpatient MRI Prior Authorization | UTILIZATION_MANAGEMENT | **CAUSAL_ESTIMATE_SUPPORTED** (synthetic DiD) |
| Multiple Procedure Payment Reduction | MPPR | **DESCRIPTIVE_ONLY** — $600 is mechanical, not causal |
| NCCI PTP Bundling (Demo) | CODING_EDIT_MODIFIER | **DESCRIPTIVE_ONLY** — $800 mechanical |

## Domain guidance (shipped)

UM, MPPR, SOS, coding edits, fee/unit, coverage determinations, denials — each has candidate outcomes and designs. DiD is **not** default for every policy.

## Non-claims

- Mechanical payer savings ≠ causal savings  
- No automatic causal estimate from NCD/LCD/NCCI effective dates alone  
- Not Blue Cross NC empirical causal attribution
