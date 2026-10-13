import { describe, it, expect } from 'vitest';
import { parseExpression, ParseError, freeVariables } from './parser';
import { evaluate } from './evaluate';

function ev(src: string, vars: Record<string, number> = {}): number {
  return evaluate(parseExpression(src), vars);
}

describe('parseExpression + evaluate', () => {
  it.each([
    ['2+3*4', 14],
    ['2^3^2', 512],
    ['-2^2', -4],
    ['(1+2)*3', 9],
    ['2^-1', 0.5],
    ['10/4', 2.5],
    ['pi', Math.PI],
    ['e', Math.E],
    ['e^2', Math.E ** 2],
    ['2pi', 2 * Math.PI],
    ['sqrt(16)', 4],
    ['abs(-3)', 3],
    ['|-3|', 3],
    ['2|-3|', 6],
    ['|1-4|+|2|', 5],
    ['ln(e)', 1],
    ['log(e^2)', 2],
    ['log10(1000)', 3],
    ['log2(8)', 3],
    ['exp(0)', 1],
    ['sin(0)', 0],
    ['cos(0)', 1],
    ['sin^2(0.5)+cos^2(0.5)', 1],
    ['sin^(-1)(1)', Math.PI / 2],
    ['arcsin(1)', Math.PI / 2],
    ['sec(0)', 1],
    ['(8)^(1/3)', 2],
    ['[1+2]*2', 6],
    ['log 2', Math.log(2)],
    ['.5+1', 1.5],
  ])('evaluates %s', (src, expected) => {
    expect(ev(src)).toBeCloseTo(expected, 10);
  });

  it.each([
    ['2x', 6],
    ['3(x+1)', 12],
    ['x(x+1)', 12],
    ['xy', 6],
    ['x y', 6],
    ['2x^2', 18],
    ['x^2y', 18],
    ['1/2x', 1.5],
    ['sin x^2', Math.sin(9)],
    ['sin 2x', Math.sin(6)],
    ['sin x cos x', Math.sin(3) * Math.cos(3)],
    ['ln x / x', Math.log(3) / 3],
    ['e^x', Math.exp(3)],
    ['2e^x', 2 * Math.exp(3)],
    ['sinx', Math.sin(3)],
    ['xsinx', 3 * Math.sin(3)],
    ['sin(x)^2', Math.sin(3) ** 2],
    ['sin^2 x', Math.sin(3) ** 2],
    ['-x^2', -9],
    ['x/-2', -1.5],
    ['sin -x', Math.sin(-3)],
    ['2|x|y', 12],
  ])('implicit multiplication / function application: %s', (src, expected) => {
    expect(ev(src, { x: 3, y: 2 })).toBeCloseTo(expected, 10);
  });

  it.each<[string, Record<string, number>]>([
    ['1/0', {}],
    ['ln(0)', {}],
    ['ln(-1)', {}],
    ['sqrt(-4)', {}],
    ['(-8)^(1/3)', {}],
    ['0^(-1)', {}],
    ['asin(2)', {}],
    ['y', { x: 1 }],
  ])('is NaN where undefined: %s', (src, vars) => {
    expect(Number.isNaN(ev(src, vars))).toBe(true);
  });

  it('evaluates inf to Infinity', () => {
    expect(ev('inf')).toBe(Infinity);
    expect(ev('-inf')).toBe(-Infinity);
    expect(ev('-infty')).toBe(-Infinity);
  });

  it('reports free variables', () => {
    expect(freeVariables(parseExpression('2x+y*sin(z)+pi+e'))).toEqual(['x', 'y', 'z']);
  });

  it.each([
    ['', 'empty'],
    ['2+', 'ends too early'],
    ['(2+3', 'closing'],
    ['2+3)', 'Unexpected ")"'],
    ['sin', 'needs an argument'],
    ['x\\pm 1', 'Unsupported notation "\\pm"'],
    ['x_1', 'Subscripts'],
    ['y=2x', 'without "="'],
    ['2**3', 'Unexpected "*"'],
    ['|x', 'closing "|"'],
    ['x^', 'Missing a value after "^"'],
    ['x#1', 'Unexpected character "#"'],
  ])('throws a readable ParseError for %s', (src, fragment) => {
    expect(() => parseExpression(src)).toThrow(ParseError);
    expect(() => parseExpression(src)).toThrow(fragment);
  });
});
