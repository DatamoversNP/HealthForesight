#!/usr/bin/env python3
"""
Close the 140-policy lifecycle gap on lean staging.

Assigns domain-plausible CANDIDATE codes (not certified), adds matching synthetic
claims into SYNTHETIC_REVIEWED_248_V1, reconfigures policies, and runs
baseline → continuation → observations → what-if for each.

Does not use the rejected office-E/M dump as the intended clinical codeset when a
name/family schedule exists. Remap state remains CANDIDATE_DOMAIN_REMAP_UNVERIFIED.
"""
from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import psycopg2
from psycopg2.extras import Json, RealDictCursor, execute_batch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "packages" / "common" / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from uepi_common.synthetic_payer.reviewed_248_book import (  # noqa: E402
    POST_END,
    POST_START,
    PRE_END,
    PRE_START,
    SOURCE_SYSTEM,
    _money,
    _month_span,
    _months,
)
from uepi_common.synthetic_payer.reviewed_248_candidate_remap import remap_candidate  # noqa: E402
from lean_staging_reviewed_248_batch import (  # noqa: E402
    TENANT,
    _book_mm,
    _configure_policy,
    _db_url,
    _run_lifecycle_for_measurable,
    _validate_alignment,
)

MANIFEST_PATH = REPO / "docs/production/releases/corrections/reviewed_248/REVIEWED_248_MANIFEST.json"
OUT = REPO / "docs/production/releases/corrections/reviewed_248/GAP_CLOSURE_140_REPORT.json"
SEED = 20261107 + 140


def _generate_claims_for_specs(specs: List[Dict[str, Any]], member_ids: List[str]) -> List[Dict[str, Any]]:
    rng = np.random.default_rng(SEED)
    months = _months(PRE_START, POST_END)
    n_members = len(member_ids)
    claims: List[Dict[str, Any]] = []
    line_id = 0
    for month in months:
        m_start, m_end_excl = _month_span(month)
        period = "PRE" if month.year == 2025 else "POST"
        for spec in specs:
            codes = list(spec["candidate_codes"])
            cat = spec.get("service_category") or "general"
            bands = spec.get("allowed_bands") or {}
            n_events = max(10, int(n_members * 0.012))
            for _ in range(n_events):
                mid = member_ids[int(rng.integers(0, n_members))]
                code = str(rng.choice(codes))
                band = bands.get(code) or (100.0, 900.0)
                svc = m_start + timedelta(days=int(rng.integers(0, max((m_end_excl - m_start).days, 1))))
                allowed = float(rng.uniform(*band))
                paid, share = _money(allowed)
                is_hcpcs = bool(code and code[0].isalpha())
                line_id += 1
                claims.append(
                    {
                        "claim_id": f"R248G_{spec['register_index']:03d}_{line_id:08d}",
                        "claim_line_id": f"R248G_{spec['register_index']:03d}_{line_id:08d}_1",
                        "member_id": mid,
                        "provider_id": f"R248_PRV_{(line_id % 40):04d}",
                        "service_date": svc,
                        "cpt_code": None if is_hcpcs else code,
                        "hcpcs_code": code if is_hcpcs else None,
                        "service_category": cat,
                        "allowed_amount": round(allowed, 2),
                        "paid_amount": paid,
                        "member_cost_share": share,
                        "units": float(rng.integers(1, 4)),
                        "lob": "COMMERCIAL",
                        "market": "SYNTHETIC",
                        "place_of_service": "22" if cat in {"imaging", "surgery", "ambulance", "infusion"} else "11",
                        "in_network": True,
                        "requires_prior_auth": "PRIOR_AUTH" in str(spec.get("policy_type") or "").upper(),
                        "facility_type": "HOPD" if cat in {"imaging", "surgery"} else "OFFICE",
                        "record_hash": json.dumps(
                            {
                                "line_status": "ACTIVE",
                                "policy_key": f"r248g_{spec['register_index']}",
                                "period": period,
                                "candidate": True,
                                "remap": True,
                            }
                        ),
                    }
                )
    return claims


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text())
    gap = [p for p in manifest["policies"] if p.get("decision") != "CANDIDATE_MEASURE"]
    remapped: List[Dict[str, Any]] = []
    for p in gap:
        r = remap_candidate(p)
        assert r is not None
        merged = {**p, **r, "exported_codes_raw": p.get("exported_codes_raw") or []}
        remapped.append(merged)

    # Update manifest decisions
    by_idx = {p["register_index"]: p for p in remapped}
    for p in manifest["policies"]:
        if p["register_index"] in by_idx:
            p.update(
                {
                    "candidate_codes": by_idx[p["register_index"]]["candidate_codes"],
                    "service_category": by_idx[p["register_index"]]["service_category"],
                    "allowed_bands": by_idx[p["register_index"]]["allowed_bands"],
                    "decision": "CANDIDATE_MEASURE",
                    "remap_method": by_idx[p["register_index"]]["remap_method"],
                    "remap_keyword": by_idx[p["register_index"]].get("remap_keyword"),
                    "code_mapping_state": by_idx[p["register_index"]]["code_mapping_state"],
                    "gap_closed": True,
                }
            )
    manifest["summary"]["candidate_measure"] = sum(
        1 for p in manifest["policies"] if p["decision"] == "CANDIDATE_MEASURE"
    )
    manifest["summary"]["config_only_bad_export"] = 0
    manifest["summary"]["config_only_no_codes"] = 0
    manifest["summary"]["gap_closed"] = len(remapped)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))

    report: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gap_policies": len(remapped),
        "remap_methods": {},
        "population": {},
        "policies": [],
        "validation_summary": {},
    }
    from collections import Counter

    report["remap_methods"] = dict(Counter(p["remap_method"] for p in remapped))

    conn = psycopg2.connect(_db_url())
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Existing R248 members
        cur.execute(
            """
            SELECT DISTINCT member_id FROM enrollment_records
            WHERE tenant_id=%s::uuid AND source_system=%s
            ORDER BY member_id
            """,
            (TENANT, SOURCE_SYSTEM),
        )
        member_ids = [r["member_id"] for r in cur.fetchall()]
        if len(member_ids) < 5000:
            raise SystemExit(f"Expected R248 population loaded; found {len(member_ids)} members")

        # Idempotent: remove prior gap-closure claims only
        cur.execute(
            "DELETE FROM claims_lines WHERE source_system=%s AND claim_id LIKE 'R248G_%%'",
            (SOURCE_SYSTEM,),
        )
        deleted = cur.rowcount
        print(f"cleared prior gap claims={deleted}", flush=True)

        print(f"Generating claims for {len(remapped)} remapped policies…", flush=True)
        claims = _generate_claims_for_specs(remapped, member_ids)
        print(f"Inserting {len(claims)} claim lines…", flush=True)
        ingestion_id = str(uuid.uuid4())
        source_file = f"reviewed-248-gap-{SEED}"
        claim_sql = """
            INSERT INTO claims_lines (
                id, tenant_id, claim_id, claim_line_id, member_id, provider_id,
                service_date, paid_date, adjudication_date, lob, market,
                cpt_code, hcpcs_code, service_category, place_of_service, units,
                allowed_amount, paid_amount, member_cost_share, in_network,
                requires_prior_auth, prior_auth_approved, facility_type,
                source_system, source_file_id, ingestion_id, record_hash,
                created_at, updated_at
            ) VALUES (
                %s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,
                %s,%s,%s,
                %s,%s,%s,%s,
                NOW(), NOW()
            )
        """
        rows = []
        for c in claims:
            rows.append(
                (
                    str(uuid.uuid4()),
                    TENANT,
                    c["claim_id"],
                    c["claim_line_id"],
                    c["member_id"],
                    c["provider_id"],
                    c["service_date"],
                    c["service_date"],
                    c["service_date"],
                    c["lob"],
                    c["market"],
                    c.get("cpt_code"),
                    c.get("hcpcs_code"),
                    c["service_category"],
                    c["place_of_service"],
                    c["units"],
                    c["allowed_amount"],
                    c["paid_amount"],
                    c["member_cost_share"],
                    True,
                    bool(c.get("requires_prior_auth")),
                    None,
                    c.get("facility_type"),
                    SOURCE_SYSTEM,
                    source_file,
                    ingestion_id,
                    c.get("record_hash"),
                )
            )
        for offset in range(0, len(rows), 5000):
            execute_batch(cur, claim_sql, rows[offset : offset + 5000], page_size=500)
            print(f"  claims {min(offset+5000, len(rows))}/{len(rows)}", flush=True)
        conn.commit()
        book_mm = _book_mm(cur, PRE_START, PRE_END)
        report["population"] = {
            "members": len(member_ids),
            "gap_claims_added": len(rows),
            "book_mm_2025": book_mm,
            "source_system": SOURCE_SYSTEM,
        }

        completed = 0
        thin = 0
        failed = 0
        for i, spec in enumerate(remapped, 1):
            print(
                f"GAP {i}/{len(remapped)} · #{spec['register_index']} {spec['name']} "
                f"[{spec['remap_method']}:{spec.get('remap_keyword')}] codes={spec['candidate_codes']}",
                flush=True,
            )
            item: Dict[str, Any] = {
                "register_index": spec["register_index"],
                "name": spec["name"],
                "remap_method": spec["remap_method"],
                "candidate_codes": spec["candidate_codes"],
            }
            try:
                _configure_policy(cur, spec)
                # stamp remap provenance on metadata
                cur.execute(
                    """
                    UPDATE policies SET policy_metadata_json =
                      policy_metadata_json || %s::jsonb, updated_at=NOW()
                    WHERE id=%s::uuid AND tenant_id=%s::uuid
                    """,
                    (
                        json.dumps(
                            {
                                "gap_closed": True,
                                "remap_method": spec["remap_method"],
                                "remap_keyword": spec.get("remap_keyword"),
                                "code_mapping_state": spec.get("code_mapping_state"),
                            }
                        ),
                        spec["policy_id"],
                        TENANT,
                    ),
                )
                conn.commit()
                validation = _validate_alignment(cur, spec, book_mm)
                item["validation"] = validation
                # clear prior lifecycle for this policy r248*
                cur.execute(
                    "DELETE FROM observations WHERE tenant_id=%s::uuid AND policy_id=%s::uuid AND observation_id LIKE 'r248-%%'",
                    (TENANT, spec["policy_id"]),
                )
                cur.execute(
                    """
                    DELETE FROM whatif_scenario_results WHERE tenant_id=%s::uuid AND analysis_id IN (
                      SELECT id FROM analyses WHERE tenant_id=%s::uuid AND policy_id=%s::uuid
                        AND name LIKE 'R248 continuation What-If%%'
                    )
                    """,
                    (TENANT, TENANT, spec["policy_id"]),
                )
                cur.execute(
                    "DELETE FROM analyses WHERE tenant_id=%s::uuid AND policy_id=%s::uuid AND name LIKE 'R248 continuation What-If%%'",
                    (TENANT, spec["policy_id"]),
                )
                # also clear older predictions linked to prior empty baselines? keep versions; new baseline version++
                if validation.get("status") in {"ALIGNED", "THIN"}:
                    item["lifecycle"] = _run_lifecycle_for_measurable(cur, spec, validation)
                    conn.commit()
                    completed += 1
                    if validation.get("status") == "THIN":
                        thin += 1
                else:
                    item["lifecycle"] = {"status": "SKIPPED", "validation": validation}
                    conn.commit()
                    failed += 1
            except Exception as e:
                conn.rollback()
                item["error"] = str(e)
                failed += 1
                print("  ERROR", e, flush=True)
            report["policies"].append(item)

        report["validation_summary"] = {
            "gap_policies": len(remapped),
            "lifecycle_completed": completed,
            "thin": thin,
            "failed_or_skipped": failed,
            "pass": completed == len(remapped) and failed == 0,
        }
    finally:
        cur.close()
        conn.close()

    OUT.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report["validation_summary"], indent=2))
    print("Wrote", OUT)
    return 0 if report["validation_summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
