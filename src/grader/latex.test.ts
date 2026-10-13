import { describe, it, expect } from 'vitest';
import { latexToPlain } from './latex';

describe('latexToPlain', () => {
  it.each([
    ['\\frac{x^{2}}{2}+C', '((x^(2))/(2))+C'],
    ['\\sin\\left(x^{2}\\right)', 'sin(x^(2))'],
    ['e^{x}', 'e^(x)'],
    ['\\frac{1}{3}', '((1)/(3))'],
    ['-\\frac{1}{3}', '-((1)/(3))'],
    ['2\\pi', '2 pi'],
    ['\\sqrt{2}', 'sqrt(2)'],
    ['\\sqrt[3]{x}', '((x)^(1/(3)))'],
    ['\\left(-\\infty,3\\right]', '(-inf,3]'],
    ['3\\cdot x', '3*x'],
    ['3\\times x', '3*x'],
    ['x\\div 2', 'x/2'],
    ['\\sin^{-1}(x)', 'asin(x)'],
    ['\\arcsin x', 'asin x'],
    ['\\operatorname{sec}(x)', 'sec(x)'],
    ['\\text{abs}(x)', 'abs(x)'],
    ['\\mathrm{e}^{x}', 'e^(x)'],
    ['\\lvert x\\rvert', '|x|'],
    ['\\left|x\\right|', '|x|'],
    ['\\{x+1\\}', '(x+1)'],
    ['\\left[0,1\\right)', '[0,1)'],
    ['x\\,\\mathrm{d}x', 'x'],
    ['\\log_{10}(x)', 'log10(x)'],
    ['\\log_{2}(8)', 'log2(8)'],
    ['\\ln\\left(x\\right)', 'ln(x)'],
    ['\\frac{\\pi}{2}', '((pi)/(2))'],
    ['\\dfrac{a}{b}', '((a)/(b))'],
    ['$x^2$', 'x^2'],
    ['x^{\\frac{1}{2}}', 'x^(((1)/(2)))'],
    ['\\placeholder{}x', 'x'],
    ['2\\sin x\\cos x', '2 sin x cos x'],
    ['x^2 − 1', 'x^2-1'],
    ['π x', 'pi x'],
    ['(−∞, 3]', '(-inf,3]'],
  ])('converts %s', (latex, plain) => {
    expect(latexToPlain(latex)).toBe(plain);
  });

  it('is idempotent on its own output and on plain syntax', () => {
    const inputs = ['\\frac{x^{2}}{2}+C', '\\sin^{-1}(x)', 'sqrt(x)+2x', '(x)^(1/3)', '|x|', 'sin(x^2)+5', '2pi', 'abs(x)'];
    for (const s of inputs) {
      const once = latexToPlain(s);
      expect(latexToPlain(once)).toBe(once);
    }
  });

  it('leaves unknown commands for the parser to report', () => {
    expect(latexToPlain('x\\pm 1')).toContain('\\pm');
  });

  it('handles nested fractions', () => {
    expect(latexToPlain('\\frac{\\frac{1}{x}}{2}')).toBe('((((1)/(x)))/(2))');
  });
});
