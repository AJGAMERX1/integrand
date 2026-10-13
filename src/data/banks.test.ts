// Content sanity: every committed problem must be gradable by the client grader against its own key.
import { describe, expect, it } from 'vitest';
import { grade } from '../grader';
import type { Diagnostic, Problem, ProblemBank, Concept, Curriculum } from '../types';
import curriculumJson from '../../data/curriculum.json';
import diagnosticJson from '../../data/diagnostic.json';

const curriculum = curriculumJson as Curriculum;
const nodeIds = new Set(curriculum.nodes.map((n) => n.id));
const bankModules = import.meta.glob<ProblemBank>('../../data/problems/*.json', { eager: true, import: 'default' });
const banks = Object.entries(bankModules).map(([path, bank]) => ({ file: path.split('/').pop()!, bank }));
const conceptModules = import.meta.glob<Concept>('../../data/concepts/*.json', { eager: true, import: 'default' });

/** Render the key the way a learner would type it (keys are already plain syntax; choice keys are indices). */
function selfAnswer(p: Problem): string {
  return p.answer;
}

describe('problem banks', () => {
  it('exist', () => { expect(banks.length).toBeGreaterThan(40); });

  for (const { file, bank } of banks) {
    describe(file, () => {
      it('has a valid skill and only verified problems', () => {
        expect(nodeIds.has(bank.skill)).toBe(true);
        for (const p of bank.problems) {
          expect(p.verified).toBe(true);
          expect(nodeIds.has(p.skill)).toBe(true);
          expect(p.hints).toHaveLength(2);
          expect(p.solution.length).toBeGreaterThanOrEqual(2);
        }
      });
      it('every key grades as correct against itself', () => {
        const failures: string[] = [];
        for (const p of bank.problems) {
          const r = grade(p, selfAnswer(p));
          if (!r.correct) failures.push(`${p.id} [${p.checker}] ${p.answer} -> ${r.reason}`);
        }
        expect(failures).toEqual([]);
      });
      it('a clearly wrong answer is rejected', () => {
        const failures: string[] = [];
        for (const p of bank.problems) {
          const wrong = p.checker === 'choice' ? String((Number(p.answer) + 1) % (p.choices?.length ?? 2))
            : p.checker === 'interval' ? '[1000,2000)'
            : p.checker === 'numeric' ? `(${p.answer})+7` : `(${p.answer})+x^7`;
          if (grade(p, wrong).correct) failures.push(`${p.id} accepted ${wrong}`);
        }
        expect(failures).toEqual([]);
      });
    });
  }

  it('has unique ids across all banks', () => {
    const ids = banks.flatMap((b) => b.bank.problems.map((p) => p.id));
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('covers every tier 0-6 for the Daily Integral', () => {
    const tiers = new Set(banks.flatMap((b) => b.bank.problems.map((p) => p.tier).filter((t) => t != null)));
    for (let t = 0; t <= 6; t++) expect(tiers.has(t)).toBe(true);
  });
});

describe('diagnostic', () => {
  const d = diagnosticJson as Diagnostic;
  it('has 18 gradable questions on known nodes', () => {
    expect(d.questions).toHaveLength(18);
    for (const q of d.questions) {
      expect(nodeIds.has(q.nodeId)).toBe(true);
      const p = { id: q.id, skill: q.nodeId, difficulty: 2 as const, statement: q.statement, checker: q.checker, answer: q.answer,
        choices: q.choices, variable: q.variable, domain: q.domain, hints: ['', ''], solution: ['', ''], verified: true as const };
      expect(grade(p, q.answer).correct, q.id).toBe(true);
    }
  });
});

describe('concepts', () => {
  it('exist for every curriculum node', () => {
    const have = new Set(Object.values(conceptModules).map((c) => c.nodeId));
    const missing = [...nodeIds].filter((id) => !have.has(id));
    expect(missing).toEqual([]);
  });
});
