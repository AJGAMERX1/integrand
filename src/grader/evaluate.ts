// Numeric evaluation of an Expr. Returns NaN wherever the expression is undefined over the reals
// (division by zero, log of a non-positive number, sqrt of a negative, non-integer power of a
// negative base, 0 to a negative power, asin/acos outside [-1,1]). The constant inf evaluates to
// Infinity so interval endpoints can be compared.

import type { Expr } from './parser';

function safeDiv(a: number, b: number): number {
  if (b === 0) return NaN;
  return a / b;
}

function safePow(base: number, exp: number): number {
  if (base === 0 && exp < 0) return NaN;
  if (base < 0 && !Number.isInteger(exp)) return NaN;
  return Math.pow(base, exp);
}

function applyFunction(fn: string, x: number): number {
  switch (fn) {
    case 'sin': return Math.sin(x);
    case 'cos': return Math.cos(x);
    case 'tan': return safeDiv(Math.sin(x), Math.cos(x));
    case 'sec': return safeDiv(1, Math.cos(x));
    case 'csc': return safeDiv(1, Math.sin(x));
    case 'cot': return safeDiv(Math.cos(x), Math.sin(x));
    case 'asin': return Math.asin(x);
    case 'acos': return Math.acos(x);
    case 'atan': return Math.atan(x);
    case 'sinh': return Math.sinh(x);
    case 'cosh': return Math.cosh(x);
    case 'tanh': return Math.tanh(x);
    case 'coth': return safeDiv(Math.cosh(x), Math.sinh(x));
    case 'sech': return safeDiv(1, Math.cosh(x));
    case 'csch': return safeDiv(1, Math.sinh(x));
    case 'exp': return Math.exp(x);
    case 'ln':
    case 'log': return x > 0 ? Math.log(x) : NaN;
    case 'log10': return x > 0 ? Math.log10(x) : NaN;
    case 'log2': return x > 0 ? Math.log2(x) : NaN;
    case 'sqrt': return x >= 0 ? Math.sqrt(x) : NaN;
    case 'abs': return Math.abs(x);
    default: return NaN;
  }
}

/** Evaluate `expr` with the given variable bindings. Unknown variables evaluate to NaN. */
export function evaluate(expr: Expr, vars: Record<string, number>): number {
  switch (expr.kind) {
    case 'num': return expr.value;
    case 'const':
      if (expr.name === 'pi') return Math.PI;
      if (expr.name === 'e') return Math.E;
      return Infinity;
    case 'var': {
      const v = vars[expr.name];
      return typeof v === 'number' ? v : NaN;
    }
    case 'neg': return -evaluate(expr.arg, vars);
    case 'bin': {
      const a = evaluate(expr.left, vars);
      const b = evaluate(expr.right, vars);
      switch (expr.op) {
        case '+': return a + b;
        case '-': return a - b;
        case '*': return a * b;
        case '/': return safeDiv(a, b);
        case '^': return safePow(a, b);
      }
      return NaN;
    }
    case 'call': return applyFunction(expr.fn, evaluate(expr.arg, vars));
  }
  return NaN;
}
