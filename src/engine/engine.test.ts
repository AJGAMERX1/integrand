import { describe, it, expect } from 'vitest';
import { CONFIG, type Config } from '../lib/config';
import { addDays } from '../lib/date';
import { seededRandom } from '../lib/seed';
import curriculumJson from '../../data/curriculum.json';
import type { Curriculum, CurriculumNode, DiagnosticQuestion, Problem, SkillState } from '../types';
import {
  applyAttempt, buildAssignment, buildWeekPlan, currentIntegralTier, dueReviews, initialSkillState, isMastered,
  isUnlocked, masteryLabel, pickProblems, readingChunk, scorePlacement, unlockedNodes, type Outcome,
} from './index';

const curriculum = curriculumJson as unknown as Curriculum;
const node = (id: string): CurriculumNode => curriculum.nodes.find((n) => n.id === id)!;
const TODAY = '2026-10-13';
const FIRST: Outcome = { correct: true, hintsUsed: 0, revealed: false };
const HINT: Outcome = { correct: true, hintsUsed: 1, revealed: false };
const MISS: Outcome = { correct: false, hintsUsed: 0, revealed: false };
const REVEAL: Outcome = { correct: false, hintsUsed: 2, revealed: true };

function mastered(id: string, extra: Partial<SkillState> = {}): SkillState {
  return { ...initialSkillState(id), mastery: 0.9, attempts: CONFIG.unlock.minAttempts, ...extra };
}
function states(...list: SkillState[]): Map<string, SkillState> {
  return new Map(list.map((s) => [s.nodeId, s]));
}
function withCfg(patch: Record<string, unknown>): Config {
  return { ...CONFIG, ...patch } as unknown as Config;
}
function repeat(s: SkillState, o: Outcome, n: number, day = TODAY): SkillState {
  for (let i = 0; i < n; i++) s = applyAttempt(s, o, day);
  return s;
}

describe('initialSkillState', () => {
  it('starts at zero mastery, difficulty 1, no review scheduled', () => {
    expect(initialSkillState('x')).toEqual({
      nodeId: 'x', mastery: 0, attempts: 0, firstTryStreak: 0, missStreak: 0, difficulty: 1, dueDate: null, intervalIndex: 0, lastPracticed: null,
    });
  });
});

describe('applyAttempt mastery math', () => {
  it('first-try correct moves mastery by rate toward 1', () => {
    const s = applyAttempt(initialSkillState('a'), FIRST, TODAY);
    expect(s.mastery).toBeCloseTo(0.3);
    expect(s.attempts).toBe(1);
    expect(s.lastPracticed).toBe(TODAY);
  });
  it('correct with a hint scores 0.5', () => {
    expect(applyAttempt(initialSkillState('a'), HINT, TODAY).mastery).toBeCloseTo(0.15);
  });
  it('a miss moves mastery toward 0', () => {
    const s = applyAttempt({ ...initialSkillState('a'), mastery: 0.8 }, MISS, TODAY);
    expect(s.mastery).toBeCloseTo(0.56);
  });
  it('a reveal is a miss even when flagged correct', () => {
    const s = applyAttempt({ ...initialSkillState('a'), mastery: 0.8 }, { correct: true, hintsUsed: 2, revealed: true }, TODAY);
    expect(s.mastery).toBeCloseTo(0.56);
    expect(s.missStreak).toBe(1);
  });
  it('is pure and honours a custom rate', () => {
    const before = initialSkillState('a');
    const after = applyAttempt(before, FIRST, TODAY, withCfg({ mastery: { ...CONFIG.mastery, rate: 0.5 } }));
    expect(before.mastery).toBe(0);
    expect(after.mastery).toBeCloseTo(0.5);
  });
});

describe('difficulty stepping', () => {
  it('steps up after 3 consecutive first-try corrects and resets the streak', () => {
    let s = repeat(initialSkillState('a'), FIRST, 2);
    expect(s.difficulty).toBe(1);
    expect(s.firstTryStreak).toBe(2);
    s = applyAttempt(s, FIRST, TODAY);
    expect(s.difficulty).toBe(2);
    expect(s.firstTryStreak).toBe(0);
  });
  it('a hinted answer breaks the first-try streak', () => {
    let s = repeat(initialSkillState('a'), FIRST, 2);
    s = applyAttempt(s, HINT, TODAY);
    expect(s.firstTryStreak).toBe(0);
    expect(s.difficulty).toBe(1);
  });
  it('steps down after 2 misses and clamps at the minimum', () => {
    let s = repeat({ ...initialSkillState('a'), difficulty: 2 }, MISS, 2);
    expect(s.difficulty).toBe(1);
    expect(s.missStreak).toBe(0);
    s = repeat(s, REVEAL, 2);
    expect(s.difficulty).toBe(1);
  });
  it('clamps at the maximum', () => {
    const s = repeat({ ...initialSkillState('a'), difficulty: 3 }, FIRST, 6);
    expect(s.difficulty).toBe(3);
  });
  it('respects a custom step-up count', () => {
    const cfg = withCfg({ difficulty: { ...CONFIG.difficulty, stepUpAfterFirstTryCorrect: 1 } });
    expect(applyAttempt(initialSkillState('a'), FIRST, TODAY, cfg).difficulty).toBe(2);
  });
});

describe('spaced repetition ladder', () => {
  it('a miss schedules a review tomorrow at index 0', () => {
    const s = applyAttempt({ ...initialSkillState('a'), intervalIndex: 3, dueDate: '2026-12-01' }, MISS, TODAY);
    expect(s.intervalIndex).toBe(0);
    expect(s.dueDate).toBe(addDays(TODAY, 1));
  });
  it('successful reviews climb 1, 3, 7, 14, 30 and cap at 30', () => {
    let s = applyAttempt(initialSkillState('a'), MISS, TODAY);
    let day = TODAY;
    const expected = [3, 7, 14, 30, 30, 30];
    for (const gap of expected) {
      day = s.dueDate!;
      s = applyAttempt(s, FIRST, day);
      expect(s.dueDate).toBe(addDays(day, gap));
    }
    expect(s.intervalIndex).toBe(4);
  });
  it('a miss mid-ladder resets to 1 day', () => {
    let s = applyAttempt(initialSkillState('a'), MISS, TODAY);
    s = applyAttempt(s, FIRST, s.dueDate!); // -> 3 days
    s = applyAttempt(s, FIRST, s.dueDate!); // -> 7 days
    expect(s.intervalIndex).toBe(2);
    const missDay = s.dueDate!;
    s = applyAttempt(s, MISS, missDay);
    expect(s.intervalIndex).toBe(0);
    expect(s.dueDate).toBe(addDays(missDay, 1));
  });
  it('a correct answer when not yet due leaves the schedule alone', () => {
    const s = applyAttempt({ ...initialSkillState('a'), mastery: 0.9, intervalIndex: 2, dueDate: '2026-11-01' }, FIRST, TODAY);
    expect(s.intervalIndex).toBe(2);
    expect(s.dueDate).toBe('2026-11-01');
  });
  it('an overdue review still counts as a review', () => {
    const s = applyAttempt({ ...initialSkillState('a'), intervalIndex: 0, dueDate: '2026-10-01' }, HINT, TODAY);
    expect(s.intervalIndex).toBe(1);
    expect(s.dueDate).toBe(addDays(TODAY, 3));
  });
  it('schedules the first review when mastery first reaches the unlock threshold', () => {
    let s = initialSkillState('a');
    for (let i = 0; i < 10 && s.dueDate === null; i++) s = applyAttempt(s, FIRST, TODAY);
    expect(s.mastery).toBeGreaterThanOrEqual(CONFIG.unlock.defaultThreshold);
    expect(s.dueDate).toBe(addDays(TODAY, 1));
    expect(s.intervalIndex).toBe(0);
  });
});

describe('unlock rule', () => {
  it('nodes with no prereqs are unlocked on an empty state', () => {
    expect(isUnlocked('numbers-and-inequalities', new Map(), curriculum)).toBe(true);
    expect(isUnlocked('linear-equations', new Map(), curriculum)).toBe(false);
  });
  it('requires mastery at the prereq threshold AND the 5-attempt minimum', () => {
    expect(isUnlocked('linear-equations', states(mastered('numbers-and-inequalities', { attempts: 4 })), curriculum)).toBe(false);
    expect(isUnlocked('linear-equations', states(mastered('numbers-and-inequalities', { mastery: 0.69 })), curriculum)).toBe(false);
    expect(isUnlocked('linear-equations', states(mastered('numbers-and-inequalities', { mastery: 0.7 })), curriculum)).toBe(true);
  });
  it('requires every prereq', () => {
    expect(isUnlocked('function-notation', states(mastered('linear-equations')), curriculum)).toBe(false);
    expect(isUnlocked('function-notation', states(mastered('linear-equations'), mastered('factoring-and-quadratics')), curriculum)).toBe(true);
  });
  it('honours a custom minAttempts', () => {
    const cfg = withCfg({ unlock: { ...CONFIG.unlock, minAttempts: 1 } });
    expect(isUnlocked('linear-equations', states(mastered('numbers-and-inequalities', { attempts: 1 })), curriculum, cfg)).toBe(true);
  });
  it('unknown nodes are never unlocked', () => {
    expect(isUnlocked('nope', new Map(), curriculum)).toBe(false);
  });
  it('unlockedNodes keeps curriculum order', () => {
    const ids = unlockedNodes(states(mastered('numbers-and-inequalities')), curriculum).map((n) => n.id);
    expect(ids).toEqual(['numbers-and-inequalities', 'exponents-and-radicals', 'linear-equations']);
  });
  it('isMastered uses the node threshold and the attempt minimum', () => {
    const n = node('numbers-and-inequalities');
    expect(isMastered(n, undefined)).toBe(false);
    expect(isMastered(n, mastered(n.id))).toBe(true);
    expect(isMastered(n, mastered(n.id, { attempts: 2 }))).toBe(false);
  });
});

describe('currentIntegralTier', () => {
  it('is 0 on an empty state', () => {
    expect(currentIntegralTier(new Map(), curriculum)).toBe(0);
  });
  it('stays 0 once area-by-geometry unlocks (linear-equations mastered)', () => {
    const st = states(mastered('numbers-and-inequalities'), mastered('linear-equations'));
    expect(unlockedNodes(st, curriculum).some((n) => n.id === 'area-by-geometry')).toBe(true);
    expect(currentIntegralTier(st, curriculum)).toBe(0);
  });
  it('takes the max unlocked tier', () => {
    const st = states(mastered('sigma-notation'), mastered('area-by-geometry'), mastered('functions-basics'));
    expect(currentIntegralTier(st, curriculum)).toBe(1);
    st.set('areas-and-distances', mastered('areas-and-distances'));
    st.set('limits-at-infinity', mastered('limits-at-infinity'));
    expect(currentIntegralTier(st, curriculum)).toBe(2);
  });
});

describe('dueReviews', () => {
  it('returns only due states, most overdue first then lowest mastery', () => {
    const st = states(
      { ...initialSkillState('a'), mastery: 0.5, dueDate: '2026-10-13' },
      { ...initialSkillState('b'), mastery: 0.2, dueDate: '2026-10-10' },
      { ...initialSkillState('c'), mastery: 0.1, dueDate: '2026-10-13' },
      { ...initialSkillState('d'), mastery: 0.1, dueDate: '2026-10-14' },
      { ...initialSkillState('e'), mastery: 0.1, dueDate: null },
    );
    expect(dueReviews(st, TODAY).map((s) => s.nodeId)).toEqual(['b', 'c', 'a']);
  });
});

describe('readingChunk', () => {
  it('splits a range into roughly equal chunks per pass and skims the whole range after', () => {
    const n = node('numbers-and-inequalities'); // A2-A9, 2 sessions
    expect(readingChunk(n, 0)).toEqual([2, 5]);
    expect(readingChunk(n, 1)).toEqual([6, 9]);
    expect(readingChunk(n, 2)).toEqual([2, 9]);
  });
  it('three passes cover the range without gaps or overlaps', () => {
    const n = node('functions-basics'); // 10-22, 3 sessions
    const chunks = [0, 1, 2].map((p) => readingChunk(n, p)!);
    expect(chunks[0][0]).toBe(10);
    expect(chunks[2][1]).toBe(22);
    expect(chunks[1][0]).toBe(chunks[0][1] + 1);
    expect(chunks[2][0]).toBe(chunks[1][1] + 1);
  });
  it('is null for ramp nodes without Stewart pages', () => {
    expect(readingChunk(node('exponents-and-radicals'), 0)).toBeNull();
  });
});

describe('buildAssignment', () => {
  const base = { today: TODAY, curriculum, sessions: [] as never[] };

  it('on an empty state focuses numbers-and-inequalities with its appendix pages', () => {
    const a = buildAssignment({ ...base, states: new Map(), reading: [] });
    expect(a.date).toBe(TODAY);
    expect(a.focusNodeId).toBe('numbers-and-inequalities');
    expect(a.readingNodeId).toBe('numbers-and-inequalities');
    expect(a.readingPages).toEqual([2, 5]);
    expect(a.readingPrefix).toBe('A');
    expect(a.reviewNodeIds).toEqual([]);
    expect(a.problemNodeIds).toEqual(['numbers-and-inequalities']);
    expect(a.estimatedMinutes).toBe(30);
    expect(a.rationale.length).toBeGreaterThanOrEqual(2);
    expect(a.rationale.length).toBeLessThanOrEqual(4);
    expect(a.rationale.join(' ')).toContain('Next up');
  });

  it('continues a node whose reading passes are started but unfinished', () => {
    const st = states(mastered('numbers-and-inequalities'));
    // Both exponents-and-radicals and linear-equations are unlocked; linear-equations has a pass started.
    const a = buildAssignment({ ...base, states: st, reading: [{ nodeId: 'linear-equations', date: '2026-10-12', passes: 1 }] });
    expect(a.focusNodeId).toBe('linear-equations');
    expect(a.readingPages).toEqual([13, 15]);
    expect(a.rationale.join(' ')).toContain('read 1 of 2 passes of App. B');
  });

  it('assigns the whole range as a skim once all passes are done', () => {
    const a = buildAssignment({ ...base, states: new Map(), reading: [{ nodeId: 'numbers-and-inequalities', date: '2026-10-12', passes: 2 }] });
    expect(a.focusNodeId).toBe('numbers-and-inequalities');
    expect(a.readingPages).toEqual([2, 9]);
    expect(a.rationale.join(' ')).toMatch(/skim/);
  });

  it('ramp nodes without Stewart pages get the concept page (readingPages null)', () => {
    const st = states(mastered('numbers-and-inequalities'));
    const a = buildAssignment({ ...base, states: st, reading: [] });
    expect(a.focusNodeId).toBe('exponents-and-radicals');
    expect(a.readingNodeId).toBe('exponents-and-radicals');
    expect(a.readingPages).toBeNull();
    expect(a.readingPrefix).toBeUndefined();
    expect(a.rationale.join(' ')).toMatch(/concept page/);
  });

  it('due reviews take priority and are explained with overdue days', () => {
    const st = states(
      mastered('numbers-and-inequalities', { dueDate: '2026-10-10' }),
      mastered('linear-equations', { mastery: 0.75, dueDate: '2026-10-13' }),
    );
    const a = buildAssignment({ ...base, states: st, reading: [] });
    expect(a.reviewNodeIds).toEqual(['numbers-and-inequalities', 'linear-equations']);
    expect(a.rationale[0]).toContain('Numbers, Inequalities, and Absolute Value (3 days overdue)');
    expect(a.rationale[0]).toContain('Linear Equations and Lines');
    expect(a.rationale[0]).toMatch(/are due for review today\.$/);
  });

  it('caps reviews at cfg.session.reviewProblems', () => {
    const st = states(
      mastered('numbers-and-inequalities', { dueDate: '2026-10-10' }),
      mastered('linear-equations', { dueDate: '2026-10-11' }),
      mastered('exponents-and-radicals', { dueDate: '2026-10-12' }),
    );
    const a = buildAssignment({ ...base, states: st, reading: [] });
    expect(a.reviewNodeIds).toEqual(['numbers-and-inequalities', 'linear-equations']);
    const one = buildAssignment({ ...base, states: st, reading: [], cfg: withCfg({ session: { ...CONFIG.session, reviewProblems: 1 } }) });
    expect(one.reviewNodeIds).toEqual(['numbers-and-inequalities']);
  });

  it('falls back to the weakest practiced unlocked skills when nothing is due', () => {
    const st = states(
      mastered('numbers-and-inequalities'),
      mastered('linear-equations', { mastery: 0.8 }),
      { ...initialSkillState('exponents-and-radicals'), mastery: 0.3, attempts: 2 },
    );
    const a = buildAssignment({ ...base, states: st, reading: [] });
    expect(a.focusNodeId).toBe('exponents-and-radicals');
    expect(a.reviewNodeIds).not.toContain('exponents-and-radicals');
    expect(a.reviewNodeIds).toEqual(['linear-equations', 'numbers-and-inequalities']);
    expect(a.rationale.join(' ')).toMatch(/Nothing is due/);
  });

  it('interleaves one weakest other practiced skill into the problems block, focus first', () => {
    const st = states(
      mastered('numbers-and-inequalities', { mastery: 0.72 }),
      mastered('linear-equations', { mastery: 0.95 }),
      mastered('exponents-and-radicals', { mastery: 0.8 }),
      { ...initialSkillState('polynomials'), mastery: 0.1, attempts: 1 },
    );
    const a = buildAssignment({ ...base, states: st, reading: [] });
    // systems-of-equations is the first unlocked, unmastered node in curriculum order.
    expect(a.focusNodeId).toBe('systems-of-equations');
    // Nothing due: weakest practiced skills fill the review slots...
    expect(a.reviewNodeIds).toEqual(['polynomials', 'numbers-and-inequalities']);
    // ...and the weakest remaining practiced skill is interleaved after the focus.
    expect(a.problemNodeIds).toEqual(['systems-of-equations', 'exponents-and-radicals']);
    expect(a.rationale.join(' ')).toMatch(/mixed in/);
  });

  it('is deterministic', () => {
    const st = states(mastered('numbers-and-inequalities', { dueDate: '2026-10-12' }));
    const a = buildAssignment({ ...base, states: st, reading: [] });
    const b = buildAssignment({ ...base, states: st, reading: [] });
    expect(a).toEqual(b);
  });

  it('sums the block minutes from config', () => {
    const cfg = withCfg({ session: { ...CONFIG.session, blocks: { review: 1, read: 2, problems: 3, daily: 4, exit: 5 } } });
    expect(buildAssignment({ ...base, states: new Map(), reading: [], cfg }).estimatedMinutes).toBe(15);
  });
});

describe('buildWeekPlan', () => {
  it('returns one assignment per day with consecutive dates', () => {
    const plan = buildWeekPlan({ today: TODAY, curriculum, states: new Map(), reading: [], sessions: [] });
    expect(plan).toHaveLength(7);
    expect(plan.map((a) => a.date)).toEqual([0, 1, 2, 3, 4, 5, 6].map((i) => addDays(TODAY, i)));
    expect(buildWeekPlan({ today: TODAY, curriculum, states: new Map(), reading: [], sessions: [] }, 3)).toHaveLength(3);
  });
  it('advances through reading passes and nodes as days are completed', () => {
    const plan = buildWeekPlan({ today: TODAY, curriculum, states: new Map(), reading: [], sessions: [] });
    expect(plan[0].readingPages).toEqual([2, 5]);
    expect(plan[1].readingPages).toEqual([6, 9]);
    const focuses = new Set(plan.map((a) => a.focusNodeId));
    expect(focuses.size).toBeGreaterThan(1);
  });
  it('does not mutate the input maps or records', () => {
    const st = states({ ...initialSkillState('numbers-and-inequalities'), mastery: 0.4, attempts: 2 });
    const reading = [{ nodeId: 'numbers-and-inequalities', date: '2026-10-12', passes: 1 }];
    const snapshotState = JSON.stringify([...st]);
    const snapshotReading = JSON.stringify(reading);
    buildWeekPlan({ today: TODAY, curriculum, states: st, reading, sessions: [] });
    expect(JSON.stringify([...st])).toBe(snapshotState);
    expect(JSON.stringify(reading)).toBe(snapshotReading);
    expect(st.size).toBe(1);
  });
});

describe('pickProblems', () => {
  const mk = (id: string, difficulty: 1 | 2 | 3): Problem => ({
    id, skill: 's', difficulty, statement: '', checker: 'numeric', answer: '1', hints: [], solution: [], verified: true,
  });
  const bank = [mk('a1', 1), mk('a2', 1), mk('b1', 2), mk('b2', 2), mk('c1', 3), mk('c2', 3)];

  it('prefers unseen problems at the current difficulty', () => {
    const out = pickProblems(bank, { ...initialSkillState('s'), difficulty: 2 }, new Set(), 2);
    expect(out.map((p) => p.id).sort()).toEqual(['b1', 'b2']);
  });
  it('then adjacent difficulties, then seen ones', () => {
    const out = pickProblems(bank, { ...initialSkillState('s'), difficulty: 1 }, new Set(['a1']), 3);
    expect(out[0].id).toBe('a2');
    expect(out.slice(1).map((p) => p.id).sort()).toEqual(['b1', 'b2']);
    const all = pickProblems(bank, { ...initialSkillState('s'), difficulty: 3 }, new Set(['c1', 'c2', 'b1', 'b2', 'a1', 'a2']), 2);
    expect(all.map((p) => p.id).sort()).toEqual(['c1', 'c2']);
  });
  it('is deterministic for the same rng seed and bank order independent', () => {
    const a = pickProblems(bank, initialSkillState('s'), new Set(), 4, seededRandom(7));
    const b = pickProblems(bank.slice().reverse(), initialSkillState('s'), new Set(), 4, seededRandom(7));
    expect(a.map((p) => p.id)).toEqual(b.map((p) => p.id));
  });
  it('returns at most count and never more than the bank', () => {
    expect(pickProblems(bank, initialSkillState('s'), new Set(), 10)).toHaveLength(6);
    expect(pickProblems(bank, initialSkillState('s'), new Set(), 0)).toHaveLength(0);
    expect(pickProblems([], initialSkillState('s'), new Set(), 3)).toHaveLength(0);
  });
});

describe('scorePlacement', () => {
  const q = (id: string, nodeId: string): DiagnosticQuestion => ({ id, nodeId, statement: '', checker: 'numeric', answer: '1' });

  it('correct answers grant mastery with the attempt minimum; wrong answers grant a little with one attempt', () => {
    const out = scorePlacement([
      { question: q('q1', 'numbers-and-inequalities'), correct: true },
      { question: q('q2', 'exponents-and-radicals'), correct: false },
    ], curriculum);
    const byId = new Map(out.map((s) => [s.nodeId, s]));
    expect(byId.get('numbers-and-inequalities')).toMatchObject({ mastery: CONFIG.placement.masteryIfCorrect, attempts: CONFIG.unlock.minAttempts });
    expect(byId.get('exponents-and-radicals')).toMatchObject({ mastery: CONFIG.placement.masteryIfWrong, attempts: 1 });
    expect(out).toHaveLength(2);
  });
  it('averages several questions on one node', () => {
    const out = scorePlacement([
      { question: q('q1', 'linear-equations'), correct: true },
      { question: q('q2', 'linear-equations'), correct: false },
    ], curriculum);
    const le = out.find((s) => s.nodeId === 'linear-equations')!;
    expect(le.mastery).toBeCloseTo((0.75 + 0.2) / 2);
    expect(le.attempts).toBe(2);
    expect(out.map((s) => s.nodeId)).not.toContain('numbers-and-inequalities');
  });
  it('propagates mastery to transitive prereqs of a mastered node', () => {
    const out = scorePlacement([{ question: q('q1', 'function-notation'), correct: true }], curriculum);
    const ids = out.map((s) => s.nodeId);
    for (const id of ['function-notation', 'linear-equations', 'factoring-and-quadratics', 'polynomials', 'exponents-and-radicals', 'numbers-and-inequalities']) {
      expect(ids).toContain(id);
      const s = out.find((x) => x.nodeId === id)!;
      expect(s.mastery).toBeGreaterThanOrEqual(CONFIG.placement.masteryIfCorrect);
      expect(s.attempts).toBeGreaterThanOrEqual(CONFIG.unlock.minAttempts);
    }
    expect(isUnlocked('function-notation', new Map(out.map((s) => [s.nodeId, s])), curriculum)).toBe(true);
  });
  it('direct wrong answers are not overwritten by propagation', () => {
    const out = scorePlacement([
      { question: q('q1', 'function-notation'), correct: true },
      { question: q('q2', 'polynomials'), correct: false },
    ], curriculum);
    expect(out.find((s) => s.nodeId === 'polynomials')!.mastery).toBe(CONFIG.placement.masteryIfWrong);
  });
  it('returns touched nodes in curriculum order', () => {
    const out = scorePlacement([
      { question: q('q1', 'linear-equations'), correct: false },
      { question: q('q2', 'numbers-and-inequalities'), correct: true },
    ], curriculum);
    expect(out.map((s) => s.nodeId)).toEqual(['numbers-and-inequalities', 'linear-equations']);
  });
});

describe('masteryLabel', () => {
  it('uses the documented thresholds', () => {
    expect(masteryLabel(0)).toBe('new');
    expect(masteryLabel(0.249)).toBe('new');
    expect(masteryLabel(0.25)).toBe('learning');
    expect(masteryLabel(0.6)).toBe('solid');
    expect(masteryLabel(0.849)).toBe('solid');
    expect(masteryLabel(0.85)).toBe('mastered');
    expect(masteryLabel(1)).toBe('mastered');
  });
});
