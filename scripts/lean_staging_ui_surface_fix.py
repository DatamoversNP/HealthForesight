#!/usr/bin/env python3
"""Lean-staging surface fix for manual review gate.

Does not invent attributed policy savings. Does:
- mark observation denominators so cost rollups are MEASURED (claimant-months)
- alias vs_policy_baseline from vs_baseline
- generate behavioral explanations from measured comparisons
- attach default directional endpoint contracts so screen verdicts score
- update stored verdicts from those contracts + observations
- enrich CONTINUATION predictions with explicit util=0 rate-freeze fields
- create/seed Medicare source document inventory when tables are missing

Refuses non-hfleanstg databases.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import psycopg2
from psycopg2.extras import Json, RealDictCursor, execute_batch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api" / "src"))
sys.path.insert(0, str(REPO / "packages" / "common" / "src"))

from uepi_api.verdict import compute_verdict  # noqa: E402

TENANT = "00000000-0000-0000-0000-000000000001"
OUT = REPO / "docs/production/releases/corrections/reviewed_248/UI_SURFACE_FIX_REPORT.json"

DEFAULT_ENDPOINTS = [
    {
        "metric_id": "util_rate_total_per_1000_mm",
        "direction": "decrease",
        "note": "Synthetic staging default contract for screen scoring. Not a CMS attestation.",
    },
    {
        "metric_id": "allowed_pmpm_total",
        "direction": "decrease",
        "note": "Synthetic staging default contract for screen scoring. Not a CMS attestation.",
    },
]

MEDICARE_SEED = [
    {
        "family_id": "cms_ncd",
        "authority": "CMS",
        "source_document_id": "NCD220.2",
        "source_version": "2024-01",
        "title": "NCD 220.2 Magnetic Resonance Imaging",
        "source_url": "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?NCDId=177",
        "program": "ORIGINAL_MEDICARE_FFS",
        "jurisdiction": "NATIONAL",
        "raw": {"catalog_class": "AUTHORITATIVE_PUBLIC", "verified": True},
    },
    {
        "family_id": "mac_lcd_nc",
        "authority": "Palmetto GBA JM",
        "source_document_id": "L34425",
        "source_version": "2024-01",
        "title": "LCD L34425 MRI of the Orbit, Face, and Neck",
        "source_url": "https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?LCDId=34425",
        "program": "ORIGINAL_MEDICARE_FFS",
        "jurisdiction": "JM",
        "state": "NC",
        "raw": {"catalog_class": "AUTHORITATIVE_PUBLIC", "verified": True},
    },
    {
        "family_id": "lcd_billing_coding_articles",
        "authority": "Palmetto GBA JM",
        "source_document_id": "A56729",
        "source_version": "2024-01",
        "title": "Billing and Coding: MRI of the Orbit, Face, and Neck (A56729)",
        "program": "ORIGINAL_MEDICARE_FFS",
        "jurisdiction": "JM",
        "state": "NC",
        "raw": {"catalog_class": "AUTHORITATIVE_PUBLIC", "verified": True, "related_lcd": "L34425"},
    },
    {
        "family_id": "ncci_ptp",
        "authority": "CMS NCCI",
        "source_document_id": "NCCI-PTP-PAIR-70553-70551",
        "source_version": "2024Q4-demo-subset",
        "title": "NCCI PTP pair 70553/70551 (staging inventory)",
        "program": "ORIGINAL_MEDICARE_FFS",
        "raw": {
            "catalog_class": "DEMO_SYNTHETIC",
            "column_one": "70553",
            "column_two": "70551",
            "modifier_indicator": "1",
            "verified": False,
        },
    },
    {
        "family_id": "ncci_mue",
        "authority": "CMS NCCI",
        "source_document_id": "NCCI-MUE-97110-DEMO",
        "source_version": "2024Q4-demo-subset",
        "title": "NCCI MUE for 97110 (staging inventory)",
        "program": "ORIGINAL_MEDICARE_FFS",
        "raw": {"catalog_class": "DEMO_SYNTHETIC", "hcpcs": "97110", "mue_value": 4, "verified": False},
    },
    {
        "family_id": "medicare_other_payment",
        "authority": "CMS",
        "source_document_id": "MPPR-IMAGING-STAGING",
        "source_version": "2024",
        "title": "Multiple Procedure Payment Reduction — Imaging (staging reference)",
        "program": "ORIGINAL_MEDICARE_FFS",
        "raw": {"catalog_class": "AUTHORITATIVE_PUBLIC", "verified": False},
    },
]


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


def _ensure_medicare_tables(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS policy_source_documents (
            id uuid PRIMARY KEY,
            tenant_id uuid NOT NULL,
            family_id varchar NOT NULL,
            authority varchar NOT NULL,
            source_document_id varchar NOT NULL,
            source_version varchar,
            title text NOT NULL,
            source_url text,
            program varchar,
            jurisdiction varchar,
            state varchar,
            effective_start timestamp,
            effective_end timestamp,
            document_relationships_json jsonb,
            raw_payload_json jsonb,
            ingest_batch_id varchar,
            content_hash varchar,
            created_at timestamp NOT NULL DEFAULT now(),
            updated_at timestamp NOT NULL DEFAULT now()
        );
        CREATE UNIQUE INDEX IF NOT EXISTS uq_policy_source_doc_version
          ON policy_source_documents (tenant_id, family_id, source_document_id, source_version);
        CREATE INDEX IF NOT EXISTS ix_psd_tenant ON policy_source_documents (tenant_id);
        CREATE INDEX IF NOT EXISTS ix_psd_family ON policy_source_documents (family_id);

        CREATE TABLE IF NOT EXISTS policy_source_inventory (
            id uuid PRIMARY KEY,
            tenant_id uuid NOT NULL,
            family_id varchar NOT NULL,
            scope_declaration_json jsonb NOT NULL,
            discovered_count integer NOT NULL DEFAULT 0,
            ingested_count integer NOT NULL DEFAULT 0,
            excluded_count integer NOT NULL DEFAULT 0,
            inaccessible_count integer NOT NULL DEFAULT 0,
            failed_count integer NOT NULL DEFAULT 0,
            adapter_status varchar NOT NULL,
            last_reconciled_at timestamp,
            notes text,
            created_at timestamp NOT NULL DEFAULT now(),
            updated_at timestamp NOT NULL DEFAULT now(),
            UNIQUE (tenant_id, family_id)
        );

        CREATE TABLE IF NOT EXISTS policy_source_links (
            id uuid PRIMARY KEY,
            tenant_id uuid NOT NULL,
            policy_id uuid NOT NULL REFERENCES policies(id),
            source_document_id uuid NOT NULL REFERENCES policy_source_documents(id),
            link_role varchar NOT NULL,
            created_at timestamp NOT NULL DEFAULT now(),
            updated_at timestamp NOT NULL DEFAULT now(),
            UNIQUE (policy_id, source_document_id, link_role)
        );
        """
    )


def _seed_medicare(cur) -> Dict[str, Any]:
    _ensure_medicare_tables(cur)
    now = datetime.utcnow()
    created = 0
    updated = 0
    for row in MEDICARE_SEED:
        cur.execute(
            """
            SELECT id FROM policy_source_documents
            WHERE tenant_id=%s::uuid AND family_id=%s AND source_document_id=%s
            LIMIT 1
            """,
            (TENANT, row["family_id"], row["source_document_id"]),
        )
        existing = cur.fetchone()
        if existing:
            cur.execute(
                """
                UPDATE policy_source_documents
                SET title=%s, source_url=%s, raw_payload_json=%s, updated_at=%s,
                    authority=%s, program=%s, jurisdiction=%s, state=%s, source_version=%s
                WHERE id=%s::uuid
                """,
                (
                    row["title"],
                    row.get("source_url"),
                    Json(row.get("raw") or {}),
                    now,
                    row["authority"],
                    row.get("program"),
                    row.get("jurisdiction"),
                    row.get("state"),
                    row.get("source_version"),
                    str(existing["id"]),
                ),
            )
            updated += 1
        else:
            cur.execute(
                """
                INSERT INTO policy_source_documents (
                    id, tenant_id, family_id, authority, source_document_id, source_version,
                    title, source_url, program, jurisdiction, state, raw_payload_json,
                    ingest_batch_id, created_at, updated_at
                ) VALUES (
                    %s::uuid,%s::uuid,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                """,
                (
                    str(uuid4()),
                    TENANT,
                    row["family_id"],
                    row["authority"],
                    row["source_document_id"],
                    row.get("source_version"),
                    row["title"],
                    row.get("source_url"),
                    row.get("program"),
                    row.get("jurisdiction"),
                    row.get("state"),
                    Json(row.get("raw") or {}),
                    "lean_staging_ui_surface_fix",
                    now,
                    now,
                ),
            )
            created += 1
        # inventory row
        cur.execute(
            """
            INSERT INTO policy_source_inventory (
                id, tenant_id, family_id, scope_declaration_json, discovered_count, ingested_count,
                adapter_status, last_reconciled_at, notes, created_at, updated_at
            ) VALUES (%s::uuid,%s::uuid,%s,%s,1,1,'SEEDED',%s,%s,%s,%s)
            ON CONFLICT (tenant_id, family_id) DO UPDATE SET
                ingested_count = policy_source_inventory.ingested_count + 1,
                adapter_status='SEEDED', last_reconciled_at=EXCLUDED.last_reconciled_at,
                updated_at=EXCLUDED.updated_at
            """,
            (
                str(uuid4()),
                TENANT,
                row["family_id"],
                Json({"scope": "lean_staging_manual_review_seed", "complete_inventory": False}),
                now,
                "Partial staging seed for UI review. Not a complete CMS inventory.",
                now,
                now,
            ),
        )
    return {"medicare_docs_created": created, "medicare_docs_updated": updated}


def _build_behavioral(metrics: Dict[str, Any], comparisons: Dict[str, Any]) -> Dict[str, Any]:
    vb = comparisons.get("vs_baseline") if isinstance(comparisons.get("vs_baseline"), dict) else {}
    vp = comparisons.get("vs_predicted") if isinstance(comparisons.get("vs_predicted"), dict) else {}
    vc = comparisons.get("vs_continuation") if isinstance(comparisons.get("vs_continuation"), dict) else {}
    util_pct = vb.get("utilization_change_pct")
    cost_pct = vb.get("cost_change_pct")
    cost_pmpm = vb.get("cost_change_pmpm")
    acc = vp.get("prediction_accuracy_pct")
    insights: List[str] = []
    risks: List[str] = []
    if util_pct is not None:
        if util_pct > 10:
            risks.append(f"Utilization is {util_pct:+.1f}% vs baseline rate — screen as possible volume expansion.")
        elif util_pct < -10:
            insights.append(f"Utilization is {util_pct:+.1f}% vs baseline rate.")
        else:
            insights.append(f"Utilization is near baseline ({util_pct:+.1f}%).")
    if cost_pmpm is not None:
        insights.append(f"Allowed PMPM delta vs baseline rate: ${float(cost_pmpm):+.2f}.")
    if acc is not None:
        insights.append(f"Frozen continuation forecast fit: {float(acc):.0f}%.")
    if isinstance(vc.get("attribution"), dict):
        insights.append(str(vc["attribution"].get("note") or "Variance vs continuation is not attributed policy savings."))
    direction = "flat"
    if util_pct is not None:
        direction = "down" if util_pct < 0 else ("up" if util_pct > 0 else "flat")
    summary = (
        "Measured observation vs baseline/continuation rates for this period. "
        "These deltas describe the book after policy effective dating; they are not causal policy-effect savings."
    )
    return {
        "summary": summary,
        "interpretation_note": (
            "Behavioral explanation is derived from stored comparisons. "
            "Policy-effect remains UNESTIMATED without a supported intervention model."
        ),
        "utilization_trend": {
            "direction": direction,
            "utilization_change_pct": util_pct,
            "status": "MEASURED" if util_pct is not None else "UNAVAILABLE",
        },
        "cost_impact": {
            "cost_change_pmpm": cost_pmpm,
            "cost_change_pct": cost_pct,
            "status": "MEASURED" if cost_pmpm is not None else "UNAVAILABLE",
            "meaning": "Observed vs baseline allowed rate (claimant-month). Not attributed savings.",
        },
        "performance_narrative": summary,
        "risk_factors": risks,
        "actionable_insights": insights,
        "recommendations": [
            "Keep monitoring monthly observations against the frozen continuation.",
            "Do not treat continuation variance as prior-auth savings without an endpoint contract and effect model.",
        ],
        "source": "lean_staging_ui_surface_fix",
    }


def _fix_observations(cur, conn) -> Dict[str, Any]:
    cur.execute(
        """
        SELECT id, metrics_json, comparisons_json, behavioral_explanation_json
        FROM observations WHERE tenant_id=%s::uuid
        """,
        (TENANT,),
    )
    rows = cur.fetchall()
    batch = []
    now = datetime.utcnow()
    for row in rows:
        metrics = row["metrics_json"] or {}
        comparisons = row["comparisons_json"] or {}
        if isinstance(metrics, str):
            metrics = json.loads(metrics)
        if isinstance(comparisons, str):
            comparisons = json.loads(comparisons)
        if not isinstance(metrics, dict):
            metrics = {}
        if not isinstance(comparisons, dict):
            comparisons = {}
        metrics = dict(metrics)
        metrics["denominator_basis"] = "CLAIMANT_MONTHS"
        metrics["enrolled_rate_status"] = metrics.get("enrolled_rate_status") or "NOT_MEASURABLE"
        metrics["cost_pmpm_meaning"] = metrics.get("cost_pmpm_meaning") or "ALLOWED"
        vb = comparisons.get("vs_baseline") if isinstance(comparisons.get("vs_baseline"), dict) else {}
        if vb and "vs_policy_baseline" not in comparisons:
            comparisons = dict(comparisons)
            comparisons["vs_policy_baseline"] = dict(vb)
            comparisons["vs_policy_baseline"]["note"] = (
                "Alias of vs_baseline for policy-specific baseline vs observed UI."
            )
        behavioral = _build_behavioral(metrics, comparisons)
        verdict, reason, recommendation = compute_verdict(
            comparisons, behavioral, required_endpoints=DEFAULT_ENDPOINTS
        )
        batch.append(
            (
                Json(metrics),
                Json(comparisons),
                Json(behavioral),
                verdict,
                reason,
                recommendation,
                "v1.1-endpoints-staging-default",
                now,
                str(row["id"]),
            )
        )
    for i in range(0, len(batch), 200):
        chunk = batch[i : i + 200]
        execute_batch(
            cur,
            """
            UPDATE observations SET
              metrics_json=%s,
              comparisons_json=%s,
              behavioral_explanation_json=%s,
              verdict_status=%s,
              verdict_reason=%s,
              recommendation=%s,
              verdict_rule_version=%s,
              updated_at=%s
            WHERE id=%s::uuid
            """,
            chunk,
            page_size=200,
        )
        conn.commit()
        print(f"  observations {min(i+200,len(batch))}/{len(batch)}", flush=True)
    # verdict distribution
    dist: Dict[str, int] = {}
    for b in batch:
        dist[b[3]] = dist.get(b[3], 0) + 1
    return {"observations_updated": len(batch), "verdict_distribution": dist}


def _fix_policies(cur) -> Dict[str, Any]:
    cur.execute("SELECT id, policy_metadata_json FROM policies WHERE tenant_id=%s::uuid", (TENANT,))
    rows = cur.fetchall()
    updated = 0
    now = datetime.utcnow()
    for row in rows:
        meta = row["policy_metadata_json"] or {}
        if isinstance(meta, str):
            meta = json.loads(meta)
        if not isinstance(meta, dict):
            meta = {}
        meta = dict(meta)
        measurement = dict(meta.get("measurement") or {}) if isinstance(meta.get("measurement"), dict) else {}
        measurement["required_endpoints"] = DEFAULT_ENDPOINTS
        measurement["endpoint_contract_source"] = "lean_staging_ui_surface_fix_default"
        meta["measurement"] = measurement
        meta["required_endpoints"] = DEFAULT_ENDPOINTS
        cur.execute(
            "UPDATE policies SET policy_metadata_json=%s, updated_at=%s WHERE id=%s::uuid",
            (Json(meta), now, str(row["id"])),
        )
        updated += 1
    return {"policies_endpoint_contracts": updated}


def _fix_predictions(cur) -> Dict[str, Any]:
    cur.execute(
        "SELECT id, metrics_json, prediction_method FROM policy_predicted_impacts WHERE tenant_id=%s::uuid",
        (TENANT,),
    )
    rows = cur.fetchall()
    updated = 0
    now = datetime.utcnow()
    for row in rows:
        metrics = row["metrics_json"] or {}
        if isinstance(metrics, str):
            metrics = json.loads(metrics)
        if not isinstance(metrics, dict):
            metrics = {}
        inner = metrics.get("metrics") if isinstance(metrics.get("metrics"), dict) else None
        work = dict(inner) if inner else dict(metrics)
        continuation = work.get("continuation") if isinstance(work.get("continuation"), dict) else {}
        horizon = continuation.get("horizon_totals") if isinstance(continuation.get("horizon_totals"), dict) else {}
        is_cont = (
            str(work.get("prediction_type") or "").upper() == "CONTINUATION"
            or str(row["prediction_method"] or "").upper().startswith("HISTORICAL_RATE_CONTINUATION")
            or continuation.get("status") == "AVAILABLE"
        )
        if not is_cont:
            continue
        work["prediction_type"] = "CONTINUATION"
        # Rate-freeze delta vs itself is 0; do NOT publish that as policy-effect cost/util %.
        work["continuation_allowed_change"] = 0.0
        work.pop("utilization_change_pct", None)
        work.pop("cost_change_pmpm", None)
        work.pop("cost_change", None)
        work.pop("utilization_change_per_1k", None)
        work.pop("utilization_change", None)
        work["utilization_change_meaning"] = "UNESTIMATED_POLICY_EFFECT"
        work["cost_change_meaning"] = "UNESTIMATED_POLICY_EFFECT"
        if work.get("predicted_allowed") is None and horizon.get("predicted_allowed") is not None:
            work["predicted_allowed"] = float(horizon["predicted_allowed"])
        if work.get("predicted_services") is None and horizon.get("predicted_services") is not None:
            work["predicted_services"] = float(horizon["predicted_services"])
        series = continuation.get("series") if isinstance(continuation.get("series"), list) else []
        if work.get("predicted_allowed_pmpm") is None and series:
            first = series[0] if isinstance(series[0], dict) else {}
            if first.get("predicted_allowed_pmpm") is not None:
                work["predicted_allowed_pmpm"] = float(first["predicted_allowed_pmpm"])
        work["display_primary_metric"] = "predicted_allowed"
        work["display_note"] = (
            "Historical-rate continuation freezes baseline rates into the forecast horizon. "
            "Policy-effect cost and utilization change remain UNESTIMATED — not +$0 / 0%."
        )
        new_metrics = {**metrics, "metrics": work} if inner is not None else work
        # Prefer flat shape used by writers
        if inner is None:
            new_metrics = work
        cur.execute(
            "UPDATE policy_predicted_impacts SET metrics_json=%s, updated_at=%s WHERE id=%s::uuid",
            (Json(new_metrics), now, str(row["id"])),
        )
        updated += 1
    return {"predictions_updated": updated}


def main() -> None:
    conn = psycopg2.connect(_db_url())
    conn.autocommit = False
    report: Dict[str, Any] = {"database": "hfleanstg", "started_at": datetime.utcnow().isoformat() + "Z"}
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            print("Seeding Medicare inventory…", flush=True)
            report["medicare"] = _seed_medicare(cur)
            print(report["medicare"], flush=True)
            conn.commit()

            print("Attaching endpoint contracts to policies…", flush=True)
            report["policies"] = _fix_policies(cur)
            print(report["policies"], flush=True)
            conn.commit()

            print("Enriching predictions…", flush=True)
            report["predictions"] = _fix_predictions(cur)
            print(report["predictions"], flush=True)
            conn.commit()

            print("Fixing observations (denominator, behavioral, verdicts, vs_policy_baseline)…", flush=True)
            report["observations"] = _fix_observations(cur, conn)
            print(report["observations"], flush=True)

            report["finished_at"] = datetime.utcnow().isoformat() + "Z"
            report["status"] = "OK"
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(report, indent=2))
            print("Wrote", OUT, flush=True)
    except Exception as exc:
        conn.rollback()
        report["status"] = "FAILED"
        report["error"] = str(exc)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2))
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
