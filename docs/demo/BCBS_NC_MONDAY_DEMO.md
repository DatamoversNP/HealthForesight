# BCBS NC Round 2 — Data Voyager demo (A+)

**URL:** https://data-voyager.vercel.app  
**Login:** `demo@example.com` / `Swan@1234`  
**Positioning line (say early):**  
> “This is an illustrative NC-oriented dataset on Data Voyager — not BCBS NC production claims. We’re showing how the decision workflow works with coherent policy stories.”

**Length:** 10–12 minutes live · ~8–10 minutes recorded  
**Do not open:** Admin, raw ROI mega-tiles on the executive summary, failed What-If runs, retired UM Validation policies.

---

## Showcase set (use only these)

| # | Policy | Story | Talking numbers |
|---|--------|--------|-----------------|
| 1 | **Advanced Imaging Comprehensive Control** | ON_TRACK — PA working | ~−14% cost vs baseline, ~−$21 PMPM |
| 2 | **Specialty Drug Comprehensive Management** | ON_TRACK — specialty spend down | ~−20% cost, ~−$29 PMPM |
| 3 | **Elective Surgery Comprehensive Management** | ON_TRACK — elective control | ~−12% cost, ~−$18 PMPM |
| 4 | **Preferred Generic Drug Tier** | ON_TRACK — strong pharmacy win | ~−21% cost, ~−$36 PMPM |
| 5 | **Bundled Payment for Joint Replacement** | **BACKFIRE** — contrast | ~+10% cost, ~+$17 PMPM |
| 6 | **Cardiac Imaging Comprehensive Control** | **BACKFIRE** — contrast | ~+11% cost, ~+$17 PMPM |

Junk (**UM Validation**, duplicate **UM Reduction…**) is **RETIRED** in the API so it should not be the hero path.

---

## Screen flow (click this order)

1. **Login** → lands Policy Owner dashboard  
2. **Policy Verdicts** → point at ON_TRACK vs BACKFIRE mix  
3. **Policies** → open **Advanced Imaging Comprehensive Control**  
4. **Baseline Analysis** → “pre-period / portfolio baseline” (don’t debate zero member-months on unrelated baselines)  
5. **Observation Analysis** → same policy; show utilization/cost vs baseline + behavioral note  
6. **Predicted Impacts** → expected direction before go-live  
7. **What-If Scenarios** — only if a **COMPLETED** scenario exists; otherwise say “precomputed path” and skip live run  
8. **Objectives Health** → portfolio objectives A–F met / gaps  
9. **Policy Verdicts** again → Joint Bundle BACKFIRE as “this is where governance acts”  
10. **Executive or Policy Owner dashboard** → members/claims context only; **skip** 3000% ROI callouts  

---

## Voice-over script (record-ready)

### 0:00–0:40 — Open
“Thanks for joining. I’m going to walk Data Voyager the way a UM or pharmacy leader would use it in North Carolina — from policy catalog, to measured impact, to a verdict you can act on.  
Quick note: the data you’ll see is illustrative and NC-themed for this session, not a pull of BCBS NC production claims.”

### 0:40–1:30 — Verdicts first (hook)
“We start on **Policy Verdicts**, not a wall of charts.  
Green **On track** means observed cost and utilization are at or below baseline.  
**Backfire** means we’re seeing cost or utilization above baseline with early warning signals — that’s where you intervene.  
About two-thirds of this showcase portfolio is on track; the rest is where the product earns its keep.”

### 1:30–3:00 — Imaging win
“Open **Advanced Imaging Comprehensive Control**.  
This is a prior-auth style control on advanced imaging — a familiar NC commercial and MA pressure point.  
Claims volume is real enough to tell a story. Observation shows cost roughly **fourteen percent** below baseline, about **twenty-one dollars PMPM** favorable.  
That’s the ‘policy doing what leadership intended’ narrative.”

### 3:00–4:15 — Specialty + elective (pattern)
“Same pattern on **Specialty Drug Comprehensive Management** — about **twenty percent** cost improvement — and **Elective Surgery Comprehensive Management** — about **twelve percent**.  
You don’t need fifty policies in the meeting. You need a repeatable pattern: baseline → observe → verdict.”

### 4:15–5:15 — Pharmacy punch
“**Preferred Generic Drug Tier** is the clean pharmacy win — roughly **twenty-one percent** cost and about **thirty-six dollars PMPM**.  
If the audience is pharmacy or finance, linger here one beat.”

### 5:15–7:00 — Backfire contrast (client impact)
“Now the uncomfortable slide — **Bundled Payment for Joint Replacement**.  
Verdict is **Backfire**: cost about **ten percent** above baseline, roughly **seventeen dollars PMPM** adverse, with behavioral risk flags.  
This is the point of the product: not a green dashboard, a **governance signal** — revisit the bundle design, leakage, site of care, or coding.  
**Cardiac Imaging Comprehensive Control** shows the same pattern on the imaging side — on-track imaging overall, but this cardiac slice is backfiring. That’s how you prioritize the next work queue.”

### 7:00–8:00 — Predicted impact / objectives
“**Predicted Impacts** answers ‘what did we think would happen before go-live?’  
**Objectives Health** rolls the portfolio into strategic objectives — forecast coverage, observation coverage, backfire watchlist — so execs see progress without living in claims extracts.”

### 8:00–9:00 — Close
“So the operating loop is: **policies → baseline → observation → predicted impact → verdict → objective**.  
What you’d do next with BCBS NC is wire this to your identity and data contracts — the decision workflow is already here.  
Happy to go deeper on any one backfire policy or on integration.”

---

## Recording checklist (Loom / QuickTime + VO)

1. Use **1080p**, browser zoom **100%**, hide bookmarks bar.  
2. Window size ~1440×900; dark/light stay consistent.  
3. Log in once before record; dismiss tours if they pop.  
4. Record **screen + separate mic**; do VO from this script (or record VO in one take while clicking).  
5. Pace: pause 1 second after each navigation so viewers can read chips.  
6. Export title: `Data Voyager — BCBS NC illustrative walkthrough (Round 2)`.  
7. First frame / description: include the illustrative-data disclaimer.

### Good voice tips
- Smile on “on track”; flatten tone on “backfire” (serious, not alarmed).  
- Never invent precision beyond one decimal; prefer “about fourteen percent.”  
- If a page spins >3s, narrate over it: “Loading the observation pack…” — don’t apologize twice.

---

## Rehearsal (night before)

- [ ] Login works  
- [ ] Junk UM policies not starring in catalog  
- [ ] All 6 showcase policies open with verdicts  
- [ ] Worker healthy (only if you plan live What-If)  
- [ ] Full dry run with this script once timed  

## If something breaks live

| Break | Fallback |
|-------|----------|
| What-If fails | Stay on Predicted Impacts + Verdicts |
| Objectives slow | Skip; verdicts already told the story |
| Weird ROI on dashboard | Don’t click it; stay on policy-level PMPM |
| Login hiccup | Hard refresh once; credentials above |
