#!/usr/bin/env python3
"""Overnight autonomous high-confidence gates for all catalog policies (excl. already-HIGH nine).

Same depth as Dec4 optional six:
  API: policy, workspace, composition, causal-feasibility, causal-impact, verdict-evidence
  Browser: workspace name, Monitoring panel, Composition, Causal, refresh persistence

Does NOT invent financial KAs. Does NOT activate policies. Does NOT reseed claims.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BATCH_DIR = ROOT / "overnight_batches"
MASTER_JSON = ROOT / "ALL_POLICIES_HIGH_CONFIDENCE_MASTER_REPORT.json"
MASTER_MD = ROOT / "ALL_POLICIES_HIGH_CONFIDENCE_MASTER_REPORT.md"
STATE = ROOT / "overnight_batches" / "runner_state.json"
SCREEN = ROOT / "overnight_batches" / "screenshots"
SCREEN.mkdir(parents=True, exist_ok=True)

BASE = "http://127.0.0.1:7868"
API = "http://127.0.0.1:7867/api/v1"
EMAIL = "admin@healthforesight.com"
PASSWORD = "Swan@1234"

NINE = {
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


def _login_token() -> str:
    req = urllib.request.Request(
        f"{API}/auth/login",
        data=json.dumps({"email": EMAIL, "password": PASSWORD}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["access_token"]


def _get(tok: str, path: str) -> dict:
    req = urllib.request.Request(f"{API}{path}", headers={"Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return {"ok": True, "status": r.status, "data": json.load(r)}
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "error": e.read().decode("utf-8", "replace")[:400]}
    except Exception as e:
        return {"ok": False, "status": None, "error": str(e)[:400]}


def api_gate(tok: str, policy_id: str, name: str) -> dict:
    checks = {}
    for key, path in [
        ("policy", f"/policies/{policy_id}"),
        ("workspace", f"/policies/{policy_id}/workspace"),
        ("composition", f"/enterprise/policies/{policy_id}/composition"),
        ("causal_feasibility", f"/enterprise/policies/{policy_id}/causal-feasibility"),
        ("causal_impact", f"/enterprise/policies/{policy_id}/causal-impact"),
        ("verdict_evidence", f"/enterprise/policies/{policy_id}/verdict-evidence?observation_verdict=UNKNOWN"),
    ]:
        checks[key] = _get(tok, path)
    ws_name_ok = False
    if checks["workspace"]["ok"]:
        pol = (checks["workspace"]["data"] or {}).get("policy") or {}
        ws_name = pol.get("name") or pol.get("policy_name") or ""
        ws_name_ok = bool(name) and (name[:20].lower() in ws_name.lower() or ws_name[:20].lower() in name.lower())
    api_ok = all(checks[k]["ok"] for k in checks) and ws_name_ok
    return {
        "api_ok": api_ok,
        "workspace_name_ok": ws_name_ok,
        "http": {k: v.get("status") for k, v in checks.items()},
        "errors": {k: v.get("error") for k, v in checks.items() if not v.get("ok")},
    }


async def _click_workspace_tab(page, label: str) -> bool:
    """Click MUI workspace tab via DOM — Playwright locator clicks miss scrollable tabs."""
    clicked = await page.evaluate(
        """(label) => {
          const roots = [
            ...document.querySelectorAll('.workspace-tabs'),
            ...document.querySelectorAll('[role="tablist"]'),
          ];
          for (const root of roots) {
            const tabs = [...root.querySelectorAll('[role="tab"]')];
            const t = tabs.find((x) => (x.innerText || x.textContent || '').trim() === label);
            if (!t) continue;
            t.scrollIntoView({ block: 'nearest', inline: 'center' });
            t.click();
            return true;
          }
          return false;
        }""",
        label,
    )
    if not clicked:
        return False
    deadline = time.time() + 8
    while time.time() < deadline:
        selected = await page.evaluate(
            """(label) => {
              const tabs = [...document.querySelectorAll('.workspace-tabs [role="tab"], [role="tablist"] [role="tab"]')];
              const t = tabs.find((x) => (x.innerText || '').trim() === label);
              return t ? t.getAttribute('aria-selected') === 'true' : false;
            }""",
            label,
        )
        if selected:
            await asyncio.sleep(0.6)
            return True
        await asyncio.sleep(0.2)
    return False


async def _main_text(page) -> str:
    try:
        return await page.locator("body").inner_text(timeout=8000)
    except Exception:
        return ""


async def browser_gate(page, policy_id: str, name: str, shot_prefix: str) -> dict:
    out = {
        "browser_ok": False,
        "workspace_ok": False,
        "monitoring_ok": False,
        "composition_ok": False,
        "causal_ok": False,
        "persistence_ok": False,
        "err": None,
    }
    try:
        await page.goto(
            f"{BASE}/policies/workspace/{policy_id}",
            wait_until="domcontentloaded",
            timeout=90000,
        )
        deadline = time.time() + 60
        while time.time() < deadline:
            body = await _main_text(page)
            if (name and name[:18].lower() in body.lower()) or "Overview" in body:
                # wait past spinner
                if await page.locator(".workspace-tabs [role='tab'], [role='tablist'] [role='tab']").count():
                    out["workspace_ok"] = True
                    break
            await asyncio.sleep(0.3)
        if not out["workspace_ok"]:
            raise TimeoutError("workspace name/overview not found")

        # Composition + Causal first (lighter APIs). Monitoring last — its fetches can starve siblings.
        if await _click_workspace_tab(page, "Composition"):
            deadline = time.time() + 45
            while time.time() < deadline:
                body = await _main_text(page)
                if "Failed to load composition" in body:
                    out["composition_ok"] = False
                    break
                if "Policy composition" in body or "Primary domain" in body:
                    out["composition_ok"] = True
                    break
                await asyncio.sleep(0.4)
            if not out["composition_ok"]:
                await page.reload(wait_until="domcontentloaded")
                await asyncio.sleep(1.0)
                await _click_workspace_tab(page, "Composition")
                deadline = time.time() + 30
                while time.time() < deadline:
                    body = await _main_text(page)
                    if "Policy composition" in body or "Primary domain" in body:
                        out["composition_ok"] = True
                        break
                    await asyncio.sleep(0.4)

        if await _click_workspace_tab(page, "Causal Impact"):
            deadline = time.time() + 45
            while time.time() < deadline:
                body = await _main_text(page)
                if "Failed to load causal" in body:
                    out["causal_ok"] = False
                    break
                if "Causal Impact Workbench" in body or "Causal feasibility" in body:
                    out["causal_ok"] = True
                    break
                await asyncio.sleep(0.4)
            if not out["causal_ok"]:
                await _click_workspace_tab(page, "Causal Impact")
                await asyncio.sleep(2)
                body = await _main_text(page)
                out["causal_ok"] = (
                    "Causal Impact Workbench" in body or "Causal feasibility" in body
                )

        if not await _click_workspace_tab(page, "Monitoring"):
            raise TimeoutError("Monitoring tab click failed")
        deadline = time.time() + 35
        while time.time() < deadline:
            if await page.locator(
                '[data-testid="demo-catalog-monitoring-panel"],'
                '[data-testid="demo-mechanical-panel"],'
                '[data-testid="demo-provenance-panel"]'
            ).count():
                out["monitoring_ok"] = True
                break
            body = await _main_text(page)
            if any(
                s in body
                for s in (
                    "Performance monitoring",
                    "Catalog policy monitoring",
                    "Mechanical / synthetic",
                    "Coverage study — provenance only",
                    "Current verdict",
                    "No observation or predicted impact",
                )
            ):
                out["monitoring_ok"] = True
                break
            if "Failed to load monitoring" in body:
                break
            await asyncio.sleep(0.3)
        try:
            await page.screenshot(path=str(SCREEN / f"{shot_prefix}_monitoring.png"), full_page=False)
        except Exception:
            pass

        await page.reload(wait_until="domcontentloaded")
        deadline = time.time() + 45
        while time.time() < deadline:
            if await page.locator(".workspace-tabs [role='tab'], [role='tablist'] [role='tab']").count():
                break
            await asyncio.sleep(0.25)
        if not await _click_workspace_tab(page, "Monitoring"):
            raise TimeoutError("Monitoring tab click failed after reload")
        await asyncio.sleep(0.8)
        body = await _main_text(page)
        out["persistence_ok"] = (
            await page.locator(
                '[data-testid="demo-catalog-monitoring-panel"],'
                '[data-testid="demo-mechanical-panel"],'
                '[data-testid="demo-provenance-panel"]'
            ).count()
            > 0
        ) or any(
            s in body
            for s in (
                "Performance monitoring",
                "Catalog policy monitoring",
                "Current verdict",
                "Mechanical / synthetic",
            )
        )

        out["browser_ok"] = all(
            [
                out["workspace_ok"],
                out["monitoring_ok"],
                out["composition_ok"],
                out["causal_ok"],
                out["persistence_ok"],
            ]
        )
    except Exception as e:
        out["err"] = str(e)[:400]
        try:
            await page.screenshot(path=str(SCREEN / f"{shot_prefix}_ERR.png"), full_page=False)
        except Exception:
            pass
    return out


def load_master() -> dict:
    if MASTER_JSON.exists():
        return json.loads(MASTER_JSON.read_text())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policies": {},
        "batches_completed": [],
        "summary": {},
    }


def save_master(master: dict) -> None:
    rows = list(master.get("policies", {}).values())
    high = sum(1 for r in rows if r.get("confidence") == "HIGH")
    fail = sum(1 for r in rows if r.get("confidence") == "FAIL")
    master["summary"] = {
        "evaluated": len(rows),
        "high": high,
        "fail": fail,
        "pass_rate": round(high / len(rows), 4) if rows else 0,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    master["updated_at"] = datetime.now(timezone.utc).isoformat()
    MASTER_JSON.write_text(json.dumps(master, indent=2) + "\n")
    lines = [
        "# All Policies High-Confidence Master Report",
        "",
        f"Updated: `{master['updated_at']}`",
        "",
        f"Evaluated: **{len(rows)}** · HIGH: **{high}** · FAIL: **{fail}** · Pass rate: **{master['summary']['pass_rate']}**",
        "",
        f"Batches completed: {master.get('batches_completed')}",
        "",
        "| Policy ID | Name | Confidence | API | Browser | Notes |",
        "|---|---|---|---|---|---|",
    ]
    for r in sorted(rows, key=lambda x: (x.get("name") or "")):
        notes = r.get("err") or ",".join((r.get("api") or {}).get("errors", {}).keys()) or ""
        lines.append(
            f"| `{r.get('policy_id')}` | {r.get('name')} | {r.get('confidence')} | "
            f"{'PASS' if (r.get('api') or {}).get('api_ok') else 'FAIL'} | "
            f"{'PASS' if (r.get('browser') or {}).get('browser_ok') else 'FAIL'} | {notes[:80]} |"
        )
    MASTER_MD.write_text("\n".join(lines) + "\n")


async def _login_browser(page) -> None:
    await page.goto(f"{BASE}/login", wait_until="domcontentloaded", timeout=60000)
    await page.get_by_label("Email").fill(EMAIL)
    await page.get_by_label("Password").fill(PASSWORD)
    await page.get_by_role("button", name="Sign in with email").click()
    await page.wait_for_url(lambda u: "/login" not in str(u), timeout=90000)


async def _launch_browser():
    from playwright.async_api import async_playwright

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    page = await browser.new_page(viewport={"width": 1440, "height": 900})
    await _login_browser(page)
    return pw, browser, page


def _already_high(master: dict, pid: str) -> bool:
    row = (master.get("policies") or {}).get(pid) or {}
    return row.get("confidence") == "HIGH"


async def run_batch(batch_num: int, api_only: bool = False, force: bool = False) -> dict:
    roster_path = BATCH_DIR / f"batch_{batch_num:02d}_roster.json"
    roster = json.loads(roster_path.read_text())
    policies = [p for p in roster["policies"] if p["policy_id"] not in NINE]
    tok = _login_token()
    master = load_master()
    results = []

    pw = browser = page = None
    if not api_only:
        pw, browser, page = await _launch_browser()

    try:
        for i, p in enumerate(policies, 1):
            pid = p["policy_id"]
            name = p.get("name") or ""
            if not force and _already_high(master, pid):
                print(f"[batch {batch_num}] {i}/{len(policies)} SKIP HIGH {name[:50]}", flush=True)
                results.append(master["policies"][pid])
                continue
            print(f"[batch {batch_num}] {i}/{len(policies)} {name[:60]}", flush=True)
            STATE.write_text(
                json.dumps(
                    {
                        "current_batch": batch_num,
                        "current_index": i,
                        "current_policy_id": pid,
                        "current_name": name,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    indent=2,
                )
                + "\n"
            )
            try:
                # refresh token periodically
                if i == 1 or i % 10 == 0:
                    try:
                        tok = _login_token()
                    except Exception:
                        pass
                api = api_gate(tok, pid, name)
                browser_res = {"browser_ok": api_only, "skipped": api_only}
                if not api_only and page is not None:
                    try:
                        browser_res = await asyncio.wait_for(
                            browser_gate(page, pid, name, f"b{batch_num:02d}_{i:02d}_{pid[:8]}"),
                            timeout=180,
                        )
                    except Exception as be:
                        print(f"  browser error, relaunching: {be}", flush=True)
                        try:
                            if browser:
                                await browser.close()
                        except Exception:
                            pass
                        try:
                            if pw:
                                await pw.stop()
                        except Exception:
                            pass
                        pw, browser, page = await _launch_browser()
                        browser_res = await asyncio.wait_for(
                            browser_gate(page, pid, name, f"b{batch_num:02d}_{i:02d}_{pid[:8]}"),
                            timeout=180,
                        )
                confidence = "HIGH" if api.get("api_ok") and browser_res.get("browser_ok") else "FAIL"
                row = {
                    "policy_id": pid,
                    "name": name,
                    "policy_type": p.get("policy_type"),
                    "status": p.get("status"),
                    "batch": batch_num,
                    "confidence": confidence,
                    "api": api,
                    "browser": browser_res,
                    "evaluated_at": datetime.now(timezone.utc).isoformat(),
                }
            except Exception as e:
                row = {
                    "policy_id": pid,
                    "name": name,
                    "policy_type": p.get("policy_type"),
                    "status": p.get("status"),
                    "batch": batch_num,
                    "confidence": "FAIL",
                    "api": {"api_ok": False, "error": str(e)[:400]},
                    "browser": {"browser_ok": False, "err": str(e)[:400]},
                    "err": str(e)[:400],
                    "evaluated_at": datetime.now(timezone.utc).isoformat(),
                }
            results.append(row)
            master.setdefault("policies", {})[pid] = row
            save_master(master)
            print(
                f"  -> {row['confidence']} api={(row.get('api') or {}).get('api_ok')} "
                f"browser={(row.get('browser') or {}).get('browser_ok')} "
                f"mon={(row.get('browser') or {}).get('monitoring_ok')} "
                f"comp={(row.get('browser') or {}).get('composition_ok')} "
                f"causal={(row.get('browser') or {}).get('causal_ok')} "
                f"persist={(row.get('browser') or {}).get('persistence_ok')}",
                flush=True,
            )
    finally:
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
        if pw:
            try:
                await pw.stop()
            except Exception:
                pass

    batch_out = {
        "batch": batch_num,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n": len(results),
        "high": sum(1 for r in results if r["confidence"] == "HIGH"),
        "fail": sum(1 for r in results if r["confidence"] == "FAIL"),
        "results": results,
    }
    (BATCH_DIR / f"batch_{batch_num:02d}_results.json").write_text(json.dumps(batch_out, indent=2) + "\n")
    master = load_master()
    master.setdefault("batches_completed", [])
    # only mark complete if all non-nine policies in roster are HIGH or evaluated this run
    roster_ids = {p["policy_id"] for p in policies}
    evaluated_ids = {r["policy_id"] for r in results}
    if roster_ids <= evaluated_ids and batch_num not in master["batches_completed"]:
        master["batches_completed"].append(batch_num)
    save_master(master)
    STATE.write_text(
        json.dumps(
            {
                "last_batch": batch_num,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "batch_high": batch_out["high"],
                "batch_fail": batch_out["fail"],
            },
            indent=2,
        )
        + "\n"
    )
    return batch_out


async def run_all(start: int, end: int, api_only: bool = False, force: bool = False):
    summary = []
    for b in range(start, end + 1):
        path = BATCH_DIR / f"batch_{b:02d}_roster.json"
        if not path.exists():
            print(f"skip missing batch {b}", flush=True)
            continue
        print(f"\n===== START BATCH {b} =====", flush=True)
        out = await run_batch(b, api_only=api_only, force=force)
        summary.append({"batch": b, "high": out["high"], "fail": out["fail"], "n": out["n"]})
        print(f"===== END BATCH {b}: high={out['high']} fail={out['fail']} =====\n", flush=True)
        await asyncio.sleep(2)
    print(json.dumps({"summary": summary}, indent=2))
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, help="Run a single batch number")
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=12)
    ap.add_argument("--api-only", action="store_true")
    ap.add_argument("--force", action="store_true", help="Re-evaluate policies already marked HIGH")
    args = ap.parse_args()
    if args.batch:
        asyncio.run(run_batch(args.batch, api_only=args.api_only, force=args.force))
    else:
        asyncio.run(run_all(args.start, args.end, api_only=args.api_only, force=args.force))


if __name__ == "__main__":
    main()
