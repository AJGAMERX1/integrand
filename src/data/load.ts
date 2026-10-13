// Loads the static content from data/ (bundled at build time). The app only reads data/; tools/ writes it.
import type { Concept, Curriculum, Diagnostic, Problem, ProblemBank } from '../types';
import curriculumJson from '../../data/curriculum.json';
import diagnosticJson from '../../data/diagnostic.json';

const problemModules = import.meta.glob<ProblemBank>('../../data/problems/*.json', { eager: true, import: 'default' });
const conceptModules = import.meta.glob<Concept>('../../data/concepts/*.json', { eager: true, import: 'default' });

export const curriculum: Curriculum = curriculumJson as Curriculum;
export const diagnostic: Diagnostic = diagnosticJson as Diagnostic;

const nodeMap = new Map(curriculum.nodes.map((n) => [n.id, n]));
export function getNode(id: string) { return nodeMap.get(id); }

const banks = new Map<string, Problem[]>();
for (const mod of Object.values(problemModules)) {
  const bank = mod as ProblemBank;
  if (!bank || !Array.isArray(bank.problems)) continue;
  const verified = bank.problems.filter((p) => p.verified === true);
  banks.set(bank.skill, [...(banks.get(bank.skill) ?? []), ...verified]);
}
export function problemsFor(nodeId: string): Problem[] { return banks.get(nodeId) ?? []; }
export function allProblems(): Problem[] { return [...banks.values()].flat(); }
const problemIndex = new Map(allProblems().map((p) => [p.id, p]));
export function getProblem(id: string) { return problemIndex.get(id); }
/** Daily Integral candidates for a tier: problems in any bank tagged with that tier. */
export function problemsForTier(tier: number): Problem[] { return allProblems().filter((p) => p.tier === tier); }

const concepts = new Map<string, Concept>();
for (const mod of Object.values(conceptModules)) { const c = mod as Concept; if (c && c.nodeId) concepts.set(c.nodeId, c); }
export function conceptFor(nodeId: string): Concept | undefined { return concepts.get(nodeId); }
