# Integrand

A phone-first, 30-minute-a-day calculus coach built around Stewart, *Calculus: Early Transcendentals* (8th ed.).
It decides what you study today, times it, grades your work, tracks what you have mastered, and explains every concept.
Static PWA on GitHub Pages: no accounts, no server. Your data stays on your phone (export it from Settings).

**Live:** https://ajgamerx1.github.io/integrand/ · install it from the browser's "Add to Home Screen".

## What it does

- **Today** opens on one generated assignment: Stewart pages to read (printed page numbers), reviews that are due, 3-4 problems, and the Daily Integral. A 7-day projection shows what is coming. A Flowmodoro timer logs free study.
- **Session** runs the 30 minutes block by block: review (4) → read (10, "mark read" unlocks the next block) → problems (9) → Daily Integral (5) → one-sentence wrap-up and confidence rating (2). Resumable if you leave.
- **Daily Integral**: one integral per day at your current tier (area by geometry → Riemann sums → … → integration by parts), 3 attempts, two hints, worked solution, countdown to the Chicago-midnight reset, streak, and a 30-day archive to replay missed days (replays never touch the streak).
- **Map**: the 97-node skill graph (17 ramp nodes for algebra 2 / precalc / trig, then Stewart chapters 1-11) with mastery, unlock status, and page ranges. Each node has an original explanation page, free practice, and history.
- **Progress**: hours logged, 14-day minutes chart, accuracy, due reviews, mastery by chapter, recent sessions.
- **Placement**: an 18-question diagnostic sets starting mastery; retake it any time.
- **Adaptive engine**: mastery updates, spaced repetition (1, 3, 7, 14, 30 days), difficulty that steps with your results, prerequisite unlocks. All tunables live in `src/lib/config.ts`.

## Content

- 2,998 original problems across 50 banks, every one verified by SymPy before commit (`tools/`). No Stewart text or exercises are stored; only section titles and printed page numbers.
- 97 original concept explanations (overview, key ideas, worked examples, common mistakes, reading guide).

## Development

```bash
npm install
npm run dev        # http://localhost:8020/integrand/
npm test           # 410 tests: grader, engine, Daily Integral, content sanity
npm run build
```

Problem pipeline (Python):

```bash
python3 -m venv tools/.venv && tools/.venv/bin/pip install -r tools/requirements.txt
tools/.venv/bin/python tools/generate_problems.py          # regenerate all banks from templates
tools/.venv/bin/python tools/verify_problems.py data/problems
```

See `SPEC.md` for scope, `CLAUDE.md` for rules, `docs/ARCHITECTURE.md` for module contracts, `data/README.md` for the page-number convention.
