# Measurement integrity P0 implementation specification

6 November 2026. Read-only specification. No calculation code, schema, database record, Azure resource, or demo fixture was changed to produce this document.

Working baseline: `docs/production/releases/HEALTHFORESIGHT_FORMULA_DECISION_STANDARD_V2.md`.

This package is the first bounded correction. It is not a platform rebuild and it is not Waves 0–7. Enrollment ingestion is out of scope. Staging has no enrollment, so an enrolled rate stays NOT_MEASURABLE. P1 items F48 (uniqueness score) and F50 (shift-detector keys) are out of scope.

## Decision required

Approve or reject the two gates below. Neither gate starts until you authorize it.

| Gate | What would change later | What stays untouched |
|---|---|---|
| A. New-output behavior | New calculations and read-time labels for F20, F26, F01, F06, F18, F29, F52, F30, F57, F07, F51, plus the F09 and F19 labels in the clarifications | Stored observation metrics, statuses, and rule versions. The 250 execution blocks. December 4 demo data and demo App Service |
| B. Quarantine metadata | A new table and, under a second approval, insert-only rows for the 2,250 staging observations | Columns and values on those observation rows |

## Clarifications carried into this package

1. **Annualization (F09).** `(allowed PMPM × member-months / months) × 12` stays. A result whose denominator is claimants is a claimant-based total. It must not be labeled as an enrolled-population annual amount. The algebra does not repair the denominator.
2. **Verdicts (F30, F57).** The default when a policy has no endpoint contract is INCONCLUSIVE. A later policy may declare one primary endpoint. Both utilization and cost are not a universal requirement. The contract names each required endpoint and its direction (`decrease`, `increase`, or `monitor_only`).
3. **Uncertainty (F19, F20).** Line-level bootstrap output is a descriptive resample range. It is not a validated confidence interval and it is not inferential uncertainty. P-values 0.01, 0.50, and the enhancement default 1.0 are not emitted. This package does not change the resampling algorithm and does not choose a clustered estimator.

## Package contents

| Priority | Correction | IDs |
|---|---|---|
| P0 | Stop fabricated p-values, confidence, and authoritative method labels | F20, F26 |
| P0 | Keep missing values missing | F01, F06, F18, F29, F52 |
| P0 | Stop objective-free ON_TRACK and reduction-is-success prose | F30, F57 |
| P0 | Separate paid and allowed identities on new comparisons | F07, F51 |
| P0 | Quarantine design that does not rewrite history | F31 |

---

## F20 — Placeholder p-value

**Current behavior.** `ImpactAnalysisEngine` in `packages/common/src/uepi_common/analytics/impact.py` sets `p_value` from `_compute_p_value` (lines 493–516) on both the difference-in-differences return (line 185) and the pre/post return (line 217). The function returns 0.50 when the resample range contains 0, otherwise 0.01.

`observation_enhancement.py` lines 196 and 204 copy that field and substitute 1.0 when it is missing (`float(...get("p_value", 1.0) or 1.0)`). Narrative text near line 805 treats `p_value < 0.05` as statistically significant.

`apps/api/src/uepi_api/routers/analyses.py` `complete_all_pending_analyses` (line 1519) writes a mock result with `"p_value": 0.01` into pending impact analyses. Several scripts under `apps/api/scripts/` do the same. Those scripts are not product paths. The route is a product path that writes the database when called.

`apps/worker/src/uepi_worker/analytics.py` already sets `p_value` to None. That behavior stays.

**Proposed correction.** `_compute_p_value` returns `None`. Callers pass `None` through. Enhancement does not substitute 1.0. Narrative does not say “significant” unless `uncertainty_status` is `INFERENTIAL` and a real p-value is present. This package never sets that status. `complete_all_pending_analyses` stops writing a numeric p-value; the route remains a development completer and its result is marked `SIMULATION_ONLY`. Do not call it as part of this work.

**Consumers.** Impact result objects; observation enhancement metrics; `MethodChecksDisplay.tsx` (renders `p_value` only when it is not null); analysis-complete route; demo scripts that are out of scope to edit except to avoid calling them.

**Compatibility.** `ImpactResult.p_value` is already `Optional[float]`. Null is compatible. Existing stored analysis JSON that already contains 0.01 or 0.50 is not rewritten. UI that checks `!== null` already hides a null. Clients that require a number will see a missing field on new results.

**Tests.** A range that contains 0 and a range that does not both yield `p_value is None`. Enhancement of a payload without `p_value` leaves it null. Narrative fixture with a negative percent change does not contain “statistically significant”.

**Expected new output.** `"p_value": null`, `"uncertainty_status": "UNAVAILABLE"`.

**Rollback.** Revert the Gate A commit so the last approved deployment is restored. That restored deployment still emits fabricated 0.01/0.50 p-values. Restoring those values is not an acceptable production correction. Stored rows are unchanged, so rollback does not need a data restore. Record that the restored deployment's analytical limitations remain.

---

## F26 — Prediction confidence and method label

**Current behavior.** `PredictedImpactGenerator.generate_predicted_impact` in `packages/common/src/uepi_common/analytics/predicted_impact.py` fills a default elasticity dict (lines 117–118), then sets `prediction_method` to `ELASTICITY_MODEL` whenever that dict is non-empty (line 155). The confidence penalty for a missing elasticity never runs. Missing baseline metrics become utilization 100, cost PMPM 500, and member count 10,000 (lines 129–131). Confidence is a required float 0–100 on `PredictedImpactMetrics`. Substitution, provider, and patient objects also carry constant confidence scores (70, 75, 70).

The API entry is `generate_predicted_impact_for_policy` in `apps/api/src/uepi_api/routers/policy_predicted_impact.py`. The web client is `apps/web/src/components/policy/PredictedImpactDisplay.tsx`, which divides `confidence_score` by 100 and colors it as if it were a probability. Scorecards read `confidence_score` and add 20 (`storage_scorecards.py` line 67). That scorecard formula is not in this package; it must tolerate a missing score instead of crashing.

**Proposed correction.** If the elasticity argument was not supplied by the caller, `prediction_method` is `SIMULATION_LOOKUP` and `evidence_class` is `SIMULATION_ONLY`. `confidence_score` is null on the prediction, the substitution effects, and the provider and patient responses. Missing baseline keys stay null. The generator does not invent 100, 500, or 10,000. Dollar totals that need those baselines are null. The lookup percent changes may still be returned, labeled as a scenario, because F25 remains SIMULATION_ONLY and is not deleted here.

**Consumers.** Predicted-impact API and UI, scorecard generation, scripts that call `generate_predicted_impact_for_policy`. Do not regenerate stored staging predictions as part of this package.

**Compatibility.** `confidence_score: float` becomes optional. That is a response-schema change. Ship the UI null check in the same change as the API. Old rows keep their stored numbers. New responses must not be described as an elasticity model.

**Tests.** No elasticity argument → method `SIMULATION_LOOKUP`, confidence null, evidence class `SIMULATION_ONLY`. No baseline → utilization and cost baselines null, not 100 and 500. A caller-supplied elasticity dict may still produce a numeric scenario percent, with confidence still null unless a future package defines a real score.

**Expected new output.** `"prediction_method": "SIMULATION_LOOKUP"`, `"confidence_score": null`, `"evidence_class": "SIMULATION_ONLY"`.

**Rollback.** Revert the generator and the UI null check together.

---

## F01 and F06 — Empty exposure and enrolled-rate labels

**Current behavior.** `services/database_baseline_computation.py` lines 94–98 and 242–245 set member-months to 0 when there are no claimants, then store utilization and PMPM as 0.0. `database_claims_loader.py` line 291 uses member-months 1 when the claimant count is 0, so the rate equals the dollar or line total. Both paths use claimants × months when claimants exist. `analytics/baseline.py` `_calculate_per_1k` always multiplies distinct claimants by 12. `_calculate_pmpm` can count enrollment rows when an enrollment frame is passed. Staging enrollment count in the audit was 0. This package does not add enrollment.

**Proposed correction.** Zero claimants: utilization, allowed PMPM, and paid PMPM are null, with `measurement_status` `NOT_MEASURABLE` and reason `EMPTY_DENOMINATOR`. The loader does not substitute 1. Non-zero claimants and no enrollment: do not relabel the claimant ratio as an enrolled rate. New metric payloads include `denominator_basis: "CLAIMANT_MONTHS"` and `enrolled_rate_status: "NOT_MEASURABLE"`. The existing numeric claimant ratio may remain under its current key for compatibility, with that basis flag. A separate key `claims_per_claimant` may carry lines / claimants. No new enrolled number is computed.

**F09 label, no algebra change.** `baseline_metrics_computation.py` lines 77 and 84 keep the annualization identity. The payload adds `annualization_basis`. When the basis is `CLAIMANT_MONTHS`, the display name is a claimant-based annualized total, not enrolled-population spend.

**Consumers.** Baseline API responses, predicted-impact baseline inputs, observation comparisons that copy these keys. Stored staging baselines are not rewritten.

**Compatibility.** Adding flags is backward compatible. Changing 0.0 to null on new empty windows is a behavior change for clients that treat 0 as “no utilization.” Document that 0 from this path meant “cannot divide,” not “zero use.”

**Tests.** 0 claimants → rates null, not 0 and not the raw total. 10 claimants and no enrollment → `enrolled_rate_status` `NOT_MEASURABLE` and `denominator_basis` `CLAIMANT_MONTHS`. Annualized value for $120,000 over 12 claimant-months remains $120,000 and is flagged claimant-based.

**Rollback.** Revert the writers. Stored baselines are unchanged.

---

## F18 and F29 — Undefined percent change

**Current behavior.** `impact.py` lines 171 and 205 set `percent_change` to 0.0 when the pre metric is ≤ 0. `observation_enhancement.py` lines 1128–1144 store 999 or −999 when the baseline is ≤ 0 and the observed value is positive. Lines 191–192 also coerce a missing effect and percent change to 0.0.

**Proposed correction.** Those branches set `percent_change` to null and `change_status` to `UNAVAILABLE`. They do not store 0 or 999. A real measured change of 0 percent is stored only when both sides exist and are equal, with `change_status` `MEASURED`.

**Consumers.** Impact results, observation comparisons, verdict inputs. A null change must hit the F30 inconclusive path rather than ON_TRACK.

**Compatibility.** Numeric fields become null on new calculations. Verdict and narrative code in this same package must accept null. Do not backfill old comparisons.

**Tests.** Pre metric 0 and post metric 10 → percent null, status `UNAVAILABLE`. Baseline 0 and observed 10 in enhancement → null, not 999. Baseline 100 and observed 100 → 0 percent, status `MEASURED`.

**Rollback.** Revert both functions together with the verdict null handling.

---

## F52 — Accuracy when the prediction is 0

**Current behavior.** `calculate_prediction_accuracy` in `apps/api/src/uepi_api/learning_loop.py` leaves `prediction_error_pct` at 0 when `predicted_effect_size` is 0, then sets accuracy to 100. `AccuracyRecordResponse` in `routers/learning.py` types `prediction_accuracy_pct` as a required float. `storage_learning.py` persists whatever the function returns. Historical accuracy rows are not rewritten.

**Proposed correction.** When the predicted effect is 0, `prediction_error_pct` and `prediction_accuracy_pct` are null and `accuracy_status` is `UNAVAILABLE`. The response model makes those two fields optional. The summary average skips nulls. A predicted −10 and observed −8 still yields error 20, accuracy 80, and `within_range` false.

**Consumers.** `GET /learning/accuracy/{policy_id}` and the history route. Web pages that read `prediction_accuracy_pct` must treat null as unavailable in the same change.

**Compatibility.** Required float becomes optional. Clients that require a number need the paired UI change. No update of existing `model_accuracy_history` rows.

**Tests.** Predicted 0, observed 10 → accuracy null, status `UNAVAILABLE`. Predicted −10, observed −8 → 80 and not within range. Summary of one null and one 80 averages 80, not 90.

**Rollback.** Revert the function and the response model together.

---

## F30 and F57 — Verdict and narrative

**Current behavior.** `compute_verdict` in `apps/api/src/uepi_api/verdict.py` (`VERDICT_RULE_VERSION = "v1.0"`) returns ON_TRACK when both percent changes are ≤ 0. Increases above 5 percent utilization or 10 percent cost become AT_RISK or BACKFIRE. Any other non-null change, including utilization +50 with cost missing, falls through to ON_TRACK at lines 121–126.

New observations copy that result in `storage_observations.py` lines 154–183. The policy verdict list in `routers/observations.py` lines 658–673 recomputes the verdict on read and does not write it back. That screen will change when `compute_verdict` changes, even though stored `verdict_status` does not.

Narrative bands in `observation_enhancement.py` lines 800–827 call a decrease “excellent,” “good,” or “moderate” performance, and call other values “needs improvement,” without a policy objective.

**Proposed correction.** Add an optional endpoint contract:

```text
required_endpoints: [
  { "metric_id": "utilization_per_1k", "direction": "decrease" }
]
```

`direction` is `decrease`, `increase`, or `monitor_only`. If the contract is absent, or a required endpoint’s change is null, the verdict is INCONCLUSIVE and the rule version for new writes is `v1.1-endpoints`. A contract with only utilization does not require cost. A contract with only cost does not require utilization. `monitor_only` does not produce ON_TRACK. Direction is applied only to the declared endpoints. Behavioral warnings do not create BACKFIRE unless a required endpoint missed its direction.

Narrative performance bands run only when the verdict is not INCONCLUSIVE and the contract supplies a direction. Otherwise the narrative states that the objective is not defined. It does not say the policy is achieving its objectives. It does not say a result is statistically significant (see F20).

**Stored 2,250 rows.** `verdict_status`, `verdict_reason`, `recommendation`, and `verdict_rule_version` (`v1.0-scoped-month` on the staging writer) are not updated.

**Read-time screen.** The verdict list keeps showing a recomputed value. For an observation that has a quarantine row (Gate B), the list shows the stored status as historical and sets the displayed decision to withheld, not to a new ON_TRACK. Until Gate B rows exist, staging policies with no endpoint contract show INCONCLUSIVE on that screen only. That is a display change, not a row update.

**December 4 demo.** This package is not deployed to the demo App Service. Demo seed scripts that set ON_TRACK directly are not edited. Recompute-on-read is the reason a shared deploy would change the demo screen; the deploy prohibition is the control.

**Consumers.** `storage_observations.py`, `routers/observations.py`, `services/policy_reconciliation_gate.py` (also calls `compute_verdict`), evidence pack labels, verdict UI.

**Compatibility.** New status values are not added. INCONCLUSIVE already exists. The behavior change is which inputs return it. `test_list_observations_latest_only_policy.py` pins a stored ON_TRACK row; update that test only if it asserts the recomputed screen. Do not change demo reimbursement known-answer tests.

**Tests.** No contract → INCONCLUSIVE, including utilization −20 and cost −10. Contract `{utilization, decrease}` and utilization −5 → ON_TRACK even if cost is missing. Same contract and utilization +5 → not ON_TRACK. Contract `{utilization, increase}` and utilization +5 → ON_TRACK. Missing change on a required endpoint → INCONCLUSIVE. Narrative without a contract does not contain “achieving its primary objectives” or “excellent performance.”

**Rollback.** Revert the Gate A commit to the last approved deployment. That deployment can still show objective-free ON_TRACK. Restoring that verdict behavior is not an acceptable production correction. Stored historical statuses are not rewritten by this package.

---

## F07 and F51 — Paid versus allowed

**Current behavior.** `database_claims_loader.py` lines 294–301 set `cost_pmpm` equal to paid PMPM and also set `allowed_pmpm`. `unified_measures.py` `BASELINE_KEY_ALIASES` maps `cost_pmpm` and `cost_per_member` to `allowed_pmpm_target`, and `utilization_per_1k` to `util_rate_target_per_1000_mm`. `normalize_to_canonical_key` is the lookup. Observation enhancement imports it.

**Proposed correction.** Stop mapping `cost_pmpm` and `cost_per_member` to `allowed_pmpm_target`. New comparison rows carry `paid_pmpm` and `allowed_pmpm` as separate keys. `cost_pmpm` on new payloads is either omitted or copied only with `cost_pmpm_meaning: "PAID"` when the source is the claims loader. A comparison does not subtract paid from allowed under one name. The utilization alias is left in place in this package and flagged `denominator_basis` from F01; renaming that key is not required to separate money.

**Consumers.** Unified measure keys, observation comparison builder, any UI column labeled allowed that currently reads `cost_pmpm`. Stored JSON is not migrated.

**Compatibility.** Removing the alias changes new comparison tables: a paid number no longer appears in the allowed column. Callers that only read `allowed_pmpm_target` will see it empty when the only source key was `cost_pmpm`. That is the intended break for new outputs. Add a release note. Do not rewrite historical comparisons.

**Tests.** Loader output with paid 75 and allowed 100 yields `paid_pmpm` 75 and `allowed_pmpm` 100. `normalize_to_canonical_key("cost_pmpm")` does not return `allowed_pmpm_target`. A comparison fixture does not show 75 as allowed.

**Rollback.** Restore the alias map.

---

## F19 label only

No change to `_bootstrap_did_ci` or `_bootstrap_pre_post_ci`. New impact payloads add:

```text
uncertainty_status: UNVERIFIED_INFERENTIAL
resample_grain: CLAIM_LINE
```

The existing `confidence_interval` tuple may remain so current clients do not break. New UI copy calls it a line-level resample range. It must not say “95% confidence” or “statistically significant.” Empty-frame sampling is unchanged and stays unverified. Justifying dependence is a later package.

---

## F31 — Quarantine design (Gate B)

**Do not alter** `observations.metrics_json`, `comparisons_json`, `verdict_status`, `verdict_reason`, `recommendation`, `verdict_rule_version`, claim rows, baselines, or execution-eligibility fields.

**Proposed table** `observation_measurement_quarantine`:

| Column | Role |
|---|---|
| `id` | Primary key |
| `tenant_id` | Tenant |
| `observation_id` | The string `observations.observation_id`. Unique with tenant |
| `reason_codes` | One or more of `NO_ENROLLMENT`, `WINDOW_MISMATCH`, `SYNTHETIC_SOURCE`, `SCOPE_UNVERIFIED` |
| `evidence_class` | `NOT_MEASURABLE` |
| `decision_standard` | `HEALTHFORESIGHT_FORMULA_DECISION_STANDARD_V2` |
| `created_at` | Insert time |

No foreign key that cascades into `observations`. Insert-only. The application reads the row and withholds outcome language. The historical status remains visible as historical.

**Population.** A separate approval, after the table exists, may insert one row per staging observation in the January–September 2026 set of 2,250, with all four reason codes, matching the audit. That insert does not update the observation. If the live count is no longer 2,250, stop and report; do not guess ids. This specification does not perform that insert.

**Rollback.** Drop the table or stop reading it. Observation rows do not need restoration.

---

## Rollout

1. Implement Gate A on a branch. Run the tests in this spec. Do not point them at the December 4 demo database.
2. Review the diff against this document. Reject any edit under `scripts/demo/`, demo seed known answers, or `docs/demo/bcbs-nc` fixtures.
3. Deploy Gate A only to an environment you name in the approval. Lean staging is the candidate. The demo App Service is excluded.
4. Gate B DDL, then a separate approval for the insert-only quarantine rows.
5. Do not copy enrollment, do not densify claims, and do not recompute the 2,250 observations.

## Acceptance criteria

- New impact results have `p_value` null and do not contain 0.01 or 0.50 from `_compute_p_value`.
- New lookup predictions have confidence null, method `SIMULATION_LOOKUP`, and do not fill 100 / 500 / 10,000.
- Zero claimants produce null rates, not 0 and not a divisor of 1.
- Non-zero claimant rates carry `denominator_basis` `CLAIMANT_MONTHS` and `enrolled_rate_status` `NOT_MEASURABLE`.
- Annualization of a claimant-based input remains algebraically the period total and is labeled claimant-based.
- Undefined percent changes are null, not 0 or 999. A true zero change stays 0 with status `MEASURED`.
- Predicted effect 0 yields accuracy null, not 100.
- No endpoint contract yields INCONCLUSIVE. A one-endpoint contract is judged on that endpoint only.
- Narrative without a contract does not claim excellent performance or statistical significance.
- `cost_pmpm` is not aliased to `allowed_pmpm_target` on new comparisons.
- Bootstrap code is unchanged. New payloads say the range is not inferential.
- The 2,250 observation rows, the 250 execution blocks, and the December 4 demo are byte-for-byte unchanged by the implementation.
- Gate B, if approved, adds rows only in `observation_measurement_quarantine`.

## Explicit exclusions

Enrollment load, partial-month day-count rules, cluster bootstrap, uniqueness-score repair (F48), shift-detector key repair (F50), scorecard weight redesign, forecast rewrite, payment-fixture edits, clinical review of the 250 code sets, and any Azure change.
