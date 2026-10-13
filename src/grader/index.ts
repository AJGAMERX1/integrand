// Client-side math grader for Integrand. Pure functions, no DOM.
// Public API is the "Grader contract" in docs/ARCHITECTURE.md.
//
// Equivalence is numeric: both expressions are sampled at random points of the domain using a
// seeded PRNG (so the same inputs always give the same verdict), compared with a relative
// tolerance of 1e-6 wherever both sides are defined, and at least 4 such points are required.

import type { Problem } from '../types';
import { latexToPlain } from './latex';
import { parseExpression, freeVariables, ParseError, type Expr } from './parser';
import { evaluate } from './evaluate';

export { latexToPlain, parseExpression, evaluate, ParseError, freeVariables };
export type { Expr };

export interface GradeResult { correct: boolean; reason: string; normalizedInput?: string }

const DEFAULT_DOMAIN: [number, number] = [-3, 3];
const DEFAULT_SAMPLES = 12;
const MIN_VALID_POINTS = 4;
const REL_TOL = 1e-6;
const ABS_FLOOR = 1e-9;

/* ---------- deterministic sampling ---------- */

function hashString(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function close(a: number, b: number, scale = 0): boolean {
  return Math.abs(a - b) <= REL_TOL * Math.max(Math.abs(a), Math.abs(b), scale) + ABS_FLOOR;
}

function describe(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

/* ---------- expression equivalence ---------- */

interface Verdict { ok: boolean; reason: string }

export interface EquivOptions { variable?: string; domain?: [number, number]; plusC?: boolean; samples?: number }

/** Compare two plain-syntax expressions. `user` and `answer` must already be plain syntax. */
function compareExpressions(user: string, answer: string, opts: EquivOptions = {}): Verdict {
  const variable = opts.variable ?? 'x';
  const domain = opts.domain ?? DEFAULT_DOMAIN;
  const samples = Math.max(1, opts.samples ?? DEFAULT_SAMPLES);
  const plusC = opts.plusC ?? false;

  let userExpr: Expr;
  try {
    userExpr = parseExpression(user);
  } catch (err) {
    return { ok: false, reason: `Couldn't read your answer: ${describe(err)}` };
  }
  let answerExpr: Expr;
  try {
    answerExpr = parseExpression(answer);
  } catch (err) {
    return { ok: false, reason: `The answer key for this problem could not be read (${describe(err)})` };
  }

  // Extra constants of integration are allowed for +C checks and bound to zero.
  const allowed = new Set([variable]);
  if (plusC) { allowed.add('C'); allowed.add('c'); }
  const unknown = freeVariables(userExpr).filter((v) => !allowed.has(v));
  if (unknown.length > 0) {
    const list = unknown.map((v) => `"${v}"`).join(', ');
    return { ok: false, reason: `Your answer uses ${list}, but the only variable here is "${variable}"` };
  }

  const [lo, hi] = domain[0] <= domain[1] ? domain : [domain[1], domain[0]];
  const rng = mulberry32(hashString(`${user}|${answer}|${variable}|${lo},${hi}|${plusC ? 'C' : ''}`) ^ 0x9e3779b9);
  const us: number[] = [];
  const as: number[] = [];
  let userDefined = 0;
  let answerDefined = 0;
  const maxDraws = samples * 5;
  for (let draw = 0; draw < maxDraws && us.length < samples; draw++) {
    const t = lo + (hi - lo) * rng();
    const vars: Record<string, number> = { [variable]: t };
    if (plusC) { vars.C = 0; vars.c = 0; }
    const u = evaluate(userExpr, vars);
    const a = evaluate(answerExpr, vars);
    if (Number.isFinite(u)) userDefined++;
    if (Number.isFinite(a)) answerDefined++;
    if (Number.isFinite(u) && Number.isFinite(a)) { us.push(u); as.push(a); }
  }

  if (us.length < MIN_VALID_POINTS) {
    if (userDefined === 0) return { ok: false, reason: `Your answer is undefined everywhere on the domain [${lo}, ${hi}]` };
    if (answerDefined === 0) return { ok: false, reason: 'The answer key is undefined on the sampling domain' };
    return { ok: false, reason: 'Your answer and the expected one are defined on different parts of the domain' };
  }

  if (plusC) {
    const d0 = us[0] - as[0];
    const constantDiff = us.every((u, i) => close(u - as[i], d0, Math.max(Math.abs(u), Math.abs(as[i]))));
    if (constantDiff) return { ok: true, reason: 'Correct' };
  } else {
    const allEqual = us.every((u, i) => close(u, as[i]));
    if (allEqual) return { ok: true, reason: 'Correct' };
  }

  // Diagnose the most common near-misses.
  const ratios: number[] = [];
  for (let i = 0; i < us.length; i++) {
    if (Math.abs(as[i]) > ABS_FLOOR) ratios.push(us[i] / as[i]);
  }
  if (ratios.length >= MIN_VALID_POINTS) {
    const r0 = ratios[0];
    const constantRatio = ratios.every((r) => close(r, r0, 1));
    if (constantRatio && Math.abs(r0) > ABS_FLOOR) {
      if (close(r0, -1)) return { ok: false, reason: 'Sign error: this is the negative of the expected answer' };
      if (!close(r0, 1)) return { ok: false, reason: 'Off by a constant factor' };
    }
  }
  if (!plusC) {
    const d0 = us[0] - as[0];
    const constantDiff = us.every((u, i) => close(u - as[i], d0, Math.max(Math.abs(u), Math.abs(as[i]))));
    if (constantDiff) return { ok: false, reason: 'Differs from the expected answer by a constant term' };
  }
  return { ok: false, reason: 'Not equivalent to the expected expression' };
}

/** Remove a trailing "+ C" / "- c" constant of integration from plain syntax. */
function stripPlusC(plain: string): string {
  return plain.replace(/\s*[+-]\s*[Cc]\s*$/, '').trim();
}

/** True when `a` and `b` (LaTeX or plain) agree on the domain. Never throws. */
export function equivalent(a: string, b: string, opts?: EquivOptions): boolean {
  try {
    let user = latexToPlain(a);
    const answer = latexToPlain(b);
    if (opts?.plusC) user = stripPlusC(user);
    return compareExpressions(user, answer, opts).ok;
  } catch {
    return false;
  }
}

/* ---------- numeric answers ---------- */

function evalConstant(plain: string): { value: number; vars: string[] } {
  const expr = parseExpression(plain);
  return { value: evaluate(expr, {}), vars: freeVariables(expr) };
}

/** Number of decimal places if `plain` is a bare decimal literal (e.g. "0.333", "-2.50"), else -1. */
function decimalPlaces(plain: string): number {
  const m = /^[+-]?(?:\d+)?\.(\d+)$/.exec(plain.replace(/\s+/g, ''));
  return m ? m[1].length : -1;
}

function compareNumeric(user: string, answer: string, tolerance?: number): Verdict {
  let expected: number;
  try {
    const a = evalConstant(answer);
    expected = a.value;
    if (a.vars.length > 0 || !Number.isFinite(expected)) throw new Error('not a number');
  } catch (err) {
    return { ok: false, reason: `The answer key for this problem could not be read (${describe(err)})` };
  }

  let got: number;
  try {
    const u = evalConstant(user);
    if (u.vars.length > 0) {
      const list = u.vars.map((v) => `"${v}"`).join(', ');
      return { ok: false, reason: `Your answer should be a number, but it uses ${list}` };
    }
    got = u.value;
  } catch (err) {
    return { ok: false, reason: `Couldn't read your answer: ${describe(err)}` };
  }
  if (!Number.isFinite(got)) return { ok: false, reason: "Your answer doesn't evaluate to a number" };

  const baseTol = tolerance ?? Math.max(1e-6, 1e-6 * Math.abs(expected));
  const places = decimalPlaces(user);
  const roundingTol = places >= 0 ? 0.5 * Math.pow(10, -places) + 1e-12 : 0;
  const diff = Math.abs(got - expected);

  if (diff <= baseTol) return { ok: true, reason: 'Correct' };
  if (places >= 3 && diff <= roundingTol) return { ok: true, reason: 'Correct' };
  if (places >= 0 && places < 3 && diff <= roundingTol) {
    return { ok: false, reason: 'Close, but give at least 3 decimal places (or an exact value like 1/3)' };
  }
  return { ok: false, reason: 'Not the expected value' };
}

/** Numeric check. `user` may be "1/3", "0.333", "2pi", "sqrt(2)", "-\frac{1}{3}". Never throws. */
export function checkNumeric(user: string, answer: string, tolerance?: number): boolean {
  try {
    return compareNumeric(latexToPlain(user), latexToPlain(answer), tolerance).ok;
  } catch {
    return false;
  }
}

/* ---------- intervals ---------- */

interface Interval { lo: number; hi: number; loClosed: boolean; hiClosed: boolean }

const INTERVAL_HELP = 'Write an interval like [a, b), (-inf, 3] or (0, inf)';

function splitTopLevel(s: string, sep: string): string[] {
  const parts: string[] = [];
  let depth = 0;
  let start = 0;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (c === '(' || c === '[') depth++;
    else if (c === ')' || c === ']') depth--;
    else if (c === sep && depth === 0) { parts.push(s.slice(start, i)); start = i + 1; }
  }
  parts.push(s.slice(start));
  return parts;
}

function parseOneInterval(text: string): Interval {
  const s = text.trim();
  const open = s[0];
  const closeCh = s[s.length - 1];
  if (s.length < 2 || !'([]'.includes(open) || !')]['.includes(closeCh)) throw new ParseError(INTERVAL_HELP);
  const inner = s.slice(1, -1);
  const parts = splitTopLevel(inner, ',');
  if (parts.length !== 2) throw new ParseError(INTERVAL_HELP);
  const ends = parts.map((p) => {
    if (p.trim() === '') throw new ParseError(INTERVAL_HELP);
    const { value, vars } = evalConstant(p);
    if (vars.length > 0) throw new ParseError(`Interval endpoints must be numbers, not "${vars[0]}"`);
    if (Number.isNaN(value)) throw new ParseError('An endpoint of the interval is undefined');
    return value;
  });
  // "]a, b[" (reversed brackets) also means open; treat "[" on the right / "]" on the left as open.
  return { lo: ends[0], hi: ends[1], loClosed: open === '[', hiClosed: closeCh === ']' };
}

/** Parse an interval or a union of intervals, written in plain syntax. */
function parseIntervals(plain: string): Interval[] {
  const pieces = plain.split(/\s*(?:\bU\b|∪)\s*/).filter((p) => p.trim() !== '');
  if (pieces.length === 0) throw new ParseError(INTERVAL_HELP);
  return pieces.map(parseOneInterval).sort((a, b) => a.lo - b.lo || a.hi - b.hi);
}

function endpointsEqual(a: number, b: number): boolean {
  if (!Number.isFinite(a) || !Number.isFinite(b)) return a === b;
  return close(a, b);
}

function compareIntervals(user: string, answer: string): Verdict {
  let expected: Interval[];
  try {
    expected = parseIntervals(answer);
  } catch (err) {
    return { ok: false, reason: `The answer key for this problem could not be read (${describe(err)})` };
  }
  let got: Interval[];
  try {
    got = parseIntervals(user);
  } catch (err) {
    return { ok: false, reason: `Couldn't read your answer: ${describe(err)}` };
  }
  for (const iv of got) {
    if (iv.lo > iv.hi) return { ok: false, reason: 'The left endpoint should be the smaller one' };
    if (!Number.isFinite(iv.lo) && iv.loClosed) return { ok: false, reason: 'Use a parenthesis ( next to -inf, never a bracket' };
    if (!Number.isFinite(iv.hi) && iv.hiClosed) return { ok: false, reason: 'Use a parenthesis ) next to inf, never a bracket' };
  }
  if (got.length !== expected.length) {
    return { ok: false, reason: expected.length === 1 ? 'The answer is a single interval' : `The answer is a union of ${expected.length} intervals` };
  }
  let bracketIssue = false;
  for (let i = 0; i < got.length; i++) {
    const g = got[i];
    const e = expected[i];
    if (!endpointsEqual(g.lo, e.lo) || !endpointsEqual(g.hi, e.hi)) return { ok: false, reason: 'Check the endpoints of the interval' };
    if (g.loClosed !== e.loClosed || g.hiClosed !== e.hiClosed) bracketIssue = true;
  }
  if (bracketIssue) return { ok: false, reason: 'Check which endpoints are included: [ ] includes the endpoint, ( ) excludes it' };
  return { ok: true, reason: 'Correct' };
}

/** Interval check: "[a,b]", "(a,b]", "(-inf,3)", "\left(-\infty, 3\right]". Never throws. */
export function checkInterval(user: string, answer: string): boolean {
  try {
    return compareIntervals(latexToPlain(user), latexToPlain(answer)).ok;
  } catch {
    return false;
  }
}

/* ---------- grade ---------- */

function gradeInner(problem: Problem, userInput: string): GradeResult {
  const raw = (userInput ?? '').trim();
  if (raw === '') return { correct: false, reason: 'Enter an answer first' };

  switch (problem.checker) {
    case 'choice': {
      const expected = String(problem.answer).trim();
      const ok = raw === expected || (raw !== '' && Number(raw) === Number(expected) && Number.isInteger(Number(raw)));
      return { correct: ok, reason: ok ? 'Correct' : "That's not the right option", normalizedInput: raw };
    }
    case 'numeric': {
      const plain = latexToPlain(raw);
      const v = compareNumeric(plain, latexToPlain(problem.answer), problem.tolerance);
      return { correct: v.ok, reason: v.reason, normalizedInput: plain };
    }
    case 'interval': {
      const plain = latexToPlain(raw);
      const v = compareIntervals(plain, latexToPlain(problem.answer));
      return { correct: v.ok, reason: v.reason, normalizedInput: plain };
    }
    case 'equiv':
    case 'equiv_plus_c': {
      const plusC = problem.checker === 'equiv_plus_c';
      let plain = latexToPlain(raw);
      if (plusC) plain = stripPlusC(plain);
      const v = compareExpressions(plain, latexToPlain(problem.answer), {
        variable: problem.variable ?? 'x',
        domain: problem.domain ?? DEFAULT_DOMAIN,
        plusC,
      });
      return { correct: v.ok, reason: v.reason, normalizedInput: plain };
    }
    default:
      return { correct: false, reason: `Unknown checker "${String(problem.checker)}"` };
  }
}

/** Grade a learner's input against a problem. Never throws. */
export function grade(problem: Problem, userInput: string): GradeResult {
  try {
    return gradeInner(problem, userInput);
  } catch (err) {
    return { correct: false, reason: `Couldn't grade that answer: ${describe(err)}` };
  }
}
