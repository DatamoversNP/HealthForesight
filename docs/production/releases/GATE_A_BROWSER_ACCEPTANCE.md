# Gate A browser acceptance — lean staging

Date: 2026-11-06. Signed in to https://hfleanstg-web.whiteplant-64737337.eastus2.azurecontainerapps.io as the staging admin. No staging rows, deployment settings, or the December 4 demo were changed.

Screenshots: `docs/production/releases/gate_a_browser_acceptance/`.

Overall: **not a full pass.** The verdict list, evidence dialog, executive baseline labels, and the reconciliation and objectives APIs behave as Gate A requires. The observation detail still presents the stored verdict as the verdict, and the executive rollup still shows a 0.0% change. The 10,000-life pilot stays stopped until those two screens are corrected.

| Screen | Result | What was seen |
| --- | --- | --- |
| Sign-in | PASS | Landed on the policy-owner dashboard. No page exceptions on the later routes. |
| Policy verdicts | PASS | 250 of 250. Screen value Inconclusive. Stored status BACKFIRE. Column reads “Dollars per claimant-month (not enrolled PMPM)”. Confidence is a dash. Reason: no endpoint contract, so a change is not a verdict. |
| Evidence dialog | PASS | Same policy. Cost change and utilization change are dashes, not zeros. Dollar label says not enrolled. The one-line still quotes the stored BACKFIRE text. |
| Objectives health API | PASS | 250 rows. Example: stored BACKFIRE, screen and recomputed INCONCLUSIVE, `verdict_is_recomputed` true. The page text includes “Screen value” and “Stored status”. The follow-up screenshot of those rows was still loading. |
| Reconciliation API | PASS | 250 policies. Readiness uses the stored status. Example text: stored BACKFIRE, screen recomputation INCONCLUSIVE, and the recomputed status is not the stored outcome. There is no separate reconciliation page in the nav. |
| Executive dashboard baseline | PASS | “Claim lines per 1,000 claimants (not enrolled utilization)” 1362.8. “Paid dollars per claimant-month (not enrolled PMPM)” $2426.17. |
| Executive cost and utilization cards | FAIL | The card still says “ΔPMPM”. Average utilization change is shown as 0.0% and described as an increase. |
| Observation list and detail | FAIL | Tiles and the CKD detail lead with Backfire risk and “Verdict: BACKFIRE”. They do not show the screen recomputation beside the stored status. Chart axes do say not enrolled. |
| What-if | PARTIAL | The configure screen rendered and Run Scenario stayed disabled until a policy is chosen. No page exception. A multi-policy result with a missing allowed amount was not run in the browser. The unit test for that case already passed. |
| Home dashboard | NOT_TESTED | The capture was still on the loading spinner. |
| Scenario comparison | NOT_TESTED | No scenario result was on screen. |

The pilot in `NINE_POLICY_EXECUTION_AND_10K_PILOT_PLAN.md` was not started.
