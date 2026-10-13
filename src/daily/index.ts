// Daily Integral: deterministic daily pick, streak math, tier labels. Pure functions; dates are YYYY-MM-DD (Chicago).
import { addDays, diffDays } from '../lib/date';
import { hashString, seededRandom } from '../lib/seed';
import type { Curriculum, DailyRecord, Problem } from '../types';

export type StreakRule = 'completion' | 'solved';

export interface StreakStats { current: number; best: number; solved: number; completed: number }

/**
 * Same date + tier (+ same seen set) always yields the same problem. Candidates are sorted by id so the pick does
 * not depend on bank order; unseen problems are preferred, falling back to the whole pool once everything is seen.
 * Returns null only when there are no candidates at all.
 */
export function pickDaily(date: string, tier: number, candidates: Problem[], seen: Set<string>): Problem | null {
  if (candidates.length === 0) return null;
  const sorted = candidates.slice().sort((a, b) => a.id.localeCompare(b.id));
  const unseen = sorted.filter((p) => !seen.has(p.id));
  const pool = unseen.length > 0 ? unseen : sorted;
  const rng = seededRandom(hashString(`${date}:${tier}`));
  return pool[Math.floor(rng() * pool.length)];
}

/** Whether a (non-archive) record counts as a streak day under the rule. */
export function dayCounts(rec: DailyRecord, rule: StreakRule): boolean {
  if (rec.isArchive) return false;
  return rule === 'solved' ? rec.outcome === 'solved' : rec.outcome === 'solved' || rec.outcome === 'revealed';
}

/**
 * Streak math. Archive replays are ignored entirely. The current streak is the run of consecutive counted days
 * ending today, or ending yesterday when today is not yet done (the streak is still alive). `best` is the longest
 * run ever, `solved` counts correct non-archive days, `completed` counts days that satisfied the rule.
 */
export function computeStreak(records: DailyRecord[], today: string, rule: StreakRule): StreakStats {
  const live = records.filter((r) => !r.isArchive);
  const counted = new Set<string>();
  for (const r of live) if (dayCounts(r, rule)) counted.add(r.date);
  const solved = new Set(live.filter((r) => r.outcome === 'solved').map((r) => r.date)).size;

  let current = 0;
  const start = counted.has(today) ? today : counted.has(addDays(today, -1)) ? addDays(today, -1) : null;
  if (start) {
    let d = start;
    while (counted.has(d)) { current += 1; d = addDays(d, -1); }
  }

  let best = 0;
  let run = 0;
  let prev: string | null = null;
  for (const d of [...counted].sort()) {
    run = prev !== null && diffDays(prev, d) === 1 ? run + 1 : 1;
    if (run > best) best = run;
    prev = d;
  }

  return { current, best, solved, completed: counted.size };
}

/** Short learner-facing labels for the integral ladder (SPEC section 3, I0..I6). */
export const TIER_LABELS: readonly string[] = [
  'Area under lines by geometry',
  'Sigma notation and Riemann sums',
  'Definite integrals by geometry',
  'Power-rule antiderivatives',
  'u-substitution',
  'Exponential, log, and trig integrals',
  'Parts, trig substitution, partial fractions',
];

export function tierDescription(tier: number): string {
  const t = Math.max(0, Math.min(TIER_LABELS.length - 1, Math.floor(tier)));
  return TIER_LABELS[t];
}

/** The Daily Integral tier a node unlocks, or null when it unlocks none (or is unknown). */
export function tierForNode(nodeId: string, curriculum: Curriculum): number | null {
  return curriculum.nodes.find((n) => n.id === nodeId)?.integralTier ?? null;
}
