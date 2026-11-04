#!/usr/bin/env python3
"""Persist candidate codes onto live policy_levers for packages with CANDIDATE_SCHEDULE.

Skips Dec4 nine. Does not invent rates. Retries on timeout.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:7867/api/v1"
EMAIL = "admin@healthforesight.com"
PASSWORD = "Swan@1234"
EVID = Path(__file__).resolve().parent
# .../docs/demo/bcbs-nc/evidence/policy_289 → v1.2 is sibling of evidence under bcbs-nc
V12 = EVID.parents[1] / "policy_definitions" / "v1.2"
REGISTRY = V12 / "POLICY_PACKAGE_REGISTRY.json"
OUT = EVID / "PERSIST_CANDIDATE_LEVERS_RESULT.json"

FROZEN = {
    "d403f101-08dd-45c9-ab83-d42e37c62018",
    "d0eeb370-df14-4478-8755-dad6c3a35a47",
    "d7441dd9-3bfe-405e-ae6c-0377204bbb7e",
    "58b839b5-b6e0-59e0-9406-d817877c3ce8",
    "e11b049d-fcce-55cc-bcd7-71329038383b",
    "f2b8e7f3-1627-5dbe-8d7e-757ce21aa55b",
    "11218053-bdc0-569f-a415-fb61c5dcda37",
    "4f8c34e3-015b-509d-90ba-521261464258",
    "649b4ac8-ca82-5b84-aa87-84834490731a",
}


def login() -> str:
    req = urllib.request.Request(
        f"{API}/auth/login",
        data=json.dumps({"email": EMAIL, "password": PASSWORD}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)["access_token"]


def get_json(tok: str, path: str, timeout: int = 300):
    req = urllib.request.Request(f"{API}{path}", headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def put_json(tok: str, path: str, body: dict, timeout: int = 120):
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
        method="PUT",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def main() -> int:
    reg = json.loads(REGISTRY.read_text())
    tok = login()
    print("loading policies…", flush=True)
    policies = {str(p["id"]): p for p in get_json(tok, "/policies")}
    print(f"loaded {len(policies)}", flush=True)

    results = []
    ok = fail = skip = 0
    for pid, folder in sorted(reg["packages"].items(), key=lambda x: x[1]):
        if pid in FROZEN:
            skip += 1
            continue
        if not str(folder).startswith("catalog/"):
            skip += 1
            continue
        pkg_path = next((V12 / folder).glob("*PACKAGE.json"), None)
        if not pkg_path:
            fail += 1
            results.append({"policy_id": pid, "error": "missing_package"})
            continue
        pkg = json.loads(pkg_path.read_text())
        if pkg.get("codeset", {}).get("status") != "CANDIDATE_SCHEDULE":
            skip += 1
            continue
        codes = [c["code"] for c in pkg["codeset"].get("codes") or []]
        if not codes:
            skip += 1
            continue
        live = policies.get(pid)
        if not live:
            fail += 1
            results.append({"policy_id": pid, "error": "not_in_live_catalog"})
            continue
        levers = list(live.get("policy_levers") or [])
        if levers:
            params = dict(levers[0].get("parameters") or {})
            params["codes"] = codes
            params["evidence_class"] = "REPRESENTATIVE_DESIGN"
            levers[0] = {**levers[0], "parameters": params}
        else:
            levers = [
                {
                    "lever_type": live.get("policy_type") or "PRIOR_AUTH",
                    "parameters": {
                        "codes": codes,
                        "requires_pa": True,
                        "evidence_class": "REPRESENTATIVE_DESIGN",
                    },
                }
            ]
        body = {
            k: v
            for k, v in {
                "name": live.get("name"),
                "description": live.get("description")
                or f"Representative Payer package {pkg.get('package_version')}",
                "policy_type": live.get("policy_type"),
                "scope": live.get("scope"),
                "policy_levers": levers,
                "status": live.get("status"),
                "effective_period": live.get("effective_period"),
                "enforcement": live.get("enforcement"),
            }.items()
            if v is not None
        }
        for attempt in range(3):
            try:
                put_json(tok, f"/policies/{pid}", body)
                ok += 1
                results.append({"policy_id": pid, "name": live.get("name"), "codes": len(codes), "ok": True})
                print(f"OK {ok} {live.get('name')[:50]} codes={len(codes)}", flush=True)
                break
            except Exception as e:
                if attempt == 2:
                    fail += 1
                    results.append({"policy_id": pid, "name": live.get("name"), "ok": False, "error": str(e)[:200]})
                    print(f"FAIL {live.get('name')[:50]} {e}", flush=True)
                else:
                    time.sleep(2 + attempt * 2)
                    try:
                        tok = login()
                    except Exception:
                        pass

    summary = {"ok": ok, "fail": fail, "skip": skip, "results": results}
    OUT.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in ("ok", "fail", "skip")}, indent=2))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
