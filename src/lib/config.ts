// All tunable defaults from SPEC.md live here. Change numbers, not logic.
export const CONFIG = {
  timezone: 'America/Chicago',
  session: {
    /** Minutes per block of the 30-minute session. */
    blocks: { review: 4, read: 10, problems: 9, daily: 5, exit: 2 } as const,
    reviewProblems: 2,
    newProblemsMin: 3,
    newProblemsMax: 4,
  },
  mastery: {
    /** m = m + rate * (score - m) */
    rate: 0.3,
    scoreFirstTry: 1,
    scoreWithHint: 0.5,
    scoreMiss: 0,
  },
  spacedRepetition: {
    /** Interval ladder in days after each successful review. A miss resets to index 0 (1 day). */
    intervalsDays: [1, 3, 7, 14, 30],
  },
  unlock: {
    minAttempts: 5,
    defaultThreshold: 0.7,
  },
  difficulty: {
    stepUpAfterFirstTryCorrect: 3,
    stepDownAfterMisses: 2,
    min: 1,
    max: 3,
  },
  daily: {
    attempts: 3,
    hints: 2,
    /** Streak counts a day on completion (correct or revealed) by default. */
    streakRule: 'completion' as 'completion' | 'solved',
  },
  flow: {
    breakRatio: 5,
  },
  placement: {
    questions: 18,
    /** Mastery assigned to a node answered correctly in the diagnostic. */
    masteryIfCorrect: 0.75,
    masteryIfWrong: 0.2,
  },
  export: { version: 1 },
  db: { name: 'integrand', version: 1 },
} as const;

export type Config = typeof CONFIG;
