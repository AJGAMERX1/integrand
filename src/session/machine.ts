// The 30-minute session state machine over SessionRecord.
// Blocks run in order review -> read -> problems -> daily -> exit (mode 'full') or just daily (mode 'dailyOnly').
// The record is persisted after every block, so reloading resumes at the first incomplete block.
import type { SessionBlock, SessionRecord, StudyKind } from '../types';
import type { Assignment } from '../engine';
import { getSession, saveSession, logStudy } from '../db/state';
import { today } from '../lib/date';
import { CONFIG } from '../lib/config';
import { getNode } from '../data/load';

export type SessionMode = SessionRecord['mode'];

export const FULL_BLOCKS: readonly SessionBlock[] = ['review', 'read', 'problems', 'daily', 'exit'];
export const DAILY_ONLY_BLOCKS: readonly SessionBlock[] = ['daily'];

export const BLOCK_TITLES: Record<SessionBlock, string> = {
  review: 'Review', read: 'Read', problems: 'Problems', daily: 'Daily Integral', exit: 'Wrap up',
};

export function blocksFor(mode: SessionMode): readonly SessionBlock[] {
  return mode === 'dailyOnly' ? DAILY_ONLY_BLOCKS : FULL_BLOCKS;
}

export function blockMinutes(block: SessionBlock): number {
  return CONFIG.session.blocks[block];
}

/** Minutes the whole session is budgeted for. */
export function totalMinutes(mode: SessionMode): number {
  return blocksFor(mode).reduce((sum, b) => sum + blockMinutes(b), 0);
}

function newRecord(assignment: Assignment, mode: SessionMode, date: string): SessionRecord {
  return {
    date, mode, blocksCompleted: [],
    readingNodeId: assignment.readingNodeId,
    problemNodeIds: [...assignment.problemNodeIds],
    confidence: null, learned: '', startedAt: Date.now(), completedAt: null, minutes: {},
  };
}

/**
 * Creates today's SessionRecord or loads the existing one. Starting a full session on a day that already has a
 * daily-only record upgrades it to 'full' and keeps the completed daily block.
 */
export async function startSession(assignment: Assignment, mode: SessionMode = 'full'): Promise<SessionRecord> {
  const date = today();
  const existing = await getSession(date);
  if (!existing) {
    const rec = newRecord(assignment, mode, date);
    await saveSession(rec);
    return rec;
  }
  let rec = existing;
  if (mode === 'full' && existing.mode === 'dailyOnly') {
    rec = {
      ...existing, mode: 'full',
      readingNodeId: existing.readingNodeId ?? assignment.readingNodeId,
      problemNodeIds: existing.problemNodeIds.length ? existing.problemNodeIds : [...assignment.problemNodeIds],
      completedAt: null,
    };
    await saveSession(rec);
  }
  return rec;
}

export function isBlockDone(rec: SessionRecord, block: SessionBlock): boolean {
  return rec.blocksCompleted.includes(block);
}

/** First incomplete block for the record's mode, or null when the session is complete. */
export function currentBlock(rec: SessionRecord): SessionBlock | null {
  for (const b of blocksFor(rec.mode)) if (!isBlockDone(rec, b)) return b;
  return null;
}

export function isComplete(rec: SessionRecord): boolean {
  return currentBlock(rec) === null;
}

export function progress(rec: SessionRecord): { done: number; total: number; blocks: { block: SessionBlock; done: boolean }[] } {
  const blocks = blocksFor(rec.mode).map((block) => ({ block, done: isBlockDone(rec, block) }));
  return { done: blocks.filter((b) => b.done).length, total: blocks.length, blocks };
}

export function minutesSpent(rec: SessionRecord): number {
  return Object.values(rec.minutes).reduce((s, m) => s + (m ?? 0), 0);
}

/**
 * Marks a block complete, adds its minutes, persists the record and logs the minutes to the study log
 * (kind = block, nodeId = the skill the block was about). Idempotent: completing a done block only adds minutes.
 */
export async function completeBlock(rec: SessionRecord, block: SessionBlock, minutes: number, nodeId: string | null = null): Promise<SessionRecord> {
  const mins = Math.max(0, Math.round(minutes));
  const next: SessionRecord = {
    ...rec,
    blocksCompleted: isBlockDone(rec, block) ? rec.blocksCompleted : [...rec.blocksCompleted, block],
    minutes: { ...rec.minutes, [block]: (rec.minutes[block] ?? 0) + mins },
  };
  if (block === 'exit' || currentBlock(next) === null) next.completedAt = next.completedAt ?? Date.now();
  await saveSession(next);
  if (mins >= 1) {
    // 'exit' is not a study kind; its couple of minutes are logged as a manual entry.
    const kind: StudyKind = block === 'exit' ? 'manual' : block;
    try { await logStudy({ minutes: mins, kind, nodeId, note: block === 'exit' ? 'session wrap-up' : '', date: rec.date }); } catch (err) { console.error('logStudy failed', err); }
  }
  return next;
}

/** Skipping a block completes it with whatever minutes were spent (often 0). */
export function skipBlock(rec: SessionRecord, block: SessionBlock, minutes = 0, nodeId: string | null = null): Promise<SessionRecord> {
  return completeBlock(rec, block, minutes, nodeId);
}

/** Saves the exit reflection and completes the exit block (which completes the session). */
export async function finishSession(
  rec: SessionRecord, exit: { learned: string; confidence: SessionRecord['confidence'] }, minutes = 0, nodeId: string | null = null,
): Promise<SessionRecord> {
  const withExit: SessionRecord = { ...rec, learned: exit.learned.trim(), confidence: exit.confidence };
  await saveSession(withExit);
  return completeBlock(withExit, 'exit', minutes, nodeId);
}

/** ---------- Reading description shared by Today and the Read block ---------- */

export interface ReadingInfo {
  nodeId: string | null;
  title: string;
  /** "2.2" or "App. D"; null for concept-page reading. */
  section: string | null;
  /** "pp. 83-88" / "pp. A24-A28" / null when reading the concept page. */
  pages: string | null;
  /** "Read pp. 83-88 of section 2.2" / "Read the concept page" / "No reading today". */
  sentence: string;
}

export function pagesLabel(pages: [number, number], prefix = ''): string {
  const [a, b] = pages;
  return a === b ? `p. ${prefix}${a}` : `pp. ${prefix}${a}-${prefix}${b}`;
}

export function describeReading(a: Pick<Assignment, 'readingNodeId' | 'readingPages' | 'readingPrefix'>): ReadingInfo {
  const node = a.readingNodeId ? getNode(a.readingNodeId) : undefined;
  if (!a.readingNodeId || !node) {
    return { nodeId: null, title: '', section: null, pages: null, sentence: 'No reading today' };
  }
  const section = node.stewart?.section ?? null;
  if (a.readingPages) {
    const prefix = a.readingPrefix ?? node.stewart?.pagePrefix ?? '';
    const pages = pagesLabel(a.readingPages, prefix);
    const where = section ? (section.startsWith('App') ? section : `section ${section}`) : node.title;
    return { nodeId: node.id, title: node.title, section, pages, sentence: `Read ${pages} of ${where}` };
  }
  return { nodeId: node.id, title: node.title, section, pages: null, sentence: 'Read the concept page' };
}
