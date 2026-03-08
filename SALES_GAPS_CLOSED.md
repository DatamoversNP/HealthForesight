# Sales-Blocking Gaps – What We Closed

This doc maps feedback gaps to what’s now in the product so value is obvious in 10 seconds, first-policy ROI is scripted, backfire is visible, and execs get a one-page artifact.

---

## 1. Value not obvious in 10 seconds

**Gap:** Payers see policies, analyses, observations but don’t immediately see: *“Which policies are saving money, which are backfiring, and why?”*

**What we did:**

- **Policy Verdicts screen** (nav: **Policy Verdicts**, path `/policy-verdicts`): One table with **Policy name | Verdict (Saving / At risk / Backfire risk) | Cost impact (PMPM) | Cost % | Confidence | Reason | What to do**. Backfire rows are highlighted; an alert at the top summarizes “X policies show backfire risk.”
- **API:** `GET /api/v1/policy-verdicts` returns one row per policy (latest observation), so the frontend can show exactly this view. This is the “10-second” screen for demos and sales.

**How to use:** Open **Policy Verdicts** first in a demo. Answer: “Green = saving/on track, orange = at risk, red = backfire risk; here’s the reason and what to do.”

---

## 2. First-policy ROI not scripted

**Gap:** No prescribed “first 60-day proof” path (one policy through the lifecycle → single verdict + recommendation).

**What we did:**

- **Demo Day script** (`scripts/run_demo_day.py`) is the prescribed path: one command creates tenant, policies, baseline, predicted impact, and **5 observations** (2 ON_TRACK, 2 AT_RISK, 1 BACKFIRE). That is the “one policy (or small set) through the lifecycle” with verdict + recommendation.
- **First-policy ROI path (prescribed):**
  1. Run `python3 scripts/run_demo_day.py` (or use existing tenant/policies and run with `--skip-seed` after baseline + predicted impact exist).
  2. Open **Policy Verdicts** – you see each policy’s verdict, impact, reason, recommendation.
  3. Click **View evidence** (or go to Observation Analysis and open an observation) to see full comparison and **Download evidence pack** for the one-page artifact.

So “first 60-day proof” = run demo day → Policy Verdicts → one observation’s evidence pack = verdict + recommendation in one place.

---

## 3. Backfire is buried

**Gap:** “Policy backfire” was the killer feature but lived only in behavioral explanation; no clear “Backfire risk” surface for execs.

**What we did:**

- **Policy Verdicts** table: Verdict column shows **“Backfire risk”** (red chip) and **Backfire risk** alert at top when any policy has `verdict_status === BACKFIRE`.
- **Observation Analysis** detail: Each observation shows a verdict chip (On track / At risk / **Backfire risk**) and the verdict reason + recommendation in the header.
- **API:** `policy-verdicts` includes `has_backfire_risk: true` and sorts BACKFIRE first so backfire is impossible to miss.

---

## 4. Executive output is not one page

**Gap:** Execs want savings estimate, confidence band, reason if wrong, decision recommendation—not just tabs and charts.

**What we did:**

- **Evidence pack** (`GET /api/v1/observations/{id}/evidence-pack`) now has an **`executive_summary`** block: verdict, verdict_label, savings_or_cost_impact_pmpm, cost_impact_pct, confidence_pct, one_line_reason, decision_recommendation. One JSON (or exported file) = one page for committee/CFO.
- **Observation Analysis** has **“Download evidence pack”** in the observation detail; the downloaded JSON includes `executive_summary` plus full baseline/prediction/observation/comparison/verdict for audit.

---

## 5. Onboarding and “day one” unclear

**Gap:** “Data onboarding in &lt; 2 weeks” and “path to first value” were not obvious.

**What we did:**

- **Day-one path to first value:**
  1. **Database:** Ensure DB is up and migrations applied: `cd apps/api && alembic upgrade head`.
  2. **Demo data:** From repo root run `python3 scripts/run_demo_day.py`. This creates tenant, policies, baseline, predicted impact, and observations with verdicts.
  3. **First value:** Open **Policy Verdicts** in the UI (or call `GET /api/v1/policy-verdicts`). You immediately see which policies deliver and which backfire.
  4. **Optional:** Ingest your own data (ingestion/pipelines), then run baseline refresh and impact analysis; create observations from analyses. Policy Verdicts will then reflect your data.

So “day one” = run demo day script → open Policy Verdicts = first value in one view. Full onboarding (your files, your policies) is documented in setup/ingestion docs; the script is the minimal path to first value.

---

## 6. Messaging matches “platform” not “answer”

**Gap:** Labels described capabilities (“Policy Impact & Guidance,” “Observation Analysis”) instead of answering “Which policies work? Which backfire? What should we do?”

**What we did:**

- **New nav item:** **“Policy Verdicts”** (path `/policy-verdicts`) with copy that answers the question: “Which policies deliver? Which backfire?” and “One view: policy name, verdict, savings or cost impact, confidence, and recommendation.”
- **Policy Verdicts** is in the top nav group (with Dashboard, Policies) so the “answer” is front and center; capability-focused items (Policy Impact & Guidance, Observation Analysis) remain for deeper workflows.

---

## Summary table

| Gap | Fix |
|-----|-----|
| Value not obvious in 10 sec | **Policy Verdicts** page + `GET /policy-verdicts` |
| First-policy ROI not scripted | **run_demo_day.py** + “Policy Verdicts → evidence pack” path |
| Backfire buried | **Backfire risk** chip + alert on Policy Verdicts; verdict chip on Observation detail |
| Executive output not one page | **executive_summary** in evidence pack + Download evidence pack in UI |
| Onboarding / day one unclear | **Day-one path** in this doc + DEMO_DAY_README |
| Messaging platform not answer | **Policy Verdicts** nav + “Which policies deliver? Which backfire?” copy |

---

## Quick reference

- **One-screen sales view:** **Policy Verdicts** (`/policy-verdicts`) or `GET /api/v1/policy-verdicts`.
- **First 60-day proof:** Run `python3 scripts/run_demo_day.py` → Policy Verdicts → open one observation → Download evidence pack.
- **Day one:** Migrations → `run_demo_day.py` → Policy Verdicts.
- **Backfire:** Policy Verdicts (red chip + alert); Observation Analysis (verdict chip + reason).
- **One-page exec artifact:** Evidence pack JSON with `executive_summary` (or download from Observation Analysis).
