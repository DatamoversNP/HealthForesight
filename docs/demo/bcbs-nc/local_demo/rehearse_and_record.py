#!/usr/bin/env python3
"""
BCBS NC demo rehearsal as a presenter on local Data Voyager (:7868).
1) Off-camera warm of full path
2) On-camera second pass (Playwright video)
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import time
from pathlib import Path

from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:7868"
EMAIL = "admin@healthforesight.com"
PASSWORD = "Swan@1234"
PID = "d403f101-08dd-45c9-ab83-d42e37c62018"
OBS = "b227220e-f9e0-45a6-8938-d55aad1fe25d"
OUT = Path(__file__).resolve().parent
RAW = OUT / "rehearsal_raw"
VIEWPORT = {"width": 1440, "height": 900}

HIDE_CSS = """
.MuiCircularProgress-root, .MuiBackdrop-root, .MuiSkeleton-root,
[role="progressbar"], .MuiLinearProgress-root {
  display: none !important; opacity: 0 !important; visibility: hidden !important;
}
"""

BEATS = [
    ("01_open", "executive", f"{BASE}/dashboard/executive", ["Executive Dashboard", "Active Policies", "Total Cost Impact"]),
    ("02_policy", "policy", f"{BASE}/policies/workspace/{PID}", ["Outpatient MRI Prior Authorization", "PRIOR_AUTH", "ACTIVE"]),
    ("03_baseline", "baseline", f"{BASE}/baseline-analysis", ["Baseline"]),
    ("04_predict", "predict", f"{BASE}/predicted-impacts", ["Predicted"]),
    ("05_observe", "observe", f"{BASE}/observation-analysis", ["Observation"]),
    ("06_whatif", "whatif", f"{BASE}/whatif/scenarios", ["What-If", "scenario"]),
    ("07_verdict", "verdict", f"{BASE}/policy-verdicts", ["policies deliver", "Policy", "Verdict"]),
    ("08_close", "close", f"{BASE}/dashboard/executive", ["Executive Dashboard", "Active Policies"]),
]


async def body_text(page) -> str:
    return await page.locator("body").inner_text()


async def inject_css(page) -> None:
    try:
        await page.add_style_tag(content=HIDE_CSS)
    except Exception:
        pass


async def wait_any(page, needles, timeout_s=60) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            body = await body_text(page)
            low = body.lower()
            if ("sign in" in low and "password" in low) or "/login" in page.url:
                return False
            if any(n.lower() in low for n in needles) and len(body) > 250:
                return True
        except Exception:
            pass
        await asyncio.sleep(0.4)
    return False


async def ensure_session(page) -> None:
    """Re-auth if Azure session bounced us to login mid-demo."""
    if "/login" in page.url or ("sign in" in (await body_text(page)).lower() and "password" in (await body_text(page)).lower()):
        print("    ↻ session lost — re-login", flush=True)
        await login(page)


async def try_fill(page, ph: str, value: str) -> bool:
    loc = page.locator(f'input[placeholder*="{ph}" i]')
    if await loc.count():
        await loc.first.fill("")
        await loc.first.fill(value)
        await asyncio.sleep(1.0)
        return True
    return False


async def login(page) -> None:
    await page.goto(f"{BASE}/login", wait_until="domcontentloaded", timeout=120000)
    await asyncio.sleep(0.8)
    body = (await body_text(page)).lower()
    if "sign in" in body or "/login" in page.url:
        await page.get_by_label("Email").fill(EMAIL)
        await page.get_by_label("Password").fill(PASSWORD)
        await page.get_by_role("button", name="Sign in with email").click()
        await page.wait_for_url(lambda u: "/login" not in str(u), timeout=180000)
    # Prefer executive deep link for demo open
    await page.goto(f"{BASE}/dashboard/executive", wait_until="domcontentloaded", timeout=180000)
    await wait_any(page, ["Executive Dashboard", "Active Policies"], 180)
    await inject_css(page)


async def prepare(page, kind: str, url: str, needles: list[str], hold_s: float) -> dict:
    t0 = time.time()
    note = ""
    await page.goto(url, wait_until="domcontentloaded", timeout=120000)
    if "/login" in page.url:
        await ensure_session(page)
        await page.goto(url, wait_until="domcontentloaded", timeout=120000)
    ok = await wait_any(page, needles, 75)
    if not ok and "/login" in page.url:
        await ensure_session(page)
        await page.goto(url, wait_until="domcontentloaded", timeout=120000)
        ok = await wait_any(page, needles, 75)
    await inject_css(page)

    if kind == "baseline":
        await try_fill(page, "Search", "Outpatient MRI")
        try:
            await wait_any(page, ["Outpatient MRI"], 30)
        except Exception:
            pass
        # click first MRI baseline row if present
        loc = page.get_by_text("Outpatient MRI Prior Authorization", exact=False)
        if await loc.count():
            try:
                await loc.first.click(timeout=3000)
                await asyncio.sleep(2)
                note = "opened MRI baseline row"
            except Exception:
                note = "MRI baseline listed"
    elif kind == "predict":
        await try_fill(page, "Search", "Outpatient MRI")
        await asyncio.sleep(1.5)
        if "Outpatient MRI" not in await body_text(page):
            # catalog fallback
            await page.goto(f"{BASE}/policies", wait_until="domcontentloaded", timeout=180000)
            await wait_any(page, ["Policies", "Policy"], 90)
            await try_fill(page, "Search", "Outpatient MRI Prior Authorization")
            await wait_any(page, ["Outpatient MRI"], 60)
            btn = page.get_by_title("Generate/View Predicted Impact (Stage 3.5)")
            if await btn.count():
                await btn.first.click()
                await asyncio.sleep(2.5)
                note = "predict via catalog dialog"
            else:
                note = "predict list only"
        else:
            note = "predict list filtered MRI"
            ok = True
    elif kind == "observe":
        try:
            field = page.get_by_label("Filter by Policy", exact=False)
            if await field.count():
                await field.click()
                await field.fill("")
                await field.type("Outpatient MRI", delay=25)
                await asyncio.sleep(1.2)
                opt = page.get_by_role("option").filter(has_text="Outpatient MRI")
                if await opt.count():
                    await opt.first.click()
                    await asyncio.sleep(2.5)
            tile = page.get_by_text("Outpatient MRI Prior Authorization", exact=False)
            if await tile.count():
                await tile.first.click()
                await asyncio.sleep(3)
                note = "MRI observation detail open"
            else:
                note = "observation list after filter"
        except Exception as e:
            note = f"observe filter note: {e}"
        # Prefer comparison-ish content
        for tab in ["Overview", "Comparisons", "Vs Baseline", "Baseline"]:
            t = page.get_by_role("tab", name=tab)
            if await t.count():
                try:
                    await t.first.click(timeout=2000)
                    await asyncio.sleep(1.2)
                    break
                except Exception:
                    pass
        body = await body_text(page)
        if "on track" in body.lower() or "ON_TRACK" in body:
            note += "; ON_TRACK visible"
    elif kind == "whatif":
        await page.keyboard.press("Escape")
        await try_fill(page, "Search", "MRI")
        await asyncio.sleep(1.2)
        opens = page.get_by_role("button", name="Open")
        if await opens.count() == 0:
            opens = page.get_by_text("Open", exact=True)
        if await opens.count():
            try:
                await opens.first.click(timeout=3000)
                await asyncio.sleep(3)
                note = "opened scenario run"
            except Exception:
                note = "whatif list MRI filtered"
        else:
            note = "whatif scenarios list"
    elif kind == "verdict":
        loc = page.get_by_label("Search policies", exact=False)
        if await loc.count() == 0:
            loc = page.locator('input[placeholder*="Search" i]')
        if await loc.count():
            await loc.first.fill("Outpatient MRI Prior Authorization")
            await asyncio.sleep(2.5)
        body = await body_text(page)
        if "Saving" in body or "on track" in body.lower() or "ON_TRACK" in body:
            note = "MRI Saving / on track visible"
            ok = True
        elif "Outpatient MRI" in body:
            note = "MRI row visible"
            ok = True
        else:
            note = "verdicts page loaded"
    elif kind in ("executive", "close"):
        note = "executive frame"
        # Give summary time; hide spinner after settle
        await asyncio.sleep(min(8.0, max(2.0, hold_s * 0.25)))
        await inject_css(page)

    await asyncio.sleep(max(1.5, hold_s))
    elapsed = time.time() - t0
    body = await body_text(page)
    checks = {
        "ok": ok,
        "elapsed_s": round(elapsed, 1),
        "note": note,
        "has_mri": "Outpatient MRI" in body or "MRI" in body,
        "has_on_track": "on track" in body.lower() or "ON_TRACK" in body or "Saving" in body,
        "url": page.url,
    }
    return checks


async def walk(page, holds: list[float], label: str) -> list[dict]:
    results = []
    for i, (name, kind, url, needles) in enumerate(BEATS):
        hold = holds[i] if i < len(holds) else 4.0
        print(f"  [{label}] {name} hold={hold:.1f}s …", flush=True)
        r = await prepare(page, kind, url, needles, hold)
        r["beat"] = name
        print(
            f"    → {'OK' if r['ok'] else 'WEAK'} {r['elapsed_s']}s | {r['note']} | "
            f"MRI={r['has_mri']} on_track={r['has_on_track']}",
            flush=True,
        )
        results.append(r)
    return results


async def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    # Presenter-paced holds (enough to read; avoid multi-minute timeouts)
    holds = [6.0, 5.0, 5.0, 5.0, 8.0, 5.0, 6.0, 5.0]
    report: dict = {"base": BASE, "beats": []}

    async with async_playwright() as p:
        # PHASE 1 — warm (no video)
        print("PHASE 1 — off-camera warm", flush=True)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport=VIEWPORT)
        page = await context.new_page()
        await login(page)
        warm = await walk(page, [2.0] * 8, "warm")
        report["warm"] = warm
        await context.close()
        await browser.close()

        # PHASE 2 — record second pass
        print("PHASE 2 — record second pass", flush=True)
        for f in RAW.glob("*"):
            if f.is_file():
                f.unlink()
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport=VIEWPORT,
            record_video_dir=str(RAW),
            record_video_size=VIEWPORT,
        )
        page = await context.new_page()
        await login(page)
        # Start on executive fully ready before "tape" feels live
        await wait_any(page, ["Executive Dashboard", "Active Policies"], 120)
        await inject_css(page)
        await asyncio.sleep(2.0)
        recorded = await walk(page, holds, "record")
        report["record"] = recorded
        await asyncio.sleep(2.0)
        await context.close()
        await browser.close()

    # Find webm
    webs = sorted(RAW.glob("*.webm"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not webs:
        raise SystemExit("No video recorded")
    webm = webs[0]
    mp4 = OUT / "BCBS_NC_Local_Demo_Rehearsal.mp4"
    subprocess.check_call(
        [
            "ffmpeg", "-y", "-i", str(webm),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            "-an",
            str(mp4),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    report["video"] = str(mp4)
    report["webm"] = str(webm)
    # Pass criteria
    rec = report["record"]
    report["pass"] = {
        "all_ok": all(b.get("ok") for b in rec),
        "mri_on_policy": any(b["beat"] == "02_policy" and b.get("has_mri") for b in rec),
        "observe_or_verdict_on_track": any(
            b["beat"] in ("05_observe", "07_verdict") and b.get("has_on_track") for b in rec
        ),
    }
    (OUT / "rehearsal_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"video": report["video"], "pass": report["pass"]}, indent=2), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
