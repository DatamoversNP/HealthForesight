# HealthForesight formula decision standard

Revision 2. 6 November 2026.

This is the authoritative decision record for the platform-wide formula review. It reconciles `PLATFORM_MEASURES_AND_FORMULAS.md`, `FORMULA_REVIEW_VALIDATION_REPORT.md`, the expert review `HealthForesight_Final_Formula_Expert_Review_and_Cursor_Implementation.docx` (Downloads, 6 November 2026), and the lean-staging observation audit under `docs/production/releases/corrections/observation_audit/`.

Every formula below was checked by reading the cited function. Arithmetic examples were recomputed by hand from those formulas. The `verify_*` payment functions were not executed. The staging database was not queried again. No application code, schema, staging row, demo fixture, infrastructure file, or production configuration was changed.

## A. Executive assessment

**Mathematically correct as written, and usable only inside the stated limit**

- Annualization `(allowed PMPM × member-months / months in period) × 12` equals the period allowed total when PMPM is that total divided by the same member-months. A 12-month total of $120,000 stays $120,000. A one-month total of $50,000 becomes $600,000 only as an extrapolation.
- Difference-in-differences arithmetic `(post − pre) − (control post − control pre)` is the standard contrast. Treated 100→80 and control 100→95 equals −15 metric units. The arithmetic does not by itself establish that a policy caused the change.
- Demo payment rules reproduce their own fixtures: MPPR secondary lines at 50 percent of allowed, hospital outpatient and off-campus lines at 80 percent of allowed, infusion steerage, NCCI PTP, a synthetic unit cap of 4, and therapy units capped at the fixture’s medically necessary units. Those results are scenario answers.
- Claim-line counts, distinct claimant counts, and dollars summed over a defined period are reconcilable descriptive totals when the grain and snapshot are stated.
- Jaccard on two code sets, name/scope/lever similarity, and the data-quality weighted score are internally consistent arithmetic. They are heuristics or descriptive scores.

**Incorrect for the name the product uses**

- “Per 1,000 member-months” and “PMPM” are computed from distinct claimants on claims, times a month count, in the database baseline, the claims loader, the staging writer, and the no-enrollment branch of `analytics/baseline.py`.
- Impact `utilization_per_1k` is claim lines per 1,000 distinct claimants, with no time denominator. The same label is used for the annual claimant rate divided by 12.
- `cost_pmpm` in the claims loader is paid dollars. `unified_measures.py` aliases that key to `allowed_pmpm_target`.
- Impact p-values are the constants 0.50 and 0.01.
- Product verdict v1.0 treats a decrease as success. A one-sided change, or an increase below 5 percent utilization and 10 percent cost, falls through to ON_TRACK.
- The staging writer compares an annual claimant rate with a monthly claimant rate and ignores cost. All 2,250 stored observations matched that formula in the 6 November audit and remain not measurable as utilization.

**Unsupported as evidence**

- Friction, category elasticity, the ×0.9 cost factor, provider-response percentages, patient deferral rates, prediction confidence points, trust-panel constants 85 and 85, scorecard access 80, learned elasticities −0.8 and −0.75, and scenario weights 0.6 and 0.4.
- `ElasticityModeler._load_historical_analyses` returns an empty list, so the historical branch never runs.
- Staging claims are synthetic densify plus small generator and Q1 demo sources. Enrollment rows in the audit were 0. Policy execution eligibility is fail-closed. The audit marked 250 of 250 policies scope-fail and 2,250 of 2,250 observations not measurable.
- Control balance always passes because the imbalance list is created empty. Seasonality divides variance by the mean. Sample size counts claim lines against 1,000. Parallel-trend gates use 0.1 and 0.3 with no unit.

**Unverified in this revision**

- Whether the live staging database still matches the audit snapshot taken at 2026-11-06T03:29:07Z. This revision did not reconnect.
- Whether any stored policy baseline used the writer’s general-metric fallback. The audit recorded 0 arithmetic mismatches; the fallback flag was not re-read from the database.
- The runtime result of sampling one row from an empty Polars frame in the bootstrap.
- The stored type of `in_network_flag` on staging, which decides whether the steerage sum is meaningful.
- Clinical correctness of the 250 policy code sets. This standard does not certify them.

Nothing in the current rate, prediction, verdict, forecast-accuracy, scorecard, or staging observation stack is suitable for authoritative payer reporting.

## B. Formula decision register

Decisions: KEEP, FIX, REPLACE, SIMULATION_ONLY, BLOCK, DEFER, UNVERIFIED.

“Authoritative now” is no for every rate and score below. Implementation approval is required before any code change. This register does not grant it.

Evidence grades: **H** source inspection plus hand arithmetic. **M** source inspection only. **A** prior read-only audit artifact, not re-queried here.

| ID | Formula | Source | Implemented calculation | Meaning and units | Issue | Decision | Corrected definition | Inputs required | Evidence | Limits | Approval |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F01 | Claimant exposure | `services/database_baseline_computation.py` `_compute` paths, lines 88–98 and 237–245; `database_claims_loader.py` line 291 | `unique_members × calendar months`. Loader uses 1 when the claimant count is 0 | Labeled member-months. Unit is claimant-months | Claimants are not enrolled exposure. Empty denominator is 0 in the database path and 1 in the loader | REPLACE | Eligible member-months from an enrollment interval. Until that exists, utilization and PMPM are NOT_MEASURABLE | Enrollment spans, plan, product | H | Do not pick a day-count rule here | Yes |
| F02 | Enrollment member-months | `analytics/baseline.py` `_calculate_pmpm` lines 610–613 | Count of (`member_id`, coverage month) on a supplied enrollment frame | Member-months if the frame is one row per member-month | Unused by staging. Partial-month convention is undefined. Missing month column was not executed | DEFER | Keep this shape only after the enrollment grain is specified | Real enrollment extract | M | Staging audit enrollment rows = 0 | Yes |
| F03 | Claims per member | database baseline line 109 | `lines / distinct claimants` | Lines per claimant in the window | Valid descriptive ratio under the wrong utilization name | FIX | Publish as claims per claimant, with window | Claim lines, member id | H | Not a rate per 1,000 | Yes to rename |
| F04 | Cost per claim | database baseline line 110; `impact.py` `avg_cost_per_claim` | Paid / lines, or mean allowed | Dollars per claim line | Two numerators share the idea of a unit cost | FIX | Name paid per line and allowed per line separately | Paid, allowed, line grain | H | Negatives would reduce the mean; staging audit had 0 negative amounts | Yes to rename |
| F05 | Utilization per 1,000 | dictionary; database baseline line 96; `impact.py` `_compute_metric` 349–355; staging writer | Dictionary and database: `(lines / claimant-months) × 1000`. Impact: `(lines / claimants) × 1000`. Staging month: `(month lines / month claimants) × 1000`. Staging year: that ratio divided by 12 | One label, four ratios | Name does not match any implemented denominator | REPLACE | `lines / eligible member-months × 1000` only when both are verified. Otherwise a named claimant ratio or NOT_MEASURABLE | Eligibility plus a stated grain | H | Impact has no month divisor, so a 1-month and a 12-month window can share the same value | Yes |
| F06 | Allowed PMPM | database baseline line 98 | `allowed / (claimants × months)` | Dollars per claimant-month, labeled PMPM | Denominator is not enrollment | REPLACE | Allowed / eligible member-months | Allowed amount, enrollment | H | Zero claimants store 0.0 | Yes |
| F07 | Paid PMPM and `cost_pmpm` | claims loader lines 294–301; `unified_measures.py` lines 31–34 | `paid / claimant-months`, stored as `cost_pmpm` and `paid_pmpm`. Alias maps `cost_pmpm` to `allowed_pmpm_target` | Paid and allowed share one key | Dimensional and semantic collision | REPLACE | Separate paid PMPM, allowed PMPM, and member-share PMPM | Paid, allowed, member share, enrollment | H | Alias must not survive | Yes |
| F08 | Member cost-share PMPM | metric dictionary only | No function divides member share by exposure | Undefined in outputs | Missing measure | DEFER | Member cost share / eligible member-months | Share field plus enrollment | M | Field exists on the contract and is unused | Yes |
| F09 | Annualized allowed | `baseline_metrics_computation.py` lines 70–84 | `(PMPM × member-months / months) × 12` | Period total when PMPM uses the same member-months. Not a forecast | Algebra holds. Upstream member-months may still be claimants | KEEP | Keep the identity. Label it period total, or an explicit extrapolation when the window is shorter than 12 months | The same PMPM inputs | H | $120,000 over 12 months stays $120,000 | No, unless inputs change |
| F10 | Site-of-care share | mix metrics lines 309–313; `baseline.py` site mix | Lines at a POS / all lines in the frame × 100 | Percent of lines | POS 22 is labeled HOPD. Share is not allowed-weighted | FIX | State line share versus allowed share. Keep the POS map under review | POS, and allowed if dollar-weighted | M | Descriptive mix only | Yes |
| F11 | In-network share | mix metrics lines 291–296 | In-network lines / lines × 100, accepting boolean and Y/N | Percent of lines | Dictionary text is a fraction. This path stores a percent | FIX | One scale, documented | Network flag | M | Descriptive | Yes |
| F12 | Steerage network percent | `baseline.py` `_calculate_steerage_metrics` line 1036 | `in_network_flag.sum() / lines × 100` | Percent if the flag is boolean | Y/N strings do not sum as counts. Staging column type not re-read | UNVERIFIED | Use the same parser as F11 | Flag type | M | Do not treat as leakage | Yes |
| F13 | OON leakage | `baseline_metrics_computation.py` lines 260–275 | OON lines / (claimants × months) × 1000 | Lines per 1,000 claimant-months | Implemented. Inventory “dictionary only” is wrong. Denominator is still claimants | FIX | OON lines / eligible member-months × 1000, or an OON line share with that name | Network flag, enrollment | H | Do not call it missing | Yes |
| F14 | Top 10 provider share | `baseline.py` lines 972–976 | Sum of the 10 largest provider line-count shares × 100 | Percent of lines | Implemented. Not an allowed-dollar share | FIX | Name it line concentration, or recompute on allowed | Provider id | H | Descriptive | Yes |
| F15 | HHI | mix path line 287; `baseline.py` line 973 | Σ(line share²), or that quantity × 10,000 | 0–1, or the 0–10,000 scale | Two scales for one name. Weights are line counts | FIX | Pick one scale and one weight. Equal two-provider split is 0.5 or 5,000 | Provider id, and dollars if dollar-weighted | H | Do not add the two scales | Yes |
| F16 | System affiliation | `baseline.py` `_calculate_system_affiliation` lines 1024–1029 | Affiliation value-counts × 100 after a provider merge | Percent of linked lines | The validation report described an allowed-dollar ratio. The code counts lines | FIX | State line share. Dollar share is a different measure | Provider linkage | H | Absent without the provider table | Yes |
| F17 | Trend band | `baseline.py` `_simple_trend` lines 277–307 | Rolling mean, month mean minus series mean, ± 2 residual SD. Window is min(12, half the series) | Descriptive band around a moving average | Not a forecast interval. Other windows use months × 30 days | FIX | Document the window. Do not call the band a confidence interval | A dated series | M | Descriptive | Yes |
| F18 | Pre/post and DiD | `impact.py` lines 141–171 | Windows are `months × 30` days. Effect is post − pre, or that minus the control change. Percent change is effect / pre × 100 when pre > 0, else 0 | Metric units, then a percent of the pre value | Calendar boundaries are approximate. A non-positive pre value becomes 0 percent | KEEP the contrast. FIX the zero case | Keep DiD arithmetic. Undefined percent stays unavailable. Causal label needs a design | Comparable pre and post metrics | H | −15 units in the worked example is not an effect estimate | Yes for labeling |
| F19 | Bootstrap interval | `impact.py` `_bootstrap_did_ci` lines 400–439 | Percentile of DiD values from line-level resampling | A resampling range of the line metric | Lines from the same member are treated as independent. Empty frames request sample size 1. That call was not executed | FIX | Describe it as a line-resample range, or return UNAVAILABLE. Do not mandate a cluster method | A non-empty frame | M | Runtime of the empty sample is UNVERIFIED | Yes |
| F20 | P-value | `impact.py` `_compute_p_value` lines 511–516 | 0.50 if the interval contains 0, else 0.01 | Not a probability from a test | Constants | BLOCK | Store UNAVAILABLE when a test is not defined | A real design, later | H | Do not publish 0.01 or 0.50 | Yes |
| F21 | Parallel trends | `method_checks.py` lines 184 and 324 | PASS if absolute slope difference < 0.1, WARN if < 0.3, else FAIL | Unitless | 0.1 is not comparable across utilization and dollars | REPLACE | No universal numeric gate. Visual review is a person’s judgment, not a PASS/FAIL | Slopes with a declared unit, if automated later | H | Current gate is not authoritative | Yes |
| F22 | Sample size | `method_checks.py` lines 203–205 | Pass when pre-period rows ≥ 1,000 | Claim lines | Lines are not independent members | FIX | Report lines, members, and providers separately. Do not pass on lines alone | Identifiers | H | 1,000 lines can be 50 members | Yes |
| F23 | Control balance | `method_checks.py` `_check_control_balance` lines 377–393 | Imbalance list starts empty, so balanced is true and score is 1.0. Covariates age, sex, and risk are named and unread | A false pass | Empty evidence is scored as balance | REPLACE | Standardized difference, or UNAVAILABLE | Covariates on the analysis unit | H | Trust panel then starts from this pass | Yes |
| F24 | Seasonality | `method_checks.py` lines 443–451 | `variance / mean`, then < 0.1 and < 0.2. Series is monthly line counts. Fewer than 12 months returns LOW | Misnamed coefficient of variation | CV is standard deviation / mean | FIX | Use SD/mean, or rename the statistic | Monthly counts | H | Current LOW/MEDIUM/HIGH is not a seasonality test | Yes |
| F25 | Predicted utilization and cost | `predicted_impact.py` lines 232–281 and 126 | Max lever friction. Prior auth 0.60, hard × 1.2, then cap 1. Imaging elasticity −0.35. `util% = friction × elasticity × 100`. `cost% = util% × 0.9` | Percent changes from a lookup | No claim history enters | SIMULATION_ONLY | Keep only as a labeled scenario | An explicit scenario id | H | 0.72 × −0.35 × 100 = −25.2%; cost −22.68% | Yes before any display change |
| F26 | Prediction confidence | `predicted_impact.py` lines 374–397 and 155–161 | Starts at 100. Subtract 30, 15, 20, or 10. After the default elasticity is filled in, the “missing elasticity” branch does not run, and the default dict has no `model_quality`, so the 30-point reduction is skipped. Method name becomes `ELASTICITY_MODEL` | A point score, not a probability | Default scenario is labeled as a fitted model | BLOCK | Confidence unavailable for lookup scenarios | None until a model exists | H | Do not show 100 | Yes |
| F27 | Provider and patient response tables | `predicted_impact.py` lines 329–371 | Friction < 0.30 → 70/20/8/2. Deferral = 0.10 × friction. Confidence constants 75 and 70 | Percentages | No history | SIMULATION_ONLY | Label as scenario assumptions | None | H | Not compliance | Yes |
| F28 | Elasticity modeler | `analytics/elasticity.py` lines 81–83 and 114–122 | Historical loader returns `[]`. Fewer than 2 analyses selects the category default | Same lookup as F25 | The regression described in the docstring does not run | SIMULATION_ONLY | Do not describe it as GAM or regression | Historical impacts, if a model is ever fit | H | Dead historical path | Yes |
| F29 | Observation percent change | `observation_enhancement.py` lines 1122–1144 | `(observed − baseline) / baseline × 100`. Baseline ≤ 0 and observed > 0 stores 999 or −999 | Percent, or a sentinel | 999 can enter a verdict. Sides must be the same metric and window | FIX | Same metric id, unit, and window. Undefined change is unavailable, not 999 | Paired metrics | H | Annual versus monthly fails this | Yes |
| F30 | Product verdict | `verdict.py` `compute_verdict`, rule v1.0 | Both changes ≤ 0 → ON_TRACK. Either util > 5 or cost > 10 → AT_RISK, or BACKFIRE if behavioral warnings exist. Any remaining non-null change, including a single +50% utilization change with cost missing, falls through to ON_TRACK | A status | Direction assumes “down is success.” Fallthrough is ON_TRACK | REPLACE | Require a policy objective. Missing objective or a missing side → inconclusive | Objective, both metrics, same window | H | Screening policies that should increase use fail a “down is good” rule when they work | Yes |
| F31 | Staging observations | `scripts/lean_staging_full_demo_lifecycle.py` lines 564–589 and 936–956 | Year rate `(lines / claimants) × (1000/12)`. Month rate `(lines / claimants) × 1000`. Month cost = allowed / month claimants, stored as `cost_pmpm`. Prediction util = baseline × 0.95, cost = baseline × 0.97. ON_TRACK when month util ≤ predicted × 1.05. BACKFIRE when month util > baseline × 1.10. Else AT_RISK. Cost ignored. A policy with zero scoped claims copies general metrics | Mixed windows and a stub status | Arithmetic matched the audit. Semantics are not utilization | BLOCK | Leave the 2,250 rows unchanged. Quarantine beside them | Not for repair in place | A for counts; H for the writer | Synthetic generator fills both years | Separate approval to add metadata only |
| F32 | Forecast | `forecast_service.py` `calculate_forecast` | Slope = (last − first) / (n − 1). Blend moves from the trend toward the prediction. Default horizon 12. Month 6 is a 50/50 blend. The last horizon month equals the prediction. “Accuracy at 6 months” is distance from that blend to the prediction. `\|slope\| < 0.1` is called stable | A projection and a self-agreement score | Accuracy needs a later actual. End-of-horizon agreement is algebraic | FIX | Rename the score convergence-to-prediction. Floor rules and units must be declared | Observed series plus a labeled target | H | Negative utilization is not floored | Yes |
| F33 | Substitution screen | `substitution.py` lines 189–198 | Keep codes whose allowed dollars rose and whose post line count is ≥ 10. Null baseline allowed is replaced by 1 before the percent. A zero baseline is not replaced | A ranked dollar increase | A rise is not substitution. The $1 fill fabricates a percent | FIX | Descriptive increase, or unavailable percent when baseline allowed is 0 or null | A defined substitute relationship, if a later measure is authorized | H | Up to the caller’s later cap | Yes |
| F34 | Substitution chi-square | `substitution.py` lines 341–361 | Chi-square on this code versus other lines, pre versus post. Returns a SciPy p-value when SciPy imports | A line-level p-value | Lines are not independent trials | SIMULATION_ONLY | Do not publish as a member-level test | None for authoritative use | M | Same defect as F22 | Yes |
| F35 | Provider archetypes | `provider_segmentation.py` `_label_archetype` lines 319–330 | Dollar and count thresholds: −1000 and −5, +1000 and site-shift 0.5, and the later bands. Stability = `1 / (1 + mean variance / 1000)` | Cluster labels | Thresholds ignore panel size | SIMULATION_ONLY | Do not read COMPLIERS as compliance | Provider panels with a declared unit | H | Seed 42 k-means is a clustering choice | Yes |
| F36 | Patient segments | `baseline.py` `_create_segments` lines 1137–1153; `baseline_segmentation_from_claims.py` lines 302–306; narrative methodology line 382 | Percentiles of total cost at 0.33 and 0.67, with a median stretch when those percentiles tie. A second path tertiles claim counts. Narrative text says $10,000 and $2,000 | Three different bands | The validation report described only the cost-percentile path | FIX | One definition. Current percentile bands are cost strata, not clinical risk | Member costs or counts, stated | H | Empty HIGH/LOW bands are still emitted | Yes |
| F37 | Deferral index | dictionary | 30-day post rate / 30-day baseline rate | Not computed | No timing engine | DEFER | Define the 30-day window before any build | Service dates and a cohort | M | Example 40 then 20 is 0.5 only as dictionary arithmetic | Yes |
| F38 | Substitution uplift | dictionary | Observed substitute rate minus trend | Not computed | No grouper | DEFER | Requires a substitute definition | Episode or time link | M | Section 10 is not this measure | Yes |
| F39 | Trust panel | `trust_panel.py` lines 205–227 | Method 90 if DiD else 70. Data quality 85. Methodology 85. Control 100 when no balance object, 90 when the empty check passes, 0 for pre/post. Weights 0.30, 0.20, 0.20, 0.15, 0.15. Sample score is lines/1000 × 100 | A weighted constant | Missing balance scores 100 | REPLACE | Unavailable until inputs are measured | Real method checks | H | Not a confidence probability | Yes |
| F40 | Effectiveness scorecard | `storage_scorecards.py` lines 31–83 | Weights 0.30, 0.25, 0.25, 0.20. Access is the constant 80. `defer_rate = abs(util change %) × 0.1` when the change is negative, then `100 − defer_rate × 200`. Regulatory score is confidence + 20 | A composite | −20% utilization sets defer_rate to 2 and the behavioral score to 0. The comment’s “0.5%” does not match the units | REPLACE | No authoritative index from these inputs. A later index may exist with declared weights | Validated components | H | This index is not a KPI | Yes |
| F41 | MPPR demo | `reimbursement_mppr.py` | Rank by allowed descending. Rank 1 pays allowed. Later lines pay 50% of allowed. `payment_impact = baseline_paid − post_paid` | Demo dollars | Fixture impact is $600, not the one-claim illustration of $300 | SIMULATION_ONLY | Keep the fixture. Do not call it CMS or payer adjudication | The fixture or an explicit scenario | H | Volume held at 0 | No for the fixture |
| F42 | Site-of-service demo | `reimbursement_sos.py` | POS 22 and 19 × 0.80. Other POS × 1. Volume change held at 0 | Demo dollars | Fixture impact is $520. A single $1,000 hospital line saves $200 | SIMULATION_ONLY | Keep the fixture | The fixture | H | Not a fee schedule | No for the fixture |
| F43 | Infusion steerage demo | `expansion_demo_scenarios.py` | First two HOPD lines repriced to $3,200 | Demo dollars | Known answer baseline $18,200, post $14,600, impact $3,600 | SIMULATION_ONLY | Keep the fixture | The fixture | H | Not steerage evidence | No for the fixture |
| F44 | NCCI PTP demo | `apply_ncci_ptp` | Column two pays 0 unless indicator 1 and modifier is 59, XE, XP, XS, or XU | Demo dollars | Baseline $4,400, post $3,600, impact $800, 3 pairs, 1 bypass | SIMULATION_ONLY | Keep the fixture. Not the CMS PTP file | The fixture | H | Mechanical, not causal | No for the fixture |
| F45 | Unit cap demo | `apply_ncci_mue` | Paid units = min(billed, 4). The 4 is a demo constant | Demo dollars | Capped line saves $100. Full fixture baseline $650, post $550, impact $100 | SIMULATION_ONLY | Keep the label synthetic | The fixture | H | Not a CMS MUE | No for the fixture |
| F46 | Therapy units demo | `apply_therapy_coverage` | Paid units = min(billed, medically necessary units on the line) | Demo dollars | Baseline $420, post $340, impact $80 | SIMULATION_ONLY | Keep the fixture | The fixture | H | Necessity units are supplied by the fixture | No for the fixture |
| F47 | Mechanism outcomes | no engine for prior authorization decisions, step therapy, quantity history, referral, access, or care management | Utilization formula is what gets stored | Not an outcome of those mechanisms | Filling them with F05 would misstate the policy | BLOCK | NOT_MEASURABLE until that mechanism has an engine and data | Decisions, histories, or program enrollment | A + M | 250 code sets are not certified | Yes |
| F48 | Data quality | `ingestion/data_quality.py` lines 136–144 and 294–335 | `0.30×completeness + 0.40×validity + 0.20×uniqueness + 0.10×(1 − min(errors/rows, 1))`. Uniqueness score uses the last `duplicate_count` in the function. An empty frame scores completeness and validity 1 | A 0–1 descriptive score | Key-field loop overwrites the row-duplicate count. Grain is whole-row unless `unique_fields` is set, and then only the last field | FIX | Score the declared grain. Empty input is unavailable, not perfect | A key definition | H | Do not hard-block every duplicate until voids and replacements are defined | Yes |
| F49 | Policy similarity | `policy/policy_similarity.py` lines 51–80 | `0.2×name + 0.3×scope + 0.4×levers + 0.1×dates`, report at ≥ 0.85 | A heuristic | Identical scope and levers, no shared words, no date overlap = 0.70 | SIMULATION_ONLY | Keep as a candidate list | Policy text and structure | H | Not identity | No |
| F50 | Baseline shift | `baseline_refresh.py` lines 126–131 and 260–276 | Change = `((new − old) / old) × 100`. Shift if absolute change > 0.01. Significant if > 5. Refresh suggested after 90 days. Keys read are `utilization_per_1k` and `cost_per_member_per_month` | Percent relative change | 100 → 100.02 is a 0.02 percent relative change and sets `shift_detected`. It is not 0.01 percentage points. Canonical keys `util_rate_*` and `cost_pmpm` are ignored and become 0 | FIX | Document 0.01 percent relative and 5 percent significant. Read the stored keys or return unavailable | The metric that was actually stored | H | Age rule is a freshness prompt | Yes |
| F51 | Measure aliases | `unified_measures.py` lines 30–35 | `utilization_per_1k` → `util_rate_target_per_1000_mm`; `cost_pmpm` and `cost_per_member` → `allowed_pmpm_target` | A rename that changes meaning | See F05 and F07 | REPLACE | Versioned ids with a unit | Mapping table | H | Comparison tables inherit the collision | Yes |
| F52 | Learning accuracy | `learning_loop.py` `calculate_prediction_accuracy` lines 32–49 | Error percent = `(observed − predicted) / abs(predicted) × 100` when predicted ≠ 0, else 0. Accuracy = `100 − abs(error percent)`. Within range if absolute error percent < 20. RMSE is set equal to the absolute error | A score | Predicted 0 stores accuracy 100 for any observed value. Predicted −10 and observed −8 is 20% error, accuracy 80, and outside the strict < 20 band | REPLACE | Undefined when predicted is 0. Do not use 100 minus percent error as a universal accuracy | Paired effects | H | Single-point RMSE equals absolute error only because n = 1 | Yes |
| F53 | Learned elasticity | `learning_loop.py` lines 147–177 | At least 3 observations. New util elasticity = `−0.8 × mean(observed/predicted)`. Cost uses −0.75. Confidence = `min(0.95, 0.5 + n/20)` | A scaled ratio | Not the imaging −0.35 table, and not a regression | BLOCK | Do not write these coefficients as authoritative elasticity | A specified model | H | Disabled for authoritative use | Yes |
| F54 | Scenario accuracy | `storage_scenario_accuracy.py` lines 226–240 | `0.6×util + 0.4×cost`. If predicted percent is 0, accuracy is 100 when observed is 0 and 0 otherwise | A weighted score | Both-zero scores 100 with no other evidence | FIX | Zero prediction is unavailable unless a separate rule says a zero change was the estimand | Paired percents | H | Weights are undeclared preferences | Yes |
| F55 | Rollout Jaccard | `policy_rollout_recommendations.py` `_jaccard` lines 159–192 | Intersection / union. Duplicate candidate if ≥ 0.55, same type, and both sets have size ≥ 2. Empty with empty returns 1. One empty set returns 0 | A set overlap | 0.55 is not proof of the same benefit | SIMULATION_ONLY | Candidate list only | Code sets | H | Not a duplicate verdict | No |
| F56 | Narrative arithmetic check | `narrative/calculation_validator.py` | Relative error ≤ 0.01 against `(claims / member_months) × 1000` and cost / member-months. Archetype averages also use an absolute tolerance of 0.01 | An arithmetic check | A wrong denominator used on both sides still passes | FIX | Call it an arithmetic check. Extend it only to compare metric id and window | The stated inputs | M | Does not validate clinical scope | Yes |
| F57 | Narrative performance bands | `observation_enhancement.py` near lines 800–825 | Decrease worse than −15% is described as excellent performance | Prose | Assumes the objective is a reduction | REPLACE | Same objective rule as F30 | A policy objective | M | Can describe the staging rows as success | Yes |
| F58 | Analytical readiness | `policy_analytical_readiness.py` `compute_policy_readiness` | CONFIGURED if id and name exist. Other flags follow record presence. IMPACT_ASSESSABLE also requires a causal flag | Existence flags | A blocked policy can still hold observations | REPLACE | Readiness requires valid inputs, not a row | Eligibility plus measurement status | H | All 250 staging policies can be OBSERVATION_READY and execution-blocked | Yes |

## C. Reconciled findings R1–R11

| ID | Final disposition | Ruling |
|---|---|---|
| R1 | REJECT the expert gloss | `baseline_refresh.py` converts the change to a percent and then compares with 0.01. A move from 100 to 100.02 is a 0.02 percent relative change and sets `shift_detected`. The separate significant-shift test remains absolute change > 5 percent. The 90-day refresh prompt stays a freshness rule. |
| R2 | NARROW | Remove publication of p = 0.01 and p = 0.50. When the design cannot support an uncertainty estimate, the result is UNAVAILABLE. This standard does not require cluster-aware bootstrap or any other single model. |
| R3 | NARROW | The automated gates 0.1 and 0.3 are not universal. Visual inspection of pre-trends is a human methodological judgment. It is not an automated PASS/FAIL result. |
| R4 | NARROW | A raw count needs grain, population or scope where it applies, period, and source snapshot. Rates, predictions, forecasts, verdicts, and impact estimates also need denominator, formula version, eligibility, provenance, and the method class. A count does not need a confidence method. |
| R5 | NARROW | Staging has no enrollment records in the audit. Do not fabricate exposure from claimants. Eligible-member-month utilization and PMPM stay NOT_MEASURABLE. No partial-month day-count convention is chosen. |
| R6 | NARROW | The current effectiveness scorecard is not an authoritative measure. A future composite with declared inputs, declared weights, and a stated validation is not forbidden. |
| R7 | NARROW | Preserve the original 2,250 rows, values, statuses, and rule versions. Do not overwrite them to NOT_MEASURABLE. Add a separate quarantine record. Design is in section G. It is not authorized to build. |
| R8 | NARROW | National policies do not default to North Carolina. BCBS-NC showcase scope and the frozen December 4 demo keep their NC content. Densify wrote `market = NC` on synthetic staging lines as a seed choice. |
| R9 | REJECT the “unimplemented” description | OON leakage, top-10 line share, and HHI are implemented. OON uses claimants × months. Top 10 and one HHI use line-count shares × 100 and × 10,000. The mix-path HHI stays on the 0–1 scale. An equal two-provider split is 0.5 or 5,000. |
| R10 | NARROW | The impact engine counts claim lines (`len(df)`). Encounters and episodes are different grains. This standard does not require those rates and does not invent a grouper. |
| R11 | REJECT as implementation authority | Waves 0–7 and the nine artifacts in the expert document are proposals. They are not approved work. None of them starts from this standard. |

## D. Mathematical examples

These are formula checks. They are not verified payer savings and they are not causal effects.

| Example | Arithmetic | Expected |
|---|---|---|
| Dictionary utilization | 120 lines / 1,000 member-months × 1,000 | 120 |
| Utilization change | (90 − 120) / 120 × 100 | −25% |
| Allowed PMPM | 120,000 / 1,200 | $100 |
| Paid PMPM | 90,000 / 1,200 | $75 |
| Annualization, full year | (100 × 1,200 / 12) × 12 | $120,000, the period total |
| Annualization, January only | 50,000 / 1 × 12 | $600,000 extrapolated |
| HHI, equal split | 0.5² + 0.5² | 0.5 on the mix path; 5,000 after × 10,000 |
| DiD | (80 − 100) − (95 − 100) | −15 metric units |
| MPPR illustration | 1,000 + 600 × 0.50 = 1,300; baseline 1,600 | impact $300 |
| MPPR fixture | 3,150 − 2,550 | impact $600, the code’s known answer |
| Site-of-service illustration | 1,000 × 0.80 | impact $200 |
| Site-of-service fixture | 4,000 − 3,480 | impact $520, the code’s known answer |
| Infusion fixture | 18,200 − 14,600 | impact $3,600 |
| PTP fixture | 4,400 − 3,600 | impact $800; 3 pairs; 1 modifier bypass |
| Unit-cap line | 6 × 50 versus 4 × 50 | impact $100 |
| Unit-cap fixture | 650 − 550 | impact $100 |
| Therapy fixture | 420 − 340 | impact $80 |
| Prediction lookup | 0.72 × −0.35 × 100, then × 0.9 | −25.2% utilization, −22.68% cost |
| Shift threshold | (100.02 − 100) / 100 × 100 | 0.02, which is greater than 0.01 |
| Learning pair | predicted −10, observed −8 | error 20%, accuracy 80, within-range false |
| Learning at zero | predicted 0, observed 10 | code stores accuracy 100; decision is UNAVAILABLE |
| Staging retail example | (11,279 / 908) × (1,000 / 12) | 1,035.15 stored baseline rate |
| Staging retail volume | (920 − 11,279 / 12) / (11,279 / 12) × 100 | −2.12% time-normalized count change |

The retail figures are the synthetic 90-Day Retail Maintenance Program from the audit. The stored rate gap near +193 and the count gap of −2.12% can both be true because the windows differ. Neither is a policy effect.

## E. Measurement and methodology standards

**Counts.** Grain is claim line, claim, unit, member, provider, or another declared unit. A count carries population or scope, period, and source snapshot.

**Rates.** Numerator grain, denominator, units, and time window are part of the result. Eligible-member-month utilization is lines, units, encounters, or episodes divided by eligible member-months, times 1,000, and only when the denominator is enrollment. A claimant ratio is named as a claimant ratio.

**Costs.** Allowed, paid, and member share are separate. PMPM divides the chosen dollars by eligible member-months. Dollars per 1,000 member-months are a different unit. Annualization is the identity in F09. It is a forecast only when labeled as an extrapolation beyond the observed window.

**Payment rules.** Demo engines report baseline paid, post paid, and payment impact as baseline minus post, with volume held at the fixture. They are SIMULATION_ONLY. They are not CMS edits and not plan adjudication.

**Predictions.** A lookup, a default, or a missing baseline produces a simulation or an unavailable result. The defaults 100 utilization and $500 PMPM are blocked. Confidence is unavailable unless a method defines it.

**Forecasts.** A slope and a blend are projections. Agreement between the projection and the prediction is convergence, not accuracy. Accuracy compares a forecast with a later actual that was not used to build it.

**Monitoring.** A monitoring status compares the same metric, unit, and window with a baseline or a declared threshold. The staging annual-versus-monthly comparison does not qualify.

**Causal evaluation.** Pre/post is a change. DiD is a contrast. Either one is a causal estimate only when the design, the comparison group, and the assumptions are stated and the diagnostics are real. No single model is mandatory. If the design is absent, the class is descriptive or NOT_MEASURABLE.

**Evidence classes.** OBSERVED_DESCRIPTIVE, MONITORING, SIMULATED_SCENARIO, ESTIMATED_ASSOCIATION, CAUSAL_ESTIMATE, NOT_MEASURABLE, INSUFFICIENT_EVIDENCE. A status string does not upgrade the class.

**Missing values.** A missing denominator, a missing baseline, or a missing objective is unavailable. It is not 0, 1, 999, 100 percent accuracy, or ON_TRACK.

**Uncertainty.** An interval that resamples claim lines is a line-level range. A p-value that was not computed is UNAVAILABLE.

## F. Policy-mechanism coverage

| Mechanism | What exists | Outcome class |
|---|---|---|
| Prior authorization, clinical criteria, step therapy, quantity or frequency history, referral, network access, care management | No decision or episode engine. Staging stores the generic utilization fields | NOT_MEASURABLE |
| Site-of-care mix | Line share by POS | Descriptive |
| Site-of-service price | Demo 80% on POS 22 and 19 | Simulation |
| MPPR, PTP, unit cap, therapy units, infusion price steerage | Demo fixtures with known answers | Simulation |
| Pharmacy | No sequence or days-supply engine in the reviewed outcome path | NOT_MEASURABLE |
| Benefit cost share | Dictionary formula only | Deferred |
| Any of the 250 staging policies | Execution eligibility fails closed when remediation says BLOCKED or the code map is unverified. The audit found 250 scope failures | Not certified. Code sets were not clinically reviewed in this revision |

## G. Historical staging treatment

The 6 November 2026 audit artifact records 53,949 claims, 1 general CY2025 baseline, 250 policy CY2025 baselines, 2,250 observations for January–September 2026, 0 enrollment rows, and 0 demo-warehouse copies. Arithmetic mismatches were 0. This revision did not confirm that the live database is still that snapshot.

Preservation requirements:

- Do not update `metrics_json`, `comparisons_json`, `verdict_status`, `verdict_reason`, `verdict_rule_version`, or claim rows for those 2,250 observations.
- Do not delete them and do not regenerate them to produce a success status.
- Do not change the 250 execution-eligibility blocks.
- Leave the December 4 demo untouched.

Proposed quarantine, not authorized to build:

- A separate record keyed by observation id, with reason codes `NO_ENROLLMENT`, `WINDOW_MISMATCH`, `SYNTHETIC_SOURCE`, and `SCOPE_UNVERIFIED`, plus the decision-standard revision and the review time.
- Authoritative screens would read that record and withhold outcome language.
- The original status `v1.0-scoped-month` remains the historical status.

## H. Implementation recommendations

**PROPOSED ONLY — NOT AUTHORIZED FOR IMPLEMENTATION**

1. Stop publishing p = 0.01 and p = 0.50. Return UNAVAILABLE.
2. Stop defaulting missing prediction baselines to 100 and $500, and stop labeling the lookup as `ELASTICITY_MODEL`.
3. Return unavailable, not 0, 1, or 999, when a denominator or a baseline is missing.
4. Split paid, allowed, and member share. Remove the `cost_pmpm` → allowed alias.
5. Add the quarantine record beside the 2,250 observations. Do not rewrite them.
6. Repair the uniqueness score so it uses the declared key, and score an empty file as unavailable.
7. Point the shift detector at the keys that were stored, and document 0.01 percent relative versus 5 percent significant.
8. Replace verdict v1.0 and the narrative “reduction is success” bands with an objective test that can return inconclusive.
9. Rename forecast self-agreement. Fix seasonality to SD/mean. Make control balance unavailable when covariates are unread.
10. Choose one HHI scale and state line weight versus dollar weight. Align the system-affiliation description with the line-count formula.
11. Collapse the three patient-band definitions to one named rule.
12. Eligible-member-month rates wait for an enrollment extract and a separate partial-month decision.

## I. Explicit non-goals

This revision does not change calculation code, database schemas, staging observations, demo fixtures, production configuration, or Azure resources. It does not copy claims, regenerate baselines, cut over the December 4 demo, or start the expert document’s seven waves.

## J. Verification limitations

| Check | Method in this revision |
|---|---|
| Formula text, units, and control flow | Source inspection of the files named in section B |
| Worked examples in section D | Hand arithmetic. Payment `verify_*` functions were not run |
| Staging counts, enrollment 0, arithmetic 2,250 / 2,250, scope fail 250 / 250 | Read from `observation_audit/audit_summary.json` and `OBSERVATION_CALCULATION_DEFECTS.md`. No new database session |
| Expert R1–R11 wording | Read from the docx paragraphs, including the 0.01 percentage-point sentence, the cluster-aware sentence, the in-place NOT_MEASURABLE sentence, and Waves 0–7 |
| Tests and live screens | Not run |

## K. Reconciliation with the validation report

The 35 accepted decisions in `FORMULA_REVIEW_VALIDATION_REPORT.md` stay accepted. Eight challenged statements stay narrowed (R2–R8 and R10). Three stay rejected (R1, R9, R11).

Formula text in that report is corrected here, without reversing those decisions:

- The MPPR engine’s fixture impact is $600. The $300 figure is a one-claim illustration of the same 50 percent rule.
- The site-of-service fixture impact is $520. The $200 figure is one $1,000 hospital line at 80 percent.
- The unit-cap fixture baseline is $650 and the post amount is $550. The impact remains $100.
- Staging cost prediction is baseline × 0.97. ON_TRACK is month utilization ≤ predicted × 1.05, which is baseline × 0.9975, then BACKFIRE above baseline × 1.10.
- System affiliation is a line-count percent, not an allowed-dollar share.
- Patient bands are cost percentiles in one function, claim-count tertiles in another, and dollar cutoffs only in narrative text.
- Verdict ON_TRACK is not limited to “both changes ≤ 0.” The later branch also returns ON_TRACK for a one-sided change and for increases below the 5 percent and 10 percent thresholds.

## L. New findings

| # | Class | Finding |
|---|---|---|
| N1 | Incorrect metric semantics | Verdict fallthrough labels one-sided and modest increases ON_TRACK (`verdict.py` lines 121–126) |
| N2 | Proven implementation defect | Learning accuracy is 100 when the predicted effect is 0 (`learning_loop.py` lines 33–37) |
| N3 | Incorrect metric semantics | Default elasticity is named `ELASTICITY_MODEL` and skips the confidence penalty (`predicted_impact.py` lines 116–161 and 374–397) |
| N4 | Proven implementation defect | Missing denominators become 0, 1, or 999 depending on the writer (database baseline, claims loader, `observation_enhancement.py`) |
| N5 | Proven code path; runtime UNVERIFIED | Bootstrap asks for one draw from an empty frame (`impact.py` lines 402–405) |
| N6 | Proven implementation defect | DiD percent change becomes 0 when the pre metric is ≤ 0 (`impact.py` line 171) |
| N7 | Proven implementation defect | Uniqueness score keeps the last duplicate counter; an empty frame scores as complete (`data_quality.py` lines 225, 302–335) |
| N8 | Incorrect metric semantics | The forecast’s last month equals the prediction, and `\|slope\| < 0.1` is called stable (`forecast_service.py` lines 102–105 and 147) |
| N9 | Proven implementation defect | Substitution percent replaces a null baseline allowed amount with $1 (`substitution.py` lines 191–192) |
| N10 | Incorrect metric semantics | Staging month `cost_pmpm` is allowed per claimant; zero-claim policies can copy general metrics (`lean_staging_full_demo_lifecycle.py` lines 583 and 954–956) |
| N11 | Incorrect metric semantics | System affiliation and steerage do not match the mix-path definitions (`baseline.py` lines 1028 and 1036) |
| N12 | Missing evidence propagation | Shift detection reads `utilization_per_1k` and `cost_per_member_per_month`, so canonical keys look like zero change (`baseline_refresh.py` lines 261–269) |
| N13 | Incorrect metric semantics | Three patient-band definitions coexist (F36) |
| N14 | Incorrect metric semantics | Narrative bands describe a utilization decrease as success (`observation_enhancement.py`) |
| N15 | Unsupported methodological assumption | `ElasticityModeler` never loads history because the loader returns an empty list (`elasticity.py` lines 114–122) |
