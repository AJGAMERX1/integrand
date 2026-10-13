// Repository helpers over the raw db. UI code should call these rather than db.* directly.
import { db } from './db';
import { today } from '../lib/date';
import { newId } from '../lib/seed';
import type { AttemptRecord, DailyRecord, ReadingRecord, SessionRecord, SkillState, StudyLog, AttemptContext } from '../types';

export async function loadSkillStates(): Promise<Map<string, SkillState>> {
  const all = await db.getAll<SkillState>('skillState');
  return new Map(all.map((s) => [s.nodeId, s]));
}
export function saveSkillState(s: SkillState) { return db.put('skillState', s); }
export function saveSkillStates(list: SkillState[]) { return db.putMany('skillState', list); }

export async function recordAttempt(a: Omit<AttemptRecord, 'id' | 'timestamp' | 'date'> & { context: AttemptContext }): Promise<AttemptRecord> {
  const rec: AttemptRecord = { ...a, id: newId('a_'), timestamp: Date.now(), date: today() };
  await db.put('attempts', rec);
  return rec;
}
export function loadAttempts() { return db.getAll<AttemptRecord>('attempts'); }
export async function seenProblemIds(): Promise<Set<string>> {
  const all = await loadAttempts();
  return new Set(all.map((a) => a.problemId));
}

export function loadSessions() { return db.getAll<SessionRecord>('sessions'); }
export function getSession(date: string) { return db.get<SessionRecord>('sessions', date); }
export function saveSession(s: SessionRecord) { return db.put('sessions', s); }

export async function loadReading(): Promise<ReadingRecord[]> { return db.getAll<ReadingRecord>('reading'); }
export async function markRead(nodeId: string): Promise<ReadingRecord> {
  const prev = await db.get<ReadingRecord>('reading', nodeId);
  const rec: ReadingRecord = { nodeId, date: today(), passes: (prev?.passes ?? 0) + 1 };
  await db.put('reading', rec);
  return rec;
}

export function loadDaily() { return db.getAll<DailyRecord>('daily'); }
export function getDaily(date: string) { return db.get<DailyRecord>('daily', date); }
export function saveDaily(d: DailyRecord) { return db.put('daily', d); }

export function loadStudyLog() { return db.getAll<StudyLog>('studyLog'); }
export async function logStudy(entry: Omit<StudyLog, 'id' | 'timestamp' | 'date'> & { date?: string }): Promise<StudyLog> {
  const rec: StudyLog = { ...entry, date: entry.date ?? today(), id: newId('l_'), timestamp: Date.now() };
  await db.put('studyLog', rec);
  return rec;
}
export function deleteStudyLog(id: string) { return db.delete('studyLog', id); }
