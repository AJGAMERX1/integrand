// Daily Integral: one integral per Chicago day, 3 attempts + hint ladder, worked solution, countdown to reset,
// streak card and a 30-day archive. Archive replays never touch the streak (isArchive records are excluded by
// computeStreak, and we never overwrite a non-archive record with an archive one).
import type { DailyRecord, Problem, Settings } from '../types';
import type { Screen } from './screens';
import { h, clear, toast } from './dom';
import { navigate } from './router';
import { tex, statement } from './math';
import { renderProblem, solutionBlock, type ProblemCardHandle } from './problemCard';
import { curriculum, getProblem, problemsForTier } from '../data/load';
import { getSettings } from '../db/db';
import { loadDaily, loadSkillStates, saveDaily } from '../db/state';
import { addDays, formatCountdown, isValidDate, msUntilMidnight, prettyDate, toLocalDate, today } from '../lib/date';
import { CONFIG } from '../lib/config';
import { hashString } from '../lib/seed';
import { currentIntegralTier } from '../engine';
import { computeStreak, pickDaily } from '../daily';

/** Short labels for the integral tiers (SPEC section 3). */
export const TIER_LABELS: Record<number, string> = {
  0: 'Area under lines by geometry',
  1: 'Sigma notation and Riemann sums',
  2: 'Definite integrals by geometry',
  3: 'Power-rule antiderivatives',
  4: 'u-substitution',
  5: 'Exponential, log and trig integrals',
  6: 'Parts, trig substitution, partial fractions',
};
export function tierLabel(tier: number): string {
  return TIER_LABELS[tier] ?? (tier > 6 ? TIER_LABELS[6] : 'Integrals');
}

export interface DailyOptions {
  /** Inside the session: no archive section, compact streak. */
  embedded?: boolean;
  /** Fires when the puzzle for this date resolves (or when Continue is tapped after it). */
  onDone?(rec: DailyRecord): void;
}
export interface DailyHandle { destroy(): void }

type Streak = { current: number; best: number; solved: number; completed: number };

function safeStreak(records: DailyRecord[], todayStr: string, rule: Settings['streakRule']): Streak {
  try { return computeStreak(records, todayStr, rule); }
  catch (err) { console.error('computeStreak failed', err); return { current: 0, best: 0, solved: 0, completed: 0 }; }
}

function pickFallback(date: string, tier: number, candidates: Problem[], seen: Set<string>): Problem | null {
  if (!candidates.length) return null;
  const unseen = candidates.filter((p) => !seen.has(p.id));
  const pool = unseen.length ? unseen : candidates;
  return pool[hashString(`${date}:${tier}`) % pool.length];
}

/** Renders the Daily Integral for `date` into container. Returns a handle whose destroy() clears the countdown. */
export async function renderDailyIntegral(container: HTMLElement, date: string, opts: DailyOptions = {}): Promise<DailyHandle> {
  const todayStr = today();
  const isArchive = date !== todayStr;
  const timers: number[] = [];
  let card: ProblemCardHandle | null = null;
  const root = h('div', { class: 'daily' });
  container.appendChild(root);

  const [settings, states, allRecords] = await Promise.all([getSettings(), loadSkillStates(), loadDaily()]);
  const records = allRecords;
  let tier = 0;
  try { tier = Math.max(0, currentIntegralTier(states, curriculum)); } catch (err) { console.error('currentIntegralTier failed', err); }

  let existing: DailyRecord | undefined = records.find((r) => r.date === date);
  // Archive replays must never overwrite a record that counts toward the streak (a completed non-archive record).
  // A past day's record left 'incomplete' never counted, so replaying it may be saved as an archive record.
  const canSave = !(isArchive && existing && !existing.isArchive && existing.outcome !== 'incomplete');

  let problem: Problem | undefined = existing ? getProblem(existing.problemId) : undefined;
  let effectiveTier = existing?.tier ?? tier;
  if (!problem) {
    const seen = new Set(records.filter((r) => !r.isArchive && r.date !== date).map((r) => r.problemId));
    let pickTier = tier;
    let candidates = problemsForTier(pickTier);
    while (candidates.length === 0 && pickTier > 0) { pickTier--; candidates = problemsForTier(pickTier); }
    effectiveTier = pickTier;
    if (candidates.length) {
      try { problem = pickDaily(date, pickTier, candidates, seen) ?? undefined; }
      catch (err) { console.error('pickDaily failed', err); problem = pickFallback(date, pickTier, candidates, seen) ?? undefined; }
    }
    // Pin the pick so the same day always shows the same problem (and so it counts as "seen").
    if (problem && canSave && (!existing || existing.problemId !== problem.id)) {
      existing = {
        date, problemId: problem.id, tier: pickTier, outcome: 'incomplete', attemptsUsed: 0, hintsUsed: 0, isArchive, completedAt: null,
      };
      try { await saveDaily(existing); } catch (err) { console.error(err); }
    }
  }

  function draw() {
    card?.destroy(); card = null;
    clear(root);
    for (const t of timers.splice(0)) window.clearInterval(t);

    // Tier line
    const tierRow = h('div', { class: 'row daily-tier' },
      h('span', { class: 'chip int' }, `Tier I${tier}`),
      h('span', { class: 'small muted' }, tierLabel(tier)),
    );
    root.appendChild(tierRow);
    if (effectiveTier !== tier && problem) {
      root.appendChild(h('p', { class: 'small muted' }, `No puzzles written for tier I${tier} yet, so today's comes from tier I${effectiveTier}.`));
    }
    if (isArchive) {
      root.appendChild(h('div', { class: 'card2 card daily-archive-note' },
        h('div', { class: 'row spread' }, h('strong', null, `Archive: ${prettyDate(date)}`), h('a', { href: '#/daily', class: 'small' }, "Today's integral")),
        h('p', { class: 'small muted', style: { margin: 0 } }, 'Replay does not affect your streak.'),
      ));
    }

    if (!problem) {
      root.appendChild(h('div', { class: 'card' },
        h('h3', null, 'No Daily Integral yet'),
        h('p', { class: 'muted' }, 'The integral banks are still being written. Check back soon; your streak is not affected by days with no puzzle.'),
      ));
    } else if (existing && existing.outcome !== 'incomplete') {
      root.appendChild(completedCard(problem, existing));
    } else {
      const host = h('div');
      root.appendChild(host);
      const prob = problem;
      card = renderProblem(host, prob, {
        context: isArchive ? 'archive' : 'daily',
        maxAttempts: CONFIG.daily.attempts,
        heading: isArchive ? `Archive integral, ${prettyDate(date)}` : 'Today’s integral',
        continueLabel: 'Done',
        onDone: (r) => {
          const rec: DailyRecord = {
            date, problemId: prob.id, tier: existing?.tier ?? effectiveTier,
            outcome: r.correct ? 'solved' : 'revealed',
            attemptsUsed: r.attempts, hintsUsed: r.hintsUsed, isArchive, completedAt: Date.now(),
          };
          if (canSave) {
            existing = rec;
            saveDaily(rec).then(() => {
              const i = records.findIndex((x) => x.date === date);
              if (i >= 0) records[i] = rec; else records.push(rec);
              refreshStreak();
            }).catch((err) => { console.error(err); toast('Could not save today’s result.'); });
          }
          opts.onDone?.(rec);
        },
        onContinue: () => draw(),
      });
    }

    // Countdown (today) / streak / archive
    if (!isArchive) root.appendChild(countdownCard());
    root.appendChild(streakCard());
    if (!opts.embedded) root.appendChild(archiveCard());
  }

  function completedCard(p: Problem, rec: DailyRecord): HTMLElement {
    const solved = rec.outcome === 'solved';
    const el = h('div', { class: 'card daily-done' },
      h('div', { class: `result-banner ${solved ? 'good' : 'warn'}` },
        solved ? `Solved${rec.attemptsUsed === 1 && rec.hintsUsed === 0 ? ' on the first try' : ''}.` : 'Completed (solution revealed).'),
      h('p', { class: 'small muted' }, `${rec.attemptsUsed} ${rec.attemptsUsed === 1 ? 'attempt' : 'attempts'}, ${rec.hintsUsed} ${rec.hintsUsed === 1 ? 'hint' : 'hints'}${rec.isArchive ? ', archive replay' : ''}`),
      h('div', { class: 'problem-statement' }, statement(p.statement)),
      solutionBlock(p),
      h('div', { class: 'row' },
        h('a', { class: 'btn ghost small', href: `#/node/${encodeURIComponent(p.skill)}` }, 'Explain this concept'),
        h('button', { type: 'button', class: 'btn ghost small', onclick: () => practiceAgain(p) }, 'Try again (practice)'),
      ),
    );
    if (!isArchive) el.appendChild(h('p', { class: 'small muted', style: { marginTop: '10px' } }, 'Come back tomorrow for a new integral.'));
    return el;
  }

  /** Re-attempt without touching any record. */
  function practiceAgain(p: Problem) {
    card?.destroy(); card = null;
    clear(root);
    for (const t of timers.splice(0)) window.clearInterval(t);
    root.appendChild(h('p', { class: 'small muted' }, 'Practice replay. Nothing is saved.'));
    const host = h('div'); root.appendChild(host);
    card = renderProblem(host, p, {
      context: isArchive ? 'archive' : 'daily', record: false, maxAttempts: CONFIG.daily.attempts,
      heading: 'Practice', continueLabel: 'Back', onDone: () => { /* nothing to save */ }, onContinue: () => draw(),
    });
  }

  function countdownCard(): HTMLElement {
    const clock = h('span', { class: 'mono countdown' }, formatCountdown(msUntilMidnight()));
    const el = h('div', { class: 'card2 card row spread daily-countdown' }, h('span', { class: 'small muted' }, 'Next integral in'), clock);
    const t = window.setInterval(() => {
      const ms = msUntilMidnight();
      clock.textContent = formatCountdown(ms);
      if (ms <= 1000 || today() !== todayStr) { window.clearInterval(t); navigate('daily'); location.reload(); }
    }, 1000);
    timers.push(t);
    return el;
  }

  let streakHost: HTMLElement | null = null;
  function streakCard(): HTMLElement {
    streakHost = h('div', { class: 'card daily-streak' });
    fillStreak(streakHost);
    return streakHost;
  }
  function fillStreak(el: HTMLElement) {
    clear(el);
    const s = safeStreak(records, todayStr, settings.streakRule);
    const stat = (n: number, l: string) => h('div', null, h('div', { class: 'n' }, String(n)), h('div', { class: 'l' }, l));
    el.append(
      h('div', { class: 'row spread' }, h('h3', null, 'Streak'), h('span', { class: 'small muted' }, settings.streakRule === 'solved' ? 'counts solved days' : 'counts completed days')),
      h('div', { class: 'bigstat four' }, stat(s.current, 'current'), stat(s.best, 'best'), stat(s.solved, 'solved'), stat(s.completed, 'completed')),
    );
  }
  function refreshStreak() { if (streakHost) fillStreak(streakHost); }

  function archiveCard(): HTMLElement {
    const createdDate = toLocalDate(new Date(settings.createdAt || Date.now()));
    const byDate = new Map(records.map((r) => [r.date, r]));
    const grid = h('div', { class: 'archive-grid' });
    for (let i = 29; i >= 0; i--) {
      const d = addDays(todayStr, -i);
      const rec = byDate.get(d);
      let status: string;
      if (rec) status = rec.outcome === 'solved' ? 'solved' : rec.outcome === 'revealed' ? 'revealed' : 'started';
      else if (d === todayStr) status = 'open';
      else if (d < createdDate) status = 'none';
      else status = 'missed';
      const cell = h('button', {
        type: 'button', class: `archive-cell ${status}${d === date ? ' active' : ''}`, title: `${prettyDate(d)}: ${status}`,
        onclick: () => navigate(d === todayStr ? 'daily' : `daily/${d}`),
      }, h('span', { class: 'archive-day' }, String(Number(d.slice(8, 10)))), h('span', { class: 'dot' }));
      grid.appendChild(cell);
    }
    const legend = h('div', { class: 'row archive-legend small muted' },
      h('span', null, h('span', { class: 'dot solved' }), ' solved'),
      h('span', null, h('span', { class: 'dot revealed' }), ' revealed'),
      h('span', null, h('span', { class: 'dot missed' }), ' missed'),
      h('span', null, h('span', { class: 'dot none' }), ' not yet'),
    );
    return h('div', { class: 'card daily-archive' },
      h('div', { class: 'row spread' }, h('h3', null, 'Archive'), h('span', { class: 'small muted' }, 'last 30 days')),
      grid, legend,
      h('p', { class: 'small muted', style: { margin: '8px 0 0' } }, 'Tap a day to replay it. Replay does not affect your streak.'),
    );
  }

  draw();

  return {
    destroy() {
      for (const t of timers.splice(0)) window.clearInterval(t);
      card?.destroy(); card = null;
      clear(root); root.remove();
    },
  };
}

let active: DailyHandle | null = null;

export const dailyScreen: Screen = {
  async render(c, params) {
    active?.destroy(); active = null;
    const todayStr = today();
    let date = todayStr;
    if (params[0]) {
      if (!isValidDate(params[0]) || params[0] > todayStr) { navigate('daily'); return; }
      date = params[0];
    }
    c.appendChild(h('h1', null, date === todayStr ? 'Daily Integral' : 'Daily Integral archive'));
    c.appendChild(h('p', { class: 'muted small', style: { marginTop: '-6px' } }, prettyDate(date)));
    active = await renderDailyIntegral(c, date, {});
  },
  unmount() { active?.destroy(); active = null; },
};
