#!/usr/bin/env python3
"""Autonomous gate: verdicts + rollout ideas + one what-if per nine mock policies.

Refuses non-hfleanstg databases. Writes evidence JSON under docs/.../nine_mock_policies/.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import psycopg2
from psycopg2.extras import Json, RealDictCursor

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api" / "src"))
sys.path.insert(0, str(REPO / "packages" / "common" / "src"))
sys.path.insert(0, str(REPO / "apps" / "worker" / "src"))

API = "https://hfleanstg-api.whiteplant-64737337.eastus2.azurecontainerapps.io/api/v1"
TENANT = "00000000-0000-0000-0000-000000000001"
OUT = REPO / "docs/production/releases/corrections/nine_mock_policies/NINE_POLICY_AUTONOMOUS_GATE_REPORT.json"

NINE_NAMES = [
    "Outpatient MRI Prior Authorization",
    "National Coverage Determination Study — MRI (NCD 220.2)",
    "Local Coverage Determination Study — LCD L34425",
    "Medically Unlikely Edit (MUE) / Unit Cap",
    "Multiple Procedure Payment Reduction (MPPR)",
    "Procedure-to-Procedure (PTP) Coding Edit",
    "Outpatient Therapy Utilization and Payment Policy",
    "Infusion Site-of-Care and Reimbursement Policy",
    "Imaging Site-of-Service Policy",
]

SCENARIO_BY_KEY = {
    "mri": {
        "lever_adjustments": {},
        "elasticity_adjustments": {},
        "member_count_multiplier": 1.0,
        "utilization_trend": -0.05,
        "cost_inflation": 0.02,
        "projection_months": 12,
        "label": "UM elasticity scenario (−5% utilization trend, 12mo)",
    },
    "ncd": {"label": "Coverage study — financial effect UNESTIMATED", "projection_months": 12},
    "lcd": {"label": "Coverage study — financial effect UNESTIMATED", "projection_months": 12},
    "therapy": {"label": "Coverage/utilization study — financial effect UNESTIMATED unless payment engine", "projection_months": 12},
    "mue": {"base_mue_value": 4, "mue_value": 3, "label": "MUE threshold 4→3"},
    "mppr": {"base_secondary_pct": 0.5, "secondary_pct": 0.4, "label": "MPPR secondary 50%→40%"},
    "ptp": {"label": "PTP fixture modifier-indicator scenario"},
    "infusion": {"base_steer_hopd_count": 2, "steer_hopd_count": 3, "label": "Infusion steer HOPD 2→3"},
    "sos": {"base_hospital_pct": 0.80, "hospital_pct": 0.70, "label": "SOS hospital share 80%→70%"},
}


def _db_url() -> str:
    raw = subprocess.check_output(
        [
            "az",
            "keyvault",
            "secret",
            "show",
            "--vault-name",
            "hfleanstgkv",
            "--name",
            "lean-staging-database-url",
            "--query",
            "value",
            "-o",
            "tsv",
        ],
        text=True,
    ).strip()
    url = raw.replace("postgresql+psycopg2://", "postgresql://", 1)
    if "hfleanstg" not in url.lower():
        raise SystemExit("Refusing: not lean staging")
    return url


def _get(path: str) -> Any:
    with urllib.request.urlopen(API + path, timeout=180) as resp:
        return json.loads(resp.read().decode())


def _policy_key(meta: Dict[str, Any], name: str) -> str:
    k = meta.get("policy_key")
    if isinstance(k, str) and k:
        return k.lower()
    n = name.upper()
    if "MRI PRIOR" in n:
        return "mri"
    if "NCD" in n:
        return "ncd"
    if "LCD" in n:
        return "lcd"
    if "MUE" in n:
        return "mue"
    if "MPPR" in n:
        return "mppr"
    if "PTP" in n:
        return "ptp"
    if "THERAPY" in n:
        return "therapy"
    if "INFUSION" in n:
        return "infusion"
    if "SITE-OF-SERVICE" in n or "SITE OF SERVICE" in n:
        return "sos"
    return "mri"


def main() -> None:
    report: Dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "database": "hfleanstg",
        "api": API,
        "policies": [],
        "rollout_ideas": {},
        "whatifs": [],
    }
    url = _db_url()
    conn = psycopg2.connect(url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT id::text, name, policy_type, status, policy_metadata_json
        FROM policies
        WHERE tenant_id=%s::uuid AND name = ANY(%s)
        ORDER BY name
        """,
        (TENANT, NINE_NAMES),
    )
    policies = cur.fetchall()
    if len(policies) != 9:
        raise SystemExit(f"Expected 9 policies, found {len(policies)}")

    # --- Verdicts (API) ---
    verdicts = _get("/policy-verdicts?limit=500")
    v_items = {i["policy_id"]: i for i in (verdicts.get("items") or [])}
    for p in policies:
        v = v_items.get(p["id"], {})
        report["policies"].append(
            {
                "policy_id": p["id"],
                "name": p["name"],
                "policy_type": p["policy_type"],
                "policy_key": _policy_key(p["policy_metadata_json"] or {}, p["name"]),
                "verdict": v.get("verdict"),
                "verdict_label": v.get("verdict_label"),
                "savings_or_cost_impact_pmpm": v.get("savings_or_cost_impact_pmpm"),
                "utilization_impact_pct": v.get("utilization_impact_pct"),
                "confidence_pct": v.get("confidence_pct"),
                "verdict_reason": v.get("verdict_reason"),
                "recommendation": v.get("recommendation"),
                "has_backfire_risk": v.get("has_backfire_risk"),
            }
        )

    # --- Rollout ideas (API) ---
    roll = _get("/recommendations/policy-rollouts?months_lookback=12")
    recs = roll.get("recommendations") or []
    report["rollout_ideas"] = {
        "parameters": roll.get("parameters"),
        "existing_policies_count": roll.get("existing_policies_count"),
        "recommendation_count": len(recs),
        "methodology_footer": roll.get("methodology_footer"),
        "recommendations": [
            {
                "recommendation_id": r.get("recommendation_id"),
                "priority": r.get("priority"),
                "title": r.get("title"),
                "policy_type": r.get("policy_type"),
                "archetype_id": r.get("archetype_id"),
                "summary": r.get("summary"),
                "estimated_impact": r.get("estimated_impact"),
                "overlap_with_nine": _overlap_nine(r, policies),
            }
            for r in recs
        ],
        "note": (
            "Rollout recommender proposes net-new catalog archetypes after dedup vs in-force book. "
            "The nine mock policies are already in-force, so ideas are adjacent gaps (e.g. advanced imaging PA, infusion steerage), not duplicates of the nine."
        ),
    }

    # --- What-if: run locally against staging DB with fixed runner ---
    import os

    os.environ["DATABASE_URL"] = url
    # Ensure API settings pick up URL
    from uepi_api.database import SessionLocal
    from uepi_api.models.analysis import Analysis, AnalysisStatus, AnalysisConfig
    from uepi_api.services.whatif_runner import run_whatif_scenario_sync

    for p in policies:
        meta = p["policy_metadata_json"] or {}
        key = _policy_key(meta, p["name"])
        params = dict(SCENARIO_BY_KEY.get(key) or SCENARIO_BY_KEY["mri"])
        label = params.pop("label", key)
        print(f"What-if {p['name'][:48]} ({key})…", flush=True)
        db = SessionLocal()
        try:
            analysis = Analysis(
                tenant_id=TENANT,
                policy_id=p["id"],
                analysis_type="SIMULATE",
                status=AnalysisStatus.PENDING.value,
                created_by=None,
                name=f"Autonomous gate what-if — {p['name'][:80]}",
            )
            db.add(analysis)
            db.flush()
            try:
                db.add(
                    AnalysisConfig(
                        tenant_id=TENANT,
                        analysis_id=analysis.id,
                        treatment_filters={},
                        control_filters=None,
                        matching_strategy=None,
                        pre_window_months=0,
                        post_window_months=0,
                    )
                )
            except Exception as cfg_exc:
                print("  AnalysisConfig skipped:", cfg_exc, flush=True)
            db.commit()
            aid = str(analysis.id)
        except Exception as exc:
            db.rollback()
            aid = str(uuid4())
            cur2 = conn.cursor()
            cur2.execute(
                """
                INSERT INTO analyses (id, tenant_id, policy_id, analysis_type, status, name, created_at, updated_at)
                VALUES (%s::uuid, %s::uuid, %s::uuid, 'SIMULATE', 'PENDING', %s, now(), now())
                """,
                (aid, TENANT, p["id"], f"Autonomous gate what-if — {p['name'][:80]}"),
            )
            conn.commit()
            print("  ORM create failed, used SQL:", exc, flush=True)
        finally:
            db.close()

        result = run_whatif_scenario_sync(
            tenant_id=TENANT,
            analysis_id=aid,
            policy_id=p["id"],
            scenario_params=params,
            baseline_filters={},
        )
        entry = {
            "policy_id": p["id"],
            "policy_name": p["name"],
            "policy_key": key,
            "analysis_id": aid,
            "scenario_label": label,
            "scenario_params": params,
            "runner_status": result.get("status"),
            "message": result.get("message"),
            "strategy": result.get("strategy") or (result.get("result") or {}).get("strategy"),
            "impact_metrics": (result.get("result") or {}).get("impact_metrics"),
            "confidence_score": result.get("confidence_score"),
        }
        # Confirm DB status
        cur.execute(
            "SELECT status, error_message FROM analyses WHERE id=%s::uuid",
            (aid,),
        )
        row = cur.fetchone()
        entry["db_status"] = row["status"] if row else None
        entry["db_error"] = row["error_message"] if row else None
        report["whatifs"].append(entry)
        print(
            f"  -> {entry['runner_status']} db={entry['db_status']} impact_keys={list((entry.get('impact_metrics') or {}).keys())[:6]}",
            flush=True,
        )

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["summary"] = {
        "verdicts_on_track": sum(1 for p in report["policies"] if p.get("verdict") == "ON_TRACK"),
        "verdicts_backfire": sum(1 for p in report["policies"] if p.get("verdict") == "BACKFIRE"),
        "whatifs_completed": sum(1 for w in report["whatifs"] if w.get("db_status") == "COMPLETED" or w.get("runner_status") == "completed"),
        "whatifs_failed": sum(1 for w in report["whatifs"] if w.get("db_status") == "FAILED" or w.get("runner_status") == "error"),
        "rollout_recommendations": report["rollout_ideas"]["recommendation_count"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str))
    print("Wrote", OUT, flush=True)
    print(json.dumps(report["summary"], indent=2), flush=True)
    conn.close()


def _overlap_nine(rec: Dict[str, Any], policies: List[Dict[str, Any]]) -> List[str]:
    text = json.dumps(rec).lower()
    hits = []
    for p in policies:
        name = p["name"].lower()
        key = (p.get("policy_metadata_json") or {}).get("policy_key") or ""
        tokens = [t for t in [name.split("(")[0].strip()[:24], str(key)] if t]
        if any(t.lower() in text for t in tokens if len(t) >= 3):
            hits.append(p["name"])
    # keyword overlaps
    kw = {
        "mri": "Outpatient MRI Prior Authorization",
        "imaging": "Imaging Site-of-Service Policy",
        "infusion": "Infusion Site-of-Care and Reimbursement Policy",
        "mppr": "Multiple Procedure Payment Reduction (MPPR)",
        "mue": "Medically Unlikely Edit (MUE) / Unit Cap",
        "ptp": "Procedure-to-Procedure (PTP) Coding Edit",
        "therapy": "Outpatient Therapy Utilization and Payment Policy",
        "ncd": "National Coverage Determination Study — MRI (NCD 220.2)",
        "lcd": "Local Coverage Determination Study — LCD L34425",
    }
    for token, pname in kw.items():
        if token in text and pname not in hits:
            # only if recommendation is clearly same domain
            title = (rec.get("title") or "").lower()
            if token in title or token in (rec.get("archetype_id") or "").lower():
                hits.append(pname)
    return hits


if __name__ == "__main__":
    main()
