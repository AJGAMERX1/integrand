// STUB — the grader agent replaces this file. Signatures are the contract in docs/ARCHITECTURE.md.
import type { Problem } from '../types';
export interface GradeResult { correct: boolean; reason: string; normalizedInput?: string }
export type Expr = unknown;
export function grade(_problem: Problem, _userInput: string): GradeResult { throw new Error('grader not implemented'); }
export function latexToPlain(latex: string): string { return latex; }
export function parseExpression(_src: string): Expr { throw new Error('grader not implemented'); }
export function evaluate(_expr: Expr, _vars: Record<string, number>): number { return NaN; }
export function equivalent(_a: string, _b: string, _opts?: { variable?: string; domain?: [number, number]; plusC?: boolean; samples?: number }): boolean { return false; }
export function checkNumeric(_user: string, _answer: string, _tolerance?: number): boolean { return false; }
export function checkInterval(_user: string, _answer: string): boolean { return false; }
