# HealthForesight QA closure report

Date of final retest: 2026-11-07  
Staging builds under test: `healthforesight-api:mock-r1-20261106f`, `healthforesight-web:mock-r1-20261106f`, `healthforesight-web:mock-r1-dv-20261106f`  
Primary evidence package (open these four files):

1. `docs/production/releases/HEALTHFORESIGHT_AUTONOMOUS_PRODUCT_QA_REPORT.md`
2. `docs/production/releases/HEALTHFORESIGHT_QA_DEFECTS.csv`
3. `docs/production/releases/HEALTHFORESIGHT_QA_POLICY_MATRIX.csv`
4. `docs/production/releases/HEALTHFORESIGHT_QA_RESULTS.json`

Absolute paths on this machine:

- `/Users/nileshl/Private/HealthForesight/docs/production/releases/HEALTHFORESIGHT_AUTONOMOUS_PRODUCT_QA_REPORT.md`
- `/Users/nileshl/Private/HealthForesight/docs/production/releases/HEALTHFORESIGHT_QA_DEFECTS.csv`
- `/Users/nileshl/Private/HealthForesight/docs/production/releases/HEALTHFORESIGHT_QA_POLICY_MATRIX.csv`
- `/Users/nileshl/Private/HealthForesight/docs/production/releases/HEALTHFORESIGHT_QA_RESULTS.json`

This closure report does not replace those four artifacts. It consolidates what they prove, what they do not prove, what was fixed, and what still blocks full functional production readiness.

---

## 1. Decisions that stand

| Decision | Status | Meaning |
| --- | --- | --- |
| Staging for supported configurations | **GO** | The six payment-rule simulations, the review-only labeling, blocked/awaiting labeling, baselines, continuation predictions, observations, and executive separation are usable on lean staging. |
| Full 287-policy mock-client lifecycle as executed product | **Incomplete** | 191 policies lack a complete executable configuration. 90 are review-only (not payment effect). Only 6 are payment simulations. |
| Functional production readiness | **FAIL** | Staging evidence is not approval for another client. Engines, authority, codes, and parameters are incomplete. |

---

## 2. Evidence verification (challenge points)

### 2.1 Independent oracle

- Source: `qa/product_agent/oracle.py`
- It does **not** import `uepi_api`, `measurement_integrity`, or the lifecycle writers.
- What it does check:
  - Exposure-scaled continuation: `pre_allowed × post_mm / pre_mm`
  - Claim-line pre/post allowed totals vs stored baseline/observed totals (± $1)
  - Per-member-month difference consistency for continuation rows
  - Separate portfolio sums for payment-rule rows vs continuation rows
- What it does **not** check:
  - That continuation is the correct *policy effect* for a clinical or UM mechanism
  - That the six payment-rule population totals equal the published fixture answers (fixtures are offline arithmetic only)
  - Claim-by-claim recomputation of What-If payment engines on the longitudinal book

Matching −2.04 and −15.78 therefore proves **internal consistency of the stored rollups**, not that those dollars are intervention savings.

### 2.2 Pass rates and exclusions

| Layer | Count | Result | Excluded from pass rate? |
| --- | --- | --- | --- |
| Policy data contract | 287 | 287 pass | No. Failures would fail the run. |
| Policy calculation | 287 | 287 pass | No. Failures would fail the run. |
| Browser journeys | 36 | 36 pass on final retest | Sampled. 275 policies are `not_in_browser_sample` in the matrix. That is disclosed; it is not counted as 287 browser passes. |
| Review-only / blocked | 90 / 191 | Recorded as classes | Not counted as payment execution. |

First-run staging decision was **NO-GO** because three browser journeys failed. Those failures were not dropped from the pass rate; they flipped staging to NO-GO until retest.

### 2.3 Staging retest used the new builds

Final run identity:

- API revision `hfleanstg-api--0000013` → `mock-r1-20261106f`
- Web revision `hfleanstg-web--0000012` → `mock-r1-20261106f`
- Data Voyager revision `hfleanstg-web-datavoyager--0000012` → `mock-r1-dv-20261106f`
- December 4 demo remained `dec4-stab-5b587ed`

---

## 3. Before / after

| Metric | First staging run (`qa_evidence/first-run-results.json`) | Final retest (`HEALTHFORESIGHT_QA_RESULTS.json`) |
| --- | --- | --- |
| Policies discovered | 287 | 287 |
| Data contract failures | 0 | 0 |
| Calculation failures | 0 | 0 |
| Browser failures | 3 | 0 |
| Open engineering defects | HFQA-001, HFQA-002, HFQA-003 | 0 open; all three **fixed** |
| Staging decision | NO-GO | GO FOR SUPPORTED CONFIGURATIONS ONLY |
| Production readiness | FAIL | FAIL |
| Dashboard payment | −2.04 matches oracle | −2.04 matches oracle |
| Dashboard continuation | −15.78 matches oracle | −15.78 matches oracle |

### Defects closed in this cycle

| ID | Severity | Class | Root cause | Retest |
| --- | --- | --- | --- | --- |
| HFQA-001 | high | frontend / chart honesty | Baseline and observed period totals were shown without stating unequal window lengths (18 vs 15 months). | Passed on `mock-r1-20261106f` |
| HFQA-002 | high | frontend / What-If honesty | Identity only recognized `SYNTHETIC_PAYER_V1`, so the longitudinal catalog hid the not-savings warning on standard web. | Passed |
| HFQA-003 | high | frontend / What-If honesty | Same defect on Data Voyager. | Passed |

---

## 4. Remaining open items by severity

### Critical / high — product engineering (still open for production readiness)

None of the three first-run engineering defects remain open.

The following are **still open product-capability gaps**. They are not hidden by the pass rate; they are why production readiness stays FAIL and why the 287-policy mock client is incomplete as an *executed* product.

| Severity | Item | Evidence | Closure owner |
| --- | --- | --- | --- |
| Critical | Functional production readiness not met | Decision FAIL; engines/authority/codes incomplete | Product + engineering |
| High | What-If does not execute valid longitudinal payment scenarios | Identity marks `what_if_engine=NOT_THIS_POPULATION`. Agent verified warning visibility, overlap rejection (HTTP 400), and observation non-overwrite. It did **not** prove executable What-If across payment mechanisms on this dataset. | Engineering |
| High | Population payment-rule arithmetic not independently recomputed claim-by-claim | Oracle matched stored executive rollups only. Fixture answers remain offline. | Engineering / QA strengthen |
| Medium | Medicare rules inventory empty | API returns 200 with `count=0`. Page no longer 500. | Data / content, not invented rules |
| Medium | Browser coverage is family-sampled, not 287 journeys | 36 journeys; matrix marks 275 as not sampled | Accept as permanent design, or expand intentionally |
| Medium | All 287 stored verdicts are INCONCLUSIVE | Expected under `v1.1-endpoints` with no endpoint contract; not a silent favorable pass | Product policy on verdict contracts |

### Configuration resolution (not automatic software defects)

These 191 `legitimate_gap` rows must be resolved by an explicit mock-client configuration process. Do not “fix” them by inventing codes, clinical authority, or payment parameters.

| Bucket | Count | Notes |
| --- | --- | --- |
| BLOCKED | 147 | Includes no candidate code, unsigned clinical/coverage authority, no executable rule |
| AWAITING_CONFIGURATION | 44 | Required parameter named; only `quantity_limit_units` has an implemented engine |
| No candidate procedure code | 102 (`NO_CANDIDATE_CODE_IN_PACKAGE`); 122 packages with zero codes in matrix | Configuration / package content |
| Unsigned clinical or coverage authority | 43 | Authority gap, not a UI bug |
| Missing step-therapy / site-of-care / frequency / cost-share / payment / quantity / episode / product / coding-edit parameters | 44 awaiting + related MISSING_* blocked reasons | Client-choice or definition input |
| No executable rule in definition | 2 | Definition gap |

Separately, **90 REVIEW_ONLY** policies are configured for review-required / no-auto-deny. They are not payment effects. Treat them as supported review behavior, not as executed savings.

**6 PAYMENT_SIMULATION** policies are the supported payment-rule set for this mock client.

---

## 5. What prevents full functional production readiness

Exact blockers, in order:

1. **Incomplete executable catalog.** Only 6 of 287 policies are payment simulations. 90 are review-only. 191 lack a complete executable configuration. A real client cannot be approved from this mix without a configuration completion process.
2. **Missing authority and codes.** 43 unsigned clinical/coverage policies and 102 no-candidate-code blocks cannot be executed without authoritative inputs. Inventing them would falsify the product.
3. **Missing mechanism engines.** Of the 44 awaiting-configuration parameters, only `quantity_limit_units` has an implemented engine. Saving other parameters would not execute those families.
4. **What-If is not proven on this longitudinal population.** The warning is now honest. Executable scenario coverage across supported mechanisms is not established.
5. **Verdict contract.** Every observation remains INCONCLUSIVE under the endpoint rule. That is honesty today; it is not a production claim of measured policy success or failure.
6. **Oracle scope.** Dashboard reconciliation proves stored math consistency, not that continuation dollars are the correct policy effect for non-payment policies.
7. **Cross-client readiness.** Staging is a synthetic mock client. Passing staging does not approve another payer’s data, codes, or authority.

---

## 6. Recommended next cycle (targeted, not another broad audit)

Keep `python -m qa.product_agent` as the permanent regression gate. Do not rebuild it.

1. **Configuration board** for the 191 gaps: assign each row to authority / codes / client parameter / out-of-scope. No invented values.
2. **What-If capability sprint** for the 6 payment-rule policies on the longitudinal source (or a deliberate decision that What-If remains unavailable for this dataset).
3. **Payment-rule claim-level oracle** for the 6 payment simulations only.
4. **Regression compare:** after every staging deploy, run the agent and diff `HEALTHFORESIGHT_QA_RESULTS.json` against the previous run (policy counts, execution classes, dashboard totals, open defects, browser fails).
5. **Stop treating review-only and continuation as execution** in any release note or client-facing summary.

---

## 7. Artifact integrity checklist for independent review

When reviewing the four files, check these directly:

- [ ] Policy matrix has **287** data rows (plus header).
- [ ] `execution_class` counts are 191 / 90 / 6, not “287 executed.”
- [ ] `browser_result=pass` appears only for the sampled policies; most rows are `not_in_browser_sample`.
- [ ] Defect CSV shows HFQA-001..003 as **fixed**, with retest notes.
- [ ] Results JSON `dashboard.comparison` has both matches true at −2.04 and −15.78.
- [ ] Results JSON `decision.production` is **FAIL**.
- [ ] Report text states browser journeys = **36**, not 287.
- [ ] First-run NO-GO evidence still exists at `docs/production/releases/qa_evidence/first-run-results.json`.

This closure report ends the current QA cycle. The next instruction to engineering should be a prioritized configuration-and-capability closure list derived from these files, not another discovery audit.
