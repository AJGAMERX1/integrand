// STUB — the engine agent replaces this file. Signatures are the contract in docs/ARCHITECTURE.md.
import type { DailyRecord, Problem } from '../types';
export function pickDaily(_date: string, _tier: number, _candidates: Problem[], _seen: Set<string>): Problem | null { throw new Error('daily not implemented'); }
export function computeStreak(_records: DailyRecord[], _today: string, _rule: 'completion' | 'solved'): { current: number; best: number; solved: number; completed: number } { throw new Error('daily not implemented'); }
