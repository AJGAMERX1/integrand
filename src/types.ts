// Shared data types for Integrand. Every module imports from here; do not duplicate these shapes.
// JSON on disk (data/) and records in IndexedDB (src/db) both conform to these types.

/** ---------- Curriculum (data/curriculum.json) ---------- */

export interface StewartRef {
  /** Section label as printed, e.g. "2.2" or "App. D" */
  section: string;
  /** Printed page numbers [first, last] from the physical book (NOT pdf indices). */
  printedPages: [number, number];
  /** Appendix pages are printed as A2, A10, ...; set to "A" for those. */
  pagePrefix?: string;
}

export interface CurriculumNode {
  id: string;
  title: string;
  /** 0 = ramp (algebra 2 / precalc / trig), 1 = Stewart */
  track: 0 | 1;
  /** Chapter grouping for display: "Ramp: Algebra", "Ch. 2 Limits", "Appendix D", ... */
  group: string;
  stewart: StewartRef | null;
  prereqs: string[];
  /** Which Daily Integral tier this node unlocks (0..6), or null. */
  integralTier: number | null;
  unlockThreshold: number;
  /** One-sentence plain-language description for the Today screen. */
  summary: string;
  /** Estimated number of 30-minute sessions to cover the node. */
  sessions: number;
}

export interface Curriculum {
  version: number;
  /** Nodes in recommended learning order. */
  nodes: CurriculumNode[];
}

/** ---------- Problems (data/problems/<node-id>.json) ---------- */

export type CheckerType = 'equiv' | 'equiv_plus_c' | 'numeric' | 'choice' | 'interval';

export interface Problem {
  id: string;
  skill: string; // node id
  difficulty: 1 | 2 | 3;
  /** LaTeX statement (rendered with KaTeX). */
  statement: string;
  checker: CheckerType;
  /**
   * Answer key.
   *  equiv / equiv_plus_c: expression in the grader's plain syntax, e.g. "sin(x^2)", "3*x^2+2".
   *  numeric: a number as a string, e.g. "2.5" or "-1/3" (fractions allowed).
   *  choice: the index (as string) of the correct entry in `choices`, e.g. "2".
   *  interval: "[a,b]", "(a,b]", "(-inf,3)" etc.
   */
  answer: string;
  /** Free variable name for equiv checkers (default "x"). */
  variable?: string;
  /** Sampling domain for equivalence checks. */
  domain?: [number, number];
  /** For checker "choice": LaTeX of each option. */
  choices?: string[];
  /** For checker "numeric": absolute tolerance (default 1e-6 relative). */
  tolerance?: number;
  hints: string[]; // hint 1, hint 2
  solution: string[]; // worked solution steps (LaTeX allowed inline with $...$)
  verified: true;
  /** For Daily Integral problems: the tier (0..6). */
  tier?: number;
  tags?: string[];
}

export interface ProblemBank {
  skill: string;
  problems: Problem[];
}

/** ---------- Concepts (data/concepts/<node-id>.json) ---------- */

export interface WorkedExample {
  title: string;
  problem: string; // LaTeX allowed with $...$
  steps: string[];
}

export interface Concept {
  nodeId: string;
  title: string;
  /** 2-4 paragraphs of plain-language explanation. Markdown-lite: paragraphs separated by blank lines, $...$ for math. */
  overview: string;
  keyIdeas: string[];
  workedExamples: WorkedExample[];
  commonMistakes: string[];
  whyItMatters: string;
  /** Short self-check questions with answers. */
  checkYourself: { q: string; a: string }[];
  /** What to look for while reading Stewart's pages (no book text). */
  readingGuide: string[];
}

/** ---------- Placement diagnostic (data/diagnostic.json) ---------- */

export interface DiagnosticQuestion {
  id: string;
  /** Node whose mastery this question informs. */
  nodeId: string;
  statement: string;
  checker: CheckerType;
  answer: string;
  choices?: string[];
  variable?: string;
  domain?: [number, number];
}

export interface Diagnostic {
  version: number;
  questions: DiagnosticQuestion[];
}

/** ---------- Learner state (IndexedDB) ---------- */

export interface SkillState {
  nodeId: string;
  mastery: number; // 0..1
  attempts: number;
  /** consecutive first-try correct answers */
  firstTryStreak: number;
  /** consecutive misses */
  missStreak: number;
  difficulty: 1 | 2 | 3;
  /** YYYY-MM-DD (Chicago) when the next spaced review is due, or null if never missed/reviewed. */
  dueDate: string | null;
  /** Index into config.spacedRepetition.intervalsDays. */
  intervalIndex: number;
  lastPracticed: string | null; // YYYY-MM-DD
}

export type AttemptContext = 'review' | 'problems' | 'daily' | 'archive' | 'placement' | 'practice';

export interface AttemptRecord {
  id: string;
  problemId: string;
  nodeId: string;
  answer: string;
  correct: boolean;
  hintsUsed: number;
  revealed: boolean;
  context: AttemptContext;
  timestamp: number; // epoch ms
  date: string; // YYYY-MM-DD Chicago
}

export type SessionBlock = 'review' | 'read' | 'problems' | 'daily' | 'exit';

export interface SessionRecord {
  date: string; // YYYY-MM-DD Chicago (primary key)
  mode: 'full' | 'dailyOnly';
  blocksCompleted: SessionBlock[];
  /** Reading assignment for the day */
  readingNodeId: string | null;
  /** Problem node ids worked in the "problems" block */
  problemNodeIds: string[];
  confidence: 1 | 2 | 3 | 4 | 5 | null;
  learned: string;
  startedAt: number;
  completedAt: number | null;
  /** Minutes actually spent (from timers), by block. */
  minutes: Partial<Record<SessionBlock, number>>;
}

export interface ReadingRecord {
  nodeId: string;
  date: string; // marked-read date (YYYY-MM-DD)
  /** How many reading passes have been marked for this node. */
  passes: number;
}

export type DailyOutcome = 'solved' | 'revealed' | 'incomplete';

export interface DailyRecord {
  date: string; // puzzle date (YYYY-MM-DD) — primary key
  problemId: string;
  tier: number;
  outcome: DailyOutcome;
  attemptsUsed: number;
  hintsUsed: number;
  /** True if this was played from the archive (never affects the streak). */
  isArchive: boolean;
  completedAt: number | null;
}

export type StudyKind = 'review' | 'read' | 'problems' | 'daily' | 'flow' | 'manual' | 'concept';

/** Time logged (flow timer, session blocks, manual entries). */
export interface StudyLog {
  id: string;
  date: string; // YYYY-MM-DD Chicago
  minutes: number;
  kind: StudyKind;
  nodeId: string | null;
  note: string;
  timestamp: number;
}

export interface Settings {
  id: 'settings';
  theme: 'system' | 'light' | 'dark';
  placementDone: boolean;
  /** 'completion' = a day counts when the attempt ends; 'solved' = only correct answers count. */
  streakRule: 'completion' | 'solved';
  flowBreakRatio: number; // focus minutes / ratio = break minutes
  /** Daily time budget in minutes (default 30). */
  dailyBudgetMinutes: number;
  createdAt: number;
  schemaVersion: number;
}

/** ---------- Export / import ---------- */

export interface ExportBundle {
  app: 'integrand';
  exportVersion: number;
  exportedAt: string; // ISO
  settings: Settings | null;
  skillState: SkillState[];
  attempts: AttemptRecord[];
  sessions: SessionRecord[];
  reading: ReadingRecord[];
  daily: DailyRecord[];
  studyLog: StudyLog[];
}
