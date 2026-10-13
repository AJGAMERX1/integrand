# tools/ — the problem pipeline

Everything here runs offline in Python and writes JSON into `data/problems/`. The app never runs this code.

```
tools/
  problemkit.py          shared kit: make_problem, verify, dedupe, write_bank, plain(), ltx(), fmt_num, seeded()
  generate_problems.py   CLI: runs every template module and writes the banks
  verify_problems.py     re-checks every committed bank (schema, verified flag, unique ids, parseable answers)
  templates/
    ramp.py              17 ramp (track 0) nodes: algebra 2, precalc, trig
    daily_low.py         Daily Integral tiers 0-2 (geometry, sigma/Riemann sums, integrals by geometry)
    stewart*.py          Stewart nodes and tiers 3-6 (separate owner)
  rejected.log           one JSON line per rejected problem (see below)
  requirements.txt       sympy, anthropic
```

## Running

```
python3 -m venv tools/.venv && tools/.venv/bin/pip install -r tools/requirements.txt

tools/.venv/bin/python tools/generate_problems.py                  # everything (truncates rejected.log first)
tools/.venv/bin/python tools/generate_problems.py --only sigma-notation
tools/.venv/bin/python tools/generate_problems.py --only tier0     # also accepts daily-tier-0 / tier-0
tools/.venv/bin/python tools/generate_problems.py --list           # which module builds which skill
tools/.venv/bin/python tools/generate_problems.py --claude         # add Claude drafts (needs ANTHROPIC_API_KEY)
tools/.venv/bin/python tools/verify_problems.py data/problems      # must print "0 with errors" before committing
```

Run from the repo root. Output is deterministic: every template seeds its own `random.Random` through
`problemkit.seeded(name)`, so re-running produces byte-identical banks unless a template changed.

The CLI prints a table per bank (`generated`, `deduped`, `verified`, `rejected`) and the most common rejection reasons.
A bank with fewer than 40 verified problems is flagged in the table. A template module whose `build()` raises is
reported and skipped so one broken module does not block the others (exit code 1 in that case).

### Where banks go

`build()` keys are skill ids from `data/curriculum.json` and are written to `data/problems/<skill>.json`. A key of the
form `daily-tier-<n>` is a Daily Integral tier: it is written to `data/problems/daily-tier-<n>.json` with `skill` set to
the node that owns that tier (0 area-by-geometry, 1 areas-and-distances, 2 definite-integral, 3 antiderivatives,
4 substitution, 5 transcendental-integrals, 6 integration-by-parts). Those problems carry `tier` and `tags: ["daily"]`.

## How verification works

A template never writes an answer key directly. It calls `problemkit.make_problem(...)` with a `_verify` spec, and
`problemkit.verify(problem)` re-derives the key with SymPy from that spec. If the stored `answer` does not match what
SymPy derives, the problem is rejected and logged; nothing is ever written with `verified != true`.

The point is independence: the spec describes the *problem data*, not the answer. For "expand (x+3)(x-2)" the spec is
`{"kind": "equiv", "expected": "(x+3)*(x-2)"}` (the unexpanded product), so a template that expanded wrongly is caught.
For "slope through two points" the spec is `{"kind": "numeric", "value": "(y2-y1)/(x2-x1)"}` with the raw coordinates.
For "area under y = 2x+1 from 1 to 4 by geometry" the spec is `{"kind": "definite", ...}` and SymPy integrates.

Verify kinds (see `problemkit.verify`):

| kind | checks |
|---|---|
| `equiv` | answer is equivalent to `expected` (symbolic simplify, then 12-point numeric sampling on `domain`); `equiv_plus_c` compares derivatives |
| `numeric` | answer equals `value` (any SymPy expression string: `sqrt(12)`, `summation(k**2,(k,1,4))`, `Mod(13*pi/4,2*pi)`, `sign(integrate(...))`, ...) |
| `solve` | answer is the unique solution of `lhs = rhs` in x; with `pick`, that root must be among the solutions |
| `evaluate` | answer equals `expr` at `x = at` |
| `definite` | answer equals the definite integral of `integrand` over `[a, b]` |
| `derivative` / `integral` | answer is d/dx of `expr` / differentiates to `integrand` |
| `limit` | answer equals the limit of `expr` as x -> `to` |
| `interval` | answer like `(-inf,3]` equals the solution set of a condition such as `3*x+2<11` or `(x>=0)&(3+2*x<15)`, or a given `Interval(...)` |
| `choice` | the option at index `answer` equals `expected` and every distractor differs; the template supplies `choices_plain` (parseable form of each LaTeX option) |

The answer syntax is the client grader's plain syntax: `+ - * / ^ ( )`, `sin cos tan sec csc cot asin acos atan exp ln
sqrt abs`, constants `pi` and `e`. Use `problemkit.plain(expr)` to produce it and `problemkit.ltx(expr)` for LaTeX in
statements. `fmt_num` renders numbers (`3`, `-1/3`, `2.5`, `sqrt(3)/2`).

After verification, `write_bank` dedupes (by normalized statement, and by answer for `equiv`/`interval` problems) and
strips every field whose name starts with `_`.

## rejected.log format

One JSON object per line, appended by `problemkit.log_reject` (the file is truncated at the start of a full run and kept
on `--only` runs):

```json
{"id": "polynomials-1a2b3c", "skill": "polynomials", "statement": "Expand ...", "answer": "x^2+x-5", "reason": "expected (x+3)*(x-2)"}
```

`reason` is the verifier's description of what it derived (`expected ...`, `value ...`, `solution ...`,
`expected one solution, got [...]`, `exception: ...`, `claude draft malformed: ...`). An empty file after a full run
means every candidate verified.

## Adding a template

1. Create `tools/templates/<name>.py` (names starting with `_` are ignored). It must define
   `build() -> dict[str, list[dict]]` mapping skill ids (or `daily-tier-<n>`) to lists of problems.
2. Build each problem with `problemkit.make_problem(skill, statement, checker, answer, difficulty=, hints=, solution=,
   verify=, ...)`. Exactly two hints, 2-6 solution steps, statements as prose with `$...$` math, a `_verify` spec that
   re-derives the key from the problem data. `ramp.py` has reusable helpers: `run(skill, families, target)` draws from a
   list of `fn(rng) -> problem | None` functions round-robin until `target` distinct candidates exist; `choice(...)`
   shuffles options and fills in `choices_plain`; `ival(Interval)` renders interval answers; `Collector` mirrors the
   dedupe rules so templates know what survives.
3. Seed randomness with `problemkit.seeded(name)` so the output is reproducible.
4. Run `generate_problems.py --only <skill>`, read `rejected.log`, then `verify_problems.py data/problems`.
5. Eyeball a handful of problems in the JSON: readable statement, hints that help without giving it away, a solution a
   learner could follow.

Hard rules (CLAUDE.md): original problems only, never copied or paraphrased from Stewart or any other book; every
problem SymPy-verified; nothing committed with `verified: false`.

## The Claude path

`--claude [DRAFT_DIR]` asks Claude (model `claude-opus-5-5` through the `anthropic` SDK) for a handful of extra problems
per skill, as JSON in the same shape the templates produce (statement, checker, answer, hints, solution, `_verify`). The
drafts are appended to that skill's template output and go through exactly the same `verify` + dedupe + `write_bank`
path, so a draft with a wrong key is rejected and logged like any other problem (reason `claude draft malformed: ...`
when the JSON itself is unusable). Accepted drafts are tagged `claude`.

The API key is read by the SDK from `ANTHROPIC_API_KEY` in the environment and is never written to disk or printed. If
the `anthropic` package is missing or the key is not set, the CLI says so and continues with templates only. Raw drafts
are saved to `DRAFT_DIR` (default `tools/claude_drafts/`) for audit; `--claude-count N` sets how many to request per
skill (default 8).
