# CLAUDE.md — Integrand (Calculus Homework Bot + study coach)

Read `SPEC.md` first. It is the source of truth for scope, schemas, and phases. This file holds the standing rules.

## What this is

A phone-first PWA hosted on GitHub Pages that runs a 30-minute daily calculus session (review, Stewart reading, problems, Daily Integral, exit) for a learner who has not done precalc/trig and has not finished algebra 2. Textbook: Stewart, *Calculus: Early Transcendentals*, 8th ed.

## Hard rules

- **Static only.** No backend, no server code, no API keys or secrets in the browser bundle or the repo. The Anthropic API key exists only as a local environment variable for `tools/`.
- **No copyrighted book content in the repo.** Never commit Stewart text, figures, exercises, or the project PDFs. Store only section titles and *printed* page numbers. Add `*.pdf` to `.gitignore`.
- **Original problems only.** Never copy or closely paraphrase Stewart exercises (or any other book's).
- **Every problem is SymPy-verified before commit.** If verification fails or is ambiguous, reject it and log it. Never commit a problem with `verified: false`.
- **Printed page numbers, not PDF page indices.** The learner reads from a physical copy. If you read page ranges out of the project PDFs, convert to printed numbers and note the offset in `data/README.md`.
- **Daily reset uses America/Chicago.** Never rely on UTC midnight. All date logic goes through one helper.
- **Archive replays never touch the streak.**
- **No nagging in v1.** No notifications, reminders, or scheduling features unless asked.
- **Math input must work on a phone.** Test layouts at 375px width; use MathLive's virtual keyboard.

## Conventions

- Vite + TypeScript, KaTeX for rendering, MathLive for input, IndexedDB for state.
- Python tooling lives in `tools/` and writes JSON into `data/`. The app only reads `data/`.
- Grading logic is pure functions in `src/grader/` with unit tests. Cover at minimum: `2x+2` vs `2(x+1)`, a missing `+ C`, a wrong constant factor, and domain edges where one side is undefined.
- Keep the curriculum graph in `data/curriculum.json` and problems in `data/problems/<node-id>.json`, matching the schemas in `SPEC.md`.
- Export/Import of all local data must keep working after every schema change. Version the export format.

## Workflow

- Work one phase at a time, in the order in `SPEC.md` section 10. Stop at each phase's acceptance check and summarize what passed.
- Before building the curriculum, extract Stewart's table of contents from the project PDFs rather than relying on memory, and flag any section or appendix whose title or page range looks uncertain.
- When a decision in `SPEC.md` is marked as a default (streak rule, mastery update, spaced-repetition intervals), implement it as configuration, not hard-coded logic, so it is easy to change.
- Ask before adding dependencies beyond the stack in `SPEC.md`.

## Product addendum (v1.1)

Beyond `SPEC.md`, Integrand absorbs the "Retention System" study app: the app **decides what to study** so the learner never has to. Every day opens on one generated assignment (reading pages, review, problems, Daily Integral), a Flowmodoro timer logs real study minutes, progress is tracked per skill and per day, and every node has an original, detailed concept explanation available on demand and after a miss. See `docs/ARCHITECTURE.md` for module contracts and directory ownership.

## Commands

- Install: `npm install`
- Dev server: `npm run dev` (http://localhost:8020)
- Build: `npm run build` (typecheck + vite build to `dist/`)
- Tests: `npm test`
- Python tools: `python3 -m venv tools/.venv && tools/.venv/bin/pip install -r tools/requirements.txt`
- Generate problems: `tools/.venv/bin/python tools/generate_problems.py` (templates; add `--claude` to use the Anthropic API with `ANTHROPIC_API_KEY` set locally)
- Verify problems: `tools/.venv/bin/python tools/verify_problems.py data/problems`
- Deploy: push to `main`; GitHub Actions builds and publishes to GitHub Pages.
