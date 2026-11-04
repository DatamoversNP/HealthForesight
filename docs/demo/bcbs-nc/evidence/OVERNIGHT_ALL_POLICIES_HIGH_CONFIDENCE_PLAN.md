# Overnight plan — All catalog policies to Dec 4 high confidence

## Scope

| Set | Count | Status |
|---|---|---|
| Full tenant catalog (live API) | **289** | Target |
| Dec 4 Representative nine | 9 | Already **HIGH** — retain, do not regress |
| Remaining catalog policies | **280** | Bring to HIGH in 12 batches × 25 |

## High-confidence definition (same depth as the six optional)

For each policy, PASS requires:

1. `GET /policies/{id}` → 200  
2. `GET /policies/{id}/workspace` → 200; name present  
3. `GET /enterprise/policies/{id}/composition` → 200  
4. `GET /enterprise/policies/{id}/causal-feasibility` → 200  
5. `GET /enterprise/policies/{id}/causal-impact` → 200 (descriptive OK)  
6. `GET /enterprise/policies/{id}/verdict-evidence` → 200  
7. Browser: workspace opens with policy name  
8. Browser: Monitoring tab loads without error (honest empty / catalog card OK; no crash)  
9. Browser: Composition tab loads  
10. Browser: Causal Impact tab loads  
11. Browser: refresh + reopen Monitoring still OK  
12. Do **not** invent financial known-answers. If no KA: show DATA_INSUFFICIENT / catalog monitoring card.  
13. Operational activation remains PROHIBITED globally.

## Batch schedule

| Batch | Roster file | Policies |
|---|---|---|
| 01–12 | `overnight_batches/batch_NN_roster.json` | 25 each (last may be shorter) |

Nine Representative policies are **excluded** from overnight batches (already HIGH).

## Autonomy rules

- Run continuously; repair systemic defects between batches.  
- Re-queue failed policies after fixes.  
- Do not reseed claims. Do not expand catalog. Do not activate operative rules.  
- Master report: `ALL_POLICIES_HIGH_CONFIDENCE_MASTER_REPORT.{json,md}`  
- Per-batch: `overnight_batches/batch_NN_results.json`

## Runner

`docs/demo/bcbs-nc/evidence/run_overnight_all_policies_high_confidence.py`
