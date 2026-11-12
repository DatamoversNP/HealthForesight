# Formula review validation report

6 November 2026. Use this to check the expert review in `HealthForesight_Final_Formula_Expert_Review_and_Cursor_Implementation (1).docx` against the code.

Three columns matter for every row:

| Column | Meaning |
|---|---|
| Code | What the repository does today |
| Expert | Disposition in that document |
| This review | Accept, accept with a narrower reading, or reject |

The expert document says it did not execute the code. This report did, by reading the functions named below. It does not certify the 250 policy code sets, and it does not change staging or the December 4 demo.

Source inventory: `docs/production/releases/PLATFORM_MEASURES_AND_FORMULAS.md`. Where this report disagrees with that inventory, the correction is marked **Inventory correction**.

## How to validate one row

1. Open the file and function named in the row.
2. Confirm the formula matches the Code cell. If it does not, the row fails.
3. Confirm the Expert cell matches the decision table in the docx (sections “Final accept / fix / block decisions”).
4. Use the Check cell. A check is a hand calculation or a condition in the source, not a request to regenerate data.

Verdicts used here:

| Verdict | Meaning |
|---|---|
| ACCEPT | Expert disposition matches the code and is the right product rule |
| NARROW | Direction is right; do not implement the broad wording |
| REJECT | The expert statement does not match the code, or the proposed rule is the wrong one |

---

## Decisions that hold

| # | Topic | Code | Expert | This review | Check |
|---|---|---|---|---|---|
| 1 | Eligible exposure | `database_baseline_computation.py`: `member_months = unique_members × calendar months`. `unique_members` is distinct `member_id` on claims. `database_claims_loader.py` line 291 does the same, and uses 1 if the count is 0. | REPLACE. Never use claimants × months as enrolled exposure. | ACCEPT | 10 claimants in a 12-month window become 120 member-months even if each had one claim. That is not enrollment. |
| 2 | Paid versus allowed | Claims loader lines 294–302: `cost_pmpm = paid_pmpm`. `unified_measures.py` maps `cost_pmpm` to `allowed_pmpm_target`. | REPLACE the ambiguous name. | ACCEPT | One stored key cannot mean both. |
| 3 | Impact utilization | `analytics/impact.py` `_compute_metric`: `(lines / distinct members) × 1000`. No division by months. | REPLACE. Name claimant ratios separately. | ACCEPT | 120 lines and 100 members is 1,200 in a 1-month window and in a 12-month window. |
| 4 | Database utilization | `(lines / member_months) × 1000` with member-months from row 1. | Same REPLACE. | ACCEPT | The label says per 1,000 member-months. The denominator is still claimants. |
| 5 | Cost per 1,000 | `baseline.py`: `(paid / member_months) × 1000`. | KEEP if labeled dollars per 1,000 member-months, not PMPM. | ACCEPT | $90,000 and 1,200 member-months is $75,000 per 1,000, which is $75 PMPM. Different units. |
| 6 | Annualization | `baseline_metrics_computation.py` lines 77 and 84: `(pmpm × member_months / months) × 12`. | KEEP. Prior double-division criticism withdrawn. Algebra matches period total / months × 12 when PMPM = total / member-months. | ACCEPT | $120,000 allowed, 1,200 member-months, 12 months. PMPM = $100. Annualized = (100 × 1,200 / 12) × 12 = $120,000. Same as the period total. It is not a forecast of a future year. |
| 7 | Fake p-value | `impact.py` lines 513 and 516 return 0.50 if the interval contains 0, else 0.01. | REPLACE. Do not publish those values. | ACCEPT | There is no test statistic in that function. |
| 8 | Parallel-trend gate | `method_checks.py`: pass if absolute slope difference < 0.1, warn if < 0.3. | Do not auto-pass. Thresholds depend on units. | ACCEPT | A slope in “per 1,000” and a slope in dollars are not comparable to 0.1. |
| 9 | Sample size | Same file: pass if pre-period rows ≥ 1,000. Rows are claim lines. | FIX. Lines are not independent members. | ACCEPT | 1,000 lines can be 50 members. |
| 10 | Control balance | Imbalance list starts empty, so balance score stays 1.0 without reading age, sex, or risk. | REPLACE. Compute a real standardized difference. | ACCEPT | An empty list is not a passed balance test. |
| 11 | Seasonality | `cv = variance / mean`, then < 0.1, < 0.2. | FIX. Coefficient of variation is standard deviation / mean. | ACCEPT | Variance / mean is not that ratio. |
| 12 | Friction and elasticity | `predicted_impact.py`: prior auth base 0.60, hard × 1.2, cap 1. Imaging elasticity −0.35. `utilization_change_pct = friction × elasticity × 100`. `cost_change_pct = utilization_change_pct × 0.9`. | SIMULATION ONLY. Do not treat as a measured effect. | ACCEPT | Friction 0.72 and elasticity −0.35 produce −25.2% utilization and −22.68% cost. Both numbers are table lookups. |
| 13 | Missing baseline | Same file: if metrics are absent, utilization defaults to 100 and cost PMPM to 500. | BLOCK those defaults. | ACCEPT | A missing baseline must stay null. |
| 14 | Fixed confidence | Substitution rows 70, provider mix 75, patient response 70. Prediction score starts at 100 and subtracts 30, 15, 20, or 10. | Not a calibrated probability. | ACCEPT | The subtractions are constants. |
| 15 | Provider and patient tables | Friction < 0.30 → 70/20/8/2. Defer = 0.10 × friction. | SIMULATION ONLY. | ACCEPT | No claim history enters those percentages. |
| 16 | Verdict | `verdict.py`: ON_TRACK when both utilization and cost percent changes are ≤ 0. AT_RISK when utilization change > 5 or cost change > 10. | REPLACE. Need a policy objective. Missing objective → inconclusive. | ACCEPT | A screening policy that should increase use fails this rule when it works. |
| 17 | Staging writer | Lifecycle script: month rate = lines / month claimants × 1000. Baseline rate divides by 12. Prediction = baseline × 0.95. Status does not use cost. | QUARANTINE the 2,250 rows. Do not regenerate them to look successful. | ACCEPT | Audit recount matched the stored formula and still marked all 2,250 NOT_MEASURABLE. |
| 18 | Forecast accuracy | `forecast_service.py`: 6-month “accuracy” is distance from the forecast to the prediction, not to a later actual. | RENAME. Accuracy needs a future actual. | ACCEPT | Landing on the prediction scores 100 even if the next observation differs. |
| 19 | Substitution detector | A code is kept only if allowed dollars rose and post count ≥ 10. | RESTRICT. A rise is not proof of substitution. | ACCEPT | Unrelated codes that grew are still listed, up to 20. |
| 20 | Archetypes | COMPLIERS if allowed delta < −1,000 and claim delta < −5. CIRCUMVENTERS if allowed delta > 1,000 and site-shift rate > 0.5. | Do not infer compliance from a dollar delta. | ACCEPT | The cutoffs are not adjusted for panel size. |
| 21 | Patient bands | LOW / MEDIUM / HIGH by cost percentile. | RENAME. These are cost strata, not clinical risk. | ACCEPT | The split is built to balance counts. |
| 22 | Trust score | Method 90 or 70. Data quality fixed at 85. Methodology fixed at 85. Control starts at 100 when no balance object exists. Weights 0.30, 0.20, 0.20, 0.15, 0.15. | REPLACE the constants. | ACCEPT | Missing a balance test currently scores 100, which is the wrong direction. |
| 23 | Scorecard | Access score is the constant 80. `defer_rate = abs(utilization_change_pct) × 0.1` when the change is negative, then `100 − defer_rate × 200`. Weights 0.30, 0.25, 0.25, 0.20. | REPLACE. | ACCEPT | A −20% utilization change sets defer_rate to 2, then the behavioral score floors at 0. The 0.1 and the 200 do not refer to the same unit. |
| 24 | Demo payment engines | MPPR, site-of-service, infusion, PTP, MUE, therapy. Each file marks `DEMO_SYNTHETIC` or states the limit is not a CMS MUE. | KEEP the known answers. Do not call them payer adjudication. | ACCEPT | See the numeric pack below. |
| 25 | Data-quality weights | `0.30×completeness + 0.40×validity + 0.20×uniqueness + 0.10×(1 − min(errors/rows, 1))`. | KEEP the score as descriptive. Hard-block critical failures. | NARROW | The weights match the code. A hard block on every duplicate key will reject voids and replacements until the grain is defined. |
| 26 | Policy similarity | `0.2×name Jaccard + 0.3×scope + 0.4×levers + 0.1×dates`, report at ≥ 0.85. | HEURISTIC ONLY. | ACCEPT | Identical scope and levers with no shared words and no date overlap score 0.70, under 0.85. |
| 27 | Learning accuracy | `accuracy = 100 − abs((observed − predicted) / abs(predicted) × 100)`. Within range if absolute error percent < 20. | Do not use 100 minus that percent as a universal accuracy. | ACCEPT | Predicted −10 and observed −8 is 20% error and accuracy 80. The “within range” test fails because it is strict less-than 20. |
| 28 | Learned elasticity | At least 3 observations. `new = −0.8 × mean(observed/predicted)` for utilization and `−0.75 ×` that mean for cost. | DISABLE as an authoritative elasticity. | ACCEPT | −0.8 and −0.75 are not the imaging −0.35 table. |
| 29 | Scenario accuracy | `0.6×util accuracy + 0.4×cost accuracy`. If predicted percent is 0 and observed percent is 0, accuracy is 100. | FIX the zero case and the fixed weights. | ACCEPT | A prediction of 0% is scored perfect when the observation is also 0%, with no other evidence. |
| 30 | Rollout duplicate | Code Jaccard ≥ 0.55, same policy type, both sets size ≥ 2. | HEURISTIC ONLY. | ACCEPT | 0.55 is not proof the policies are the same benefit rule. |
| 31 | Narrative checker | Relative error ≤ 1% against `(claims / member_months) × 1000` and cost / member-months. | EXTEND. This checks arithmetic only. | ACCEPT | A wrong denominator that is applied consistently still passes. |
| 32 | Readiness | CONFIGURED if id and name exist. Other flags are “a baseline / forecast / observation record exists,” plus a causal flag for IMPACT_ASSESSABLE. | REPLACE. Existence is not validity. | ACCEPT | All 250 staging policies can hold observation rows and remain execution-blocked. |
| 33 | Staging observations | 53,949 claims, 1 general baseline, 250 policy baselines, 2,250 January–September observations. Enrollment count 0. Demo copy count 0. | Do not present them as outcomes. | ACCEPT | Recount of the stored formula was 2,250 / 2,250. Scope was FAIL on 250 / 250 because execution eligibility is BLOCKED. |
| 34 | December 4 demo | Frozen App Service demo and its known-answer fixtures. | Do not change it in this work. | ACCEPT | National-product rules and the demo fixture are different scopes. |
| 35 | One causal model for every policy | DiD formula is `(treatment post − pre) − (control post − pre)`. | KEEP the arithmetic. Do not mandate one model. Causal label needs a design. | ACCEPT | Treated 100→80 and control 100→95 is −15 metric units. That is not automatically an effect of the policy. |

## Decisions to narrow or reject

| # | Expert statement | Why it does not hold as written | Use this instead | Check |
|---|---|---|---|---|
| R1 | Baseline shift threshold 0.01 “means 0.01 percentage points if the input is a percent.” | REJECT the gloss. `baseline_refresh.py` lines 265 and 276: change is already `((new − old) / old) × 100`, and shift fires when that value exceeds 0.01. | Say: shift fires on a relative change larger than 0.01 percent. Significant shift is 5 percent. Both should be documented in those units. | Utilization 100 to 100.02 is a 0.02 percent relative change and sets `shift_detected`. It is not a 0.02 percentage-point move in a rate that is already “per 1,000.” |
| R2 | Replace the fake p-value with cluster-aware resampling. | NARROW. Removing 0.01 and 0.50 is required. The same document says not to mandate one statistical model. | If the design does not support an interval, store unavailable. Do not pick member, provider, or facility clustering in this report. | `impact.py` has no cluster id in `_compute_p_value`. |
| R3 | Pre-trend review should be visual and statistical, and the gate should be replaced. | NARROW. A picture cannot be a failing test. | Keep an automated comparison only after the unit of the slope is defined. Leave visual review to a person. | The current 0.1 / 0.3 comparison is fully automatic. |
| R4 | Every metric needs the full contract: jurisdiction, code-set version, confidence method, permitted consumers. | NARROW. Required for rates, predictions, verdicts, and anything shown as impact. | A raw claim-line count can be published as a count without that contract. It still needs a period and a snapshot. | The contract list is in the docx under “Canonical measurement contract.” |
| R5 | Implement enrollment-interval exposure now. | NARROW. The rule “do not substitute claimants” is right. Staging enrollment is 0 rows. | Return NOT_MEASURABLE for utilization and PMPM. Do not build a partial-month convention until an enrollment table exists. The review does not choose the 15-day rule or the day-count rule. | `enrollment_records` count on staging was 0 at the audit. |
| R6 | No composite score until weights are formally validated. | NARROW. This scorecard’s index is not usable. | Remove this index from authoritative screens. Do not ban a later composite that has declared weights and inputs. | Section 13 of the inventory. |
| R7 | Mark the 2,250 observations NOT_MEASURABLE in place. | NARROW. Overwriting the stored status rewrites history. The same document says to preserve historical outputs. | Leave metrics and the original status. Add a quarantine record beside them. | Observation rows already contain `verdict_status` and `verdict_rule_version`. |
| R8 | No North Carolina context anywhere. | NARROW. Right for a national product default. | Do not strip NC from the frozen demo or from the BCBS-NC showcase policies. Do not apply NC as the default market on a national policy. | Densify wrote `market = NC` on synthetic staging lines. That is a seed choice, not a national rule. |
| R9 | OON leakage, top-10 share, and HHI are unimplemented. | REJECT as a description of the repo. **Inventory correction.** | `baseline_metrics_computation.py` lines 260–288 compute OON leakage and HHI on a 0–1 scale, using claimants × months. `baseline.py` lines 972–976 compute HHI × 10,000 and a top-10 share × 100 from provider line counts. | Two equal providers: mix path HHI = 0.5. Network path HHI = 5,000. Do not mix the scales. |
| R10 | Build episode, encounter, and unit rates now. | NARROW. Distinguishing them is right. | The impact engine counts lines (`len(df)`). An episode rate needs a grouper this review does not specify. | Do not invent episode ids. |
| R11 | Seven waves and nine new artifacts are the next code change. | REJECT as an immediate build. | They are a program plan. Calculation changes, demo edits, and staging rewrites are separate approvals. | The docx says it did not execute the code and did not certify the 250 policies. |

## Family register

Use this as the checklist. “Agree” means this review accepts the expert disposition, including the narrower reading in the table above.

| Family | Code location | Formula in code | Expert | Agree | Validate |
|---|---|---|---|---|---|
| Member-months | `database_baseline_computation.py`; `database_claims_loader.py` | claimants × months | REPLACE | Yes | Row 1 |
| Claims per member | database baseline | lines / claimants | RENAME | Yes | 240 / 100 = 2.4 per claimant |
| Cost per claim | database baseline versus impact engine | paid / lines, or mean allowed | RENAME, keep both | Yes | $90,000 / 240 = $375 paid per line |
| Utilization per 1,000 | dictionary, database baseline, impact engine, staging writer | four different ratios, one label | REPLACE | Yes | Rows 3 and 4 |
| Allowed PMPM | database baseline | allowed / (claimants × months) | REPLACE name and denominator | Yes | Not enrolled PMPM |
| Paid PMPM | claims loader | paid / (claimants × months), stored as `cost_pmpm` | REPLACE | Yes | Row 2 |
| Member cost share PMPM | dictionary only | share / member-months | IMPLEMENT WHEN ENROLLMENT | Yes | Field exists on the line and is unused |
| Annualized allowed | `baseline_metrics_computation.py` 77–84 | (PMPM × member-months / months) × 12 | KEEP | Yes | Row 6. $50,000 in January annualizes to $600,000 only as an extrapolation |
| Site share | `baseline.py` and mix metrics | count at POS / all lines × 100 | KEEP, fix mapping | Yes | POS 22 is labeled HOPD in the mix map |
| In-network share | mix metrics line 295 | in-network lines / lines × 100 | KEEP | Yes | Dictionary text is a fraction. This path stores a percent |
| OON leakage | mix metrics 260–275 | OON lines / (claimants × months) × 1000 | IMPLEMENT WHEN DATA | Narrow | **Inventory correction.** It is implemented, on the wrong denominator |
| Top 10 providers | `baseline.py` 976 | sum of the 10 largest line-count shares × 100 | IMPLEMENT WHEN DATA | Narrow | **Inventory correction.** Implemented on line counts, not allowed dollars |
| HHI | mix path versus `baseline.py` 973 | Σ share², or that times 10,000 | FIX the scale | Yes | Row R9 |
| System affiliation | `baseline.py` when a provider table is passed | affiliated allowed / total allowed | KEEP CONDITIONAL | Yes | Absent without provider linkage |
| Trend band | `baseline.py` `_simple_trend` | rolling mean, month mean minus series mean, ± 2 residual SD | FIX / restrict | Yes | Window is min(12, half the series). Pre windows elsewhere use months × 30 days |
| Pre/post and DiD | `impact.py` | post − pre, or that minus the control change | KEEP arithmetic, restrict the causal label | Yes | Row 35 |
| Bootstrap interval | `impact.py` | percentile of resampled changes | KEEP as a descriptive interval only | Narrow | It resamples lines, not members |
| Parallel trends, N, balance, CV | `method_checks.py` | 0.1 / 0.3, 1,000 lines, empty balance, variance/mean | FIX or REPLACE | Yes | Rows 8–11 |
| Prediction | `predicted_impact.py` | friction × elasticity × 100; cost = that × 0.9 | SIMULATION ONLY | Yes | Row 12 |
| Observation percent | `observation_enhancement.py` | (observed − baseline) / baseline × 100 | FIX so both sides are the same metric | Yes | Annual rate minus monthly rate fails this |
| Product verdict | `verdict.py` v1.0 | down or flat = ON_TRACK | REPLACE | Yes | Row 16 |
| Staging verdict | lifecycle script | compared with baseline × 0.95, cost ignored | QUARANTINE | Yes | Row 17 |
| Prediction error | dictionary | observed percent change − predicted percent change, in percentage points | FIX the stored staging delta, which subtracts rate levels | Yes | −10% observed and −8% predicted is −2 percentage points, not a dollar error |
| Forecast | `forecast_service.py` | slope = (last − first) / (n − 1); blend toward the prediction | RENAME accuracy | Yes | Row 18. Zero slope does not divide. Negative utilization forecasts are not floored |
| Substitution test | `substitution.py` | chi-square on this code versus other lines, pre versus post | RESTRICT | Yes | Lines are treated as independent. That is the same sample-size defect as row 9 |
| Deferral index and substitution uplift | dictionary only | post 30-day rate / baseline 30-day rate; observed − trend | NOT IMPLEMENTED | Yes | No function computes them |
| Trust panel | `trust_panel.py` | weighted constants | REPLACE | Yes | Row 22 |
| Scorecard | `storage_scorecards.py` | 30/25/25/20 with access = 80 | REPLACE | Yes | Row 23 |
| MPPR | `reimbursement_mppr.py` | rank by allowed; later lines × 0.50 | KEEP DEMO | Yes | $1,000 + $600 → post $1,300 against $1,600, impact $300 |
| Site-of-service price | `reimbursement_sos.py` | POS 22 and 19 × 0.80; other POS × 1; volume held at 0 | KEEP DEMO | Yes | $1,000 hospital allowed → post $800, impact $200 |
| Infusion steerage | `expansion_demo_scenarios.py` | first 2 HOPD lines repriced to $3,200 | KEEP DEMO | Yes | Baseline $18,200, post $14,600, impact $3,600 |
| NCCI PTP | `apply_ncci_ptp` | column two pays 0 unless indicator 1 and modifier 59, XE, XP, XS, or XU | KEEP DEMO | Yes | Baseline $4,400, post $3,600, impact $800, 3 pairs, 1 bypass |
| NCCI units | `apply_ncci_mue` | paid units = min(billed, 4) | KEEP DEMO | Yes | 6 × $50 with cap 4 → $300 to $200, impact $100. The 4 is not a CMS MUE |
| Therapy units | `apply_therapy_coverage` | paid units = min(billed, medically necessary units on the fixture) | KEEP DEMO | Yes | Baseline $420, post $340, impact $80 |
| Unimplemented mechanisms | no engine | prior auth decisions, step therapy, quantity history, referral, access, care management | NOT MEASURABLE | Yes | Do not fill these with the utilization formula |
| Data quality | `ingestion/data_quality.py` | weights above | KEEP + gates | Narrow | Row 25 |
| Baseline refresh | `baseline_refresh.py` 265–276 | relative percent; shift > 0.01; significant > 5; age > 90 days | FIX the wording | Reject their gloss | Row R1 |
| Staging lifecycle | `scripts/lean_staging_full_demo_lifecycle.py` | synthetic densify plus the rates in row 17 | QUARANTINE | Yes | Not an authoritative metric writer |
| Aliases | `unified_measures.py` 31–35 | `utilization_per_1k` and `cost_pmpm` point at target rates | REPLACE with versioned ids | Yes | Row 2 |
| Learning | `learning_loop.py` | 100 − absolute percent error; elasticity −0.8 and −0.75 × ratio | DISABLE the elasticity as authoritative | Yes | Rows 27 and 28. Confidence = min(0.95, 0.5 + n/20) |
| Scenario accuracy | `storage_scenario_accuracy.py` | 60/40 | FIX | Yes | Row 29 |
| Rollout Jaccard | `policy_rollout_recommendations.py` `_jaccard` | intersection / union, cutoff 0.55 | HEURISTIC | Yes | Empty with empty returns 1. One empty set returns 0 |
| Readiness | `policy_analytical_readiness.py` | flags from record presence | REPLACE | Yes | Row 32 |

## Hand checks

These are the numbers to recompute without the application. If a result differs, the report row that cites it fails.

| Check | Arithmetic | Result |
|---|---|---|
| Dictionary utilization | 120 lines / 1,000 member-months × 1,000 | 120 |
| Change | (90 − 120) / 120 × 100 | −25% |
| Allowed PMPM | 120,000 / 1,200 | $100 |
| Paid PMPM | 90,000 / 1,200 | $75 |
| January annualized | 50,000 / 1 × 12 | $600,000 extrapolated, not observed annual spend |
| HHI, equal split | 0.5² + 0.5² | 0.5, or 5,000 if multiplied by 10,000 |
| DiD | (80 − 100) − (95 − 100) | −15 |
| MPPR | 1,000 + 600 × 0.5 = 1,300; baseline 1,600 | impact 300 |
| Site of service | 1,000 × 0.80 | impact 200 |
| MUE demo | 6 × 50 versus 4 × 50 | impact 100 |
| Missing enrollment | 0 enrollment rows | utilization and PMPM are not measurable |

Staging example already recomputed, synthetic, not an effect: 90-Day Retail Maintenance Program, 11,279 lines in 2025 and 908 claimants. Stored baseline utilization 1,035.15 equals (11,279 / 908) × (1,000 / 12). January has 920 lines. The stored rate gap is about +193. The time-normalized count gap is (920 − 11,279 / 12) / (11,279 / 12) × 100 = −2.12%.

## What this report does not say

- It does not say the 250 code sets are clinically correct.
- It does not say any staging observation is a payer outcome.
- It does not authorize a change to the December 4 demo, a new Azure resource, or a cutover.
- It does not choose a partial-month enrollment rule or a clustered standard error.
- The expert document’s seven waves remain a later plan. They are not the validation result.
