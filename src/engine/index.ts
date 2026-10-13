// STUB — the engine agent replaces this file. Signatures are the contract in docs/ARCHITECTURE.md.
import type { Config } from '../lib/config';
import type { Curriculum, CurriculumNode, DiagnosticQuestion, Problem, ReadingRecord, SessionRecord, SkillState } from '../types';
export interface Outcome { correct: boolean; hintsUsed: number; revealed: boolean }
export interface Assignment {
  date: string; focusNodeId: string; reviewNodeIds: string[]; readingNodeId: string | null;
  readingPages: [number, number] | null; readingPrefix?: string; problemNodeIds: string[]; rationale: string[]; estimatedMinutes: number;
}
export interface AssignmentContext { today: string; curriculum: Curriculum; states: Map<string, SkillState>; reading: ReadingRecord[]; sessions: SessionRecord[]; cfg?: Config }
const NI = () => { throw new Error('engine not implemented'); };
export function initialSkillState(_nodeId: string): SkillState { return NI(); }
export function applyAttempt(_s: SkillState, _o: Outcome, _today: string, _cfg?: Config): SkillState { return NI(); }
export function isUnlocked(_id: string, _s: Map<string, SkillState>, _c: Curriculum, _cfg?: Config): boolean { return NI(); }
export function unlockedNodes(_s: Map<string, SkillState>, _c: Curriculum, _cfg?: Config): CurriculumNode[] { return NI(); }
export function dueReviews(_s: Map<string, SkillState>, _today: string): SkillState[] { return NI(); }
export function currentIntegralTier(_s: Map<string, SkillState>, _c: Curriculum, _cfg?: Config): number { return NI(); }
export function buildAssignment(_ctx: AssignmentContext): Assignment { return NI(); }
export function buildWeekPlan(_ctx: AssignmentContext, _days?: number): Assignment[] { return NI(); }
export function pickProblems(_bank: Problem[], _s: SkillState, _seen: Set<string>, _count: number, _rng?: () => number): Problem[] { return NI(); }
export function scorePlacement(_r: { question: DiagnosticQuestion; correct: boolean }[], _c: Curriculum, _cfg?: Config): SkillState[] { return NI(); }
export function masteryLabel(_m: number): 'new' | 'learning' | 'solid' | 'mastered' { return NI(); }
