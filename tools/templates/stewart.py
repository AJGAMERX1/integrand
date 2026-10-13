"""stewart: shared helpers for the Stewart chapter templates (stewart_ch1.py ... stewart_ch5.py) and daily_high.py.

This module exposes build() -> {} so the generator CLI can import it like any other template; the real banks are
produced by the chapter modules. Import it as `stewart` (templates dir on sys.path) or `templates.stewart`.
"""
from __future__ import annotations
import os, sys, random
_HERE = os.path.dirname(os.path.abspath(__file__))
_TOOLS = os.path.dirname(_HERE)
for _p in (_TOOLS, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import sympy as sp
from problemkit import make_problem, plain, ltx, fmt_num, seeded, rat, x, t, u  # noqa: F401

h, y, k, n, w = sp.symbols('h y k n w')


def build() -> dict:
    return {}


# ---------- formatting ----------

def P(e) -> str:
    return plain(e)


def L(e) -> str:
    return ltx(e)


def N(v) -> str:
    """LaTeX for a number (int / Rational / float)."""
    v = sp.nsimplify(v)
    return sp.latex(v)


def coef(c, var='x') -> str:
    """LaTeX for c*var with 1 and -1 handled: coef(1) -> 'x', coef(-1) -> '-x', coef(3) -> '3x'."""
    if c == 1:
        return var
    if c == -1:
        return f'-{var}'
    return f'{N(c)}{var}'


def signed(c) -> str:
    """' + 3' / ' - 3' for building sums in LaTeX."""
    c = sp.nsimplify(c)
    return f' + {sp.latex(c)}' if c >= 0 else f' - {sp.latex(-c)}'


def nz(rng: random.Random, lo: int, hi: int, exclude=(0,)) -> int:
    while True:
        v = rng.randint(lo, hi)
        if v not in exclude:
            return v


def pick(rng: random.Random, items):
    return items[rng.randrange(len(items))]


# ---------- multiple choice ----------

def opt(v):
    """(latex, plain) pair for a numeric value."""
    v = sp.nsimplify(v)
    return (f'${sp.latex(v)}$', fmt_num(v))


def num_distractors(val, rng: random.Random, count=3):
    """Distinct wrong numeric values near val."""
    val = sp.nsimplify(val)
    cands = [val + 1, val - 1, -val, 2 * val, val / 2, val + 2, 1 - val, val - 2, val + sp.Rational(1, 2)]
    if val not in (0, 1, -1):
        cands.append(val * val)
    out = []
    for c in cands:
        c = sp.nsimplify(c)
        if c != val and c not in out:
            out.append(c)
    rng.shuffle(out)
    return out[:count]


def mc(skill, statement, options, correct, rng: random.Random, *, difficulty, hints, solution, verify,
       tags=None, tier=None):
    """options: list of (latex, plain) pairs; correct: index into options. Shuffles and fills choices_plain."""
    order = list(range(len(options)))
    rng.shuffle(order)
    choices = [options[i][0] for i in order]
    plains = [options[i][1] for i in order]
    v = dict(verify)
    v['choices_plain'] = plains
    return make_problem(skill, statement, 'choice', str(order.index(correct)), difficulty=difficulty,
                        hints=hints, solution=solution, verify=v, choices=choices, tags=tags, tier=tier)


def numeric_mc(skill, statement, val, rng, *, difficulty, hints, solution, verify, tags=None, tier=None):
    opts = [opt(val)] + [opt(d) for d in num_distractors(val, rng)]
    return mc(skill, statement, opts, 0, rng, difficulty=difficulty, hints=hints, solution=solution,
              verify=verify, tags=tags, tier=tier)


def limit_class_mc(skill, statement, expr, to, rng, *, difficulty, hints, solution, direction=None, extra=None,
                   var='x'):
    """Choice item whose answer may be a finite value, +/- infinity or 'does not exist'."""
    from problemkit import _limit_label
    label = _limit_label(sp.sympify(expr), sp.Symbol(var), sp.sympify(to), direction)
    opts = [('$\\infty$', 'inf'), ('$-\\infty$', '-inf'), ('does not exist', 'dne')]
    if isinstance(label, str):
        correct = [o[1] for o in opts].index(label)
        finite = extra if extra is not None else [0, 1]
        for f_ in finite:
            opts.append(opt(f_))
    else:
        opts.insert(0, opt(label))
        correct = 0
        for d in num_distractors(label, rng, 1):
            opts.append(opt(d))
    verify = {'kind': 'limit_class', 'expr': str(expr), 'to': str(to)}
    if direction:
        verify['dir'] = direction
    return mc(skill, statement, opts, correct, rng, difficulty=difficulty, hints=hints, solution=solution,
              verify=verify)


def label_mc(skill, statement, options, correct_label, rng, *, difficulty, hints, solution, verify=None,
             tags=None, tier=None):
    """options: list of (latex_or_text, label). verify defaults to kind 'label'."""
    idx = [o[1] for o in options].index(correct_label)
    v = verify or {'kind': 'label', 'expected': correct_label}
    return mc(skill, statement, options, idx, rng, difficulty=difficulty, hints=hints, solution=solution,
              verify=v, tags=tags, tier=tier)


# ---------- common problem shapes ----------

def numeric_problem(skill, statement, value, *, difficulty, hints, solution, verify, tags=None, tier=None,
                    tolerance=None, variable=None):
    p = make_problem(skill, statement, 'numeric', fmt_num(value), difficulty=difficulty, hints=hints,
                     solution=solution, verify=verify, tags=tags, tier=tier, tolerance=tolerance)
    if variable:
        p['variable'] = variable   # tells verify() which symbol the _verify expressions use
    return p


def equiv_problem(skill, statement, answer_expr, *, difficulty, hints, solution, verify, variable='x',
                  domain=(-3, 3), tags=None, tier=None, plus_c=False):
    return make_problem(skill, statement, 'equiv_plus_c' if plus_c else 'equiv', plain(answer_expr),
                        difficulty=difficulty, hints=hints, solution=solution, verify=verify, variable=variable,
                        domain=domain, tags=tags, tier=tier)


def interval_problem(skill, statement, answer: str, expected: str, *, difficulty, hints, solution, tags=None):
    return make_problem(skill, statement, 'interval', answer, difficulty=difficulty, hints=hints,
                        solution=solution, verify={'kind': 'interval', 'expected': expected}, tags=tags)


def interval_str(lo, hi, lo_open, hi_open) -> str:
    a = '-inf' if lo == -sp.oo else fmt_num(lo)
    b = 'inf' if hi == sp.oo else fmt_num(hi)
    return f"{'(' if lo_open or lo == -sp.oo else '['}{a},{b}{')' if hi_open or hi == sp.oo else ']'}"


def interval_ltx(lo, hi, lo_open, hi_open) -> str:
    a = '-\\infty' if lo == -sp.oo else N(lo)
    b = '\\infty' if hi == sp.oo else N(hi)
    return f"{'(' if lo_open or lo == -sp.oo else '['}{a}, {b}{')' if hi_open or hi == sp.oo else ']'}"


def difficulty_for(expr, base=1) -> int:
    """Rough difficulty from expression size."""
    size = sp.count_ops(expr)
    return min(3, base + (1 if size > 6 else 0) + (1 if size > 14 else 0))


def tidy(problems):
    """Collapse runs of spaces in statement/hints/solution (cosmetic; safe inside LaTeX)."""
    import re
    def fix(s_):
        s_ = re.sub(r' {2,}', ' ', s_)
        for a_, b_ in (('\\operatorname{asin}', '\\arcsin'), ('\\operatorname{acos}', '\\arccos'), ('\\operatorname{atan}', '\\arctan')):
            s_ = s_.replace(a_, b_)
        return s_
    for p in problems:
        p['statement'] = fix(p['statement']).replace('( ', '(').replace(' )', ')')
        p['hints'] = [fix(s_) for s_ in p['hints']]
        p['solution'] = [fix(s_) for s_ in p['solution']]
        if 'choices' in p:
            p['choices'] = [fix(s_) for s_ in p['choices']]
    return problems


def pow_form(f) -> str:
    """LaTeX of a sum of terms with roots/reciprocals written as powers of x (for 'rewrite first' steps)."""
    parts = []
    for term in sp.Add.make_args(sp.expand(f)):
        c, rest = term.as_coeff_Mul()
        if rest == 1:
            parts.append(sp.latex(c))
            continue
        b_, e_ = rest.as_base_exp()
        if b_ == x and e_ != 1:
            cs = '' if c == 1 else ('-' if c == -1 else sp.latex(c))
            parts.append(f"{cs}x^{{{sp.latex(e_)}}}")
        else:
            parts.append(sp.latex(term))
    out = ' + '.join(parts)
    return out.replace('+ -', '- ')


# ---------- integrals ----------

def nice_anti(expr):
    """Replace asinh/acosh (not in the grader's function list) with their logarithmic forms."""
    expr = sp.sympify(expr)
    expr = expr.replace(lambda e: isinstance(e, sp.asinh), lambda e: sp.log(e.args[0] + sp.sqrt(e.args[0]**2 + 1)))
    expr = expr.replace(lambda e: isinstance(e, sp.acosh), lambda e: sp.log(e.args[0] + sp.sqrt(e.args[0]**2 - 1)))
    return expr


def int_ltx(f, a=None, b=None, var='x') -> str:
    fl = L(f)
    if isinstance(sp.sympify(f), sp.Add) or fl.startswith('- '):
        fl = f"\\left({fl}\\right)"
    body = f"{fl}\\,d{var}"
    if a is None:
        return f"\\int {body}"
    return f"\\int_{{{L(a)}}}^{{{L(b)}}} {body}"


def indefinite_problem(skill, integrand, answer, *, difficulty, hints, solution, domain=(-3, 3), stmt=None,
                       tags=None, tier=None, variable='x'):
    stmt = stmt or f"Evaluate ${int_ltx(integrand, var=variable)}$."
    return make_problem(skill, stmt, 'equiv_plus_c', plain(nice_anti(answer)), difficulty=difficulty, hints=hints,
                        solution=solution, verify={'kind': 'integral', 'integrand': str(integrand)}, variable=variable,
                        domain=domain, tags=tags, tier=tier)


def definite_problem(skill, integrand, a, b, *, difficulty, hints, solution, stmt=None, tags=None, tier=None,
                     value=None, tolerance=None, variable='x'):
    var = sp.Symbol(variable)
    val = value if value is not None else sp.integrate(integrand, (var, a, b))
    if sp.sympify(val).has(sp.log):
        val = sp.expand_log(sp.sympify(val), force=True)   # ln(5^(2/3)/2) -> 2*ln(5)/3 - ln(2)
    stmt = stmt or f"Evaluate ${int_ltx(integrand, a, b, var=variable)}$."
    return numeric_problem(skill, stmt, val, difficulty=difficulty, hints=hints, solution=solution, tags=tags, tier=tier,
                           tolerance=tolerance, variable=variable,
                           verify={'kind': 'definite', 'integrand': str(integrand), 'a': str(a), 'b': str(b)})
