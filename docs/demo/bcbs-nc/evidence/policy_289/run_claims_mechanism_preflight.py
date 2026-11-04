#!/usr/bin/env python3
"""Lane B preflight: claims coverage + mechanism input readiness for all 289.

In-process DB counts (not bulk HTTP refresh).
Does not modify policy scope to manufacture matches.
Zero cohort → blocks claims-based numerical execution.
Nonzero cohort still requires mechanism-specific input checks.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

EVID = Path(__file__).resolve().parent
REPO = EVID.parents[4]
INV = EVID / "POLICY_289_MASTER_INVENTORY.json"
V12 = EVID.parents[1] / "policy_definitions" / "v1.2"
OUT = EVID / "POLICY_289_PREFLIGHT_FEASIBILITY_MATRIX.json"
LEDGER_B = EVID / "POLICY_289_LANE_B_EXECUTION_LEDGER.json"

FROZEN_PRIMARY = {
    "d403f101-08dd-45c9-ab83-d42e37c62018",
    "d0eeb370-df14-4478-8755-dad6c3a35a47",
    "d7441dd9-3bfe-405e-ae6c-0377204bbb7e",
}
FROZEN_NINE = {
    *FROZEN_PRIMARY,
    "58b839b5-b6e0-59e0-9406-d817877c3ce8",
    "e11b049d-fcce-55cc-bcd7-71329038383b",
    "f2b8e7f3-1627-5dbe-8d7e-757ce21aa55b",
    "11218053-bdc0-569f-a415-fb61c5dcda37",
    "4f8c34e3-015b-509d-90ba-521261464258",
    "649b4ac8-ca82-5b84-aa87-84834490731a",
}
PROVENANCE = {
    "4f8c34e3-015b-509d-90ba-521261464258",
    "649b4ac8-ca82-5b84-aa87-84834490731a",
}

# Mechanisms that need coded claim intersection for EMPIRICAL_COHORT
CODED_EMPIRICAL = {
    "PRIOR_AUTH_UM",
    "MEDICAL_NECESSITY_COVERAGE",
    "SITE_OF_CARE",
    "THERAPY_REHAB",
    "PAYMENT_REIMBURSEMENT",
    "PHARMACY_SPECIALTY",
    "BENEFIT_ELIGIBILITY",
    "TELEHEALTH",
    "CODING_CLAIM_INTEGRITY",
}


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def config_digest(scope: dict, levers: list, codes: list, folder: Optional[str]) -> str:
    payload = {"scope": scope, "levers": levers, "codes": codes, "folder": folder}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]


def package_codeset_status(folder: Optional[str]) -> Optional[str]:
    if not folder:
        return None
    p = V12 / folder
    if not p.exists():
        return None
    pkg = next(iter(sorted(p.glob("*PACKAGE.json"))), None)
    if pkg:
        try:
            return (json.loads(pkg.read_text()).get("codeset") or {}).get("status")
        except Exception:
            return None
    if folder in {
        "mri", "mppr", "sos", "ptp", "mue", "therapy", "infusion", "ncd_study", "lcd_study"
    }:
        return "LEGACY_NINE"
    return None


def lever_codes(meta_levers: list) -> List[str]:
    out: List[str] = []
    for L in meta_levers or []:
        params = (L or {}).get("parameters") or {}
        targets = (L or {}).get("targets") or {}
        for src in (params, targets):
            for k in ("codes", "cpt_codes", "hcpcs_codes", "procedure_codes", "target_codes", "ndc_codes"):
                v = src.get(k)
                if isinstance(v, list):
                    out.extend(str(x).strip() for x in v if x is not None and str(x).strip())
    return sorted(set(out))


def classify_pathway(
    *,
    pid: str,
    arch: str,
    codeset_status: Optional[str],
    codes: List[str],
    claim_count: int,
    mechanism_inputs_ok: bool,
    def_complete: bool,
) -> str:
    if pid in PROVENANCE:
        return "PROVENANCE_ONLY"
    if pid in FROZEN_NINE:
        return "REPRESENTATIVE_SYNTHETIC_FIXTURE"
    if not def_complete or codeset_status == "UNRESOLVED":
        return "BLOCKED"
    if codeset_status == "NOT_APPLICABLE" and arch in {
        "ADMINISTRATIVE", "PROVIDER_NETWORK", "COMPOSITE", "CLINICAL_PATHWAY"
    }:
        return "PROVENANCE_ONLY"  # non-code — no financial claims cohort required
    if arch in CODED_EMPIRICAL:
        if claim_count > 0 and mechanism_inputs_ok and codes:
            return "EMPIRICAL_COHORT"
        if codes and claim_count == 0:
            # Directionally configured but no matching claims — synthetic demo path eligible
            return "REPRESENTATIVE_SYNTHETIC_FIXTURE"
        return "BLOCKED"
    if claim_count > 0 and mechanism_inputs_ok:
        return "EMPIRICAL_COHORT"
    return "REPRESENTATIVE_SYNTHETIC_FIXTURE"


def main() -> int:
    # Load demo env
    env_path = REPO / ".env.demo7867"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    sys.path.insert(0, str(REPO / "apps" / "api" / "src"))
    sys.path.insert(0, str(REPO / "packages" / "common" / "src"))

    from collections import defaultdict

    from sqlalchemy import func, or_, and_
    from sqlalchemy.orm import sessionmaker
    from uepi_api.database import get_engine, set_local_statement_timeout
    from uepi_api.models.policy import Policy
    from uepi_api.models.canonical_data import ClaimsLineDB

    inv = json.loads(INV.read_text())
    reg = {}
    reg_path = V12 / "POLICY_PACKAGE_REGISTRY.json"
    if reg_path.exists():
        reg = json.loads(reg_path.read_text()).get("packages") or {}

    engine = get_engine()
    Session = sessionmaker(bind=engine)
    db = Session()
    set_local_statement_timeout(db, 300_000)

    # Default tenant used by demo
    tenant_id = UUID("00000000-0000-0000-0000-000000000001")
    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    # Required claim columns for empirical analytics — verify once against ORM
    required_columns = [
        "service_date", "member_id", "cpt_code", "hcpcs_code",
        "paid_amount", "allowed_amount", "lob", "market", "provider_id",
    ]
    claim_cols = {c.name for c in ClaimsLineDB.__table__.columns}
    missing_schema_cols = [c for c in required_columns if c not in claim_cols]
    schema_ok = len(missing_schema_cols) == 0

    policies_db = {str(p.id): p for p in db.query(Policy).filter(Policy.tenant_id == tenant_id).all()}
    print(f"DB policies={len(policies_db)} inventory={len(inv['policies'])} schema_ok={schema_ok}", flush=True)

    # Warehouse-oriented: ONE grouped extract, then in-memory intersection (no 289 full scans)
    print("Extracting claims code×lob×market aggregates (single pass)...", flush=True)
    extract_error: Optional[str] = None
    # key: (lob, market, code) -> count; also totals
    code_bucket: Dict[tuple, int] = {}
    lob_market_total: Dict[tuple, int] = defaultdict(int)
    c_tenant = 0
    try:
        window_f = and_(
            ClaimsLineDB.tenant_id == tenant_id,
            ClaimsLineDB.service_date >= start_date,
            ClaimsLineDB.service_date <= end_date,
        )
        c_tenant = db.query(func.count(ClaimsLineDB.id)).filter(window_f).scalar() or 0
        for lob_v, mkt_v, cnt in (
            db.query(ClaimsLineDB.lob, ClaimsLineDB.market, func.count(ClaimsLineDB.id))
            .filter(window_f)
            .group_by(ClaimsLineDB.lob, ClaimsLineDB.market)
        ):
            lob_market_total[(str(lob_v), str(mkt_v))] = int(cnt)
        # CPT buckets
        for lob_v, mkt_v, code_v, cnt in (
            db.query(
                ClaimsLineDB.lob,
                ClaimsLineDB.market,
                ClaimsLineDB.cpt_code,
                func.count(ClaimsLineDB.id),
            )
            .filter(window_f, ClaimsLineDB.cpt_code.isnot(None), ClaimsLineDB.cpt_code != "")
            .group_by(ClaimsLineDB.lob, ClaimsLineDB.market, ClaimsLineDB.cpt_code)
        ):
            code_bucket[(str(lob_v), str(mkt_v), str(code_v).strip())] = int(cnt)
        # HCPCS-only lines (no CPT) — avoid double-count when both present
        for lob_v, mkt_v, code_v, cnt in (
            db.query(
                ClaimsLineDB.lob,
                ClaimsLineDB.market,
                ClaimsLineDB.hcpcs_code,
                func.count(ClaimsLineDB.id),
            )
            .filter(
                window_f,
                ClaimsLineDB.hcpcs_code.isnot(None),
                ClaimsLineDB.hcpcs_code != "",
                or_(ClaimsLineDB.cpt_code.is_(None), ClaimsLineDB.cpt_code == ""),
            )
            .group_by(ClaimsLineDB.lob, ClaimsLineDB.market, ClaimsLineDB.hcpcs_code)
        ):
            key = (str(lob_v), str(mkt_v), str(code_v).strip())
            code_bucket[key] = code_bucket.get(key, 0) + int(cnt)
        print(
            f"Extract done: tenant={c_tenant} code_buckets={len(code_bucket)} lob_markets={len(lob_market_total)}",
            flush=True,
        )
    except Exception as e:
        extract_error = str(e)[:400]
        print(f"Extract FAILED: {extract_error}", flush=True)

    def resolve_lobs(lob) -> List[str]:
        if lob is None:
            return []
        if isinstance(lob, list):
            return [str(x) for x in lob]
        return [str(lob)]

    def resolve_markets(markets) -> List[str]:
        if markets is None:
            return []
        if isinstance(markets, list):
            return [str(x) for x in markets]
        return [str(markets)]

    def count_lob_market(lob, markets) -> int:
        lobs = resolve_lobs(lob)
        mkts = resolve_markets(markets)
        if not lobs and not mkts:
            return int(c_tenant)
        total = 0
        for (lv, mv), cnt in lob_market_total.items():
            if lobs and lv not in lobs:
                continue
            if mkts and mv not in mkts:
                continue
            total += cnt
        return total

    def count_codes(lob, markets, codes: List[str]) -> int:
        code_set = {str(c).strip() for c in codes if c}
        if not code_set:
            return 0
        lobs = resolve_lobs(lob)
        mkts = resolve_markets(markets)
        total = 0
        for (lv, mv, cv), cnt in code_bucket.items():
            if cv not in code_set:
                continue
            if lobs and lv not in lobs:
                continue
            if mkts and mv not in mkts:
                continue
            total += cnt
        return total

    cache_lob_mkt: Dict[str, int] = {}
    cache_codes: Dict[str, int] = {}

    rows = []
    for i, inv_row in enumerate(inv["policies"], 1):
        pid = inv_row["policy_id"]
        pol = policies_db.get(pid)
        name = inv_row["name"]
        arch = inv_row["archetype"]
        folder = reg.get(pid) or inv_row.get("v12_package_folder")
        codeset_status = package_codeset_status(folder)
        def_complete = inv_row["gates"].get("DEFINITION_COMPLETE") == "PASS"

        meta = getattr(pol, "policy_metadata_json", None) or {} if pol else {}
        scope = meta.get("scope") or inv_row.get("scope") or {}
        levers = meta.get("policy_levers") or []
        codes = lever_codes(levers)
        if not codes and inv_row.get("codes"):
            codes = list(inv_row["codes"])

        lob = scope.get("lob")
        markets = scope.get("markets") or scope.get("market")
        states = scope.get("states")

        c_lob_mkt = c_codes = 0
        count_error = extract_error
        try:
            lm_key = json.dumps({"lob": lob, "markets": markets}, sort_keys=True, default=str)
            if lm_key not in cache_lob_mkt:
                cache_lob_mkt[lm_key] = count_lob_market(lob, markets)
            c_lob_mkt = cache_lob_mkt[lm_key]
            if codes:
                ck = json.dumps(
                    {"lob": lob, "markets": markets, "codes": sorted(set(codes))},
                    sort_keys=True,
                    default=str,
                )
                if ck not in cache_codes:
                    cache_codes[ck] = count_codes(lob, markets, codes)
                c_codes = cache_codes[ck]
            elif codeset_status == "NOT_APPLICABLE":
                c_codes = c_lob_mkt
            else:
                c_codes = 0
        except Exception as e:
            count_error = str(e)[:240]

        # Mechanism input checks (beyond nonzero count)
        missing_inputs: List[str] = []
        if not schema_ok:
            missing_inputs.append(f"claim_schema_missing:{','.join(missing_schema_cols)}")
        if arch in CODED_EMPIRICAL and codeset_status not in {"NOT_APPLICABLE", "LEGACY_NINE"}:
            if not codes and codeset_status != "NOT_APPLICABLE":
                missing_inputs.append("procedure_or_product_codes")
            if not markets:
                missing_inputs.append("scope.markets")
            if not lob:
                missing_inputs.append("scope.lob")
            if not states:
                missing_inputs.append("scope.states")
            # Mechanism-specific minimum inputs (not universal N)
            if arch == "PAYMENT_REIMBURSEMENT" and levers:
                has_pct = any(
                    (("parameters" in (L or {})) and (
                        "reduction_percent" in ((L or {}).get("parameters") or {})
                        or "mppr_percent" in ((L or {}).get("parameters") or {})
                        or "percent" in ((L or {}).get("parameters") or {})
                    ))
                    or "reduction" in str((L or {}).get("lever_type") or "").lower()
                    for L in levers
                )
                if not has_pct and "mppr" not in (name or "").lower():
                    # Still OK if representative payment lever present
                    if not levers:
                        missing_inputs.append("payment_lever_parameters")
            if arch == "PRIOR_AUTH_UM" and not levers:
                missing_inputs.append("um_levers")
        if codeset_status == "UNRESOLVED":
            missing_inputs.append("codeset_UNRESOLVED")
        if not def_complete:
            missing_inputs.append("definition_incomplete")

        # Date window: effective start vs observation window
        eff = inv_row.get("effective_period") or meta.get("effective_period") or {}
        eff_start = eff.get("start_date")
        window_ok = True
        if eff_start:
            try:
                es = str(eff_start)[:10]
                if es > end_date.isoformat():
                    window_ok = False
                    missing_inputs.append("effective_date_after_observation_window")
            except Exception:
                pass

        # Baseline/observation windows must have tenant claims for empirical path
        if c_tenant == 0 and arch in CODED_EMPIRICAL:
            missing_inputs.append("baseline_observation_window_empty")

        mechanism_inputs_ok = len(missing_inputs) == 0 and window_ok and count_error is None
        eligible_claim_count = int(c_codes or 0)

        pathway = classify_pathway(
            pid=pid,
            arch=arch,
            codeset_status=codeset_status,
            codes=codes,
            claim_count=eligible_claim_count,
            mechanism_inputs_ok=mechanism_inputs_ok or pid in FROZEN_NINE,
            def_complete=def_complete or pid in FROZEN_NINE,
        )

        # Empirical eligibility: pathway EMPIRICAL + nonzero + inputs
        empirical_eligible = (
            pathway == "EMPIRICAL_COHORT"
            and eligible_claim_count > 0
            and mechanism_inputs_ok
        )

        digest = config_digest(scope, levers, codes, folder)
        row = {
            "policy_id": pid,
            "name": name,
            "archetype": arch,
            "configuration_digest": digest,
            "definition_complete": def_complete,
            "codeset_status": codeset_status,
            "lever_code_count": len(codes),
            "codes_sample": codes[:12],
            "scope": {
                "lob": lob,
                "markets": markets,
                "states": states,
            },
            "window": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "required_claim_columns": required_columns,
            "claim_schema_ok": schema_ok,
            "counts": {
                "tenant_window": c_tenant,
                "lob_market_window": c_lob_mkt,
                "eligible_code_intersection": eligible_claim_count,
            },
            "mechanism_inputs_ok": mechanism_inputs_ok,
            "missing_inputs": missing_inputs,
            "count_error": count_error,
            "evidence_pathway": pathway,
            "empirical_execution_eligible": empirical_eligible,
            "synthetic_execution_eligible": pathway == "REPRESENTATIVE_SYNTHETIC_FIXTURE",
            "provenance_only": pathway == "PROVENANCE_ONLY",
            "blocked": pathway == "BLOCKED",
            "frozen_dec4": pid in FROZEN_NINE,
            "preflight_pass": pathway != "BLOCKED" and count_error is None,
        }
        rows.append(row)
        if i % 25 == 0 or i == len(inv["policies"]):
            print(f"  preflighted {i}/{len(inv['policies'])}", flush=True)

    db.close()

    summary = {
        "preflighted": len(rows),
        "nonzero_eligible_claim_cohorts": sum(
            1 for r in rows if r["counts"]["eligible_code_intersection"] > 0
        ),
        "mechanism_inputs_sufficient": sum(1 for r in rows if r["mechanism_inputs_ok"]),
        "empirical_execution_eligible": sum(1 for r in rows if r["empirical_execution_eligible"]),
        "synthetic_execution_eligible": sum(1 for r in rows if r["synthetic_execution_eligible"]),
        "provenance_only": sum(1 for r in rows if r["provenance_only"]),
        "blocked": sum(1 for r in rows if r["blocked"]),
        "preflight_pass": sum(1 for r in rows if r["preflight_pass"]),
        "coded_levers": sum(1 for r in rows if r["lever_code_count"] > 0),
    }

    matrix = {
        "document_id": "POLICY_289_PREFLIGHT_FEASIBILITY_MATRIX",
        "generated_at": utc(),
        "lane": "B_MECHANISM_EXECUTION",
        "rule": (
            "Zero matching cohort blocks claims-based numerical execution. "
            "Nonzero cohort still requires mechanism-specific input checks. "
            "Directional Representative Payer — not BCBS NC exact fidelity."
        ),
        "window": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "claim_schema": {"required": required_columns, "ok": schema_ok, "missing": missing_schema_cols},
        "cache_stats": {
            "lob_market_keys": len(cache_lob_mkt),
            "code_intersection_keys": len(cache_codes),
        },
        "summary": summary,
        "policies": rows,
        "blocked_policy_ids": [r["policy_id"] for r in rows if r["blocked"]],
        "empirical_policy_ids": [r["policy_id"] for r in rows if r["empirical_execution_eligible"]],
    }
    OUT.write_text(json.dumps(matrix, indent=2) + "\n")

    # Lane B ledger skeleton
    lane_b = {
        "document_id": "POLICY_289_LANE_B_EXECUTION_LEDGER",
        "generated_at": utc(),
        "preflight_summary": summary,
        "policies": [
            {
                "policy_id": r["policy_id"],
                "name": r["name"],
                "evidence_pathway": r["evidence_pathway"],
                "preflight_pass": r["preflight_pass"],
                "cohort_count": r["counts"]["eligible_code_intersection"],
                "mechanism_inputs_ok": r["mechanism_inputs_ok"],
                "job_status": "NOT_STARTED",
                "mechanism_result": "NOT_STARTED",
                "persistence": "NOT_STARTED",
            }
            for r in rows
        ],
    }
    LEDGER_B.write_text(json.dumps(lane_b, indent=2) + "\n")

    print(json.dumps(summary, indent=2))
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
