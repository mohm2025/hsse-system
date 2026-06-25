# ASP → CSP Study Plan

A domain-weighted schedule for a **15-year safety professional** studying **1–2 hrs/day** (~7–14 hrs/week), taking **ASP first, then CSP**.

> **Estimate:** ASP-ready in ~5–6 weeks, CSP-ready ~2–2.5 months after that — roughly **3.5–4 months end to end**, including BCSP application/scheduling gaps. These are planning targets, not guarantees; your `study_log.json` per-domain accuracy is the real readiness signal (see [Readiness bar](#readiness-bar)).

## Daily session shape (1–2 hrs)

| Block | Time | What |
|-------|------|------|
| Review | ~5 min | Skim yesterday's missed questions + explanations |
| Learn | ~30–50 min | Read the day's focus-domain KB material |
| Practice | ~20–40 min | `python quiz_engine.py --interactive`, then read every explanation — right *and* wrong |

The engine auto-shifts weight toward your weak domains, so you don't have to manually rebalance — just keep showing up.

## Where 15 years of experience won't fully carry you

Weight extra time here regardless of how the quizzes feel — these are the classic "I know this in practice but missed it on the test" traps:

- **Math / calculations** (ASP-D1) — formula recall under time pressure (exposure/TLV math, ventilation, noise dose, financials). Pure reps.
- **Legal / regulatory specifics** (ASP-D9) — exact standard numbers, not just how it works on site.
- **Risk & program management, quantitative** (CSP-D2/D3) — decision-analysis framing.

---

## Phase 1 — ASP (~6 weeks)

ASP11 blueprint weights: D1 Math 10% · **D2 Safety Programs 25%** · D3 Ergonomics 8% · D4 Fire 12% · D5 Emergency 10% · D6 IH & Occ Health 12% · D7 Environmental 7% · D8 Training 11% · D9 Legal 5%.

| Week | Primary focus (by weight) | Notes |
|------|---------------------------|-------|
| 1 | **D2 Safety Programs (25%)** + baseline mixed quiz | Biggest domain — anchor here first |
| 2 | **D4 Fire (12%)**, **D6 IH/Occ Health (12%)** | Two of the heaviest after D2 |
| 3 | **D8 Training (11%)**, **D5 Emergency (10%)** | |
| 4 | **D1 Math (10%)** — calculation drills | Daily calc reps; don't skip even if scores look fine |
| 5 | **D3 Ergonomics (8%)**, **D7 Environmental (7%)**, **D9 Legal (5%)** | The "long tail" — quick to cover, easy to neglect |
| 6 | **Full-blueprint mixed quizzes** | Hit the [readiness bar](#readiness-bar); schedule the exam |

## Phase 2 — CSP (~8 weeks)

Begins after you pass ASP. CSP11 weights: **D1 Advanced Application 25%** · **D2 Program Management 25%** · D3 Risk Management 15% · D4 Emergency Management 9% · D5 Environmental 6% · D6 Occ Health & Applied Science 10% · D7 Training 10%.

| Week | Primary focus (by weight) | Notes |
|------|---------------------------|-------|
| 1 | **D1 Advanced Application (25%)** | Scenario/application-heavy |
| 2 | **D2 Program Management (25%)** | |
| 3 | **D3 Risk Management (15%)** — quantitative | The make-or-break CSP domain; give it two weeks |
| 4 | **D3 Risk Management** (continued) | Decision analysis, cost/benefit, quantitative risk |
| 5 | **D6 Occ Health & Applied Science (10%)**, **D7 Training (10%)** | |
| 6 | **D4 Emergency Management (9%)**, **D5 Environmental (6%)** | |
| 7 | **Full-blueprint mixed quizzes** | |
| 8 | **Mixed + timed practice** | Hit the [readiness bar](#readiness-bar); schedule the exam |

---

## Readiness bar

You're ready when, on recent quizzes:

- **≥ 80% in *every* blueprint domain** — not just a good overall average. The exam tests all domains, so one lagging domain is the risk.
- Accuracy has **plateaued** (no domain still climbing steeply — you've stopped finding new gaps).
- Held steady for **~2 weeks**, not a single good day.

Check it any time:

```python
from quiz_engine import load_log
acc = load_log()["domain_accuracy"]
for d, v in sorted(acc.items()):
    print(f"{d}: {round(100*v['correct']/v['total'])}%  (n={v['total']})")
```

Treat 80%/domain as a safety margin — BCSP doesn't publish a fixed passing percentage.

## Important caveat

The engine only quizzes what's in `./kb/`. "Ready by the engine's measure" = ready **on the material you've loaded**. For the estimate above to mean anything, your KB must cover the full ASP11 blueprint (Phase 1), then be swapped/expanded for CSP11 (Phase 2). Loading comprehensive per-domain material is the real gating task — not the engine.
