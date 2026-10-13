"""
Ramp (track 0) problem templates: algebra 2 / precalc / trig essentials.

Every family is a function `fn(rng) -> problem dict` built with problemkit.make_problem and carrying a `_verify`
spec that lets problemkit re-derive the key with SymPy independently of how the template built the answer.
`build()` returns {skill: [problems]} for the 17 ramp nodes. Randomness is seeded per skill so output is
reproducible. Statements are prose with $...$ math (rendered by the app's richText helper).
"""
from __future__ import annotations
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sympy as sp
from sympy import Rational as R, sqrt, pi, sin, cos, tan, Abs, symbols, oo
from problemkit import make_problem, seeded, plain, ltx, fmt_num, parse_plain, x

y, k, i_, n_ = symbols('y k i n')

# ---------------------------------------------------------------- shared helpers

def P(skill, stmt, checker, answer, *, d, hints, sol, verify, **kw):
    return make_problem(skill, stmt, checker, answer, difficulty=d, hints=hints, solution=sol, verify=verify, **kw)

def nz(rng, lo, hi):
    """Random non-zero integer in [lo, hi]."""
    while True:
        v = rng.randint(lo, hi)
        if v != 0:
            return v

def frac(a, b) -> str:
    return r'\frac{' + str(a) + '}{' + str(b) + '}'

def num(v) -> str:
    """LaTeX for a number (int/Rational/sympy)."""
    return sp.latex(sp.nsimplify(v))

def ival(I) -> str:
    """sp.Interval -> grader interval syntax, e.g. '(-inf,3]'."""
    lo = '-inf' if I.start == -oo else fmt_num(I.start)
    hi = 'inf' if I.end == oo else fmt_num(I.end)
    return ('(' if I.left_open else '[') + lo + ',' + hi + (')' if I.right_open else ']')

def ival_ltx(I) -> str:
    lo = r'-\infty' if I.start == -oo else num(I.start)
    hi = r'\infty' if I.end == oo else num(I.end)
    return ('(' if I.left_open else '[') + lo + ', ' + hi + (')' if I.right_open else ']')

OPL = {'<': '<', '<=': r'\le', '>': '>', '>=': r'\ge'}

def choice(skill, stmt, options, correct, expected, *, d, hints, sol, rng, extra_verify=None, **kw):
    """options: list of (latex, plain). `correct` is the index into options before shuffling."""
    order = list(range(len(options)))
    rng.shuffle(order)
    opts = [options[j] for j in order]
    idx = order.index(correct)
    verify = {'kind': 'choice', 'expected': str(expected), 'choices_plain': [o[1] for o in opts]}
    if extra_verify:
        verify.update(extra_verify)
    return P(skill, stmt, 'choice', str(idx), d=d, hints=hints, sol=sol, verify=verify,
             choices=[o[0] for o in opts], **kw)

class Collector:
    """Mirrors problemkit.dedupe so templates know which candidates will survive."""
    def __init__(self):
        self.items, self.seen_s, self.seen_a = [], set(), set()
    def add(self, p) -> bool:
        ks = re.sub(r'\s+', '', p['statement'].lower())
        ka = (p['checker'], re.sub(r'\s+', '', p['answer']))
        if ks in self.seen_s or (p['checker'] in ('equiv', 'equiv_plus_c', 'interval') and ka in self.seen_a):
            return False
        self.seen_s.add(ks); self.seen_a.add(ka); self.items.append(p)
        return True

def run(skill, families, target=60, seed=None):
    """Round-robin over families until `target` distinct candidates exist (or attempts run out)."""
    rng = seeded(seed or skill)
    col = Collector()
    attempts = 0
    while len(col.items) < target and attempts < target * 40:
        fn = families[attempts % len(families)]
        attempts += 1
        p = fn(rng)
        if p:
            col.add(p)
    return col.items

def lin(a, b):
    """LaTeX for a*x + b."""
    return ltx(a * x + b)

def pick_points(rng, lo=-6, hi=6):
    while True:
        x1, y1, x2, y2 = (rng.randint(lo, hi) for _ in range(4))
        if x1 != x2:
            return x1, y1, x2, y2

# ================================================================ numbers-and-inequalities
S1 = 'numbers-and-inequalities'

def nai_linear(rng):
    a, b, c = nz(rng, -6, 6), rng.randint(-9, 9), rng.randint(-9, 9)
    op = rng.choice(['<', '<=', '>', '>='])
    cond = f"{a}*x+({b}) {op} {c}"
    I = sp.sympify(cond).as_set()
    if not isinstance(I, sp.Interval):
        return None
    flip = a < 0
    sol = [f"Subtract ${b}$ from both sides: ${a}x {OPL[op]} {c - b}$.",
           (f"Divide both sides by ${a}$. Because ${a}$ is negative the inequality flips: $x {OPL[{'<':'>','<=':'>=','>':'<','>=':'<='}[op]]} {num(R(c-b, a))}$."
            if flip else f"Divide both sides by ${a}$ (positive, so the direction is unchanged): $x {OPL[op]} {num(R(c-b, a))}$."),
           f"In interval notation: ${ival_ltx(I)}$."]
    return P(S1, f"Solve the inequality ${lin(a, b)} {OPL[op]} {c}$. Give the solution set in interval notation.",
             'interval', ival(I), d=2 if flip else 1,
             hints=["Isolate x the same way you would for an equation: undo the addition first, then the multiplication.",
                    "Multiplying or dividing both sides by a negative number reverses the inequality sign." if flip
                    else "A strict inequality gives a round bracket; a non-strict one gives a square bracket at that endpoint."],
             sol=sol, verify={'kind': 'interval', 'expected': cond})

def nai_compound(rng):
    b, c = rng.choice([1, 2, 3, 4]), rng.randint(-5, 5)
    lo, hi = rng.randint(-8, 2), rng.randint(3, 12)
    lo_op, hi_op = rng.choice(['<', '<=']), rng.choice(['<', '<='])
    cond = f"({b}*x+({c}) {'>' if lo_op == '<' else '>='} {lo}) & ({b}*x+({c}) {hi_op} {hi})"
    I = sp.sympify(cond).as_set()
    if not isinstance(I, sp.Interval):
        return None
    return P(S1, f"Solve the compound inequality ${lo} {OPL[lo_op]} {lin(b, c)} {OPL[hi_op]} {hi}$. Give the answer in interval notation.",
             'interval', ival(I), d=2,
             hints=["Whatever you do to the middle expression, do to all three parts.",
                    f"Subtract ${c}$ from all three parts, then divide all three parts by ${b}$."],
             sol=[f"Subtract ${c}$ everywhere: ${lo - c} {OPL[lo_op]} {b}x {OPL[hi_op]} {hi - c}$.",
                  f"Divide everywhere by ${b}$: ${num(R(lo - c, b))} {OPL[lo_op]} x {OPL[hi_op]} {num(R(hi - c, b))}$.",
                  f"Interval notation: ${ival_ltx(I)}$."],
             verify={'kind': 'interval', 'expected': cond})

def nai_abs_lt(rng):
    a, b = rng.randint(-6, 6), rng.randint(1, 7)
    op = rng.choice(['<', '<='])
    cond = f"Abs(x-({a})) {op} {b}"
    I = sp.solveset(sp.sympify(cond), x, sp.S.Reals)
    inner = ltx(x - a)
    return P(S1, f"Solve $|{inner}| {OPL[op]} {b}$. Give the solution set in interval notation.",
             'interval', ival(I), d=2,
             hints=[f"$|{inner}| {OPL[op]} {b}$ means the distance from $x$ to ${a}$ is at most ${b}$." if op == '<=' else
                    f"$|{inner}| < {b}$ means the distance from $x$ to ${a}$ is less than ${b}$.",
                    f"Rewrite it without the absolute value: $-{b} {OPL[op]} {inner} {OPL[op]} {b}$."],
             sol=[f"$|{inner}| {OPL[op]} {b}$ is equivalent to $-{b} {OPL[op]} {inner} {OPL[op]} {b}$.",
                  f"Add ${a}$ to all three parts: ${a - b} {OPL[op]} x {OPL[op]} {a + b}$.",
                  f"So the solution set is ${ival_ltx(I)}$."],
             verify={'kind': 'interval', 'expected': cond})

def nai_abs_gt(rng):
    a, b = rng.randint(-5, 5), rng.randint(1, 6)
    S = sp.solveset(sp.Abs(x - a) > b, x, sp.S.Reals)
    inside = [v for v in range(a - b - 6, a + b + 7) if v in S]
    outside = [v for v in range(a - b, a + b + 1)]
    if len(inside) < 1 or len(outside) < 3:
        return None
    good = rng.choice(inside)
    bad = rng.sample(outside, 3)
    opts = [(str(good), str(good))] + [(str(v), str(v)) for v in bad]
    inner = ltx(x - a)
    return choice(S1, f"Which value of $x$ satisfies $|{inner}| > {b}$?", opts, 0, good, d=2, rng=rng,
                  hints=[f"$|{inner}| > {b}$ says the distance from $x$ to ${a}$ is more than ${b}$.",
                         f"The solutions are $x < {a - b}$ or $x > {a + b}$; test each option."],
                  sol=[f"$|{inner}| > {b}$ means ${inner} > {b}$ or ${inner} < -{b}$.",
                       f"That gives $x > {a + b}$ or $x < {a - b}$.",
                       f"Of the options only ${good}$ lies in one of those pieces (its distance from ${a}$ is ${abs(good - a)} > {b}$)."])

def nai_distance(rng):
    a, b = rng.randint(-12, 12), rng.randint(-12, 12)
    if a == b:
        return None
    return P(S1, f"What is the distance between ${a}$ and ${b}$ on the number line?", 'numeric', str(abs(a - b)), d=1,
             hints=["Distance is never negative; it is the absolute value of the difference.",
                    f"Compute $|{a} - ({b})|$."],
             sol=[f"Distance $= |{a} - ({b})| = |{a - b}|$.", f"$= {abs(a - b)}$."],
             verify={'kind': 'numeric', 'value': f"Abs({a}-({b}))"})

def nai_abs_eval(rng):
    a, b, c, d = rng.randint(-9, 9), rng.randint(-9, 9), nz(rng, -9, 9), rng.randint(-5, 5)
    expr = f"Abs({a}-({b})) - Abs({c}) + ({d})"
    val = abs(a - b) - abs(c) + d
    return P(S1, f"Evaluate $|{a} - ({b})| - |{c}| + ({d})$.", 'numeric', str(val), d=1,
             hints=["Work inside each absolute value first, then take the absolute value.",
                    f"$|{a} - ({b})| = |{a - b}| = {abs(a - b)}$ and $|{c}| = {abs(c)}$."],
             sol=[f"$|{a} - ({b})| = |{a - b}| = {abs(a - b)}$.", f"$|{c}| = {abs(c)}$.",
                  f"So the value is ${abs(a - b)} - {abs(c)} + ({d}) = {val}$."],
             verify={'kind': 'numeric', 'value': expr})

def nai_compare(rng):
    cands = [(R(7, 9), frac(7, 9), '7/9'), (R(3, 4), frac(3, 4), '3/4'), (R(5, 8), frac(5, 8), '5/8'),
             (sp.Float('0.7'), '0.7', '0.7'), (sp.Float('0.78'), '0.78', '0.78'), (sp.Float('0.71'), '0.71', '0.71'),
             (sqrt(R(1, 2)), r'\sqrt{0.5}', 'sqrt(0.5)'), (sqrt(R(3, 5)), r'\sqrt{0.6}', 'sqrt(0.6)'),
             (R(2, 3), frac(2, 3), '2/3'), (sp.Float('0.66'), '0.66', '0.66'), (R(11, 16), frac(11, 16), '11/16'),
             (sqrt(2) / 2, frac(r'\sqrt{2}', 2), 'sqrt(2)/2'), (pi / 4, frac(r'\pi', 4), 'pi/4'),
             (R(4, 5), frac(4, 5), '4/5'), (sp.Float('0.8'), '0.8', '0.8')]
    sel = rng.sample(cands, 4)
    vals = [float(c[0]) for c in sel]
    if len({round(v, 6) for v in vals}) < 4:
        return None
    want_max = rng.random() < 0.5
    target = max(vals) if want_max else min(vals)
    ci = vals.index(target)
    fn = 'Max' if want_max else 'Min'
    expected = f"{fn}({', '.join(c[2] for c in sel)})"
    word = 'largest' if want_max else 'smallest'
    return choice(S1, f"Which of these numbers is the {word}?", [(c[1], c[2]) for c in sel], ci, expected, d=1, rng=rng,
                  hints=["Convert everything to decimals to compare.", "Fractions: divide numerator by denominator; roots: estimate to two decimal places."],
                  sol=["As decimals: " + ', '.join(f"${c[1]} \\approx {float(c[0]):.3f}$" for c in sel) + ".",
                       f"The {word} is ${sel[ci][1]}$."])

def nai_setbuilder(rng):
    lo, hi = rng.randint(-9, 3), rng.randint(4, 12)
    lo_op, hi_op = rng.choice(['<', '<=']), rng.choice(['<', '<='])
    cond = f"(x {'>' if lo_op == '<' else '>='} {lo}) & (x {hi_op} {hi})"
    I = sp.sympify(cond).as_set()
    return P(S1, r"Write the set $\{x \mid " + f"{lo} {OPL[lo_op]} x {OPL[hi_op]} {hi}" + r"\}$ in interval notation.",
             'interval', ival(I), d=1,
             hints=["A square bracket means the endpoint is included; a round bracket means it is not.",
                    "$\\le$ includes the endpoint, $<$ does not."],
             sol=[f"The left endpoint ${lo}$ is {'included' if lo_op == '<=' else 'excluded'} and the right endpoint ${hi}$ is {'included' if hi_op == '<=' else 'excluded'}.",
                  f"So the interval is ${ival_ltx(I)}$."],
             verify={'kind': 'interval', 'expected': cond})

def nai_word(rng):
    base, rate, limit = rng.choice([2, 3, 4, 5]), rng.choice([2, 3, 4]), rng.choice([15, 18, 20, 23, 25, 30])
    cond = f"(x>=0) & ({base}+{rate}*x < {limit})"
    I = sp.sympify(cond).as_set()
    return P(S1, f"A ride costs {base} dollars plus {rate} dollars per mile. For which distances $d$ (in miles, $d \\ge 0$) is the fare under {limit} dollars? Answer as an interval.",
             'interval', ival(I), d=2,
             hints=[f"The fare is ${base} + {rate}d$. Write an inequality saying it is less than ${limit}$.",
                    "Remember a distance cannot be negative, so the interval starts at 0."],
             sol=[f"Fare $< {limit}$ means ${base} + {rate}d < {limit}$.", f"So ${rate}d < {limit - base}$ and $d < {num(R(limit - base, rate))}$.",
                  f"With $d \\ge 0$: $d \\in {ival_ltx(I)}$."],
             verify={'kind': 'interval', 'expected': cond})

def nai_abs_eq(rng):
    a, b = rng.randint(-6, 6), rng.randint(1, 9)
    larger = rng.random() < 0.5
    val = a + b if larger else a - b
    inner = ltx(x - a)
    fn = 'Max' if larger else 'Min'
    return P(S1, f"The equation $|{inner}| = {b}$ has two solutions. Find the {'larger' if larger else 'smaller'} one.",
             'numeric', str(val), d=2,
             hints=[f"$|{inner}| = {b}$ means ${inner} = {b}$ or ${inner} = -{b}$.", f"Solve both equations and compare: the solutions are ${a - b}$ and ${a + b}$."],
             sol=[f"Case 1: ${inner} = {b}$ gives $x = {a + b}$.", f"Case 2: ${inner} = -{b}$ gives $x = {a - b}$.",
                  f"The {'larger' if larger else 'smaller'} solution is ${val}$."],
             verify={'kind': 'numeric', 'value': f"{fn}(*solveset(Eq(Abs(x-({a})),{b}),x,Reals))"})

def nai_not_in(rng):
    lo, hi = rng.randint(-8, 0), rng.randint(2, 9)
    lo_open, hi_open = rng.choice([True, False]), rng.choice([True, False])
    I = sp.Interval(lo, hi, lo_open, hi_open)
    inside = [v for v in range(lo - 1, hi + 2) if v in I]
    outside = [v for v in range(lo - 3, hi + 4) if v not in I]
    if len(inside) < 3 or not outside:
        return None
    bad = rng.choice(outside)
    opts = [(str(bad), str(bad))] + [(str(v), str(v)) for v in rng.sample(inside, 3)]
    return choice(S1, f"Which of these numbers is NOT in the interval ${ival_ltx(I)}$?", opts, 0, bad, d=1, rng=rng,
                  hints=["Check whether each endpoint is included (square bracket) or excluded (round bracket).",
                         "A number outside the two endpoints, or an excluded endpoint, is not in the interval."],
                  sol=[f"The interval contains every number between ${lo}$ and ${hi}$" +
                       (f", with ${lo}$ {'excluded' if lo_open else 'included'} and ${hi}$ {'excluded' if hi_open else 'included'}."),
                       f"${bad}$ is not in it."])

def nai_abs_coef(rng):
    a, b, c = rng.choice([2, 3, 4, 5]), rng.randint(-7, 7), rng.randint(1, 9)
    op = rng.choice(['<', '<='])
    cond = f"Abs({a}*x+({b})) {op} {c}"
    I = sp.solveset(sp.sympify(cond), x, sp.S.Reals)
    if not isinstance(I, sp.Interval):
        return None
    inner = lin(a, b)
    return P(S1, f"Solve $|{inner}| {OPL[op]} {c}$. Give the solution set in interval notation.", 'interval', ival(I), d=3,
             hints=[f"Rewrite as the double inequality $-{c} {OPL[op]} {inner} {OPL[op]} {c}$.", f"Then subtract ${b}$ from all three parts and divide by ${a}$."],
             sol=[f"$-{c} {OPL[op]} {inner} {OPL[op]} {c}$.", f"Subtract ${b}$: ${-c - b} {OPL[op]} {a}x {OPL[op]} {c - b}$.",
                  f"Divide by ${a}$: ${num(R(-c - b, a))} {OPL[op]} x {OPL[op]} {num(R(c - b, a))}$, i.e. ${ival_ltx(I)}$."],
             verify={'kind': 'interval', 'expected': cond})

FAM = {S1: [nai_linear, nai_compound, nai_abs_lt, nai_abs_gt, nai_distance, nai_abs_eval, nai_compare, nai_setbuilder, nai_word, nai_abs_eq, nai_not_in, nai_abs_coef]}

# ================================================================ exponents-and-radicals
S2 = 'exponents-and-radicals'

def exr_product_quotient(rng):
    a, b, c = rng.randint(2, 7), rng.randint(1, 6), rng.randint(1, 9)
    e = a + b - c
    if e == 0:
        return None
    ans = x ** e
    return P(S2, r"Simplify $\dfrac{x^{" + str(a) + r"} \cdot x^{" + str(b) + r"}}{x^{" + str(c) + r"}}$. Write the answer with a single power of $x$" +
             (" (a positive exponent in the denominator is fine)." if e < 0 else "."),
             'equiv', plain(ans), d=1 if e > 0 else 2,
             hints=["Same base multiplied: add the exponents. Same base divided: subtract the exponents.",
                    f"The numerator is $x^{{{a + b}}}$; now subtract ${c}$."],
             sol=[f"$x^{{{a}}} \\cdot x^{{{b}}} = x^{{{a + b}}}$.", f"$x^{{{a + b}}} / x^{{{c}}} = x^{{{a + b - c}}}$." +
                  (f" A negative exponent means a reciprocal: $x^{{{e}}} = \\dfrac{{1}}{{x^{{{-e}}}}}$." if e < 0 else "")],
             verify={'kind': 'equiv', 'expected': f"x**{a}*x**{b}/x**{c}"}, domain=(0.5, 3))

def exr_power_of_product(rng):
    a, m, n, p = rng.choice([2, 3, 4, 5]), rng.randint(1, 4), rng.randint(1, 3), rng.choice([2, 3])
    expr = (a * x ** m * y ** n) ** p
    return P(S2, f"Simplify $\\left({a}x^{{{m}}}y^{{{n}}}\\right)^{{{p}}}$.", 'equiv', plain(sp.expand(expr)), d=2,
             hints=["A power of a product is the product of the powers: raise every factor to the outer exponent.",
                    f"Raise the coefficient: ${a}^{{{p}}} = {a ** p}$. For the variables, multiply exponents."],
             sol=[f"Apply the exponent to each factor: ${a}^{{{p}}} \\cdot (x^{{{m}}})^{{{p}}} \\cdot (y^{{{n}}})^{{{p}}}$.",
                  f"Multiply exponents: $x^{{{m * p}}}$ and $y^{{{n * p}}}$.", f"Result: ${ltx(sp.expand(expr))}$."],
             verify={'kind': 'equiv', 'expected': f"({a}*x**{m}*y**{n})**{p}"})

def exr_fractional(rng):
    base = rng.choice([4, 8, 9, 16, 25, 27, 32, 36, 49, 64, 81, 100, 125])
    ex = rng.choice([R(1, 2), R(3, 2), R(2, 3), R(-1, 2), R(-2, 3), R(1, 3), R(3, 4), R(5, 2), R(-3, 2), R(4, 3), R(-1, 3)])
    val = sp.Integer(base) ** ex
    if not val.is_Rational:
        return None
    root = sp.Integer(base) ** (1 / sp.Integer(ex.q))
    d = 1 if ex > 0 and ex.p == 1 else (2 if ex > 0 else 3)
    return P(S2, f"Evaluate ${base}^{{{num(ex)}}}$ without a calculator.", 'numeric', fmt_num(val), d=d,
             hints=[f"$a^{{m/n}}$ means take the ${ex.q}$th root first, then raise to the power ${abs(ex.p)}$." +
                    (" A negative exponent means take the reciprocal at the end." if ex < 0 else ""),
                    f"The ${ex.q}$th root of ${base}$ is ${root}$."],
             sol=[f"${base}^{{1/{ex.q}}} = {root}$ because ${root}^{{{ex.q}}} = {base}$.",
                  f"Raise to the power ${abs(ex.p)}$: ${root}^{{{abs(ex.p)}}} = {root ** abs(ex.p)}$."] +
                 ([f"Take the reciprocal for the negative exponent: ${num(val)}$."] if ex < 0 else []),
             verify={'kind': 'numeric', 'value': f"{base}**({ex.p}/{ex.q})"})

def exr_simplify_root(rng):
    a, b = rng.choice([2, 3, 4, 5, 6]), rng.choice([2, 3, 5, 6, 7, 10])
    n = a * a * b
    ans = sqrt(n)
    return P(S2, f"Simplify $\\sqrt{{{n}}}$ (take all perfect-square factors out of the root).", 'numeric', plain(ans), d=1 if a <= 3 else 2,
             hints=["Look for the largest perfect square that divides the number.", f"${n} = {a * a} \\cdot {b}$."],
             sol=[f"$\\sqrt{{{n}}} = \\sqrt{{{a * a} \\cdot {b}}} = \\sqrt{{{a * a}}}\\sqrt{{{b}}}$.", f"$= {a}\\sqrt{{{b}}}$."],
             verify={'kind': 'numeric', 'value': f"sqrt({n})"})

def exr_cube_root(rng):
    a, b = rng.choice([2, 3]), rng.choice([2, 3, 5, 7])
    n = a ** 3 * b
    ans = sp.cbrt(n)
    return P(S2, f"Simplify $\\sqrt[3]{{{n}}}$.", 'numeric', plain(ans), d=3,
             hints=["Look for a perfect cube factor.", f"${n} = {a ** 3} \\cdot {b}$ and ${a ** 3} = {a}^3$."],
             sol=[f"$\\sqrt[3]{{{n}}} = \\sqrt[3]{{{a ** 3} \\cdot {b}}} = \\sqrt[3]{{{a ** 3}}}\\sqrt[3]{{{b}}}$.", f"$= {a}\\sqrt[3]{{{b}}}$."],
             verify={'kind': 'numeric', 'value': f"cbrt({n})"})

def exr_negative(rng):
    a, m, n = rng.choice([2, 3, 5, 7]), rng.randint(1, 4), rng.randint(1, 4)
    expr = a * y ** n / x ** m
    return P(S2, f"Rewrite ${a}x^{{-{m}}}y^{{{n}}}$ using only positive exponents.", 'equiv', plain(expr), d=2,
             hints=["A negative exponent means a reciprocal: $x^{-m} = 1/x^{m}$.", "Only the factor with the negative exponent moves to the denominator."],
             sol=[f"$x^{{-{m}}} = \\dfrac{{1}}{{x^{{{m}}}}}$.", f"So ${a}x^{{-{m}}}y^{{{n}}} = {ltx(expr)}$."],
             verify={'kind': 'equiv', 'expected': f"{a}*x**(-{m})*y**{n}"}, domain=(0.5, 3))

def exr_negative_quotient(rng):
    m, n = rng.randint(1, 4), rng.randint(1, 4)
    expr = y ** n / x ** m
    return P(S2, f"Rewrite $\\dfrac{{x^{{-{m}}}}}{{y^{{-{n}}}}}$ using only positive exponents.", 'equiv', plain(expr), d=2,
             hints=["A factor with a negative exponent switches between numerator and denominator.", f"$x^{{-{m}}}$ goes down, $y^{{-{n}}}$ comes up."],
             sol=[f"$x^{{-{m}}} = 1/x^{{{m}}}$ in the numerator and $1/y^{{-{n}}} = y^{{{n}}}$ in the denominator.", f"Result: ${ltx(expr)}$."],
             verify={'kind': 'equiv', 'expected': f"x**(-{m})/y**(-{n})"}, domain=(0.5, 3))

def exr_rationalize(rng):
    c, b = rng.choice([1, 2, 3, 4, 5, 6, 9, 10, 12]), rng.choice([2, 3, 5, 6, 7])
    ans = sp.radsimp(sp.Integer(c) / sqrt(b))
    return P(S2, f"Rationalize the denominator: $\\dfrac{{{c}}}{{\\sqrt{{{b}}}}}$.", 'numeric', plain(ans), d=2,
             hints=[f"Multiply numerator and denominator by $\\sqrt{{{b}}}$.", f"$\\sqrt{{{b}}}\\cdot\\sqrt{{{b}}} = {b}$."],
             sol=[f"$\\dfrac{{{c}}}{{\\sqrt{{{b}}}}} \\cdot \\dfrac{{\\sqrt{{{b}}}}}{{\\sqrt{{{b}}}}} = \\dfrac{{{c}\\sqrt{{{b}}}}}{{{b}}}$.", f"Simplified: ${ltx(ans)}$."],
             verify={'kind': 'numeric', 'value': f"{c}/sqrt({b})"})

def exr_rationalize_binomial(rng):
    a, b = rng.choice([2, 3, 5, 7]), rng.choice([1, 2, 3])
    if a == b * b:
        return None
    ans = sp.radsimp(1 / (sqrt(a) + b))
    return P(S2, f"Rationalize the denominator: $\\dfrac{{1}}{{\\sqrt{{{a}}} + {b}}}$.", 'numeric', plain(ans), d=3,
             hints=[f"Multiply top and bottom by the conjugate $\\sqrt{{{a}}} - {b}$.", f"$(\\sqrt{{{a}}}+{b})(\\sqrt{{{a}}}-{b}) = {a} - {b * b}$."],
             sol=[f"$\\dfrac{{1}}{{\\sqrt{{{a}}}+{b}}}\\cdot\\dfrac{{\\sqrt{{{a}}}-{b}}}{{\\sqrt{{{a}}}-{b}}} = \\dfrac{{\\sqrt{{{a}}}-{b}}}{{{a - b * b}}}$.", f"Simplified: ${ltx(ans)}$."],
             verify={'kind': 'numeric', 'value': f"1/(sqrt({a})+{b})"})

def exr_root_of_power(rng):
    a, b, m = rng.choice([2, 3, 4, 5]), rng.choice([1, 2, 3, 5]), rng.randint(1, 3)
    n = a * a * b
    ans = a * sqrt(b) * x ** m
    return P(S2, f"For $x > 0$, simplify $\\sqrt{{{n}x^{{{2 * m}}}}}$.", 'equiv', plain(ans), d=2,
             hints=["Split the root over the factors: $\\sqrt{ab} = \\sqrt{a}\\sqrt{b}$.", f"$\\sqrt{{x^{{{2 * m}}}}} = x^{{{m}}}$ when $x > 0$, and ${n} = {a * a}\\cdot{b}$."],
             sol=[f"$\\sqrt{{{n}x^{{{2 * m}}}}} = \\sqrt{{{a * a}}}\\sqrt{{{b}}}\\sqrt{{x^{{{2 * m}}}}}$.", f"$= {ltx(ans)}$."],
             verify={'kind': 'equiv', 'expected': f"sqrt({n}*x**{2 * m})"}, domain=(0.1, 3))

def exr_choice_rule(rng):
    kind = rng.choice(['prod', 'power', 'quot'])
    b = rng.choice([2, 3, 5])
    if kind == 'prod':
        m, n = rng.randint(2, 6), rng.randint(2, 6)
        stmt, expected = f"Which expression equals ${b}^{{{m}}} \\cdot {b}^{{{n}}}$?", f"{b}**{m}*{b}**{n}"
        opts = [(f"{b}^{{{m + n}}}", f"{b}^{m + n}"), (f"{b}^{{{m * n}}}", f"{b}^{m * n}"), (f"{b * b}^{{{m + n}}}", f"{b * b}^{m + n}"), (f"{b * b}^{{{m * n}}}", f"{b * b}^{m * n}")]
        rule = "same base, multiply: add exponents"
    elif kind == 'power':
        m, n = rng.randint(2, 4), rng.randint(2, 4)
        stmt, expected = f"Which expression equals $\\left({b}^{{{m}}}\\right)^{{{n}}}$?", f"({b}**{m})**{n}"
        opts = [(f"{b}^{{{m * n}}}", f"{b}^{m * n}"), (f"{b}^{{{m + n}}}", f"{b}^{m + n}"), (f"{b}^{{{m ** n}}}", f"{b}^{m ** n}"), (f"{b * n}^{{{m}}}", f"{b * n}^{m}")]
        rule = "a power of a power: multiply exponents"
    else:
        m, n = rng.randint(5, 9), rng.randint(2, 4)
        stmt, expected = f"Which expression equals $\\dfrac{{{b}^{{{m}}}}}{{{b}^{{{n}}}}}$?", f"{b}**{m}/{b}**{n}"
        opts = [(f"{b}^{{{m - n}}}", f"{b}^{m - n}"), (f"{b}^{{{m + n}}}", f"{b}^{m + n}"), (f"1^{{{m - n}}}", f"1^{m - n}"), (f"{b}^{{{m}/{n}}}", f"{b}^({m}/{n})")]
        rule = "same base, divide: subtract exponents"
    vals = [float(sp.sympify(o[1].replace('^', '**'))) for o in opts]
    if len(set(vals)) < 4:
        return None
    return choice(S2, stmt, opts, 0, expected, d=1, rng=rng,
                  hints=[f"Rule: {rule}.", "Try it with small numbers if you are unsure, e.g. $2^2 \\cdot 2^3 = 4 \\cdot 8 = 32 = 2^5$."],
                  sol=[f"Rule: {rule}.", f"So the answer is ${opts[0][0]}$."])

def exr_radical_to_power(rng):
    forms = [(r"x\sqrt{x}", "x*sqrt(x)", R(3, 2)), (r"\dfrac{\sqrt{x}}{x}", "sqrt(x)/x", R(-1, 2)), (r"\sqrt[3]{x^{2}}", "cbrt(x**2)", R(2, 3)),
             (r"\dfrac{1}{\sqrt{x^{3}}}", "1/sqrt(x**3)", R(-3, 2)), (r"x^{2}\sqrt{x}", "x**2*sqrt(x)", R(5, 2)), (r"\sqrt{x}\,\sqrt[3]{x}", "sqrt(x)*cbrt(x)", R(5, 6)),
             (r"\dfrac{x}{\sqrt[3]{x}}", "x/cbrt(x)", R(2, 3)), (r"\dfrac{1}{\sqrt[4]{x}}", "1/x**(1/4)", R(-1, 4)), (r"\sqrt{x^{5}}", "sqrt(x**5)", R(5, 2)), (r"\sqrt[4]{x^{3}}", "x**(3/4)", R(3, 4))]
    lt, ex, e = rng.choice(forms)
    ans = x ** e
    return P(S2, f"For $x > 0$, write ${lt}$ as a single power of $x$ (fractional and negative exponents allowed).", 'equiv', plain(ans), d=2,
             hints=["$\\sqrt[n]{x} = x^{1/n}$, and dividing by a power means a negative exponent.", "Then add or subtract the exponents as fractions."],
             sol=[f"Rewrite every root as a fractional exponent and every reciprocal as a negative exponent.",
                  f"Combine the exponents: the result is $x^{{{num(e)}}}$."],
             verify={'kind': 'equiv', 'expected': ex}, domain=(0.2, 3))

def exr_solve_exponent(rng):
    b, n = rng.choice([2, 3, 4, 5, 10]), rng.randint(2, 6)
    c = rng.randint(-2, 2)
    v = b ** n
    if n - c <= 0:
        return None
    return P(S2, f"Solve for $n$: ${b}^{{{ltx(x + c).replace('x', 'n')}}} = {v}$.", 'numeric', str(n - c), d=2 if c else 1,
             hints=[f"Write ${v}$ as a power of ${b}$.", f"${v} = {b}^{{{n}}}$, so the exponents must be equal."],
             sol=[f"${v} = {b}^{{{n}}}$.", f"Equal bases means equal exponents: ${ltx(x + c).replace('x', 'n')} = {n}$.", f"So $n = {n - c}$."],
             verify={'kind': 'solve', 'lhs': f"{b}**(x+({c}))", 'rhs': str(v)})

def exr_monomial_product(rng):
    a, m, b, n, p = rng.choice([2, 3, 4]), rng.randint(1, 3), rng.choice([2, 3, 5]), rng.randint(1, 3), rng.choice([2, 3])
    expr = (a * x ** m) ** p * (b * x ** n)
    return P(S2, f"Simplify $\\left({a}x^{{{m}}}\\right)^{{{p}}}\\left({b}x^{{{n}}}\\right)$.", 'equiv', plain(sp.expand(expr)), d=2,
             hints=["Deal with the power first: raise the coefficient and the variable to that power.", "Then multiply coefficients and add the exponents of $x$."],
             sol=[f"$\\left({a}x^{{{m}}}\\right)^{{{p}}} = {a ** p}x^{{{m * p}}}$.", f"Multiply by ${b}x^{{{n}}}$: ${a ** p * b}x^{{{m * p + n}}}$."],
             verify={'kind': 'equiv', 'expected': f"({a}*x**{m})**{p}*({b}*x**{n})"})

def exr_zero_negative(rng):
    a, b, c = rng.choice([3, 5, 7, 9, 12]), rng.choice([2, 3, 4, 5]), rng.choice([1, 2, 3])
    val = 1 + R(1, b ** c)
    sign = rng.choice([1, -1])
    val = 1 + sign * R(1, b ** c)
    op = '+' if sign > 0 else '-'
    return P(S2, f"Evaluate ${a}^{{0}} {op} {b}^{{-{c}}}$.", 'numeric', fmt_num(val), d=1,
             hints=["Any non-zero number to the power 0 is 1.", f"${b}^{{-{c}}} = \\dfrac{{1}}{{{b}^{{{c}}}}}$."],
             sol=[f"${a}^0 = 1$ and ${b}^{{-{c}}} = {frac(1, b ** c)}$.", f"So the value is $1 {op} {frac(1, b ** c)} = {num(val)}$."],
             verify={'kind': 'numeric', 'value': f"{a}**0 {op} {b}**(-{c})"})

FAM[S2] = [exr_product_quotient, exr_power_of_product, exr_fractional, exr_simplify_root, exr_cube_root, exr_negative, exr_negative_quotient,
           exr_rationalize, exr_rationalize_binomial, exr_root_of_power, exr_choice_rule, exr_radical_to_power, exr_solve_exponent, exr_monomial_product, exr_zero_negative]

# ================================================================ linear-equations
S3 = 'linear-equations'

def le_two_sided(rng):
    a, c = nz(rng, -7, 7), nz(rng, -7, 7)
    if a == c:
        return None
    b, d = rng.randint(-9, 9), rng.randint(-9, 9)
    sol = R(d - b, a - c)
    return P(S3, f"Solve for $x$: ${lin(a, b)} = {lin(c, d)}$.", 'numeric', fmt_num(sol), d=1 if sol.is_Integer else 2,
             hints=["Collect the $x$ terms on one side and the constants on the other.", f"Subtract ${c}x$ and ${b}$ from both sides."],
             sol=[f"Subtract ${c}x$ from both sides: ${a - c}x + ({b}) = {d}$.", f"Subtract ${b}$: ${a - c}x = {d - b}$.", f"Divide by ${a - c}$: $x = {num(sol)}$."],
             verify={'kind': 'solve', 'lhs': f"{a}*x+({b})", 'rhs': f"{c}*x+({d})"})

def le_parentheses(rng):
    a, b, c, d, e = nz(rng, -5, 5), nz(rng, -6, 6), nz(rng, -5, 5), nz(rng, -6, 6), rng.randint(-9, 9)
    if a == c:
        return None
    lhs, rhs = a * (x + b), c * (x - d) + e
    sol = sp.solve(sp.Eq(lhs, rhs), x)
    if len(sol) != 1:
        return None
    return P(S3, f"Solve for $x$: ${a}({ltx(x + b)}) = {c}({ltx(x - d)}) + ({e})$.", 'numeric', fmt_num(sol[0]), d=2,
             hints=["Distribute first to remove the parentheses.", f"Left side becomes ${ltx(sp.expand(lhs))}$; right side becomes ${ltx(sp.expand(rhs))}$."],
             sol=[f"Distribute: ${ltx(sp.expand(lhs))} = {ltx(sp.expand(rhs))}$.", f"Move the $x$ terms together: ${a - c}x = {sp.expand(rhs).subs(x, 0) - a * b}$.", f"Divide: $x = {num(sol[0])}$."],
             verify={'kind': 'solve', 'lhs': f"{a}*(x+({b}))", 'rhs': f"{c}*(x-({d}))+({e})"})

def le_fraction(rng):
    a, b, c = rng.choice([2, 3, 4, 5, 6]), rng.randint(-8, 8), rng.randint(-8, 8)
    sol = (c - b) * a
    return P(S3, f"Solve for $x$: $\\dfrac{{x}}{{{a}}} + ({b}) = {c}$.", 'numeric', str(sol), d=2,
             hints=["Undo the addition first, then undo the division.", f"After subtracting ${b}$, multiply both sides by ${a}$."],
             sol=[f"Subtract ${b}$: $\\dfrac{{x}}{{{a}}} = {c - b}$.", f"Multiply by ${a}$: $x = {sol}$."],
             verify={'kind': 'solve', 'lhs': f"x/{a}+({b})", 'rhs': str(c)})

def le_slope(rng):
    x1, y1, x2, y2 = pick_points(rng)
    m = R(y2 - y1, x2 - x1)
    return P(S3, f"Find the slope of the line through $({x1}, {y1})$ and $({x2}, {y2})$.", 'numeric', fmt_num(m), d=1,
             hints=["Slope is rise over run: change in $y$ divided by change in $x$.", f"$m = \\dfrac{{{y2} - ({y1})}}{{{x2} - ({x1})}}$."],
             sol=[f"$m = \\dfrac{{{y2} - ({y1})}}{{{x2} - ({x1})}} = \\dfrac{{{y2 - y1}}}{{{x2 - x1}}}$.", f"$m = {num(m)}$."],
             verify={'kind': 'numeric', 'value': f"({y2}-({y1}))/({x2}-({x1}))"})

def le_point_slope(rng):
    m = rng.choice([1, 2, 3, -1, -2, -3, R(1, 2), R(-1, 2), R(2, 3), R(3, 4), R(-3, 2)])
    x0, y0 = rng.randint(-6, 6), rng.randint(-6, 6)
    expr = sp.expand(m * (x - x0) + y0)
    return P(S3, f"Write the equation of the line with slope ${num(m)}$ through $({x0}, {y0})$ in the form $y = mx + b$. Enter the right-hand side only.",
             'equiv', plain(expr), d=2,
             hints=["Start from point-slope form: $y - y_0 = m(x - x_0)$.", f"$y - ({y0}) = {num(m)}(x - ({x0}))$; then solve for $y$."],
             sol=[f"Point-slope: $y - ({y0}) = {num(m)}(x - ({x0}))$.", f"Distribute: $y = {ltx(m * x)} {'+' if -m * x0 >= 0 else '-'} {num(abs(m * x0))} + ({y0})$.", f"So $y = {ltx(expr)}$."],
             verify={'kind': 'equiv', 'expected': f"({m})*(x-({x0}))+({y0})"})

def le_two_points(rng):
    x1, y1, x2, y2 = pick_points(rng)
    m = R(y2 - y1, x2 - x1)
    expr = sp.expand(y1 + m * (x - x1))
    return P(S3, f"Find the equation of the line through $({x1}, {y1})$ and $({x2}, {y2})$. Give it as $y = mx + b$ and enter the right-hand side.",
             'equiv', plain(expr), d=2 if m.is_Integer else 3,
             hints=["First find the slope from the two points.", f"The slope is ${num(m)}$; then use point-slope form with either point."],
             sol=[f"Slope: $m = \\dfrac{{{y2} - ({y1})}}{{{x2} - ({x1})}} = {num(m)}$.", f"Point-slope with $({x1}, {y1})$: $y - ({y1}) = {num(m)}(x - ({x1}))$.", f"Solve for $y$: $y = {ltx(expr)}$."],
             verify={'kind': 'equiv', 'expected': f"{y1}+({m})*(x-({x1}))"})

def le_parallel_perp(rng):
    m = rng.choice([1, 2, 3, -1, -2, -3, R(1, 2), R(-1, 2), R(2, 3), R(-3, 4)])
    b = rng.randint(-5, 5)
    x0, y0 = rng.randint(-5, 5), rng.randint(-5, 5)
    perp = rng.random() < 0.5
    m2 = -1 / m if perp else m
    expr = sp.expand(m2 * (x - x0) + y0)
    word = 'perpendicular' if perp else 'parallel'
    return P(S3, f"Find the line through $({x0}, {y0})$ that is {word} to $y = {lin(m, b)}$. Give it as $y = mx + b$ and enter the right-hand side.",
             'equiv', plain(expr), d=3 if perp else 2,
             hints=["Parallel lines share a slope; perpendicular slopes are negative reciprocals.", f"The slope you need is ${num(m2)}$; then use point-slope form."],
             sol=[f"The given slope is ${num(m)}$, so the {word} slope is ${num(m2)}$.", f"Point-slope: $y - ({y0}) = {num(m2)}(x - ({x0}))$.", f"Simplify: $y = {ltx(expr)}$."],
             verify={'kind': 'equiv', 'expected': f"({m2})*(x-({x0}))+({y0})"})

def le_intercepts(rng):
    a, b, c = nz(rng, -6, 6), nz(rng, -6, 6), nz(rng, -12, 12)
    which = rng.choice(['x', 'y'])
    coef = a if which == 'x' else b
    val = R(c, coef)
    return P(S3, f"Find the ${which}$-intercept of the line ${ltx(a * x + b * y)} = {c}$. Enter just the {which}-coordinate.", 'numeric', fmt_num(val), d=1,
             hints=[f"At the ${which}$-intercept the other variable is $0$.", f"Set ${'y' if which == 'x' else 'x'} = 0$ and solve for ${which}$."],
             sol=[f"Set ${'y' if which == 'x' else 'x'} = 0$: ${coef}{which} = {c}$.", f"So ${which} = {num(val)}$."],
             verify={'kind': 'solve', 'lhs': f"{coef}*x", 'rhs': str(c)})

def le_word(rng):
    kind = rng.choice(['gym', 'phone', 'rental', 'savings'])
    if kind == 'gym':
        fee, rate, total = rng.choice([20, 25, 30, 40]), rng.choice([10, 12, 15, 18]), None
        n = rng.randint(4, 12); total = fee + rate * n
        stmt = f"A gym charges a {fee} dollar sign-up fee plus {rate} dollars per month. After how many months does the total paid reach {total} dollars?"
        lhs, rhs, h = f"{fee}+{rate}*x", str(total), f"Total $= {fee} + {rate}m$."
    elif kind == 'phone':
        base, cents, mins = rng.choice([15, 20, 25]), rng.choice([5, 10, 20]), rng.choice([40, 60, 75, 90, 120])
        total = R(base) + R(cents, 100) * mins
        stmt = f"A phone plan costs {base} dollars per month plus {cents} cents per minute of calls. If one month's bill was {float(total):.2f} dollars, how many minutes were used?"
        lhs, rhs, h, n = f"{base}+({cents}/100)*x", f"{total.p}/{total.q}", f"Bill $= {base} + {num(R(cents, 100))}m$.", mins
    elif kind == 'rental':
        day, mile, miles = rng.choice([30, 35, 40]), rng.choice([R(1, 4), R(1, 2), R(3, 10)]), rng.choice([80, 100, 120, 150, 200])
        total = day + mile * miles
        stmt = f"A rental car costs {day} dollars per day plus {float(mile):g} dollars per mile. A one-day rental cost {float(total):.2f} dollars. How many miles were driven?"
        lhs, rhs, h, n = f"{day}+({mile})*x", f"{total}", f"Cost $= {day} + {num(mile)}d$.", miles
    else:
        start, weekly, weeks = rng.choice([50, 80, 120]), rng.choice([15, 20, 25]), rng.randint(5, 14)
        total = start + weekly * weeks
        stmt = f"Jo starts with {start} dollars in savings and adds {weekly} dollars every week. After how many weeks will the savings reach {total} dollars?"
        lhs, rhs, h, n = f"{start}+{weekly}*x", str(total), f"Savings $= {start} + {weekly}w$.", weeks
    return P(S3, stmt, 'numeric', str(n), d=2 if kind in ('phone', 'rental') else 1,
             hints=["Write the total as a fixed amount plus a rate times the unknown.", h],
             sol=[f"Set up the equation: ${sp.latex(sp.sympify(lhs))} = {sp.latex(sp.sympify(rhs))}$.", "Subtract the fixed amount, then divide by the rate.", f"The unknown is ${n}$."],
             verify={'kind': 'solve', 'lhs': lhs, 'rhs': rhs})

def le_choice_line(rng):
    m, x0, y0 = rng.choice([2, 3, -2, -1, R(1, 2)]), rng.randint(-4, 4), rng.randint(-4, 4)
    e = sp.expand(m * (x - x0) + y0)
    cands = [(e, True), (sp.expand(-m * (x - x0) + y0), False), (sp.expand(m * (x + x0) + y0), False), (sp.expand(m * x + y0), False), (sp.expand(m * (x - x0) - y0), False)]
    seen, opts = set(), []
    for ex, ok in cands:
        s = plain(ex)
        if s in seen:
            continue
        seen.add(s); opts.append((f"y = {ltx(ex)}", s))
    if len(opts) < 4:
        return None
    opts = opts[:4]
    return choice(S3, f"Which equation describes the line with slope ${num(m)}$ that passes through $({x0}, {y0})$?", opts, 0, str(e), d=2, rng=rng,
                  hints=["Check the slope first: it is the coefficient of $x$.", f"Then plug in $x = {x0}$ and see which equation gives $y = {y0}$."],
                  sol=[f"The slope ${num(m)}$ must be the coefficient of $x$.", f"Substituting $x = {x0}$ into $y = {ltx(e)}$ gives $y = {y0}$, so that is the line."])

def le_cross_axis(rng):
    m, b = rng.choice([2, 3, 4, -2, -3, 5, R(1, 2), R(3, 2)]), nz(rng, -9, 9)
    val = -R(b) / m
    return P(S3, f"Where does the line $y = {lin(m, b)}$ cross the $x$-axis? Enter the $x$-coordinate.", 'numeric', fmt_num(val), d=1,
             hints=["On the $x$-axis, $y = 0$.", f"Solve ${lin(m, b)} = 0$."],
             sol=[f"Set $y = 0$: ${lin(m, b)} = 0$.", f"So ${ltx(m * x)} = {-b}$ and $x = {num(val)}$."],
             verify={'kind': 'solve', 'lhs': f"({m})*x+({b})", 'rhs': '0'})

def le_predict(rng):
    m, x0, y0, x1 = rng.choice([2, 3, -2, 4, R(1, 2), R(-3, 2)]), rng.randint(-4, 4), rng.randint(-6, 6), rng.randint(5, 10)
    val = y0 + m * (x1 - x0)
    return P(S3, f"A line has slope ${num(m)}$ and passes through $({x0}, {y0})$. What is $y$ when $x = {x1}$?", 'numeric', fmt_num(val), d=2,
             hints=["Slope tells you how much $y$ changes for each unit change in $x$.", f"From $x = {x0}$ to $x = {x1}$ is a run of ${x1 - x0}$; the rise is ${num(m)} \\cdot {x1 - x0}$."],
             sol=[f"Run: ${x1} - ({x0}) = {x1 - x0}$. Rise: ${num(m)} \\cdot {x1 - x0} = {num(m * (x1 - x0))}$.", f"$y = {y0} + {num(m * (x1 - x0))} = {num(val)}$."],
             verify={'kind': 'numeric', 'value': f"{y0}+({m})*({x1}-({x0}))"})

def le_slope_from_standard(rng):
    a, b, c = nz(rng, -6, 6), nz(rng, -6, 6), rng.randint(-10, 10)
    ysol = sp.solve(sp.Eq(a * x + b * y, c), y)[0]
    m = sp.diff(ysol, x)
    return P(S3, f"What is the slope of the line ${ltx(a * x + b * y)} = {c}$?", 'numeric', fmt_num(m), d=2,
             hints=["Solve for $y$ to get slope-intercept form.", f"Move ${a}x$ to the right and divide everything by ${b}$."],
             sol=[f"${b}y = {ltx(-a * x + c)}$.", f"$y = {ltx(ysol)}$, so the slope is ${num(m)}$."],
             verify={'kind': 'numeric', 'value': str(m)})

FAM[S3] = [le_two_sided, le_parentheses, le_fraction, le_slope, le_point_slope, le_two_points, le_parallel_perp, le_intercepts, le_word, le_choice_line, le_cross_axis, le_predict, le_slope_from_standard]

# ================================================================ systems-of-equations
S4 = 'systems-of-equations'

def _system(rng, rational=False):
    """Returns (a,b,c,d,e,f, xs, ys) with a*x+b*y=c, d*x+e*y=f."""
    for _ in range(50):
        a, b, d, e = nz(rng, -5, 5), nz(rng, -5, 5), nz(rng, -5, 5), nz(rng, -5, 5)
        if a * e - b * d == 0:
            continue
        if rational:
            c, f = rng.randint(-9, 9), rng.randint(-9, 9)
            sol = sp.solve([a * x + b * y - c, d * x + e * y - f], [x, y])
            if sol[x].is_Integer and sol[y].is_Integer:
                continue
            return a, b, c, d, e, f, sol[x], sol[y]
        xs, ys = rng.randint(-5, 5), rng.randint(-5, 5)
        return a, b, a * xs + b * ys, d, e, d * xs + e * ys, sp.Integer(xs), sp.Integer(ys)
    return None

def sys_ltx(a, b, c, d, e, f):
    return r"\begin{cases} " + ltx(a * x + b * y) + f" = {c} \\\\ " + ltx(d * x + e * y) + f" = {f} \\end{{cases}}"

def se_solve(rng):
    rational = rng.random() < 0.25
    s = _system(rng, rational)
    if not s:
        return None
    a, b, c, d, e, f, xs, ys = s
    which = rng.choice(['x', 'y'])
    val = xs if which == 'x' else ys
    easy = 1 in (abs(a), abs(b), abs(d), abs(e))
    dd = 3 if rational else (1 if easy else 2)
    return P(S4, f"Solve the system ${sys_ltx(a, b, c, d, e, f)}$ and enter the value of ${which}$.", 'numeric', fmt_num(val), d=dd,
             hints=["Use elimination: scale the equations so one variable has opposite coefficients, then add.",
                    f"Multiply the first equation by ${d}$ and the second by ${-a}$ to eliminate $x$." if which == 'y' else f"Multiply the first equation by ${e}$ and the second by ${-b}$ to eliminate $y$."],
             sol=[f"Eliminate one variable: ${e}\\cdot({ltx(a * x + b * y)}) - {b}\\cdot({ltx(d * x + e * y)}) = {e * c - b * f}$ gives ${a * e - b * d}x = {e * c - b * f}$, so $x = {num(xs)}$.",
                  f"Substitute back: $y = {num(ys)}$.", f"So ${which} = {num(val)}$."],
             verify={'kind': 'numeric', 'value': str(val)})

def se_substitution(rng):
    m1, b1, m2, b2 = nz(rng, -4, 4), rng.randint(-8, 8), nz(rng, -4, 4), rng.randint(-8, 8)
    if m1 == m2:
        return None
    xs = R(b2 - b1, m1 - m2)
    return P(S4, f"The lines $y = {lin(m1, b1)}$ and $y = {lin(m2, b2)}$ intersect at one point. Find its $x$-coordinate.", 'numeric', fmt_num(xs), d=1 if xs.is_Integer else 2,
             hints=["At the intersection both equations give the same $y$, so set the right-hand sides equal.", f"Solve ${lin(m1, b1)} = {lin(m2, b2)}$."],
             sol=[f"Set equal: ${lin(m1, b1)} = {lin(m2, b2)}$.", f"${m1 - m2}x = {b2 - b1}$, so $x = {num(xs)}$."],
             verify={'kind': 'solve', 'lhs': f"{m1}*x+({b1})", 'rhs': f"{m2}*x+({b2})"})

def se_word(rng):
    kind = rng.choice(['tickets', 'coins', 'numbers', 'mixture'])
    if kind == 'tickets':
        pa, pc, adults, kids = rng.choice([8, 10, 12]), rng.choice([4, 5, 6]), rng.randint(5, 30), rng.randint(5, 30)
        n, total = adults + kids, pa * adults + pc * kids
        stmt = f"Adult tickets cost {pa} dollars and child tickets cost {pc} dollars. {n} tickets were sold for a total of {total} dollars. How many adult tickets were sold?"
        eqs, ans = [f"a+c={n}", f"{pa}a+{pc}c={total}"], adults
        val = sp.solve([x + y - n, pa * x + pc * y - total], [x, y])[x]
    elif kind == 'coins':
        dimes, quarters = rng.randint(2, 15), rng.randint(2, 15)
        n, cents = dimes + quarters, 10 * dimes + 25 * quarters
        stmt = f"A jar has {n} coins, all dimes and quarters, worth {cents} cents in total. How many quarters are there?"
        eqs, ans = [f"d+q={n}", f"10d+25q={cents}"], quarters
        val = sp.solve([x + y - n, 10 * x + 25 * y - cents], [x, y])[y]
    elif kind == 'numbers':
        p, q = rng.randint(1, 30), rng.randint(1, 30)
        if p == q:
            return None
        big, small = max(p, q), min(p, q)
        stmt = f"The sum of two numbers is {big + small} and their difference is {big - small}. Find the larger number."
        eqs, ans = [f"a+b={big + small}", f"a-b={big - small}"], big
        val = sp.solve([x + y - (big + small), x - y - (big - small)], [x, y])[x]
    else:
        c1, c2, v1, v2 = rng.choice([10, 20, 30]), rng.choice([50, 60, 80]), rng.randint(1, 8), rng.randint(1, 8)
        tot = v1 + v2
        conc = R(c1 * v1 + c2 * v2, tot)
        stmt = f"A chemist mixes a {c1}% solution with a {c2}% solution to get {tot} liters of a {float(conc):g}% solution. How many liters of the {c2}% solution are used?"
        eqs, ans = [f"a+b={tot}", f"{c1}a+{c2}b={c1 * v1 + c2 * v2}"], v2
        val = sp.solve([x + y - tot, c1 * x + c2 * y - (c1 * v1 + c2 * v2)], [x, y])[y]
    return P(S4, stmt, 'numeric', str(ans), d=2 if kind != 'numbers' else 1,
             hints=["Name the two unknowns and write two equations: one for the count (or amount) and one for the value.",
                    f"The equations are ${eqs[0]}$ and ${eqs[1]}$."],
             sol=[f"Equations: ${eqs[0]}$ and ${eqs[1]}$.", "Solve the first for one unknown and substitute into the second.", f"The requested quantity is ${ans}$."],
             verify={'kind': 'numeric', 'value': str(val)})

def se_count_solutions(rng):
    a, b, c = nz(rng, -4, 4), nz(rng, -4, 4), rng.randint(-6, 6)
    kind = rng.choice(['none', 'one', 'inf'])
    m = rng.choice([2, 3, -1, -2])
    if kind == 'none':
        d, e, f = m * a, m * b, m * c + rng.choice([1, 2, -3])
    elif kind == 'inf':
        d, e, f = m * a, m * b, m * c
    else:
        d, e, f = nz(rng, -4, 4), nz(rng, -4, 4), rng.randint(-6, 6)
        if a * e - b * d == 0:
            return None
    sol = sp.linsolve([a * x + b * y - c, d * x + e * y - f], [x, y])
    code = 0 if sol == sp.S.EmptySet else (2 if any(s.free_symbols for s in list(sol)[0]) else 1)
    opts = [('0', '0'), ('1', '1'), (r'\text{infinitely many}', '2')]
    expl = {0: "the left sides are proportional but the right sides are not, so the lines are parallel and never meet",
            1: "the coefficients are not proportional, so the lines cross at exactly one point",
            2: "the second equation is a multiple of the first, so both describe the same line"}[code]
    return choice(S4, f"How many solutions does the system ${sys_ltx(a, b, c, d, e, f)}$ have?", opts, code, code, d=2, rng=rng,
                  hints=["Compare the ratios of the $x$ coefficients, the $y$ coefficients, and the constants.",
                         "Proportional coefficients mean the lines are parallel (no solution) or identical (infinitely many)."],
                  sol=[f"Compare: the second equation's coefficients are {'' if code == 1 else str(m) + ' times '}{'not proportional to' if code == 1 else ''} the first's.",
                       f"Here {expl}."],
                  extra_verify={'note': 'choices_plain codes: 0 = no solution, 1 = one, 2 = infinitely many'})

def se_combo(rng):
    s = _system(rng)
    if not s:
        return None
    a, b, c, d, e, f, xs, ys = s
    kind = rng.choice(['sum', 'product'])
    val = xs + ys if kind == 'sum' else xs * ys
    return P(S4, f"Solve ${sys_ltx(a, b, c, d, e, f)}$ and enter ${'x + y' if kind == 'sum' else 'xy'}$.", 'numeric', fmt_num(val), d=2,
             hints=["Solve the system fully first.", "Elimination: combine multiples of the equations so one variable cancels."],
             sol=[f"Solving gives $x = {xs}$ and $y = {ys}$.", f"So ${'x + y' if kind == 'sum' else 'xy'} = {val}$."],
             verify={'kind': 'numeric', 'value': str(val)})

def se_parameter(rng):
    a, b, c, f = nz(rng, -4, 4), nz(rng, -4, 4), rng.randint(-6, 6), rng.randint(-6, 6)
    m = rng.choice([2, 3, -2, -1])
    kk = m * a
    e = m * b
    if m * c == f:
        return None
    return P(S4, f"For which value of $k$ does the system ${sys_ltx(a, b, c, 1, e, f).replace('x', 'kx', 1) if False else chr(92) + 'begin{cases} ' + ltx(a * x + b * y) + f' = {c} ' + chr(92) * 2 + f' kx {'+' if e > 0 else '-'} {abs(e)}y = {f} ' + chr(92) + 'end{cases}'}$ have no solution?",
             'numeric', str(kk), d=3,
             hints=["No solution means the two lines are parallel: same slope, different intercepts.", f"The $y$ coefficient ${e}$ is ${m}$ times ${b}$, so $k$ must be ${m}$ times ${a}$."],
             sol=[f"Parallel lines have proportional coefficients: $\\dfrac{{k}}{{{a}}} = \\dfrac{{{e}}}{{{b}}} = {m}$.", f"So $k = {kk}$; the constants ${c}$ and ${f}$ are not in that ratio, so there is no solution."],
             verify={'kind': 'numeric', 'value': f"{a}*{e}/{b}"})

FAM[S4] = [se_solve, se_substitution, se_word, se_count_solutions, se_combo, se_parameter]

# ================================================================ polynomials
S5 = 'polynomials'

def po_binomials(rng):
    a, c = rng.choice([1, 1, 1, 2, 3]), rng.choice([1, 1, 2, 3])
    b, d = nz(rng, -7, 7), nz(rng, -7, 7)
    e = sp.expand((a * x + b) * (c * x + d))
    return P(S5, f"Expand $({lin(a, b)})({lin(c, d)})$.", 'equiv', plain(e), d=1 if a == c == 1 else 2,
             hints=["Multiply every term of the first factor by every term of the second (FOIL).", f"First: ${ltx(a * c * x ** 2)}$; Outer + Inner: ${ltx((a * d + b * c) * x)}$; Last: ${b * d}$."],
             sol=[f"First: ${ltx(a * x)} \\cdot {ltx(c * x)} = {ltx(a * c * x ** 2)}$.", f"Outer and Inner: ${ltx(a * d * x)} + {ltx(b * c * x)} = {ltx((a * d + b * c) * x)}$.", f"Last: ${b} \\cdot {d} = {b * d}$. Total: ${ltx(e)}$."],
             verify={'kind': 'equiv', 'expected': f"({a}*x+({b}))*({c}*x+({d}))"})

def po_special(rng):
    kind = rng.choice(['sq', 'sq', 'diff', 'sqa'])
    a = rng.randint(1, 9)
    if kind == 'sq':
        s = rng.choice([1, -1]); e = sp.expand((x + s * a) ** 2); stmt = f"Expand $({ltx(x + s * a)})^2$."; ex = f"(x+({s * a}))**2"; d = 1
        h = "$(u+v)^2 = u^2 + 2uv + v^2$: do not forget the middle term."
    elif kind == 'diff':
        e = sp.expand((x + a) * (x - a)); stmt = f"Expand $({ltx(x + a)})({ltx(x - a)})$."; ex = f"(x+{a})*(x-{a})"; d = 1
        h = "$(u+v)(u-v) = u^2 - v^2$: the middle terms cancel."
    else:
        c = rng.choice([2, 3, 4]); s = rng.choice([1, -1]); e = sp.expand((c * x + s * a) ** 2); stmt = f"Expand $({ltx(c * x + s * a)})^2$."; ex = f"({c}*x+({s * a}))**2"; d = 2
        h = "$(u+v)^2 = u^2 + 2uv + v^2$ with $u$ the whole first term."
    return P(S5, stmt, 'equiv', plain(e), d=d, hints=[h, "Write the factor twice and multiply term by term if you are unsure."],
             sol=["Use the special product pattern (or FOIL).", f"Result: ${ltx(e)}$."], verify={'kind': 'equiv', 'expected': ex})

def po_add_sub(rng):
    p1 = rng.randint(1, 5) * x ** 2 + rng.randint(-6, 6) * x + rng.randint(-6, 6)
    p2 = rng.randint(-4, 4) * x ** 2 + nz(rng, -6, 6) * x + nz(rng, -6, 6)
    sub = rng.random() < 0.6
    e = sp.expand(p1 - p2 if sub else p1 + p2)
    op = '-' if sub else '+'
    return P(S5, f"Simplify $({ltx(p1)}) {op} ({ltx(p2)})$.", 'equiv', plain(e), d=1,
             hints=["Combine like terms: the $x^2$ terms together, the $x$ terms together, the constants together.",
                    "When subtracting, change the sign of every term in the second polynomial first." if sub else "Line up the terms by their power of $x$."],
             sol=[(f"Distribute the minus sign: ${ltx(p1)} {ltx(-p2) if str(ltx(-p2)).startswith('-') else '+ ' + ltx(-p2)}$." if sub else f"Remove the parentheses: ${ltx(p1)} + {ltx(p2)}$."),
                  f"Combine like terms: ${ltx(e)}$."],
             verify={'kind': 'equiv', 'expected': f"({p1}) {op} ({p2})"})

def po_monomial(rng):
    c, m = rng.choice([2, 3, -2, 4, -3, 5]), rng.randint(1, 3)
    p = rng.randint(1, 4) * x ** 2 + nz(rng, -6, 6) * x + nz(rng, -6, 6)
    e = sp.expand(c * x ** m * p)
    return P(S5, f"Expand ${ltx(c * x ** m)}({ltx(p)})$.", 'equiv', plain(e), d=1,
             hints=["Distribute the monomial to each term.", "Multiply coefficients and add the exponents of $x$."],
             sol=[f"Multiply each term by ${ltx(c * x ** m)}$.", f"Result: ${ltx(e)}$."], verify={'kind': 'equiv', 'expected': f"{c}*x**{m}*({p})"})

def po_cubic(rng):
    kind = rng.choice(['tri', 'cube'])
    a = nz(rng, -5, 5)
    if kind == 'tri':
        b, c = nz(rng, -5, 5), nz(rng, -6, 6)
        q = x ** 2 + b * x + c
        e = sp.expand((x + a) * q)
        stmt, ex = f"Expand $({ltx(x + a)})({ltx(q)})$.", f"(x+({a}))*(x**2+({b})*x+({c}))"
        h2 = "Each of the two terms in the first factor multiplies all three terms in the second: six products."
    else:
        e = sp.expand((x + a) ** 3)
        stmt, ex = f"Expand $({ltx(x + a)})^3$.", f"(x+({a}))**3"
        h2 = f"First expand $({ltx(x + a)})^2 = {ltx(sp.expand((x + a) ** 2))}$, then multiply by $({ltx(x + a)})$ once more."
    return P(S5, stmt, 'equiv', plain(e), d=3, hints=["Multiply term by term, then combine like terms carefully.", h2],
             sol=["Multiply every term of the first factor by every term of the second.", "Collect like powers of $x$.", f"Result: ${ltx(e)}$."],
             verify={'kind': 'equiv', 'expected': ex})

def po_degree(rng):
    m, n = rng.randint(1, 3), rng.randint(1, 3)
    p = (rng.choice([1, 2, 3]) * x ** m + nz(rng, -5, 5)) * (x ** n + nz(rng, -5, 5) * x + nz(rng, -5, 5))
    p1, p2 = p.args[0], p.args[1]
    deg = sp.degree(sp.expand(p), x)
    return P(S5, f"What is the degree of the polynomial $({ltx(p1)})({ltx(p2)})$?", 'numeric', str(deg), d=1 if m + n <= 3 else 2,
             hints=["The degree is the highest power of $x$ after expanding.", "You do not need to expand everything: multiply only the highest-power terms."],
             sol=[f"The highest-power terms are $x^{{{sp.degree(p1, x)}}}$ and $x^{{{sp.degree(p2, x)}}}$.", f"Their product has degree ${sp.degree(p1, x)} + {sp.degree(p2, x)} = {deg}$."],
             verify={'kind': 'numeric', 'value': f"degree(({p1})*({p2}), x)"})

def po_evaluate(rng):
    p = rng.choice([1, 2, -1, 3]) * x ** 3 + rng.randint(-4, 4) * x ** 2 + nz(rng, -6, 6) * x + rng.randint(-9, 9)
    a = rng.choice([-3, -2, -1, 2, 3])
    val = p.subs(x, a)
    return P(S5, f"If $p(x) = {ltx(p)}$, find $p({a})$.", 'numeric', str(val), d=1,
             hints=[f"Replace every $x$ with ${a}$, keeping the parentheses.", "Compute the powers first, then multiply, then add."],
             sol=[f"$p({a}) = {ltx(p).replace('x', f'({a})')}$.", f"$= {val}$."], verify={'kind': 'evaluate', 'expr': str(p), 'at': str(a)})

def po_choice_square(rng):
    a = rng.randint(1, 8); s = rng.choice([1, -1])
    e = sp.expand((x + s * a) ** 2)
    opts = [(ltx(e), plain(e)), (ltx(x ** 2 + a * a), plain(x ** 2 + a * a)), (ltx(x ** 2 + s * a * x + a * a), plain(x ** 2 + s * a * x + a * a)), (ltx(x ** 2 - s * 2 * a * x + a * a), plain(x ** 2 - s * 2 * a * x + a * a))]
    return choice(S5, f"Which expression equals $({ltx(x + s * a)})^2$?", opts, 0, f"(x+({s * a}))**2", d=1, rng=rng,
                  hints=["Squaring a binomial produces three terms, not two.", f"$(u+v)^2 = u^2 + 2uv + v^2$ with $u = x$, $v = {s * a}$."],
                  sol=[f"$({ltx(x + s * a)})^2 = x^2 + 2({s * a})x + ({s * a})^2$.", f"$= {ltx(e)}$."])

def po_coefficient(rng):
    a, b, c, d = nz(rng, -5, 5), nz(rng, -5, 5), rng.choice([1, 2, 3]), nz(rng, -5, 5)
    p = (x + a) * (c * x ** 2 + b * x + d)
    kk = rng.choice([1, 2])
    e = sp.expand(p)
    coef = sp.Poly(e, x).coeff_monomial(x ** kk)
    return P(S5, f"What is the coefficient of $x^{{{kk}}}$" + ("" if kk > 1 else " (the $x$ term)") + f" in the expansion of $({ltx(x + a)})({ltx(c * x ** 2 + b * x + d)})$?",
             'numeric', str(coef), d=2,
             hints=[f"Only two products contribute to $x^{{{kk}}}$: pick a term from each factor whose exponents add to ${kk}$.", "You can expand fully and read it off, but it is faster to collect just the needed products."],
             sol=[f"Full expansion: ${ltx(e)}$.", f"The coefficient of $x^{{{kk}}}$ is ${coef}$."],
             verify={'kind': 'numeric', 'value': f"Poly(expand((x+({a}))*({c}*x**2+({b})*x+({d}))), x).coeff_monomial(x**{kk})"})

def po_leading_constant(rng):
    a, b, c, d = rng.choice([2, 3, -2, 4]), nz(rng, -5, 5), rng.choice([1, 2, 3, -1]), nz(rng, -5, 5)
    p = (a * x ** 2 + b) * (c * x + d)
    which = rng.choice(['leading', 'constant'])
    e = sp.expand(p)
    val = sp.LC(e, x) if which == 'leading' else e.subs(x, 0)
    return P(S5, f"Find the {which} {'coefficient' if which == 'leading' else 'term'} of $({ltx(a * x ** 2 + b)})({ltx(c * x + d)})$ after expanding.",
             'numeric', str(val), d=1,
             hints=["The leading coefficient comes from multiplying the highest-power terms." if which == 'leading' else "The constant term comes from multiplying the constants.",
                    f"${a} \\cdot {c}$" if which == 'leading' else f"${b} \\cdot {d}$"],
             sol=[f"Expansion: ${ltx(e)}$.", f"The {which} {'coefficient' if which == 'leading' else 'term'} is ${val}$."],
             verify={'kind': 'numeric', 'value': (f"LC(expand(({a}*x**2+({b}))*({c}*x+({d}))), x)" if which == 'leading' else f"expand(({a}*x**2+({b}))*({c}*x+({d}))).subs(x,0)")})

FAM[S5] = [po_binomials, po_special, po_add_sub, po_monomial, po_cubic, po_degree, po_evaluate, po_choice_square, po_coefficient, po_leading_constant]

# ================================================================ factoring-and-quadratics
S6 = 'factoring-and-quadratics'

def fq_factor_monic(rng):
    p, q = nz(rng, -8, 8), nz(rng, -8, 8)
    if p == q:
        return None
    e = sp.expand((x + p) * (x + q))
    return P(S6, f"Factor ${ltx(e)}$.", 'equiv', plain(sp.factor(e)), d=1,
             hints=[f"Look for two numbers that multiply to ${p * q}$ and add to ${p + q}$.", f"Try ${p}$ and ${q}$."],
             sol=[f"We need two numbers with product ${p * q}$ and sum ${p + q}$: they are ${p}$ and ${q}$.", f"So ${ltx(e)} = ({ltx(x + p)})({ltx(x + q)})$."],
             verify={'kind': 'equiv', 'expected': str(e)})

def fq_factor_lead(rng):
    a, c = rng.choice([2, 3, 5]), rng.choice([1, 2, 3])
    b, d = nz(rng, -5, 5), nz(rng, -5, 5)
    e = sp.expand((a * x + b) * (c * x + d))
    f = sp.factor(e)
    if f == e or sp.gcd(a * c, sp.gcd(a * d + b * c, b * d)) != 1:
        return None
    return P(S6, f"Factor ${ltx(e)}$.", 'equiv', plain(f), d=2 if c == 1 else 3,
             hints=[f"The leading coefficient is ${a * c}$, so the factors look like $(\\square x + \\square)(\\square x + \\square)$.",
                    f"Find two numbers with product ${a * c * b * d}$ and sum ${a * d + b * c}$, then split the middle term and factor by grouping."],
             sol=[f"Product of leading coefficient and constant: ${a * c} \\cdot {b * d} = {a * c * b * d}$; we need a pair summing to ${a * d + b * c}$: ${a * d}$ and ${b * c}$.",
                  f"Split the middle term: ${ltx(a * c * x ** 2)} + {ltx(a * d * x)} + {ltx(b * c * x)} + {b * d}$, then group.", f"Result: ${ltx(f)}$."],
             verify={'kind': 'equiv', 'expected': str(e)})

def fq_gcf_dos(rng):
    kind = rng.choice(['gcf', 'dos', 'dos2'])
    if kind == 'gcf':
        g, m, b = rng.choice([2, 3, 4, 5, 6]), rng.randint(1, 2), nz(rng, -7, 7)
        e = sp.expand(g * x ** m * (x + b)); f = sp.factor(e); d = 1
        h = [f"Every term is divisible by ${g}$ and by $x$.", "Factor out the greatest common factor, then check by distributing."]
    elif kind == 'dos':
        a = rng.choice([2, 3, 4, 5, 6, 7, 8, 9, 10]); e = x ** 2 - a * a; f = sp.factor(e); d = 1
        h = [f"This is a difference of squares: $x^2 - {a}^2$.", "$u^2 - v^2 = (u - v)(u + v)$."]
    else:
        a, b = rng.choice([2, 3, 4, 5]), rng.choice([1, 2, 3, 5, 7]); e = a * a * x ** 2 - b * b; f = sp.factor(e); d = 2
        h = [f"Both terms are perfect squares: $({a}x)^2$ and ${b}^2$.", "$u^2 - v^2 = (u - v)(u + v)$."]
    return P(S6, f"Factor completely: ${ltx(e)}$.", 'equiv', plain(f), d=d, hints=h,
             sol=["Identify the pattern (common factor or difference of squares).", f"${ltx(e)} = {ltx(f)}$."], verify={'kind': 'equiv', 'expected': str(e)})

def fq_solve_factor(rng):
    p, q = nz(rng, -7, 7), nz(rng, -7, 7)
    if p == q:
        return None
    e = sp.expand((x - p) * (x - q))
    big = max(p, q)
    return P(S6, f"Solve ${ltx(e)} = 0$. Enter the larger solution.", 'numeric', str(big), d=2,
             hints=["Factor the left side, then set each factor equal to zero.", f"Two numbers with product ${p * q}$ and sum ${-(p + q)}$: ${-p}$ and ${-q}$."],
             sol=[f"${ltx(e)} = ({ltx(x - p)})({ltx(x - q)})$.", f"So $x = {p}$ or $x = {q}$.", f"The larger solution is ${big}$."],
             verify={'kind': 'solve', 'lhs': str(e), 'rhs': '0', 'pick': str(big)})

def fq_quadratic_formula(rng):
    b, c = rng.randint(-7, 7), rng.randint(-9, 9)
    D = b * b - 4 * c
    if D <= 0 or sp.sqrt(D).is_Integer:
        return None
    e = x ** 2 + b * x + c
    root = (-b + sqrt(D)) / 2
    return P(S6, f"Use the quadratic formula to solve ${ltx(e)} = 0$. Enter the larger solution in exact form.", 'numeric', plain(root), d=3,
             hints=["$x = \\dfrac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$ with $a = 1$.", f"The discriminant is ${b}^2 - 4({c}) = {D}$."],
             sol=[f"$a = 1$, $b = {b}$, $c = {c}$: discriminant $= {b * b} - ({4 * c}) = {D}$.", f"$x = \\dfrac{{{-b} \\pm \\sqrt{{{D}}}}}{{2}}$.",
                  f"The larger one uses the plus sign: $x = {ltx(root)}$."],
             verify={'kind': 'solve', 'lhs': str(e), 'rhs': '0', 'pick': str(root)})

def fq_complete_square(rng):
    h, kk = nz(rng, -6, 6), rng.randint(-9, 9)
    e = sp.expand((x + h) ** 2 + kk)
    ans = (x + h) ** 2 + kk
    return P(S6, f"Complete the square: write ${ltx(e)}$ in the form $(x + h)^2 + k$.", 'equiv', plain(ans), d=2,
             hints=["Take half the coefficient of $x$ and square it.", f"Half of ${2 * h}$ is ${h}$; ${h}^2 = {h * h}$. Add and subtract it."],
             sol=[f"${ltx(e)} = (x^2 + {2 * h}x + {h * h}) + ({kk})$.", f"$= ({ltx(x + h)})^2 + ({kk})$."],
             verify={'kind': 'equiv', 'expected': str(e)})

def fq_vertex(rng):
    a, b, c = rng.choice([1, 2, -1, 3, -2]), nz(rng, -8, 8), rng.randint(-6, 6)
    q = a * x ** 2 + b * x + c
    xv = sp.solve(sp.diff(q, x), x)[0]
    return P(S6, f"Find the $x$-coordinate of the vertex of the parabola $y = {ltx(q)}$.", 'numeric', fmt_num(xv), d=2,
             hints=["The vertex sits on the axis of symmetry, halfway between the roots.", "For $y = ax^2 + bx + c$ the axis is $x = -\\dfrac{b}{2a}$."],
             sol=[f"$x = -\\dfrac{{b}}{{2a}} = -\\dfrac{{{b}}}{{2({a})}}$.", f"$x = {num(xv)}$."],
             verify={'kind': 'numeric', 'value': str(xv)})

def fq_discriminant_count(rng):
    a, b, c = rng.choice([1, 2, -1, 3]), rng.randint(-6, 6), rng.randint(-6, 6)
    q = a * x ** 2 + b * x + c
    n = len(sp.real_roots(sp.Poly(q, x)))
    D = b * b - 4 * a * c
    opts = [('0', '0'), ('1', '1'), ('2', '2')]
    return choice(S6, f"How many real solutions does ${ltx(q)} = 0$ have?", opts, n, n, d=2, rng=rng,
                  hints=["Compute the discriminant $b^2 - 4ac$.", "Positive: two real solutions; zero: one; negative: none."],
                  sol=[f"$b^2 - 4ac = ({b})^2 - 4({a})({c}) = {D}$.", f"The discriminant is {'positive' if D > 0 else ('zero' if D == 0 else 'negative')}, so there {'are' if n != 1 else 'is'} ${n}$ real solution{'s' if n != 1 else ''}."])

def fq_word_rectangle(rng):
    w, a = rng.randint(2, 9), rng.randint(1, 6)
    A = w * (w + a)
    return P(S6, f"A rectangle is {a} cm longer than it is wide and has area {A} square centimeters. Find its width in cm.", 'numeric', str(w), d=2,
             hints=[f"If the width is $w$, the length is $w + {a}$ and the area is $w(w + {a})$.", f"Solve $w^2 + {a}w - {A} = 0$ by factoring; keep the positive root."],
             sol=[f"$w(w + {a}) = {A}$ gives $w^2 + {a}w - {A} = 0$.", f"Factor: $(w - {w})(w + {w + a}) = 0$.", f"Width must be positive: $w = {w}$."],
             verify={'kind': 'solve', 'lhs': f"x**2+{a}*x-{A}", 'rhs': '0', 'pick': str(w)})

def fq_which_factor(rng):
    p, q = nz(rng, -7, 7), nz(rng, -7, 7)
    if p == q:
        return None
    e = sp.expand((x + p) * (x + q))
    good = x + p
    distract = [x - p, x + 2 * q, x - q, x + p + q, x + p * q, x + 1, x - 1]
    opts = [(ltx(good), plain(good))]
    for dfac in distract:
        if sp.rem(e, dfac, x) != 0 and plain(dfac) not in [o[1] for o in opts]:
            opts.append((ltx(dfac), plain(dfac)))
        if len(opts) == 4:
            break
    if len(opts) < 4:
        return None
    return choice(S6, f"Which of these is a factor of ${ltx(e)}$?", opts, 0, str(good), d=1, rng=rng,
                  hints=["A factor $x - r$ means $r$ is a root; test each candidate's root in the polynomial.", f"Or factor directly: product ${p * q}$, sum ${p + q}$."],
                  sol=[f"${ltx(e)} = ({ltx(x + p)})({ltx(x + q)})$.", f"So ${ltx(good)}$ is a factor."])

def fq_discriminant_value(rng):
    a, b, c = rng.choice([1, 2, 3, -1, -2]), nz(rng, -7, 7), nz(rng, -7, 7)
    q = a * x ** 2 + b * x + c
    return P(S6, f"Compute the discriminant $b^2 - 4ac$ of ${ltx(q)}$.", 'numeric', str(b * b - 4 * a * c), d=1,
             hints=["Identify $a$, $b$, $c$ from $ax^2 + bx + c$, including signs.", f"$a = {a}$, $b = {b}$, $c = {c}$."],
             sol=[f"$b^2 - 4ac = ({b})^2 - 4({a})({c})$.", f"$= {b * b} - ({4 * a * c}) = {b * b - 4 * a * c}$."],
             verify={'kind': 'numeric', 'value': f"discriminant({q}, x)"})

def fq_vieta(rng):
    p, q = nz(rng, -6, 6), nz(rng, -6, 6)
    a = rng.choice([1, 1, 2])
    e = sp.expand(a * (x - p) * (x - q))
    kind = rng.choice(['sum', 'product'])
    roots = sp.solve(e, x)
    val = sum(roots) if kind == 'sum' else sp.Mul(*roots)
    if p == q:
        val = 2 * p if kind == 'sum' else p * p
    return P(S6, f"Find the {kind} of the solutions of ${ltx(e)} = 0$.", 'numeric', fmt_num(val), d=3,
             hints=["You can solve the equation, or use the shortcut: for $ax^2+bx+c=0$ the roots sum to $-b/a$ and multiply to $c/a$.", f"Here $a = {a}$."],
             sol=[f"Factor: ${ltx(e)} = {ltx(sp.factor(e))}$, so the roots are ${p}$ and ${q}$.", f"Their {kind} is ${num(val)}$."],
             verify={'kind': 'numeric', 'value': str(val)})

FAM[S6] = [fq_factor_monic, fq_factor_lead, fq_gcf_dos, fq_solve_factor, fq_quadratic_formula, fq_complete_square, fq_vertex, fq_discriminant_count, fq_word_rectangle, fq_which_factor, fq_discriminant_value, fq_vieta]

# ================================================================ rational-expressions
S7 = 'rational-expressions'

def re_dos(rng):
    a = rng.randint(1, 9)
    s = rng.choice([1, -1])
    num_, den = x ** 2 - a * a, x - s * a
    ans = sp.cancel(num_ / den)
    return P(S7, f"Simplify $\\dfrac{{{ltx(num_)}}}{{{ltx(den)}}}$ (assume the denominator is not zero).", 'equiv', plain(ans), d=1,
             hints=["Factor the numerator as a difference of squares.", f"$x^2 - {a * a} = (x - {a})(x + {a})$; cancel the common factor."],
             sol=[f"$x^2 - {a * a} = (x - {a})(x + {a})$.", f"Cancel $({ltx(den)})$: the result is ${ltx(ans)}$."],
             verify={'kind': 'equiv', 'expected': f"({num_})/({den})"}, domain=(-3, 3))

def re_cancel(rng):
    r, p, q = nz(rng, -5, 5), nz(rng, -5, 5), nz(rng, -5, 5)
    if p == q:
        return None
    num_, den = sp.expand((x + r) * (x + p)), sp.expand((x + r) * (x + q))
    ans = sp.cancel(num_ / den)
    return P(S7, f"Simplify $\\dfrac{{{ltx(num_)}}}{{{ltx(den)}}}$.", 'equiv', plain(ans), d=2,
             hints=["Factor the top and the bottom separately.", f"Both contain the factor $({ltx(x + r)})$."],
             sol=[f"Numerator: $({ltx(x + r)})({ltx(x + p)})$. Denominator: $({ltx(x + r)})({ltx(x + q)})$.", f"Cancel the common factor: ${ltx(ans)}$."],
             verify={'kind': 'equiv', 'expected': f"({num_})/({den})"})

def re_add(rng):
    a, b, c = nz(rng, -5, 5), nz(rng, -5, 5), nz(rng, -6, 6)
    e = a / x + b / (x + c)
    ans = sp.together(e)
    return P(S7, f"Combine into a single fraction: $\\dfrac{{{a}}}{{x}} + \\dfrac{{{b}}}{{{ltx(x + c)}}}$.", 'equiv', plain(ans), d=2,
             hints=["The common denominator is the product of the two denominators.", f"Multiply the first fraction by $\\dfrac{{{ltx(x + c)}}}{{{ltx(x + c)}}}$ and the second by $\\dfrac{{x}}{{x}}$."],
             sol=[f"$\\dfrac{{{a}({ltx(x + c)})}}{{x({ltx(x + c)})}} + \\dfrac{{{b}x}}{{x({ltx(x + c)})}}$.", f"Add the numerators: $\\dfrac{{{ltx(sp.expand(a * (x + c) + b * x))}}}{{x({ltx(x + c)})}}$."],
             verify={'kind': 'equiv', 'expected': f"{a}/x+{b}/(x+({c}))"})

def re_subtract(rng):
    a, b = nz(rng, -5, 5), nz(rng, -5, 5)
    if a == b:
        return None
    e = 1 / (x - a) - 1 / (x - b)
    ans = sp.cancel(sp.together(e))
    return P(S7, f"Simplify $\\dfrac{{1}}{{{ltx(x - a)}}} - \\dfrac{{1}}{{{ltx(x - b)}}}$ into one fraction.", 'equiv', plain(ans), d=2,
             hints=["Use the product of the denominators as the common denominator.", "Subtract the new numerators carefully (watch the signs)."],
             sol=[f"$\\dfrac{{({ltx(x - b)}) - ({ltx(x - a)})}}{{({ltx(x - a)})({ltx(x - b)})}}$.", f"Numerator simplifies to ${a - b}$: result ${ltx(ans)}$."],
             verify={'kind': 'equiv', 'expected': f"1/(x-({a}))-1/(x-({b}))"})

def re_divide(rng):
    a, b, c = nz(rng, -5, 5), nz(rng, -5, 5), nz(rng, -5, 5)
    if len({a, b, c}) < 3:
        return None
    e = ((x + a) / (x + b)) / ((x + a) / (x + c))
    ans = sp.cancel(e)
    mul = rng.random() < 0.4
    if mul:
        e = ((x + a) / (x + b)) * ((x + b) / (x + c)); ans = sp.cancel(e)
        stmt = f"Multiply and simplify: $\\dfrac{{{ltx(x + a)}}}{{{ltx(x + b)}}} \\cdot \\dfrac{{{ltx(x + b)}}}{{{ltx(x + c)}}}$."
        ex = f"((x+({a}))/(x+({b})))*((x+({b}))/(x+({c})))"
        h = ["Multiply straight across, then cancel any factor that appears on top and bottom.", f"The factor $({ltx(x + b)})$ cancels."]
    else:
        stmt = f"Divide and simplify: $\\dfrac{{{ltx(x + a)}}}{{{ltx(x + b)}}} \\div \\dfrac{{{ltx(x + a)}}}{{{ltx(x + c)}}}$."
        ex = f"((x+({a}))/(x+({b})))/((x+({a}))/(x+({c})))"
        h = ["Dividing by a fraction is multiplying by its reciprocal.", f"After flipping, the factor $({ltx(x + a)})$ cancels."]
    return P(S7, stmt, 'equiv', plain(ans), d=2, hints=h, sol=["Flip the second fraction if dividing, then multiply across." if not mul else "Multiply numerators and denominators.",
                                                              f"Cancel the common factor: ${ltx(ans)}$."], verify={'kind': 'equiv', 'expected': ex})

def re_undefined(rng):
    a, b = nz(rng, -7, 7), nz(rng, -7, 7)
    if a == -b:
        return None
    den = sp.expand((x - a) * (x + b))
    vals = sorted([a, -b])
    kind = rng.choice(['larger', 'sum'])
    val = vals[1] if kind == 'larger' else vals[0] + vals[1]
    n_ = rng.choice([x + 1, 2 * x, x - 3, 5])
    stmt = f"For which values of $x$ is $\\dfrac{{{ltx(n_)}}}{{{ltx(den)}}}$ undefined? " + ("Enter the larger value." if kind == 'larger' else "Enter the sum of those values.")
    return P(S7, stmt, 'numeric', str(val), d=1 if kind == 'larger' else 2,
             hints=["A fraction is undefined where its denominator is zero.", f"Factor the denominator: $({ltx(x - a)})({ltx(x + b)})$."],
             sol=[f"Set ${ltx(den)} = 0$: $({ltx(x - a)})({ltx(x + b)}) = 0$.", f"So $x = {vals[0]}$ or $x = {vals[1]}$." + (f" The larger is ${val}$." if kind == 'larger' else f" Their sum is ${val}$.")],
             verify=({'kind': 'solve', 'lhs': str(den), 'rhs': '0', 'pick': str(val)} if kind == 'larger' else {'kind': 'numeric', 'value': f"sum(solveset(Eq({den},0),x,Reals))"}))

def re_domain(rng):
    a, b = rng.randint(-5, 6), rng.randint(-9, -1)
    if b >= a:
        return None
    if rng.random() < 0.5:
        b = a + rng.randint(-8, -1)
    cond = f"x-({a})>=0"
    I = sp.sympify(cond).as_set()
    return P(S7, f"Find the domain of $f(x) = \\dfrac{{\\sqrt{{{ltx(x - a)}}}}}{{{ltx(x - b)}}}$ in interval notation.", 'interval', ival(I), d=2,
             hints=["Two restrictions: the square root needs a non-negative inside, and the denominator cannot be zero.", f"The root needs $x \\ge {a}$; the denominator is zero at $x = {b}$. Is that excluded already?"],
             sol=[f"Square root: ${ltx(x - a)} \\ge 0$, so $x \\ge {a}$.", f"Denominator: $x \\ne {b}$, but ${b} < {a}$ so it is already outside the allowed set.", f"Domain: ${ival_ltx(I)}$."],
             verify={'kind': 'interval', 'expected': cond})

def re_evaluate(rng):
    a, b, c = nz(rng, -5, 5), nz(rng, -5, 5), nz(rng, -5, 5)
    e = (a * x + b) / (x ** 2 + c)
    at = rng.choice([-3, -2, -1, 1, 2, 3])
    val = e.subs(x, at)
    return P(S7, f"If $f(x) = \\dfrac{{{ltx(a * x + b)}}}{{{ltx(x ** 2 + c)}}}$, find $f({at})$. Give an exact fraction.", 'numeric', fmt_num(val), d=1,
             hints=[f"Substitute $x = {at}$ into numerator and denominator separately.", "Reduce the fraction if possible."],
             sol=[f"Numerator: ${a}({at}) + ({b}) = {a * at + b}$. Denominator: $({at})^2 + ({c}) = {at * at + c}$.", f"$f({at}) = {num(val)}$."],
             verify={'kind': 'evaluate', 'expr': str(e), 'at': str(at)})

def re_complex(rng):
    a = rng.choice([1, 2, 3, 4, 5])
    e = (1 + a / x) / (1 - a * a / x ** 2)
    ans = sp.cancel(e)
    return P(S7, f"Simplify the complex fraction $\\dfrac{{1 + \\dfrac{{{a}}}{{x}}}}{{1 - \\dfrac{{{a * a}}}{{x^2}}}}$.", 'equiv', plain(ans), d=3,
             hints=["Multiply numerator and denominator by $x^2$ to clear the inner fractions.", f"That gives $\\dfrac{{x^2 + {a}x}}{{x^2 - {a * a}}}$; now factor and cancel."],
             sol=[f"Multiply top and bottom by $x^2$: $\\dfrac{{x^2 + {a}x}}{{x^2 - {a * a}}}$.", f"Factor: $\\dfrac{{x(x + {a})}}{{(x - {a})(x + {a})}}$.", f"Cancel: ${ltx(ans)}$."],
             verify={'kind': 'equiv', 'expected': f"(1+{a}/x)/(1-{a * a}/x**2)"})

def re_choice_undefined(rng):
    r = nz(rng, -6, 6)
    sq = rng.random() < 0.4
    den = (x - r) ** 2 if sq else x - r
    n_ = rng.choice([x + 2, 3 * x, x ** 2 + 1, 4])
    opts = [(str(r), str(r)), (str(-r), str(-r)), (str(0), '0'), (str(r + 1), str(r + 1))]
    if 0 in (r, -r, r + 1) or r + 1 == -r:
        return None
    return choice(S7, f"Which value of $x$ makes $\\dfrac{{{ltx(n_)}}}{{{ltx(den)}}}$ undefined?", opts, 0, str(r), d=1, rng=rng,
                  hints=["Division by zero is undefined; look at the denominator only.", f"Solve ${ltx(den)} = 0$."],
                  sol=[f"The denominator ${ltx(den)}$ is zero exactly when $x = {r}$.", "The numerator does not matter for where the expression is undefined."])

def re_cancel_monomial(rng):
    a, m = nz(rng, -6, 6), rng.choice([1, 2])
    num_ = sp.expand(x ** (m + 1) - a * x ** m)
    ans = sp.cancel(num_ / x ** m)
    return P(S7, f"Simplify $\\dfrac{{{ltx(num_)}}}{{x^{{{m}}}}}$ for $x \\ne 0$.", 'equiv', plain(ans), d=1,
             hints=["Factor the greatest common power of $x$ out of the numerator.", f"The numerator is $x^{{{m}}}({ltx(x - a)})$."],
             sol=[f"${ltx(num_)} = x^{{{m}}}({ltx(x - a)})$.", f"Cancel $x^{{{m}}}$: ${ltx(ans)}$."],
             verify={'kind': 'equiv', 'expected': f"({num_})/x**{m}"})

FAM[S7] = [re_dos, re_cancel, re_add, re_subtract, re_divide, re_undefined, re_domain, re_evaluate, re_complex, re_choice_undefined, re_cancel_monomial]

# ================================================================ function-notation
S8 = 'function-notation'

def _quad(rng):
    return rng.choice([1, 2, -1, 3]) * x ** 2 + rng.randint(-5, 5) * x + rng.randint(-6, 6)

def fn_evaluate(rng):
    kind = rng.choice(['quad', 'rational', 'abs', 'root'])
    if kind == 'quad':
        f = _quad(rng); at = rng.choice([-3, -2, -1, 0, 2, 3, 4]); d = 1
    elif kind == 'rational':
        f = (x + nz(rng, -5, 5)) / (x - nz(rng, -5, 5)); at = rng.choice([-3, -2, 0, 2, 3, 5]); d = 2
        if f.subs(x, at) in (sp.zoo, sp.nan):
            return None
    elif kind == 'abs':
        f = sp.Abs(rng.choice([2, 3]) * x - rng.randint(1, 9)) - rng.randint(0, 5); at = rng.choice([-2, -1, 0, 1, 2]); d = 1
    else:
        c = rng.choice([1, 4, 9, 16]); f = sqrt(x + c) + rng.randint(-3, 3) * x; at = rng.choice([0, 5, 12, 20]) if c != 1 else rng.choice([0, 3, 8, 15]); d = 2
        if not f.subs(x, at).is_Integer:
            return None
    val = f.subs(x, at)
    return P(S8, f"Let $f(x) = {ltx(f)}$. Find $f({at})$.", 'numeric', fmt_num(val), d=d,
             hints=[f"Replace every $x$ in the formula with ${at}$, keeping parentheses around negatives.", "Work the operations in order: powers, then products and quotients, then sums."],
             sol=[f"$f({at}) = {ltx(f).replace('x', f'({at})')}$.", f"$= {num(val)}$."],
             verify={'kind': 'evaluate', 'expr': str(f), 'at': str(at)})

def fn_transform_input(rng):
    f = _quad(rng)
    sub = rng.choice([x + 1, x - 2, 2 * x, -x, x + 3, 3 * x])
    g = f.subs(x, sub)
    e = sp.expand(g)
    return P(S8, f"If $f(x) = {ltx(f)}$, find and expand $f({ltx(sub)})$.", 'equiv', plain(e), d=2,
             hints=[f"Every $x$ in the formula becomes $({ltx(sub)})$.", "Then expand the squared term and collect like terms."],
             sol=[f"$f({ltx(sub)}) = {ltx(g)}$.", f"Expand: ${ltx(e)}$."],
             verify={'kind': 'equiv', 'expected': str(g)})

def fn_compose(rng):
    f = rng.choice([x ** 2, x ** 2 + nz(rng, -4, 4), 2 * x + rng.randint(-5, 5), 3 * x - 1, x ** 2 - x])
    g = rng.choice([x + nz(rng, -5, 5), 2 * x, 1 - x, 3 * x + 2, x - 4])
    outer_f = rng.random() < 0.5
    comp = f.subs(x, g) if outer_f else g.subs(x, f)
    e = sp.expand(comp)
    name = "f(g(x))" if outer_f else "g(f(x))"
    return P(S8, f"Let $f(x) = {ltx(f)}$ and $g(x) = {ltx(g)}$. Find ${name}$ and expand.", 'equiv', plain(e), d=2 if sp.degree(e, x) <= 1 else 3,
             hints=[f"${name}$ means: apply the inner function first, then feed its output into the outer one.",
                    f"Replace $x$ in ${'f' if outer_f else 'g'}$ with $({ltx(g if outer_f else f)})$."],
             sol=[f"${name} = {ltx(comp)}$.", f"Expand: ${ltx(e)}$."],
             verify={'kind': 'equiv', 'expected': str(comp)})

def fn_domain_root(rng):
    a, b = rng.choice([1, 2, 3, -1, -2]), rng.randint(-8, 8)
    cond = f"{a}*x+({b})>=0"
    I = sp.sympify(cond).as_set()
    return P(S8, f"Find the domain of $f(x) = \\sqrt{{{lin(a, b)}}}$ in interval notation.", 'interval', ival(I), d=1 if a > 0 else 2,
             hints=["The expression under a square root must be $\\ge 0$.", f"Solve ${lin(a, b)} \\ge 0$." + (" Dividing by a negative flips the inequality." if a < 0 else "")],
             sol=[f"Require ${lin(a, b)} \\ge 0$.", f"Solve: $x {'\\ge' if a > 0 else '\\le'} {num(R(-b, a))}$.", f"Domain: ${ival_ltx(I)}$."],
             verify={'kind': 'interval', 'expected': cond})

def fn_domain_root_den(rng):
    a = rng.randint(-6, 8)
    cond = f"{a}-x>0"
    I = sp.sympify(cond).as_set()
    return P(S8, f"Find the domain of $g(x) = \\dfrac{{1}}{{\\sqrt{{{ltx(a - x)}}}}}$ in interval notation.", 'interval', ival(I), d=2,
             hints=["The inside of the root must be positive here: zero would put a $0$ in the denominator.", f"Solve ${ltx(a - x)} > 0$."],
             sol=[f"Need ${ltx(a - x)} > 0$ (strict, because of the denominator).", f"So $x < {a}$: domain ${ival_ltx(I)}$."],
             verify={'kind': 'interval', 'expected': cond})

def fn_avg_rate(rng):
    f = rng.choice([_quad(rng), x ** 3 - 2 * x, 2 ** x, x ** 2 + 1])
    a, b = sorted(rng.sample([-2, -1, 0, 1, 2, 3, 4], 2))
    val = (f.subs(x, b) - f.subs(x, a)) / (b - a)
    return P(S8, f"For $f(x) = {ltx(f)}$, find the average rate of change of $f$ from $x = {a}$ to $x = {b}$.", 'numeric', fmt_num(val), d=2,
             hints=["Average rate of change is the slope between the two points on the graph.", f"Compute $\\dfrac{{f({b}) - f({a})}}{{{b} - ({a})}}$."],
             sol=[f"$f({b}) = {f.subs(x, b)}$ and $f({a}) = {f.subs(x, a)}$.", f"Rate $= \\dfrac{{{f.subs(x, b)} - ({f.subs(x, a)})}}{{{b - a}}} = {num(val)}$."],
             verify={'kind': 'numeric', 'value': f"(({f}).subs(x,{b})-({f}).subs(x,{a}))/({b}-({a}))"})

def fn_choice_notation(rng):
    f = rng.choice([x ** 2 + nz(rng, -4, 4), 2 * x + 1, x ** 2 - 3 * x, 3 - x ** 2])
    target = rng.choice(['f(2x)', '2f(x)', 'f(x)+2', 'f(x+2)', 'f(-x)', '-f(x)'])
    forms = {'f(2x)': f.subs(x, 2 * x), '2f(x)': 2 * f, 'f(x)+2': f + 2, 'f(x+2)': f.subs(x, x + 2), 'f(-x)': f.subs(x, -x), '-f(x)': -f}
    e = sp.expand(forms[target])
    opts, seen = [(ltx(e), plain(e))], {plain(e)}
    for name_, ex in forms.items():
        s = plain(sp.expand(ex))
        if s not in seen:
            seen.add(s); opts.append((ltx(sp.expand(ex)), s))
        if len(opts) == 4:
            break
    if len(opts) < 4:
        return None
    return choice(S8, f"If $f(x) = {ltx(f)}$, which expression equals ${target}$?", opts, 0, str(forms[target]), d=2, rng=rng,
                  hints=["Decide whether the change happens to the input (inside the parentheses) or to the output (outside).",
                         "Inside: substitute for $x$. Outside: do the operation to the whole formula."],
                  sol=[f"${target}$ means " + ("substitute into the input" if target in ('f(2x)', 'f(x+2)', 'f(-x)') else "operate on the output") + f": ${ltx(forms[target])}$.", f"Expanded: ${ltx(e)}$."])

def fn_solve_output(rng):
    m, b, c = nz(rng, -5, 5), rng.randint(-8, 8), rng.randint(-10, 10)
    sol = R(c - b, m)
    return P(S8, f"Let $f(x) = {lin(m, b)}$. Find the value of $x$ for which $f(x) = {c}$.", 'numeric', fmt_num(sol), d=1,
             hints=["Set the formula equal to the given output and solve for $x$.", f"${lin(m, b)} = {c}$."],
             sol=[f"${lin(m, b)} = {c}$ gives ${m}x = {c - b}$.", f"$x = {num(sol)}$."],
             verify={'kind': 'solve', 'lhs': f"{m}*x+({b})", 'rhs': str(c)})

def fn_word(rng):
    kind = rng.choice(['cost', 'temp', 'drop'])
    if kind == 'cost':
        a, b, n = rng.choice([3, 4, 5, 6]), rng.choice([20, 25, 30, 50]), rng.choice([10, 12, 15, 20, 25])
        f, stmt = a * x + b, f"A print shop charges $C(n) = {a}n + {b}$ dollars for $n$ posters. Find $C({n})$, the cost of {n} posters."
    elif kind == 'temp':
        n = rng.choice([2, 4, 6, 8]); f = 68 - R(3, 2) * x; stmt = f"The temperature in a cooling room is $T(h) = 68 - 1.5h$ degrees after $h$ hours. Find $T({n})$."
    else:
        n = rng.choice([1, 2, 3]); f = 80 - 16 * x ** 2; stmt = f"A dropped ball's height is $h(t) = 80 - 16t^2$ feet after $t$ seconds. Find $h({n})$."
    val = f.subs(x, n)
    return P(S8, stmt, 'numeric', fmt_num(val), d=1,
             hints=["The letter in parentheses is the input; replace it with the given number.", "Then just do the arithmetic."],
             sol=[f"Substitute ${n}$ for the input: ${ltx(f).replace('x', f'({n})')}$.", f"$= {num(val)}$."],
             verify={'kind': 'evaluate', 'expr': str(f), 'at': str(n)})

def fn_nested_numeric(rng):
    f = rng.choice([x ** 2 - 1, 2 * x + 3, x ** 2 + x, 5 - x])
    g = rng.choice([x + 2, 3 * x, x - 1, x ** 2])
    at = rng.choice([-2, -1, 1, 2, 3])
    outer_f = rng.random() < 0.5
    inner, outer = (g, f) if outer_f else (f, g)
    mid = inner.subs(x, at)
    val = outer.subs(x, mid)
    name = f"f(g({at}))" if outer_f else f"g(f({at}))"
    return P(S8, f"Let $f(x) = {ltx(f)}$ and $g(x) = {ltx(g)}$. Compute ${name}$.", 'numeric', fmt_num(val), d=2,
             hints=["Work from the inside out: evaluate the inner function first.", f"The inner value is ${'g' if outer_f else 'f'}({at}) = {mid}$."],
             sol=[f"Inner: ${'g' if outer_f else 'f'}({at}) = {mid}$.", f"Outer: ${'f' if outer_f else 'g'}({mid}) = {val}$."],
             verify={'kind': 'numeric', 'value': f"({outer}).subs(x, ({inner}).subs(x, {at}))"})

def fn_piecewise(rng):
    c = rng.randint(0, 3)
    f1, f2 = rng.choice([x ** 2, -x, x + 4, 2 * x]), rng.choice([2 * x + 1, 5 - x, x ** 2 - 1, 3])
    at = rng.choice([c - 2, c - 1, c, c + 1, c + 2, c + 3])
    expr = sp.Piecewise((f1, x < c), (f2, True))
    val = expr.subs(x, at)
    return P(S8, f"Let $f(x) = \\begin{{cases}} {ltx(f1)} & \\text{{if }} x < {c} \\\\ {ltx(f2)} & \\text{{if }} x \\ge {c} \\end{{cases}}$. Find $f({at})$.",
             'numeric', fmt_num(val), d=3,
             hints=[f"First decide which piece applies: is ${at} < {c}$ or ${at} \\ge {c}$?", f"Use the {'first' if at < c else 'second'} formula."],
             sol=[f"Since ${at} {'<' if at < c else '\\ge'} {c}$, use ${ltx(f1 if at < c else f2)}$.", f"$f({at}) = {num(val)}$."],
             verify={'kind': 'evaluate', 'expr': f"Piecewise(({f1}, x<{c}), ({f2}, True))", 'at': str(at)})

FAM[S8] = [fn_evaluate, fn_transform_input, fn_compose, fn_domain_root, fn_domain_root_den, fn_avg_rate, fn_choice_notation, fn_solve_output, fn_word, fn_nested_numeric, fn_piecewise]

# ================================================================ graphs-of-second-degree
S9 = 'graphs-of-second-degree'

def _circle_general(h, kk, r):
    """Return (expanded expr, D, E, F) for x^2+y^2+Dx+Ey+F = 0."""
    e = sp.expand((x - h) ** 2 + (y - kk) ** 2 - r * r)
    pol = sp.Poly(e, x, y)
    return e, pol.coeff_monomial(x), pol.coeff_monomial(y), pol.coeff_monomial(1)

def gs_circle_standard(rng):
    h, kk, r = rng.randint(-6, 6), rng.randint(-6, 6), rng.choice([1, 2, 3, 4, 5, 6, 7, 10])
    which = rng.choice(['radius', 'cx', 'cy'])
    e, D, E, F = _circle_general(h, kk, r)
    stmt_eq = f"({ltx(x - h)})^2 + ({ltx(y - kk)})^2 = {r * r}" if h or kk else f"x^2 + y^2 = {r * r}"
    if which == 'radius':
        val, q, vstr = r, "What is its radius?", f"sqrt(({D}/2)**2+({E}/2)**2-({F}))"
        h2 = f"The right-hand side is $r^2 = {r * r}$."
    elif which == 'cx':
        val, q, vstr = h, "What is the $x$-coordinate of its center?", f"-({D})/2"
        h2 = "Inside $(x - h)^2$ the center's $x$-coordinate is $h$ (watch the sign)."
    else:
        val, q, vstr = kk, "What is the $y$-coordinate of its center?", f"-({E})/2"
        h2 = "Inside $(y - k)^2$ the center's $y$-coordinate is $k$ (watch the sign)."
    return P(S9, f"The equation ${stmt_eq}$ describes a circle. {q}", 'numeric', str(val), d=1,
             hints=["Standard form: $(x - h)^2 + (y - k)^2 = r^2$ with center $(h, k)$ and radius $r$.", h2],
             sol=[f"Match to $(x - h)^2 + (y - k)^2 = r^2$: $h = {h}$, $k = {kk}$, $r^2 = {r * r}$.", f"So the answer is ${val}$."],
             verify={'kind': 'numeric', 'value': vstr})

def gs_circle_general(rng):
    h, kk, r = rng.randint(-5, 5), rng.randint(-5, 5), rng.choice([1, 2, 3, 4, 5, 6])
    if h == 0 and kk == 0:
        return None
    e, D, E, F = _circle_general(h, kk, r)
    which = rng.choice(['radius', 'cx', 'cy'])
    val = {'radius': r, 'cx': h, 'cy': kk}[which]
    vstr = {'radius': f"sqrt(({D}/2)**2+({E}/2)**2-({F}))", 'cx': f"-({D})/2", 'cy': f"-({E})/2"}[which]
    q = {'radius': 'its radius', 'cx': "the $x$-coordinate of its center", 'cy': "the $y$-coordinate of its center"}[which]
    return P(S9, f"The circle ${ltx(e)} = 0$ is written in general form. Find {q}.", 'numeric', str(val), d=3 if which == 'radius' else 2,
             hints=["Complete the square in $x$ and in $y$ separately.", f"Group: $(x^2 {'+' if D >= 0 else '-'} {abs(D)}x) + (y^2 {'+' if E >= 0 else '-'} {abs(E)}y) = {-F}$, then add $({num(R(D, 2))})^2$ and $({num(R(E, 2))})^2$ to both sides."],
             sol=[f"$(x^2 {'+' if D >= 0 else '-'} {abs(D)}x + {h * h}) + (y^2 {'+' if E >= 0 else '-'} {abs(E)}y + {kk * kk}) = {-F} + {h * h} + {kk * kk}$.",
                  f"$({ltx(x - h)})^2 + ({ltx(y - kk)})^2 = {r * r}$.", f"Center $({h}, {kk})$, radius ${r}$."],
             verify={'kind': 'numeric', 'value': vstr})

def gs_parabola_vertex(rng):
    a, b, c = rng.choice([1, 2, -1, -2, 3]), nz(rng, -8, 8), rng.randint(-6, 6)
    q = a * x ** 2 + b * x + c
    xv = sp.solve(sp.diff(q, x), x)[0]
    which = rng.choice(['x', 'y'])
    if which == 'x':
        return P(S9, f"Find the $x$-coordinate of the vertex of $y = {ltx(q)}$.", 'numeric', fmt_num(xv), d=2,
                 hints=["The vertex lies on the axis of symmetry $x = -b/(2a)$.", f"$a = {a}$, $b = {b}$."],
                 sol=[f"$x = -\\dfrac{{{b}}}{{2({a})}} = {num(xv)}$."] + ["The vertex is the point on the parabola at this $x$."],
                 verify={'kind': 'numeric', 'value': str(xv)})
    yv = q.subs(x, xv)
    return P(S9, f"Find the $y$-coordinate of the vertex of $y = {ltx(q)}$.", 'numeric', fmt_num(yv), d=3,
             hints=["First find the vertex's $x$-coordinate from $x = -b/(2a)$.", f"Then substitute $x = {num(xv)}$ into the equation."],
             sol=[f"$x_v = -\\dfrac{{{b}}}{{2({a})}} = {num(xv)}$.", f"$y_v = {ltx(q).replace('x', f'({num(xv)})')} = {num(yv)}$."],
             verify={'kind': 'evaluate', 'expr': str(q), 'at': str(xv)})

def gs_intercepts(rng):
    a, p, qq = rng.choice([1, 1, 2, -1]), nz(rng, -6, 6), nz(rng, -6, 6)
    if p == qq:
        return None
    q = sp.expand(a * (x - p) * (x - qq))
    which = rng.choice(['y', 'x'])
    if which == 'y':
        val = q.subs(x, 0)
        return P(S9, f"Find the $y$-intercept of the parabola $y = {ltx(q)}$. Enter the $y$-value.", 'numeric', str(val), d=1,
                 hints=["The $y$-intercept is where $x = 0$.", "Substitute $x = 0$: only the constant term survives."],
                 sol=[f"Set $x = 0$: $y = {val}$."] + ["So the parabola crosses the $y$-axis at $(0, " + str(val) + ")$."],
                 verify={'kind': 'evaluate', 'expr': str(q), 'at': '0'})
    big = max(p, qq)
    return P(S9, f"The parabola $y = {ltx(q)}$ crosses the $x$-axis twice. Enter the larger $x$-intercept.", 'numeric', str(big), d=2,
             hints=["$x$-intercepts are where $y = 0$: solve the quadratic.", f"Factor: ${ltx(q)} = {ltx(sp.factor(q))}$."],
             sol=[f"Set $y = 0$: ${ltx(sp.factor(q))} = 0$.", f"$x = {p}$ or $x = {qq}$; the larger is ${big}$."],
             verify={'kind': 'solve', 'lhs': str(q), 'rhs': '0', 'pick': str(big)})

def gs_choice_circle(rng):
    h, kk, r = nz(rng, -5, 5), nz(rng, -5, 5), rng.choice([1, 2, 3, 4, 5])
    good = (x - h) ** 2 + (y - kk) ** 2 - r * r
    cands = [good, (x + h) ** 2 + (y + kk) ** 2 - r * r, (x - h) ** 2 + (y - kk) ** 2 - r, (x - h) ** 2 + (y + kk) ** 2 - r * r, (x + h) ** 2 + (y - kk) ** 2 - r * r]
    opts = [(f"({ltx(x - h)})^2 + ({ltx(y - kk)})^2 = {r * r}", str(good)),
            (f"({ltx(x + h)})^2 + ({ltx(y + kk)})^2 = {r * r}", str(cands[1])),
            (f"({ltx(x - h)})^2 + ({ltx(y - kk)})^2 = {r}", str(cands[2])),
            (f"({ltx(x - h)})^2 + ({ltx(y + kk)})^2 = {r * r}", str(cands[3]))]
    if r == 1:
        opts[2] = (f"({ltx(x + h)})^2 + ({ltx(y - kk)})^2 = {r * r}", str(cands[4]))
    return choice(S9, f"Which equation describes the circle with center $({h}, {kk})$ and radius ${r}$?", opts, 0, str(good), d=2, rng=rng,
                  hints=["Standard form: $(x - h)^2 + (y - k)^2 = r^2$.", f"With $h = {h}$ the first factor is $(x - ({h}))^2 = ({ltx(x - h)})^2$, and the right side is $r^2 = {r * r}$."],
                  sol=[f"Substitute $h = {h}$, $k = {kk}$, $r = {r}$ into $(x - h)^2 + (y - k)^2 = r^2$.", f"$({ltx(x - h)})^2 + ({ltx(y - kk)})^2 = {r * r}$."])

def gs_point_position(rng):
    h, kk, r = rng.randint(-4, 4), rng.randint(-4, 4), rng.choice([2, 3, 4, 5])
    px, py = rng.randint(h - r - 2, h + r + 2), rng.randint(kk - r - 2, kk + r + 2)
    d2 = (px - h) ** 2 + (py - kk) ** 2
    code = 0 if d2 < r * r else (1 if d2 == r * r else 2)
    opts = [(r'\text{inside the circle}', '0'), (r'\text{on the circle}', '1'), (r'\text{outside the circle}', '2')]
    stmt_eq = f"({ltx(x - h)})^2 + ({ltx(y - kk)})^2 = {r * r}" if h or kk else f"x^2 + y^2 = {r * r}"
    return choice(S9, f"Is the point $({px}, {py})$ inside, on, or outside the circle ${stmt_eq}$?", opts, code, code, d=2, rng=rng,
                  hints=["Compare the squared distance from the center to $r^2$.", f"Substitute the point into the left side and compare with ${r * r}$."],
                  sol=[f"Left side at the point: $({px} - ({h}))^2 + ({py} - ({kk}))^2 = {d2}$.", f"Since ${d2}$ is {'less than' if code == 0 else ('equal to' if code == 1 else 'greater than')} ${r * r}$, the point is {opts[code][0][6:-1]}."],
                  extra_verify={'note': 'codes 0 inside, 1 on, 2 outside; expected = sign(d^2 - r^2) + 1', 'expected': f"sign(({px}-({h}))**2+({py}-({kk}))**2-{r * r})+1"})

def gs_vertex_form(rng):
    a, h, kk = rng.choice([1, 1, 2, -1]), nz(rng, -5, 5), rng.randint(-8, 8)
    e = sp.expand(a * (x + h) ** 2 + kk)
    ans = a * (x + h) ** 2 + kk
    return P(S9, f"Write $y = {ltx(e)}$ in vertex form $y = a(x - h)^2 + k$. Enter the right-hand side.", 'equiv', plain(ans), d=2 if a == 1 else 3,
             hints=["Complete the square." + (f" First factor ${a}$ out of the $x^2$ and $x$ terms." if a != 1 else ""), f"Half of the $x$ coefficient (after factoring) is ${h}$; square it and compensate."],
             sol=[(f"Factor: ${a}(x^2 + {2 * h}x) + {kk - 0}$." if a != 1 else f"$x^2 + {2 * h}x + ({e.subs(x, 0)})$: add and subtract ${h * h}$."),
                  f"Result: $y = {ltx(ans)}$, vertex $({-h}, {kk})$."],
             verify={'kind': 'equiv', 'expected': str(e)})

def gs_opens(rng):
    a, b, c = rng.choice([1, 2, -1, -3, 4, -2, R(1, 2), R(-1, 2)]), rng.randint(-5, 5), rng.randint(-5, 5)
    q = a * x ** 2 + b * x + c
    opts = [(r'\text{upward}', '1'), (r'\text{downward}', '-1'), (r'\text{neither: it is a line}', '0')]
    code = 0 if a > 0 else 1
    return choice(S9, f"Does the parabola $y = {ltx(q)}$ open upward or downward?", opts, code, int(sp.sign(a)), d=1, rng=rng,
                  hints=["Only the sign of the $x^2$ coefficient matters.", "Positive: opens up (has a minimum); negative: opens down (has a maximum)."],
                  sol=[f"The coefficient of $x^2$ is ${num(a)}$, which is {'positive' if a > 0 else 'negative'}.", f"So the parabola opens {'upward' if a > 0 else 'downward'}."])

def gs_circle_from_points(rng):
    kind = rng.choice(['radius2', 'center'])
    if kind == 'radius2':
        h, kk, px, py = rng.randint(-5, 5), rng.randint(-5, 5), rng.randint(-5, 5), rng.randint(-5, 5)
        if (px, py) == (h, kk):
            return None
        val = (px - h) ** 2 + (py - kk) ** 2
        return P(S9, f"A circle has center $({h}, {kk})$ and passes through $({px}, {py})$. Find $r^2$, the square of its radius.", 'numeric', str(val), d=2,
                 hints=["The radius is the distance from the center to any point on the circle.", "Use the distance formula; you only need the squared distance."],
                 sol=[f"$r^2 = ({px} - ({h}))^2 + ({py} - ({kk}))^2$.", f"$= {(px - h) ** 2} + {(py - kk) ** 2} = {val}$."],
                 verify={'kind': 'numeric', 'value': f"({px}-({h}))**2+({py}-({kk}))**2"})
    x1, y1, x2, y2 = rng.randint(-6, 6), rng.randint(-6, 6), rng.randint(-6, 6), rng.randint(-6, 6)
    if (x1, y1) == (x2, y2):
        return None
    which = rng.choice(['x', 'y'])
    val = R(x1 + x2, 2) if which == 'x' else R(y1 + y2, 2)
    return P(S9, f"The points $({x1}, {y1})$ and $({x2}, {y2})$ are the endpoints of a diameter of a circle. Find the ${which}$-coordinate of the center.", 'numeric', fmt_num(val), d=2,
             hints=["The center is the midpoint of any diameter.", "Midpoint: average the coordinates."],
             sol=[f"Center $= \\left(\\dfrac{{{x1} + ({x2})}}{{2}}, \\dfrac{{{y1} + ({y2})}}{{2}}\\right)$.", f"The ${which}$-coordinate is ${num(val)}$."],
             verify={'kind': 'numeric', 'value': (f"({x1}+({x2}))/2" if which == 'x' else f"({y1}+({y2}))/2")})

def gs_extreme(rng):
    a, b, c = rng.choice([1, 2, -1, -2]), nz(rng, -8, 8), rng.randint(-6, 6)
    q = a * x ** 2 + b * x + c
    xv = sp.solve(sp.diff(q, x), x)[0]
    yv = q.subs(x, xv)
    word = 'minimum' if a > 0 else 'maximum'
    return P(S9, f"Find the {word} value of $y = {ltx(q)}$.", 'numeric', fmt_num(yv), d=3,
             hints=[f"The {word} occurs at the vertex because the parabola opens {'upward' if a > 0 else 'downward'}.", f"Vertex $x = -b/(2a) = {num(xv)}$; evaluate $y$ there."],
             sol=[f"$x_v = -\\dfrac{{{b}}}{{2({a})}} = {num(xv)}$.", f"$y({num(xv)}) = {num(yv)}$ is the {word} value."],
             verify={'kind': 'evaluate', 'expr': str(q), 'at': str(xv)})

FAM[S9] = [gs_circle_standard, gs_circle_general, gs_parabola_vertex, gs_intercepts, gs_choice_circle, gs_point_position, gs_vertex_form, gs_opens, gs_circle_from_points, gs_extreme]

# ================================================================ transformations
S10 = 'transformations'

BASE_FUNCS = [(x ** 2, 'x^2', (-3, 3)), (Abs(x), '|x|', (-3, 3)), (sqrt(x), r'\sqrt{x}', (0.1, 4)), (x ** 3, 'x^3', (-2, 2)), (1 / x, r'\frac{1}{x}', (0.5, 3))]

def _dom_for(base_idx, h):
    lo, hi = BASE_FUNCS[base_idx][2]
    return (lo + h, hi + h)

def tr_shift(rng):
    bi = rng.randrange(len(BASE_FUNCS))
    f, fl, _ = BASE_FUNCS[bi]
    h, kk = nz(rng, -5, 5), nz(rng, -5, 5)
    g = f.subs(x, x - h) + kk
    hdir = 'right' if h > 0 else 'left'
    vdir = 'up' if kk > 0 else 'down'
    return P(S10, f"Start with $y = {fl}$. Shift the graph {abs(h)} units {hdir} and {abs(kk)} units {vdir}. Write the equation of the new graph (enter the right-hand side).",
             'equiv', plain(g), d=1 if bi in (0, 1) else 2,
             hints=["Horizontal shifts go inside with the opposite sign: right by $h$ means replace $x$ with $x - h$.", "Vertical shifts go outside with the same sign: up by $k$ means add $k$."],
             sol=[f"Shift {hdir} {abs(h)}: replace $x$ by $({ltx(x - h)})$, giving $y = {ltx(f.subs(x, x - h))}$.", f"Shift {vdir} {abs(kk)}: add $({kk})$: $y = {ltx(g)}$."],
             verify={'kind': 'equiv', 'expected': str(g)}, domain=_dom_for(bi, h))

def tr_choice_shift(rng):
    bi = rng.choice([0, 1, 2, 3])
    f, fl, _ = BASE_FUNCS[bi]
    h = nz(rng, -5, 5)
    horiz = rng.random() < 0.6
    if horiz:
        good = f.subs(x, x - h); desc = f"shifted {abs(h)} units to the {'right' if h > 0 else 'left'}"
    else:
        good = f + h; desc = f"shifted {abs(h)} units {'up' if h > 0 else 'down'}"
    cands = [good, f.subs(x, x + h), f - h, f + h, f.subs(x, x - h)]
    opts, seen = [], set()
    for c_ in cands:
        s = plain(c_)
        if s not in seen:
            seen.add(s); opts.append((f"y = {ltx(c_)}", s))
    if len(opts) < 4:
        return None
    return choice(S10, f"Which equation gives the graph of $y = {fl}$ {desc}?", opts[:4], 0, str(good), d=1, rng=rng,
                  hints=["Horizontal changes happen inside the function (next to $x$) and feel backwards; vertical changes happen outside.",
                         "Test a point: where does the vertex or corner of the original graph end up?"],
                  sol=[f"A graph {desc} has equation $y = {ltx(good)}$.", "Check: the key point of the original graph moves exactly that way."])

def tr_reflect(rng):
    f = rng.choice([x ** 3 - 2 * x, sqrt(x), x ** 2 + 3 * x, 2 ** x, Abs(x) + 1, x ** 2 - 4])
    across_x = rng.random() < 0.5
    g = -f if across_x else f.subs(x, -x)
    dom = (0.1, 3) if (f == sqrt(x) and across_x) else ((-3, -0.1) if f == sqrt(x) else (-2, 2))
    return P(S10, f"Reflect the graph of $y = {ltx(f)}$ across the ${'x' if across_x else 'y'}$-axis. Write the new equation (right-hand side only).", 'equiv', plain(g), d=2,
             hints=["Reflecting across the $x$-axis flips the sign of every output; across the $y$-axis replaces $x$ by $-x$.",
                    f"{'Multiply the whole expression by -1.' if across_x else 'Substitute -x for x and simplify.'}"],
             sol=[f"{'Across the x-axis: y = -f(x)' if across_x else 'Across the y-axis: y = f(-x)'}.", f"$y = {ltx(g)}$."],
             verify={'kind': 'equiv', 'expected': str(g)}, domain=dom)

def tr_stretch_shift(rng):
    bi = rng.choice([0, 1, 2, 3])
    f, fl, dom = BASE_FUNCS[bi]
    a, kk = rng.choice([2, 3, 4, R(1, 2), -2]), nz(rng, -5, 5)
    g = a * f + kk
    desc = (f"stretched vertically by a factor of {num(a)}" if a > 1 else (f"compressed vertically by a factor of 2" if a == R(1, 2) else "stretched vertically by a factor of 2 and reflected across the $x$-axis"))
    return P(S10, f"Start with $y = {fl}$. The graph is {desc}, then shifted {abs(kk)} units {'up' if kk > 0 else 'down'}. Write the new equation (right-hand side only).",
             'equiv', plain(g), d=2,
             hints=["Vertical stretches multiply the output; vertical shifts add to the output.", "Apply the stretch first, then the shift, in the order described."],
             sol=[f"Stretch: $y = {ltx(a * f)}$.", f"Shift: $y = {ltx(g)}$."],
             verify={'kind': 'equiv', 'expected': str(g)}, domain=dom)

def tr_point(rng):
    px, py = rng.randint(-5, 5), rng.randint(-5, 5)
    a, h, kk = rng.choice([1, 2, 3, -1, -2]), rng.randint(-4, 4), rng.randint(-4, 4)
    which = rng.choice(['x', 'y'])
    inner = ltx(x - h) if h else 'x'
    outer = f"{a if a != 1 else ''}f({inner}){'+' if kk > 0 else '-'}{abs(kk)}" if kk else f"{a if a != 1 else ''}f({inner})"
    if a == -1:
        outer = outer.replace('-1f', '-f')
    val = px + h if which == 'x' else a * py + kk
    return P(S10, f"The point $({px}, {py})$ lies on the graph of $y = f(x)$. Find the ${which}$-coordinate of the corresponding point on $y = {outer}$.", 'numeric', str(val), d=2,
             hints=["Inside changes move the point horizontally; outside changes act on the $y$-value.",
                    f"{'The x-value shifts by ' + str(h) if which == 'x' else 'New y = ' + str(a) + ' times old y, plus ' + str(kk)}."],
             sol=[(f"The input $x - ({h})$ equals ${px}$ when $x = {px + h}$." if which == 'x' else f"New $y = {a}\\cdot({py}) + ({kk}) = {val}$."), f"So the ${which}$-coordinate is ${val}$."],
             verify={'kind': 'numeric', 'value': (f"{px}+({h})" if which == 'x' else f"{a}*({py})+({kk})")})

def tr_combo_root(rng):
    h, kk = rng.randint(-4, 4), rng.randint(-4, 4)
    neg = rng.random() < 0.5
    g = (-1 if neg else 1) * sqrt(x - h) + kk
    desc = ("reflected across the $x$-axis, " if neg else "") + f"shifted {abs(h)} {'right' if h >= 0 else 'left'} and {abs(kk)} {'up' if kk >= 0 else 'down'}"
    if h == 0 or kk == 0:
        return None
    return P(S10, f"The graph of $y = \\sqrt{{x}}$ is {desc}. Write the resulting equation (right-hand side only).", 'equiv', plain(g), d=3,
             hints=["Apply the reflection (a minus sign in front) before the shifts.", "Horizontal shift inside the root with opposite sign; vertical shift added outside."],
             sol=[f"{'Reflection: y = -sqrt(x). ' if neg else ''}Horizontal shift: replace $x$ with $({ltx(x - h)})$.", f"Vertical shift: add $({kk})$. Result: $y = {ltx(g)}$."],
             verify={'kind': 'equiv', 'expected': str(g)}, domain=(h + 0.2, h + 4))

def tr_horizontal_scale(rng):
    f = rng.choice([x ** 2 + 1, Abs(x) - 2, x ** 3, 4 - x ** 2])
    c = rng.choice([2, 3, R(1, 2)])
    g = f.subs(x, c * x)
    desc = f"compressed horizontally by a factor of {c}" if c > 1 else "stretched horizontally by a factor of 2"
    return P(S10, f"The graph of $y = {ltx(f)}$ is {desc}. Write the new equation (right-hand side only).", 'equiv', plain(sp.expand(g)), d=3,
             hints=["Horizontal scaling happens inside: $y = f(cx)$ compresses by $c$ when $c > 1$ and stretches when $0 < c < 1$.",
                    f"Replace $x$ with ${num(c)}x$."],
             sol=[f"Replace $x$ by ${num(c)}x$: $y = {ltx(g)}$.", f"Simplified: $y = {ltx(sp.expand(g))}$."],
             verify={'kind': 'equiv', 'expected': str(g)}, domain=(-2, 2))

def tr_choice_describe(rng):
    bi = rng.choice([0, 1, 3])
    f, fl, _ = BASE_FUNCS[bi]
    h, kk = nz(rng, -5, 5), nz(rng, -5, 5)
    g = f.subs(x, x - h) + kk
    def d_(hh, kkk):
        return f"\\text{{{abs(hh)} {'right' if hh > 0 else 'left'}, {abs(kkk)} {'up' if kkk > 0 else 'down'}}}"
    opts = [(d_(h, kk), str(g)), (d_(-h, kk), str(f.subs(x, x + h) + kk)), (d_(h, -kk), str(f.subs(x, x - h) - kk)), (d_(-h, -kk), str(f.subs(x, x + h) - kk))]
    return choice(S10, f"Compared with $y = {fl}$, the graph of $y = {ltx(g)}$ is shifted how?", opts, 0, str(g), d=2, rng=rng,
                  hints=["Inside the function: $x - h$ means right by $h$ (and $x + h$ means left).", "Outside: $+k$ means up, $-k$ means down."],
                  sol=[f"$x - ({h})$ inside means {abs(h)} unit{'s' if abs(h) != 1 else ''} {'right' if h > 0 else 'left'}.", f"$+({kk})$ outside means {abs(kk)} unit{'s' if abs(kk) != 1 else ''} {'up' if kk > 0 else 'down'}."],
                  extra_verify={'note': 'each option plain is the equation that description would produce'})

def tr_choice_reflect(rng):
    f, fl = rng.choice([(sqrt(x), r'\sqrt{x}'), (2 ** x, '2^x'), (x ** 3, 'x^3'), (x ** 2 - 2 * x, 'x^2 - 2x')])
    across_x = rng.random() < 0.5
    good = -f if across_x else f.subs(x, -x)
    cands = [good, f.subs(x, -x) if across_x else -f, f + 1, -f.subs(x, -x), 1 / f]
    opts, seen = [], set()
    for c_ in cands:
        s = plain(c_)
        if s not in seen:
            seen.add(s); opts.append((f"y = {ltx(c_)}", s))
    if len(opts) < 4:
        return None
    return choice(S10, f"Which equation is the reflection of $y = {fl}$ across the ${'x' if across_x else 'y'}$-axis?", opts[:4], 0, str(good), d=1, rng=rng,
                  hints=["Across the $x$-axis: $y$ becomes $-y$, so $y = -f(x)$. Across the $y$-axis: $x$ becomes $-x$, so $y = f(-x)$.", "Picture one point of the graph and where it lands."],
                  sol=[f"{'Across the x-axis: negate the output.' if across_x else 'Across the y-axis: substitute -x.'}", f"$y = {ltx(good)}$."])

def tr_how_far(rng):
    bi = rng.choice([0, 1, 3])
    f, fl, _ = BASE_FUNCS[bi]
    kk = nz(rng, -9, 9)
    g = f + kk
    return P(S10, f"The graph of $y = {ltx(g)}$ is the graph of $y = {fl}$ shifted vertically. By how many units {'up' if kk > 0 else 'down'}?", 'numeric', str(abs(kk)), d=1,
             hints=["A constant added outside the function moves the whole graph vertically.", "Compare the outputs at the same $x$, for example $x = 0$."],
             sol=[f"At $x = 0$: the original gives ${f.subs(x, 0)}$, the new one gives ${g.subs(x, 0)}$.", f"The difference is ${abs(kk)}$ units {'up' if kk > 0 else 'down'}."],
             verify={'kind': 'numeric', 'value': f"Abs(({g}).subs(x,0)-({f}).subs(x,0))"})

FAM[S10] = [tr_shift, tr_choice_shift, tr_reflect, tr_stretch_shift, tr_point, tr_combo_root, tr_horizontal_scale, tr_choice_describe, tr_choice_reflect, tr_how_far]

# ================================================================ exponentials-and-logs-ramp
S11 = 'exponentials-and-logs-ramp'

def el_eval_log(rng):
    b = rng.choice([2, 3, 4, 5, 10, 8, 9, 16, 25, 27])
    e = rng.choice([R(1), R(2), R(3), R(4), R(-1), R(-2), R(1, 2), R(3, 2), R(2, 3), R(-1, 2), R(1, 3)])
    v = sp.Integer(b) ** e
    if not v.is_Rational or v == b and e == 1 and rng.random() < 0.7:
        return None
    if b in (16, 25, 27) and e.q == 1 and abs(e) > 1:
        return None
    vl = num(v)
    d = 1 if e.is_Integer and e > 0 else (2 if e.is_Integer else 3)
    return P(S11, f"Evaluate $\\log_{{{b}}} {vl}$." if v.is_Integer else f"Evaluate $\\log_{{{b}}} \\left({vl}\\right)$.", 'numeric', fmt_num(e), d=d,
             hints=[f"$\\log_{{{b}}} N$ asks: ${b}$ to what power gives $N$?", f"Write ${vl}$ as a power of ${b}$" + (" (a fraction means a negative exponent, a root means a fractional one)." if not (e.is_Integer and e > 0) else ".")],
             sol=[f"${vl} = {b}^{{{num(e)}}}$.", f"So $\\log_{{{b}}} {vl} = {num(e)}$."],
             verify={'kind': 'numeric', 'value': f"log({v.p}/{v.q},{b})" if not v.is_Integer else f"log({v},{b})"})

def el_solve_exp(rng):
    b, n = rng.choice([2, 3, 5, 4, 10]), rng.randint(2, 5)
    kind = rng.choice(['plain', 'shift', 'coef'])
    if kind == 'plain':
        stmt, lhs, rhs, ans = f"Solve ${b}^{{x}} = {b ** n}$.", f"{b}**x", str(b ** n), n
        h2 = f"${b ** n} = {b}^{{{n}}}$."
        sol = [h2, f"Equal bases, so $x = {n}$."]
        d = 1
    elif kind == 'shift':
        c = nz(rng, -3, 3)
        stmt, lhs, rhs, ans = f"Solve ${b}^{{{ltx(x + c)}}} = {b ** n}$.", f"{b}**(x+({c}))", str(b ** n), n - c
        h2 = f"${b ** n} = {b}^{{{n}}}$, so the exponents must match: ${ltx(x + c)} = {n}$."
        sol = [f"${b ** n} = {b}^{{{n}}}$.", f"${ltx(x + c)} = {n}$, so $x = {n - c}$."]
        d = 2
    else:
        c = rng.choice([2, 3, 5, 7])
        stmt, lhs, rhs, ans = f"Solve ${c} \\cdot {b}^{{x}} = {c * b ** n}$.", f"{c}*{b}**x", str(c * b ** n), n
        h2 = f"Divide both sides by ${c}$ first."
        sol = [f"Divide by ${c}$: ${b}^x = {b ** n}$.", f"${b ** n} = {b}^{{{n}}}$, so $x = {n}$."]
        d = 2
    return P(S11, stmt, 'numeric', str(ans), d=d, hints=["Write both sides as powers of the same base.", h2], sol=sol, verify={'kind': 'solve', 'lhs': lhs, 'rhs': rhs})

def el_solve_log(rng):
    b, n = rng.choice([2, 3, 4, 5, 10]), rng.randint(1, 4)
    c = rng.choice([0, 0, 1, -2, 3, -1])
    if b == 10 and n > 3:
        return None
    v = b ** n
    if c == 0:
        stmt, lhs = f"Solve $\\log_{{{b}}} x = {n}$.", f"log(x,{b})"
        sol = [f"Rewrite in exponential form: $x = {b}^{{{n}}}$.", f"$x = {v}$."]
        ans, d = v, 1
    else:
        stmt, lhs = f"Solve $\\log_{{{b}}}({ltx(x + c)}) = {n}$.", f"log(x+({c}),{b})"
        sol = [f"Exponential form: ${ltx(x + c)} = {b}^{{{n}}} = {v}$.", f"$x = {v - c}$."]
        ans, d = v - c, 2
    return P(S11, stmt, 'numeric', str(ans), d=d,
             hints=["$\\log_b A = n$ means $b^n = A$.", f"So the inside equals ${b}^{{{n}}} = {v}$."], sol=sol, verify={'kind': 'solve', 'lhs': lhs, 'rhs': str(n)})

def el_solve_e(rng):
    kind = rng.choice(['e', 'e2', 'other'])
    v = rng.choice([3, 5, 7, 10, 12, 20])
    if kind == 'e':
        stmt, lhs, ans, sol = f"Solve $e^{{x}} = {v}$. Give the exact answer.", "exp(x)", sp.log(v), [f"Take the natural log of both sides: $\\ln e^x = \\ln {v}$.", f"$x = \\ln {v}$."]
        d = 2
    elif kind == 'e2':
        cc = rng.choice([2, 3, 4])
        stmt, lhs, ans, sol = f"Solve $e^{{{cc}x}} = {v}$. Give the exact answer.", f"exp({cc}*x)", sp.log(v) / cc, [f"Take $\\ln$: ${cc}x = \\ln {v}$.", f"$x = \\dfrac{{\\ln {v}}}{{{cc}}}$."]
        d = 2
    else:
        b = rng.choice([2, 3, 5, 7])
        if v == b:
            return None
        stmt, lhs, ans, sol = f"Solve ${b}^{{x}} = {v}$. Give the exact answer using natural logs.", f"{b}**x", sp.log(v) / sp.log(b), [f"Take $\\ln$ of both sides: $x \\ln {b} = \\ln {v}$.", f"$x = \\dfrac{{\\ln {v}}}{{\\ln {b}}}$."]
        d = 3
    return P(S11, stmt, 'numeric', plain(ans), d=d,
             hints=["Undo the exponential with the natural logarithm.", "$\\ln(e^{u}) = u$, and $\\ln(b^{u}) = u \\ln b$."], sol=sol,
             verify={'kind': 'solve', 'lhs': lhs, 'rhs': str(v)})

def el_expand_condense(rng):
    kind = rng.choice(['expand', 'expand2', 'condense', 'root'])
    if kind == 'expand':
        a, b = rng.choice([2, 3, 4, 5]), rng.choice([1, 2, 3, 4])
        orig, ans = sp.log(x ** a / (x + b)), a * sp.log(x) - sp.log(x + b)
        stmt = f"Expand $\\ln\\dfrac{{x^{{{a}}}}}{{x + {b}}}$ as far as possible using the log rules ($x > 0$)."
        sol = [f"Quotient rule: $\\ln x^{{{a}}} - \\ln(x + {b})$.", f"Power rule: ${a}\\ln x - \\ln(x + {b})$."]
    elif kind == 'expand2':
        a, b = rng.choice([2, 3, 5]), rng.choice([1, 2, 3])
        orig, ans = sp.log(x ** a * (x + b)), a * sp.log(x) + sp.log(x + b)
        stmt = f"Expand $\\ln\\left(x^{{{a}}}(x + {b})\\right)$ using the log rules ($x > 0$)."
        sol = [f"Product rule: $\\ln x^{{{a}}} + \\ln(x + {b})$.", f"Power rule: ${a}\\ln x + \\ln(x + {b})$."]
    elif kind == 'condense':
        a, c = rng.choice([2, 3, 4]), rng.choice([2, 3, 5, 7])
        orig, ans = a * sp.log(x) + sp.log(c), sp.log(c * x ** a)
        stmt = f"Write ${a}\\ln x + \\ln {c}$ as a single logarithm ($x > 0$)."
        sol = [f"Power rule: ${a}\\ln x = \\ln x^{{{a}}}$.", f"Product rule: $\\ln x^{{{a}}} + \\ln {c} = \\ln({c}x^{{{a}}})$."]
    else:
        n = rng.choice([2, 3])
        orig, ans = sp.log(x ** (sp.Integer(1) / n)), sp.log(x) / n
        stmt = f"Write $\\ln\\sqrt{{x}}$ without a root ($x > 0$)." if n == 2 else "Write $\\ln\\sqrt[3]{x}$ without a root ($x > 0$)."
        sol = [f"A root is a fractional power: $\\sqrt{'[3]' if n == 3 else ''}{{x}} = x^{{1/{n}}}$.", f"Power rule: $\\dfrac{{1}}{{{n}}}\\ln x$."]
    return P(S11, stmt, 'equiv', plain(ans), d=2,
             hints=["Rules: $\\ln(AB) = \\ln A + \\ln B$, $\\ln(A/B) = \\ln A - \\ln B$, $\\ln A^p = p\\ln A$.", "Apply the product/quotient rule first, then the power rule (or the reverse when condensing)."],
             sol=sol, verify={'kind': 'equiv', 'expected': str(orig)}, domain=(0.5, 3))

def el_simplify(rng):
    kind = rng.choice(['loge', 'elog', 'logbase'])
    if kind == 'loge':
        c = rng.choice([2, 3, 4, 5, -2])
        orig, ans, stmt = sp.log(sp.exp(c * x)), c * x, f"Simplify $\\ln\\left(e^{{{ltx(c * x)}}}\\right)$."
        sol = ["$\\ln$ and $e^{(\\cdot)}$ undo each other.", f"$\\ln(e^{{{ltx(c * x)}}}) = {ltx(c * x)}$."]; d = 1; dom = (-3, 3)
    elif kind == 'elog':
        c = rng.choice([2, 3, 5])
        orig, ans, stmt = sp.exp(sp.log(x) + sp.log(c)), c * x, f"Simplify $e^{{\\ln x + \\ln {c}}}$ for $x > 0$."
        sol = [f"Combine the logs: $\\ln x + \\ln {c} = \\ln({c}x)$.", f"$e^{{\\ln({c}x)}} = {c}x$."]; d = 3; dom = (0.5, 3)
    else:
        b, p = rng.choice([2, 3, 5]), rng.choice([2, 3])
        orig, ans, stmt = sp.log((b ** p) ** x, b), p * x, f"Simplify $\\log_{{{b}}}\\left({b ** p}^{{x}}\\right)$."
        sol = [f"${b ** p} = {b}^{{{p}}}$, so ${b ** p}^x = {b}^{{{p}x}}$.", f"$\\log_{{{b}}} {b}^{{{p}x}} = {p}x$."]; d = 2; dom = (-3, 3)
    return P(S11, stmt, 'equiv', plain(ans), d=d,
             hints=["A log and an exponential with the same base cancel each other.", "Rewrite everything in terms of one base first."], sol=sol,
             verify={'kind': 'equiv', 'expected': str(orig)}, domain=dom)

def el_growth(rng):
    kind = rng.choice(['amount', 'time', 'half'])
    if kind == 'amount':
        P0, T, t = rng.choice([200, 500, 800, 1000]), rng.choice([2, 3, 4, 5]), None
        t = T * rng.randint(2, 4)
        val = P0 * 2 ** (t // T)
        return P(S11, f"A bacteria population starts at {P0} and doubles every {T} hours. How many bacteria are there after {t} hours?", 'numeric', str(val), d=1,
                 hints=[f"The population is $P(t) = {P0}\\cdot 2^{{t/{T}}}$.", f"In {t} hours there are ${t // T}$ doublings."],
                 sol=[f"$P({t}) = {P0}\\cdot 2^{{{t}/{T}}} = {P0}\\cdot 2^{{{t // T}}}$.", f"$= {P0}\\cdot{2 ** (t // T)} = {val}$."],
                 verify={'kind': 'numeric', 'value': f"{P0}*2**({t}/{T})"})
    if kind == 'time':
        P0, T, n = rng.choice([100, 250, 500]), rng.choice([2, 3, 5, 6]), rng.randint(3, 6)
        V = P0 * 2 ** n
        return P(S11, f"A colony starts at {P0} cells and doubles every {T} hours. After how many hours will it reach {V} cells?", 'numeric', str(n * T), d=3,
                 hints=[f"Set ${P0}\\cdot 2^{{t/{T}}} = {V}$ and divide by ${P0}$.", f"${V // P0} = 2^{{{n}}}$, so $t/{T} = {n}$."],
                 sol=[f"${P0}\\cdot 2^{{t/{T}}} = {V}$ gives $2^{{t/{T}}} = {V // P0} = 2^{{{n}}}$.", f"So $t/{T} = {n}$ and $t = {n * T}$ hours."],
                 verify={'kind': 'solve', 'lhs': f"{P0}*2**(x/{T})", 'rhs': str(V)})
    A0, H, n = rng.choice([80, 120, 200, 640]), rng.choice([3, 5, 8, 10]), rng.randint(2, 4)
    val = R(A0, 2 ** n)
    return P(S11, f"A {A0} g sample of a substance has a half-life of {H} days. How many grams remain after {n * H} days?", 'numeric', fmt_num(val), d=2,
             hints=[f"Remaining amount $= {A0}\\cdot\\left(\\tfrac12\\right)^{{t/{H}}}$.", f"${n * H}$ days is ${n}$ half-lives."],
             sol=[f"${n * H}/{H} = {n}$ half-lives.", f"${A0}\\cdot\\left(\\tfrac12\\right)^{{{n}}} = {num(val)}$ g."],
             verify={'kind': 'numeric', 'value': f"{A0}*(1/2)**({n * H}/{H})"})

def el_choice_rule(rng):
    kind = rng.choice(['sum', 'base'])
    if kind == 'sum':
        c = rng.choice([2, 3, 4, 5])
        good = sp.log(x * (x + c))
        opts = [(f"\\ln\\left(x(x + {c})\\right)", str(good)), (f"\\ln({ltx(2 * x + c)})", str(sp.log(2 * x + c))), (f"\\ln x \\cdot \\ln(x + {c})", f"log(x)*log(x+{c})"), (f"\\ln\\dfrac{{x}}{{x + {c}}}", f"log(x/(x+{c}))")]
        stmt, expected = f"Which expression equals $\\ln x + \\ln(x + {c})$?", f"log(x)+log(x+{c})"
        sol = ["The sum of two logs is the log of the product.", f"$\\ln x + \\ln(x + {c}) = \\ln\\left(x(x + {c})\\right)$."]
    else:
        b, p = rng.choice([2, 3, 5]), rng.choice([2, 3])
        v = b ** p
        good = p + sp.log(x, b)
        opts = [(f"{p} + \\log_{{{b}}} x", str(good)), (f"{p}\\log_{{{b}}} x", f"{p}*log(x,{b})"), (f"{v}\\log_{{{b}}} x", f"{v}*log(x,{b})"), (f"\\log_{{{b}}} x + \\log_{{{b}}} {b}", f"log(x,{b})+1")]
        stmt, expected = f"Which expression equals $\\log_{{{b}}}({v}x)$?", f"log({v}*x,{b})"
        sol = [f"Product rule: $\\log_{{{b}}}({v}x) = \\log_{{{b}}} {v} + \\log_{{{b}}} x$.", f"$\\log_{{{b}}} {v} = {p}$, so the result is ${p} + \\log_{{{b}}} x$."]
    return choice(S11, stmt, opts, 0, expected, d=2, rng=rng,
                  hints=["Product rule: $\\log(AB) = \\log A + \\log B$. There is no rule for $\\log A \\cdot \\log B$.", "Try a number: let $x = 1$ and compare both sides."],
                  sol=sol)

def el_convert(rng):
    kind = rng.choice(['lne', 'eln', 'log10', 'tolog'])
    if kind == 'lne':
        c = rng.choice([2, 3, 5, 7, -1, -4, R(1, 2)])
        return P(S11, f"Evaluate $\\ln\\left(e^{{{num(c)}}}\\right)$.", 'numeric', fmt_num(c), d=1,
                 hints=["$\\ln$ is the logarithm with base $e$.", "$\\ln(e^u) = u$ for any $u$."], sol=[f"$\\ln(e^{{{num(c)}}}) = {num(c)}$ because $\\ln$ undoes $e^{{(\\cdot)}}$."] + ["No calculator needed."],
                 verify={'kind': 'numeric', 'value': f"log(exp({c}))"})
    if kind == 'eln':
        c = rng.choice([2, 3, 5, 7, 10, 12])
        return P(S11, f"Evaluate $e^{{\\ln {c}}}$.", 'numeric', str(c), d=1,
                 hints=["$e^{(\\cdot)}$ and $\\ln$ are inverse functions.", "$e^{\\ln u} = u$ for $u > 0$."], sol=[f"$e^{{\\ln {c}}} = {c}$."] + ["The exponential undoes the natural log."],
                 verify={'kind': 'numeric', 'value': f"exp(log({c}))"})
    if kind == 'log10':
        n = rng.choice([2, 3, 4, -1, -2, 5])
        v = sp.Integer(10) ** n
        return P(S11, f"Evaluate $\\log_{{10}} {num(v)}$." if n > 0 else f"Evaluate $\\log_{{10}} \\left({num(v)}\\right)$.", 'numeric', str(n), d=1 if n > 0 else 2,
                 hints=["Ask: 10 to what power gives this number?", f"${num(v)} = 10^{{{n}}}$."], sol=[f"${num(v)} = 10^{{{n}}}$, so the log is ${n}$."] + ["Count the zeros (negative for a fraction)."],
                 verify={'kind': 'numeric', 'value': f"log({v.p}/{v.q},10)" if not v.is_Integer else f"log({v},10)"})
    b, n = rng.choice([2, 3, 4, 5]), rng.randint(2, 5)
    return P(S11, f"Rewrite ${b}^{{{n}}} = {b ** n}$ as a logarithm statement $\\log_{{{b}}} {b ** n} = ?$ and enter the missing value.", 'numeric', str(n), d=1,
             hints=["$b^n = N$ is the same statement as $\\log_b N = n$.", "The exponent becomes the value of the log."],
             sol=[f"${b}^{{{n}}} = {b ** n}$ means $\\log_{{{b}}} {b ** n} = {n}$."] + ["The base stays the base; the exponent is the answer."],
             verify={'kind': 'numeric', 'value': f"log({b ** n},{b})"})

FAM[S11] = [el_eval_log, el_solve_exp, el_solve_log, el_solve_e, el_expand_condense, el_simplify, el_growth, el_choice_rule, el_convert]

# ================================================================ sigma-notation
S12 = 'sigma-notation'

def sig_ltx(term, idx, lo, hi):
    return f"\\sum_{{{idx}={lo}}}^{{{hi}}} {term}"

def sg_linear(rng):
    a, b, n = rng.choice([1, 2, 3, 4, 5, -2]), rng.randint(-4, 6), rng.randint(3, 6)
    idx = rng.choice(['k', 'i', 'j'])
    term = ltx(a * x + b).replace('x', idx)
    val = sum(a * j + b for j in range(1, n + 1))
    terms = ' + '.join(f"({a * j + b})" if a * j + b < 0 else str(a * j + b) for j in range(1, n + 1))
    return P(S12, f"Evaluate ${sig_ltx(term, idx, 1, n)}$.", 'numeric', str(val), d=1,
             hints=[f"Substitute ${idx} = 1, 2, \\ldots, {n}$ into ${term}$ and add the results.", f"The first term is ${a + b}$ and the last is ${a * n + b}$."],
             sol=[f"Terms: ${terms}$.", f"Sum $= {val}$."],
             verify={'kind': 'numeric', 'value': f"summation({a}*k+({b}),(k,1,{n}))"})

def sg_power(rng):
    kind = rng.choice(['sq', 'cube', 'sqk', 'alt', 'recip', 'two'])
    n = rng.randint(3, 5)
    if kind == 'sq':
        term, f, lo = 'k^2', lambda j: j * j, 1
    elif kind == 'cube':
        term, f, lo, n = 'k^3', lambda j: j ** 3, 1, rng.randint(2, 4)
    elif kind == 'sqk':
        term, f, lo = '(k^2 - k)', lambda j: j * j - j, 1
    elif kind == 'alt':
        term, f, lo = '(-1)^k k', lambda j: (-1) ** j * j, 1
    elif kind == 'recip':
        term, f, lo, n = r'\frac{1}{k}', lambda j: R(1, j), 1, rng.randint(3, 4)
    else:
        term, f, lo = '2^k', lambda j: 2 ** j, 0
    val = sum(f(j) for j in range(lo, n + 1))
    terms = ' + '.join(f"({num(f(j))})" if f(j) < 0 else num(f(j)) for j in range(lo, n + 1))
    sym = {'k^2': 'k**2', 'k^3': 'k**3', '(k^2 - k)': 'k**2-k', '(-1)^k k': '(-1)**k*k', r'\frac{1}{k}': '1/k', '2^k': '2**k'}[term]
    return P(S12, f"Evaluate ${sig_ltx(term, 'k', lo, n)}$." + (" Give an exact fraction." if kind == 'recip' else ""), 'numeric', fmt_num(val), d=3 if kind in ('recip', 'alt') else 2,
             hints=[f"Write out each term for $k = {lo}$ to ${n}$ before adding.", "Watch the sign pattern." if kind == 'alt' else ("Use a common denominator." if kind == 'recip' else f"The first term is ${num(f(lo))}$.")],
             sol=[f"Terms: ${terms}$.", f"Sum $= {num(val)}$."],
             verify={'kind': 'numeric', 'value': f"summation({sym},(k,{lo},{n}))"})

def sg_choice_notation(rng):
    a, n = rng.choice([2, 3, 4, 5]), rng.randint(4, 6)
    off = rng.choice([0, 0, 1, -1])
    seq = [a * j + off for j in range(1, n + 1)]
    if min(seq) <= 0:
        return None
    written = ' + '.join(str(v) for v in seq)
    term = ltx(a * x + off).replace('x', 'k')
    if off:
        term = f"({term})"
    cands = [(sig_ltx(term, 'k', 1, n), f"summation({a}*k+({off}),(k,1,{n}))"), (sig_ltx(term, 'k', 1, n - 1), f"summation({a}*k+({off}),(k,1,{n - 1}))"),
             (sig_ltx(term, 'k', 0, n), f"summation({a}*k+({off}),(k,0,{n}))"), (sig_ltx(f"({a} + k)" if off == 0 else f"(k + {a + off})", 'k', 1, n), f"summation(k+{a + off},(k,1,{n}))"),
             (sig_ltx(f"{a}^k", 'k', 1, n), f"summation({a}**k,(k,1,{n}))")]
    vals, opts = set(), []
    for lt, pl in cands:
        v = sp.sympify(pl)
        if v in vals:
            continue
        vals.add(v); opts.append((lt, pl))
        if len(opts) == 4:
            break
    if len(opts) < 4:
        return None
    return choice(S12, f"Which sigma notation represents the sum ${written}$?", opts, 0, str(sum(seq)), d=1 if off == 0 else 2, rng=rng,
                  hints=["Find a formula for the $k$th term, then check the first and last values of $k$.", f"The terms go up by ${a}$ each time, so the formula is linear in $k$ with slope ${a}$."],
                  sol=[f"The $k$th term is ${term}$: at $k = 1$ it gives ${seq[0]}$ and at $k = {n}$ it gives ${seq[-1]}$.", f"So the sum is ${opts[0][0]}$."],
                  extra_verify={'note': 'expected is the numeric value of the written sum; each option is evaluated by SymPy'})

def sg_choice_expand(rng):
    kind = rng.choice(['sq', 'lin', 'alt'])
    n = rng.randint(3, 5)
    if kind == 'sq':
        term, good_terms, sym = 'k^2', [j * j for j in range(1, n + 1)], 'k**2'
    elif kind == 'lin':
        c = rng.choice([2, 3])
        term, good_terms, sym = f"({c}k - 1)", [c * j - 1 for j in range(1, n + 1)], f"{c}*k-1"
    else:
        term, good_terms, sym = '(-1)^{k+1} k', [(-1) ** (j + 1) * j for j in range(1, n + 1)], '(-1)**(k+1)*k'
    def fmt(ts):
        return ' + '.join(f"({t})" if t < 0 else str(t) for t in ts)
    cands = [good_terms, list(range(1, n + 1)), [2 * j for j in range(1, n + 1)], [j ** 3 for j in range(1, n + 1)], [j * j for j in range(1, n + 1)], [-t for t in good_terms]]
    opts, seen = [], set()
    for ts in cands:
        s = fmt(ts)
        if s in seen or sum(ts) in {sum(sp.sympify(o[1].split('+')).__iter__()) if False else 0 for o in []}:
            continue
        seen.add(s); opts.append((s, '+'.join(f"({t})" for t in ts)))
    vals, final = set(), []
    for o in opts:
        v = sp.sympify(o[1])
        if v not in vals:
            vals.add(v); final.append(o)
    if len(final) < 4:
        return None
    return choice(S12, f"Which written-out sum equals ${sig_ltx(term, 'k', 1, n)}$?", final[:4], 0, f"summation({sym},(k,1,{n}))", d=1, rng=rng,
                  hints=[f"Plug in $k = 1$, then $k = 2$, and so on up to $k = {n}$.", f"The first term is ${good_terms[0]}$."],
                  sol=[f"Terms for $k = 1, \\ldots, {n}$: ${fmt(good_terms)}$.", "Match this list against the options."])

def sg_formula(rng):
    kind = rng.choice(['k', 'c', 'k2'])
    if kind == 'k':
        n = rng.choice([20, 25, 30, 40, 50, 100])
        return P(S12, f"Use the formula $\\sum_{{k=1}}^{{n}} k = \\dfrac{{n(n+1)}}{{2}}$ to evaluate $\\sum_{{k=1}}^{{{n}}} k$.", 'numeric', str(n * (n + 1) // 2), d=2,
                 hints=[f"Substitute $n = {n}$ into the formula.", f"$\\dfrac{{{n}\\cdot{n + 1}}}{{2}}$."],
                 sol=[f"$\\dfrac{{{n}({n} + 1)}}{{2}} = \\dfrac{{{n * (n + 1)}}}{{2}}$.", f"$= {n * (n + 1) // 2}$."],
                 verify={'kind': 'numeric', 'value': f"summation(k,(k,1,{n}))"})
    if kind == 'c':
        c, n = rng.choice([3, 5, 7, -2, 4]), rng.choice([8, 10, 12, 15, 20])
        return P(S12, f"Evaluate $\\sum_{{k=1}}^{{{n}}} {c}$ (the summand does not depend on $k$).", 'numeric', str(c * n), d=1,
                 hints=["Every term is the same constant.", f"There are ${n}$ terms."],
                 sol=[f"The sum adds ${c}$ to itself ${n}$ times.", f"$= {n}\\cdot({c}) = {c * n}$."],
                 verify={'kind': 'numeric', 'value': f"summation({c},(k,1,{n}))"})
    n = rng.choice([6, 7, 8, 10, 12])
    return P(S12, f"Use the formula $\\sum_{{k=1}}^{{n}} k^2 = \\dfrac{{n(n+1)(2n+1)}}{{6}}$ to evaluate $\\sum_{{k=1}}^{{{n}}} k^2$.", 'numeric', str(n * (n + 1) * (2 * n + 1) // 6), d=3,
             hints=[f"Substitute $n = {n}$.", f"$\\dfrac{{{n}\\cdot{n + 1}\\cdot{2 * n + 1}}}{{6}}$."],
             sol=[f"$\\dfrac{{{n}({n + 1})({2 * n + 1})}}{{6}} = \\dfrac{{{n * (n + 1) * (2 * n + 1)}}}{{6}}$.", f"$= {n * (n + 1) * (2 * n + 1) // 6}$."],
             verify={'kind': 'numeric', 'value': f"summation(k**2,(k,1,{n}))"})

def sg_count_terms(rng):
    a, b = rng.randint(0, 6), rng.randint(8, 20)
    term = rng.choice(['k^2', '(2k+1)', r'\frac{1}{k+1}', '3k'])
    return P(S12, f"How many terms does the sum ${sig_ltx(term, 'k', a, b)}$ have?", 'numeric', str(b - a + 1), d=1,
             hints=["Count the integers from the lower limit to the upper limit, inclusive.", f"From ${a}$ to ${b}$ there are ${b} - {a} + 1$ values."],
             sol=[f"$k$ takes the values ${a}, {a + 1}, \\ldots, {b}$.", f"That is ${b} - {a} + 1 = {b - a + 1}$ terms."],
             verify={'kind': 'numeric', 'value': f"summation(1,(k,{a},{b}))"})

def sg_linearity(rng):
    n, A, B = rng.choice([4, 5, 6, 8, 10]), rng.randint(-10, 20), rng.randint(-10, 15)
    c, d, e = rng.choice([2, 3, -1, 4]), rng.choice([1, 2, 3, -2]), rng.choice([0, 1, 2, 5, -3])
    val = c * A - d * B + e * n
    term = f"({c}a_k - {d}b_k" + (f" + {e})" if e > 0 else (f" - {abs(e)})" if e < 0 else ")"))
    return P(S12, f"Suppose $\\sum_{{k=1}}^{{{n}}} a_k = {A}$ and $\\sum_{{k=1}}^{{{n}}} b_k = {B}$. Find $\\sum_{{k=1}}^{{{n}}} {term}$.", 'numeric', str(val), d=3,
             hints=["Sums split over addition and constants factor out: $\\sum (ca_k - db_k) = c\\sum a_k - d\\sum b_k$.", f"A constant term adds up to the constant times the number of terms, ${n}$."],
             sol=[f"$\\sum {term} = {c}\\sum a_k - {d}\\sum b_k + \\sum {e}$." if e else f"$\\sum {term} = {c}\\sum a_k - {d}\\sum b_k$.",
                  f"$= {c}({A}) - {d}({B})" + (f" + {e}\\cdot{n}" if e else "") + f" = {val}$."],
             verify={'kind': 'numeric', 'value': f"{c}*{A}-{d}*{B}+{e}*{n}"})

def sg_telescope(rng):
    n = rng.randint(3, 8)
    val = (n + 1) ** 2 - 1
    return P(S12, f"Evaluate $\\sum_{{k=1}}^{{{n}}} \\left((k+1)^2 - k^2\\right)$.", 'numeric', str(val), d=3,
             hints=["Write out the first few terms: most of them cancel in pairs.", f"Only $-1^2$ and $({n + 1})^2$ survive."],
             sol=[f"The terms are $(2^2 - 1^2) + (3^2 - 2^2) + \\cdots + ({n + 1}^2 - {n}^2)$.", f"Everything cancels except $-1 + {n + 1}^2 = {val}$."],
             verify={'kind': 'numeric', 'value': f"summation((k+1)**2-k**2,(k,1,{n}))"})

def sg_shifted_index(rng):
    a, b, lo = rng.choice([2, 3, 4]), rng.randint(-3, 3), rng.choice([0, 2, 3])
    hi = lo + rng.randint(2, 4)
    idx = rng.choice(['i', 'j'])
    term = ltx(a * x + b).replace('x', idx)
    val = sum(a * j + b for j in range(lo, hi + 1))
    return P(S12, f"Evaluate ${sig_ltx(term, idx, lo, hi)}$. Note that the index starts at ${lo}$.", 'numeric', str(val), d=2,
             hints=[f"The index runs over ${idx} = {lo}, {lo + 1}, \\ldots, {hi}$: ${hi - lo + 1}$ terms.", f"The first term is ${a * lo + b}$."],
             sol=[f"Terms: ${' + '.join(f'({a * j + b})' if a * j + b < 0 else str(a * j + b) for j in range(lo, hi + 1))}$.", f"Sum $= {val}$."],
             verify={'kind': 'numeric', 'value': f"summation({a}*k+({b}),(k,{lo},{hi}))"})

FAM[S12] = [sg_linear, sg_power, sg_choice_notation, sg_choice_expand, sg_formula, sg_count_terms, sg_linearity, sg_telescope, sg_shifted_index]

# ================================================================ area-by-geometry
S13 = 'area-by-geometry'

def ag_shapes(rng):
    kind = rng.choice(['rect', 'tri', 'trap'])
    if kind == 'rect':
        w, h = rng.randint(2, 12), rng.randint(2, 12)
        return P(S13, f"A rectangle is {w} units wide and {h} units tall. What is its area?", 'numeric', str(w * h), d=1,
                 hints=["Area of a rectangle is width times height.", f"${w} \\times {h}$."], sol=[f"$A = {w}\\cdot{h} = {w * h}$."] + ["Square units."],
                 verify={'kind': 'numeric', 'value': f"{w}*{h}"})
    if kind == 'tri':
        b, h = rng.randint(2, 12), rng.randint(1, 12)
        return P(S13, f"A triangle has base {b} and height {h}. What is its area?", 'numeric', fmt_num(R(b * h, 2)), d=1,
                 hints=["A triangle is half of a rectangle with the same base and height.", f"$\\tfrac12 \\cdot {b} \\cdot {h}$."],
                 sol=[f"$A = \\tfrac12 bh = \\tfrac12\\cdot{b}\\cdot{h}$.", f"$= {num(R(b * h, 2))}$."], verify={'kind': 'numeric', 'value': f"{b}*{h}/2"})
    a, b, h = rng.randint(1, 8), rng.randint(2, 12), rng.randint(1, 8)
    if a == b:
        return None
    return P(S13, f"A trapezoid has parallel sides of lengths {a} and {b} and height {h}. What is its area?", 'numeric', fmt_num(R((a + b) * h, 2)), d=1,
             hints=["Average the two parallel sides, then multiply by the height.", f"$\\dfrac{{{a} + {b}}}{{2}} \\cdot {h}$."],
             sol=[f"$A = \\dfrac{{a + b}}{{2}}h = \\dfrac{{{a} + {b}}}{{2}}\\cdot{h}$.", f"$= {num(R((a + b) * h, 2))}$."], verify={'kind': 'numeric', 'value': f"({a}+{b})*{h}/2"})

def ag_rect_under(rng):
    c, a = rng.randint(1, 9), rng.randint(-4, 5)
    b = a + rng.randint(1, 8)
    return P(S13, f"Find the area of the region under $y = {c}$ and above the $x$-axis from $x = {a}$ to $x = {b}$.", 'numeric', str(c * (b - a)), d=1,
             hints=["The region is a rectangle.", f"Its width is ${b} - ({a})$ and its height is ${c}$."],
             sol=[f"Width $= {b} - ({a}) = {b - a}$, height $= {c}$.", f"Area $= {b - a}\\cdot{c} = {c * (b - a)}$."],
             verify={'kind': 'definite', 'integrand': str(c), 'a': str(a), 'b': str(b)})

def ag_tri_under(rng):
    m, b = rng.choice([1, 2, 3, 4, R(1, 2), R(3, 2)]), rng.randint(1, 8)
    val = m * b * b / 2
    return P(S13, f"Find the area of the region under the line $y = {ltx(m * x)}$ from $x = 0$ to $x = {b}$.", 'numeric', fmt_num(val), d=1,
             hints=["Sketch it: the line starts at the origin, so the region is a right triangle.", f"The base is ${b}$ and the height is the $y$-value at $x = {b}$."],
             sol=[f"At $x = {b}$ the height is $y = {num(m * b)}$.", f"Area $= \\tfrac12\\cdot{b}\\cdot{num(m * b)} = {num(val)}$."],
             verify={'kind': 'definite', 'integrand': f"({m})*x", 'a': '0', 'b': str(b)})

def ag_trap_under(rng):
    m, c = rng.choice([1, 2, 3, R(1, 2), -1, -2, R(-1, 2)]), rng.randint(1, 10)
    a = rng.randint(-3, 4); b = a + rng.randint(1, 6)
    ya, yb = m * a + c, m * b + c
    if ya <= 0 or yb <= 0:
        return None
    val = (ya + yb) * (b - a) / 2
    return P(S13, f"Find the area of the region under $y = {lin(m, c)}$ and above the $x$-axis from $x = {a}$ to $x = {b}$.", 'numeric', fmt_num(val), d=2,
             hints=["The region is a trapezoid standing on the $x$-axis: its parallel sides are the heights at the two ends.", f"Heights: $y({a}) = {num(ya)}$ and $y({b}) = {num(yb)}$; width ${b - a}$."],
             sol=[f"$y({a}) = {num(ya)}$, $y({b}) = {num(yb)}$.", f"Area $= \\dfrac{{{num(ya)} + {num(yb)}}}{{2}}\\cdot{b - a} = {num(val)}$."],
             verify={'kind': 'definite', 'integrand': f"({m})*x+({c})", 'a': str(a), 'b': str(b)})

def ag_shoelace(rng):
    pts = [(rng.randint(-5, 5), rng.randint(-5, 5)) for _ in range(3)]
    (x1, y1), (x2, y2), (x3, y3) = pts
    area2 = abs(x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if area2 == 0:
        return None
    val = R(area2, 2)
    return P(S13, f"Find the area of the triangle with vertices $({x1}, {y1})$, $({x2}, {y2})$, and $({x3}, {y3})$.", 'numeric', fmt_num(val), d=2,
             hints=["Enclose the triangle in a rectangle and subtract the corner right triangles, or use the shoelace formula.",
                    "Shoelace: $\\tfrac12|x_1(y_2 - y_3) + x_2(y_3 - y_1) + x_3(y_1 - y_2)|$."],
             sol=[f"$\\tfrac12|{x1}({y2} - ({y3})) + {x2}({y3} - ({y1})) + {x3}({y1} - ({y2}))|$.", f"$= \\tfrac12|{x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)}| = {num(val)}$."],
             verify={'kind': 'numeric', 'value': f"Abs({x1}*({y2}-({y3}))+{x2}*({y3}-({y1}))+{x3}*({y1}-({y2})))/2"})

def ag_between(rng):
    c, m = rng.randint(3, 10), rng.choice([1, 2, R(1, 2)])
    b = rng.randint(1, 6)
    if m * b > c:
        return None
    val = c * b - m * b * b / 2
    return P(S13, f"Find the area of the region between the horizontal line $y = {c}$ and the line $y = {ltx(m * x)}$ for $0 \\le x \\le {b}$.", 'numeric', fmt_num(val), d=3,
             hints=["Take the rectangle under $y = {c}$ and remove the triangle under the slanted line.".replace('{c}', str(c)), f"Rectangle: ${c}\\cdot{b}$; triangle: $\\tfrac12\\cdot{b}\\cdot{num(m * b)}$."],
             sol=[f"Rectangle area $= {c}\\cdot{b} = {c * b}$.", f"Triangle under $y = {ltx(m * x)}$: $\\tfrac12\\cdot{b}\\cdot{num(m * b)} = {num(m * b * b / 2)}$.", f"Difference: ${num(val)}$."],
             verify={'kind': 'definite', 'integrand': f"{c}-({m})*x", 'a': '0', 'b': str(b)})

def ag_choice_formula(rng):
    m, c = rng.choice([1, 2, 3]), rng.randint(1, 6)
    a = rng.randint(0, 3); b = a + rng.randint(2, 5)
    fa, fb = m * a + c, m * b + c
    val = (fa + fb) * (b - a) // 2 if (fa + fb) * (b - a) % 2 == 0 else R((fa + fb) * (b - a), 2)
    opts = [(f"\\dfrac{{{fa} + {fb}}}{{2}}\\cdot{b - a}", f"({fa}+{fb})/2*{b - a}"), (f"({fa} + {fb})\\cdot{b - a}", f"({fa}+{fb})*{b - a}"),
            (f"{fb}\\cdot{b - a}", f"{fb}*{b - a}"), (f"{fa}\\cdot{b - a}", f"{fa}*{b - a}")]
    return choice(S13, f"The region under $y = {lin(m, c)}$ from $x = {a}$ to $x = {b}$ is a trapezoid. Which computation gives its area?", opts, 0,
                  f"integrate({m}*x+{c},(x,{a},{b}))", d=2, rng=rng,
                  hints=["The two parallel sides are the heights of the line at the endpoints.", "Trapezoid area = (average of the parallel sides) times the width."],
                  sol=[f"Heights: $y({a}) = {fa}$ and $y({b}) = {fb}$; width ${b - a}$.", f"Area $= \\dfrac{{{fa} + {fb}}}{{2}}\\cdot{b - a} = {num(val)}$."],
                  extra_verify={'note': 'expected is the definite integral; the correct option must equal it and distractors must not'})

def ag_circle_part(rng):
    r = rng.choice([1, 2, 3, 4, 5, 6])
    kind = rng.choice(['quarter', 'half'])
    val = pi * r * r / (4 if kind == 'quarter' else 2)
    return P(S13, f"Find the area of a {'quarter' if kind == 'quarter' else 'half'} circle of radius {r}. Give an exact answer in terms of $\\pi$.", 'numeric', plain(val), d=2,
             hints=["A full circle has area $\\pi r^2$.", f"Take {'one quarter' if kind == 'quarter' else 'half'} of it."],
             sol=[f"Full circle: $\\pi\\cdot{r}^2 = {r * r}\\pi$.", f"{'Quarter' if kind == 'quarter' else 'Half'}: ${ltx(val)}$."],
             verify={'kind': 'numeric', 'value': f"pi*{r}**2/{4 if kind == 'quarter' else 2}"})

def ag_abs(rng):
    a, b = rng.randint(1, 5), rng.randint(1, 6)
    val = R(a * a + b * b, 2)
    return P(S13, f"Find the area of the region under $y = |x|$ from $x = -{a}$ to $x = {b}$.", 'numeric', fmt_num(val), d=3,
             hints=["The graph of $|x|$ is a V: the region is two right triangles meeting at the origin.", f"Left triangle: base ${a}$, height ${a}$. Right triangle: base ${b}$, height ${b}$."],
             sol=[f"Left: $\\tfrac12\\cdot{a}\\cdot{a} = {num(R(a * a, 2))}$.", f"Right: $\\tfrac12\\cdot{b}\\cdot{b} = {num(R(b * b, 2))}$.", f"Total: ${num(val)}$."],
             verify={'kind': 'definite', 'integrand': 'Abs(x)', 'a': str(-a), 'b': str(b)})

def ag_line_two_points(rng):
    x1, y1 = rng.randint(0, 2), rng.randint(1, 6)
    x2, y2 = x1 + rng.randint(2, 6), rng.randint(1, 8)
    if y1 == y2:
        return None
    m = R(y2 - y1, x2 - x1)
    val = R(y1 + y2, 2) * (x2 - x1)
    return P(S13, f"A line passes through $({x1}, {y1})$ and $({x2}, {y2})$. Find the area under this line and above the $x$-axis from $x = {x1}$ to $x = {x2}$.", 'numeric', fmt_num(val), d=3,
             hints=["You do not need the equation of the line: the two given points are the tops of the trapezoid's parallel sides.", f"Parallel sides ${y1}$ and ${y2}$, width ${x2 - x1}$."],
             sol=[f"The region is a trapezoid with heights ${y1}$ and ${y2}$ and width ${x2} - {x1} = {x2 - x1}$.", f"Area $= \\dfrac{{{y1} + {y2}}}{{2}}\\cdot{x2 - x1} = {num(val)}$."],
             verify={'kind': 'definite', 'integrand': f"{y1}+({m})*(x-{x1})", 'a': str(x1), 'b': str(x2)})

FAM[S13] = [ag_shapes, ag_rect_under, ag_tri_under, ag_trap_under, ag_shoelace, ag_between, ag_choice_formula, ag_circle_part, ag_abs, ag_line_two_points]

# ================================================================ right-triangle-trig
S14 = 'right-triangle-trig'
TRIPLES = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (6, 8, 10), (9, 12, 15), (20, 21, 29), (9, 40, 41), (12, 16, 20)]
SPECIAL = [(30, pi / 6), (45, pi / 4), (60, pi / 3)]
FN = {'sin': sin, 'cos': cos, 'tan': tan}
FNL = {'sin': r'\sin', 'cos': r'\cos', 'tan': r'\tan'}

def rt_ratio(rng):
    a, b, c = rng.choice(TRIPLES)
    if rng.random() < 0.5:
        a, b = b, a
    fn = rng.choice(['sin', 'cos', 'tan'])
    val = {'sin': R(a, c), 'cos': R(b, c), 'tan': R(a, b)}[fn]
    vstr = {'sin': f"{a}/sqrt({a}**2+{b}**2)", 'cos': f"{b}/sqrt({a}**2+{b}**2)", 'tan': f"{a}/{b}"}[fn]
    return P(S14, f"A right triangle has legs of length {a} and {b}. Let $\\theta$ be the acute angle opposite the leg of length {a}. Find ${FNL[fn]}\\theta$ as a fraction.", 'numeric', fmt_num(val), d=1,
             hints=["SOH-CAH-TOA: sine = opposite/hypotenuse, cosine = adjacent/hypotenuse, tangent = opposite/adjacent.", f"First find the hypotenuse with the Pythagorean theorem: $\\sqrt{{{a}^2 + {b}^2}} = {c}$."],
             sol=[f"Hypotenuse: $\\sqrt{{{a * a} + {b * b}}} = {c}$.", f"Opposite $= {a}$, adjacent $= {b}$.", f"${FNL[fn]}\\theta = {num(val)}$."],
             verify={'kind': 'numeric', 'value': vstr})

def rt_from_sin(rng):
    a, b, c = rng.choice(TRIPLES)
    if sp.gcd(a, c) != 1:
        return None
    given = rng.choice(['sin', 'cos'])
    want = rng.choice([f for f in ['sin', 'cos', 'tan'] if f != given])
    if given == 'sin':
        g = R(a, c); vals = {'cos': (R(b, c), f"sqrt(1-({a}/{c})**2)"), 'tan': (R(a, b), f"({a}/{c})/sqrt(1-({a}/{c})**2)")}
    else:
        g = R(b, c); vals = {'sin': (R(a, c), f"sqrt(1-({b}/{c})**2)"), 'tan': (R(a, b), f"sqrt(1-({b}/{c})**2)/({b}/{c})")}
    val, vstr = vals[want]
    return P(S14, f"$\\theta$ is an acute angle with ${FNL[given]}\\theta = {num(g)}$. Find ${FNL[want]}\\theta$.", 'numeric', fmt_num(val), d=2,
             hints=[f"Draw a right triangle where ${FNL[given]}\\theta = {num(g)}$ and find the third side.", "Use the Pythagorean theorem for the missing side, then read off the ratio."],
             sol=[f"Sides: {'opposite' if given == 'sin' else 'adjacent'} ${g.p}$, hypotenuse ${c}$, so the third side is $\\sqrt{{{c}^2 - {g.p}^2}} = {b if given == 'sin' else a}$.", f"${FNL[want]}\\theta = {num(val)}$."],
             verify={'kind': 'numeric', 'value': vstr})

def rt_pythagoras(rng):
    kind = rng.choice(['hyp', 'leg'])
    if kind == 'hyp':
        a, b = rng.randint(1, 9), rng.randint(1, 9)
        val = sqrt(a * a + b * b)
        return P(S14, f"A right triangle has legs {a} and {b}. Find the length of the hypotenuse (exact, simplified).", 'numeric', plain(val), d=1,
                 hints=["Pythagorean theorem: $a^2 + b^2 = c^2$.", f"$c = \\sqrt{{{a}^2 + {b}^2}}$; simplify the root if you can."],
                 sol=[f"$c^2 = {a * a} + {b * b} = {a * a + b * b}$.", f"$c = {ltx(val)}$."], verify={'kind': 'numeric', 'value': f"sqrt({a}**2+{b}**2)"})
    a, b, c = rng.choice(TRIPLES)
    return P(S14, f"A right triangle has hypotenuse {c} and one leg {a}. Find the other leg.", 'numeric', str(b), d=1,
             hints=["The hypotenuse is the longest side: $c^2 = a^2 + b^2$.", f"$b = \\sqrt{{{c}^2 - {a}^2}}$."],
             sol=[f"$b^2 = {c * c} - {a * a} = {b * b}$.", f"$b = {b}$."], verify={'kind': 'numeric', 'value': f"sqrt({c}**2-{a}**2)"})

def rt_convert(rng):
    to_rad = rng.random() < 0.5
    if to_rad:
        deg = rng.choice([30, 45, 60, 90, 120, 135, 150, 180, 210, 225, 240, 270, 300, 315, 330, 360, 15, 75, 20, 36, 72])
        val = sp.nsimplify(deg * pi / 180)
        return P(S14, f"Convert ${deg}^\\circ$ to radians. Give an exact answer in terms of $\\pi$.", 'numeric', plain(val), d=1,
                 hints=["$180^\\circ = \\pi$ radians, so multiply degrees by $\\pi/180$.", f"$\\dfrac{{{deg}}}{{180}}$ reduces to ${num(R(deg, 180))}$."],
                 sol=[f"${deg}^\\circ \\cdot \\dfrac{{\\pi}}{{180^\\circ}} = \\dfrac{{{deg}\\pi}}{{180}}$.", f"$= {ltx(val)}$."], verify={'kind': 'numeric', 'value': f"{deg}*pi/180"})
    p, q = rng.choice([(1, 6), (1, 4), (1, 3), (1, 2), (2, 3), (3, 4), (5, 6), (7, 6), (5, 4), (4, 3), (3, 2), (5, 3), (7, 4), (11, 6), (1, 12), (5, 12), (1, 10), (2, 5)])
    deg = R(p, q) * 180
    return P(S14, f"Convert $\\dfrac{{{p}\\pi}}{{{q}}}$ radians to degrees." if p != 1 else f"Convert $\\dfrac{{\\pi}}{{{q}}}$ radians to degrees.", 'numeric', fmt_num(deg), d=1,
             hints=["$\\pi$ radians $= 180^\\circ$, so replace $\\pi$ with $180$.", f"$\\dfrac{{{p}\\cdot 180}}{{{q}}}$."],
             sol=[f"$\\dfrac{{{p}\\pi}}{{{q}}} = \\dfrac{{{p}\\cdot 180^\\circ}}{{{q}}}$.", f"$= {num(deg)}^\\circ$."], verify={'kind': 'numeric', 'value': f"{p}*pi/{q}*180/pi"})

def rt_special(rng):
    deg, rad = rng.choice(SPECIAL)
    fn = rng.choice(['sin', 'cos', 'tan'])
    use_deg = rng.random() < 0.5
    val = FN[fn](rad)
    arg = f"{deg}^\\circ" if use_deg else ltx(rad)
    return P(S14, f"Find the exact value of ${FNL[fn]}\\left({arg}\\right)$.", 'numeric', plain(val), d=1 if fn != 'tan' else 2,
             hints=["Use the 30-60-90 triangle (sides $1, \\sqrt{3}, 2$) or the 45-45-90 triangle (sides $1, 1, \\sqrt{2}$).", f"${arg}$ is ${deg}^\\circ$: " + ("use the 45-45-90 triangle." if deg == 45 else f"the side opposite it in the 30-60-90 triangle is ${'1' if deg == 30 else chr(92) + 'sqrt{3}'}$.")],
             sol=[f"In the reference triangle, the sides give ${FNL[fn]}({arg}) = {ltx(val)}$."] + ["Rationalize the denominator if needed."],
             verify={'kind': 'numeric', 'value': f"{fn}({rad})"})

def rt_word(rng):
    kind = rng.choice(['ladder', 'shadow', 'ramp'])
    deg, rad = rng.choice(SPECIAL)
    if kind == 'ladder':
        L = rng.choice([4, 6, 8, 10, 12])
        val = sp.simplify(L * sin(rad))
        return P(S14, f"A {L} m ladder leans against a wall, making a ${deg}^\\circ$ angle with the ground. How high up the wall does it reach? Give an exact answer.", 'numeric', plain(val), d=2,
                 hints=["The ladder is the hypotenuse; the height is the side opposite the ground angle.", f"height $= {L}\\sin {deg}^\\circ$."],
                 sol=[f"$\\sin {deg}^\\circ = \\dfrac{{\\text{{height}}}}{{{L}}}$.", f"height $= {L}\\cdot{ltx(sin(rad))} = {ltx(val)}$."], verify={'kind': 'numeric', 'value': f"{L}*sin({rad})"})
    if kind == 'shadow':
        s = rng.choice([5, 6, 9, 10, 12])
        val = sp.simplify(s * tan(rad))
        return P(S14, f"A tree casts a shadow {s} m long when the sun is ${deg}^\\circ$ above the horizon. How tall is the tree? Give an exact answer.", 'numeric', plain(val), d=2,
                 hints=["The shadow is the adjacent side and the tree is the opposite side.", f"height $= {s}\\tan {deg}^\\circ$."],
                 sol=[f"$\\tan {deg}^\\circ = \\dfrac{{\\text{{height}}}}{{{s}}}$.", f"height $= {s}\\cdot{ltx(tan(rad))} = {ltx(val)}$."], verify={'kind': 'numeric', 'value': f"{s}*tan({rad})"})
    h = rng.choice([2, 3, 4, 5, 6])
    val = sp.simplify(h / sin(rad))
    return P(S14, f"A ramp rises {h} m and makes a ${deg}^\\circ$ angle with the ground. How long is the ramp? Give an exact answer.", 'numeric', plain(val), d=2,
             hints=["The ramp is the hypotenuse; the rise is opposite the angle.", f"ramp $= \\dfrac{{{h}}}{{\\sin {deg}^\\circ}}$."],
             sol=[f"$\\sin {deg}^\\circ = \\dfrac{{{h}}}{{\\text{{ramp}}}}$.", f"ramp $= \\dfrac{{{h}}}{{{ltx(sin(rad))}}} = {ltx(val)}$."], verify={'kind': 'numeric', 'value': f"{h}/sin({rad})"})

def rt_solve_side(rng):
    deg, rad = rng.choice(SPECIAL)
    opp = rng.choice([2, 3, 4, 5, 6, 8])
    want = rng.choice(['hyp', 'adj'])
    val = sp.simplify(opp / sin(rad)) if want == 'hyp' else sp.simplify(opp / tan(rad))
    return P(S14, f"In a right triangle one acute angle is ${deg}^\\circ$ and the side opposite it has length {opp}. Find the {'hypotenuse' if want == 'hyp' else 'other leg (adjacent to the angle)'}. Give an exact answer.",
             'numeric', plain(val), d=2 if want == 'hyp' else 3,
             hints=[f"Pick the ratio that links the opposite side with the side you want: {'sine (opp/hyp)' if want == 'hyp' else 'tangent (opp/adj)'}.", f"${'\\sin' if want == 'hyp' else '\\tan'} {deg}^\\circ = \\dfrac{{{opp}}}{{?}}$."],
             sol=[f"${'\\sin' if want == 'hyp' else '\\tan'} {deg}^\\circ = {ltx(sin(rad) if want == 'hyp' else tan(rad))}$.", f"Side $= \\dfrac{{{opp}}}{{{ltx(sin(rad) if want == 'hyp' else tan(rad))}}} = {ltx(val)}$."],
             verify={'kind': 'numeric', 'value': f"{opp}/{'sin' if want == 'hyp' else 'tan'}({rad})"})

def rt_choice_ratio(rng):
    a, b, c = rng.choice(TRIPLES[:6])
    fn = rng.choice(['sin', 'cos', 'tan'])
    good = {'sin': (frac(a, c), f"{a}/{c}"), 'cos': (frac(b, c), f"{b}/{c}"), 'tan': (frac(a, b), f"{a}/{b}")}[fn]
    allr = [(frac(a, c), f"{a}/{c}"), (frac(b, c), f"{b}/{c}"), (frac(a, b), f"{a}/{b}"), (frac(b, a), f"{b}/{a}"), (frac(c, a), f"{c}/{a}")]
    opts = [good] + [o for o in allr if o != good][:3]
    expected = {'sin': f"{a}/sqrt({a}**2+{b}**2)", 'cos': f"{b}/sqrt({a}**2+{b}**2)", 'tan': f"{a}/{b}"}[fn]
    return choice(S14, f"A right triangle has legs {a} and {b} and hypotenuse {c}. Which fraction is ${FNL[fn]}$ of the angle opposite the leg of length {a}?", opts, 0, expected, d=1, rng=rng,
                  hints=["Label the sides relative to that angle: opposite, adjacent, hypotenuse.", "SOH-CAH-TOA."],
                  sol=[f"Opposite $= {a}$, adjacent $= {b}$, hypotenuse $= {c}$.", f"${FNL[fn]}\\theta = {good[0]}$."])

def rt_arc(rng):
    r = rng.choice([2, 3, 4, 5, 6, 8, 9, 12])
    p, q = rng.choice([(1, 6), (1, 4), (1, 3), (1, 2), (2, 3), (3, 4), (5, 6), (3, 2)])
    theta = R(p, q) * pi
    kind = rng.choice(['arc', 'sector'])
    if kind == 'arc':
        val = r * theta
        return P(S14, f"A circle has radius {r}. Find the length of the arc cut off by a central angle of ${ltx(theta)}$ radians. Give an exact answer.", 'numeric', plain(val), d=2,
                 hints=["Arc length $s = r\\theta$ (this is why radians are convenient).", f"$s = {r}\\cdot{ltx(theta)}$."],
                 sol=[f"$s = r\\theta = {r}\\cdot{ltx(theta)}$.", f"$= {ltx(val)}$."], verify={'kind': 'numeric', 'value': f"{r}*{theta}"})
    val = r * r * theta / 2
    return P(S14, f"A circle has radius {r}. Find the area of the sector with central angle ${ltx(theta)}$ radians. Give an exact answer.", 'numeric', plain(val), d=3,
             hints=["Sector area $= \\tfrac12 r^2\\theta$ with $\\theta$ in radians.", f"$\\tfrac12\\cdot{r}^2\\cdot{ltx(theta)}$."],
             sol=[f"$A = \\tfrac12 r^2\\theta = \\tfrac12\\cdot{r * r}\\cdot{ltx(theta)}$.", f"$= {ltx(val)}$."], verify={'kind': 'numeric', 'value': f"{r}**2*{theta}/2"})

def rt_angle_from_sides(rng):
    kind = rng.choice([(1, 1, pi / 4), (1, sqrt(3), pi / 6), (sqrt(3), 1, pi / 3), (2, 2, pi / 4), (3, 3 * sqrt(3), pi / 6), (5 * sqrt(3), 5, pi / 3)])
    a, b, ans = kind
    return P(S14, f"A right triangle has legs ${ltx(a)}$ (opposite $\\theta$) and ${ltx(b)}$ (adjacent to $\\theta$). Find $\\theta$ in radians.", 'numeric', plain(ans), d=2,
             hints=[f"$\\tan\\theta = \\dfrac{{\\text{{opposite}}}}{{\\text{{adjacent}}}} = {ltx(a / b)}$.", "Which special angle has that tangent?"],
             sol=[f"$\\tan\\theta = {ltx(sp.simplify(a / b))}$.", f"So $\\theta = {ltx(ans)}$."], verify={'kind': 'numeric', 'value': f"atan(({a})/({b}))"})

def rt_cofunction(rng):
    deg = rng.choice([10, 20, 25, 35, 40, 50, 55, 65, 70, 80])
    fn, co = rng.choice([('sin', 'cos'), ('cos', 'sin')])
    return P(S14, f"For an acute angle $\\theta$, ${FNL[fn]} {deg}^\\circ = {FNL[co]}\\theta$. Find $\\theta$ in degrees.", 'numeric', str(90 - deg), d=1,
             hints=["Sine and cosine of complementary angles are equal.", "Two angles are complementary when they add to $90^\\circ$."],
             sol=[f"${FNL[fn]}\\theta = {FNL[co]}(90^\\circ - \\theta)$ for every acute angle.", f"So $\\theta = 90^\\circ - {deg}^\\circ = {90 - deg}^\\circ$."],
             verify={'kind': 'numeric', 'value': f"90-{deg}"})

FAM[S14] = [rt_ratio, rt_from_sin, rt_pythagoras, rt_convert, rt_special, rt_word, rt_solve_side, rt_choice_ratio, rt_arc, rt_angle_from_sides, rt_cofunction]

# ================================================================ unit-circle
S15 = 'unit-circle'
ANGLES = [R(p, q) * pi for p, q in [(0, 1), (1, 6), (1, 4), (1, 3), (1, 2), (2, 3), (3, 4), (5, 6), (1, 1), (7, 6), (5, 4), (4, 3), (3, 2), (5, 3), (7, 4), (11, 6)]]

def _quadrant(theta):
    t = sp.Mod(theta, 2 * pi)
    return int(sp.floor(t / (pi / 2))) + 1

def uc_exact(rng):
    theta = rng.choice(ANGLES[1:])
    fn = rng.choice(['sin', 'cos', 'tan'])
    val = FN[fn](theta)
    if val in (sp.zoo, sp.nan):
        return None
    q = _quadrant(theta)
    ref = min(sp.Mod(theta, pi), pi - sp.Mod(theta, pi))
    return P(S15, f"Find the exact value of ${FNL[fn]}\\left({ltx(theta)}\\right)$.", 'numeric', plain(val), d=1 if q <= 2 and fn != 'tan' else 2,
             hints=[f"Locate the angle: ${ltx(theta)}$ is in quadrant {'I II III IV'.split()[q - 1]} with reference angle ${ltx(ref)}$." if theta not in (pi, 3 * pi / 2, pi / 2) else f"${ltx(theta)}$ lands on an axis; use the point's coordinates.",
                    f"{'Sine is the y-coordinate' if fn == 'sin' else ('Cosine is the x-coordinate' if fn == 'cos' else 'Tangent is y/x')} of the point on the unit circle; fix the sign by quadrant."],
             sol=[f"Reference angle ${ltx(ref)}$, quadrant {'I II III IV'.split()[q - 1]}." if ref not in (0,) else f"The angle ${ltx(theta)}$ lies on an axis.",
                  f"${FNL[fn]}({ltx(theta)}) = {ltx(val)}$."],
             verify={'kind': 'numeric', 'value': f"{fn}({theta})"})

def uc_degrees(rng):
    deg = rng.choice([120, 135, 150, 180, 210, 225, 240, 270, 300, 315, 330, 360, 90])
    fn = rng.choice(['sin', 'cos', 'tan'])
    val = FN[fn](deg * pi / 180)
    if val in (sp.zoo, sp.nan):
        return None
    return P(S15, f"Find the exact value of ${FNL[fn]} {deg}^\\circ$.", 'numeric', plain(val), d=2,
             hints=[f"Find the reference angle: the acute angle between the terminal side of ${deg}^\\circ$ and the $x$-axis.", "Then attach the sign for the quadrant (All Students Take Calculus)."],
             sol=[f"${deg}^\\circ$ has reference angle ${int(min(deg % 180, 180 - deg % 180))}^\\circ$.", f"${FNL[fn]} {deg}^\\circ = {ltx(val)}$."],
             verify={'kind': 'numeric', 'value': f"{fn}({deg}*pi/180)"})

def uc_reference(rng):
    theta = rng.choice([a for a in ANGLES if a not in (0, pi / 2, pi, 3 * pi / 2)])
    ref = min(sp.Mod(theta, pi), pi - sp.Mod(theta, pi))
    return P(S15, f"Find the reference angle of ${ltx(theta)}$ (in radians).", 'numeric', plain(ref), d=1,
             hints=["The reference angle is the acute angle between the terminal side and the $x$-axis.", "In quadrants II and III measure from $\\pi$; in quadrant IV measure from $2\\pi$."],
             sol=[f"${ltx(theta)}$ is in quadrant {'I II III IV'.split()[_quadrant(theta) - 1]}.", f"Its distance to the nearest half-turn of the $x$-axis is ${ltx(ref)}$."],
             verify={'kind': 'numeric', 'value': f"Min(Mod({theta},pi), pi-Mod({theta},pi))"})

def uc_quadrant(rng):
    theta = rng.choice([a for a in ANGLES if a not in (0, pi / 2, pi, 3 * pi / 2)] + [-pi / 3, -pi / 6, -3 * pi / 4, 13 * pi / 6, 9 * pi / 4, -5 * pi / 4])
    q = _quadrant(theta)
    opts = [('\\text{I}', '1'), ('\\text{II}', '2'), ('\\text{III}', '3'), ('\\text{IV}', '4')]
    return choice(S15, f"In which quadrant does the terminal side of the angle ${ltx(theta)}$ lie?", opts, q - 1, q, d=1, rng=rng,
                  hints=["Compare the angle with $\\pi/2$, $\\pi$, and $3\\pi/2$ (add or subtract $2\\pi$ first if it is negative or more than one turn).", "Quadrant I: $0$ to $\\pi/2$; II: $\\pi/2$ to $\\pi$; III: $\\pi$ to $3\\pi/2$; IV: $3\\pi/2$ to $2\\pi$."],
                  sol=[f"Reduced to one turn: ${ltx(sp.Mod(theta, 2 * pi))}$.", f"That lies in quadrant {'I II III IV'.split()[q - 1]}."])

def uc_coterminal(rng):
    theta = rng.choice([13 * pi / 6, 9 * pi / 4, 7 * pi / 3, 5 * pi / 2, 17 * pi / 6, 11 * pi / 4, 10 * pi / 3, 3 * pi, -pi / 6, -pi / 4, -pi / 3, -2 * pi / 3, -5 * pi / 4, -7 * pi / 6, -pi / 2, -3 * pi / 2])
    val = sp.Mod(theta, 2 * pi)
    return P(S15, f"Find the angle in $[0, 2\\pi)$ that is coterminal with ${ltx(theta)}$.", 'numeric', plain(val), d=2,
             hints=["Coterminal angles differ by whole turns of $2\\pi$.", f"{'Subtract' if theta > 0 else 'Add'} $2\\pi$ until the result is between $0$ and $2\\pi$."],
             sol=[f"${ltx(theta)} {'-' if theta > 0 else '+'} 2\\pi" + (f" = {ltx(theta - 2 * pi if theta > 0 else theta + 2 * pi)}$." if abs(theta) < 4 * pi else "$ ...")] +
                 [f"The coterminal angle in $[0, 2\\pi)$ is ${ltx(val)}$."],
             verify={'kind': 'numeric', 'value': f"Mod({theta}, 2*pi)"})

def uc_point(rng):
    theta = rng.choice(ANGLES)
    coord = rng.choice(['x', 'y'])
    val = cos(theta) if coord == 'x' else sin(theta)
    return P(S15, f"A point on the unit circle is at angle ${ltx(theta)}$ measured from the positive $x$-axis. Find its ${coord}$-coordinate.", 'numeric', plain(val), d=1,
             hints=["On the unit circle the point at angle $\\theta$ is $(\\cos\\theta, \\sin\\theta)$.", f"So you need ${'\\cos' if coord == 'x' else '\\sin'}\\left({ltx(theta)}\\right)$."],
             sol=[f"The point is $(\\cos{ltx(theta)}, \\sin{ltx(theta)})$.", f"The ${coord}$-coordinate is ${ltx(val)}$."],
             verify={'kind': 'numeric', 'value': f"{'cos' if coord == 'x' else 'sin'}({theta})"})

def uc_choice_angle(rng):
    fn = rng.choice(['sin', 'cos'])
    pool = [a for a in ANGLES if a not in (0,)]
    target = rng.choice(pool)
    v = FN[fn](target)
    others = [a for a in pool if FN[fn](a) != v]
    if len(others) < 3:
        return None
    opts = [(ltx(target), str(target))] + [(ltx(a), str(a)) for a in rng.sample(others, 3)]
    return choice(S15, f"Which angle $\\theta$ satisfies ${FNL[fn]}\\theta = {ltx(v)}$?", opts, 0, str(target), d=2, rng=rng,
                  hints=[f"{'Sine is the y-coordinate' if fn == 'sin' else 'Cosine is the x-coordinate'} on the unit circle; the sign tells you the possible quadrants.", "Compute the reference angle from the absolute value, then place it in the right quadrant."],
                  sol=[f"${ltx(v)}$ has reference angle ${ltx(min(sp.Mod(target, pi), pi - sp.Mod(target, pi)))}$ and the sign points to quadrant {'I II III IV'.split()[_quadrant(target) - 1]}.", f"${FNL[fn]}\\left({ltx(target)}\\right) = {ltx(v)}$."])

def uc_solve(rng):
    fn = rng.choice(['sin', 'cos'])
    v = rng.choice([R(1, 2), R(-1, 2), sqrt(3) / 2, -sqrt(3) / 2, sqrt(2) / 2, -sqrt(2) / 2])
    S = sp.solveset(sp.Eq(FN[fn](x), v), x, sp.Interval.Ropen(0, 2 * pi))
    sols = sorted(S, key=float)
    if len(sols) != 2:
        return None
    larger = rng.random() < 0.5
    val = sols[1] if larger else sols[0]
    return P(S15, f"Solve ${FNL[fn]}\\theta = {ltx(v)}$ for $0 \\le \\theta < 2\\pi$. There are two solutions; enter the {'larger' if larger else 'smaller'} one.", 'numeric', plain(val), d=3,
             hints=["Find the reference angle from the absolute value, then use the sign to pick two quadrants.", f"The two solutions are symmetric: for {'sine' if fn == 'sin' else 'cosine'} they are reflections across the ${'y' if fn == 'sin' else 'x'}$-axis."],
             sol=[f"Reference angle: ${ltx(min(sp.Mod(sols[0], pi), pi - sp.Mod(sols[0], pi)))}$.", f"Solutions in $[0, 2\\pi)$: ${ltx(sols[0])}$ and ${ltx(sols[1])}$.", f"The {'larger' if larger else 'smaller'} is ${ltx(val)}$."],
             verify={'kind': 'numeric', 'value': str(val)})

def uc_negative(rng):
    theta = -rng.choice([pi / 6, pi / 4, pi / 3, pi / 2, 2 * pi / 3, 3 * pi / 4, 5 * pi / 6, pi])
    fn = rng.choice(['sin', 'cos'])
    val = FN[fn](theta)
    return P(S15, f"Find the exact value of ${FNL[fn]}\\left({ltx(theta)}\\right)$.", 'numeric', plain(val), d=2,
             hints=["A negative angle is measured clockwise from the positive $x$-axis.", f"{'Sine is odd: $\\sin(-t) = -\\sin t$.' if fn == 'sin' else 'Cosine is even: $\\cos(-t) = \\cos t$.'}"],
             sol=[f"${FNL[fn]}({ltx(theta)}) = {'-' if fn == 'sin' else ''}{FNL[fn]}({ltx(-theta)})$.", f"$= {ltx(val)}$."],
             verify={'kind': 'numeric', 'value': f"{fn}({theta})"})

def uc_sign(rng):
    theta = rng.choice([a for a in ANGLES if a not in (0, pi / 2, pi, 3 * pi / 2)])
    fn = rng.choice(['sin', 'cos', 'tan'])
    s = int(sp.sign(FN[fn](theta)))
    opts = [('\\text{positive}', '1'), ('\\text{negative}', '-1'), ('\\text{zero}', '0')]
    idx = 0 if s > 0 else (1 if s < 0 else 2)
    return choice(S15, f"Without computing its value, decide whether ${FNL[fn]}\\left({ltx(theta)}\\right)$ is positive, negative, or zero.", opts, idx, s, d=1, rng=rng,
                  hints=["Find the quadrant first.", "Sine has the sign of $y$, cosine the sign of $x$, tangent the sign of $y/x$."],
                  sol=[f"${ltx(theta)}$ is in quadrant {'I II III IV'.split()[_quadrant(theta) - 1]}.", f"There ${FNL[fn]}$ is {'positive' if s > 0 else 'negative'}."])

def uc_reciprocal(rng):
    theta = rng.choice([a for a in ANGLES if a != 0])
    fn = rng.choice(['sec', 'csc', 'cot'])
    f = {'sec': sp.sec, 'csc': sp.csc, 'cot': sp.cot}[fn]
    val = f(theta)
    if val in (sp.zoo, sp.nan) or not val.is_finite:
        return None
    base = {'sec': 'cos', 'csc': 'sin', 'cot': 'tan'}[fn]
    return P(S15, f"Find the exact value of $\\{fn}\\left({ltx(theta)}\\right)$.", 'numeric', plain(sp.radsimp(val)), d=3,
             hints=[f"$\\{fn}\\theta = \\dfrac{{1}}{{\\{base}\\theta}}$.", f"First find $\\{base}\\left({ltx(theta)}\\right)$ from the unit circle, then take the reciprocal."],
             sol=[f"$\\{base}\\left({ltx(theta)}\\right) = {ltx(FN[base](theta))}$.", f"Reciprocal: ${ltx(sp.radsimp(val))}$."],
             verify={'kind': 'numeric', 'value': f"{fn}({theta})"})

FAM[S15] = [uc_exact, uc_degrees, uc_reference, uc_quadrant, uc_coterminal, uc_point, uc_choice_angle, uc_solve, uc_negative, uc_sign, uc_reciprocal]

# ================================================================ trig-identities
S16 = 'trig-identities'
# (latex, sympy string, answer plain, difficulty, which identity to mention)
IDENTITIES = [
    (r"\dfrac{1 - \cos^2 x}{\sin x}", "(1-cos(x)**2)/sin(x)", "sin(x)", 1, "Pythagorean: $1 - \\cos^2 x = \\sin^2 x$"),
    (r"\sin x \cdot \sec x", "sin(x)*sec(x)", "tan(x)", 1, "reciprocal: $\\sec x = 1/\\cos x$"),
    (r"\cos x \cdot \csc x", "cos(x)*csc(x)", "cot(x)", 1, "reciprocal: $\\csc x = 1/\\sin x$"),
    (r"\dfrac{1 - \sin^2 x}{\cos x}", "(1-sin(x)**2)/cos(x)", "cos(x)", 1, "Pythagorean: $1 - \\sin^2 x = \\cos^2 x$"),
    (r"(1 + \cos x)(1 - \cos x)", "(1+cos(x))*(1-cos(x))", "sin(x)^2", 1, "difference of squares, then Pythagorean"),
    (r"\dfrac{\sin^2 x}{1 - \cos x}", "sin(x)**2/(1-cos(x))", "1+cos(x)", 2, "write $\\sin^2 x = (1-\\cos x)(1+\\cos x)$"),
    (r"\sec x - \sin x \tan x", "sec(x)-sin(x)*tan(x)", "cos(x)", 3, "put everything over $\\cos x$"),
    (r"(1 + \tan^2 x)\cos^2 x", "(1+tan(x)**2)*cos(x)**2", "1", 2, "Pythagorean: $1 + \\tan^2 x = \\sec^2 x$"),
    (r"\dfrac{\sec^2 x - 1}{\tan^2 x}", "(sec(x)**2-1)/tan(x)**2", "1", 2, "Pythagorean: $\\sec^2 x - 1 = \\tan^2 x$"),
    (r"(\sec x - 1)(\sec x + 1)", "(sec(x)-1)*(sec(x)+1)", "tan(x)^2", 2, "difference of squares, then $\\sec^2 x - 1 = \\tan^2 x$"),
    (r"2\sin x\cos x", "2*sin(x)*cos(x)", "sin(2*x)", 1, "double angle: $\\sin 2x = 2\\sin x\\cos x$"),
    (r"\cos^2 x - \sin^2 x", "cos(x)**2-sin(x)**2", "cos(2*x)", 1, "double angle: $\\cos 2x = \\cos^2 x - \\sin^2 x$"),
    (r"\cos 2x + \sin^2 x", "cos(2*x)+sin(x)**2", "cos(x)^2", 2, "double angle: $\\cos 2x = \\cos^2 x - \\sin^2 x$"),
    (r"1 - \cos 2x", "1-cos(2*x)", "2*sin(x)^2", 2, "double angle: $\\cos 2x = 1 - 2\\sin^2 x$"),
    (r"\dfrac{\sin 2x}{\sin x}", "sin(2*x)/sin(x)", "2*cos(x)", 2, "double angle: $\\sin 2x = 2\\sin x\\cos x$"),
    (r"\dfrac{\sin 2x}{\cos x}", "sin(2*x)/cos(x)", "2*sin(x)", 2, "double angle: $\\sin 2x = 2\\sin x\\cos x$"),
    (r"(\sin x + \cos x)^2 - 1", "(sin(x)+cos(x))**2-1", "2*sin(x)*cos(x)", 2, "expand, use $\\sin^2 x + \\cos^2 x = 1$"),
    (r"\tan x + \cot x", "tan(x)+cot(x)", "1/(sin(x)*cos(x))", 3, "write both in terms of sine and cosine and add"),
    (r"\csc^2 x - \cot^2 x + \sin^2 x", "csc(x)**2-cot(x)**2+sin(x)**2", "1+sin(x)^2", 2, "Pythagorean: $\\csc^2 x - \\cot^2 x = 1$"),
    (r"\dfrac{\cos x}{1 - \sin x} - \tan x", "cos(x)/(1-sin(x))-tan(x)", "1/cos(x)", 3, "multiply the first fraction by $\\frac{1+\\sin x}{1+\\sin x}$"),
    (r"\dfrac{\tan x}{\sec x}", "tan(x)/sec(x)", "sin(x)", 2, "write both in terms of sine and cosine"),
    (r"\sin x \cot x", "sin(x)*cot(x)", "cos(x)", 1, "reciprocal: $\\cot x = \\cos x/\\sin x$"),
    (r"\cos^4 x - \sin^4 x", "cos(x)**4-sin(x)**4", "cos(2*x)", 3, "difference of squares, then Pythagorean and double angle"),
    (r"\dfrac{1 + \cos 2x}{2}", "(1+cos(2*x))/2", "cos(x)^2", 2, "double angle: $\\cos 2x = 2\\cos^2 x - 1$"),
    (r"\sec^2 x - \tan^2 x + \cos^2 x", "sec(x)**2-tan(x)**2+cos(x)**2", "1+cos(x)^2", 2, "Pythagorean: $\\sec^2 x - \\tan^2 x = 1$"),
]

def ti_simplify(rng):
    lt, ex, ans, d, hint = rng.choice(IDENTITIES)
    simp = parse_plain(ans)
    return P(S16, f"Simplify ${lt}$ as far as possible.", 'equiv', ans, d=d,
             hints=["Rewrite everything in terms of sine and cosine if you get stuck.", f"Useful identity here: {hint}."],
             sol=[f"Apply: {hint}.", f"The expression simplifies to ${ltx(simp)}$."],
             verify={'kind': 'equiv', 'expected': ex}, domain=(-3, 3))

def ti_double_from_ratio(rng):
    a, b, c = rng.choice(TRIPLES[:6])
    if rng.random() < 0.5:
        a, b = b, a
    quad = rng.choice(['I', 'II'])
    given_fn = rng.choice(['sin', 'cos'])
    want = rng.choice(['sin', 'cos', 'tan'])
    # sin theta = a/c (QI or QII: sin positive), cos theta = +-b/c
    s = R(a, c); co = R(b, c) * (1 if quad == 'I' else -1)
    if given_fn == 'cos':
        g = co; gstr = f"\\cos\\theta = {num(co)}"
        inner = f"acos({co})"
    else:
        g = s; gstr = f"\\sin\\theta = {num(s)}"
        inner = f"asin({s})" if quad == 'I' else f"pi-asin({s})"
    vals = {'sin': (2 * s * co, f"2*sin({inner})*cos({inner})"), 'cos': (co * co - s * s, f"cos(2*({inner}))"), 'tan': ((2 * s * co) / (co * co - s * s), f"tan(2*({inner}))")}
    val, vstr = vals[want]
    return P(S16, f"Suppose ${gstr}$ and $\\theta$ is in quadrant {quad}. Find ${FNL[want]} 2\\theta$.", 'numeric', fmt_num(val), d=2 if want != 'tan' else 3,
             hints=[f"First find the other ratio with $\\sin^2\\theta + \\cos^2\\theta = 1$; in quadrant {quad}, cosine is {'positive' if quad == 'I' else 'negative'}.",
                    {'sin': "$\\sin 2\\theta = 2\\sin\\theta\\cos\\theta$.", 'cos': "$\\cos 2\\theta = \\cos^2\\theta - \\sin^2\\theta$.", 'tan': "$\\tan 2\\theta = \\dfrac{\\sin 2\\theta}{\\cos 2\\theta}$."}[want]],
             sol=[f"$\\sin\\theta = {num(s)}$, $\\cos\\theta = {num(co)}$.", f"${FNL[want]} 2\\theta = {num(val)}$."],
             verify={'kind': 'numeric', 'value': vstr})

def ti_sum_angles(rng):
    deg = rng.choice([15, 75, 105, 165, 195, 255, 285, 345])
    fn = rng.choice(['sin', 'cos', 'tan'])
    use_rad = rng.random() < 0.4
    val = sp.simplify(FN[fn](deg * pi / 180))
    split = {15: (45, 30), 75: (45, 30), 105: (60, 45), 165: (120, 45), 195: (150, 45), 255: (210, 45), 285: (240, 45), 345: (300, 45)}[deg]
    op = '-' if deg == 15 else '+'
    arg = f"{deg}^\\circ" if not use_rad else ltx(deg * pi / 180)
    return P(S16, f"Use a sum or difference formula to find the exact value of ${FNL[fn]}\\left({arg}\\right)$.", 'numeric', plain(val), d=3 if fn == 'tan' else 2,
             hints=[f"Write ${deg}^\\circ = {split[0]}^\\circ {op} {split[1]}^\\circ$.",
                    {'sin': "$\\sin(A \\pm B) = \\sin A\\cos B \\pm \\cos A\\sin B$.", 'cos': "$\\cos(A \\pm B) = \\cos A\\cos B \\mp \\sin A\\sin B$.", 'tan': "$\\tan(A \\pm B) = \\dfrac{\\tan A \\pm \\tan B}{1 \\mp \\tan A\\tan B}$."}[fn]],
             sol=[f"${FNL[fn]}({deg}^\\circ) = {FNL[fn]}({split[0]}^\\circ {op} {split[1]}^\\circ)$; expand with the formula and substitute the special values.", f"$= {ltx(val)}$."],
             verify={'kind': 'numeric', 'value': f"{fn}({deg}*pi/180)"})

def ti_choice_identity(rng):
    kind = rng.choice(['cos2', 'sin2', 'sinsum', 'cosdiff', 'pyth'])
    a, b = symbols('a b')
    if kind == 'cos2':
        stmt, expected = "Which expression equals $\\cos 2x$?", "cos(2*x)"
        opts = [(r"\cos^2 x - \sin^2 x", "cos(x)**2-sin(x)**2"), (r"2\cos^2 x + 1", "2*cos(x)**2+1"), (r"1 - \cos^2 x", "1-cos(x)**2"), (r"2\sin x\cos x", "2*sin(x)*cos(x)")]
        why = "The double-angle formula: $\\cos 2x = \\cos^2 x - \\sin^2 x$ (also $2\\cos^2 x - 1$ or $1 - 2\\sin^2 x$)."
    elif kind == 'sin2':
        stmt, expected = "Which expression equals $\\sin 2x$?", "sin(2*x)"
        opts = [(r"2\sin x\cos x", "2*sin(x)*cos(x)"), (r"2\sin x", "2*sin(x)"), (r"\sin^2 x", "sin(x)**2"), (r"\sin x + \cos x", "sin(x)+cos(x)")]
        why = "The double-angle formula: $\\sin 2x = 2\\sin x\\cos x$. Note $\\sin 2x \\ne 2\\sin x$."
    elif kind == 'sinsum':
        stmt, expected = "Which expression equals $\\sin(a + b)$?", "sin(a+b)"
        opts = [(r"\sin a\cos b + \cos a\sin b", "sin(a)*cos(b)+cos(a)*sin(b)"), (r"\sin a + \sin b", "sin(a)+sin(b)"), (r"\sin a\cos b - \cos a\sin b", "sin(a)*cos(b)-cos(a)*sin(b)"), (r"\cos a\cos b - \sin a\sin b", "cos(a)*cos(b)-sin(a)*sin(b)")]
        why = "Addition formula: $\\sin(a+b) = \\sin a\\cos b + \\cos a\\sin b$."
    elif kind == 'cosdiff':
        stmt, expected = "Which expression equals $\\cos(a - b)$?", "cos(a-b)"
        opts = [(r"\cos a\cos b + \sin a\sin b", "cos(a)*cos(b)+sin(a)*sin(b)"), (r"\cos a\cos b - \sin a\sin b", "cos(a)*cos(b)-sin(a)*sin(b)"), (r"\cos a - \cos b", "cos(a)-cos(b)"), (r"\sin a\cos b - \cos a\sin b", "sin(a)*cos(b)-cos(a)*sin(b)")]
        why = "Subtraction formula: $\\cos(a-b) = \\cos a\\cos b + \\sin a\\sin b$ (plus sign for a difference)."
    else:
        stmt, expected = "Which expression equals $\\sec^2 x$?", "sec(x)**2"
        opts = [(r"1 + \tan^2 x", "1+tan(x)**2"), (r"1 - \tan^2 x", "1-tan(x)**2"), (r"1 + \cot^2 x", "1+cot(x)**2"), (r"\tan^2 x - 1", "tan(x)**2-1")]
        why = "Divide $\\sin^2 x + \\cos^2 x = 1$ by $\\cos^2 x$ to get $\\tan^2 x + 1 = \\sec^2 x$."
    return choice(S16, stmt, opts, 0, expected, d=1 if kind in ('sin2', 'cos2', 'pyth') else 2, rng=rng,
                  hints=["Test with a specific angle such as $x = \\pi/6$ (or $a = \\pi/2$, $b = 0$) to rule out wrong options.", why.split(':')[0] + " is the one you need."],
                  sol=[why, "The other options fail a numerical test."])

def ti_half_angle(rng):
    theta, lt = rng.choice([(pi / 8, r"\frac{\pi}{8}"), (pi / 12, r"\frac{\pi}{12}"), (3 * pi / 8, r"\frac{3\pi}{8}"), (5 * pi / 12, r"\frac{5\pi}{12}")])
    fn = rng.choice(['sin', 'cos'])
    val = sp.sqrtdenest(sp.simplify(FN[fn](theta)))
    double = 2 * theta
    return P(S16, f"Use a half-angle formula to find the exact value of ${FNL[fn]}\\left({lt}\\right)$.", 'numeric', plain(val), d=3,
             hints=[f"${lt}$ is half of ${ltx(double)}$, whose cosine you know.", "$\\sin^2\\tfrac{u}{2} = \\dfrac{1 - \\cos u}{2}$ and $\\cos^2\\tfrac{u}{2} = \\dfrac{1 + \\cos u}{2}$; take the positive root in quadrant I."],
             sol=[f"$\\cos\\left({ltx(double)}\\right) = {ltx(cos(double))}$.", f"${FNL[fn]}\\left({lt}\\right) = \\sqrt{{\\dfrac{{1 {'-' if fn == 'sin' else '+'} {ltx(cos(double))}}}{{2}}}} = {ltx(val)}$."],
             verify={'kind': 'numeric', 'value': f"{fn}({theta})"})

def ti_rewrite(rng):
    kind = rng.choice(['cos2sin', 'cos2cos', 'sin2', 'tan'])
    if kind == 'cos2sin':
        stmt, ans, ex = "Write $\\cos 2x$ in terms of $\\sin x$ only.", "1-2*sin(x)^2", "cos(2*x)"
        sol = ["$\\cos 2x = \\cos^2 x - \\sin^2 x$ and $\\cos^2 x = 1 - \\sin^2 x$.", "So $\\cos 2x = 1 - 2\\sin^2 x$."]
    elif kind == 'cos2cos':
        stmt, ans, ex = "Write $\\cos 2x$ in terms of $\\cos x$ only.", "2*cos(x)^2-1", "cos(2*x)"
        sol = ["$\\cos 2x = \\cos^2 x - \\sin^2 x$ and $\\sin^2 x = 1 - \\cos^2 x$.", "So $\\cos 2x = 2\\cos^2 x - 1$."]
    elif kind == 'sin2':
        stmt, ans, ex = "Write $\\sin 2x \\cdot \\sec x$ in terms of $\\sin x$ only.", "2*sin(x)", "sin(2*x)*sec(x)"
        sol = ["$\\sin 2x = 2\\sin x\\cos x$ and $\\sec x = 1/\\cos x$.", "The cosines cancel: $2\\sin x$."]
    else:
        stmt, ans, ex = "Write $\\tan x \\cdot \\cos x$ in terms of $\\sin x$ only.", "sin(x)", "tan(x)*cos(x)"
        sol = ["$\\tan x = \\sin x/\\cos x$.", "Multiplying by $\\cos x$ leaves $\\sin x$."]
    return P(S16, stmt, 'equiv', ans, d=2,
             hints=["Start from a form of the identity that contains both sine and cosine, then eliminate the one you do not want using $\\sin^2 x + \\cos^2 x = 1$ or a reciprocal identity.", sol[0]],
             sol=sol, verify={'kind': 'equiv', 'expected': ex})

def ti_from_tan(rng):
    t = rng.choice([2, 3, R(1, 2), R(3, 4), R(4, 3), 1, R(5, 12)])
    quad = rng.choice(['I', 'III'])
    want = rng.choice(['sec', 'sin', 'cos'])
    inner = f"atan({t})" + ("+pi" if quad == 'III' else "")
    sign = 1 if quad == 'I' else -1
    vals = {'sec': (sign * sqrt(1 + t * t), f"sec({inner})"), 'sin': (sign * t / sqrt(1 + t * t), f"sin({inner})"), 'cos': (sign / sqrt(1 + t * t), f"cos({inner})")}
    val, vstr = vals[want]
    val = sp.radsimp(sp.simplify(val))
    return P(S16, f"Suppose $\\tan\\theta = {num(t)}$ and $\\theta$ is in quadrant {quad}. Find $\\{want}\\theta$ exactly.", 'numeric', plain(val), d=2 if want == 'sec' else 3,
             hints=["Use $1 + \\tan^2\\theta = \\sec^2\\theta$ to get $\\sec\\theta$ up to sign.", f"In quadrant {quad}, cosine (and secant) is {'positive' if quad == 'I' else 'negative'}."],
             sol=[f"$\\sec^2\\theta = 1 + ({num(t)})^2 = {num(1 + t * t)}$, so $\\sec\\theta = {'' if quad == 'I' else '-'}{ltx(sqrt(1 + t * t))}$.",
                  f"Then $\\cos\\theta = 1/\\sec\\theta$ and $\\sin\\theta = \\tan\\theta\\cos\\theta$. The requested value is ${ltx(val)}$."],
             verify={'kind': 'numeric', 'value': vstr})

FAM[S16] = [ti_simplify, ti_double_from_ratio, ti_sum_angles, ti_choice_identity, ti_half_angle, ti_rewrite, ti_from_tan, ti_simplify, ti_simplify, ti_choice_identity]

# ================================================================ trig-graphs
S17 = 'trig-graphs'

def _sinusoid(rng, allow_phase=True):
    A = rng.choice([1, 2, 3, 4, 5, -2, -3, R(1, 2)])
    B = rng.choice([1, 2, 3, 4, R(1, 2), R(1, 3), pi])
    C = rng.choice([0, 0, pi / 2, -pi / 3, pi / 4, -pi / 6, 1]) if allow_phase else 0
    D = rng.choice([0, 0, 1, -2, 3, 5, -1])
    fn = rng.choice([sin, cos])
    expr = A * fn(B * x + C) + D
    return A, B, C, D, fn, expr

def tg_amplitude(rng):
    A, B, C, D, fn, expr = _sinusoid(rng)
    return P(S17, f"Find the amplitude of $y = {ltx(expr)}$.", 'numeric', fmt_num(abs(A)), d=1,
             hints=["Amplitude is half the distance between the maximum and minimum values.", "For $y = A\\sin(Bx + C) + D$ it is $|A|$."],
             sol=[f"The coefficient in front of the trig function is ${num(A)}$.", f"Amplitude $= |{num(A)}| = {num(abs(A))}$."],
             verify={'kind': 'numeric', 'value': f"Abs({A})"})

def tg_period(rng):
    A, B, C, D, fn, expr = _sinusoid(rng)
    per = sp.periodicity(expr, x)
    return P(S17, f"Find the period of $y = {ltx(expr)}$.", 'numeric', plain(per), d=1 if B in (1, 2) else 2,
             hints=["The basic sine and cosine have period $2\\pi$.", "For $y = A\\sin(Bx + C) + D$ the period is $2\\pi/|B|$."],
             sol=[f"$B = {num(B)}$.", f"Period $= \\dfrac{{2\\pi}}{{{num(B)}}} = {ltx(per)}$."],
             verify={'kind': 'numeric', 'value': f"periodicity({expr}, x)"})

def tg_period_tan(rng):
    B = rng.choice([1, 2, 3, R(1, 2), 4, pi])
    expr = tan(B * x)
    per = sp.periodicity(expr, x)
    opts = [(ltx(per), str(per)), (ltx(2 * per), str(2 * per)), (ltx(per / 2), str(per / 2)), (ltx(4 * per), str(4 * per))]
    return choice(S17, f"What is the period of $y = {ltx(expr)}$?", opts, 0, f"periodicity(tan({B}*x), x)", d=2, rng=rng,
                  hints=["The basic tangent repeats every $\\pi$, not $2\\pi$.", "For $y = \\tan(Bx)$ the period is $\\pi/|B|$."],
                  sol=[f"$B = {num(B)}$, so the period is $\\pi/{num(B)}$.", f"$= {ltx(per)}$."])

def tg_midline_extremes(rng):
    A, B, C, D, fn, expr = _sinusoid(rng)
    kind = rng.choice(['mid', 'max', 'min'])
    val = {'mid': D, 'max': D + abs(A), 'min': D - abs(A)}[kind]
    q = {'mid': "What is the midline $y = ?$ (enter the constant)", 'max': "What is the maximum value of $y$", 'min': "What is the minimum value of $y$"}[kind]
    return P(S17, f"Consider $y = {ltx(expr)}$. {q}?", 'numeric', fmt_num(val), d=1 if kind == 'mid' else 2,
             hints=["The vertical shift $D$ is the midline; the graph swings $|A|$ above and below it.", f"Here $D = {D}$ and $|A| = {num(abs(A))}$."],
             sol=[f"Midline $y = {D}$, amplitude ${num(abs(A))}$.", {'mid': f"So the midline is $y = {D}$.", 'max': f"Maximum $= {D} + {num(abs(A))} = {num(val)}$.", 'min': f"Minimum $= {D} - {num(abs(A))} = {num(val)}$."}[kind]],
             verify={'kind': 'numeric', 'value': {'mid': f"{D}", 'max': f"{D}+Abs({A})", 'min': f"{D}-Abs({A})"}[kind]})

def tg_phase(rng):
    A = rng.choice([1, 2, 3])
    B = rng.choice([1, 2, 3, R(1, 2)])
    h = rng.choice([pi / 2, pi / 3, pi / 4, pi / 6, -pi / 4, -pi / 6, -pi / 3, 2])
    fn = rng.choice([sin, cos])
    factored = rng.random() < 0.5
    if factored:
        expr_l = f"{num(A) if A != 1 else ''}\\{fn.__name__}\\left({num(B) if B != 1 else ''}\\left({ltx(x - h)}\\right)\\right)"
        C = -B * h
    else:
        C = -B * h
        expr_l = ltx(A * fn(B * x + C))
    return P(S17, f"By how many units is the graph of $y = {expr_l}$ shifted horizontally compared with $y = \\{fn.__name__}({num(B) if B != 1 else ''}x)$? Enter a positive number for a shift to the right, negative for a shift to the left.",
             'numeric', plain(h), d=2 if factored else 3,
             hints=["Factor the inside so it reads $B(x - h)$; the shift is $h$.", "If the inside is $Bx + C$, the shift is $-C/B$." if not factored else "The inside is already factored: read $h$ directly (watch the sign)."],
             sol=[f"Inside: ${ltx(B * (x - h))}$ $= {num(B) if B != 1 else ''}\\left({ltx(x - h)}\\right)$.", f"So the shift is $h = {ltx(h)}$ ({'right' if h > 0 else 'left'})."],
             verify={'kind': 'numeric', 'value': f"-({C})/({B})"})

def tg_choice_build(rng):
    A = rng.choice([2, 3, 4, 5])
    per = rng.choice([pi, 2 * pi, pi / 2, 4 * pi, pi / 3])
    B = 2 * pi / per
    fn = rng.choice([sin, cos])
    good = A * fn(B * x)
    cands = [good, B * fn(A * x) if A != B else A * fn(2 * B * x), A * fn(x / B) if B != 1 else A * fn(3 * x), fn(B * x), A * fn(B * x) + A]
    opts, seen = [], set()
    for c_ in cands:
        s = plain(c_)
        if s not in seen:
            seen.add(s); opts.append((f"y = {ltx(c_)}", s))
    if len(opts) < 4:
        return None
    return choice(S17, f"Which function has amplitude ${A}$, period ${ltx(per)}$, and midline $y = 0$?", opts[:4], 0, str(good), d=2, rng=rng,
                  hints=["Amplitude is the coefficient in front; period is $2\\pi/B$.", f"Solve $2\\pi/B = {ltx(per)}$ for $B$: $B = {num(B)}$."],
                  sol=[f"$|A| = {A}$ and $B = 2\\pi/{ltx(per)} = {num(B)}$.", f"So $y = {ltx(good)}$ (no vertical shift keeps the midline at $0$)."])

def tg_evaluate(rng):
    A, B, C, D, fn, expr = _sinusoid(rng, allow_phase=False)
    at = rng.choice([0, pi / 6, pi / 4, pi / 3, pi / 2, pi, 3 * pi / 2, 2 * pi])
    val = sp.nsimplify(expr.subs(x, at))
    if not val.is_number:
        return None
    return P(S17, f"If $y = {ltx(expr)}$, find $y$ when $x = {ltx(at)}$. Give an exact value.", 'numeric', plain(val), d=1,
             hints=[f"Substitute $x = {ltx(at)}$ into the formula.", f"First compute $\\{fn.__name__}\\left({ltx(B * at)}\\right)$ from the unit circle."],
             sol=[f"$\\{fn.__name__}\\left({ltx(B * at)}\\right) = {ltx(fn(B * at))}$.", f"$y = {num(A)}\\cdot{ltx(fn(B * at))} + ({D}) = {ltx(val)}$."],
             verify={'kind': 'evaluate', 'expr': str(expr), 'at': str(at)})

def tg_choice_describe(rng):
    fn = rng.choice([sin, cos])
    h, kk = rng.choice([pi / 4, pi / 3, pi / 6, pi / 2]), rng.choice([1, 2, -1, -3, 4])
    good = fn(x - h) + kk
    def d_(hh, kkk):
        return f"\\text{{right }}{ltx(hh)}\\text{{, {'up' if kkk > 0 else 'down'} {abs(kkk)}}}" if hh > 0 else f"\\text{{left }}{ltx(-hh)}\\text{{, {'up' if kkk > 0 else 'down'} {abs(kkk)}}}"
    opts = [(d_(h, kk), str(good)), (d_(-h, kk), str(fn(x + h) + kk)), (d_(h, -kk), str(fn(x - h) - kk)), (d_(-h, -kk), str(fn(x + h) - kk))]
    return choice(S17, f"Compared with $y = \\{fn.__name__} x$, how is the graph of $y = {ltx(good)}$ shifted?", opts, 0, str(good), d=2, rng=rng,
                  hints=["$x - h$ inside shifts right by $h$; a constant added outside shifts up.", "Horizontal shifts feel backwards: $x - \\pi/4$ moves the graph to the right."],
                  sol=[f"Inside: $x - {ltx(h)}$ means right by ${ltx(h)}$.", f"Outside: $+({kk})$ means {'up' if kk > 0 else 'down'} by ${abs(kk)}$."],
                  extra_verify={'note': 'each option plain is the equation that description would produce'})

def tg_cycles(rng):
    B = rng.choice([2, 3, 4, 5, 6, R(1, 2)])
    fn = rng.choice([sin, cos])
    val = 2 * pi / sp.periodicity(fn(B * x), x)
    return P(S17, f"How many complete cycles does $y = {ltx(fn(B * x))}$ make on the interval $[0, 2\\pi]$?", 'numeric', fmt_num(val), d=2,
             hints=["Find the period first.", "Number of cycles on $[0, 2\\pi]$ is $2\\pi$ divided by the period, which equals $|B|$."],
             sol=[f"Period $= 2\\pi/{num(B)} = {ltx(sp.periodicity(fn(B * x), x))}$.", f"Cycles in $[0, 2\\pi]$: $2\\pi \\div {ltx(sp.periodicity(fn(B * x), x))} = {num(val)}$."],
             verify={'kind': 'numeric', 'value': f"2*pi/periodicity({fn(B * x)}, x)"})

def tg_first_zero(rng):
    A = rng.choice([1, 2, 3])
    B = rng.choice([1, 2, 3, R(1, 2)])
    fn = rng.choice([sin, cos])
    expr = A * fn(B * x)
    S = sp.solveset(sp.Eq(expr, 0), x, sp.Interval.Lopen(0, 4 * pi))
    val = S.inf
    return P(S17, f"Find the smallest positive $x$ at which $y = {ltx(expr)}$ crosses the $x$-axis.", 'numeric', plain(val), d=3,
             hints=[f"$\\{fn.__name__}$ is zero first at ${ltx(pi) if fn == sin else ltx(pi / 2)}$ (for positive input).", f"Set ${num(B)}x$ equal to that and solve."],
             sol=[f"${num(B)}x = {ltx(pi) if fn == sin else ltx(pi / 2)}$.", f"$x = {ltx(val)}$."],
             verify={'kind': 'numeric', 'value': str(val)})

def tg_extreme_location(rng):
    fn = rng.choice([sin, cos])
    B = rng.choice([1, 2, R(1, 2)])
    which = rng.choice(['max', 'min'])
    expr = fn(B * x)
    pts = [sp.nsimplify(t) for t in [sp.Rational(i, 12) * pi for i in range(0, 49)]]
    vals = [(expr.subs(x, t), t) for t in pts]
    target = 1 if which == 'max' else -1
    cands = [t for v, t in vals if v == target and t > 0]
    if not cands:
        return None
    val = min(cands)
    return P(S17, f"Find the smallest positive $x$ at which $y = {ltx(expr)}$ reaches its {'maximum' if which == 'max' else 'minimum'} value.", 'numeric', plain(val), d=2,
             hints=[f"$\\{fn.__name__}$ equals ${target}$ first at ${ltx(pi / 2 if (fn == sin and which == 'max') else (3 * pi / 2 if fn == sin else (2 * pi if which == 'max' else pi)))}$ for positive input.", f"Set ${num(B)}x$ equal to that and solve."],
             sol=[f"${num(B)}x = {ltx(val * B)}$.", f"$x = {ltx(val)}$."],
             verify={'kind': 'numeric', 'value': str(val)})

FAM[S17] = [tg_amplitude, tg_period, tg_period_tan, tg_midline_extremes, tg_phase, tg_choice_build, tg_evaluate, tg_choice_describe, tg_cycles, tg_first_zero, tg_extreme_location]

RAMP_SKILLS = [S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, S14, S15, S16, S17]

def build() -> dict[str, list[dict]]:
    return {skill: run(skill, FAM[skill], target=64) for skill in RAMP_SKILLS}
