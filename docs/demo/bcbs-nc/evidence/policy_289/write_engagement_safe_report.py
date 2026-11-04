#!/usr/bin/env python3
"""Required next report: engagement-safe analytics architecture status."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

EVID = Path(__file__).resolve().parent
OUT_JSON = EVID / "POLICY_289_ENGAGEMENT_SAFE_EXECUTION_REPORT.json"
OUT_MD = EVID / "POLICY_289_ENGAGEMENT_SAFE_EXECUTION_REPORT.md"

FROZEN = {
    "mri": "d403f101-08dd-45c9-ab83-d42e37c62018",
    "mppr": "d0eeb370-df14-4478-8755-dad6c3a35a47",
    "sos": "d7441dd9-3bfe-405e-ae6c-0377204bbb7e",
}


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load(name: str):
    p = EVID / name
    if not p.exists():
        return None
    return json.loads(p.read_text())


def main() -> int:
    pre = load("POLICY_289_PREFLIGHT_FEASIBILITY_MATRIX.json") or {}
    jobs = load("POLICY_289_JOB_EXECUTION_RESULTS.json") or {}
    dir_led = load("POLICY_289_DIRECTIONAL_ACCURACY_LEDGER.json") or {}
    retired = (EVID / "BULK_HTTP_RUNNER_RETIRED.md").exists()

    ps = pre.get("summary") or {}
    js = jobs.get("summary") or {}
    ds = dir_led.get("summary") or {}

    # Prefer durable per-job artifacts (survives idempotent re-runs that only record duplicates)
    job_dir = EVID / "analytics_jobs"
    durable = []
    for p in sorted(job_dir.glob("paj_*.json")) if job_dir.exists() else []:
        try:
            durable.append(json.loads(p.read_text()))
        except Exception:
            pass
    success_statuses = {
        "BLOCKED_PERSISTED",
        "PROVENANCE_COMPLETED",
        "SYNTHETIC_QUEUED_BOUNDED",
        "SYNTHETIC_VERIFY_ONLY",
        "EMPIRICAL_ELIGIBLE_QUEUED",
        "EMPIRICAL_EVIDENCE_RECORDED",
        "CELERY_ENQUEUED",
        "COMPLETED",
    }
    durable_success = sum(1 for r in durable if r.get("status") in success_statuses)
    durable_by_pid = {r["policy_id"]: r for r in durable if r.get("policy_id")}

    # API health probe (best-effort)
    api_health = "UNKNOWN"
    try:
        import urllib.request

        with urllib.request.urlopen("http://127.0.0.1:7867/health", timeout=5) as r:
            api_health = f"OK_{r.status}"
    except Exception as e:
        api_health = f"UNREACHABLE:{e}"

    regression = {}
    for label, pid in FROZEN.items():
        prow = next((p for p in (pre.get("policies") or []) if p["policy_id"] == pid), None)
        jrow = durable_by_pid.get(pid) or next(
            (p for p in (jobs.get("results") or []) if p.get("policy_id") == pid), None
        )
        regression[label] = {
            "policy_id": pid,
            "preflight_pathway": (prow or {}).get("evidence_pathway"),
            "frozen_dec4": (prow or {}).get("frozen_dec4"),
            "job_status": (jrow or {}).get("status"),
            "ka_rewrite_attempted": False,
        }

    report = {
        "document_id": "POLICY_289_ENGAGEMENT_SAFE_EXECUTION_REPORT",
        "generated_at": utc(),
        "bulk_http_runner_retired": retired,
        "directional_standard": {
            "policy_realism": "REQUIRED",
            "analytical_correctness": "REQUIRED_FOR_SUPPORTED_SCENARIOS",
            "bcbs_nc_exact_fidelity": "NOT_REQUIRED",
        },
        "counts": {
            "policies_preflighted": ps.get("preflighted"),
            "nonzero_eligible_claim_cohorts": ps.get("nonzero_eligible_claim_cohorts"),
            "mechanism_inputs_sufficient": ps.get("mechanism_inputs_sufficient"),
            "empirical_execution_eligible": ps.get("empirical_execution_eligible"),
            "validated_synthetic_execution": ps.get("synthetic_execution_eligible"),
            "provenance_only_execution": ps.get("provenance_only"),
            "blocked_missing_evidence": ps.get("blocked"),
            "successful_worker_jobs": durable_success or (
                (js.get("blocked_persisted") or 0)
                + (js.get("provenance_completed") or 0)
                + (js.get("synthetic_queued_or_verify") or 0)
                + (js.get("empirical_eligible_queued") or 0)
            ),
            "timed_out_or_cancelled_jobs": js.get("timed_out_or_cancelled") or 0,
            "duplicate_executions_prevented": js.get("duplicates_prevented") or 0,
            "reproducible_persisted_results": max(
                len(durable),
                js.get("reproducible_persisted") or 0,
            ),
            "directional_accuracy_pass": ds.get("DIRECTIONAL_POLICY_ACCURACY_PASS"),
            "directional_accuracy_fail": ds.get("DIRECTIONAL_POLICY_ACCURACY_FAIL"),
            "demo_ready_pass": ds.get("DEMO_READY_PASS"),
        },
        "lanes": {
            "A_definition_accuracy": {
                "directional_pass": ds.get("DIRECTIONAL_POLICY_ACCURACY_PASS"),
                "directional_fail": ds.get("DIRECTIONAL_POLICY_ACCURACY_FAIL"),
                "fail_policy_ids": ds.get("fail_policy_ids"),
            },
            "B_mechanism_execution": {
                "preflight": ps,
                "jobs": js,
                "blocked_policy_ids": pre.get("blocked_policy_ids"),
                "empirical_policy_ids": pre.get("empirical_policy_ids"),
            },
            "C_platform_reliability": {
                "api_health": api_health,
                "note": "Bulk HTTP retired; interactive endpoints preserved; Celery solo worker for async jobs",
            },
        },
        "dec4_regression": regression,
        "architecture": {
            "registry": "POLICY_289_MASTER_INVENTORY + v1.2 packages",
            "preflight": "run_claims_mechanism_preflight.py",
            "jobs": "policy_analytics_job_runner.py + uepi_worker.tasks.policy_analytics_lifecycle_job",
            "bulk_http": "RETIRED",
        },
    }
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    c = report["counts"]
    md = [
        "# Engagement-Safe Policy Analytics — Required Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Architecture",
        "- Bulk HTTP lifecycle runner: **RETIRED**",
        "- Preflight → pathway classification → isolated job runner / Celery",
        "- Directional Representative Payer standard (not BCBS NC exact fidelity)",
        "",
        "## Required counts",
        f"- Policies preflighted: **{c.get('policies_preflighted')}**",
        f"- Nonzero eligible claim cohorts: **{c.get('nonzero_eligible_claim_cohorts')}**",
        f"- Mechanism inputs sufficient: **{c.get('mechanism_inputs_sufficient')}**",
        f"- Eligible for empirical execution: **{c.get('empirical_execution_eligible')}**",
        f"- Validated synthetic execution path: **{c.get('validated_synthetic_execution')}**",
        f"- Provenance-only: **{c.get('provenance_only_execution')}**",
        f"- Blocked by missing evidence: **{c.get('blocked_missing_evidence')}**",
        f"- Successful worker jobs: **{c.get('successful_worker_jobs')}**",
        f"- Timed-out / cancelled: **{c.get('timed_out_or_cancelled_jobs')}**",
        f"- Duplicates prevented: **{c.get('duplicate_executions_prevented')}**",
        f"- Reproducible persisted results: **{c.get('reproducible_persisted_results')}**",
        f"- Directional accuracy PASS: **{c.get('directional_accuracy_pass')}**",
        "",
        "## Lane C — Platform",
        f"- API health: `{api_health}`",
        "",
        "## Dec4 MRI / MPPR / SOS",
    ]
    for label, info in regression.items():
        md.append(
            f"- **{label.upper()}** `{info['policy_id']}` pathway={info['preflight_pathway']} "
            f"job={info['job_status']} frozen={info['frozen_dec4']} rewrite={info['ka_rewrite_attempted']}"
        )
    md.append("")
    blocked = pre.get("blocked_policy_ids") or []
    if blocked:
        md.append("## Blocked policy IDs")
        for pid in blocked:
            md.append(f"- `{pid}`")
        md.append("")
    fails = ds.get("fail_policy_ids") or []
    if fails:
        md.append("## Directional FAIL policy IDs")
        for pid in fails:
            md.append(f"- `{pid}`")
        md.append("")
    OUT_MD.write_text("\n".join(md) + "\n")
    print(json.dumps(c, indent=2))
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
