# Synthetic payer 500,000-life local run

Date: 2026-11-06. Local disposable database only. The dataset was not deployed. Staging, production, Azure, and the December 4 demo were not changed.

Every dollar below is a synthetic illustration. It is not real-world savings, CMS adjudication, clinical certification, or a causal effect.

## Configuration

| Item | Value |
| --- | --- |
| Git commit at HEAD | `0745a0c84e276ae085eaf6a04084762acbf4eb09` on `measurement-integrity-gate-a` |
| Code actually executed | That commit plus the uncommitted working tree, including the policy-identity baseline filter and the executive label |
| Generator | `synthetic-payer-v1` |
| Seed | `20261106` |
| Partial months | `SYNTHETIC_PARTIAL_MONTH_V1` |
| Census | 500,000 members enrolled on 2025-07-01 |
| Window | 2024-01-01 inclusive through 2026-10-01 exclusive |
| Database | `synthetic_payer_500k` on `127.0.0.1:55434` only |
| 10,000-life reference | Left in place as `synthetic_payer` (100 MB) |
| Disk before the run | 589 GB free. The run required at least 20 GB free |
| Machine memory | 24 GB. Peak process memory was 3.8 GB, under the 6 GB stop |

Machine-readable result: `data/synthetic/integration_500000.json`.

## Population

This is a 500,000-life covered population and a policy-event extract. It is not that population's full medical and pharmacy history.

| Fact | Value |
| --- | ---: |
| Reference enrollment | 500,000 |
| Mean enrolled days | 546.82 |
| Member-months | 8,986,494.004 |
| Member-months per reference member | 17.973 |
| Claim rows | 256,428 |
| Active claim rows | 215,000 |
| Members with no claims | 300,000 (60 percent, by the index rule) |
| Pharmacy rows | 0 |
| Enrollment month rows | 9,479,433 |

The application general baseline uses the same 8,986,494.004 member-months and `denominator_basis = ENROLLMENT`. A second SQL sum of the stored spans returned the same figure in 2.58 seconds.

Allowed equals plan paid plus member cost share on the whole claim table. Drift is $0.00. Count 256,428. Allowed $83,806,000. Plan paid $67,044,800. Cost share $16,761,200.

No frequency in the generator is taken from a cited commercial benchmark.

## Nine policies

Operational activation stays prohibited. Codes stay candidates. No endpoint contract is stored, so every verdict is `INCONCLUSIVE`. Shared CPT codes did not mix populations: every policy baseline line count matched the policy identity, and `cpt_overlap` is false for all nine.

| Policy | Execution | Active lines | Simulated allowed difference | Verdict |
| --- | --- | ---: | ---: | --- |
| MPPR | Simulation, secondary 50 percent | 20,000 | Payer pays $2,000,000 less | INCONCLUSIVE |
| Imaging site of service | Simulation, hospital 80 percent | 5,000 | $450,000 less. Neutral $0. Adverse −$225,000 | INCONCLUSIVE |
| PTP | Simulation | 10,000 | $1,519,600 less | INCONCLUSIVE |
| Unit cap | Simulation, demo cap 4, not a CMS MUE | 5,000 | $204,000 less | INCONCLUSIVE |
| Therapy | Simulation | 5,000 | $400,000 less | INCONCLUSIVE |
| Infusion site | Simulation, per claim. Codeset not closed | 5,000 | $6,750,000 less | INCONCLUSIVE |
| Lumbar MRI prior authorization | Source events only | 10,000 | none | INCONCLUSIVE |
| NCD 220.2 | Source events only | 5,000 | none | INCONCLUSIVE |
| LCD L34425 | Source events only | 5,000 | none | INCONCLUSIVE |

The six engines matched the independent oracle within $0.02, including the neutral and adverse site-of-service scenarios. Oracle results were not written into the baseline or observation tables. The MPPR evidence pack reads the stored observation: evidence class `SYNTHETIC_ILLUSTRATIVE`, execution `SYNTHETIC_SIMULATION`, payment difference $2,000,000, verdict `INCONCLUSIVE`.

Plan paid remains 80 percent of allowed. The engines score allowed dollars. Those amounts are not substituted for each other.

A policy baseline now keeps a line when its stored policy key matches the policy, and it still applies the policy's procedure scope. A line tagged for another policy is excluded even when the CPT is shared. Untagged claims, which this file does not contain, would still match by scope. On this run, 72148 did not mix imaging site of service with lumbar MRI, 70551 did not mix PTP with NCD 220.2, and 97110 did not mix the unit cap with therapy.

## Executive figure

On the 10,000-life application the card now reads **−1.27 $ / enrolled member-month**.

The label is: simulated allowed-dollar difference per enrolled member-month. Negative means simulated allowed is below baseline allowed. The figure is the sum of the policy allowed differences divided by the shared enrolled member-month denominator. It is not measured savings.

The same construction at 500,000 lives is −$11,323,600 / 8,986,494.004 member-months, about **−$1.26 per enrolled member-month**. The live screen is still the 10,000-life database, so it shows −1.27. Utilization on that screen stays Unavailable. Missing changes are not shown as zero.

## Performance

| Step | Seconds |
| --- | ---: |
| Generation | 3.0 |
| Database load | 1,089.5 |
| Baselines, general and nine policy | 7.6 |
| Read lines back and run six engines | 8.0 |
| Nine observations | 0.5 |
| Oracle comparison | 0.1 |
| Total inside the pipeline | 1,114.9 |
| Wall clock, including process startup | 1,118 |

| Resource | Value |
| --- | --- |
| Peak process memory | 3.8 GB |
| Database size | 4.2 GB |
| Claims identity query | 0.09 s |
| Policy, observation, and baseline counts | 0.03 s, 0.00 s, 0.00 s |
| Exposure recount | 2.58 s |

The 10,000-life API, which is the one serving the screen, answered the dashboard in 0.06 seconds with the corrected label.

## What-if

What-if does not calculate this population. The screen now says that when the loaded policies are the synthetic illustrations, and it does not present a legacy scenario as their result. There is no synthetic-population what-if run.

The next integration, when it is built, should call the same payment engines on the lines for the selected policy, label the output as a synthetic simulation, and keep MRI, NCD 220.2, and LCD L34425 without an outcome. It should not read an older scenario table and display it as this population.

## Demo readiness

Do not deploy this dataset.

The local pipeline can carry 500,000 covered lives through enrollment, policy-scoped baselines, six payment simulations, three blocked clinical policies, observations, inconclusive verdicts, and an evidence pack. That is enough to demonstrate the nine mechanisms.

It is not a complete payer book. A customer looking for enterprise medical and pharmacy analytics will see too few claims, because 300,000 members have none and there is no pharmacy file. Present it as a covered population plus the policy-relevant events, or build a fuller claims history before calling it a full book.

Remaining gaps: no endpoint contracts, candidate codes, infusion codeset not closed, clinical outcomes not measurable, what-if not connected, and the executive paid-dollar sketch is still an extrapolation labeled as not a confidence interval.
