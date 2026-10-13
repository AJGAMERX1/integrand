"""
problemkit: shared helpers for the Integrand problem pipeline.

Templates (tools/templates/*.py) build problems with `make_problem(...)`, attaching a `_verify` spec.
`verify(problem)` re-derives the answer independently with SymPy and rejects anything that does not match.
`write_bank(...)` dedupes, strips private fields, and writes data/problems/<node-id>.json.
Rejections are appended to tools/rejected.log. Nothing is ever written with verified != True.

Answer syntax (what the client grader parses):  + - * / ^ ( )  sin cos tan sec csc cot asin acos atan sinh cosh tanh exp ln log sqrt abs  pi e
Use `plain(expr)` to convert a SymPy expression to that syntax and `ltx(expr)` for LaTeX in statements.
"""
from __future__ import annotations
import json, os, re, random, hashlib
import sympy as sp
from sympy import Symbol, symbols, sin, cos, tan, exp, log, sqrt, pi, E, Rational, oo, Abs

x, t, u = symbols('x t u')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK_DIR = os.path.join(ROOT, 'data', 'problems')
REJECT_LOG = os.path.join(ROOT, 'tools', 'rejected.log')

# ---------- formatting ----------

def plain(expr) -> str:
    """SymPy expression -> grader plain syntax."""
    s = sp.sstr(sp.sympify(expr))
    s = s.replace('**', '^').replace('log(', 'ln(').replace('Abs(', 'abs(').replace('E', 'e') if 'E' in s and 'Eq' not in s else s.replace('**', '^').replace('log(', 'ln(').replace('Abs(', 'abs(')
    s = re.sub(r'\bexp\(', 'exp(', s)
    return s.replace(' ', '')

def ltx(expr) -> str:
    """SymPy expression -> LaTeX for KaTeX. ln instead of log, no Abs bars issues."""
    return sp.latex(sp.sympify(expr), ln_notation=True)

def rat(a, b=1):
    return Rational(a, b)

def fmt_num(v) -> str:
    """Number (int, Rational, float) -> answer string like '3', '-1/3', '2.5'."""
    v = sp.nsimplify(v) if not isinstance(v, (int, float)) else v
    if isinstance(v, float):
        return repr(round(v, 10)).rstrip('0').rstrip('.') if '.' in repr(v) else repr(v)
    if v == sp.zoo or v == oo or v == -oo or v is sp.nan:
        raise ValueError('non-finite numeric answer')
    if v.is_Integer:
        return str(int(v))
    if v.is_Rational:
        return f"{v.p}/{v.q}"
    return plain(v)

# ---------- problem construction ----------

def pid(skill: str, seed_text: str) -> str:
    h = hashlib.sha1(seed_text.encode()).hexdigest()[:6]
    return f"{skill}-{h}"

def make_problem(skill: str, statement: str, checker: str, answer: str, *, difficulty: int = 1,
                 hints: list[str], solution: list[str], verify: dict, variable: str = 'x',
                 domain: tuple | None = None, choices: list[str] | None = None, tolerance: float | None = None,
                 tier: int | None = None, tags: list[str] | None = None) -> dict:
    assert checker in ('equiv', 'equiv_plus_c', 'numeric', 'choice', 'interval'), checker
    assert len(hints) == 2, 'exactly two hints'
    assert len(solution) >= 2, 'solution needs at least two steps'
    p = {
        'id': pid(skill, statement + '|' + answer),
        'skill': skill, 'difficulty': int(difficulty), 'statement': statement, 'checker': checker, 'answer': answer,
        'hints': hints, 'solution': solution, 'verified': False, '_verify': verify,
    }
    if checker in ('equiv', 'equiv_plus_c'):
        p['variable'] = variable
        p['domain'] = list(domain) if domain else [-3, 3]
    if checker == 'choice':
        assert choices and len(choices) >= 3, 'choice needs >= 3 options'
        p['choices'] = choices
    if tolerance is not None:
        p['tolerance'] = tolerance
    if tier is not None:
        p['tier'] = tier
    if tags:
        p['tags'] = tags
    return p

# ---------- verification ----------

_LOCALS = {'e': E, 'pi': pi, 'ln': log, 'log': log, 'abs': Abs, 'inf': oo, 'oo': oo}

def parse_plain(s: str):
    """Parse grader plain syntax into SymPy (for checking answer strings round-trip)."""
    s2 = s.replace('^', '**')
    s2 = re.sub(r'(?<=[0-9)])(?=[a-zA-Z(])', '*', s2)  # implicit multiplication 2x, 3(x+1)
    s2 = re.sub(r'(?<=[a-zA-Z)])(?=\()', '*', s2) if False else s2
    return sp.sympify(s2, locals=_LOCALS)

def _same(a, b, var=x, dom=(-3, 3), samples=12, plus_c=False) -> bool:
    a, b = sp.sympify(a), sp.sympify(b)
    try:
        if plus_c:
            d = sp.simplify(sp.diff(a - b, var))
            if d == 0:
                return True
        else:
            if sp.simplify(a - b) == 0:
                return True
    except Exception:
        pass
    # numeric fallback
    rng = random.Random(1234)
    ok = 0
    diffs = []
    for _ in range(samples * 3):
        v = rng.uniform(dom[0], dom[1])
        try:
            av, bv = complex(a.subs(var, v)), complex(b.subs(var, v))
        except Exception:
            continue
        if any(abs(z.imag) > 1e-9 or abs(z.real) > 1e12 for z in (av, bv)):
            continue
        if plus_c:
            diffs.append(av.real - bv.real)
        else:
            if abs(av.real - bv.real) > 1e-6 * max(1.0, abs(av.real), abs(bv.real)):
                return False
        ok += 1
        if ok >= samples:
            break
    if ok < 4:
        return False
    if plus_c:
        return max(diffs) - min(diffs) < 1e-6 * max(1.0, abs(diffs[0]))
    return True

def verify(p: dict) -> tuple[bool, str]:
    """Return (ok, reason). Independently re-derives the key from p['_verify']."""
    v = p.get('_verify') or {}
    kind = v.get('kind')
    var = Symbol(p.get('variable', 'x'))
    dom = tuple(p.get('domain', [-3, 3]))
    try:
        if p['checker'] in ('equiv', 'equiv_plus_c'):
            key = parse_plain(p['answer'])
        if kind == 'derivative':          # answer == d/dvar expr
            expected = sp.diff(sp.sympify(v['expr']), var)
            return (_same(key, expected, var, dom), f"derivative of {v['expr']}")
        if kind == 'integral':            # d/dvar answer == integrand (indefinite)
            integrand = sp.sympify(v['integrand'])
            return (_same(sp.diff(key, var), integrand, var, dom), f"d/d{var} of answer vs integrand {v['integrand']}")
        if kind == 'definite':            # numeric answer == integral over [a,b]
            val = sp.integrate(sp.sympify(v['integrand']), (var, sp.sympify(v['a']), sp.sympify(v['b'])))
            return (_num_match(p['answer'], val, p.get('tolerance')), f"definite integral = {val}")
        if kind == 'limit':
            val = sp.limit(sp.sympify(v['expr']), var, sp.sympify(v['to']), v.get('dir', '+'))
            if p['checker'] == 'numeric':
                return (_num_match(p['answer'], val, p.get('tolerance')), f"limit = {val}")
            return (_choice_match(p, val), f"limit = {val}")
        if kind == 'equiv':               # answer equivalent to expected expression
            expected = sp.sympify(v['expected'])
            return (_same(key, expected, var, dom, plus_c=(p['checker'] == 'equiv_plus_c')), f"expected {v['expected']}")
        if kind == 'numeric':             # answer == value
            return (_num_match(p['answer'], sp.sympify(v['value']), p.get('tolerance')), f"value {v['value']}")
        if kind == 'solve':               # numeric answer is the unique solution of eq (lhs=rhs) in var
            sols = sp.solve(sp.Eq(sp.sympify(v['lhs']), sp.sympify(v['rhs'])), var)
            if v.get('pick') is not None:
                sols = [sp.sympify(v['pick'])] if sp.sympify(v['pick']) in sols else []
            if len(sols) != 1:
                return (False, f"expected one solution, got {sols}")
            return (_num_match(p['answer'], sols[0], p.get('tolerance')), f"solution {sols[0]}")
        if kind == 'choice':              # correct option (by index) equals expected
            return (_choice_match(p, sp.sympify(v['expected'])), f"expected {v['expected']}")
        if kind == 'interval':
            return (_interval_match(p['answer'], v), 'interval')
        if kind == 'evaluate':            # numeric: expr at var=at
            val = sp.sympify(v['expr']).subs(var, sp.sympify(v['at']))
            return (_num_match(p['answer'], val, p.get('tolerance')), f"value {val}")
        return (False, f"unknown verify kind {kind}")
    except Exception as ex:  # any exception = reject
        return (False, f"exception: {ex!r}")

def _num_match(answer: str, val, tol=None) -> bool:
    a = parse_plain(answer)
    if not a.is_number or not sp.sympify(val).is_number:
        return False
    av, vv = float(a), float(val)
    tol = tol if tol is not None else 1e-6 * max(1.0, abs(vv))
    return abs(av - vv) <= tol

def _choice_match(p: dict, expected) -> bool:
    idx = int(p['answer'])
    choices = p['choices']
    if not (0 <= idx < len(choices)):
        return False
    # choices are LaTeX; the template must also pass plain forms in _verify['choices_plain']
    plains = p['_verify'].get('choices_plain')
    if not plains or len(plains) != len(choices):
        return False
    try:
        correct = parse_plain(plains[idx])
    except Exception:
        return False
    var = Symbol(p.get('variable', 'x'))
    if not _same(correct, expected, var):
        return False
    # every distractor must differ from expected
    for i, s in enumerate(plains):
        if i == idx:
            continue
        try:
            if _same(parse_plain(s), expected, var):
                return False
        except Exception:
            return False
    return True

def _interval_match(answer: str, v: dict) -> bool:
    m = re.fullmatch(r'\s*([\[(])\s*([^,]+),\s*([^\])]+)\s*([\])])\s*', answer)
    if not m:
        return False
    lo = -oo if m.group(2).strip() in ('-inf', '-oo', '-infinity') else parse_plain(m.group(2))
    hi = oo if m.group(3).strip() in ('inf', 'oo', 'infinity') else parse_plain(m.group(3))
    got = sp.Interval(lo, hi, left_open=(m.group(1) == '('), right_open=(m.group(4) == ')'))
    exp_ = v.get('expected')
    if isinstance(exp_, str):
        # expected given as sympy set expression, e.g. "Interval(-oo, 3, True, True)" or a condition like "x**2 < 4"
        try:
            es = sp.sympify(exp_, locals=_LOCALS)
            if isinstance(es, sp.Set):
                return es == got
            return sp.solveset(es, x, sp.S.Reals) == got
        except Exception:
            return False
    return False

# ---------- dedupe + output ----------

def _norm_statement(s: str) -> str:
    return re.sub(r'\s+', '', s.lower())

def dedupe(problems: list[dict]) -> list[dict]:
    seen_s, seen_a, out = set(), set(), []
    for p in problems:
        ks, ka = _norm_statement(p['statement']), (p['skill'], p['checker'], re.sub(r'\s+', '', p['answer']))
        if ks in seen_s or (p['checker'] != 'choice' and ka in seen_a and p['checker'] != 'numeric'):
            continue
        seen_s.add(ks); seen_a.add(ka); out.append(p)
    return out

def log_reject(p: dict, reason: str):
    with open(REJECT_LOG, 'a') as f:
        f.write(json.dumps({'id': p.get('id'), 'skill': p.get('skill'), 'statement': p.get('statement'), 'answer': p.get('answer'), 'reason': reason}) + '\n')

def verify_all(problems: list[dict]) -> list[dict]:
    good = []
    for p in problems:
        ok, reason = verify(p)
        if ok:
            q = {k: v for k, v in p.items() if not k.startswith('_')}
            q['verified'] = True
            good.append(q)
        else:
            log_reject(p, reason)
    return good

def write_bank(skill: str, problems: list[dict], filename: str | None = None) -> int:
    """Verify, dedupe, and write data/problems/<skill>.json. Returns count written."""
    problems = dedupe(problems)
    good = verify_all(problems)
    good = dedupe(good)
    os.makedirs(BANK_DIR, exist_ok=True)
    path = os.path.join(BANK_DIR, (filename or skill) + '.json')
    with open(path, 'w') as f:
        json.dump({'skill': skill, 'problems': good}, f, indent=1, ensure_ascii=False)
    return len(good)

def seeded(name: str) -> random.Random:
    return random.Random(int(hashlib.sha1(name.encode()).hexdigest(), 16) % (2**32))
