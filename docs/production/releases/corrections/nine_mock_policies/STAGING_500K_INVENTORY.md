# Staging 500k inventory (lean staging `hfleanstg`)

Captured before the additive 5k load. Source: live counts on `hfleanstg-pg`.

## Operational tables present

| Table | source_system | Rows | Distinct members |
| --- | --- | ---: | ---: |
| `claims_lines` | `SYNTHETIC_LONGITUDINAL_V1` | 1,423,575 | 500,000 |
| `enrollment_records` | `SYNTHETIC_LONGITUDINAL_V1` | 9,479,433 | 500,000 |

Claim periods in `record_hash.period`: PRE 825,825 · POST 597,750.

## Target-model entity tables

None of these tables exist in lean staging Postgres:

- MemberMaster / EligibilityEnrollment / MemberRiskStratification
- ClaimHeader / EpisodeOfCare
- PharmacyClaim
- ProviderMaster / FacilityMaster / NetworkConfiguration / ProviderContract
- BenefitDesign / MemberAccumulator
- PriorAuthorizationRequest / AppealGrievance

Conclusion: the 500k book is a **narrow operational extract** (enrollment + claim lines), not a full target-model warehouse. The additive 5k book must supply the full entity file pack and dual-write operational rows under a new `source_system`.
