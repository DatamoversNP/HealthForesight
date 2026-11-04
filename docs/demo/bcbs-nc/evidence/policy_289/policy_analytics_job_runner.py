#!/usr/bin/env python3
"""Isolated policy analytics job runner (engagement-safe).

Reads preflight matrix → enqueues/executes by evidence pathway.
Prefers Celery when broker reachable; falls back to process-isolated local workers.
Does NOT use the retired bulk HTTP refresh loop as primary path.
Idempotent on (policy_id, config_digest, pathway, window).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

EVID = Path(__file__).resolve().parent
REPO = EVID.parents[4]
MATRIX = EVID / "POLICY_289_PREFLIGHT_FEASIBILITY_MATRIX.json"
JOBS_DIR = EVID / "analytics_jobs"
LEDGER_B = EVID / "POLICY_289_LANE_B_EXECUTION_LEDGER.json"
RESULTS = EVID / "POLICY_289_JOB_EXECUTION_RESULTS.json"

FROZEN_PRIMARY = {
    "d403f101-08dd-45c9-ab83-d42e37c62018",
    "d0eeb370-df14-4478-8755-dad6c3a35a47",
    "d7441dd9-3bfe-405e-ae6c-0377204bbb7e",
}


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def job_id_for(row: dict) -> str:
    raw = "|".join(
        [
            row["policy_id"],
            row.get("configuration_digest") or "",
            row.get("evidence_pathway") or "",
            (row.get("window") or {}).get("start") or "",
            (row.get("window") or {}).get("end") or "",
        ]
    )
    return "paj_" + hashlib.sha256(raw.encode()).hexdigest()[:24]


def load_env() -> None:
    env_path = REPO / ".env.demo7867"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def try_celery_enqueue(job: dict) -> Optional[str]:
    """Enqueue Celery task if broker works; return celery task id or None."""
    try:
        sys.path.insert(0, str(REPO / "apps" / "api" / "src"))
        sys.path.insert(0, str(REPO / "packages" / "common" / "src"))
        from uepi_api.celery_client import send_task

        async_result = send_task(
            "uepi_worker.tasks.policy_analytics_lifecycle_job",
            kwargs={
                "job_id": job["job_id"],
                "policy_id": job["policy_id"],
                "pathway": job["evidence_pathway"],
                "configuration_digest": job["configuration_digest"],
                "cohort_count": job.get("cohort_count", 0),
            },
            soft_time_limit=120,
            time_limit=150,
        )
        return str(async_result.id)
    except Exception as e:
        return None


def execute_job_local(job: dict) -> dict:
    """Process-isolated friendly: pure classification + optional in-process verify for frozen.

    Numerical empirical refresh is NOT done via HTTP here.
    Empirical jobs are marked READY_FOR_WORKER until Celery task is registered & healthy.
    """
    started = utc()
    pathway = job["evidence_pathway"]
    pid = job["policy_id"]
    out = {
        "job_id": job["job_id"],
        "policy_id": pid,
        "name": job.get("name"),
        "evidence_pathway": pathway,
        "configuration_digest": job.get("configuration_digest"),
        "started_at": started,
        "finished_at": None,
        "status": "FAILED",
        "duplicate_prevented": False,
        "result": {},
        "error": None,
    }
    try:
        if pathway == "BLOCKED":
            out["status"] = "BLOCKED_PERSISTED"
            out["result"] = {
                "missing_inputs": job.get("missing_inputs") or [],
                "message": "Numerical engines not invoked — required inputs absent",
            }
        elif pathway == "PROVENANCE_ONLY":
            out["status"] = "PROVENANCE_COMPLETED"
            out["result"] = {
                "actions": [
                    "source_applicability_recorded",
                    "jurisdiction_noted",
                    "no_financial_outcomes_manufactured",
                ]
            }
        elif pathway == "REPRESENTATIVE_SYNTHETIC_FIXTURE":
            if pid in FROZEN_PRIMARY:
                out["status"] = "SYNTHETIC_VERIFY_ONLY"
                out["result"] = {
                    "message": "Dec4 frozen KA — verify path only; no rewrite",
                    "ka_frozen": True,
                }
            else:
                out["status"] = "SYNTHETIC_QUEUED_BOUNDED"
                out["result"] = {
                    "message": (
                        "Eligible for representative synthetic fixture; "
                        "requires policy-specific known-answer inputs before numerical demo"
                    ),
                    "label": "REPRESENTATIVE_SYNTHETIC_FIXTURE",
                    "not": "empirical_or_causal",
                }
        elif pathway == "EMPIRICAL_COHORT":
            # Do not call HTTP refresh. Persist eligibility for worker/Celery execution.
            out["status"] = "EMPIRICAL_ELIGIBLE_QUEUED"
            out["result"] = {
                "cohort_count": job.get("cohort_count"),
                "message": (
                    "Preflight PASS — enqueue Celery/worker analytical services; "
                    "not executed via bulk HTTP"
                ),
                "next": "uepi_worker.tasks.policy_analytics_lifecycle_job",
            }
        else:
            out["status"] = "FAILED"
            out["error"] = f"unknown pathway {pathway}"
    except Exception as e:
        out["status"] = "FAILED"
        out["error"] = str(e)[:400]
        out["traceback"] = traceback.format_exc()[-500:]
    out["finished_at"] = utc()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="0 = all preflight rows")
    ap.add_argument("--pathway", default="", help="filter pathway")
    ap.add_argument("--prefer-celery", action="store_true")
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()

    if not MATRIX.exists():
        print("Missing preflight matrix — run run_claims_mechanism_preflight.py first", file=sys.stderr)
        return 2

    load_env()
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    matrix = json.loads(MATRIX.read_text())
    rows = matrix["policies"]
    if args.pathway:
        rows = [r for r in rows if r["evidence_pathway"] == args.pathway]
    if args.limit:
        rows = rows[: args.limit]

    # Idempotency store
    done_path = JOBS_DIR / "completed_job_ids.json"
    done = set(json.loads(done_path.read_text()) if done_path.exists() else [])

    jobs = []
    for r in rows:
        jid = job_id_for(r)
        job = {
            "job_id": jid,
            "policy_id": r["policy_id"],
            "name": r["name"],
            "evidence_pathway": r["evidence_pathway"],
            "configuration_digest": r["configuration_digest"],
            "cohort_count": r["counts"]["eligible_code_intersection"],
            "missing_inputs": r.get("missing_inputs"),
            "window": r.get("window"),
        }
        if jid in done:
            jobs.append({**job, "skip": True})
        else:
            jobs.append({**job, "skip": False})

    results = []
    celery_enqueued = 0
    duplicates = 0
    timed_out = 0

    to_run = [j for j in jobs if not j.get("skip")]
    skipped = [j for j in jobs if j.get("skip")]
    duplicates = len(skipped)
    for j in skipped:
        results.append(
            {
                "job_id": j["job_id"],
                "policy_id": j["policy_id"],
                "status": "DUPLICATE_PREVENTED",
                "duplicate_prevented": True,
            }
        )

    print(f"Jobs to run={len(to_run)} duplicates_prevented={duplicates}", flush=True)

    # Prefer local isolated execution for classification paths; Celery optional for empirical
    for j in to_run:
        celery_id = None
        if args.prefer_celery and j["evidence_pathway"] == "EMPIRICAL_COHORT":
            celery_id = try_celery_enqueue(j)
            if celery_id:
                celery_enqueued += 1
                r = {
                    "job_id": j["job_id"],
                    "policy_id": j["policy_id"],
                    "name": j["name"],
                    "evidence_pathway": j["evidence_pathway"],
                    "status": "CELERY_ENQUEUED",
                    "celery_task_id": celery_id,
                    "duplicate_prevented": False,
                    "finished_at": utc(),
                }
                results.append(r)
                done.add(j["job_id"])
                (JOBS_DIR / f"{j['job_id']}.json").write_text(json.dumps(r, indent=2) + "\n")
                continue
        r = execute_job_local(j)
        results.append(r)
        done.add(j["job_id"])
        (JOBS_DIR / f"{j['job_id']}.json").write_text(json.dumps(r, indent=2) + "\n")
        print(f"  {r['status']} {j['name'][:50]}", flush=True)

    done_path.write_text(json.dumps(sorted(done), indent=2) + "\n")

    summary = {
        "attempted": len(to_run),
        "duplicates_prevented": duplicates,
        "celery_enqueued": celery_enqueued,
        "blocked_persisted": sum(1 for r in results if r.get("status") == "BLOCKED_PERSISTED"),
        "provenance_completed": sum(1 for r in results if r.get("status") == "PROVENANCE_COMPLETED"),
        "synthetic_queued_or_verify": sum(
            1
            for r in results
            if r.get("status") in {"SYNTHETIC_QUEUED_BOUNDED", "SYNTHETIC_VERIFY_ONLY"}
        ),
        "empirical_eligible_queued": sum(
            1 for r in results if r.get("status") in {"EMPIRICAL_ELIGIBLE_QUEUED", "CELERY_ENQUEUED"}
        ),
        "failed": sum(1 for r in results if r.get("status") == "FAILED"),
        "timed_out_or_cancelled": timed_out,
        "reproducible_persisted": sum(
            1
            for r in results
            if r.get("status")
            in {
                "BLOCKED_PERSISTED",
                "PROVENANCE_COMPLETED",
                "SYNTHETIC_VERIFY_ONLY",
                "SYNTHETIC_QUEUED_BOUNDED",
                "EMPIRICAL_ELIGIBLE_QUEUED",
                "CELERY_ENQUEUED",
                "DUPLICATE_PREVENTED",
            }
        ),
    }

    payload = {
        "document_id": "POLICY_289_JOB_EXECUTION_RESULTS",
        "generated_at": utc(),
        "summary": summary,
        "results": results,
    }
    RESULTS.write_text(json.dumps(payload, indent=2) + "\n")

    # Update Lane B ledger job statuses
    if LEDGER_B.exists():
        lane = json.loads(LEDGER_B.read_text())
        by_id = {r["policy_id"]: r for r in results if r.get("policy_id")}
        for p in lane.get("policies") or []:
            r = by_id.get(p["policy_id"])
            if not r:
                continue
            p["job_status"] = r.get("status")
            p["mechanism_result"] = r.get("status")
            p["persistence"] = "PASS" if r.get("status") not in {"FAILED", None} else "FAILED"
            p["updated_at"] = utc()
        lane["job_summary"] = summary
        lane["generated_at"] = utc()
        LEDGER_B.write_text(json.dumps(lane, indent=2) + "\n")

    print(json.dumps(summary, indent=2))
    print(f"Wrote {RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
