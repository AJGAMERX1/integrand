import { describe, it, expect } from 'vitest';
import type { Problem } from '../types';
import { grade, equivalent, checkNumeric, checkInterval, parseExpression, evaluate, latexToPlain } from './index';

function problem(overrides: Partial<Problem>): Problem {
  return {
    id: 'p',
    skill: 'test',
    difficulty: 1,
    statement: '',
    checker: 'equiv',
    answer: 'x',
    hints: [],
    solution: [],
    verified: true,
    ...overrides,
  };
}

describe('grade: equiv', () => {
  const p = problem({ checker: 'equiv', answer: '2x+2' });

  it('accepts 2(x+1) for 2x+2', () => {
    const r = grade(p, '2(x+1)');
    expect(r.correct).toBe(true);
    expect(r.reason).toBe('Correct');
  });

  it('accepts MathLive LaTeX 2\\left(x+1\\right)', () => {
    expect(grade(p, '2\\left(x+1\\right)').correct).toBe(true);
  });

  it('rejects a wrong answer with a learner-facing reason', () => {
    const r = grade(p, '2x+3');
    expect(r.correct).toBe(false);
    expect(r.reason).toBe('Differs from the expected answer by a constant term');
  });

  it('rejects a wrong expression', () => {
    const r = grade(p, 'x^2');
    expect(r.correct).toBe(false);
    expect(r.reason).toBe('Not equivalent to the expected expression');
  });

  it('detects a wrong constant factor', () => {
    expect(grade(p, '4x+4').reason).toBe('Off by a constant factor');
  });

  it('detects a sign error', () => {
    expect(grade(p, '-2x-2').reason).toBe('Sign error: this is the negative of the expected answer');
  });

  it('reports an unknown variable', () => {
    const r = grade(p, '2y+2');
    expect(r.correct).toBe(false);
    expect(r.reason).toContain('"y"');
  });

  it('returns a readable reason on a parse error instead of throwing', () => {
    const r = grade(p, '2x+');
    expect(r.correct).toBe(false);
    expect(r.reason).toMatch(/^Couldn't read your answer: /);
  });

  it('returns a readable reason for unsupported LaTeX', () => {
    const r = grade(p, '2x\\pm 2');
    expect(r.correct).toBe(false);
    expect(r.reason).toContain('\\pm');
  });

  it('rejects an empty answer', () => {
    expect(grade(p, '   ').correct).toBe(false);
    expect(grade(p, '').reason).toBe('Enter an answer first');
  });

  it('sets normalizedInput to the plain syntax', () => {
    expect(grade(p, '2\\cdot x+2').normalizedInput).toBe('2*x+2');
  });

  it('is deterministic', () => {
    const a = grade(p, '2(x+1)');
    const b = grade(p, '2(x+1)');
    expect(a).toEqual(b);
  });

  it('handles trig identities and e^x', () => {
    expect(grade(problem({ answer: '1' }), '\\sin^{2}(x)+\\cos^{2}(x)').correct).toBe(true);
    expect(grade(problem({ answer: 'exp(x)' }), 'e^{x}').correct).toBe(true);
    expect(grade(problem({ answer: 'sin(2x)' }), '2\\sin x\\cos x').correct).toBe(true);
  });

  it('respects a custom variable', () => {
    expect(grade(problem({ answer: '3t^2', variable: 't' }), '3t^{2}').correct).toBe(true);
    expect(grade(problem({ answer: '3t^2', variable: 't' }), '3x^{2}').correct).toBe(false);
  });

  it('accepts +C only when the checker is equiv_plus_c', () => {
    expect(grade(problem({ checker: 'equiv', answer: '2x' }), '2x+C').correct).toBe(false);
  });
});

describe('grade: equiv_plus_c', () => {
  const p = problem({ checker: 'equiv_plus_c', answer: 'sin(x^2)' });

  it('accepts sin(x^2)+C', () => {
    expect(grade(p, 'sin(x^2)+C').correct).toBe(true);
  });

  it('accepts sin(x^2) + c (lowercase, spaces)', () => {
    expect(grade(p, 'sin(x^2) + c').correct).toBe(true);
  });

  it('accepts a missing + C', () => {
    expect(grade(p, 'sin(x^2)').correct).toBe(true);
  });

  it('accepts a different constant: sin(x^2)+5', () => {
    expect(grade(p, 'sin(x^2)+5').correct).toBe(true);
  });

  it('accepts C written first', () => {
    expect(grade(p, 'C+\\sin\\left(x^{2}\\right)').correct).toBe(true);
  });

  it('rejects 2sin(x^2) as a wrong constant factor', () => {
    const r = grade(p, '2sin(x^2)');
    expect(r.correct).toBe(false);
    expect(r.reason).toBe('Off by a constant factor');
  });

  it('rejects 2sin(x^2)+C', () => {
    expect(grade(p, '2\\sin\\left(x^{2}\\right)+C').correct).toBe(false);
  });

  it('accepts MathLive \\frac{x^{2}}{2}+C for x^2/2', () => {
    const q = problem({ checker: 'equiv_plus_c', answer: 'x^2/2' });
    const r = grade(q, '\\frac{x^{2}}{2}+C');
    expect(r.correct).toBe(true);
    expect(r.normalizedInput).toBe('((x^(2))/(2))');
  });

  it('rejects a wrong antiderivative', () => {
    expect(grade(problem({ checker: 'equiv_plus_c', answer: 'x^3/3' }), 'x^2+C').correct).toBe(false);
  });
});

describe('grade: domain edges', () => {
  it('accepts ln(x) vs ln(x) on [-2,2] where half the domain is undefined', () => {
    expect(grade(problem({ answer: 'ln(x)', domain: [-2, 2] }), '\\ln\\left(x\\right)').correct).toBe(true);
  });

  it('accepts abs(sqrt(x)) for sqrt(x)', () => {
    expect(grade(problem({ answer: 'sqrt(x)' }), '\\left|\\sqrt{x}\\right|').correct).toBe(true);
  });

  it('rejects -sqrt(x) for sqrt(x)', () => {
    expect(grade(problem({ answer: 'sqrt(x)' }), '-\\sqrt{x}').correct).toBe(false);
  });

  it('accepts 1/x vs x^-1 across the pole at 0', () => {
    expect(grade(problem({ answer: '1/x' }), 'x^{-1}').correct).toBe(true);
  });

  it('accepts tan(x) vs sin(x)/cos(x)', () => {
    expect(grade(problem({ answer: 'tan(x)' }), '\\frac{\\sin x}{\\cos x}').correct).toBe(true);
  });

  it('reports an answer undefined everywhere on the domain', () => {
    const r = grade(problem({ answer: 'x', domain: [0, 1] }), '\\sqrt{-1-x^{2}}');
    expect(r.correct).toBe(false);
    expect(r.reason).toContain('undefined');
  });

  it('reports when domains do not overlap enough', () => {
    const r = grade(problem({ answer: 'sqrt(x)', domain: [-3, 3] }), '\\sqrt{-x}');
    expect(r.correct).toBe(false);
    expect(r.reason).toContain('different parts of the domain');
  });

  it('sqrt(x^2) is not x on a domain containing negatives', () => {
    expect(grade(problem({ answer: 'x' }), '\\sqrt{x^{2}}').correct).toBe(false);
    expect(grade(problem({ answer: 'x', domain: [0, 3] }), '\\sqrt{x^{2}}').correct).toBe(true);
  });
});

describe('grade: numeric', () => {
  const third = problem({ checker: 'numeric', answer: '1/3' });

  it.each([
    ['1/3', true],
    ['\\frac{1}{3}', true],
    ['0.333', true],
    ['0.3333', true],
    ['0.33333333', true],
    ['.333', true],
    ['0.3', false],
    ['0.33', false],
    ['0.334', false],
    ['1/4', false],
    ['x', false],
  ])('1/3 vs %s -> %s', (input, ok) => {
    expect(grade(third, input).correct).toBe(ok);
  });

  it('tells the learner to give more decimals when a short decimal rounds correctly', () => {
    expect(grade(third, '0.3').reason).toContain('3 decimal places');
  });

  it('accepts exact forms: 2pi, sqrt(2), -\\frac{1}{3}, e^{2}', () => {
    expect(grade(problem({ checker: 'numeric', answer: '6.283185307179586' }), '2\\pi').correct).toBe(true);
    expect(grade(problem({ checker: 'numeric', answer: '1.4142135623730951' }), '\\sqrt{2}').correct).toBe(true);
    expect(grade(problem({ checker: 'numeric', answer: '-1/3' }), '-\\frac{1}{3}').correct).toBe(true);
    expect(grade(problem({ checker: 'numeric', answer: 'e^2' }), '7.389').correct).toBe(true);
  });

  it('accepts integers and rejects near misses', () => {
    const p = problem({ checker: 'numeric', answer: '2.5' });
    expect(grade(p, '2.5').correct).toBe(true);
    expect(grade(p, '5/2').correct).toBe(true);
    expect(grade(p, '2.6').correct).toBe(false);
    expect(grade(p, '2.4999').correct).toBe(false);
  });

  it('honours a problem tolerance', () => {
    const p = problem({ checker: 'numeric', answer: '3.14159', tolerance: 0.01 });
    expect(grade(p, '3.14').correct).toBe(true);
    expect(grade(p, '3.1').correct).toBe(false);
  });

  it('rejects an expression with a variable', () => {
    const r = grade(third, '2x');
    expect(r.correct).toBe(false);
    expect(r.reason).toContain('"x"');
  });

  it('never throws on garbage', () => {
    expect(grade(third, '1/').correct).toBe(false);
    expect(grade(third, '1/0').correct).toBe(false);
  });
});

describe('grade: choice', () => {
  const p = problem({ checker: 'choice', answer: '2', choices: ['a', 'b', 'c'] });
  it('accepts the matching index string', () => {
    expect(grade(p, '2').correct).toBe(true);
    expect(grade(p, ' 2 ').correct).toBe(true);
  });
  it('rejects a different index', () => {
    const r = grade(p, '1');
    expect(r.correct).toBe(false);
    expect(r.reason).toBe("That's not the right option");
  });
});

describe('grade: interval', () => {
  it.each([
    ['(-inf,3]', '\\left(-\\infty,3\\right]', true],
    ['(-inf,3]', '(-\\infty, 3]', true],
    ['(-inf,3]', '(-inf, 3)', false],
    ['(-inf,3]', '(-inf, 4]', false],
    ['[0,1)', '[0,1)', true],
    ['[0,1)', '\\left[0,1\\right)', true],
    ['[0,1)', '(0,1)', false],
    ['[0,1)', '[0,1]', false],
    ['(0,pi/2)', '\\left(0,\\frac{\\pi}{2}\\right)', true],
    ['(0,inf)', '(0, \\infty)', true],
    ['(0,inf)', '(0, \\infty]', false],
    ['(-1,1)', '(-1,1) U (2,3)', false],
    ['(-inf,0) U (0,inf)', '(0,\\infty)\\cup(-\\infty,0)', true],
    ['(-inf,0) U (0,inf)', '(-\\infty,0)\\cup(0,\\infty)', true],
  ])('%s vs %s -> %s', (answer, input, ok) => {
    expect(grade(problem({ checker: 'interval', answer }), input).correct).toBe(ok);
  });

  it('gives a bracket-specific reason', () => {
    expect(grade(problem({ checker: 'interval', answer: '[0,1)' }), '(0,1)').reason).toContain('included');
  });

  it('gives an endpoint-specific reason', () => {
    expect(grade(problem({ checker: 'interval', answer: '[0,1)' }), '[0,2)').reason).toContain('endpoints');
  });

  it('returns a readable reason for something that is not an interval', () => {
    const r = grade(problem({ checker: 'interval', answer: '[0,1)' }), 'x>0');
    expect(r.correct).toBe(false);
    expect(r.reason).toMatch(/^Couldn't read your answer/);
  });
});

describe('exported helpers', () => {
  it('equivalent()', () => {
    expect(equivalent('2x+2', '2(x+1)')).toBe(true);
    expect(equivalent('2x+2', '2x')).toBe(false);
    expect(equivalent('sin(x^2)+C', 'sin(x^2)', { plusC: true })).toBe(true);
    expect(equivalent('2sin(x^2)', 'sin(x^2)', { plusC: true })).toBe(false);
    expect(equivalent('ln(x)', 'ln(x)', { domain: [-2, 2] })).toBe(true);
    expect(equivalent('3t', 't+t+t', { variable: 't' })).toBe(true);
    expect(equivalent('2x+', '2x')).toBe(false);
  });

  it('checkNumeric()', () => {
    expect(checkNumeric('0.333', '1/3')).toBe(true);
    expect(checkNumeric('0.3', '1/3')).toBe(false);
    expect(checkNumeric('2\\pi', '2pi')).toBe(true);
    expect(checkNumeric('sqrt(2)', '1.41421356237')).toBe(true);
    expect(checkNumeric('3.14', '3.14159', 0.01)).toBe(true);
    expect(checkNumeric('garbage(', '1')).toBe(false);
  });

  it('checkInterval()', () => {
    expect(checkInterval('\\left(-\\infty,3\\right]', '(-inf,3]')).toBe(true);
    expect(checkInterval('(-inf,3)', '(-inf,3]')).toBe(false);
    expect(checkInterval('nope', '(-inf,3]')).toBe(false);
  });

  it('parseExpression() + evaluate() + latexToPlain() round trip', () => {
    const expr = parseExpression(latexToPlain('\\frac{x^{2}}{2}'));
    expect(evaluate(expr, { x: 4 })).toBe(8);
  });
});
