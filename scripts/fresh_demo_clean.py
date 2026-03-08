#!/usr/bin/env python3
"""
Phase 1: Fresh Demo Clean – Remove all source/target data and derived analytics for demo tenant.

Deletes (in safe FK order):
- observations
- impact_analysis_results, baseline_analysis_results, analysis_results_index, analysis_runs, analysis_configs, analysis_narratives, elasticity_analysis_results, whatif_scenario_results
- analyses
- baselines
- policy_predicted_impacts
- analytics_runs
- data_periods (if any reference dataset_snapshots we may skip or delete snapshots)
- ingestions, ingestion_errors
- pipeline_runs (optional)
- claims_lines, enrollment_records, provider_records (raw)

Run from repo root: python3 scripts/fresh_demo_clean.py [--tenant-id UUID] [--skip-raw] [--dry-run]
"""
import argparse
import sys
from pathlib import Path
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


def main():
    parser = argparse.ArgumentParser(description="Clean all demo data for a tenant (raw + derived)")
    parser.add_argument("--tenant-id", type=str, default=str(DEFAULT_TENANT_ID))
    parser.add_argument("--skip-raw", action="store_true", help="Do not delete claims_lines, enrollment_records, provider_records")
    parser.add_argument("--dry-run", action="store_true", help="Only print counts and exit")
    args = parser.parse_args()
    tenant_id = UUID(args.tenant_id)

    from sqlalchemy import text
    from uepi_api.database import SessionLocal

    db = SessionLocal()
    try:
        counts = {}

        def table_missing(exc: Exception) -> bool:
            """True if error is 'relation does not exist' (table not created yet)."""
            msg = str(exc).lower()
            return "does not exist" in msg or "undefinedtable" in msg

        def skip_and_rollback(msg: str) -> None:
            """Roll back so the next statement can run (transaction no longer aborted)."""
            if not args.dry_run:
                db.rollback()
            print(msg)

        BATCH_SIZE = 50_000

        def delete_table(name: str, table: str, where: str = "tenant_id = :tid"):
            if args.dry_run:
                r = db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE {where}"), {"tid": str(tenant_id)})
                c = r.scalar() or 0
                counts[name] = c
                print(f"  [dry-run] Would delete {c} from {table}")
                return
            r = db.execute(text(f"DELETE FROM {table} WHERE {where}"), {"tid": str(tenant_id)})
            counts[name] = r.rowcount
            print(f"  Deleted {r.rowcount} from {table}")

        def delete_table_batched(name: str, table: str):
            """Delete in batches to avoid statement timeout (e.g. claims_lines)."""
            if args.dry_run:
                r = db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE tenant_id = :tid"), {"tid": str(tenant_id)})
                c = r.scalar() or 0
                counts[name] = c
                print(f"  [dry-run] Would delete {c} from {table} (batched)")
                return
            total = 0
            while True:
                try:
                    # Delete one batch; subquery limits rows so each statement stays under timeout
                    r = db.execute(text(f"""
                        DELETE FROM {table} WHERE id IN (
                            SELECT id FROM {table} WHERE tenant_id = :tid LIMIT {BATCH_SIZE}
                        )
                    """), {"tid": str(tenant_id)})
                    n = r.rowcount
                    total += n
                    if not args.dry_run:
                        db.commit()
                    if n == 0:
                        break
                except Exception as e:
                    if not args.dry_run:
                        db.rollback()
                    raise e
            counts[name] = total
            print(f"  Deleted {total} from {table}")

        print("=" * 60)
        print("FRESH DEMO CLEAN")
        print("=" * 60)
        print(f"Tenant: {tenant_id}")
        if args.dry_run:
            print("(dry-run – no changes)")
        print()

        # 1. Observations (reference analyses, baselines, predicted_impacts, analytics_runs)
        print("1. Observations")
        try:
            delete_table("observations", "observations")
            if not args.dry_run:
                db.commit()
        except Exception as e:
            if table_missing(e):
                skip_and_rollback(f"  Skip observations (table missing)")
            else:
                raise

        # 2. Impact / analysis result tables (reference analyses)
        print("2. Analysis results")
        for t in ("impact_analysis_results", "baseline_analysis_results", "elasticity_analysis_results", "whatif_scenario_results", "analysis_narratives"):
            try:
                delete_table(t, t)
            except Exception as e:
                skip_and_rollback(f"  Skip {t}: {e}")

        # analysis_results_index, analysis_runs, analysis_configs – reference analyses
        for t in ("analysis_results_index", "analysis_runs", "analysis_configs"):
            try:
                if args.dry_run:
                    r = db.execute(text(f"SELECT COUNT(*) FROM {t} r JOIN analyses a ON r.analysis_id = a.id WHERE a.tenant_id = :tid"), {"tid": str(tenant_id)})
                    counts[t] = r.scalar() or 0
                    print(f"  [dry-run] Would delete {counts[t]} from {t}")
                else:
                    r = db.execute(text(f"DELETE FROM {t} WHERE analysis_id IN (SELECT id FROM analyses WHERE tenant_id = :tid)"), {"tid": str(tenant_id)})
                    counts[t] = r.rowcount
                    print(f"  Deleted {r.rowcount} from {t}")
            except Exception as e:
                skip_and_rollback(f"  Skip {t}: {e}")
        if not args.dry_run:
            db.commit()

        # 3. Analyses
        print("3. Analyses")
        try:
            delete_table("analyses", "analyses")
            if not args.dry_run:
                db.commit()
        except Exception as e:
            if table_missing(e):
                skip_and_rollback(f"  Skip analyses (table missing)")
            else:
                raise

        # 4. Baselines
        print("4. Baselines")
        try:
            delete_table("baselines", "baselines")
            if not args.dry_run:
                db.commit()
        except Exception as e:
            if table_missing(e):
                skip_and_rollback(f"  Skip baselines (table missing)")
            else:
                raise

        # 5. Predicted impact
        print("5. Policy predicted impacts")
        try:
            delete_table("policy_predicted_impacts", "policy_predicted_impacts")
            if not args.dry_run:
                db.commit()
        except Exception as e:
            if table_missing(e):
                skip_and_rollback(f"  Skip policy_predicted_impacts (table missing)")
            else:
                raise

        # 6. Analytics runs (table may not exist if migrations not fully applied)
        print("6. Analytics runs")
        try:
            delete_table("analytics_runs", "analytics_runs")
            if not args.dry_run:
                db.commit()
        except Exception as e:
            if table_missing(e):
                skip_and_rollback(f"  Skip analytics_runs (table missing)")
            else:
                raise

        # 7. Data periods (optional – may have FK to dataset_snapshots)
        print("7. Data periods")
        try:
            delete_table("data_periods", "data_periods")
            if not args.dry_run:
                db.commit()
        except Exception as e:
            if table_missing(e):
                skip_and_rollback(f"  Skip data_periods (table missing)")
            else:
                skip_and_rollback(f"  Skip data_periods: {e}")

        # 8. Ingestions
        print("8. Ingestions")
        try:
            delete_table("ingestion_errors", "ingestion_errors", "ingestion_id IN (SELECT id FROM ingestions WHERE tenant_id = :tid)")
            if not args.dry_run:
                db.commit()
        except Exception as e:
            if table_missing(e):
                skip_and_rollback(f"  Skip ingestion_errors (table missing)")
            else:
                skip_and_rollback(f"  Skip ingestion_errors: {e}")
        try:
            delete_table("ingestions", "ingestions")
            if not args.dry_run:
                db.commit()
        except Exception as e:
            if table_missing(e):
                skip_and_rollback(f"  Skip ingestions (table missing)")
            else:
                raise

        # 9. Pipeline runs (optional; table may not exist)
        print("9. Pipeline runs")
        try:
            delete_table("pipeline_runs", "pipeline_runs")
            if not args.dry_run:
                db.commit()
        except Exception as e:
            if table_missing(e):
                skip_and_rollback(f"  Skip pipeline_runs (table missing)")
            else:
                skip_and_rollback(f"  Skip pipeline_runs: {e}")

        # 10. Raw tables (batched to avoid statement timeout)
        if not args.skip_raw:
            print("10. Raw tables (claims_lines, enrollment_records, provider_records)")
            for t in ("claims_lines", "enrollment_records", "provider_records"):
                try:
                    delete_table_batched(t, t)
                except Exception as e:
                    if table_missing(e):
                        skip_and_rollback(f"  Skip {t} (table missing)")
                    else:
                        skip_and_rollback(f"  Skip {t}: {e}")
            if not args.dry_run:
                try:
                    db.commit()
                except Exception:
                    db.rollback()
        else:
            print("10. Raw tables skipped (--skip-raw)")

        print()
        print("=" * 60)
        if args.dry_run:
            print("Dry-run complete. Run without --dry-run to apply.")
        else:
            print("Clean complete.")
        print("=" * 60)
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
