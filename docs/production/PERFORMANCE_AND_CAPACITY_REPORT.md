# Performance and Capacity Report

## Proposed SLOs (targets — not verified platform SLOs)

| Workload | Target |
|----------|--------|
| Cached/read API p95 | < 300 ms |
| Policy workspace p95 | < 2 s |
| Job submission p95 | < 500 ms |
| Precomputed what-if p95 | < 3 s |
| API availability | 99.95% monthly (end-to-end design TBD) |

Analytical jobs: separate **queue wait**, **compute**, **E2E** budgets — not one universal timeout.

## Measured (demo / bounded) — 2026-11-04

Source: `docs/demo/bcbs-nc/evidence/policy_289/POLICY_289_ENTERPRISE_HARDENING_REPORT.json`

| Metric | Value |
|--------|-------|
| Claims rows | ~3.51M |
| Worker topology | 2× threads c=2 |
| Bench c=4 jpm | ~247 (8 sleep probes) |
| API p95 under load | ~1–2 ms (`/health`) |
| Hard cancel | PASS (`pg_terminate_backend`) |
| Shared PG | YES — enterprise storage FAIL |

## Gaps vs billion-row / first customer

- No Databricks path measured.
- No 500M-row simulation.
- Connection pool budgets not sized for multi-tenant concurrency.
- Cost per million rows / per workload: **not measured**.

## Next harness increments

1. Job-submit API p95 with outbox.
2. Cohort COUNT against PG vs Delta (dual-run).
3. Concurrent what-if class isolation.
4. Autoscale Container Apps under synthetic queue depth.
