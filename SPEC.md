# Calculus Homework Bot — Spec (v1)

A phone-first, 30-minute-a-day calculus trainer. It assigns reading from Stewart, serves problems, grades them, adapts to what is weak, and ends every session with a **Daily Integral**.

## 1. Learner and constraints

- **Learner:** has never done precalculus or trigonometry and has not finished algebra 2. Passionate about integrals. Textbook: Stewart, *Calculus: Early Transcendentals*, 8th ed. (physical copy arriving; printed page numbers are the reference).
- **Time budget:** 30 minutes/day.
- **Device:** phone (iPhone vs Android not yet confirmed — build as an installable PWA that works on both).
- **Hosting:** GitHub Pages. Static only: no server, no accounts, no API key in the browser.
- **Out of scope for v1:** notifications/nagging, accounts, live Claude calls, photo-of-handwriting grading, cloud sync.
- **Content rules:**
  - Do not commit Stewart text, figures, PDFs, or exercises to the repo. The app stores only section titles and printed page ranges.
  - All problems are original, written by Claude and verified by SymPy (see section 5).

## 2. The daily session (30 min)

| Min | Block | Detail |
|---|---|---|
| 0-4 | Review | 2 problems from skills that are due for spaced review |
| 4-14 | Read | Today's Stewart pages (from the book). Timer. "Mark read" unlocks the next block |
| 14-23 | Problems | 3-4 new problems tied to today's reading |
| 23-28 | Daily Integral | One integral for the day (section 3) |
| 28-30 | Exit | One-sentence "what I learned" plus a 1-5 confidence rating |

Also support a **Daily Integral only** quick mode for days with no time.

## 3. Daily Integral

Mechanic inspired by dailyintegral.com: one integral per day, a countdown to reset, a streak, an archive for missed days, and a full worked solution. Build our own name, look, and content. Do not copy their branding or puzzles.

- **One integral per local calendar day**, resetting at midnight America/Chicago. Show a countdown to reset.
- **Selection:** the learner's current *integral tier* (below) plus the date picks a problem deterministically (seeded hash), skipping problems already seen.
- **Attempts:** 3 attempts, a hint ladder (hint 1, hint 2, then reveal), then the full worked solution is always shown after the attempt ends.
- **Streak (defaults, easy to change):** a day counts when the attempt is completed (correct or revealed). A separate "solved" stat counts correct answers only. Show both.
- **Archive:** pick any past date and replay. Archive replays never affect the streak. A missed day gets the problem that day's seed yields at the learner's current tier.
- **Integral tiers** (the ladder unlocks with the skill graph):
  - I0: area under lines using geometry (rectangles, triangles, trapezoids)
  - I1: sigma notation and Riemann sums, small n (Stewart 5.1-5.2, Appendix on sigma notation)
  - I2: definite integrals of linear functions and semicircles via geometry (5.2)
  - I3: power-rule antiderivatives and simple definite integrals (4.9, 5.3-5.4)
  - I4: u-substitution (5.5)
  - I5: exponential, logarithmic, and trig integrals
  - I6+: integration by parts, trig integrals, trig substitution, partial fractions (Ch. 7)

## 4. Curriculum and skill graph

Everything is a node in one graph, stored in `data/curriculum.json`.

**Track 0 — ramp (not in Stewart):** finish algebra 2, then precalc/trig essentials. Candidate nodes: linear equations and graphs, systems, factoring and quadratics, polynomials, rational expressions, radicals and exponents, function notation and transformations, exponentials and logs, sigma notation, right-triangle trig, unit circle, essential trig identities. Reading refs come from Stewart's appendices where they match (likely Appendices A, B, D and the sigma-notation appendix; **confirm against the real table of contents**).

**Track 1 — Stewart:** Ch. 1-5 first (about 38 sections; roughly 3-4 months of daily sessions at 2-3 sessions per section), then Ch. 6-11.

**Node schema:**
```json
{
  "id": "limits-intro",
  "title": "The Limit of a Function",
  "track": 1,
  "stewart": { "section": "2.2", "printedPages": [0, 0] },
  "prereqs": ["functions-basics"],
  "integralTier": null,
  "unlockThreshold": 0.7
}
```
`printedPages` come from the printed page numbers in Stewart's table of contents (the project PDFs are the source to extract them from). Verify against the physical book when it arrives.

**Placement diagnostic:** 15-20 questions on first run sets starting mastery and places the learner in the graph. It can be retaken.

**Unlock rule:** a node unlocks when all prerequisites have mastery of at least `unlockThreshold` with at least 5 attempts. Integral-tier skills follow the same rule, so integrals surface as early as the prerequisites allow.

## 5. Problem bank and generation pipeline

Runs **offline**, in Python under `tools/`. The Anthropic API key lives only in the local environment and is never committed.

1. Claude generates problems per skill node as structured JSON.
2. **SymPy verifies every answer key** (derive, integrate, simplify, evaluate). A failed check rejects the problem. No problem is committed unverified.
3. Dedupe by normalized statement and by answer.
4. Commit one JSON file per skill under `data/problems/<node-id>.json`.

**Problem schema:**
```json
{
  "id": "u-sub-0042",
  "skill": "u-substitution",
  "difficulty": 2,
  "statement": "Evaluate \\int 2x\\cos(x^2)\\,dx",
  "checker": "equiv_plus_c",
  "answer": "sin(x^2)",
  "domain": [-2, 2],
  "hints": ["Look for an inner function whose derivative is also present.", "Try u = x^2."],
  "solution": ["Let u = x^2, so du = 2x dx.", "The integral becomes \\int \\cos u \\, du = \\sin u + C.", "Substitute back: \\sin(x^2) + C."],
  "verified": true
}
```
Checker types: `equiv` (expressions agree), `equiv_plus_c` (antiderivatives that differ by a constant), `numeric` (value with tolerance), `choice` (multiple choice for early algebra), `interval`.

Target depth: 40+ verified problems per node for Track 0 and Ch. 1-5 before launch; more for integral tiers.

## 6. Grading (client-side)

- **Input:** MathLive math field (virtual math keyboard on phone). Rendering with KaTeX.
- **Equivalence:** evaluate the learner's expression and the key at about 12 random points in `domain`; agree within relative tolerance 1e-6 wherever both are defined. For `equiv_plus_c`, check that the *difference* is constant across points, so a missing `+ C` is accepted and a wrong constant factor is not.
- **Feedback:** correct/incorrect, hint ladder, then the worked solution. No live Claude calls in v1.

## 7. Adaptive engine

- **Mastery** per skill in [0, 1]. Update: `m = m + 0.3 * (score - m)`, where score is 1 for correct on first attempt, 0.5 if a hint was used, 0 for a miss.
- **Spaced repetition:** a miss schedules a review in 1 day. Each successful review lengthens the interval along 1, 3, 7, 14, 30 days.
- **Tomorrow's selection priority:** (1) reviews that are due, (2) weakest unlocked skills, (3) next unlocked skill in sequence.
- **Difficulty:** stay at the edge of ability. Step difficulty up after 3 consecutive first-try correct answers, down after 2 misses.

## 8. Data (IndexedDB on the phone)

Stores: `settings`, `skillState` (mastery, due date, interval), `attempts` (problem id, answer, correct, hintsUsed, timestamp), `sessions` (date, blocks completed, confidence), `reading` (node id, marked-read date), `daily` (date, problem id, outcome, attempts used).

**Backup:** Export/Import JSON from a settings screen from day one. Browsers can wipe site data, and there is no server copy.

## 9. Tech stack

- Vite + TypeScript, static build deployed to GitHub Pages (GitHub Actions)
- KaTeX (render), MathLive (input), a small expression evaluator for numeric checking
- PWA: manifest + service worker, offline after first load, installable
- Python tooling in `tools/` (Anthropic SDK + SymPy) for the problem pipeline only
- Mobile-first layout, large tap targets, light and dark themes

## 10. Phases and acceptance

1. **Scaffold and curriculum.** PWA shell deploys to Pages. `curriculum.json` built from Stewart's TOC and the Track 0 ramp. *Done when:* app loads on a phone, nodes list with printed page ranges.
2. **Problem pipeline.** Generation + SymPy verification script. First banks: Track 0 core nodes and Stewart 2.1-2.3. *Done when:* a rejected-problem log exists and every committed problem is `verified: true`.
3. **Core loop.** Session timer, KaTeX/MathLive, client grader, hint ladder, local progress. *Done when:* a full 30-minute session can be completed and saved.
4. **Placement, graph, adaptivity.** Diagnostic, mastery, unlocks, spaced repetition.
5. **Daily Integral.** Tiers, deterministic daily pick, streak, archive, worked solutions, countdown. *Done when:* the same date gives the same problem, and archive replays leave the streak unchanged.
6. **Reading gate and polish.** Page-range assignments, mark-read unlock, exit step, export/import, weekly stats screen. Optional: "Add to Google Calendar" link for the daily block.
7. **Later (not v1):** Cloudflare Worker proxy for "explain my miss" and photo grading, cloud sync, reminders.

## 11. Open questions

- iPhone or Android? (affects install steps and keyboard testing)
- App name.
- Confirm the physical book is the 8th edition and that its printed page numbers match the project PDFs.
- Confirm streak rule (completion vs. correct answer only).
