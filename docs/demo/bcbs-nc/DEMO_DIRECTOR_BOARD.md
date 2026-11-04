# DEMO_DIRECTOR_BOARD — HealthForesight × Blue Cross NC

**Working title:** From Medical Policy to Measurable Outcomes  
**Runtime:** 4:45–5:00 hard stop  
**Environment for recording (when READY):** https://data-voyager.vercel.app (or HealthForesight web) → Azure API  
**Hero policy:** Outpatient MRI Prior Authorization (`d403f101-08dd-45c9-ab83-d42e37c62018`)  
**Status:** **READY TO RECORD** — verdicts fix deployed; MRI ON_TRACK; two rehearsals ≤5:00 passed (see DEMO_TEST_RESULTS.md)

---

## Positioning (say this, not “AI dashboard”)

Blue Cross NC stakeholders already have medical policy, UM (including imaging prior review / Carelon-class programs), claims analytics, and financial forecasts. The question HealthForesight creates:

> After a policy is implemented, do we know whether it produced the intended clinical, utilization, and financial outcomes — early enough to act?

Lifecycle on camera (one policy, one evidence trail):

1. Baseline → 2. Predict → 3. Observe → 4. Simulate → 5. Decide

---

## Exact timeline + shot list

| Time | Beat | URL | Mouse / UI | Expected visual | Spoken intent |
|---|---|---|---|---|---|
| 0:00–0:35 | Executive question | `/dashboard/executive` | Hold; point to portfolio pulse only | Executive Dashboard metrics load | Open with decision question — not navigation tour |
| 0:35–1:05 | Select MRI use case | `/policies/workspace/d403f101-08dd-45c9-ab83-d42e37c62018` | Land on Overview; optional Scope/Levers glance (≤10s) | Title **Outpatient MRI Prior Authorization**, PRIOR_AUTH, ACTIVE, description | Objective = appropriate imaging + sustainable cost — not “cut MRI” |
| 1:05–1:45 | Policy-specific baseline | `/baseline-analysis` | Search/filter **Outpatient MRI**; open baseline `9f996021-…` (2024-12-31→2025-12-31) | Policy scope row; claims/members/paid; provider archetypes if visible | “What normal looked like” for the **targeted** population |
| 1:45–2:25 | Predicted impact | `/predicted-impacts` then filter/search MRI **or** workspace Forecasts tab | Open MRI predicted impact | Util ~−14%, cost ~−13%, substitution / response cues | Prospective expectation with uncertainty — not a pledged savings number |
| 2:25–3:20 | Observation (centerpiece) | `/observation-analysis?observation=b227220e-f9e0-45a6-8938-d55aad1fe25d` | Show vs baseline %; mention vs prediction directionally | ON_TRACK; util ~−10%, cost ~−12.5% vs embedded baseline | “Looks favorable vs baseline — still ask: vs what we predicted?” |
| 3:20–4:10 | What-If | Prefer `/whatif/scenarios` → open completed `f73e506f-…` **or** live `/whatif` if verified | One lever / friction change or open completed result cards | Visible impact metrics on completed scenario | Explore alternative **before** changing live UM |
| 4:10–4:40 | Verdict climax | `/policy-verdicts` → search MRI | Click MRI row / View observation | Verdict ≠ UNKNOWN; reason + recommendation | Evidence → recommended next step + accountability |
| 4:40–5:00 | Close | `/dashboard/executive` or branded end card | Stop moving | Calm frame | Invite: evaluate one priority policy category together |

---

## Spoken narration (revised — matches validated data)

### 0:00–0:35 | Executive opening

Every health plan makes medical policy and utilization management decisions intended to improve care appropriateness and manage medical costs.

But after a policy is implemented, how do we know whether it actually delivered the outcomes we expected? Did utilization change for the right reasons? Did costs move with it? Did care shift somewhere else? Were there unintended consequences?

HealthForesight connects those questions into one decision process — baseline, predict, observe, simulate, decide.

### 0:35–1:05 | Policy selection

We start from the executive view, then open a single real-world style use case: outpatient MRI prior authorization — familiar to any plan that runs diagnostic imaging prior review.

Our objective is not simply to reduce imaging volume. It is to understand whether the policy supports appropriate care while delivering sustainable financial outcomes.

*[UI note: say “illustrative demonstration policy aligned to common UM structures — not a copy of Blue Cross NC medical policy text.”]*

### 1:05–1:45 | Baseline

Before evaluating impact, we lock what “normal” looked like for this policy’s population — utilization, allowed and paid cost, membership, and imaging-oriented provider patterns.

That baseline is policy-specific. It is not the whole book of business dressed up as MRI.

### 1:45–2:25 | Prediction

Prospectively, HealthForesight estimates the directional change we should expect — here, roughly mid-teens percent utilization reduction and a similar-direction cost change, with behavioral assumptions including possible substitution into other settings.

That gives leadership a measurable expectation — not an assumed savings line in a slide.

### 2:25–3:20 | Observation

Now the centerpiece: what actually happened relative to the pre-period reference in this observation window.

In this demonstration, utilization and cost are both below that reference — on the order of about ten percent utilization and about twelve percent cost — and the system marks the policy **on track**.

That is useful — and incomplete — until we also ask how results compare with the original prediction and whether substitution or access effects need a closer look. Policy reporting becomes policy intelligence when expected versus observed is visible in one place.

### 3:20–4:10 | What-If

Suppose leadership wants to refine the program. Instead of changing live UM on intuition alone, we examine a scenario — a previously validated run for this recording — to make utilization and cost tradeoffs visible before a decision.

These are projections, not guarantees.

### 4:10–4:40 | Decision

Finally, the verdict layer connects evidence to an assessment and a recommended next step — with a trail back to the observation — so the outcome is not trapped in a deck or an inbox.

### 4:40–5:00 | Close

For Blue Cross NC, the opportunity is to connect medical policy, utilization management, and financial performance in one continuous, evidence-driven process — complementing existing UM and analytics, not replacing them.

Predict the impact. Measure the outcome. Understand the difference. Make a better-informed decision.

We would welcome the opportunity to evaluate one of your priority policy categories and show how HealthForesight could connect existing policy, utilization, and claims data into that measurable decision framework.

That’s HealthForesight — turning medical policy into measurable intelligence.

---

## Fallbacks (if a step fails mid-take)

| Failure | Fallback |
|---|---|
| Executive dashboard slow / wild totals | Narrate the question; do not quote absolute $ impact; move to policy workspace |
| Catalog search hard | Deep-link workspace URL above |
| Wrong baseline selected | Abort take; never use General baseline for MRI |
| Predicted impacts list slow | Use workspace **Forecasts** tab if populated; else API-backed card already cached |
| Live What-If hangs | Open `/whatif/scenarios` completed `f73e506f-ace5-4815-aefb-979367621212` and say “previously generated scenario” |
| Verdicts regresses to UNKNOWN | **Stop recording** — re-check `/policy-verdicts` API; do not fake climax |
| Predicted Impacts search empty | Use Policies → search MRI → Predicted Impact (Stage 3.5) dialog |

---

## Intentionally excluded from the 5-minute video

Persona deep-dives, Scorecards, Cohorts, Ingestion/DQ/Lineage, Admin, Database Viewer, QA, multi-policy packages, elasticity coefficient lectures, builder editing, live claim-count tips.

---

## Recording setup

- Resolution: 1920×1080; browser zoom 100–110%  
- Hide bookmarks; large cursor optional  
- Prefetch: login → executive → MRI workspace → MRI baseline → predicted → observation URL → what-if history → verdicts (after fix)  
- Do not clear cache mid-take  
- Label on-screen if possible: “Illustrative demonstration data”
