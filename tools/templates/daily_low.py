"""
Daily Integral tiers 0-2 (the geometry-and-sums ladder that comes before antiderivatives).

tier 0 -> area under lines by geometry        (owning node: area-by-geometry)
tier 1 -> sigma notation and small Riemann sums (owning node: areas-and-distances)
tier 2 -> definite integrals of constants, lines, |x| and semicircles by geometry, incl. signed area (owning node: definite-integral)

build() returns {'daily-tier-0': [...], 'daily-tier-1': [...], 'daily-tier-2': [...]}; generate_problems.py maps each key to its
owning skill and writes data/problems/daily-tier-<n>.json. Every problem carries tier and tags=['daily'].
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sympy as sp
from sympy import Rational as R, sqrt, pi, Abs
from problemkit import make_problem, plain, ltx, fmt_num, x
from ramp import run, nz, num, lin, frac

TIER_SKILL = {0: 'area-by-geometry', 1: 'areas-and-distances', 2: 'definite-integral'}
k = sp.Symbol('k')

def D(tier, stmt, checker, answer, *, d, hints, sol, verify, **kw):
    return make_problem(TIER_SKILL[tier], stmt, checker, answer, difficulty=d, hints=hints, solution=sol, verify=verify, tier=tier, tags=['daily'], **kw)

def under(expr_l, a, b):
    return f"Find the area of the region under $y = {expr_l}$ and above the $x$-axis from $x = {a}$ to $x = {b}$."

# ================================================================ tier 0: area under lines by geometry

def t0_rect(rng):
    c, a = rng.randint(1, 12), rng.randint(-5, 6)
    b = a + rng.randint(1, 9)
    return D(0, under(str(c), a, b), 'numeric', str(c * (b - a)), d=1,
             hints=["A constant function is a horizontal line, so the region is a rectangle.", f"Width ${b} - ({a})$, height ${c}$."],
             sol=[f"Width $= {b} - ({a}) = {b - a}$, height $= {c}$.", f"Area $= {b - a}\\cdot{c} = {c * (b - a)}$."],
             verify={'kind': 'definite', 'integrand': str(c), 'a': str(a), 'b': str(b)})

def t0_tri_origin(rng):
    m, b = rng.choice([1, 2, 3, 4, 5, R(1, 2), R(3, 2), R(2, 3)]), rng.randint(1, 9)
    val = m * b * b / 2
    return D(0, under(ltx(m * x), 0, b), 'numeric', fmt_num(val), d=1,
             hints=["The line passes through the origin, so the region is a right triangle.", f"Base ${b}$; height is the $y$-value at $x = {b}$."],
             sol=[f"Height at $x = {b}$: $y = {num(m * b)}$.", f"Area $= \\tfrac12\\cdot{b}\\cdot{num(m * b)} = {num(val)}$."],
             verify={'kind': 'definite', 'integrand': f"({m})*x", 'a': '0', 'b': str(b)})

def t0_tri_shifted(rng):
    m, a = rng.choice([1, 2, 3, R(1, 2), R(3, 2)]), rng.randint(-4, 5)
    b = a + rng.randint(1, 7)
    expr = sp.expand(m * (x - a))
    val = m * (b - a) ** 2 / 2
    return D(0, under(ltx(expr), a, b), 'numeric', fmt_num(val), d=2,
             hints=[f"The line crosses the $x$-axis at $x = {a}$, the left end of the interval, so the region is a triangle.", f"Base ${b - a}$, height $y({b}) = {num(m * (b - a))}$."],
             sol=[f"$y({a}) = 0$ and $y({b}) = {num(m * (b - a))}$.", f"Area $= \\tfrac12\\cdot{b - a}\\cdot{num(m * (b - a))} = {num(val)}$."],
             verify={'kind': 'definite', 'integrand': str(expr), 'a': str(a), 'b': str(b)})

def t0_trap(rng):
    m, c = rng.choice([1, 2, 3, R(1, 2), R(3, 2), -1, -2, R(-1, 2)]), rng.randint(1, 12)
    a = rng.randint(-4, 5); b = a + rng.randint(1, 7)
    ya, yb = m * a + c, m * b + c
    if ya <= 0 or yb <= 0:
        return None
    val = (ya + yb) * (b - a) / 2
    return D(0, under(lin(m, c), a, b), 'numeric', fmt_num(val), d=2,
             hints=["The region is a trapezoid whose parallel sides are the heights at the two ends.", f"$y({a}) = {num(ya)}$, $y({b}) = {num(yb)}$, width ${b - a}$."],
             sol=[f"$y({a}) = {num(ya)}$ and $y({b}) = {num(yb)}$.", f"Area $= \\dfrac{{{num(ya)} + {num(yb)}}}{{2}}\\cdot{b - a} = {num(val)}$."],
             verify={'kind': 'definite', 'integrand': f"({m})*x+({c})", 'a': str(a), 'b': str(b)})

def t0_abs(rng):
    kind = rng.choice(['v', 'shift', 'tent'])
    if kind == 'v':
        a, b = rng.randint(1, 6), rng.randint(1, 7)
        val = R(a * a + b * b, 2)
        return D(0, under('|x|', -a, b), 'numeric', fmt_num(val), d=3,
                 hints=["$|x|$ makes a V shape; split the region at $x = 0$ into two right triangles.", f"Left triangle: legs ${a}$ and ${a}$. Right triangle: legs ${b}$ and ${b}$."],
                 sol=[f"Left: $\\tfrac12\\cdot{a}^2 = {num(R(a * a, 2))}$. Right: $\\tfrac12\\cdot{b}^2 = {num(R(b * b, 2))}$.", f"Total: ${num(val)}$."],
                 verify={'kind': 'definite', 'integrand': 'Abs(x)', 'a': str(-a), 'b': str(b)})
    if kind == 'shift':
        c = rng.randint(-3, 6); a = c - rng.randint(1, 5); b = c + rng.randint(1, 5)
        val = R((c - a) ** 2 + (b - c) ** 2, 2)
        return D(0, under(ltx(Abs(x - c)), a, b), 'numeric', fmt_num(val), d=3,
                 hints=[f"The V has its corner at $x = {c}$; split there.", f"Two right triangles with legs ${c - a}$ and ${b - c}$."],
                 sol=[f"Left triangle: $\\tfrac12\\cdot{c - a}^2 = {num(R((c - a) ** 2, 2))}$. Right: $\\tfrac12\\cdot{b - c}^2 = {num(R((b - c) ** 2, 2))}$.", f"Total: ${num(val)}$."],
                 verify={'kind': 'definite', 'integrand': f"Abs(x-({c}))", 'a': str(a), 'b': str(b)})
    c = rng.randint(1, 8)
    val = c * c
    return D(0, under(ltx(c - Abs(x)), -c, c), 'numeric', str(val), d=3,
             hints=["This is an upside-down V (a tent) with its peak on the $y$-axis.", f"Base from $-{c}$ to ${c}$, height ${c}$: one triangle."],
             sol=[f"Peak at $(0, {c})$; the line hits the axis at $x = \\pm{c}$.", f"Area $= \\tfrac12\\cdot{2 * c}\\cdot{c} = {val}$."],
             verify={'kind': 'definite', 'integrand': f"{c}-Abs(x)", 'a': str(-c), 'b': str(c)})

def t0_piecewise(rng):
    kind = rng.choice(['roof', 'plateau'])
    if kind == 'roof':
        m, c = rng.choice([1, 2, R(1, 2)]), rng.randint(2, 6)
        h = m * c
        f1, f2 = m * x, sp.expand(2 * h - m * x)
        val = h * c
        return D(0, f"Let $y = \\begin{{cases}} {ltx(f1)} & 0 \\le x \\le {c} \\\\ {ltx(f2)} & {c} < x \\le {2 * c} \\end{{cases}}$. Find the area under this graph from $x = 0$ to $x = {2 * c}$.",
                 'numeric', fmt_num(val), d=3,
                 hints=["Sketch both pieces: together they form a triangle with its peak in the middle.", f"Peak at $x = {c}$ with height ${num(h)}$; base ${2 * c}$."],
                 sol=[f"Height at $x = {c}$: ${num(h)}$. Base: ${2 * c}$.", f"Area $= \\tfrac12\\cdot{2 * c}\\cdot{num(h)} = {num(val)}$."],
                 verify={'kind': 'definite', 'integrand': f"Piecewise(({f1}, x<={c}), ({f2}, True))", 'a': '0', 'b': str(2 * c)})
    m, c, w = rng.choice([1, 2, 3]), rng.randint(2, 6), rng.randint(1, 5)
    xc = R(c, m)
    f1, f2 = m * x, sp.Integer(c)
    b = xc + w
    val = c * xc / 2 + c * w
    return D(0, f"Let $y = \\begin{{cases}} {ltx(f1)} & 0 \\le x \\le {num(xc)} \\\\ {c} & {num(xc)} < x \\le {num(b)} \\end{{cases}}$. Find the area under this graph from $x = 0$ to $x = {num(b)}$.",
             'numeric', fmt_num(val), d=3,
             hints=["The graph rises along a line, then stays flat: a triangle followed by a rectangle.", f"Triangle: base ${num(xc)}$, height ${c}$. Rectangle: width ${w}$, height ${c}$."],
             sol=[f"Triangle: $\\tfrac12\\cdot{num(xc)}\\cdot{c} = {num(c * xc / 2)}$.", f"Rectangle: ${w}\\cdot{c} = {c * w}$.", f"Total: ${num(val)}$."],
             verify={'kind': 'definite', 'integrand': f"Piecewise(({f1}, x<={xc}), ({c}, True))", 'a': '0', 'b': str(b)})

def t0_two_points(rng):
    x1, y1 = rng.randint(-2, 3), rng.randint(1, 8)
    x2, y2 = x1 + rng.randint(2, 7), rng.randint(1, 8)
    if y1 == y2:
        return None
    m = R(y2 - y1, x2 - x1)
    val = R(y1 + y2, 2) * (x2 - x1)
    return D(0, f"A line passes through $({x1}, {y1})$ and $({x2}, {y2})$. Find the area under the line and above the $x$-axis from $x = {x1}$ to $x = {x2}$.", 'numeric', fmt_num(val), d=2,
             hints=["The two points are the top corners of a trapezoid.", f"Parallel sides ${y1}$ and ${y2}$, width ${x2 - x1}$."],
             sol=[f"Trapezoid with heights ${y1}$, ${y2}$ and width ${x2 - x1}$.", f"Area $= \\dfrac{{{y1} + {y2}}}{{2}}\\cdot{x2 - x1} = {num(val)}$."],
             verify={'kind': 'definite', 'integrand': f"{y1}+({m})*(x-({x1}))", 'a': str(x1), 'b': str(x2)})

def t0_decreasing_to_zero(rng):
    c, b = rng.randint(2, 10), rng.randint(1, 8)
    m = R(c, b)
    expr = c - m * x
    val = R(c * b, 2)
    return D(0, under(ltx(expr), 0, b), 'numeric', fmt_num(val), d=2,
             hints=[f"The line starts at height ${c}$ and reaches the $x$-axis at $x = {b}$.", "That makes a right triangle with the axes."],
             sol=[f"$y(0) = {c}$ and $y({b}) = 0$.", f"Area $= \\tfrac12\\cdot{b}\\cdot{c} = {num(val)}$."],
             verify={'kind': 'definite', 'integrand': str(expr), 'a': '0', 'b': str(b)})

T0 = [t0_rect, t0_tri_origin, t0_tri_shifted, t0_trap, t0_abs, t0_piecewise, t0_two_points, t0_decreasing_to_zero, t0_trap]

# ================================================================ tier 1: sigma notation and Riemann sums

RS_FUNCS = [(x ** 2, 0, 3), (x ** 2 + 1, 0, 2), (2 * x + 1, 0, 4), (x ** 3, 0, 2), (4 - x ** 2, 0, 2), (x ** 2, 1, 3), (1 / x, 1, 3), (6 - x, 0, 4), (x ** 2 - x, 1, 3), (sqrt(x), 0, 4)]

def t1_riemann(rng):
    f, a, b = rng.choice(RS_FUNCS)
    n = rng.choice([2, 3, 4, 5])
    rule = rng.choice(['left', 'right', 'midpoint'])
    dx = R(b - a, n)
    off = {'left': 0, 'right': dx, 'midpoint': dx / 2}[rule]
    pts = [a + j * dx + off for j in range(n)]
    heights = [f.subs(x, t) for t in pts]
    if any(not h.is_rational for h in heights):
        return None
    val = sum(heights) * dx
    word = {'left': 'left-endpoint', 'right': 'right-endpoint', 'midpoint': 'midpoint'}[rule]
    linear = f.is_polynomial(x) and sp.degree(f, x) <= 1
    d = 3 if (rule == 'midpoint' or f in (1 / x, sqrt(x)) or n >= 5) else (1 if (linear and n <= 3) else 2)
    return D(1, f"Approximate the area under $f(x) = {ltx(f)}$ on $[{a}, {b}]$ using the {word} Riemann sum with $n = {n}$ rectangles. Give an exact answer.",
             'numeric', fmt_num(val), d=d,
             hints=[f"$\\Delta x = \\dfrac{{{b} - {a}}}{{{n}}} = {num(dx)}$; the sample points are ${', '.join(num(t) for t in pts)}$.",
                    "Sum $f$ at the sample points, then multiply by $\\Delta x$."],
             sol=[f"$\\Delta x = {num(dx)}$, sample points ${', '.join(num(t) for t in pts)}$.",
                  f"Heights: ${' + '.join(num(h) for h in heights)} = {num(sum(heights))}$.",
                  f"Sum $= {num(dx)}\\cdot{num(sum(heights))} = {num(val)}$."],
             verify={'kind': 'numeric', 'value': f"summation(({f}).subs(x, {a}+k*({dx})+({off})), (k,0,{n - 1}))*({dx})"})

def t1_sigma(rng):
    kind = rng.choice(['lin', 'sq', 'cube', 'alt', 'const', 'frac'])
    n = rng.randint(3, 6)
    lo = 1
    if kind == 'lin':
        a_, b_ = rng.choice([2, 3, 4]), rng.randint(-3, 3); term, sym = ltx(a_ * x + b_).replace('x', 'k'), f"{a_}*k+({b_})"
    elif kind == 'sq':
        term, sym = 'k^2', 'k**2'
    elif kind == 'cube':
        term, sym, n = 'k^3', 'k**3', rng.randint(2, 4)
    elif kind == 'alt':
        term, sym = '(-1)^k k^2', '(-1)**k*k**2'
    elif kind == 'const':
        c = rng.choice([2, 5, 7]); term, sym, n = str(c), str(c), rng.randint(4, 9)
    else:
        term, sym, n, lo = r'\frac{1}{k(k+1)}', '1/(k*(k+1))', rng.randint(3, 5), 1
    val = sp.summation(sp.sympify(sym), (k, lo, n))
    terms = [sp.sympify(sym).subs(k, j) for j in range(lo, n + 1)]
    return D(1, f"Evaluate $\\displaystyle\\sum_{{k={lo}}}^{{{n}}} {term}$." + (" Give an exact fraction." if kind == 'frac' else ""), 'numeric', fmt_num(val), d=1 if kind in ('lin', 'const') else (3 if kind in ('alt', 'frac') else 2),
             hints=[f"Substitute $k = {lo}, \\ldots, {n}$ and add.", "Write every term before adding; watch signs." if kind == 'alt' else f"The first term is ${num(terms[0])}$."],
             sol=[f"Terms: ${' + '.join(f'({num(t)})' if t < 0 else num(t) for t in terms)}$.", f"Sum $= {num(val)}$."],
             verify={'kind': 'numeric', 'value': f"summation({sym},(k,{lo},{n}))"})

def t1_dx(rng):
    a = rng.randint(-3, 4); b = a + rng.randint(1, 9); n = rng.choice([2, 3, 4, 5, 6, 8, 10])
    val = R(b - a, n)
    return D(1, f"The interval $[{a}, {b}]$ is divided into $n = {n}$ equal subintervals for a Riemann sum. What is the width $\\Delta x$ of each subinterval?", 'numeric', fmt_num(val), d=1,
             hints=["$\\Delta x = \\dfrac{b - a}{n}$.", f"$\\dfrac{{{b} - ({a})}}{{{n}}}$."],
             sol=[f"$\\Delta x = \\dfrac{{{b} - ({a})}}{{{n}}} = \\dfrac{{{b - a}}}{{{n}}}$.", f"$= {num(val)}$."],
             verify={'kind': 'numeric', 'value': f"({b}-({a}))/{n}"})

def t1_sample_point(rng):
    a = rng.randint(-2, 3); b = a + rng.randint(2, 8); n = rng.choice([3, 4, 5, 6])
    i = rng.randint(1, n)
    rule = rng.choice(['right', 'left', 'midpoint'])
    dx = R(b - a, n)
    val = {'right': a + i * dx, 'left': a + (i - 1) * dx, 'midpoint': a + (i - R(1, 2)) * dx}[rule]
    name = {'right': f"the right endpoint $x_{{{i}}}$", 'left': f"the left endpoint $x_{{{i - 1}}}$", 'midpoint': f"the midpoint $\\bar{{x}}_{{{i}}}$"}[rule]
    return D(1, f"For a Riemann sum on $[{a}, {b}]$ with $n = {n}$ equal subintervals, find {name} of the {['first', 'second', 'third', 'fourth', 'fifth', 'sixth'][i - 1]} subinterval.",
             'numeric', fmt_num(val), d=2,
             hints=[f"$\\Delta x = {num(dx)}$; the subintervals start at $x_0 = {a}$.", f"$x_i = a + i\\,\\Delta x$; a midpoint is halfway between $x_{{i-1}}$ and $x_i$."],
             sol=[f"$\\Delta x = {num(dx)}$, so $x_i = {a} + i\\cdot{num(dx)}$.", f"The requested point is ${num(val)}$."],
             verify={'kind': 'numeric', 'value': {'right': f"{a}+{i}*({dx})", 'left': f"{a}+{i - 1}*({dx})", 'midpoint': f"{a}+({i}-1/2)*({dx})"}[rule]})

def t1_over_under(rng):
    f, a, b = rng.choice([(x ** 2, 0, 2), (2 * x + 1, 0, 3), (4 - x, 0, 4), (1 / x, 1, 3), (x ** 3, 0, 2), (5 - x ** 2, 0, 2)])
    n = rng.choice([2, 3, 4])
    rule = rng.choice(['left', 'right'])
    dx = R(b - a, n)
    off = 0 if rule == 'left' else dx
    L = sum(f.subs(x, a + j * dx + off) for j in range(n)) * dx
    exact = sp.integrate(f, (x, a, b))
    s = int(sp.sign(L - exact))
    opts = [('\\text{an overestimate}', '1'), ('\\text{an underestimate}', '-1'), ('\\text{exact}', '0')]
    idx = 0 if s > 0 else (1 if s < 0 else 2)
    inc = sp.diff(f, x).subs(x, R(a + b, 2)) > 0
    return D(1, f"On $[{a}, {b}]$, is the {rule}-endpoint Riemann sum for $f(x) = {ltx(f)}$ (with $n = {n}$) an overestimate or an underestimate of the true area?",
             'choice', str([o[1] for o in opts].index(str(s)) if False else idx), d=2,
             hints=[f"Decide whether $f$ is increasing or decreasing on $[{a}, {b}]$.", "For an increasing function, left endpoints sit below the curve (underestimate) and right endpoints above (overestimate); the reverse for a decreasing function."],
             sol=[f"$f$ is {'increasing' if inc else 'decreasing'} on $[{a}, {b}]$.", f"So the {rule}-endpoint rectangles are {'an overestimate' if s > 0 else 'an underestimate'} (here ${num(L)}$ versus the true area ${ltx(exact)}$)."],
             verify={'kind': 'choice', 'expected': f"sign(summation(({f}).subs(x, {a}+k*({dx})+({off})), (k,0,{n - 1}))*({dx}) - integrate({f},(x,{a},{b})))", 'choices_plain': [o[1] for o in opts]},
             choices=[o[0] for o in opts])

def t1_choice_sum(rng):
    f, a, b = rng.choice([(x ** 2, 0, 2), (x + 1, 0, 4), (x ** 2 + 1, 1, 3), (2 * x, 0, 3)])
    n = rng.choice([2, 4])
    dx = R(b - a, n)
    pts = [a + (j + 1) * dx for j in range(n)]
    good_terms = [f.subs(x, t) for t in pts]
    val = sum(good_terms) * dx
    def render(terms, w):
        return f"{num(w)}\\left({' + '.join(num(t) for t in terms)}\\right)"
    cands = [(render(good_terms, dx), f"({'+'.join(str(t) for t in good_terms)})*({dx})"),
             (render([f.subs(x, a + j * dx) for j in range(n)], dx), f"({'+'.join(str(f.subs(x, a + j * dx)) for j in range(n))})*({dx})"),
             (render(good_terms, 1), f"({'+'.join(str(t) for t in good_terms)})"),
             (render(pts, dx), f"({'+'.join(str(t) for t in pts)})*({dx})")]
    seen, opts = set(), []
    for lt, pl in cands:
        v = sp.sympify(pl)
        if v in seen:
            continue
        seen.add(v); opts.append((lt, pl))
    if len(opts) < 4:
        return None
    rng.shuffle(opts)
    idx = [o[1] for o in opts].index(cands[0][1])
    return D(1, f"Which computation is the right-endpoint Riemann sum for $f(x) = {ltx(f)}$ on $[{a}, {b}]$ with $n = {n}$?", 'choice', str(idx), d=2,
             hints=[f"$\\Delta x = {num(dx)}$ and the right endpoints are ${', '.join(num(t) for t in pts)}$.", "Each term is $f(\\text{sample point})\\cdot\\Delta x$; factor out $\\Delta x$."],
             sol=[f"Right endpoints: ${', '.join(num(t) for t in pts)}$; heights ${', '.join(num(t) for t in good_terms)}$.", f"Sum $= {num(dx)}({' + '.join(num(t) for t in good_terms)}) = {num(val)}$."],
             verify={'kind': 'choice', 'expected': f"summation(({f}).subs(x, {a}+(k+1)*({dx})), (k,0,{n - 1}))*({dx})", 'choices_plain': [o[1] for o in opts]},
             choices=[o[0] for o in opts])

def t1_formula(rng):
    n = rng.choice([10, 20, 25, 50, 100])
    kind = rng.choice(['k', 'k2'])
    if kind == 'k':
        val = n * (n + 1) // 2
        return D(1, f"Use $\\sum_{{k=1}}^{{n}} k = \\dfrac{{n(n+1)}}{{2}}$ to evaluate $\\sum_{{k=1}}^{{{n}}} k$.", 'numeric', str(val), d=1,
                 hints=[f"Set $n = {n}$.", f"$\\dfrac{{{n}\\cdot{n + 1}}}{{2}}$."], sol=[f"$\\dfrac{{{n}({n + 1})}}{{2}} = {val}$."] + ["This formula is what makes Riemann sums with many rectangles manageable."],
                 verify={'kind': 'numeric', 'value': f"summation(k,(k,1,{n}))"})
    n = rng.choice([5, 6, 8, 10, 12])
    val = n * (n + 1) * (2 * n + 1) // 6
    return D(1, f"Use $\\sum_{{k=1}}^{{n}} k^2 = \\dfrac{{n(n+1)(2n+1)}}{{6}}$ to evaluate $\\sum_{{k=1}}^{{{n}}} k^2$.", 'numeric', str(val), d=2,
             hints=[f"Set $n = {n}$.", f"$\\dfrac{{{n}\\cdot{n + 1}\\cdot{2 * n + 1}}}{{6}}$."], sol=[f"$\\dfrac{{{n}({n + 1})({2 * n + 1})}}{{6}} = {val}$."] + ["Check with a small case, such as $n = 2$: $1 + 4 = 5$."],
             verify={'kind': 'numeric', 'value': f"summation(k**2,(k,1,{n}))"})

T1 = [t1_riemann, t1_sigma, t1_dx, t1_sample_point, t1_over_under, t1_choice_sum, t1_formula, t1_riemann, t1_riemann]

# ================================================================ tier 2: definite integrals by geometry (signed area)

def integ(expr_l, a, b):
    return f"\\int_{{{a}}}^{{{b}}} {expr_l}\\,dx"

def t2_constant(rng):
    c, a = nz(rng, -8, 8), rng.randint(-5, 5)
    b = a + rng.randint(1, 8)
    val = c * (b - a)
    return D(2, f"Evaluate ${integ(str(c), a, b)}$ by interpreting it as a signed area.", 'numeric', str(val), d=1,
             hints=["The region is a rectangle; if it lies below the $x$-axis the integral is negative.", f"Width ${b - a}$, height $|{c}|$."],
             sol=[f"Rectangle of width ${b - a}$ and height ${abs(c)}$, {'above' if c > 0 else 'below'} the axis.", f"Integral $= {'+' if c > 0 else '-'}{abs(c)}\\cdot{b - a} = {val}$."],
             verify={'kind': 'definite', 'integrand': str(c), 'a': str(a), 'b': str(b)})

def t2_line(rng):
    m, c = rng.choice([1, 2, 3, -1, -2, R(1, 2), R(-1, 2)]), rng.randint(-6, 6)
    a = rng.randint(-5, 4); b = a + rng.randint(1, 7)
    ya, yb = m * a + c, m * b + c
    val = (ya + yb) * (b - a) / 2
    crosses = ya * yb < 0
    return D(2, f"Evaluate ${integ(chr(92) + 'left(' + lin(m, c) + chr(92) + 'right)', a, b)}$ using geometry.", 'numeric', fmt_num(val), d=3 if crosses else 2,
             hints=["Sketch the line over the interval; area above the axis counts positive, below counts negative." if crosses else "The region is a trapezoid (or triangle); sign it by whether it is above or below the axis.",
                    (f"The line crosses the axis at $x = {num(-R(c) / m)}$: split there into two triangles." if crosses else f"$y({a}) = {num(ya)}$, $y({b}) = {num(yb)}$.")],
             sol=([f"Zero at $x = {num(-R(c) / m)}$. Left triangle: $\\tfrac12\\cdot{num(-R(c) / m - a)}\\cdot({num(ya)}) = {num((-R(c) / m - a) * ya / 2)}$ (signed). Right triangle: $\\tfrac12\\cdot{num(b + R(c) / m)}\\cdot({num(yb)}) = {num((b + R(c) / m) * yb / 2)}$ (signed).",
                   f"Total: ${num(val)}$."] if crosses else
                  [f"Heights ${num(ya)}$ and ${num(yb)}$, width ${b - a}$.", f"Signed trapezoid area $= \\dfrac{{{num(ya)} + {num(yb)}}}{{2}}\\cdot{b - a} = {num(val)}$."]),
             verify={'kind': 'definite', 'integrand': f"({m})*x+({c})", 'a': str(a), 'b': str(b)})

def t2_semicircle(rng):
    r = rng.choice([1, 2, 3, 4, 5, 6])
    kind = rng.choice(['half', 'half', 'quarter', 'quarter_left', 'neg'])
    if kind == 'half':
        a, b, expr, val, desc = -r, r, sqrt(r * r - x ** 2), pi * r * r / 2, "the upper half of a circle"
    elif kind == 'quarter':
        a, b, expr, val, desc = 0, r, sqrt(r * r - x ** 2), pi * r * r / 4, "a quarter circle"
    elif kind == 'quarter_left':
        a, b, expr, val, desc = -r, 0, sqrt(r * r - x ** 2), pi * r * r / 4, "a quarter circle"
    else:
        a, b, expr, val, desc = -r, r, -sqrt(r * r - x ** 2), -pi * r * r / 2, "the lower half of a circle (below the axis, so the integral is negative)"
    return D(2, f"Evaluate ${integ(ltx(expr), a, b)}$ by recognizing the region. Give an exact answer in terms of $\\pi$.", 'numeric', plain(val), d=2 if kind in ('half', 'quarter') else 3,
             hints=[f"$y = \\sqrt{{{r * r} - x^2}}$ is the upper half of the circle $x^2 + y^2 = {r * r}$ of radius ${r}$.", f"Over $[{a}, {b}]$ the region is {desc}."],
             sol=[f"Radius ${r}$; full circle area $= {r * r}\\pi$.", f"The region is {desc}: integral $= {ltx(val)}$."],
             verify={'kind': 'definite', 'integrand': str(expr), 'a': str(a), 'b': str(b)})

def t2_semicircle_plus(rng):
    r, c = rng.choice([1, 2, 3, 4]), rng.choice([1, 2, 3, -1, -2])
    kind = rng.choice(['half', 'quarter'])
    a, b = (-r, r) if kind == 'half' else (0, r)
    expr = c + sqrt(r * r - x ** 2)
    val = c * (b - a) + pi * r * r / (2 if kind == 'half' else 4)
    return D(2, f"Evaluate ${integ(chr(92) + 'left(' + ltx(expr) + chr(92) + 'right)', a, b)}$ using geometry. Give an exact answer in terms of $\\pi$.", 'numeric', plain(val), d=3,
             hints=["Split the integrand: a constant plus a semicircle function.", f"Rectangle of height ${c}$ and width ${b - a}$ (signed), plus {'half' if kind == 'half' else 'a quarter'} of a circle of radius ${r}$."],
             sol=[f"Constant part: ${c}\\cdot{b - a} = {c * (b - a)}$.", f"Circle part: ${ltx(pi * r * r / (2 if kind == 'half' else 4))}$.", f"Total: ${ltx(val)}$."],
             verify={'kind': 'definite', 'integrand': str(expr), 'a': str(a), 'b': str(b)})

def t2_abs(rng):
    c = rng.randint(-3, 4)
    a = c - rng.randint(1, 5); b = c + rng.randint(1, 5)
    expr = Abs(x - c) if c else Abs(x)
    val = R((c - a) ** 2 + (b - c) ** 2, 2)
    return D(2, f"Evaluate ${integ(ltx(expr), a, b)}$ using geometry.", 'numeric', fmt_num(val), d=2,
             hints=[f"The graph is a V with its corner at $x = {c}$; the integrand is never negative.", f"Two right triangles with legs ${c - a}$ and ${b - c}$."],
             sol=[f"Left triangle: $\\tfrac12\\cdot{c - a}^2 = {num(R((c - a) ** 2, 2))}$. Right triangle: $\\tfrac12\\cdot{b - c}^2 = {num(R((b - c) ** 2, 2))}$.", f"Total: ${num(val)}$."],
             verify={'kind': 'definite', 'integrand': str(expr), 'a': str(a), 'b': str(b)})

def t2_properties(rng):
    kind = rng.choice(['reverse', 'additive', 'same', 'scale'])
    a, b = rng.randint(-3, 3), None
    b = a + rng.randint(1, 6); c = b + rng.randint(1, 5)
    A, B = nz(rng, -9, 9), nz(rng, -9, 9)
    if kind == 'reverse':
        return D(2, f"Suppose $\\int_{{{a}}}^{{{b}}} f(x)\\,dx = {A}$. Find $\\int_{{{b}}}^{{{a}}} f(x)\\,dx$.", 'numeric', str(-A), d=1,
                 hints=["Swapping the limits of integration changes the sign.", "$\\int_b^a f = -\\int_a^b f$."], sol=[f"$\\int_{{{b}}}^{{{a}}} f(x)\\,dx = -\\int_{{{a}}}^{{{b}}} f(x)\\,dx = {-A}$."] + ["The width $\\Delta x$ becomes negative when you integrate from right to left."],
                 verify={'kind': 'numeric', 'value': f"-({A})"})
    if kind == 'additive':
        return D(2, f"Suppose $\\int_{{{a}}}^{{{b}}} f(x)\\,dx = {A}$ and $\\int_{{{b}}}^{{{c}}} f(x)\\,dx = {B}$. Find $\\int_{{{a}}}^{{{c}}} f(x)\\,dx$.", 'numeric', str(A + B), d=1,
                 hints=["Integrals over adjacent intervals add.", f"$\\int_{{{a}}}^{{{c}}} = \\int_{{{a}}}^{{{b}}} + \\int_{{{b}}}^{{{c}}}$."], sol=[f"$\\int_{{{a}}}^{{{c}}} f = {A} + ({B}) = {A + B}$."] + ["Signed areas over adjacent pieces simply add."],
                 verify={'kind': 'numeric', 'value': f"{A}+({B})"})
    if kind == 'same':
        expr = rng.choice([x ** 2 + 1, sqrt(x + 4), 3 * x - 2])
        return D(2, f"Evaluate ${integ(ltx(expr), a, a)}$.", 'numeric', '0', d=1,
                 hints=["Look at the limits of integration.", "An interval of zero width encloses no area."], sol=["The upper and lower limits are equal, so the region has width $0$.", "The integral is $0$."],
                 verify={'kind': 'definite', 'integrand': str(expr), 'a': str(a), 'b': str(a)})
    cfac = rng.choice([2, 3, -1, -2, R(1, 2)])
    return D(2, f"Suppose $\\int_{{{a}}}^{{{b}}} f(x)\\,dx = {A}$. Find $\\int_{{{a}}}^{{{b}}} {num(cfac)}f(x)\\,dx$.", 'numeric', fmt_num(cfac * A), d=1,
             hints=["A constant factor can be pulled out of the integral.", f"${num(cfac)}\\int_{{{a}}}^{{{b}}} f(x)\\,dx$."], sol=[f"$\\int {num(cfac)}f = {num(cfac)}\\int f = {num(cfac)}\\cdot({A}) = {num(cfac * A)}$."] + ["Scaling the heights scales the area."],
             verify={'kind': 'numeric', 'value': f"({cfac})*({A})"})

def t2_sign_choice(rng):
    m = rng.choice([1, 2, -1, -2])
    a = rng.randint(-5, 2); b = a + rng.randint(1, 7)
    expr = m * x
    val = sp.integrate(expr, (x, a, b))
    s = int(sp.sign(val))
    opts = [('\\text{positive}', '1'), ('\\text{negative}', '-1'), ('\\text{zero}', '0')]
    idx = 0 if s > 0 else (1 if s < 0 else 2)
    return D(2, f"Without computing it exactly, is ${integ(ltx(expr), a, b)}$ positive, negative, or zero?", 'choice', str(idx), d=2,
             hints=["Sketch the line; compare the triangle above the axis with the one below.", "The integral is positive when more signed area lies above the axis than below."],
             sol=[f"Over $[{a}, {b}]$ the line $y = {ltx(expr)}$ makes triangles of signed area ${num(sp.integrate(expr, (x, a, 0)) if a < 0 < b else 0)}$ (left of $0$) and ${num(sp.integrate(expr, (x, 0, b)) if a < 0 < b else val)}$ (right of $0$)." if a < 0 < b else f"The whole region is on one side of the axis.",
                  f"Total: ${num(val)}$, which is {'positive' if s > 0 else ('negative' if s < 0 else 'zero')}."],
             verify={'kind': 'choice', 'expected': f"sign(integrate({expr},(x,{a},{b})))", 'choices_plain': [o[1] for o in opts]}, choices=[o[0] for o in opts])

def t2_symmetric(rng):
    kind = rng.choice(['odd_line', 'centered'])
    if kind == 'odd_line':
        a = rng.randint(1, 6); m = rng.choice([1, 2, 3, -2])
        expr = m * x
        return D(2, f"Evaluate ${integ(ltx(expr), -a, a)}$ using geometry.", 'numeric', '0', d=2,
                 hints=["Sketch the line over a symmetric interval.", "The triangle below the axis exactly cancels the one above it."],
                 sol=[f"Left triangle (signed area ${num(-m * a * a / 2)}$) and right triangle (signed area ${num(m * a * a / 2)}$).", "They cancel: the integral is $0$."],
                 verify={'kind': 'definite', 'integrand': str(expr), 'a': str(-a), 'b': str(a)})
    c, w = rng.randint(-3, 4), rng.randint(1, 5)
    expr = x - c
    return D(2, f"Evaluate ${integ(ltx(expr), c - w, c + w)}$ using geometry.", 'numeric', '0', d=3,
             hints=[f"The line crosses the axis at $x = {c}$, the midpoint of the interval.", "Equal triangles above and below the axis cancel."],
             sol=[f"Below the axis from ${c - w}$ to ${c}$: signed area ${num(-R(w * w, 2))}$. Above from ${c}$ to ${c + w}$: ${num(R(w * w, 2))}$.", "Sum: $0$."],
             verify={'kind': 'definite', 'integrand': str(expr), 'a': str(c - w), 'b': str(c + w)})

T2 = [t2_constant, t2_line, t2_semicircle, t2_semicircle_plus, t2_abs, t2_properties, t2_sign_choice, t2_symmetric, t2_line, t2_semicircle]

def build() -> dict[str, list[dict]]:
    return {'daily-tier-0': run('daily-tier-0', T0, target=72), 'daily-tier-1': run('daily-tier-1', T1, target=64), 'daily-tier-2': run('daily-tier-2', T2, target=64)}
