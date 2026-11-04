# Reliability and DR Report

## Implemented / tested (demo)

| Control | Status | Evidence |
|---------|--------|----------|
| Multi-worker concurrent jobs | PASS (bounded) | Hardening report |
| Hard cancel + PG terminate | PASS | Hardening report |
| Idempotent duplicate submit | PASS | Hardening report |
| task_acks_late / reject_on_worker_lost | Configured | `celery_app.py` |
| Transactional outbox | Code + migration | `013`, `outbox.py` |
| Broker HA / PG failover | **FAIL / untested** | |
| Regional DR | Design only | |
| Backup restore drill | Outstanding | |

## Proposed RPO/RTO (by class — not contracted)

| Data class | RPO intent | RTO intent |
|------------|------------|------------|
| Job metadata / config | Near-zero (PG HA sync) | Minutes |
| Result index | Near-zero | Minutes |
| Lake snapshots | Minutes–hours (replication) | Hours |
| Demo Dec4 fixtures | Offline freeze | N/A (immutable) |

## Staging fault injection (planned)

Worker kill, SB outage, PG failover, storage 429/5xx — **staging only**.

## Non-claim

Azure service SLAs ≠ end-to-end HealthForesight availability until measured.
