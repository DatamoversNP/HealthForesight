# Dec 4 Nine-Policy Platform Execution Report

**Status:** Demo platform execution complete for the nine existing Representative Payer Policies.  
**Operational activation:** PROHIBITED (release blockers remain open).  
**Frozen fixtures modified:** false  
**Claims reseed:** false (~3.5M lines retained)

## Browser rehearsal

| Gate | Result |
|---|---|
| Primary route MRI → MPPR → SOS → Medicare Rules → Objectives Health | **PASS** |
| All nine policy workspaces open + refresh | **PASS** |
| **Six optional policies high-confidence** (Monitoring figures, composition, causal, refresh, what-if pages) | **PASS / HIGH** |
| Screenshots | `dec4_nine_browser/` · `dec4_six_optional/` |
| Machine-readable | `DEC4_NINE_BROWSER_GATES.json` · `DEC4_SIX_OPTIONAL_HIGH_CONFIDENCE.json` |

See also: `DEC4_SIX_OPTIONAL_HIGH_CONFIDENCE.md`

## Known-answer preservation

| Policy | Preserved result |
|---|---|
| MRI | −9.4167 **INDEX_POINTS** (Jan=100); not util/1k |
| MPPR | $3,150 → $2,550; payer savings **$600**; what-if 50%→40% **+$120** |
| SOS | payer savings **$520**; what-if 80%→70% **+$260** |
| PTP | synthetic mechanical **$800**; what-if **$400** (not CMS quarterly) |
| MUE | synthetic **$100**; MUE 4→3 what-if (not CMS confidential) |
| Therapy | **$80** mechanical; what-if **NOT_SUPPORTED_FOR_THIS_MECHANISM** |
| Infusion | **$3,600**; steerage 2→3 what-if **+$1,800** |
| NCD 220.2 | **PROVENANCE_ONLY** — no financial baseline/causal |
| LCD L34425 | **PROVENANCE_ONLY** — orbit/face/neck only; never lumbar |

## Per-policy execution matrix

| Key | Policy ID | Def | Integration | Baseline | Prediction | Observation | Causal feas. | Causal est. | What-if | Verdict | Browser | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mri | `d403f101-08dd-45c9-ab83-d42e37c62018` | v1.2.1 | OK | EXISTING_COMPLETED | EXISTING | EXISTING | CAUSAL_ESTIMATE_SUPPORTED | Frozen DiD INDEX_POINTS | EXISTING_SIMULATE | OK | PASS | FULLY_VALIDATED_DEMO |
| mppr | `d0eeb370-df14-4478-8755-dad6c3a35a47` | v1.2.1-sc | OK | SYNTHETIC_MECHANICAL | SYNTHETIC_MECHANICAL | SYNTHETIC_OR_EXISTING | CAUSAL_DESIGN_POSSIBLE_DATA_INSUFFICIENT | Deterministic ≠ causal | completed | OK | PASS | FULLY_VALIDATED_DEMO |
| sos | `d7441dd9-3bfe-405e-ae6c-0377204bbb7e` | v1.2.1-sc | OK | SYNTHETIC_MECHANICAL | SYNTHETIC_MECHANICAL | SYNTHETIC_OR_EXISTING | CAUSAL_DESIGN_POSSIBLE_DATA_INSUFFICIENT | Deterministic ≠ causal | completed | OK | PASS | FULLY_VALIDATED_DEMO |
| ptp | `58b839b5-…` | v1.2.1-sc | OK | DATA_INSUFFICIENT (modifiers) | SYNTHETIC_MECHANICAL | N/A_EMPIRICAL | NOT_IDENTIFIABLE / descriptive | Mechanical synthetic | completed | OK | PASS | FULLY_VALIDATED_DEMO |
| mue | `e11b049d-…` | v1.2.1-sc | OK | DATA_INSUFFICIENT (MUE file) | SYNTHETIC_MECHANICAL | N/A_EMPIRICAL | CAUSAL_DESIGN_POSSIBLE_DATA_INSUFFICIENT | Mechanical synthetic | completed | OK | PASS | FULLY_VALIDATED_DEMO |
| therapy | `f2b8e7f3-…` | v1.2.1-sc | OK | SYNTHETIC_MECHANICAL | SYNTHETIC_MECHANICAL | N/A_OR_SYNTHETIC | CAUSAL_DESIGN_POSSIBLE_DATA_INSUFFICIENT | Design possible | **NOT_SUPPORTED_FOR_THIS_MECHANISM** | OK | PASS | FULLY_VALIDATED_DEMO |
| infusion | `11218053-…` | v1.2.1-sc | OK | SYNTHETIC_MECHANICAL | SYNTHETIC_MECHANICAL | N/A_OR_SYNTHETIC | CAUSAL_DESIGN_POSSIBLE_DATA_INSUFFICIENT | Deterministic ≠ causal | completed | OK | PASS | FULLY_VALIDATED_DEMO |
| ncd | `4f8c34e3-…` | v1.2.1-sc | OK | N/A PROVENANCE_ONLY | N/A | N/A | Study feasibility | NOT_IDENTIFIABLE financial | N/A | OK | PASS | PROVENANCE_VALIDATED |
| lcd | `649b4ac8-…` | v1.2.1-sc | OK | N/A PROVENANCE_ONLY | N/A | N/A | Study feasibility | NOT_IDENTIFIABLE financial | N/A | OK | PASS | PROVENANCE_VALIDATED |

Full machine-readable detail (analysis IDs, mechanical totals, limitations):  
`DEC4_NINE_POLICY_PLATFORM_EXECUTION_REPORT.json`

## Platform fixes applied (implementation, not policy-definition docs)

1. `GET /policies/{id}` enforcement touchpoint sanitization — restored catalog/detail for 8 policies that returned HTTP 500.  
2. Mechanism-specific enterprise composition; provider-behavior no longer reuses MRI fixture.  
3. Monitoring panel loads MPPR/SOS/expansion mechanical verticals from live APIs.  
4. Verdict evidence uses live observation verdict (removed hardcoded `ON_TRACK`).  
5. Expansion what-if analyses re-persisted via `persist_expansion_lifecycles.py`.  
6. Causal feasibility uses policy ID (MRI exact) rather than name collision with NCD/LCD studies.

## Explicit non-claims

- Not production-ready; not operatively activated.  
- NCD/LCD do **not** have full financial/causal lifecycles.  
- Synthetic coding edits are **not** authoritative CMS files.  
- Denied requests are **not** realized payer savings.  
- Deterministic payment effects are **not** automatic causal estimates.
