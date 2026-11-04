# Data Platform Migration Plan

## Target layers

1. **Landing/Raw** — immutable files, checksums, ingest manifests (ADLS)
2. **Validated/Curated** — Delta tables, contracts, quality checks
3. **Serving/Aggregates** — cohort summaries, snapshots
4. **Results** — versioned artifacts + PostgreSQL result index

## Compatibility path

Keep PostgreSQL `claims_lines` readable until **dual-run** passes:

| Check | Method |
|-------|--------|
| Row counts | Same snapshot ID, PG vs Databricks SQL |
| Paid/allowed sums | Tolerance policy documented |
| Code×lob×market buckets | Match preflight extract logic |
| Evidence digests | Compare checksums of published artifacts |

**Cutover rule:** UI reads switch only after dual-run PASS for a frozen snapshot; feature flag per tenant.

## Incremental processing

- Partition by tenant + service_date (and market when selective).
- Late-arriving data: reconcile windows, never silent overwrite of published snapshots.
- Compaction jobs for small files (Databricks OPTIMIZE / equivalent).

## Forbidden

- Blind historical copy without checksums.
- Claims payloads in Service Bus or job state JSON.
- Cache reuse across tenant/snapshot/config boundaries.

## Wave sequencing

Wave 3 delivers adapters + dual-run harness; Wave 2 only provisions ADLS containers when authorized.
