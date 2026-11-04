#!/usr/bin/env python3
"""Browser gates for Dec 4 nine-policy demo readiness (local demo7867)."""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:7868"
API = "http://127.0.0.1:7867/api/v1"
EMAIL = "admin@healthforesight.com"
PASSWORD = "Swan@1234"
OUT = Path(__file__).resolve().parent / "dec4_nine_browser"
OUT.mkdir(parents=True, exist_ok=True)

POLICIES = [
    ("mri", "d403f101-08dd-45c9-ab83-d42e37c62018", "Outpatient MRI Prior Authorization"),
    ("mppr", "d0eeb370-df14-4478-8755-dad6c3a35a47", "Multiple Procedure Payment Reduction"),
    ("sos", "d7441dd9-3bfe-405e-ae6c-0377204bbb7e", "Freestanding Imaging Steerage"),
    ("ptp", "58b839b5-b6e0-59e0-9406-d817877c3ce8", "NCCI Procedure-to-Procedure Bundling"),
    ("mue", "e11b049d-fcce-55cc-bcd7-71329038383b", "NCCI Medically Unlikely Units"),
    ("therapy", "f2b8e7f3-1627-5dbe-8d7e-757ce21aa55b", "Outpatient Therapy Coverage and Payment"),
    ("infusion", "11218053-bdc0-569f-a415-fb61c5dcda37", "Infusion Site-of-Care Optimization"),
    ("ncd", "4f8c34e3-015b-509d-90ba-521261464258", "NCD 220.2"),
    ("lcd", "649b4ac8-ca82-5b84-aa87-84834490731a", "LCD L34425"),
]


async def body_text(page):
    return await page.locator("body").inner_text()


async def wait_any(page, needles, timeout_ms=60000):
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        body = await body_text(page)
        low = body.lower()
        for n in needles:
            if n.lower() in low:
                return n, body
        await asyncio.sleep(0.35)
    raise TimeoutError(f"None of {needles}")


async def login(page):
    await page.goto(f"{BASE}/login", wait_until="domcontentloaded", timeout=60000)
    await page.get_by_label("Email").fill(EMAIL)
    await page.get_by_label("Password").fill(PASSWORD)
    await page.get_by_role("button", name="Sign in with email").click()
    await page.wait_for_url(lambda u: "/login" not in str(u), timeout=90000)


async def main():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await login(page)

        # Primary route
        primary = [
            ("executive", f"{BASE}/dashboard/executive", ["Executive Dashboard", "Active Policies"]),
            ("mri_workspace", f"{BASE}/policies/workspace/{POLICIES[0][1]}", ["Outpatient MRI Prior Authorization"]),
            ("mppr_workspace", f"{BASE}/policies/workspace/{POLICIES[1][1]}", ["Multiple Procedure Payment Reduction"]),
            ("sos_workspace", f"{BASE}/policies/workspace/{POLICIES[2][1]}", ["Freestanding Imaging Steerage"]),
            ("medicare", f"{BASE}/medicare-rules", ["Medicare", "NCD", "LCD", "Rules"]),
            ("objectives", f"{BASE}/objectives-health", ["Objectives", "Health", "Guardrail"]),
        ]
        for name, url, needles in primary:
            ok = True
            err = None
            matched = None
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=90000)
                matched, _ = await wait_any(page, needles, 70000)
                await page.screenshot(path=str(OUT / f"primary_{name}.png"), full_page=False)
            except Exception as e:
                ok = False
                err = str(e)[:300]
            results.append({"gate": f"primary:{name}", "ok": ok, "matched": matched, "err": err})
            print(f"primary {name}: ok={ok} match={matched} err={err}", flush=True)

        # All nine workspaces — overview + monitoring tab click if present
        for key, pid, title in POLICIES:
            ok = True
            err = None
            matched = None
            monitoring_ok = None
            try:
                await page.goto(f"{BASE}/policies/workspace/{pid}", wait_until="domcontentloaded", timeout=90000)
                matched, body = await wait_any(page, [title, "Overview", "Monitoring"], 70000)
                # try Monitoring tab
                tab = page.get_by_role("tab", name="Monitoring")
                if await tab.count():
                    await tab.first.click()
                    await asyncio.sleep(1.5)
                    body2 = await body_text(page)
                    monitoring_ok = any(
                        s in body2
                        for s in (
                            "Performance monitoring",
                            "Mechanical",
                            "Predicted impact",
                            "No observation",
                            "FULLY_VALIDATED",
                            "Payer savings",
                            "verdict",
                        )
                    )
                await page.screenshot(path=str(OUT / f"ws_{key}.png"), full_page=False)
                # refresh persistence check
                await page.reload(wait_until="domcontentloaded")
                await wait_any(page, [title, "Overview"], 45000)
            except Exception as e:
                ok = False
                err = str(e)[:300]
            results.append(
                {
                    "gate": f"workspace:{key}",
                    "policy_id": pid,
                    "ok": ok,
                    "matched": matched,
                    "monitoring_ok": monitoring_ok,
                    "err": err,
                }
            )
            print(f"ws {key}: ok={ok} mon={monitoring_ok} err={err}", flush=True)

        await browser.close()

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base": BASE,
        "primary_route_passed": all(r["ok"] for r in results if r["gate"].startswith("primary:")),
        "all_workspaces_passed": all(r["ok"] for r in results if r["gate"].startswith("workspace:")),
        "results": results,
        "screenshots_dir": str(OUT),
    }
    out = Path(__file__).resolve().parent / "DEC4_NINE_BROWSER_GATES.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("primary_route_passed", "all_workspaces_passed")}, indent=2))
    print("wrote", out)
    return 0 if report["primary_route_passed"] and report["all_workspaces_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
