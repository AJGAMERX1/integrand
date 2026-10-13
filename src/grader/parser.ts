// Recursive-descent parser for the grader's plain syntax.
//
// Grammar (lowest to highest precedence):
//   expr    := term (('+' | '-') term)*
//   term    := unary (('*' | '/') unary | <implicit> power)*       implicit multiplication: 2x, 3(x+1), x y, 2|x|
//   unary   := ('-' | '+') unary | power
//   power   := primary ('^' unary)?                                 right-associative; x^-2 allowed
//   primary := number | constant | variable | '(' expr ')' | '[' expr ']' | '|' expr '|' | funcall
//   funcall := name ('^' unary)? ( '(' expr ')' | funcarg )
//   funcarg := ('-' | '+')? power (<implicit> power)*   stops at the next function name or explicit operator
//
// Rules worth knowing:
//   - Implicit multiplication binds like '*': "1/2x" is (1/2)*x, "x^2y" is (x^2)*y.
//   - A function without parentheses applies to the following product of power-factors:
//     "sin x^2" = sin(x^2), "sin 2x" = sin(2x), "sin x cos x" = sin(x)*cos(x), "ln x / x" = ln(x)/x.
//   - "sin^2(x)" = (sin(x))^2 and "sin^(-1)(x)" = asin(x).
//   - A run of letters is split greedily into known names then single-letter variables:
//     "xy" = x*y, "2pi" = 2*pi, "e^x" uses the constant e, "sinx" = sin(x). (Single-letter variables only.)
//   - "log" is the natural log. "log10(...)" / "log2(...)" are base-10 / base-2 only when written
//     glued and followed by "(": "log 2x" is log(2x).
//   - "x(x+1)" is multiplication because x is not a function; "f(x)" would be f*x.
// Errors throw ParseError with a short learner-facing message.

export type Expr =
  | { kind: 'num'; value: number }
  | { kind: 'const'; name: 'pi' | 'e' | 'inf' }
  | { kind: 'var'; name: string }
  | { kind: 'neg'; arg: Expr }
  | { kind: 'bin'; op: '+' | '-' | '*' | '/' | '^'; left: Expr; right: Expr }
  | { kind: 'call'; fn: string; arg: Expr };

export class ParseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ParseError';
  }
}

/** Canonical function names understood by the evaluator. */
export const FUNCTIONS = new Set([
  'sin', 'cos', 'tan', 'sec', 'csc', 'cot',
  'asin', 'acos', 'atan',
  'sinh', 'cosh', 'tanh', 'coth', 'sech', 'csch',
  'exp', 'ln', 'log', 'log10', 'log2', 'sqrt', 'abs',
]);

/** Aliases accepted in input. */
const FUNCTION_ALIASES: Record<string, string> = {
  arcsin: 'asin', arccos: 'acos', arctan: 'atan',
};

const CONSTANT_ALIASES: Record<string, 'pi' | 'e' | 'inf'> = {
  pi: 'pi', e: 'e', inf: 'inf', infty: 'inf', infinity: 'inf', oo: 'inf',
};

/** Names tried (longest first) when splitting a run of letters. */
const KNOWN_NAMES = [...FUNCTIONS, ...Object.keys(FUNCTION_ALIASES), ...Object.keys(CONSTANT_ALIASES)]
  .filter((n) => n.length > 1)
  .sort((a, b) => b.length - a.length);

type Token =
  | { type: 'num'; value: number; text: string }
  | { type: 'func'; name: string; text: string }
  | { type: 'const'; name: 'pi' | 'e' | 'inf'; text: string }
  | { type: 'var'; name: string; text: string }
  | { type: 'op'; value: '+' | '-' | '*' | '/' | '^'; text: string }
  | { type: 'lparen'; text: '(' | '[' }
  | { type: 'rparen'; text: ')' | ']' }
  | { type: 'bar'; text: '|' }
  | { type: 'comma'; text: ',' }
  | { type: 'end'; text: '' };

function tokenize(src: string): Token[] {
  const tokens: Token[] = [];
  let i = 0;
  while (i < src.length) {
    const ch = src[i];
    if (/\s/.test(ch)) { i++; continue; }

    if (/[0-9.]/.test(ch)) {
      const m = /^(\d+\.?\d*|\.\d+)/.exec(src.slice(i));
      if (!m || m[0] === '.') throw new ParseError('A number is missing its digits');
      tokens.push({ type: 'num', value: Number(m[0]), text: m[0] });
      i += m[0].length;
      continue;
    }

    if (/[a-zA-Z]/.test(ch)) {
      let j = i;
      while (j < src.length && /[a-zA-Z]/.test(src[j])) j++;
      const run = src.slice(i, j);
      let k = 0;
      while (k < run.length) {
        const rest = run.slice(k);
        const name = KNOWN_NAMES.find((n) => rest.startsWith(n));
        if (name) {
          if (name in CONSTANT_ALIASES) tokens.push({ type: 'const', name: CONSTANT_ALIASES[name], text: name });
          else tokens.push({ type: 'func', name: FUNCTION_ALIASES[name] ?? name, text: name });
          k += name.length;
        } else {
          const letter = run[k];
          if (letter === 'e') tokens.push({ type: 'const', name: 'e', text: 'e' });
          else tokens.push({ type: 'var', name: letter, text: letter });
          k++;
        }
      }
      i = j;
      // "log10(" / "log2(" glued to a base and followed by "(".
      const last = tokens[tokens.length - 1];
      if (last && last.type === 'func' && last.name === 'log') {
        const base = /^(10|2)\s*\(/.exec(src.slice(i));
        if (base) {
          last.name = 'log' + base[1];
          last.text = 'log' + base[1];
          i += base[1].length;
        }
      }
      continue;
    }

    if ('+-*/^'.includes(ch)) { tokens.push({ type: 'op', value: ch as '+' | '-' | '*' | '/' | '^', text: ch }); i++; continue; }
    if (ch === '(' || ch === '[') { tokens.push({ type: 'lparen', text: ch }); i++; continue; }
    if (ch === ')' || ch === ']') { tokens.push({ type: 'rparen', text: ch }); i++; continue; }
    if (ch === '|') { tokens.push({ type: 'bar', text: '|' }); i++; continue; }
    if (ch === ',') { tokens.push({ type: 'comma', text: ',' }); i++; continue; }

    if (ch === '\\') {
      const m = /^\\([a-zA-Z]+|.)/.exec(src.slice(i));
      throw new ParseError(`Unsupported notation "${m ? m[0] : '\\'}"`);
    }
    if (ch === '_') throw new ParseError('Subscripts are not supported here');
    if (ch === '=') throw new ParseError('Enter just the expression, without "="');
    if (ch === '{' || ch === '}') throw new ParseError('Use parentheses ( ) instead of braces { }');
    throw new ParseError(`Unexpected character "${ch}"`);
  }
  tokens.push({ type: 'end', text: '' });
  return tokens;
}

class Parser {
  private pos = 0;
  private absDepth = 0;
  constructor(private tokens: Token[]) {}

  private peek(): Token { return this.tokens[this.pos]; }
  private next(): Token { return this.tokens[this.pos++]; }
  private isOp(t: Token, v: string): boolean { return t.type === 'op' && t.value === v; }

  parse(): Expr {
    const e = this.parseExpr();
    const t = this.peek();
    if (t.type !== 'end') {
      if (t.type === 'rparen') throw new ParseError(`Unexpected "${t.text}" (no matching opening bracket)`);
      if (t.type === 'comma') throw new ParseError('Unexpected comma');
      throw new ParseError(`Unexpected "${t.text}"`);
    }
    return e;
  }

  private parseExpr(): Expr {
    let left = this.parseTerm();
    for (;;) {
      const t = this.peek();
      if (this.isOp(t, '+') || this.isOp(t, '-')) {
        this.next();
        const right = this.parseTerm();
        left = { kind: 'bin', op: t.text as '+' | '-', left, right };
      } else return left;
    }
  }

  /** Can this token begin an implicitly-multiplied factor? */
  private startsFactor(t: Token): boolean {
    switch (t.type) {
      case 'num': case 'func': case 'const': case 'var': case 'lparen': return true;
      case 'bar': return this.absDepth === 0;
      default: return false;
    }
  }

  private parseTerm(): Expr {
    let left = this.parseUnary();
    for (;;) {
      const t = this.peek();
      if (this.isOp(t, '*') || this.isOp(t, '/')) {
        this.next();
        const right = this.parseUnary();
        left = { kind: 'bin', op: t.text as '*' | '/', left, right };
      } else if (this.startsFactor(t)) {
        const right = this.parsePower();
        left = { kind: 'bin', op: '*', left, right };
      } else return left;
    }
  }

  private parseUnary(): Expr {
    const t = this.peek();
    if (this.isOp(t, '-')) { this.next(); return { kind: 'neg', arg: this.parseUnary() }; }
    if (this.isOp(t, '+')) { this.next(); return this.parseUnary(); }
    return this.parsePower();
  }

  private parsePower(): Expr {
    const base = this.parsePrimary();
    if (this.isOp(this.peek(), '^')) {
      this.next();
      this.requireValue('^');
      const exponent = this.parseUnary();
      return { kind: 'bin', op: '^', left: base, right: exponent };
    }
    return base;
  }

  private requireValue(after: string): void {
    const t = this.peek();
    if (t.type === 'end') throw new ParseError(`Missing a value after "${after}"`);
    if (t.type === 'rparen' || t.type === 'comma' || (t.type === 'op' && t.value !== '-' && t.value !== '+')) {
      throw new ParseError(`Missing a value after "${after}"`);
    }
  }

  private parsePrimary(): Expr {
    const t = this.next();
    switch (t.type) {
      case 'num': return { kind: 'num', value: t.value };
      case 'const': return { kind: 'const', name: t.name };
      case 'var': return { kind: 'var', name: t.name };
      case 'lparen': {
        const close = t.text === '(' ? ')' : ']';
        this.requireValue(t.text);
        const savedDepth = this.absDepth;
        this.absDepth = 0;
        const e = this.parseExpr();
        this.absDepth = savedDepth;
        const c = this.next();
        if (c.type !== 'rparen') throw new ParseError(`Missing a closing "${close}"`);
        return e;
      }
      case 'bar': {
        this.absDepth++;
        this.requireValue('|');
        const e = this.parseExpr();
        this.absDepth--;
        const c = this.next();
        if (c.type !== 'bar') throw new ParseError('Missing a closing "|" for the absolute value');
        return { kind: 'call', fn: 'abs', arg: e };
      }
      case 'func': return this.parseFunction(t.name, t.text);
      case 'end': throw new ParseError('The expression ends too early');
      case 'rparen': throw new ParseError(`Unexpected "${t.text}"`);
      case 'comma': throw new ParseError('Unexpected comma');
      case 'op': throw new ParseError(`Unexpected "${t.text}"`);
    }
  }

  private parseFunction(fn: string, text: string): Expr {
    // Optional exponent written on the function name: sin^2(x), sin^(-1)(x).
    let exponent: Expr | null = null;
    if (this.isOp(this.peek(), '^')) {
      this.next();
      this.requireValue('^');
      exponent = this.parseUnary();
    }
    let arg: Expr;
    const t = this.peek();
    if (t.type === 'lparen') {
      this.next();
      this.requireValue(`${text}(`);
      const savedDepth = this.absDepth;
      this.absDepth = 0;
      arg = this.parseExpr();
      this.absDepth = savedDepth;
      const c = this.next();
      if (c.type !== 'rparen') throw new ParseError(`Missing a closing parenthesis after ${text}(`);
    } else if (this.startsFactor(t) || this.isOp(t, '-') || this.isOp(t, '+')) {
      arg = this.parseFuncArg();
    } else {
      throw new ParseError(`"${text}" needs an argument, e.g. ${text}(x)`);
    }

    if (exponent === null) return { kind: 'call', fn, arg };
    const inverse = inverseOf(fn);
    if (inverse && isMinusOne(exponent)) return { kind: 'call', fn: inverse, arg };
    return { kind: 'bin', op: '^', left: { kind: 'call', fn, arg }, right: exponent };
  }

  /** Argument of a function written without parentheses: a product of power-factors. */
  private parseFuncArg(): Expr {
    const t = this.peek();
    if (this.isOp(t, '-')) { this.next(); return { kind: 'neg', arg: this.parseFuncArg() }; }
    if (this.isOp(t, '+')) { this.next(); return this.parseFuncArg(); }
    let node = this.parsePower();
    for (;;) {
      const n = this.peek();
      if (n.type === 'func' || !this.startsFactor(n)) return node;
      const right = this.parsePower();
      node = { kind: 'bin', op: '*', left: node, right };
    }
  }
}

function inverseOf(fn: string): string | null {
  switch (fn) {
    case 'sin': return 'asin';
    case 'cos': return 'acos';
    case 'tan': return 'atan';
    default: return null;
  }
}

function isMinusOne(e: Expr): boolean {
  return e.kind === 'neg' && e.arg.kind === 'num' && e.arg.value === 1;
}

/** Parse plain syntax into an Expr. Throws ParseError on bad input. */
export function parseExpression(src: string): Expr {
  if (typeof src !== 'string' || src.trim() === '') throw new ParseError('The expression is empty');
  return new Parser(tokenize(src)).parse();
}

/** Names of the free variables used in an expression (constants pi/e/inf excluded). */
export function freeVariables(expr: Expr): string[] {
  const seen = new Set<string>();
  const walk = (e: Expr): void => {
    switch (e.kind) {
      case 'var': seen.add(e.name); break;
      case 'neg': walk(e.arg); break;
      case 'bin': walk(e.left); walk(e.right); break;
      case 'call': walk(e.arg); break;
      default: break;
    }
  };
  walk(expr);
  return [...seen].sort();
}
