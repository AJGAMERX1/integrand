// Adaptive engine: mastery, difficulty, spaced repetition, unlocks, assignment builder, placement scoring.
// Everything here is pure: no DB, no clock. Dates are YYYY-MM-DD strings (America/Chicago, produced by src/lib/date).
// Every tunable comes from `cfg` (defaults to CONFIG) so tests and future settings can override.
import { CONFIG, type Config } from '../lib/config';
import { addDays, diffDays } from '../lib/date';
import { seededRandom } from '../lib/seed';
import type { Curriculum, CurriculumNode, DiagnosticQuestion, Problem, ReadingRecord, SessionRecord, SkillState } from '../types';

export interface Outcome { correct: boolean; hintsUsed: number; revealed: boolean }

export interface Assignment {
  date: string; focusNodeId: string; reviewNodeIds: string[]; readingNodeId: string | null;
  readingPages: [number, number] | null; readingPrefix?: string; problemNodeIds: string[]; rationale: string[]; estimatedMinutes: number;
}

export interface AssignmentContext { today: string; curriculum: Curriculum; states: Map<string, SkillState>; reading: ReadingRecord[]; sessions: SessionRecord[]; cfg?: Config }

/** ---------- Skill state ---------- */

export function initialSkillState(nodeId: string): SkillState {
  return { nodeId, mastery: 0, attempts: 0, firstTryStreak: 0, missStreak: 0, difficulty: 1, dueDate: null, intervalIndex: 0, lastPracticed: null };
}

function clampDifficulty(d: number, cfg: Config): 1 | 2 | 3 {
  return Math.max(cfg.difficulty.min, Math.min(cfg.difficulty.max, d)) as 1 | 2 | 3;
}

/** A miss is a wrong answer or a reveal; a reveal never counts as correct even if the UI flags it so. */
export function isMiss(outcome: Outcome): boolean {
  return !outcome.correct || outcome.revealed;
}

export function scoreFor(outcome: Outcome, cfg: Config = CONFIG): number {
  if (isMiss(outcome)) return cfg.mastery.scoreMiss;
  return outcome.hintsUsed > 0 ? cfg.mastery.scoreWithHint : cfg.mastery.scoreFirstTry;
}

/**
 * First time a skill reaches the unlock threshold (and has no review scheduled yet), book its first spaced review
 * at intervals[0]. Pure: returns a new state when it schedules, otherwise the same object.
 */
export function scheduleFirstReview(state: SkillState, today: string, cfg: Config = CONFIG): SkillState {
  if (state.dueDate !== null || state.mastery < cfg.unlock.defaultThreshold) return state;
  return { ...state, intervalIndex: 0, dueDate: addDays(today, cfg.spacedRepetition.intervalsDays[0]) };
}

/**
 * Pure mastery / difficulty / spaced-repetition update for one attempt.
 *  - mastery: m += rate * (score - m); score 1 first-try, 0.5 with hint, 0 miss or reveal.
 *  - difficulty: up after N consecutive first-try corrects, down after M consecutive misses (streak resets on step).
 *  - spaced repetition: miss => due tomorrow (index 0). Correct on a due review => next rung of the ladder.
 *    Correct when not due leaves the schedule alone, except that a skill with no review scheduled gets one
 *    (at intervals[0]) the first time its mastery reaches the unlock threshold.
 */
export function applyAttempt(state: SkillState, outcome: Outcome, today: string, cfg: Config = CONFIG): SkillState {
  const miss = isMiss(outcome);
  const firstTry = !miss && outcome.hintsUsed === 0;
  const score = scoreFor(outcome, cfg);
  const mastery = clamp01(state.mastery + cfg.mastery.rate * (score - state.mastery));

  let firstTryStreak = firstTry ? state.firstTryStreak + 1 : 0;
  let missStreak = miss ? state.missStreak + 1 : 0;
  let difficulty: number = state.difficulty;
  if (firstTryStreak >= cfg.difficulty.stepUpAfterFirstTryCorrect) { difficulty += 1; firstTryStreak = 0; }
  if (missStreak >= cfg.difficulty.stepDownAfterMisses) { difficulty -= 1; missStreak = 0; }

  const ladder = cfg.spacedRepetition.intervalsDays;
  let intervalIndex = state.intervalIndex;
  let dueDate = state.dueDate;
  if (miss) {
    intervalIndex = 0;
    dueDate = addDays(today, ladder[0]);
  } else if (dueDate !== null && dueDate <= today) {
    intervalIndex = Math.min(intervalIndex + 1, ladder.length - 1);
    dueDate = addDays(today, ladder[intervalIndex]);
  }

  const next: SkillState = {
    ...state, mastery, attempts: state.attempts + 1, firstTryStreak, missStreak,
    difficulty: clampDifficulty(difficulty, cfg), intervalIndex, dueDate, lastPracticed: today,
  };
  return miss ? next : scheduleFirstReview(next, today, cfg);
}

function clamp01(x: number): number { return Math.max(0, Math.min(1, x)); }

/** ---------- Unlocks ---------- */

function nodeIndex(curriculum: Curriculum): Map<string, CurriculumNode> {
  return new Map(curriculum.nodes.map((n) => [n.id, n]));
}

/** Mastered = mastery at/above the node's own threshold with the minimum attempts (SPEC 4 unlock rule). */
export function isMastered(node: CurriculumNode, state: SkillState | undefined, cfg: Config = CONFIG): boolean {
  if (!state) return false;
  const threshold = node.unlockThreshold ?? cfg.unlock.defaultThreshold;
  return state.mastery >= threshold && state.attempts >= cfg.unlock.minAttempts;
}

export function isUnlocked(nodeId: string, states: Map<string, SkillState>, curriculum: Curriculum, cfg: Config = CONFIG): boolean {
  const byId = nodeIndex(curriculum);
  const node = byId.get(nodeId);
  if (!node) return false;
  return node.prereqs.every((pid) => {
    const prereq = byId.get(pid);
    const st = states.get(pid);
    if (!st) return false;
    const threshold = prereq?.unlockThreshold ?? cfg.unlock.defaultThreshold;
    return st.mastery >= threshold && st.attempts >= cfg.unlock.minAttempts;
  });
}

/** Unlocked nodes in curriculum order. */
export function unlockedNodes(states: Map<string, SkillState>, curriculum: Curriculum, cfg: Config = CONFIG): CurriculumNode[] {
  return curriculum.nodes.filter((n) => isUnlocked(n.id, states, curriculum, cfg));
}

/** Highest Daily Integral tier whose owning node is unlocked; 0 when none so there is always a daily integral. */
export function currentIntegralTier(states: Map<string, SkillState>, curriculum: Curriculum, cfg: Config = CONFIG): number {
  let tier = 0;
  for (const n of unlockedNodes(states, curriculum, cfg)) {
    if (n.integralTier !== null && n.integralTier > tier) tier = n.integralTier;
  }
  return tier;
}

/** ---------- Reviews ---------- */

/** States whose review is due (dueDate <= today), most overdue first, then lowest mastery. */
export function dueReviews(states: Map<string, SkillState>, today: string): SkillState[] {
  return [...states.values()]
    .filter((s) => s.dueDate !== null && s.dueDate <= today)
    .sort((a, b) => (a.dueDate! < b.dueDate! ? -1 : a.dueDate! > b.dueDate! ? 1 : a.mastery - b.mastery || a.nodeId.localeCompare(b.nodeId)));
}

/** ---------- Reading ---------- */

/**
 * Split a node's printed page range into `sessions` roughly equal chunks and return the chunk for the given pass.
 * Once every pass is done, the whole range is assigned again as a skim.
 */
export function readingChunk(node: CurriculumNode, pass: number): [number, number] | null {
  if (!node.stewart) return null;
  const [first, last] = node.stewart.printedPages;
  const total = last - first + 1;
  if (total <= 0) return [first, last];
  const parts = Math.max(1, Math.min(node.sessions || 1, total));
  if (pass < 0 || pass >= parts) return [first, last];
  const start = first + Math.floor((pass * total) / parts);
  const end = first + Math.floor(((pass + 1) * total) / parts) - 1;
  return [start, end];
}

function passesFor(reading: ReadingRecord[], nodeId: string): number {
  let passes = 0;
  for (const r of reading) if (r.nodeId === nodeId && r.passes > passes) passes = r.passes;
  return passes;
}

/** ---------- Assignment ---------- */

function pct(m: number): string { return `${Math.round(m * 100)}%`; }

function formatPages(pages: [number, number], prefix?: string): string {
  const p = prefix ?? '';
  return pages[0] === pages[1] ? `page ${p}${pages[0]}` : `pages ${p}${pages[0]}-${p}${pages[1]}`;
}

/**
 * "Tell me what to study today." Priority (SPEC 7): due reviews, then weakest unlocked skills, then the next
 * unlocked skill in curriculum order. Deterministic for a given input.
 */
export function buildAssignment(ctx: AssignmentContext): Assignment {
  const cfg = ctx.cfg ?? CONFIG;
  const { today, curriculum, states, reading } = ctx;
  const byId = nodeIndex(curriculum);
  const unlocked = unlockedNodes(states, curriculum, cfg);
  const rationale: string[] = [];

  // Focus: first unlocked, not-yet-mastered node; prefer one whose reading is started but unfinished.
  const candidates = unlocked.filter((n) => !isMastered(n, states.get(n.id), cfg));
  const inProgress = candidates.find((n) => { const p = passesFor(reading, n.id); return p > 0 && p < n.sessions; });
  const focus = inProgress ?? candidates[0]
    ?? [...unlocked].sort((a, b) => (states.get(a.id)?.mastery ?? 0) - (states.get(b.id)?.mastery ?? 0))[0]
    ?? curriculum.nodes[0];
  const focusState = states.get(focus.id);

  // Reviews: due first; otherwise the weakest previously practiced unlocked skills (other than the focus).
  const due = dueReviews(states, today).filter((s) => byId.has(s.nodeId));
  let reviewNodeIds = due.slice(0, cfg.session.reviewProblems).map((s) => s.nodeId);
  let reviewsAreDue = reviewNodeIds.length > 0;
  if (!reviewsAreDue) {
    reviewNodeIds = unlocked
      .filter((n) => n.id !== focus.id && (states.get(n.id)?.attempts ?? 0) > 0)
      .sort((a, b) => states.get(a.id)!.mastery - states.get(b.id)!.mastery)
      .slice(0, cfg.session.reviewProblems)
      .map((n) => n.id);
  }
  if (reviewsAreDue) {
    const parts = reviewNodeIds.map((id) => {
      const st = states.get(id)!;
      const overdue = diffDays(st.dueDate!, today);
      const when = overdue <= 0 ? '' : overdue === 1 ? ' (1 day overdue)' : ` (${overdue} days overdue)`;
      return `${byId.get(id)!.title}${when}`;
    });
    rationale.push(parts.length === 1 ? `${parts[0]} is due for review today.` : `${parts.join(' and ')} are due for review today.`);
  } else if (reviewNodeIds.length > 0) {
    const names = reviewNodeIds.map((id) => `${byId.get(id)!.title} (${pct(states.get(id)!.mastery)})`);
    rationale.push(`Nothing is due, so you will warm up on your weakest skill${names.length > 1 ? 's' : ''}: ${names.join(' and ')}.`);
  }

  // Focus sentence.
  if (focusState && focusState.attempts > 0) {
    rationale.push(`Keep building ${focus.title} (${focus.group}): mastery ${pct(focusState.mastery)} after ${focusState.attempts} attempt${focusState.attempts === 1 ? '' : 's'}.`);
  } else {
    rationale.push(`Next up: ${focus.title} (${focus.group}).`);
  }

  // Reading: the focus node's pages split across its sessions, or the concept page for ramp nodes without Stewart pages.
  const passes = passesFor(reading, focus.id);
  const readingPages = readingChunk(focus, passes);
  const readingPrefix = focus.stewart?.pagePrefix;
  if (focus.stewart && readingPages) {
    const parts = Math.max(1, Math.min(focus.sessions || 1, focus.stewart.printedPages[1] - focus.stewart.printedPages[0] + 1));
    const pagesText = formatPages(readingPages, readingPrefix);
    if (passes >= parts) {
      rationale.push(`You have finished all ${parts} reading pass${parts === 1 ? '' : 'es'} of ${focus.stewart.section}; skim ${pagesText} again before the problems.`);
    } else {
      rationale.push(`You have read ${passes} of ${parts} pass${parts === 1 ? '' : 'es'} of ${focus.stewart.section}; today is ${pagesText}.`);
    }
  } else {
    rationale.push(`${focus.title} is ramp material not in Stewart, so read the concept page instead.`);
  }

  // Problems: the focus plus one weakest practiced unlocked skill for interleaving.
  const interleave = unlocked
    .filter((n) => n.id !== focus.id && !reviewNodeIds.includes(n.id) && (states.get(n.id)?.attempts ?? 0) > 0)
    .sort((a, b) => states.get(a.id)!.mastery - states.get(b.id)!.mastery)[0];
  const problemNodeIds = interleave ? [focus.id, interleave.id] : [focus.id];
  if (interleave && rationale.length < 4) {
    rationale.push(`A few ${interleave.title} problems are mixed in to keep it fresh (${pct(states.get(interleave.id)!.mastery)}).`);
  }

  const blocks = cfg.session.blocks;
  const estimatedMinutes = Object.values(blocks).reduce((a, b) => a + b, 0);

  return {
    date: today,
    focusNodeId: focus.id,
    reviewNodeIds,
    readingNodeId: focus.id,
    readingPages,
    ...(readingPrefix ? { readingPrefix } : {}),
    problemNodeIds,
    rationale: rationale.slice(0, 4),
    estimatedMinutes,
  };
}

/**
 * Projection for the coming days: build each day's assignment, then pretend the learner completed it
 * (reading pass marked, focus mastery bumped, reviews answered) and continue. Never mutates the inputs.
 */
export function buildWeekPlan(ctx: AssignmentContext, days = 7): Assignment[] {
  const cfg = ctx.cfg ?? CONFIG;
  const states = new Map<string, SkillState>([...ctx.states].map(([k, v]) => [k, { ...v }]));
  const reading: ReadingRecord[] = ctx.reading.map((r) => ({ ...r }));
  const plan: Assignment[] = [];
  const correct: Outcome = { correct: true, hintsUsed: 0, revealed: false };

  for (let i = 0; i < days; i++) {
    const date = addDays(ctx.today, i);
    const a = buildAssignment({ ...ctx, today: date, states, reading, cfg });
    plan.push(a);

    // Reading pass.
    if (a.readingNodeId) {
      const rec = reading.find((r) => r.nodeId === a.readingNodeId);
      if (rec) { rec.passes += 1; rec.date = date; } else reading.push({ nodeId: a.readingNodeId, date, passes: 1 });
    }
    // Reviews answered correctly (advances the ladder when due).
    for (const id of a.reviewNodeIds) {
      states.set(id, applyAttempt(states.get(id) ?? initialSkillState(id), correct, date, cfg));
    }
    // Focus block: a plausible session's worth of progress.
    const f = states.get(a.focusNodeId) ?? initialSkillState(a.focusNodeId);
    const bumped: SkillState = { ...f, mastery: clamp01(f.mastery + 0.3 * (1 - f.mastery)), attempts: f.attempts + 4, lastPracticed: date };
    states.set(a.focusNodeId, scheduleFirstReview(bumped, date, cfg));
  }
  return plan;
}

/** ---------- Problem selection ---------- */

function shuffle<T>(arr: T[], rng: () => number): T[] {
  const out = arr.slice();
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

/**
 * Up to `count` problems: unseen at the learner's current difficulty first, then unseen at adjacent difficulties,
 * then seen ones (same order of preference). Deterministic for a given rng (default seededRandom(1)).
 */
export function pickProblems(bank: Problem[], state: SkillState, seen: Set<string>, count: number, rng: () => number = seededRandom(1)): Problem[] {
  if (count <= 0 || bank.length === 0) return [];
  const sorted = bank.slice().sort((a, b) => a.id.localeCompare(b.id));
  const buckets: Problem[][] = [];
  for (const wasSeen of [false, true]) {
    for (const distance of [0, 1, 2]) {
      buckets.push(sorted.filter((p) => seen.has(p.id) === wasSeen && Math.abs(p.difficulty - state.difficulty) === distance));
    }
  }
  const out: Problem[] = [];
  for (const bucket of buckets) {
    if (out.length >= count) break;
    for (const p of shuffle(bucket, rng)) {
      if (out.length >= count) break;
      out.push(p);
    }
  }
  return out;
}

/** ---------- Placement ---------- */

/**
 * Turn diagnostic answers into starting skill states. Correct => masteryIfCorrect with the minimum attempts so the
 * node counts as a mastered prerequisite; wrong => masteryIfWrong with one attempt. Nodes with several questions
 * average their scores. A mastered node also lifts its transitive prerequisites to at least masteryIfCorrect,
 * unless the learner answered that prerequisite directly (direct evidence wins). Returns touched nodes only.
 */
export function scorePlacement(results: { question: DiagnosticQuestion; correct: boolean }[], curriculum: Curriculum, cfg: Config = CONFIG): SkillState[] {
  const byId = nodeIndex(curriculum);
  const direct = new Map<string, number[]>();
  for (const r of results) {
    const list = direct.get(r.question.nodeId) ?? [];
    list.push(r.correct ? cfg.placement.masteryIfCorrect : cfg.placement.masteryIfWrong);
    direct.set(r.question.nodeId, list);
  }

  const out = new Map<string, SkillState>();
  const thresholdOf = (id: string) => byId.get(id)?.unlockThreshold ?? cfg.unlock.defaultThreshold;
  for (const [nodeId, scores] of direct) {
    const mastery = scores.reduce((a, b) => a + b, 0) / scores.length;
    const mastered = mastery >= thresholdOf(nodeId);
    out.set(nodeId, { ...initialSkillState(nodeId), mastery, attempts: mastered ? Math.max(cfg.unlock.minAttempts, scores.length) : scores.length });
  }

  // Propagate down the prerequisite graph from every directly mastered node.
  const masteredIds = [...out.values()].filter((s) => s.mastery >= thresholdOf(s.nodeId)).map((s) => s.nodeId);
  const visited = new Set<string>();
  const stack = masteredIds.flatMap((id) => byId.get(id)?.prereqs ?? []);
  while (stack.length) {
    const id = stack.pop()!;
    if (visited.has(id)) continue;
    visited.add(id);
    const node = byId.get(id);
    if (!node) continue;
    if (!direct.has(id)) {
      const prev = out.get(id);
      const mastery = Math.max(prev?.mastery ?? 0, cfg.placement.masteryIfCorrect);
      out.set(id, { ...(prev ?? initialSkillState(id)), mastery, attempts: Math.max(prev?.attempts ?? 0, cfg.unlock.minAttempts) });
    }
    stack.push(...node.prereqs);
  }

  const order = new Map(curriculum.nodes.map((n, i) => [n.id, i]));
  return [...out.values()].sort((a, b) => (order.get(a.nodeId) ?? 1e9) - (order.get(b.nodeId) ?? 1e9));
}

/** ---------- Labels ---------- */

export function masteryLabel(m: number): 'new' | 'learning' | 'solid' | 'mastered' {
  if (m < 0.25) return 'new';
  if (m < 0.6) return 'learning';
  if (m < 0.85) return 'solid';
  return 'mastered';
}
