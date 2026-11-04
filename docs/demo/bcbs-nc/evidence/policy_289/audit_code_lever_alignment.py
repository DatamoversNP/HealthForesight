#!/usr/bin/env python3
"""Workstream C — code/lever alignment audit across all 289.

Candidate levers ≠ approved live. Non-code policies not penalized for missing CPT.
Frozen Dec4 fixtures flagged protected.
"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:7867/api/v1"
EMAIL = "admin@healthforesight.com"
PASSWORD = "Swan@1234"
EVID = Path(__file__).resolve().parent
INV = EVID / "POLICY_289_MASTER_INVENTORY.json"
V12 = EVID.parents[1] / "policy_definitions" / "v1.2"
OUT = EVID / "POLICY_289_CODE_LEVER_ALIGNMENT_AUDIT.json"

FROZEN = {
    "d403f101-08dd-45c9-ab83-d42e37c62018",
    "d0eeb370-df14-4478-8755-dad6c3a35a47",
    "d7441dd9-3bfe-405e-ae6c-0377204bbb7e",
}
EM = {"99213", "99214", "99215", "99203", "99204", "99205"}


def login():
    req = urllib.request.Request(
        f"{API}/auth/login",
        data=json.dumps({"email": EMAIL, "password": PASSWORD}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["access_token"]


def codes_from(policy):
    out = []
    evidence = set()
    for L in policy.get("policy_levers") or []:
        params = (L or {}).get("parameters") or {}
        if params.get("evidence_class"):
            evidence.add(params["evidence_class"])
        for k in ("codes", "cpt_codes", "target_codes", "procedure_codes", "ndc_codes"):
            v = params.get(k)
            if isinstance(v, list):
                out.extend(str(x) for x in v if x is not None)
    return sorted(set(out)), evidence


def main():
    tok = login()
    req = urllib.request.Request(f"{API}/policies", headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        live = {str(p["id"]): p for p in json.load(r)}
    inv = json.loads(INV.read_text())
    reg = json.loads((V12 / "POLICY_PACKAGE_REGISTRY.json").read_text()).get("packages") or {}

    rows = []
    fails = 0
    candidate = 0
    for r in inv["policies"]:
        pid = r["policy_id"]
        pol = live.get(pid) or {}
        codes, evidence = codes_from(pol)
        folder = reg.get(pid)
        codeset_status = None
        if folder:
            pkg = next((V12 / folder).glob("*PACKAGE.json"), None)
            if pkg:
                codeset_status = (json.loads(pkg.read_text()).get("codeset") or {}).get("status")
            elif folder in {"mri", "mppr", "sos", "ptp", "mue", "therapy", "infusion", "ncd_study", "lcd_study"}:
                codeset_status = "LEGACY_NINE"

        issues = []
        lever_class = "NONE"
        if "REPRESENTATIVE_DESIGN" in evidence or (
            codes and codeset_status == "CANDIDATE_SCHEDULE"
        ):
            lever_class = "CANDIDATE_PERSISTED"
            candidate += 1
        elif codes and pid in FROZEN:
            lever_class = "FROZEN_DEMO"
        elif codes:
            lever_class = "CODES_PRESENT_UNCLASSIFIED"
        elif codeset_status == "NOT_APPLICABLE":
            lever_class = "NOT_APPLICABLE"
        elif codeset_status == "UNRESOLVED":
            lever_class = "UNRESOLVED"

        name = (r.get("name") or "").lower()
        if codes and set(codes) & EM and ("mri" in name or "imaging" in name):
            issues.append("E/M_CODES_ON_IMAGING_TARGETS")
        if codeset_status == "CANDIDATE_SCHEDULE" and not codes and r["archetype"] in {
            "PRIOR_AUTH_UM",
            "SITE_OF_CARE",
        }:
            issues.append("CANDIDATE_SCHEDULE_BUT_LIVE_LEVERS_EMPTY")
        if codeset_status == "NOT_APPLICABLE" and codes:
            issues.append("NOT_APPLICABLE_CODESET_BUT_CODES_ON_LEVERS")
        if pid in FROZEN:
            # ensure primary untouched structurally — markets for MRI
            sc = pol.get("scope") or {}
            if pid == "d403f101-08dd-45c9-ab83-d42e37c62018":
                if set(codes) - {"72148", "72149", "72158"}:
                    issues.append("MRI_FROZEN_CODES_DRIFTED")
                if sc.get("states") != ["NC"]:
                    issues.append("MRI_STATES_DRIFTED")

        if issues:
            fails += 1
        rows.append(
            {
                "policy_id": pid,
                "name": r["name"],
                "archetype": r["archetype"],
                "codeset_status": codeset_status,
                "lever_class": lever_class,
                "code_count": len(codes),
                "codes_sample": codes[:10],
                "issues": issues,
                "frozen_protected": pid in FROZEN,
                "pass": len(issues) == 0,
            }
        )

    out = {
        "document_id": "POLICY_289_CODE_LEVER_ALIGNMENT_AUDIT",
        "total": len(rows),
        "pass": sum(1 for x in rows if x["pass"]),
        "fail": fails,
        "candidate_persisted": candidate,
        "approved_live": 0,  # none claimed as operative approved
        "not_applicable": sum(1 for x in rows if x["lever_class"] == "NOT_APPLICABLE"),
        "rule": "Candidate levers must not be reported as approved live/operative levers",
        "policies": rows,
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(
        json.dumps(
            {
                "total": out["total"],
                "pass": out["pass"],
                "fail": out["fail"],
                "candidate_persisted": out["candidate_persisted"],
                "approved_live": 0,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
