# Outpatient MRI Prior Authorization — Lifecycle Execution Spec

Executable contract for HealthForesight policy lifecycle orchestration.
Reference policy: **MOCK-UM-MRI-001** (illustrative synthetic fixture).

## Architecture decision

Same orchestration for all nine mock policies:

1. Configured policy definition  
2. Baseline — what historically happened?  
3. Predictive Impact — continuation vs supported policy-effect (separate)  
4. Observations — what actually happened after implementation?  
5. Reconciliation — actual vs frozen expectations (raw + exposure-adjusted)  
6. Verdict & objectives — only with approved endpoints and valid evidence  
7. Dashboards & evidence — render persisted lifecycle records only  

Calculators remain mechanism-specific. MRI prior auth must not use the MPPR payment engine.

## Non-negotiable invariants

1. One policy version governs applicability across the linked lifecycle.  
2. No future-data leakage into a frozen prediction.  
3. No fabricated monthly series from aggregate totals.  
4. No unvalidated clinical decisions from claims matching.  
5. No policy savings inferred from continuation differences.  
6. No zero substituted for missing or unestimated metrics.  
7. No comparison of incompatible populations, periods, units, or financial bases.  
8. No overwritten observations or predictions from What-If.  
9. No verdict without an applicable endpoint contract.  
10. No dashboard-only calculations that disagree with the lifecycle engine.  
11. Eligibility comes from policy scope / levers / codesets / assumptions / guardrails — never from hardcoded `preferred_source_system` or `policy_key` query stamps.

## Implementation map

| Capability | Module |
|---|---|
| Pure calculators | `packages/common/src/uepi_common/lifecycle/continuation.py` |
| MRI fixture + oracle | `packages/common/src/uepi_common/lifecycle/mri_fixture.py` |
| API adapter | `apps/api/src/uepi_api/services/policy_lifecycle_continuation.py` |
| Scope filters | `build_policy_claims_filters` / `extract_policy_target_codes` |
| Baseline (definition-driven) | `database_baseline_computation.compute_policy_baseline_from_database` |
| Verdict without endpoint | `uepi_api.verdict.compute_verdict` → `INCONCLUSIVE` |
| Acceptance tests | `packages/common/tests/test_mri_lifecycle_fixture.py` |

## Oracle fixture (synthetic)

| Step | Input | Expected |
|---|---|---|
| Historical rates | 14,400 services; 4.8M MM; $11.52M allowed | rate 0.003; $2.40 PMPM; 36 /1k MY |
| Jan continuation | 405,000 forecast MM | 1,215 services; $972,000 allowed |
| Horizon | 12 × 405,000 | 14,580 services; $11,664,000 |
| Observation Jan | 1,170; 407,000 MM; $936,000 | ~$2.2998 PMPM; 34.50 /1k MY |
| Raw recon | $936k − $972k | −$36,000 |
| Exposure-adjusted | $2.40 × 407,000 | $976,800 expected; −$40,800 variance |
| Auth feed missing | — | `NOT_MEASURABLE` |
| Effect model missing | — | `UNESTIMATED` (not zero) |
| Endpoint missing | — | `INCONCLUSIVE` |
| What-If 420k MM | $2.40 × 420,000 | $1,008,000; parent frozen unchanged |

## Acceptance matrix (illustrative fixture)

| Capability | Expected classification |
|---|---|
| Policy definition | Configured fixture |
| Baseline | Testable |
| Continuation prediction | Testable |
| Policy-effect prediction | UNESTIMATED |
| Claims observations | Testable |
| Authorization outcomes | NOT_MEASURABLE |
| Reconciliation | Testable |
| Verdict | INCONCLUSIVE |
| What-If continuation | Testable |

For each capability the QA agent must record:

- **Execution status** — was the capability legitimately executable with available config/data?  
- **Implementation correctness** — did the platform calculate, store, and display correctly?

`UNESTIMATED` is the correct policy-effect state when no valid model exists. Displaying that label does not prove effect models work for other policies.

## Run tests

```bash
cd packages/common && poetry run pytest tests/test_mri_lifecycle_fixture.py -q
```

## Staging / demo safety

- Preserve December 4 demo and production environments.  
- Do not manufacture clinical criteria, policy effects, financial savings, authorization decisions, or verdict endpoints.  
- Do not declare MRI fully executable merely because baseline, continuation, and claims observations work.
