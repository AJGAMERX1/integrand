"""Stewart 5.5 and the custom transcendental-integrals node (original problems, SymPy-verified):
substitution (5.5), transcendental-integrals (5.4-5.5: e^x, 1/x, trig, inverse trig, with substitution).

Also exposes pools of substitution / transcendental integrals reused by daily_high.py (tiers 4 and 5).
"""
from __future__ import annotations
import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
_TOOLS = os.path.dirname(_HERE)
for _p in (_TOOLS, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import sympy as sp
from problemkit import make_problem, plain, ltx, fmt_num, seeded, x, t, u
from stewart import (P, L, N, coef, signed, nz, pick, opt, num_distractors, mc, numeric_mc, limit_class_mc,
                     label_mc, numeric_problem, equiv_problem, interval_problem, interval_str, interval_ltx, h, y,
                     tidy, pow_form, int_ltx, indefinite_problem, definite_problem, nice_anti)

sin, cos, tan, sec, csc, cot, exp, log, sqrt, pi, E, R = sp.sin, sp.cos, sp.tan, sp.sec, sp.csc, sp.cot, sp.exp, sp.log, sp.sqrt, sp.pi, sp.E, sp.Rational


def du_ltx(g) -> str:
    """LaTeX for g'(x) as it appears in 'du = g'(x) dx', with parentheses around sums and sec^2 for tan."""
    d = sp.diff(g, x)
    if g == tan(x):
        return "\\sec^{2}{\\left(x \\right)}"
    dl = L(d)
    if isinstance(d, sp.Add) or dl.startswith('- '):
        dl = f"\\left({dl}\\right)"
    return dl


def lin_dom(a, b, width=2.5):
    """Open interval where a*x + b > 0."""
    r = -sp.Rational(b, a)
    return (float(r) + 0.5, float(r) + 0.5 + width) if a > 0 else (float(r) - 0.5 - width, float(r) - 0.5)


class Item:
    """One integral: integrand f, substitution u = g(x) (None for table integrals), integrand in u, factor c
    with f dx = c * inner(u) du, sampling domain, difficulty, and a category tag."""
    def __init__(self, f, g, inner, c, dom, diff, cat, F=None):
        self.f, self.g, self.inner, self.c, self.dom, self.diff, self.cat = sp.sympify(f), g, inner, sp.nsimplify(c), dom, diff, cat
        if g is not None:
            self.Fu = sp.integrate(sp.sympify(inner), u)
        if F is not None:
            self.F = sp.sympify(F)
        elif g is not None:
            self.F = (self.c * self.Fu).subs(u, g)
        else:
            self.F = sp.integrate(self.f, x)
        self.F = nice_anti(self.F)

    def hints(self):
        if self.g is None:
            return ["Match each piece to an entry of the table of basic integrals (no substitution needed).",
                    "Check by differentiating your answer."]
        return [f"Try the substitution $u = {L(self.g)}$; then $du = {du_ltx(self.g)}\\,dx$.",
                f"Rewrite everything in terms of $u$: the integral becomes $\\displaystyle\\int {L(self.c * self.inner)}\\,du$."]

    def solution(self):
        if self.g is None:
            return [f"Use the basic integral formulas term by term.", f"${int_ltx(self.f)} = {L(self.F)} + C$."]
        return [f"Let $u = {L(self.g)}$, so $du = {du_ltx(self.g)}\\,dx$; hence ${L(self.f)}\\,dx = {L(self.c * self.inner)}\\,du$.",
                f"$\\displaystyle{int_ltx(self.f)} = \\int {L(self.c * self.inner)}\\,du = {L(self.c * self.Fu)} + C$.",
                f"Substitute $u = {L(self.g)}$ back: ${L(self.F)} + C$."]


def pool_usub(rng, want=None):
    """Return a list of candidate Items (substitution rule). want: optional set of category tags."""
    a = nz(rng, -4, 4); b = rng.randint(-4, 4); c = rng.randint(1, 5); n_ = rng.randint(2, 5); k = rng.randint(2, 5); ap = rng.randint(1, 4)
    items = [
        Item((a * x + b)**n_, a * x + b, u**n_, R(1, a), (-2, 2), 1, 'pow'),
        Item(x * (x**2 + c)**n_, x**2 + c, u**n_, R(1, 2), (-2, 2), 1, 'pow'),
        Item(x * sqrt(x**2 + c), x**2 + c, sqrt(u), R(1, 2), (-2, 2), 2, 'root'),
        Item(x**2 * sqrt(x**3 + c), x**3 + c, sqrt(u), R(1, 3), (0, 2), 2, 'root'),
        Item(x / sqrt(x**2 + c), x**2 + c, 1 / sqrt(u), R(1, 2), (-2, 2), 2, 'root'),
        Item(cos(k * x), k * x, cos(u), R(1, k), (-2, 2), 1, 'trig'),
        Item(sin(ap * x + b), ap * x + b, sin(u), R(1, ap), (-2, 2), 1, 'trig'),
        Item(sin(x)**n_ * cos(x), sin(x), u**n_, 1, (-3, 3), 2, 'trig'),
        Item(cos(x)**n_ * sin(x), cos(x), u**n_, -1, (-3, 3), 2, 'trig'),
        Item(exp(k * x), k * x, exp(u), R(1, k), (-1, 1), 1, 'exp'),
        Item(x * exp(x**2), x**2, exp(u), R(1, 2), (-1, 1), 2, 'exp'),
        Item(x * exp(-x**2), -x**2, exp(u), R(-1, 2), (-1, 1), 2, 'exp'),
        Item(1 / (ap * x + c), ap * x + c, 1 / u, R(1, ap), lin_dom(ap, c), 2, 'log'),
        Item(x / (x**2 + c), x**2 + c, 1 / u, R(1, 2), (-2, 2), 2, 'log'),
        Item(sec(k * x)**2, k * x, sec(u)**2, R(1, k), (-0.25, 0.25), 2, 'trig'),
        Item(sec(ap * x) * tan(ap * x), ap * x, sec(u) * tan(u), R(1, ap), (-0.3, 0.3), 2, 'trig'),
        Item(log(x)**n_ / x, log(x), u**n_, 1, (1, 4), 2, 'log'),
        Item(tan(x), cos(x), 1 / u, -1, (-1, 1), 3, 'log', F=-log(cos(x))),
        Item(exp(x) / (1 + exp(x)), 1 + exp(x), 1 / u, 1, (-2, 2), 2, 'log'),
        Item(cos(x) / (1 + sin(x)**2), sin(x), 1 / (1 + u**2), 1, (-3, 3), 3, 'inv'),
        Item(1 / sqrt(1 - k**2 * x**2), k * x, 1 / sqrt(1 - u**2), R(1, k), (-0.9 / k, 0.9 / k), 3, 'inv'),
        Item(1 / (x**2 + c**2), x / c, 1 / (1 + u**2), R(1, c), (-2, 2), 3, 'inv'),
        Item(sqrt(ap * x + c), ap * x + c, sqrt(u), R(1, ap), lin_dom(ap, c), 1, 'root'),
        Item(1 / (ap * x + c)**2, ap * x + c, u**(-2), R(1, ap), lin_dom(ap, c), 2, 'pow'),
        Item(x / (x**2 + c)**2, x**2 + c, u**(-2), R(1, 2), (-2, 2), 2, 'pow'),
        Item(sin(sqrt(x)) / sqrt(x), sqrt(x), sin(u), 2, (0.5, 4), 3, 'trig'),
        Item(x * cos(x**2), x**2, cos(u), R(1, 2), (-2, 2), 2, 'trig'),
        Item((2 * x + ap) / (x**2 + ap * x + c), x**2 + ap * x + c, 1 / u, 1, (0.5, 3), 2, 'log'),
        Item(1 / (x * log(x)), log(x), 1 / u, 1, (1.5, 4), 3, 'log'),
        Item(exp(x) * sin(exp(x)), exp(x), sin(u), 1, (-1, 1), 3, 'trig'),
        Item(exp(1 / x) / x**2, 1 / x, exp(u), -1, (0.5, 2), 3, 'exp'),
        Item(x**2 * (x**3 + c)**n_, x**3 + c, u**n_, R(1, 3), (-1.5, 1.5), 2, 'pow'),
        Item(x**3 * sqrt(x**4 + c), x**4 + c, sqrt(u), R(1, 4), (-1.5, 1.5), 2, 'root'),
        Item((log(x) + 1) / x if False else log(x) / x, log(x), u, 1, (1, 4), 2, 'log'),
        Item(x * sin(x**2 + c), x**2 + c, sin(u), R(1, 2), (-2, 2), 2, 'trig'),
        Item(exp(sin(x)) * cos(x), sin(x), exp(u), 1, (-3, 3), 2, 'exp'),
        Item(sin(x) * exp(cos(x)), cos(x), exp(u), -1, (-3, 3), 2, 'exp'),
        Item(exp(sqrt(x)) / sqrt(x), sqrt(x), exp(u), 2, (0.5, 3), 3, 'exp'),
        Item(x / (1 + x**4), x**2, 1 / (1 + u**2), R(1, 2), (-2, 2), 3, 'inv'),
        Item(1 / sqrt(ap * x + c), ap * x + c, 1 / sqrt(u), R(1, ap), lin_dom(ap, c), 2, 'root'),
        Item(sec(x)**2 * tan(x)**n_, tan(x), u**n_, 1, (-1, 1), 3, 'trig'),
        Item(cos(x) / sin(x)**2, sin(x), u**(-2), 1, (0.3, 2.8), 3, 'trig'),
    ]
    if want:
        items = [it for it in items if it.cat in want]
    return items


def pool_transc(rng):
    """Exponential, logarithmic, trigonometric and inverse-trig integrals (with and without substitution)."""
    a = nz(rng, -4, 4); b = rng.randint(-3, 3); c = rng.randint(1, 5); n_ = rng.randint(2, 4); k = rng.randint(2, 5); ap = rng.randint(1, 4); bb = rng.choice([2, 3, 5, 10])
    items = [
        Item(exp(ap * x + b), ap * x + b, exp(u), R(1, ap), (-1, 1), 1, 'exp'),
        Item(exp(-k * x), -k * x, exp(u), R(-1, k), (-1, 1), 1, 'exp'),
        Item(x * exp(x**2 + b), x**2 + b, exp(u), R(1, 2), (-1, 1), 2, 'exp'),
        Item((exp(x) + c)**2, None, None, 1, (-1, 1), 2, 'exp', F=exp(2 * x) / 2 + 2 * c * exp(x) + c * c * x),
        Item(exp(2 * x) / (1 + exp(2 * x)), 1 + exp(2 * x), 1 / u, R(1, 2), (-1, 1), 3, 'exp'),
        Item(exp(sqrt(x)) / sqrt(x), sqrt(x), exp(u), 2, (0.5, 3), 3, 'exp'),
        Item(sp.Integer(bb)**x, None, None, 1, (-1, 1), 2, 'exp', F=sp.Integer(bb)**x / log(bb)),
        Item(exp(x) * sin(exp(x)), exp(x), sin(u), 1, (-1, 1), 3, 'exp'),
        Item(exp(x) + exp(-x), None, None, 1, (-1, 1), 1, 'exp'),
        Item(exp(1 / x) / x**2, 1 / x, exp(u), -1, (0.5, 2), 3, 'exp'),
        Item(exp(x) * (1 + exp(x))**n_, 1 + exp(x), u**n_, 1, (-1, 1), 2, 'exp'),
        Item(exp(x) / sqrt(1 + exp(x)), 1 + exp(x), 1 / sqrt(u), 1, (-1, 1), 3, 'exp'),
        Item(1 / (ap * x + c), ap * x + c, 1 / u, R(1, ap), lin_dom(ap, c), 1, 'log'),
        Item(x / (x**2 + c), x**2 + c, 1 / u, R(1, 2), (-2, 2), 2, 'log'),
        Item((x + 1) / (x**2 + 2 * x + c + 1), x**2 + 2 * x + c + 1, 1 / u, R(1, 2), (-2, 2), 2, 'log'),
        Item(1 / (x * log(x)), log(x), 1 / u, 1, (1.5, 4), 3, 'log'),
        Item(log(x)**n_ / x, log(x), u**n_, 1, (1, 4), 2, 'log'),
        Item(tan(x), cos(x), 1 / u, -1, (-1, 1), 2, 'log', F=-log(cos(x))),
        Item(cot(x), sin(x), 1 / u, 1, (0.3, 2.8), 2, 'log'),
        Item((2 * x + ap) / (x**2 + ap * x + c), x**2 + ap * x + c, 1 / u, 1, (0.5, 3), 2, 'log'),
        Item(exp(x) / (exp(x) + c), exp(x) + c, 1 / u, 1, (-2, 2), 2, 'log'),
        Item(sin(x) / (1 + cos(x)), 1 + cos(x), 1 / u, -1, (-2, 2), 3, 'log'),
        Item(c / x + ap / x**2, None, None, 1, (0.5, 3), 1, 'log'),
        Item(log(x) / x, log(x), u, 1, (1, 4), 2, 'log'),
        Item(sin(k * x), k * x, sin(u), R(1, k), (-2, 2), 1, 'trig'),
        Item(cos(ap * x + b), ap * x + b, cos(u), R(1, ap), (-2, 2), 1, 'trig'),
        Item(sec(k * x)**2, k * x, sec(u)**2, R(1, k), (-0.25, 0.25), 2, 'trig'),
        Item(sec(ap * x) * tan(ap * x), ap * x, sec(u) * tan(u), R(1, ap), (-0.3, 0.3), 2, 'trig'),
        Item(sin(x)**n_ * cos(x), sin(x), u**n_, 1, (-3, 3), 2, 'trig'),
        Item(sin(x) / cos(x)**2, cos(x), u**(-2), -1, (-1, 1), 2, 'trig'),
        Item(x * sin(x**2), x**2, sin(u), R(1, 2), (-2, 2), 2, 'trig'),
        Item(cos(log(x)) / x, log(x), cos(u), 1, (1, 4), 3, 'trig'),
        Item(sec(x)**2 * tan(x), tan(x), u, 1, (-1, 1), 2, 'trig'),
        Item(sin(x) * exp(cos(x)), cos(x), exp(u), -1, (-3, 3), 2, 'trig'),
        Item(csc(k * x)**2, k * x, csc(u)**2, R(1, k), (0.3 / k, 2.8 / k), 2, 'trig'),
        Item(sin(x) * cos(x), sin(x), u, 1, (-3, 3), 2, 'trig'),
        Item(cos(x) / (1 + sin(x)**2), sin(x), 1 / (1 + u**2), 1, (-3, 3), 3, 'inv'),
        Item(sin(sqrt(x)) / sqrt(x), sqrt(x), sin(u), 2, (0.5, 4), 3, 'trig'),
        Item(c * cos(x) - ap * sin(x), None, None, 1, (-3, 3), 1, 'trig'),
        Item(cos(x)**n_ * sin(x), cos(x), u**n_, -1, (-3, 3), 2, 'trig'),
        Item(1 / (1 + x**2), None, None, 1, (-2, 2), 1, 'inv'),
        Item(1 / sqrt(1 - x**2), None, None, 1, (-0.9, 0.9), 1, 'inv'),
        Item(1 / (c**2 + x**2), x / c, 1 / (1 + u**2), R(1, c), (-2, 2), 2, 'inv'),
        Item(1 / sqrt(c**2 - x**2), x / c, 1 / sqrt(1 - u**2), 1, (-0.9 * c, 0.9 * c), 2, 'inv'),
        Item(x / (1 + x**4), x**2, 1 / (1 + u**2), R(1, 2), (-2, 2), 3, 'inv'),
        Item(exp(x) / (1 + exp(2 * x)), exp(x), 1 / (1 + u**2), 1, (-2, 2), 3, 'inv'),
        Item(1 / sqrt(1 - k**2 * x**2), k * x, 1 / sqrt(1 - u**2), R(1, k), (-0.9 / k, 0.9 / k), 3, 'inv'),
        Item(1 / (x * sqrt(1 - log(x)**2)), log(x), 1 / sqrt(1 - u**2), 1, (1.1, 2.5), 3, 'inv'),
    ]
    return items


def take(rng, items, count, exclude=()):
    """Pick up to count distinct items (by integrand) from items, shuffled."""
    rng.shuffle(items)
    out, seen = [], set(exclude)
    for it in items:
        key = str(it.f)
        if key in seen:
            continue
        seen.add(key); out.append(it)
        if len(out) >= count:
            break
    return out


def nice_limits(rng, it):
    """Choose definite-integral limits (a, b) inside the domain with a clean exact value; None if none found."""
    f = it.f
    cands = []
    if it.cat == 'trig' and f.has(sin) or f.has(cos) or f.has(sec) or f.has(csc) or f.has(tan):
        cands = [(0, pi / 2), (0, pi), (0, pi / 4), (0, pi / 6), (pi / 6, pi / 2), (pi / 4, pi / 3), (0, pi / 3)]
    elif f.has(exp):
        cands = [(0, 1), (0, log(2)), (0, log(3)), (-1, 0), (0, 2), (log(2), log(4))]
    elif f.has(log):
        cands = [(1, E), (1, E**2), (E, E**2), (1, 2), (2, 4), (1, 3)]
    else:
        cands = [(0, 1), (0, 2), (1, 2), (1, 3), (0, 3), (-1, 1), (0, 4), (1, 4), (2, 5)]
    rng.shuffle(cands)
    lo, hi = it.dom
    for a, b in cands:
        try:
            if not (lo - 1e-9 <= float(a) and float(b) <= hi + 1e-9):
                # allow limits outside the sampling domain only when the integrand is defined there
                vals = [f.subs(x, a + (b - a) * q / 7) for q in range(8)]
                if any((not v.is_real) or v.has(sp.zoo) or v.has(sp.nan) or v == sp.oo or v == -sp.oo for v in [sp.simplify(v_) for v_ in vals]):
                    continue
            val = sp.integrate(f, (x, a, b))
            val = sp.simplify(val)
            if val.is_real and val.is_finite and sp.count_ops(val) <= 5 and not val.has(sp.Integral):
                return a, b, val
        except Exception:
            continue
    return None


def definite_from_item(S, it, rng, *, tags=None, tier=None, difficulty=None):
    r = nice_limits(rng, it)
    if r is None:
        return None
    a, b, val = r
    if it.g is None:
        hints = ["Find an antiderivative from the basic formulas, then apply FTC2.", f"$F(x) = {L(it.F)}$."]
        sol = [f"An antiderivative is $F(x) = {L(it.F)}$.", f"$F({L(b)}) - F({L(a)}) = {L(val)}$."]
    else:
        ga, gb = sp.simplify(it.g.subs(x, a)), sp.simplify(it.g.subs(x, b))
        hints = [f"Substitute $u = {L(it.g)}$, $du = {du_ltx(it.g)}\\,dx$, and change the limits: $x = {L(a)} \\Rightarrow u = {L(ga)}$, $x = {L(b)} \\Rightarrow u = {L(gb)}$.",
                 f"The integral becomes $\\displaystyle\\int_{{{L(ga)}}}^{{{L(gb)}}} {L(it.c * it.inner)}\\,du$."]
        sol = [f"With $u = {L(it.g)}$ the limits become $u = {L(ga)}$ and $u = {L(gb)}$.",
               f"$\\displaystyle\\int_{{{L(ga)}}}^{{{L(gb)}}} {L(it.c * it.inner)}\\,du = \\left[{L(it.c * it.Fu)}\\right]_{{{L(ga)}}}^{{{L(gb)}}} = {L(val)}$."]
    return definite_problem(S, it.f, a, b, difficulty=difficulty or min(3, it.diff + 1), hints=hints, solution=sol, value=val, tags=tags, tier=tier)


# ======================================================================
# 5.5 substitution
# ======================================================================

def substitution():
    S = 'substitution'
    rng = seeded(S)
    out = []
    items = take(rng, pool_usub(rng) + pool_usub(rng), 34)
    for it in items:
        out.append(indefinite_problem(S, it.f, it.F, difficulty=it.diff, domain=it.dom, hints=it.hints(), solution=it.solution()))

    # definite integrals by substitution
    for it in take(rng, pool_usub(rng), 40):
        p = definite_from_item(S, it, rng)
        if p:
            out.append(p)
        if sum(1 for q in out if q['checker'] == 'numeric') >= 14:
            break

    # new limits after substitution
    for _ in range(5):
        g = rng.choice([x**2 + rng.randint(1, 4), 3 * x - 1, sin(x), exp(x), log(x), 2 * x**3 + 1])
        a, b = rng.choice([(0, 1), (1, 2), (0, 2)]) if not g.has(log) else (1, E)
        if g.has(sin):
            a, b = 0, pi / 2
        f_l = rng.choice(["x\\,", "", "\\cos x\\,"]) if False else ""
        new_lo, new_hi = sp.simplify(g.subs(x, a)), sp.simplify(g.subs(x, b))
        which = rng.choice(['upper', 'lower'])
        val = new_hi if which == 'upper' else new_lo
        out.append(numeric_problem(S, f"In a definite integral $\\displaystyle\\int_{{{L(a)}}}^{{{L(b)}}} f(x)\\,dx$ you substitute $u = {L(g)}$. What is the new {which} limit of integration (in terms of $u$)?", val, difficulty=1,
            hints=["When you substitute, the limits must be converted to $u$-values: evaluate $u = g(x)$ at the old limits.", f"The {which} limit is $u = g({L(b if which == 'upper' else a)})$."],
            solution=[f"$u = {L(g)}$; at $x = {L(a)}$, $u = {L(new_lo)}$; at $x = {L(b)}$, $u = {L(new_hi)}$.", f"So the new {which} limit is ${L(val)}$."],
            verify={'kind': 'evaluate', 'expr': str(g), 'at': str(b if which == 'upper' else a)}))

    # symmetry
    for _ in range(6):
        a = rng.choice([1, 2, 3]); kind = rng.choice(['odd', 'even'])
        if kind == 'odd':
            f = rng.choice([x**3 - rng.randint(1, 4) * x, x * cos(x), sin(x) * x**2, x**5 / (1 + x**2), tan(x) if a == 1 else x**3, x * exp(-x**2)])
            why = "the integrand is odd ($f(-x) = -f(x)$), so the integral over a symmetric interval is $0$"
        else:
            f = rng.choice([x**2 + rng.randint(1, 3), rng.randint(1, 3) * x**4, x**2 * rng.randint(1, 3) - 1, sp.Abs(x)])
            why = "the integrand is even, so $\\int_{-a}^{a} f = 2\\int_0^a f$"
        val = sp.integrate(f, (x, -a, a))
        out.append(definite_problem(S, f, -a, a, difficulty=2, value=val,
            stmt=f"Use symmetry to evaluate ${int_ltx(f, -a, a)}$.",
            hints=["Check whether the integrand is even or odd by replacing $x$ with $-x$.", "Odd on $[-a, a]$ gives $0$; even gives twice the integral over $[0, a]$."],
            solution=[f"Here {why}.", f"${int_ltx(f, -a, a)} = {L(val)}$."]))

    # choose the substitution (conceptual)
    for _ in range(5):
        c = rng.randint(1, 5); k = rng.randint(2, 5)
        f, g, dis = rng.choice([(x * sqrt(x**2 + c), x**2 + c, [sqrt(x**2 + c), x, x**2]), (cos(k * x) * exp(sin(k * x)), sin(k * x), [cos(k * x), exp(sin(k * x)), k * x]), (log(x)**2 / x, log(x), [log(x)**2, x, 1 / x]), (x**2 / (x**3 + c), x**3 + c, [x**2, x**3, 1 / (x**3 + c)])])
        opts = [(f"$u = {L(g)}$", 'ok')] + [(f"$u = {L(d)}$", f'w{j}') for j, d in enumerate(dis)]
        out.append(label_mc(S, f"Which substitution is the most useful first step for ${int_ltx(f)}$?", opts, 'ok', rng, difficulty=1,
            hints=["Look for an inner function whose derivative (up to a constant) also appears as a factor.", f"The derivative of ${L(g)}$ is ${L(sp.diff(g, x))}$; is that factor present?"],
            solution=[f"With $u = {L(g)}$, $du = {L(sp.diff(g, x))}\\,dx$ absorbs the remaining factor of the integrand.", "The other choices leave an $x$ that cannot be expressed in terms of $u$."]))

    concept = [
        ("The Substitution Rule $\\displaystyle\\int f(g(x))g'(x)\\,dx = \\int f(u)\\,du$ (with $u = g(x)$) is the integration counterpart of", [("the Chain Rule", 'ok'), ("the Product Rule", 'prod'), ("the Quotient Rule", 'quot'), ("the Power Rule", 'pow')], 'ok',
         ["Differentiate $F(g(x))$ and see which rule appears.", "$\\frac{d}{dx}F(g(x)) = F'(g(x))g'(x)$."],
         ["By the Chain Rule, $\\frac{d}{dx}F(g(x)) = f(g(x))g'(x)$ when $F' = f$.", "Reading this backwards is exactly the Substitution Rule."]),
        ("When using $u = g(x)$ in a definite integral $\\displaystyle\\int_a^b f(g(x))g'(x)\\,dx$, the limits become", [("$g(a)$ and $g(b)$", 'ok'), ("$a$ and $b$ unchanged", 'same'), ("$g'(a)$ and $g'(b)$", 'deriv'), ("$f(a)$ and $f(b)$", 'f')], 'ok',
         ["The limits refer to the integration variable; once that is $u$, they must be $u$-values.", "Alternatively, substitute back to $x$ before using the original limits."],
         ["$\\int_a^b f(g(x))g'(x)\\,dx = \\int_{g(a)}^{g(b)} f(u)\\,du$.", "Forgetting to change limits (or to substitute back) is a common error."]),
    ]
    for stmt, opts, lab, hints, sol in concept:
        out.append(label_mc(S, stmt, opts, lab, rng, difficulty=1, hints=hints, solution=sol))
    return out


# ======================================================================
# transcendental-integrals
# ======================================================================

def transcendental_integrals():
    S = 'transcendental-integrals'
    rng = seeded(S)
    out = []
    items = take(rng, pool_transc(rng) + pool_transc(rng), 36)
    for it in items:
        out.append(indefinite_problem(S, it.f, it.F, difficulty=it.diff, domain=it.dom, hints=it.hints(), solution=it.solution()))

    count = 0
    for it in take(rng, pool_transc(rng), 48):
        p = definite_from_item(S, it, rng)
        if p:
            out.append(p); count += 1
        if count >= 14:
            break

    # multiple choice: identify the antiderivative
    mcs = [(exp(2 * x), [2 * exp(2 * x), exp(2 * x), exp(x**2)], "Differentiate each option; only one gives $e^{2x}$."),
           (1 / x, [-1 / x**2, log(x**2), x * log(x)], "Which function has derivative $1/x$? The power rule fails for $n = -1$."),
           (sec(x)**2, [sec(x) * tan(x), -cot(x), sec(x)**3 / 3], "Recall the derivative of $\\tan x$."),
           (1 / (1 + x**2), [log(1 + x**2), -1 / (2 * x), 1 / (x + x**3 / 3)], "Which function has derivative $\\dfrac{1}{1 + x^2}$?"),
           (sin(x), [cos(x), -sin(x), sin(x)**2 / 2], "Which function has derivative $\\sin x$? Watch the sign.")]
    for f, dis, hint2 in mcs:
        F = sp.integrate(f, x)
        opts = [(f'${L(F)} + C$', P(F))] + [(f'${L(w)} + C$', P(w)) for w in dis]
        out.append(mc(S, f"Which is the correct antiderivative: ${int_ltx(f)} = \\;?$", opts, 0, rng, difficulty=1,
            hints=["Integration undoes differentiation: differentiate each candidate and compare with the integrand.", hint2],
            solution=[f"$\\frac{{d}}{{dx}}\\left[{L(F)}\\right] = {L(f)}$, so this is the antiderivative.", "The other options differentiate to something else."],
            verify={'kind': 'choice', 'expected': str(F)}))
    out.append(label_mc(S, "Why is $\\displaystyle\\int \\frac{1}{x}\\,dx$ written as $\\ln|x| + C$ rather than $\\ln x + C$?", [("$\\ln x$ is undefined for $x < 0$, but $\\ln|x|$ has derivative $1/x$ on both sides of $0$", 'ok'), ("because $1/x$ is always positive", 'pos'), ("the absolute value is a typo", 'typo'), ("because $\\ln|x| = |\\ln x|$", 'eq')], 'ok', rng, difficulty=1,
        hints=["$1/x$ is defined for negative $x$ too; its antiderivative should be as well.", "Check $\\frac{d}{dx}\\ln(-x)$ for $x < 0$."],
        solution=["For $x < 0$, $\\frac{d}{dx}\\ln(-x) = \\frac{-1}{-x} = \\frac{1}{x}$.", "So $\\ln|x|$ works on both $(-\\infty, 0)$ and $(0, \\infty)$, while $\\ln x$ only exists for $x > 0$."]))
    return out


def build() -> dict:
    return {
        'substitution': tidy(substitution()),
        'transcendental-integrals': tidy(transcendental_integrals()),
    }
