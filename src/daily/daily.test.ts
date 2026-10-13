import { describe, it, expect } from 'vitest';
import curriculumJson from '../../data/curriculum.json';
import type { Curriculum, DailyRecord, Problem } from '../types';
import { computeStreak, dayCounts, pickDaily, tierDescription, tierForNode, TIER_LABELS } from './index';

const curriculum = curriculumJson as unknown as Curriculum;
const TODAY = '2026-10-13';

const mk = (id: string, tier = 0): Problem => ({
  id, skill: 'area-by-geometry', difficulty: 1, statement: '', checker: 'numeric', answer: '1', hints: [], solution: [], verified: true, tier,
});
const bank = ['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8'].map((id) => mk(id));

const rec = (date: string, outcome: DailyRecord['outcome'], isArchive = false): DailyRecord => ({
  date, problemId: 'p', tier: 0, outcome, attemptsUsed: 1, hintsUsed: 0, isArchive, completedAt: 1,
});

describe('pickDaily', () => {
  it('same date and tier yields the same problem', () => {
    const a = pickDaily(TODAY, 0, bank, new Set());
    const b = pickDaily(TODAY, 0, bank, new Set());
    expect(a).not.toBeNull();
    expect(a!.id).toBe(b!.id);
  });
  it('is independent of candidate order', () => {
    const a = pickDaily(TODAY, 0, bank, new Set());
    const b = pickDaily(TODAY, 0, bank.slice().reverse(), new Set());
    expect(a!.id).toBe(b!.id);
  });
  it('different dates usually yield different problems', () => {
    const picks = new Set<string>();
    for (let d = 1; d <= 20; d++) picks.add(pickDaily(`2026-10-${String(d).padStart(2, '0')}`, 0, bank, new Set())!.id);
    expect(picks.size).toBeGreaterThan(3);
  });
  it('different tiers can yield different problems for the same date', () => {
    const picks = new Set<string>();
    for (let t = 0; t <= 6; t++) picks.add(pickDaily(TODAY, t, bank, new Set())!.id);
    expect(picks.size).toBeGreaterThan(1);
  });
  it('skips seen problems', () => {
    const first = pickDaily(TODAY, 0, bank, new Set())!;
    const next = pickDaily(TODAY, 0, bank, new Set([first.id]))!;
    expect(next.id).not.toBe(first.id);
    const seen = new Set(bank.map((p) => p.id).filter((id) => id !== 'd5'));
    expect(pickDaily(TODAY, 0, bank, seen)!.id).toBe('d5');
  });
  it('falls back to the whole pool when everything is seen', () => {
    const all = new Set(bank.map((p) => p.id));
    const p = pickDaily(TODAY, 0, bank, all);
    expect(p).not.toBeNull();
    expect(all.has(p!.id)).toBe(true);
  });
  it('returns null only for an empty candidate list', () => {
    expect(pickDaily(TODAY, 0, [], new Set())).toBeNull();
    expect(pickDaily(TODAY, 0, [mk('only')], new Set(['only']))!.id).toBe('only');
  });
});

describe('computeStreak', () => {
  it('counts consecutive days ending today', () => {
    const r = [rec('2026-10-11', 'solved'), rec('2026-10-12', 'solved'), rec('2026-10-13', 'solved')];
    expect(computeStreak(r, TODAY, 'completion')).toEqual({ current: 3, best: 3, solved: 3, completed: 3 });
  });
  it('is still alive when yesterday counted and today is not yet done', () => {
    const r = [rec('2026-10-11', 'solved'), rec('2026-10-12', 'revealed')];
    expect(computeStreak(r, TODAY, 'completion').current).toBe(2);
  });
  it('is 0 when the last counted day is before yesterday', () => {
    const r = [rec('2026-10-10', 'solved'), rec('2026-10-11', 'solved')];
    const s = computeStreak(r, TODAY, 'completion');
    expect(s.current).toBe(0);
    expect(s.best).toBe(2);
  });
  it('a gap breaks the current streak but best remembers the longest run', () => {
    const r = [rec('2026-10-01', 'solved'), rec('2026-10-02', 'solved'), rec('2026-10-03', 'solved'), rec('2026-10-04', 'solved'),
      rec('2026-10-12', 'solved'), rec('2026-10-13', 'solved')];
    expect(computeStreak(r, TODAY, 'completion')).toMatchObject({ current: 2, best: 4 });
  });
  it("'completion' counts revealed days; 'solved' does not", () => {
    const r = [rec('2026-10-11', 'solved'), rec('2026-10-12', 'revealed'), rec('2026-10-13', 'solved')];
    expect(computeStreak(r, TODAY, 'completion')).toEqual({ current: 3, best: 3, solved: 2, completed: 3 });
    expect(computeStreak(r, TODAY, 'solved')).toEqual({ current: 1, best: 1, solved: 2, completed: 2 });
  });
  it('incomplete days never count under either rule', () => {
    const r = [rec('2026-10-12', 'solved'), rec('2026-10-13', 'incomplete')];
    expect(computeStreak(r, TODAY, 'completion')).toMatchObject({ current: 1, completed: 1 });
    expect(computeStreak(r, TODAY, 'solved')).toMatchObject({ current: 1, completed: 1 });
  });
  it('archive replays never affect the streak or the counters', () => {
    const live = [rec('2026-10-12', 'solved'), rec('2026-10-13', 'solved')];
    const archive = [rec('2026-10-11', 'solved', true), rec('2026-10-10', 'solved', true), rec('2026-09-01', 'revealed', true)];
    const withArchive = computeStreak([...live, ...archive], TODAY, 'completion');
    expect(withArchive).toEqual(computeStreak(live, TODAY, 'completion'));
    expect(withArchive).toEqual({ current: 2, best: 2, solved: 2, completed: 2 });
    expect(computeStreak(archive, TODAY, 'completion')).toEqual({ current: 0, best: 0, solved: 0, completed: 0 });
  });
  it('handles no records and unsorted input', () => {
    expect(computeStreak([], TODAY, 'completion')).toEqual({ current: 0, best: 0, solved: 0, completed: 0 });
    const r = [rec('2026-10-13', 'solved'), rec('2026-10-11', 'solved'), rec('2026-10-12', 'solved')];
    expect(computeStreak(r, TODAY, 'solved').current).toBe(3);
  });
  it('dayCounts applies the rule and ignores archive', () => {
    expect(dayCounts(rec('2026-10-13', 'revealed'), 'completion')).toBe(true);
    expect(dayCounts(rec('2026-10-13', 'revealed'), 'solved')).toBe(false);
    expect(dayCounts(rec('2026-10-13', 'solved', true), 'completion')).toBe(false);
  });
});

describe('tier helpers', () => {
  it('describes tiers I0..I6 and clamps out-of-range tiers', () => {
    expect(TIER_LABELS).toHaveLength(7);
    expect(tierDescription(0)).toMatch(/geometry/i);
    expect(tierDescription(4)).toMatch(/substitution/i);
    expect(tierDescription(6)).toMatch(/parts/i);
    expect(tierDescription(99)).toBe(tierDescription(6));
    expect(tierDescription(-1)).toBe(tierDescription(0));
  });
  it('tierForNode reads integralTier from the curriculum', () => {
    expect(tierForNode('area-by-geometry', curriculum)).toBe(0);
    expect(tierForNode('substitution', curriculum)).toBe(4);
    expect(tierForNode('numbers-and-inequalities', curriculum)).toBeNull();
    expect(tierForNode('nope', curriculum)).toBeNull();
  });
});
