// LaTeX (as produced by MathLive) -> the grader's plain syntax.
//
// The output is what `parseExpression` in ./parser.ts understands:
//   numbers, single-letter variables, + - * / ^, ( ) [ ] | |, function names, pi, e, inf.
// Plain-syntax input passes through unchanged (the conversion is idempotent), so callers
// can run every user input and every answer key through `latexToPlain` without checking first.
//
// Rules (see the README-style comment on each helper for details):
//   \frac{a}{b}      -> ((a)/(b))            \sqrt{x} -> sqrt(x)      \sqrt[n]{x} -> ((x)^(1/(n)))
//   x^{2}            -> x^(2)                {group}  -> (group)
//   \cdot \times     -> *                    \div     -> /
//   \sin ... \ln     -> sin ... ln           \pi      -> pi           \infty -> inf
//   \left( \right)   -> ( )                  \{ \}    -> ( )          \lvert \rvert \left| -> |
//   \text{..} \mathrm{..} \operatorname{..}  -> contents
//   \sin^{-1}        -> asin (also handled by the parser for sin^(-1))
//   \log_{10} \log_{2} \log_{e} -> log10 log2 ln
//   \mathrm{d}x      -> removed (differential after an integrand)
//   spacing commands (\, \; \! \: \quad ~) and style commands are dropped.
// Anything unrecognised is left as "\name" so the parser can report it in a readable message.

/** Commands that map to a fixed replacement. Spaces guard against gluing to neighbours. */
const SIMPLE: Record<string, string> = {
  // functions
  sin: ' sin ', cos: ' cos ', tan: ' tan ', sec: ' sec ', csc: ' csc ', cot: ' cot ',
  arcsin: ' arcsin ', arccos: ' arccos ', arctan: ' arctan ',
  sinh: ' sinh ', cosh: ' cosh ', tanh: ' tanh ', coth: ' coth ', sech: ' sech ', csch: ' csch ',
  ln: ' ln ', log: ' log ', exp: ' exp ',
  // constants
  pi: ' pi ', infty: ' inf ', infin: ' inf ', exponentialE: ' e ',
  // operators
  cdot: '*', times: '*', ast: '*', div: '/', cup: ' U ',
  // delimiters
  lvert: '|', rvert: '|', vert: '|', mid: '|',
  lbrace: '(', rbrace: ')', lbrack: '[', rbrack: ']', lparen: '(', rparen: ')',
  '{': '(', '}': ')', '|': '|',
  // spacing
  ',': ' ', ';': ' ', '!': ' ', ':': ' ', ' ': ' ', quad: ' ', qquad: ' ', enspace: ' ', thinspace: ' ',
  // style / layout commands that carry no meaning
  displaystyle: '', textstyle: '', scriptstyle: '', scriptscriptstyle: '', limits: '', nolimits: '',
};

/** Commands whose single brace argument is kept as plain content. */
const CONTENT_WRAPPERS = new Set([
  'text', 'textrm', 'textit', 'textbf', 'mathrm', 'mathit', 'mathbf', 'mathsf', 'mathtt',
  'operatorname', 'mathop', 'mbox',
]);

const FENCE_COMMANDS = new Set(['left', 'right', 'mleft', 'mright', 'bigl', 'bigr', 'Bigl', 'Bigr', 'biggl', 'biggr', 'Biggl', 'Biggr', 'big', 'Big', 'bigg', 'Bigg']);

const UNICODE: [RegExp, string][] = [
  [/[−–—]/g, '-'],       // minus sign, en dash, em dash
  [/[×⋅·∗]/g, '*'], // times, dot operator, middle dot, asterisk operator
  [/÷/g, '/'],
  [/∞/g, ' inf '],
  [/π/g, ' pi '],
  [/√/g, ' sqrt '],
  [/²/g, '^2'],
  [/³/g, '^3'],
  [/∪/g, ' U '],
  [/≤/g, '<='], [/≥/g, '>='],
];

/** Index of the bracket matching the one at `open`, or -1 if unbalanced. */
function findMatching(s: string, open: number, lch: string, rch: string): number {
  let depth = 0;
  for (let i = open; i < s.length; i++) {
    const c = s[i];
    if (c === '\\') { i++; continue; } // skip escaped char (e.g. \{ )
    if (c === lch) depth++;
    else if (c === rch) { depth--; if (depth === 0) return i; }
  }
  return -1;
}

function skipWs(s: string, i: number): number {
  while (i < s.length && /\s/.test(s[i])) i++;
  return i;
}

/**
 * Read one LaTeX argument starting at i: a {group}, a \command, or a single character.
 * Returns the raw (unconverted) argument text and the index after it.
 */
function readArg(s: string, i: number): [string, number] {
  i = skipWs(s, i);
  if (i >= s.length) return ['', i];
  if (s[i] === '{') {
    const close = findMatching(s, i, '{', '}');
    if (close === -1) return [s.slice(i + 1), s.length];
    return [s.slice(i + 1, close), close + 1];
  }
  if (s[i] === '\\') {
    let j = i + 1;
    if (j < s.length && /[a-zA-Z]/.test(s[j])) { while (j < s.length && /[a-zA-Z]/.test(s[j])) j++; }
    else j++;
    return [s.slice(i, j), j];
  }
  return [s[i], i + 1];
}

function convert(s: string): string {
  let out = '';
  let i = 0;
  while (i < s.length) {
    const ch = s[i];

    if (ch === '\\') {
      let j = i + 1;
      if (j < s.length && /[a-zA-Z]/.test(s[j])) { while (j < s.length && /[a-zA-Z]/.test(s[j])) j++; }
      else j++;
      const name = s.slice(i + 1, j);
      i = j;

      if (name === 'frac' || name === 'dfrac' || name === 'tfrac') {
        const [a, i1] = readArg(s, i);
        const [b, i2] = readArg(s, i1);
        i = i2;
        out += `((${convert(a)})/(${convert(b)}))`;
        continue;
      }
      if (name === 'sqrt') {
        const k = skipWs(s, i);
        if (s[k] === '[') {
          const close = findMatching(s, k, '[', ']');
          const n = close === -1 ? s.slice(k + 1) : s.slice(k + 1, close);
          const [a, i1] = readArg(s, close === -1 ? s.length : close + 1);
          i = i1;
          out += `((${convert(a)})^(1/(${convert(n)})))`;
        } else {
          const [a, i1] = readArg(s, i);
          i = i1;
          out += `sqrt(${convert(a)})`;
        }
        continue;
      }
      if (CONTENT_WRAPPERS.has(name)) {
        const [a, i1] = readArg(s, i);
        i = i1;
        out += ' ' + convert(a) + ' ';
        continue;
      }
      if (FENCE_COMMANDS.has(name)) {
        const k = skipWs(s, i);
        i = s[k] === '.' ? k + 1 : k; // "\left." is an invisible delimiter
        continue;
      }
      if (name === 'placeholder') {
        const [, i1] = readArg(s, i);
        i = i1;
        continue;
      }
      if (Object.prototype.hasOwnProperty.call(SIMPLE, name)) {
        out += SIMPLE[name];
        continue;
      }
      out += '\\' + name + ' '; // unknown: leave for the parser to report
      continue;
    }

    if (ch === '{') {
      const close = findMatching(s, i, '{', '}');
      const inner = close === -1 ? s.slice(i + 1) : s.slice(i + 1, close);
      i = close === -1 ? s.length : close + 1;
      const c = convert(inner).trim();
      if (c !== '') out += `(${c})`;
      continue;
    }
    if (ch === '}') { i++; continue; }

    if (ch === '^') {
      const k = skipWs(s, i + 1);
      if (s[k] === '{') {
        const close = findMatching(s, k, '{', '}');
        const inner = close === -1 ? s.slice(k + 1) : s.slice(k + 1, close);
        i = close === -1 ? s.length : close + 1;
        out += `^(${convert(inner)})`;
      } else {
        out += '^';
        i++;
      }
      continue;
    }

    if (ch === '_') {
      const [a, i1] = readArg(s, i + 1);
      const base = convert(a).trim();
      const trimmed = out.trimEnd();
      if (trimmed.endsWith('log')) {
        const head = trimmed.slice(0, -3);
        if (base === '10') out = head + ' log10 ';
        else if (base === '2') out = head + ' log2 ';
        else if (base === 'e') out = head + ' ln ';
        else out = trimmed + '_' + base;
        i = i1;
        continue;
      }
      out += '_';
      i++;
      continue;
    }

    out += ch;
    i++;
  }
  return out;
}

/** Convert MathLive LaTeX (or plain syntax) into the grader's plain syntax. Idempotent. */
export function latexToPlain(latex: string): string {
  let s = latex ?? '';
  // Math-mode delimiters around the whole input.
  s = s.trim().replace(/^\$+|\$+$/g, '').replace(/^\\[\(\[]/, '').replace(/\\[\)\]]$/, '');
  // Differentials written as \mathrm{d}x or \differentialD x are not part of the expression.
  s = s.replace(/\\mathrm\{d\}\s*[a-zA-Z]/g, ' ').replace(/\\differentialD\s*[a-zA-Z]/g, ' ');
  for (const [re, rep] of UNICODE) s = s.replace(re, rep);

  let out = convert(s);

  // sin^(-1) -> asin and friends (the parser accepts the exponent form too).
  out = out.replace(/\b(sin|cos|tan|sec|csc|cot|sinh|cosh|tanh)\s*\^\s*\(\s*-\s*1\s*\)/g, 'a$1');
  out = out.replace(/\barc(sin|cos|tan)\b/g, 'a$1');

  // Tidy whitespace: single spaces only, none next to operators or brackets.
  out = out.replace(/\s+/g, ' ').trim();
  out = out.replace(/\s*([+\-*/^(),\[\]|])\s*/g, '$1');
  return out;
}
