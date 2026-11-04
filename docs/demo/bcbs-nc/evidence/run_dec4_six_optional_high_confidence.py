#!/usr/bin/env python3
"""High-confidence browser rehearsal for the six optional Dec 4 policies."""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:7868"
EMAIL = "admin@healthforesight.com"
PASSWORD = "Swan@1234"
OUT = Path(__file__).resolve().parent / "dec4_six_optional"
OUT.mkdir(parents=True, exist_ok=True)

# Expected visible strings / figures on Monitoring tab (from live APIs, not hardcoded UI constants).
SIX = [
    {
        "key": "ptp",
        "policy_id": "58b839b5-b6e0-59e0-9406-d817877c3ce8",
        "title": "NCCI Procedure-to-Procedure Bundling",
        "must": ["$800", "FULLY_VALIDATED_DEMO", "SYNTHETIC", "$400"],
        "panel": "demo-mechanical-panel",
    },
    {
        "key": "mue",
        "policy_id": "e11b049d-fcce-55cc-bcd7-71329038383b",
        "title": "NCCI Medically Unlikely Units",
        "must": ["$100", "FULLY_VALIDATED_DEMO", "SYNTHETIC", "MUE"],
        "panel": "demo-mechanical-panel",
    },
    {
        "key": "therapy",
        "policy_id": "f2b8e7f3-1627-5dbe-8d7e-757ce21aa55b",
        "title": "Outpatient Therapy Coverage and Payment",
        "must": ["$80", "FULLY_VALIDATED_DEMO", "NOT_SUPPORTED_FOR_THIS_MECHANISM"],
        "panel": "demo-mechanical-panel",
    },
    {
        "key": "infusion",
        "policy_id": "11218053-bdc0-569f-a415-fb61c5dcda37",
        "title": "Infusion Site-of-Care Optimization",
        "must": ["$3,600", "FULLY_VALIDATED_DEMO", "$1,800"],
        "panel": "demo-mechanical-panel",
        # locale may render 3600 without comma
        "must_any_groups": [["$3,600", "$3600"], ["$1,800", "$1800"]],
    },
    {
        "key": "ncd",
        "policy_id": "4f8c34e3-015b-509d-90ba-521261464258",
        "title": "NCD 220.2",
        "must": ["PROVENANCE_ONLY", "N/A", "NCD"],
        "panel": "demo-provenance-panel",
        "forbid": ["Payer savings: $"],
    },
    {
        "key": "lcd",
        "policy_id": "649b4ac8-ca82-5b84-aa87-84834490731a",
        "title": "LCD L34425",
        "must": ["PROVENANCE_ONLY", "orbit", "lumbar"],
        "panel": "demo-provenance-panel",
        "forbid": ["Payer savings: $"],
    },
]


async def body_text(page):
    return await page.locator("body").inner_text()


async def wait_any(page, needles, timeout_ms=70000):
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        body = await body_text(page)
        low = body.lower()
        for n in needles:
            if n.lower() in low:
                return n, body
        await asyncio.sleep(0.3)
    raise TimeoutError(str(needles))


async def login(page):
    await page.goto(f"{BASE}/login", wait_until="domcontentloaded", timeout=60000)
    await page.get_by_label("Email").fill(EMAIL)
    await page.get_by_label("Password").fill(PASSWORD)
    await page.get_by_role("button", name="Sign in with email").click()
    await page.wait_for_url(lambda u: "/login" not in str(u), timeout=90000)


async def open_monitoring(page, policy_id: str, title: str):
    await page.goto(f"{BASE}/policies/workspace/{policy_id}", wait_until="domcontentloaded", timeout=90000)
    await wait_any(page, [title, "Overview", "Monitoring"], 70000)
    # Prefer role tab; fall back to text click
    tab = page.get_by_role("tab", name="Monitoring")
    if await tab.count():
        await tab.first.click()
    else:
        await page.get_by_text("Monitoring", exact=True).first.click()
    # Wait for panel
    deadline = time.time() + 45
    while time.time() < deadline:
        if await page.locator('[data-testid="demo-mechanical-panel"]').count():
            return "mechanical"
        if await page.locator('[data-testid="demo-provenance-panel"]').count():
            return "provenance"
        # also accept visible text while HMR catching up
        body = await body_text(page)
        if "Mechanical / synthetic calculation" in body or "Coverage study — provenance only" in body:
            return "text"
        await asyncio.sleep(0.4)
    raise TimeoutError("Monitoring demo panel not visible")


def check_must(body: str, spec: dict):
    missing = []
    for m in spec.get("must", []):
        if m not in body and m.lower() not in body.lower():
            # case-insensitive fallback for some tokens
            if m.lower() not in body.lower():
                missing.append(m)
    for group in spec.get("must_any_groups", []):
        if not any(g in body for g in group):
            missing.append(f"any_of:{group}")
    forbidden_hit = []
    for f in spec.get("forbid", []):
        if f in body:
            forbidden_hit.append(f)
    return missing, forbidden_hit


async def main():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await login(page)

        for spec in SIX:
            row = {"key": spec["key"], "policy_id": spec["policy_id"], "ok": False}
            try:
                panel_kind = await open_monitoring(page, spec["policy_id"], spec["title"])
                body = await body_text(page)
                missing, forbidden = check_must(body, spec)
                # Composition + Causal tabs soft check
                comp_ok = False
                caus_ok = False
                for tab_name, flag in (("Composition", "comp_ok"), ("Causal Impact", "caus_ok")):
                    t = page.get_by_role("tab", name=tab_name)
                    if await t.count():
                        await t.first.click()
                        await asyncio.sleep(1.2)
                        b2 = await body_text(page)
                        if tab_name == "Composition":
                            comp_ok = "Policy composition" in b2 or "composition" in b2.lower() or "mechanism" in b2.lower()
                        else:
                            caus_ok = "causal" in b2.lower() or "feasibility" in b2.lower() or "descriptive" in b2.lower()
                # reopen monitoring for screenshot
                await open_monitoring(page, spec["policy_id"], spec["title"])
                await page.screenshot(path=str(OUT / f"{spec['key']}_monitoring.png"), full_page=False)
                # refresh persistence
                await page.reload(wait_until="domcontentloaded")
                await open_monitoring(page, spec["policy_id"], spec["title"])
                body2 = await body_text(page)
                missing2, forbidden2 = check_must(body2, spec)

                row.update(
                    {
                        "ok": not missing and not forbidden and not missing2 and not forbidden2,
                        "panel_kind": panel_kind,
                        "missing_first": missing,
                        "forbidden_first": forbidden,
                        "missing_after_refresh": missing2,
                        "forbidden_after_refresh": forbidden2,
                        "composition_tab_ok": comp_ok,
                        "causal_tab_ok": caus_ok,
                        "persistence_ok": not missing2 and not forbidden2,
                    }
                )
            except Exception as e:
                row["err"] = str(e)[:400]
            results.append(row)
            print(json.dumps(row, indent=2), flush=True)

        # What-if / verdicts deep links for mechanical four
        for spec in SIX[:4]:
            ok = True
            err = None
            try:
                await page.goto(
                    f"{BASE}/whatif?policy={spec['policy_id']}",
                    wait_until="domcontentloaded",
                    timeout=90000,
                )
                await asyncio.sleep(2)
                await wait_any(page, ["What-If", "What-if", "scenario", "Simulate", "NOT_SUPPORTED", "policy"], 40000)
                await page.screenshot(path=str(OUT / f"{spec['key']}_whatif.png"), full_page=False)
            except Exception as e:
                ok = False
                err = str(e)[:240]
            results.append({"key": f"{spec['key']}:whatif_page", "ok": ok, "err": err})
            print(f"whatif {spec['key']}: ok={ok} err={err}", flush=True)

        await browser.close()

    passed = all(r.get("ok") for r in results)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base": BASE,
        "high_confidence_six": passed,
        "results": results,
        "screenshots_dir": str(OUT),
    }
    out = Path(__file__).resolve().parent / "DEC4_SIX_OPTIONAL_HIGH_CONFIDENCE.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"high_confidence_six": passed, "n": len(results)}, indent=2))
    print("wrote", out)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
