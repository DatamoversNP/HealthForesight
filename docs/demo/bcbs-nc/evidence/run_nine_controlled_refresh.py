#!/usr/bin/env python3
"""Controlled refresh for Representative nine after NC scope hygiene.

Rules:
- Do NOT mass-refresh the catalog.
- Preserve Dec 4 known-answer fixtures (MRI/MPPR/SOS mechanical KAs).
- MRI lever codes 72148/72149/72158 exist only in claim markets NYC/DFW/BOS (not NC).
  Jurisdiction stays NC via states=[]; claim markets set to metros that hold lumbar codes.
- Empirical baseline/predicted/observation are labeled SYNTHETIC demo substrate.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "http://127.0.0.1:7867/api/v1"
EMAIL = "admin@healthforesight.com"
PASSWORD = "Swan@1234"
EVIDENCE = Path(__file__).resolve().parent
OUT = EVIDENCE / "NINE_CONTROLLED_REFRESH_EXECUTION_REPORT.json"

NINE = [
    {
        "key": "mri",
        "policy_id": "d403f101-08dd-45c9-ab83-d42e37c62018",
        "ka_frozen": True,
        "claim_markets": ["NYC", "DFW"],  # lumbar CPT locations in demo claims
        "states": ["NC"],
        "run_predicted": True,
        "notes": "Lumbar CPTs absent from market=NC; metros hold codes. Jurisdiction NC via states.",
    },
    {
        "key": "mppr",
        "policy_id": "d0eeb370-df14-4478-8755-dad6c3a35a47",
        "ka_frozen": True,
        "claim_markets": ["NC"],
        "states": ["NC"],
        "run_predicted": False,  # mechanical KA fixture; empty lever codes
        "notes": "Preserve mechanical KA; empirical predicted skipped (no CPT levers).",
    },
    {
        "key": "sos",
        "policy_id": "d7441dd9-3bfe-405e-ae6c-0377204bbb7e",
        "ka_frozen": True,
        "claim_markets": ["NC"],
        "states": ["NC"],
        "run_predicted": False,
        "notes": "Preserve mechanical KA; empirical predicted skipped.",
    },
    {
        "key": "ptp",
        "policy_id": "58b839b5-b6e0-59e0-9406-d817877c3ce8",
        "ka_frozen": True,
        "claim_markets": ["NC"],
        "states": ["NC"],
        "run_predicted": False,
        "notes": "SYNTHETIC fixture / modifiers absent for empirical PTP.",
    },
    {
        "key": "mue",
        "policy_id": "e11b049d-fcce-55cc-bcd7-71329038383b",
        "ka_frozen": True,
        "claim_markets": ["NC"],
        "states": ["NC"],
        "run_predicted": False,
        "notes": "SYNTHETIC fixture; authoritative MUE file not on host.",
    },
    {
        "key": "therapy",
        "policy_id": "f2b8e7f3-1627-5dbe-8d7e-757ce21aa55b",
        "ka_frozen": True,
        "claim_markets": ["NC"],
        "states": ["NC"],
        "run_predicted": False,
        "notes": "Mechanical $80 KA; coverage what-if NOT_SUPPORTED.",
    },
    {
        "key": "infusion",
        "policy_id": "11218053-bdc0-569f-a415-fb61c5dcda37",
        "ka_frozen": True,
        "claim_markets": ["NC"],
        "states": ["NC"],
        "run_predicted": False,
        "notes": "Mechanical KA fixture.",
    },
    {
        "key": "ncd",
        "policy_id": "4f8c34e3-015b-509d-90ba-521261464258",
        "ka_frozen": True,
        "claim_markets": ["NC"],
        "states": ["NC"],
        "run_predicted": False,
        "notes": "PROVENANCE_ONLY — no financial lifecycle.",
    },
    {
        "key": "lcd",
        "policy_id": "649b4ac8-ca82-5b84-aa87-84834490731a",
        "ka_frozen": True,
        "claim_markets": ["NC"],
        "states": ["NC"],
        "run_predicted": False,
        "notes": "PROVENANCE_ONLY — no financial lifecycle.",
    },
]


def _req(method: str, path: str, tok: str | None = None, data=None, timeout: int = 600):
    headers = {"Content-Type": "application/json"}
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(f"{API}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode("utf-8", "replace")[:800]}
    except Exception as e:
        return 0, {"error": str(e)[:400]}


def login() -> str:
    code, body = _req("POST", "/auth/login", data={"email": EMAIL, "password": PASSWORD}, timeout=60)
    if code != 200:
        raise RuntimeError(f"login failed {code} {body}")
    return body["access_token"]


def align_scope(tok: str, spec: dict, policy: dict) -> dict:
    sc = dict(policy.get("scope") or {})
    before = {"markets": sc.get("markets"), "states": sc.get("states")}
    sc["markets"] = list(spec["claim_markets"])
    sc["states"] = list(spec["states"])
    if not sc.get("lob"):
        sc["lob"] = ["COMMERCIAL"]
    payload = {
        "name": policy["name"],
        "policy_type": policy["policy_type"],
        "owner_role": policy.get("owner_role"),
        "description": policy.get("description") or policy["name"],
        "status": policy.get("status") or "ACTIVE",
        "scope": sc,
        "effective_period": policy.get("effective_period")
        or {"start_date": "2026-01-01T00:00:00", "end_date": None},
        "enforcement": policy.get("enforcement")
        or {"mechanism": "HARD", "touchpoint": ["PA_WORKFLOW"], "override_allowed": False},
        "policy_levers": policy.get("policy_levers") or [],
        "expected_behavioral_response": policy.get("expected_behavioral_response"),
        "analytics_expectations": policy.get("analytics_expectations"),
        "ui_hints": policy.get("ui_hints"),
    }
    # MRI description keeps NC jurisdiction + metro claim markets honesty
    if spec["key"] == "mri":
        payload["description"] = (
            "Representative Payer (Blue Cross NC-like) outpatient MRI prior authorization. "
            "Proposed v1.2 anatomy: lumbar spine MRI (CPT 72148/72149/72158). "
            "Jurisdiction: NC. Claim market filter uses NYC/DFW because demo lumbar CPTs "
            "are planted there (not in market=NC). DEFINITION_REVIEW_REQUIRED; activation prohibited; "
            "Dec 4 synthetic KAs remain frozen independently."
        )
    code, body = _req("PUT", f"/policies/{spec['policy_id']}", tok, payload, timeout=180)
    after = None
    if code == 200:
        after = {
            "markets": (body.get("scope") or {}).get("markets"),
            "states": (body.get("scope") or {}).get("states"),
        }
    return {"http": code, "before": before, "after": after, "error": body.get("error") if code != 200 else None}


def refresh_baseline(tok: str, policy_id: str) -> dict:
    t0 = time.time()
    code, body = _req(
        "POST",
        "/baselines/refresh",
        tok,
        {
            "policy_id": policy_id,
            "baseline_type": "ROLLING",
            "window_months": 12,
            "refresh_reason": "POLICY_UPDATE",
        },
        timeout=900,
    )
    out = {"http": code, "elapsed_s": round(time.time() - t0, 1)}
    if code in (200, 201) and isinstance(body, dict):
        m = body.get("baseline_metrics") or {}
        out["baseline_id"] = body.get("baseline_id")
        out["window"] = [body.get("window_start_date"), body.get("window_end_date")]
        out["total_claims"] = m.get("total_claims")
        out["unique_members"] = m.get("unique_members")
        out["util"] = m.get("util_rate_target_per_1000_mm") or m.get("util_rate_total_per_1000_mm")
    else:
        out["error"] = body.get("error") or body.get("detail") or body
    return out


def predicted_impact(tok: str, policy_id: str) -> dict:
    t0 = time.time()
    code, body = _req("POST", f"/policies/{policy_id}/predicted-impact", tok, timeout=600)
    out = {"http": code, "elapsed_s": round(time.time() - t0, 1)}
    if code in (200, 201) and isinstance(body, dict):
        out["keys"] = list(body.keys())[:20]
        out["has_impact"] = bool(body)
    else:
        out["error"] = body.get("error") or body.get("detail") or body
    return out


def latest_impact_analysis(tok: str, policy_id: str) -> str | None:
    code, body = _req(
        "GET",
        f"/analyses?policy_id={policy_id}&analysis_type=IMPACT&limit=5",
        tok,
        timeout=120,
    )
    if code != 200:
        return None
    rows = body if isinstance(body, list) else (body.get("items") or body.get("analyses") or [])
    for r in rows:
        if str(r.get("status", "")).upper() == "COMPLETED":
            return str(r.get("id") or r.get("analysis_id"))
    return str(rows[0].get("id")) if rows else None


def observation_from_analysis(tok: str, analysis_id: str, policy_id: str) -> dict:
    t0 = time.time()
    code, body = _req(
        "POST",
        f"/observations/from-analysis/{analysis_id}?policy_id={policy_id}",
        tok,
        timeout=600,
    )
    out = {"http": code, "elapsed_s": round(time.time() - t0, 1), "analysis_id": analysis_id}
    if code in (200, 201) and isinstance(body, dict):
        out["observation_id"] = body.get("observation_id") or body.get("id")
        out["verdict"] = body.get("verdict_status") or body.get("verdict")
    else:
        out["error"] = body.get("error") or body.get("detail") or body
    return out


def get_policy(tok: str, policy_id: str) -> dict:
    code, body = _req("GET", f"/policies/{policy_id}", tok, timeout=120)
    if code != 200:
        raise RuntimeError(f"get policy {policy_id} {code} {body}")
    return body


def main():
    tok = login()
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "claims_mapping_note": (
            "Lumbar CPT 72148/72149/72158 exist only in NYC/DFW/BOS claim markets; "
            "market=NC has other MRI codes (e.g. 72141/72142) but zero lumbar rows. "
            "MRI claim markets restored to NYC/DFW for cohort match; states remain NC."
        ),
        "preserve_frozen_kas": True,
        "results": [],
    }
    for spec in NINE:
        print(f"\n===== {spec['key']} =====", flush=True)
        row = {
            "key": spec["key"],
            "policy_id": spec["policy_id"],
            "ka_frozen": spec["ka_frozen"],
            "notes": spec["notes"],
        }
        try:
            pol = get_policy(tok, spec["policy_id"])
            row["scope_align"] = align_scope(tok, spec, pol)
            print("  scope", row["scope_align"].get("after"), flush=True)

            # provenance-only: skip empirical chain
            if spec["key"] in ("ncd", "lcd"):
                row["baseline"] = {"skipped": True, "reason": "PROVENANCE_ONLY"}
                row["predicted"] = {"skipped": True, "reason": "PROVENANCE_ONLY"}
                row["observation"] = {"skipped": True, "reason": "PROVENANCE_ONLY"}
                row["status"] = "PROVENANCE_ONLY"
                report["results"].append(row)
                continue

            row["baseline"] = refresh_baseline(tok, spec["policy_id"])
            print(
                "  baseline",
                row["baseline"].get("http"),
                "claims",
                row["baseline"].get("total_claims"),
                flush=True,
            )

            if spec.get("run_predicted"):
                row["predicted"] = predicted_impact(tok, spec["policy_id"])
                print("  predicted", row["predicted"].get("http"), flush=True)
            else:
                row["predicted"] = {
                    "skipped": True,
                    "reason": "KA_FROZEN_OR_NO_LEVER_CODES",
                }

            # Observation only when we have a completed IMPACT analysis (do not invent)
            aid = latest_impact_analysis(tok, spec["policy_id"])
            if aid and spec.get("run_predicted"):
                row["observation"] = observation_from_analysis(tok, aid, spec["policy_id"])
                print(
                    "  observation",
                    row["observation"].get("http"),
                    row["observation"].get("verdict"),
                    flush=True,
                )
            else:
                row["observation"] = {
                    "skipped": True,
                    "reason": "No IMPACT analysis or predicted skipped — existing obs retained",
                    "latest_impact_analysis_id": aid,
                }

            bl_ok = row["baseline"].get("http") in (200, 201)
            row["status"] = "REFRESHED" if bl_ok else "BASELINE_FAILED"
            if spec["ka_frozen"]:
                row["ka_guard"] = "FROZEN_KA_PRESERVED"
        except Exception as e:
            row["status"] = "ERROR"
            row["error"] = str(e)[:400]
            print("  ERROR", e, flush=True)
        report["results"].append(row)
        OUT.write_text(json.dumps(report, indent=2) + "\n")

    summary = {
        "refreshed": sum(1 for r in report["results"] if r.get("status") == "REFRESHED"),
        "baseline_failed": sum(1 for r in report["results"] if r.get("status") == "BASELINE_FAILED"),
        "provenance_only": sum(1 for r in report["results"] if r.get("status") == "PROVENANCE_ONLY"),
        "errors": sum(1 for r in report["results"] if r.get("status") == "ERROR"),
    }
    report["summary"] = summary
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    md = EVIDENCE / "NINE_CONTROLLED_REFRESH_EXECUTION_REPORT.md"
    lines = [
        "# Nine Policy Controlled Refresh — Execution Report",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        report["claims_mapping_note"],
        "",
        f"Summary: {summary}",
        "",
        "| Key | Status | Baseline HTTP | Claims | Predicted | Observation | Notes |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in report["results"]:
        bl = r.get("baseline") or {}
        pred = r.get("predicted") or {}
        obs = r.get("observation") or {}
        lines.append(
            f"| {r['key']} | {r.get('status')} | {bl.get('http') or ('skip' if bl.get('skipped') else '')} | "
            f"{bl.get('total_claims', '—')} | "
            f"{pred.get('http') or ('skip' if pred.get('skipped') else '')} | "
            f"{obs.get('http') or ('skip' if obs.get('skipped') else '')} | {r.get('notes','')[:60]} |"
        )
    md.write_text("\n".join(lines) + "\n")
    print("\nDONE", summary, flush=True)
    print("WROTE", OUT, flush=True)


if __name__ == "__main__":
    main()
