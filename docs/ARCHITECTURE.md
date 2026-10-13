# Integrand architecture and module contracts

Integrand = the Calculus Homework Bot from `SPEC.md` **plus** the study-coach features of the earlier "Retention System" app
(Flowmodoro timer, study-time logging, spaced review ladder, daily plan, 14-day progress charts, export/import).
The product goal: **the app decides what to study; the learner just studies.** Every day opens on one assignment.

Stack: Vite + TypeScript, no framework, KaTeX (render), MathLive (input), IndexedDB (state), static deploy to GitHub Pages.

## Directory ownership

| Path | Owner | Purpose |
|---|---|---|
| `src/types.ts` | shared (frozen) | all data shapes; add fields only, never rename |
| `src/lib/config.ts` | shared | tunable defaults from SPEC (mastery, SR intervals, streak rule, ...) |
| `src/lib/date.ts` | shared | America/Chicago date helper (`today()`, `addDays`, `msUntilMidnight`, ...) |
| `src/lib/seed.ts` | shared | `hashString`, `seededRandom`, `newId` |
| `src/db/db.ts`, `src/db/state.ts` | shared | IndexedDB stores, versioned export/import, repository helpers |
| `src/data/load.ts` | shared | `curriculum`, `diagnostic`, `problemsFor(nodeId)`, `problemsForTier(t)`, `conceptFor(nodeId)`, `getNode`, `getProblem` |
| `src/ui/dom.ts`, `src/ui/math.ts`, `src/ui/router.ts`, `src/main.ts`, `src/styles.css` | shared | DOM helpers `h()`, `tex()`, `richText()`, `mathInput()`, hash router, app shell, base CSS |
| `src/grader/` | grader agent | pure grading functions + tests |
| `src/engine/` | engine agent | mastery, spaced repetition, unlocks, assignment builder, placement scoring + tests |
| `src/daily/` | engine agent | Daily Integral pick, streak, archive + tests |
| `src/session/` | ui-core agent | 30-minute session state machine |
| `src/ui/today.ts`, `session.ts`, `daily.ts`, `placement.ts`, `timer.ts`, `problemCard.ts` | ui-core agent | Today/assignment, session flow, Daily Integral, placement, flow timer, problem UI |
| `src/ui/map.ts`, `node.ts`, `progress.ts`, `settings.ts`, `concept.ts` | ui-more agent | curriculum map, node page (concept + practice), progress, settings |
| `data/curriculum.json` | done | 97 nodes (17 ramp + 80 Stewart) |
| `data/concepts/*.json` | concepts agent | original explanations per node |
| `data/problems/*.json`, `tools/` | problems agent | SymPy-verified banks and the pipeline |
| `data/diagnostic.json` | concepts agent | placement questions |

Routes (hash): `#/today`, `#/session`, `#/daily`, `#/daily/YYYY-MM-DD` (archive), `#/map`, `#/node/<id>`, `#/progress`, `#/settings`, `#/placement`.
Screen modules export `const xScreen: Screen` with `render(container, params)`; see `src/ui/screens.ts`.

## Grader contract (`src/grader/index.ts`)

```ts
export interface GradeResult { correct: boolean; reason: string; normalizedInput?: string }
/** userInput is LaTeX from MathLive (or plain text). For checker "choice" it is the chosen index as a string. */
export function grade(problem: Problem, userInput: string): GradeResult;
export function latexToPlain(latex: string): string;          // \frac{a}{b} -> (a)/(b), \sin -> sin, \cdot -> *, ^{..} -> ^(..), \pi -> pi, \sqrt{x} -> sqrt(x), \left( -> ( ...
export function parseExpression(src: string): Expr;          // plain syntax: + - * / ^ ( ) implicit multiplication (2x, 3(x+1), x sin(x)), functions sin cos tan sec csc cot asin acos atan arcsin.. sinh cosh tanh exp ln log log10 sqrt abs, constants pi e, variables single letters
export function evaluate(expr: Expr, vars: Record<string, number>): number; // NaN when undefined
export function equivalent(a: string, b: string, opts?: { variable?: string; domain?: [number, number]; plusC?: boolean; samples?: number }): boolean;
export function checkNumeric(user: string, answer: string, tolerance?: number): boolean;  // user may be "1/3", "0.333", "2pi", "sqrt(2)"
export function checkInterval(user: string, answer: string): boolean;                     // "[a,b]", "(a,b]", "(-inf,3)", "(-\infty, 3)"
```
Equivalence: ~12 random points in domain (default [-3,3]), relative tolerance 1e-6 where both sides defined; ignore points where either is NaN/Inf; require at least 4 valid points; `plusC` means the *difference* must be constant. Answers in `data/problems` use the plain syntax above.

## Engine contract (`src/engine/index.ts`)

```ts
export function initialSkillState(nodeId: string): SkillState;
export interface Outcome { correct: boolean; hintsUsed: number; revealed: boolean }
export function applyAttempt(state: SkillState, outcome: Outcome, today: string, cfg?: Config): SkillState; // pure; mastery update, difficulty step, SR due date
export function isUnlocked(nodeId: string, states: Map<string, SkillState>, curriculum: Curriculum, cfg?: Config): boolean;
export function unlockedNodes(states, curriculum, cfg?): CurriculumNode[];
export function dueReviews(states: Map<string, SkillState>, today: string): SkillState[];   // dueDate <= today
export function currentIntegralTier(states, curriculum, cfg?): number;                      // max tier among unlocked tier nodes, min 0
export interface Assignment {
  date: string; focusNodeId: string; reviewNodeIds: string[]; readingNodeId: string | null;
  readingPages: [number, number] | null; readingPrefix?: string; problemNodeIds: string[]; rationale: string[]; estimatedMinutes: number;
}
export function buildAssignment(ctx: { today: string; curriculum: Curriculum; states: Map<string, SkillState>; reading: ReadingRecord[]; sessions: SessionRecord[]; cfg?: Config }): Assignment;
export function buildWeekPlan(ctx, days?: number): Assignment[];   // projection assuming each day is completed
export function pickProblems(bank: Problem[], state: SkillState, seen: Set<string>, count: number, rng?: () => number): Problem[]; // prefer current difficulty, unseen first
export function scorePlacement(results: { question: DiagnosticQuestion; correct: boolean }[], curriculum: Curriculum, cfg?: Config): SkillState[];
export function masteryLabel(m: number): 'new' | 'learning' | 'solid' | 'mastered';
```
Selection priority (SPEC 7): due reviews, then weakest unlocked skills, then next unlocked skill in curriculum order. Reading = the focus node's Stewart pages, split across `node.sessions` passes (`ReadingRecord.passes`). Ramp nodes without Stewart pages get a reading assignment of the concept page instead (`readingNodeId` set, `readingPages` null).

## Daily Integral contract (`src/daily/index.ts`)

```ts
export function pickDaily(date: string, tier: number, candidates: Problem[], seen: Set<string>): Problem | null; // deterministic: seededRandom(hashString(date + ':' + tier)); skip seen unless all seen
export function computeStreak(records: DailyRecord[], today: string, rule: 'completion' | 'solved'): { current: number; best: number; solved: number; completed: number };
// Archive records (isArchive: true) are excluded from streak math entirely.
```

## Problem JSON (data/problems/<node-id>.json)

```json
{ "skill": "<node-id>", "problems": [ { ...Problem } ] }
```
Daily Integral candidates are problems with a `tier` field (0..6); they live in the bank of the node that owns that tier (see `integralTier` in curriculum) or in `data/problems/daily-tier-<n>.json` with `skill` = owning node id.
