# Production Release Gates

A release may be labeled **enterprise production-ready** only if all **MUST** gates PASS with linked evidence.

## MUST

1. [ ] Dual operating modes (ADR-005 SaaS + customer subscription) reflected in IaC `deployment_mode` and identity profiles; per-release mode documented.
2. [ ] Staging provisioned via IaC (no portal-only snowflakes).
3. [ ] Durable job outbox + idempotency tests green in staging.
4. [ ] Hard cancellation verified against analytical compute/DB.
5. [ ] Dual-run analytics reconciliation PASS for frozen snapshot (if lake path enabled).
6. [ ] API / worker multi-replica health probes + rollback drill.
7. [ ] Backup restore drill evidenced for PG + critical lake prefixes.
8. [ ] Security matrix: no Critical open vulns on release artifacts; secrets via Key Vault/MI.
9. [ ] Performance smoke meets agreed SLO subset for that release.
10. [ ] December 4 / demo environment unchanged by the release pipeline.

## MUST NOT

- Claim HA or billion-row scale without tests.
- Deploy billable prod without authorization.
- Mix Celery + Service Bus + Temporal as competing schedulers.
- Ship policy customization under this program.

## Evidence links (fill per release)

| Gate | Link |
|------|------|
| Hardening / benchmarks | `docs/demo/bcbs-nc/evidence/policy_289/POLICY_289_ENTERPRISE_HARDENING_REPORT.md` |
| Contracts tests | `apps/api/tests/execution/test_execution_contracts.py` |
| IaC | `infra/terraform/envs/enterprise-staging` |
