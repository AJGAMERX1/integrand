"""Stewart Chapter 1 templates (original problems, SymPy-verified):
functions-basics (1.1), essential-functions (1.2), new-functions-from-old (1.3),
exponential-functions (1.4), inverse-functions-and-logs (1.5).

Statements are prose with inline $...$ LaTeX (rendered by richText). build() -> {skill: [problems]}.
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
                     label_mc, numeric_problem, equiv_problem, interval_problem, interval_str, interval_ltx, h, y, w)


# ======================================================================
# 1.1 functions-basics
# ======================================================================

def functions_basics():
    S = 'functions-basics'
    rng = seeded(S)
    out = []

    # evaluate a quadratic at a point
    for _ in range(7):
        a, b, c = nz(rng, -4, 4), nz(rng, -5, 5), rng.randint(-6, 6)
        f = a * x**2 + b * x + c
        at = nz(rng, -3, 3)
        val = f.subs(x, at)
        out.append(numeric_problem(S, f"Let $f(x) = {L(f)}$. Find $f({at})$.", val, difficulty=1,
            hints=["Replace every $x$ in the formula with the given number, keeping the parentheses.",
                   f"Square first: $({at})^2 = {at**2}$. Then multiply and add the remaining terms."],
            solution=[f"$f({at}) = {a}({at})^2 {signed(b)}({at}) {signed(c)}$.",
                      f"$= {a*at**2} {signed(b*at)} {signed(c)} = {val}$."],
            verify={'kind': 'evaluate', 'expr': str(f), 'at': at}))

    # evaluate a rational or root function at a point
    for _ in range(6):
        kind = rng.choice(['rat', 'root'])
        if kind == 'rat':
            a, b = nz(rng, -3, 3), nz(rng, -4, 4)
            at = nz(rng, -4, 4, exclude=(0, b))
            f = (a * x + 1) / (x - b)
        else:
            a = rng.randint(1, 4)
            m = rng.randint(1, 5)
            at = (m * m - a) // 1
            f = sp.sqrt(x + a) + rng.randint(-3, 3) * x
            at = m * m - a
        val = f.subs(x, at)
        out.append(numeric_problem(S, f"If $g(x) = {L(f)}$, evaluate $g({at})$. Give an exact value.", val, difficulty=1 if kind == 'root' else 2,
            hints=["Substitute the number for $x$ everywhere it appears.",
                   "Simplify the numerator and denominator (or the square root) separately before combining."],
            solution=[f"Substitute $x = {at}$: $g({at}) = {L(f.subs(x, at, evaluate=False)) if kind == 'rat' else L(f).replace('x', f'({at})')}$.",
                      f"Simplify to get $g({at}) = {N(val)}$."],
            verify={'kind': 'evaluate', 'expr': str(f), 'at': at}))

    # domain of sqrt(ax+b) and sqrt(b-ax), 1/sqrt(...)
    for _ in range(8):
        a, b = rng.randint(1, 4), nz(rng, -8, 8)
        form = rng.choice(['sqrt_up', 'sqrt_down', 'recip_sqrt_up', 'recip_sqrt_down'])
        if form == 'sqrt_up':
            f = sp.sqrt(a * x + b); cond = f'{a}*x+{b} >= 0'; lo = sp.Rational(-b, a)
            ans, lt = interval_str(lo, sp.oo, False, True), interval_ltx(lo, sp.oo, False, True)
            why = f"we need ${L(a*x+b)} \\ge 0$, so $x \\ge {N(lo)}$"
        elif form == 'sqrt_down':
            f = sp.sqrt(b - a * x); cond = f'{b}-{a}*x >= 0'; hi = sp.Rational(b, a)
            ans, lt = interval_str(-sp.oo, hi, True, False), interval_ltx(-sp.oo, hi, True, False)
            why = f"we need ${L(b-a*x)} \\ge 0$, so $x \\le {N(hi)}$"
        elif form == 'recip_sqrt_up':
            f = 1 / sp.sqrt(a * x + b); cond = f'{a}*x+{b} > 0'; lo = sp.Rational(-b, a)
            ans, lt = interval_str(lo, sp.oo, True, True), interval_ltx(lo, sp.oo, True, True)
            why = f"the radicand must be positive (it is under a root and in a denominator): ${L(a*x+b)} > 0$, so $x > {N(lo)}$"
        else:
            f = 1 / sp.sqrt(b - a * x); cond = f'{b}-{a}*x > 0'; hi = sp.Rational(b, a)
            ans, lt = interval_str(-sp.oo, hi, True, True), interval_ltx(-sp.oo, hi, True, True)
            why = f"the radicand must be positive: ${L(b-a*x)} > 0$, so $x < {N(hi)}$"
        out.append(interval_problem(S, f"Find the domain of $f(x) = {L(f)}$. Answer in interval notation.", ans, cond, difficulty=1 if form.startswith('sqrt') else 2,
            hints=["An even root is only defined when the expression inside is not negative.",
                   "Also rule out any value that makes a denominator zero." if 'recip' in form else "Solve the inequality for $x$; remember to flip the sign if you divide by a negative."],
            solution=[f"{'Because the root is in a denominator, ' if 'recip' in form else 'The square root needs a non-negative radicand: '}{why}.",
                      f"Domain: ${lt}$."]))

    # difference quotient
    for _ in range(7):
        a, b = nz(rng, -3, 3), rng.randint(-5, 5)
        c = rng.randint(-4, 4)
        f = a * x**2 + b * x + c
        at = rng.randint(-2, 3)
        dq = sp.cancel((f.subs(x, at + h) - f.subs(x, at)) / h)
        out.append(equiv_problem(S, f"Let $f(x) = {L(f)}$. Simplify the difference quotient $\\dfrac{{f({at}+h) - f({at})}}{{h}}$ for $h \\ne 0$.", dq, difficulty=2, variable='h', domain=(-2, 2),
            hints=[f"Start by expanding $f({at}+h)$ completely; $({at}+h)^2 = {at**2} + {2*at}h + h^2$.",
                   f"After subtracting $f({at}) = {f.subs(x, at)}$ every remaining term has a factor of $h$ that cancels."],
            solution=[f"$f({at}+h) = {L(sp.expand(f.subs(x, at+h)))}$ and $f({at}) = {f.subs(x, at)}$.",
                      f"$f({at}+h) - f({at}) = {L(sp.expand(f.subs(x, at+h) - f.subs(x, at)))}$.",
                      f"Divide by $h$: $\\dfrac{{f({at}+h)-f({at})}}{{h}} = {L(dq)}$."],
            verify={'kind': 'equiv', 'expected': f'(({str(f.subs(x, at+h))}) - ({str(f.subs(x, at))}))/h'}))

    # piecewise evaluation
    for _ in range(7):
        c = rng.randint(-1, 3)
        m1, b1 = nz(rng, -3, 3), rng.randint(-4, 4)
        a2, b2 = nz(rng, -2, 3), rng.randint(-3, 3)
        f = sp.Piecewise((m1 * x + b1, x < c), (a2 * x**2 + b2, True))
        at = rng.choice([c - rng.randint(1, 3), c, c + rng.randint(1, 3)])
        val = f.subs(x, at)
        branch = 'first' if at < c else 'second'
        out.append(numeric_problem(S, f"Let $f(x) = \\begin{{cases}} {L(m1*x+b1)} & \\text{{if }} x < {c} \\\\ {L(a2*x**2+b2)} & \\text{{if }} x \\ge {c} \\end{{cases}}$. Find $f({at})$.", val, difficulty=1 if at != c else 2,
            hints=[f"First decide which condition ${at}$ satisfies: is ${at} < {c}$ or ${at} \\ge {c}$?",
                   f"Use only the {branch} formula, since the other one does not apply at $x={at}$."],
            solution=[f"Since ${at} {'<' if at < c else '\\ge'} {c}$, the {branch} rule applies.",
                      f"$f({at}) = {L((m1*x+b1) if at < c else (a2*x**2+b2))}$ at $x={at}$, which equals ${val}$."],
            verify={'kind': 'evaluate', 'expr': str(f), 'at': at}))

    # even / odd / neither
    for _ in range(7):
        kind = rng.choice(['even', 'odd', 'neither'])
        a, b, c = nz(rng, -3, 3), nz(rng, -3, 3), nz(rng, -4, 4)
        if kind == 'even':
            f = rng.choice([a * x**4 + b * x**2 + c, a * x**2 + c, sp.Abs(x) * a + b * x**2, a / (x**2 + abs(c))])
        elif kind == 'odd':
            f = rng.choice([a * x**3 + b * x, a * x**5 - b * x**3, a * x / (x**2 + abs(c)), a * x**3 + sp.sin(x) * b])
        else:
            f = rng.choice([a * x**2 + b * x + c, a * x**3 + c, a * x**2 + b * x, sp.sqrt(x + abs(c)) + a * x])
        fm = sp.simplify(f.subs(x, -x))
        lab = 'even' if sp.simplify(fm - f) == 0 else ('odd' if sp.simplify(fm + f) == 0 else 'neither')
        out.append(label_mc(S, f"Is $f(x) = {L(f)}$ even, odd, or neither?", [('even', 'even'), ('odd', 'odd'), ('neither', 'neither')], lab, rng, difficulty=2,
            hints=["Compute $f(-x)$ by replacing $x$ with $-x$ and simplify; watch how each power of $x$ behaves.",
                   "Even means $f(-x)=f(x)$; odd means $f(-x)=-f(x)$. If neither identity holds for all $x$, the answer is neither."],
            solution=[f"$f(-x) = {L(fm)}$.",
                      {'even': "This equals $f(x)$, so $f$ is even (its graph is symmetric about the $y$-axis).",
                       'odd': "This equals $-f(x)$, so $f$ is odd (its graph is symmetric about the origin).",
                       'neither': "This is neither $f(x)$ nor $-f(x)$, so $f$ is neither even nor odd."}[lab]]))

    # table representation
    for _ in range(5):
        xs = [0, 1, 2, 3, 4]
        vals = [rng.randint(-5, 9) for _ in xs]
        i, j = rng.sample(range(5), 2)
        op = rng.choice(['sum', 'diff', 'prod'])
        if op == 'sum':
            val, q = vals[i] + vals[j], f"f({xs[i]}) + f({xs[j]})"
        elif op == 'diff':
            val, q = vals[i] - vals[j], f"f({xs[i]}) - f({xs[j]})"
        else:
            val, q = vals[i] * vals[j], f"f({xs[i]}) \\cdot f({xs[j]})"
        table = "\\begin{array}{c|ccccc} x & " + " & ".join(map(str, xs)) + " \\\\ \\hline f(x) & " + " & ".join(map(str, vals)) + " \\end{array}"
        out.append(numeric_problem(S, f"A function $f$ is given by the table ${table}$. Compute ${q}$.", val, difficulty=1,
            hints=["Read each function value from the row labelled $f(x)$ under the matching $x$.",
                   f"$f({xs[i]}) = {vals[i]}$ and $f({xs[j]}) = {vals[j]}$."],
            solution=[f"From the table, $f({xs[i]}) = {vals[i]}$ and $f({xs[j]}) = {vals[j]}$.",
                      f"So ${q} = {val}$."],
            verify={'kind': 'numeric', 'value': val}))

    # word problems: build a formula
    for _ in range(4):
        Pm = rng.choice([20, 24, 30, 36, 40, 50])
        A = w * (sp.Rational(Pm, 2) - w)
        out.append(equiv_problem(S, f"A rectangle has perimeter ${Pm}$ m. Express its area $A$ as a function of the width $w$.", A, difficulty=3, variable='w', domain=(1, Pm / 2 - 1),
            hints=["Write the perimeter equation $2w + 2\\ell = " + str(Pm) + "$ and solve it for the length $\\ell$.",
                   "Area is width times length; substitute your expression for $\\ell$."],
            solution=[f"From $2w + 2\\ell = {Pm}$ we get $\\ell = {Pm//2} - w$.",
                      f"$A(w) = w\\ell = w({Pm//2} - w) = {L(sp.expand(A))}$, for $0 < w < {Pm//2}$."],
            verify={'kind': 'equiv', 'expected': f'w*({Pm}/2 - w)'}))
    for _ in range(3):
        V = rng.choice([8, 16, 27, 32, 64, 100])
        Sx = x**2 + 4 * V / x
        out.append(equiv_problem(S, f"An open box has a square base of side $x$ and volume ${V}$ cubic units. Express the total surface area $S$ (base plus four sides) as a function of $x$.", Sx, difficulty=3, variable='x', domain=(0.5, 4),
            hints=["Let the height be $h$; the volume gives $x^2 h = " + str(V) + "$.",
                   "Surface area is the base $x^2$ plus four sides of area $xh$ each; replace $h$ using the volume equation."],
            solution=[f"Volume: $x^2 h = {V}$, so $h = {V}/x^2$.",
                      f"$S = x^2 + 4xh = x^2 + 4x \\cdot \\dfrac{{{V}}}{{x^2}} = x^2 + \\dfrac{{{4*V}}}{{x}}$."],
            verify={'kind': 'equiv', 'expected': f'x**2 + 4*x*({V}/x**2)'}))

    # range of a simple function (interval)
    for _ in range(4):
        a = rng.randint(1, 3); c = rng.randint(-5, 5)
        form = rng.choice(['sq', 'nsq', 'abs'])
        if form == 'sq':
            f = a * x**2 + c; ans = interval_str(c, sp.oo, False, True); exp_ = f'Interval({c}, oo)'; lt = interval_ltx(c, sp.oo, False, True)
            why = f"$x^2 \\ge 0$, so ${L(f)} \\ge {c}$, and the value ${c}$ is reached at $x = 0$"
        elif form == 'nsq':
            f = c - a * x**2; ans = interval_str(-sp.oo, c, True, False); exp_ = f'Interval(-oo, {c})'; lt = interval_ltx(-sp.oo, c, True, False)
            why = f"$-{a}x^2 \\le 0$, so ${L(f)} \\le {c}$, with equality at $x = 0$"
        else:
            f = sp.Abs(x - a) + c; ans = interval_str(c, sp.oo, False, True); exp_ = f'Interval({c}, oo)'; lt = interval_ltx(c, sp.oo, False, True)
            why = f"$|x-{a}| \\ge 0$, so $f(x) \\ge {c}$, with equality at $x = {a}$"
        out.append(interval_problem(S, f"Find the range of $f(x) = {L(f)}$. Answer in interval notation.", ans, exp_, difficulty=2,
            hints=["Ask what values the squared (or absolute-value) part can take, then see what the rest of the formula does to them.",
                   "The smallest (or largest) output happens where the squared or absolute part equals zero."],
            solution=[f"Since {why}, every output is {'at least' if form != 'nsq' else 'at most'} ${c}$.",
                      f"As $|x|$ grows the outputs grow without bound {'upward' if form != 'nsq' else 'downward'}, so the range is ${lt}$."]))

    # vertical line test conceptual
    for i in range(4):
        a = rng.randint(1, 5); b = rng.randint(1, 4)
        opts = [(f"$y = x^2 {signed(a)}$", 'f1'), (f"$x = y^2 {signed(-a)}$", 'n1'), (f"$x^2 + y^2 = {a*a+b*b}$", 'n2'), (f"$y = \\sqrt{{x {signed(b)}}} {signed(-a)}$", 'f2'), (f"$|y| = x {signed(b)}$", 'n3')]
        rng.shuffle(opts)
        funcs = [o for o in opts if o[1].startswith('f')]
        chosen = [funcs[0]] + [o for o in opts if o[1].startswith('n')]
        out.append(label_mc(S, "Exactly one of these equations defines $y$ as a function of $x$. Which one?", chosen, funcs[0][1], rng, difficulty=2,
            hints=["A function gives exactly one output $y$ for each input $x$: no vertical line may hit the graph twice.",
                   "Try solving each equation for $y$; a $\\pm$ square root or $|y|$ means two $y$-values for one $x$."],
            solution=["Solving $x = y^2 + c$, $x^2 + y^2 = r^2$, or $|y| = x + c$ for $y$ gives $y = \\pm(\\dots)$, two outputs for one input, so those fail the vertical line test.",
                      f"The equation {funcs[0][0]} gives a single $y$ for each allowed $x$, so it defines a function."]))
    return out


# ======================================================================
# 1.2 essential-functions
# ======================================================================

def essential_functions():
    S = 'essential-functions'
    rng = seeded(S)
    out = []

    # line through two points
    for _ in range(7):
        x1, x2 = rng.sample(range(-4, 6), 2)
        m = sp.Rational(nz(rng, -5, 5), rng.choice([1, 1, 2, 3]))
        b = rng.randint(-6, 6)
        y1, y2 = m * x1 + b, m * x2 + b
        f = m * x + b
        out.append(equiv_problem(S, f"Find the linear function $f$ whose graph passes through $({x1}, {N(y1)})$ and $({x2}, {N(y2)})$.", f, difficulty=1 if m.q == 1 else 2,
            hints=["The slope is the change in $y$ divided by the change in $x$ between the two points.",
                   "Once you have the slope $m$, plug one point into $y = mx + b$ to find $b$."],
            solution=[f"Slope: $m = \\dfrac{{{N(y2)} - ({N(y1)})}}{{{x2} - ({x1})}} = {N(m)}$.",
                      f"Using $({x1}, {N(y1)})$: ${N(y1)} = {N(m)}({x1}) + b$, so $b = {b}$.",
                      f"$f(x) = {L(f)}$."],
            verify={'kind': 'equiv', 'expected': f'({y1}) + (({y2})-({y1}))/(({x2})-({x1}))*(x-({x1}))'}))

    # line with given slope through a point, or parallel line
    for _ in range(5):
        m = sp.Rational(nz(rng, -4, 4), rng.choice([1, 2]))
        x0, y0 = rng.randint(-4, 4), rng.randint(-5, 5)
        f = sp.expand(y0 + m * (x - x0))
        out.append(equiv_problem(S, f"Write the formula for the linear function with slope ${N(m)}$ whose graph passes through $({x0}, {y0})$.", f, difficulty=1,
            hints=["Use point-slope form: $y - y_0 = m(x - x_0)$.",
                   "Expand and solve for $y$ to get slope-intercept form."],
            solution=[f"$y - ({y0}) = {N(m)}(x - ({x0}))$.",
                      f"$f(x) = {L(f)}$."],
            verify={'kind': 'equiv', 'expected': f'{y0} + ({m})*(x - ({x0}))'}))

    # degree of polynomial
    for _ in range(5):
        deg = rng.randint(3, 6)
        coeffs = [nz(rng, -5, 5) if i == deg else rng.randint(-6, 6) for i in range(deg + 1)]
        terms = [coeffs[i] * x**i for i in range(deg + 1) if coeffs[i] != 0]
        rng.shuffle(terms)
        f = sum(terms)
        shown = ' '.join((('+' if sp.Poly(tm, x).LC() > 0 and idx > 0 else '') + L(tm)) for idx, tm in enumerate(terms)).replace('+-', '-')
        out.append(numeric_mc(S, f"What is the degree of the polynomial $P(x) = {shown}$?", deg, rng, difficulty=1,
            hints=["The degree is the largest exponent on $x$, regardless of the order the terms are written in.",
                   "Scan every term for its exponent; the constant term has degree 0."],
            solution=[f"The term with the highest power of $x$ is ${L(coeffs[deg]*x**deg)}$.",
                      f"So the degree is ${deg}$ and the leading coefficient is ${coeffs[deg]}$."],
            verify={'kind': 'choice', 'expected': int(sp.degree(f, x))}))

    # classify function type
    kinds = [('power', lambda: x**sp.Rational(rng.choice([1, 2, 3, 5]), rng.choice([2, 3, 4]))),
             ('exponential', lambda: rng.choice([2, 3, 5, sp.Rational(1, 2)])**x),
             ('rational', lambda: (x**2 + rng.randint(1, 5)) / (x - rng.randint(1, 5))),
             ('polynomial', lambda: nz(rng, -3, 3) * x**rng.randint(3, 5) + rng.randint(-4, 4) * x + rng.randint(1, 5)),
             ('trigonometric', lambda: rng.randint(2, 5) * rng.choice([sp.sin, sp.cos])(rng.randint(2, 4) * x)),
             ('logarithmic', lambda: rng.randint(2, 4) * sp.log(x) + rng.randint(1, 4))]
    labels = [('power function', 'power'), ('exponential function', 'exponential'), ('rational function', 'rational'), ('polynomial', 'polynomial'), ('trigonometric function', 'trigonometric'), ('logarithmic function', 'logarithmic')]
    for i in range(7):
        kname, maker = kinds[i % len(kinds)]
        f = maker()
        others = rng.sample([lb for lb in labels if lb[1] != kname], 3)
        opts = [lb for lb in labels if lb[1] == kname] + others
        out.append(label_mc(S, f"Which type of function from the catalog of essential functions is $f(x) = {L(f)}$?", opts, kname, rng, difficulty=1,
            hints=["Look at where the variable sits: in the base of a power, in an exponent, inside a trig or log, or in a quotient of polynomials.",
                   {'power': "$x^a$ with a constant exponent $a$ is a power function, even when $a$ is a fraction.",
                    'exponential': "A constant base raised to the variable $x$ is exponential.",
                    'rational': "A ratio of two polynomials is a rational function.",
                    'polynomial': "Only non-negative integer powers of $x$ with constant coefficients make a polynomial.",
                    'trigonometric': "Sine and cosine of a multiple of $x$ are trigonometric functions.",
                    'logarithmic': "$\\ln x$ (with constants) is a logarithmic function."}[kname]],
            solution=[f"$f(x) = {L(f)}$ has the form of a {kname if kname != 'polynomial' else 'polynomial'}{' function' if kname != 'polynomial' else ''}.",
                      "Classifying by form matters because each family has its own shape, domain, and rate of growth."]))

    # linear model word problems (draining tank / taxi fare)
    for _ in range(6):
        V0 = rng.choice([120, 200, 240, 300, 450, 600])
        r = rng.choice([4, 5, 6, 8, 10, 12, 15])
        V = V0 - r * t
        if rng.random() < 0.5:
            out.append(equiv_problem(S, f"A tank holds ${V0}$ liters and drains at a steady ${r}$ liters per minute. Write the volume $V$ (liters) as a function of the time $t$ (minutes) since draining began.", V, difficulty=1, variable='t', domain=(0, V0 / r),
                hints=["A steady rate means a linear model: start value plus (rate)(time).",
                       "Draining lowers the volume, so the rate enters with a negative sign."],
                solution=[f"Initial volume ${V0}$, decreasing by ${r}$ each minute: $V(t) = {V0} - {r}t$.",
                          f"The model is valid until the tank is empty, at $t = {N(sp.Rational(V0, r))}$ minutes."],
                verify={'kind': 'equiv', 'expected': f'{V0} - {r}*t'}))
        else:
            out.append(numeric_problem(S, f"A tank holds ${V0}$ liters and drains at a steady ${r}$ liters per minute. After how many minutes is the tank empty?", sp.Rational(V0, r), difficulty=1,
                hints=["First write the linear model $V(t) = (\\text{start}) - (\\text{rate})t$.",
                       "Empty means $V(t) = 0$; solve that equation for $t$."],
                solution=[f"$V(t) = {V0} - {r}t$.",
                          f"$V(t) = 0$ gives $t = {V0}/{r} = {N(sp.Rational(V0, r))}$ minutes."],
                verify={'kind': 'solve', 'lhs': f'{V0} - {r}*x', 'rhs': 0}))

    # slope interpretation
    for _ in range(4):
        m, b = nz(rng, -6, 6), rng.randint(-10, 10)
        kk = rng.randint(2, 6)
        f = m * x + b
        out.append(numeric_problem(S, f"For the linear function $f(x) = {L(f)}$, by how much does $f(x)$ change when $x$ increases by ${kk}$?", m * kk, difficulty=1,
            hints=["For a line, the change in output is always slope times change in input.",
                   f"Compute $f(a + {kk}) - f(a)$ for any $a$; the $b$ and the $a$-terms cancel."],
            solution=[f"$f(a+{kk}) - f(a) = {m}(a+{kk}) + {b} - ({m}a + {b}) = {m}\\cdot {kk}$.",
                      f"So $f$ changes by ${m*kk}$ (a {'decrease' if m < 0 else 'increase'} of ${abs(m*kk)}$)."],
            verify={'kind': 'evaluate', 'expr': f'({str(f.subs(x, x+kk))}) - ({str(f)})', 'at': 0}))

    # power functions with fractional exponents
    for _ in range(5):
        p, q = rng.choice([(3, 2), (2, 3), (1, 2), (5, 2), (4, 3), (1, 3), (3, 4)])
        base = rng.choice([4, 9, 16, 25] if q == 2 else ([8, 27, 64] if q == 3 else [16, 81]))
        f = x**sp.Rational(p, q)
        val = f.subs(x, base)
        out.append(numeric_problem(S, f"Evaluate the power function $f(x) = {L(f)}$ at $x = {base}$.", val, difficulty=2 if p > 1 else 1,
            hints=[f"$x^{{{p}/{q}}}$ means take the {'square' if q == 2 else ('cube' if q == 3 else 'fourth')} root, then raise to the power ${p}$.",
                   f"The {'square' if q == 2 else ('cube' if q == 3 else 'fourth')} root of ${base}$ is ${sp.root(base, q)}$."],
            solution=[f"${base}^{{{p}/{q}}} = (\\sqrt[{q}]{{{base}}})^{{{p}}} = {sp.root(base, q)}^{{{p}}}$.",
                      f"$= {val}$."],
            verify={'kind': 'evaluate', 'expr': str(f), 'at': base}))

    # rational function: where undefined
    for _ in range(4):
        a = nz(rng, -6, 6); c = rng.randint(1, 5)
        f = (x**2 + c) / (rng.choice([1, 2, 3]) * x - a * rng.choice([1, 2, 3]))
        den = sp.denom(f)
        root = sp.solve(den, x)[0]
        out.append(numeric_problem(S, f"The rational function $f(x) = {L(f)}$ is undefined at exactly one value of $x$. Find it.", root, difficulty=1,
            hints=["A rational function is undefined only where its denominator is zero.",
                   "Set the denominator equal to zero and solve."],
            solution=[f"Set ${L(den)} = 0$.", f"$x = {N(root)}$. The numerator is never zero there, so this is where $f$ is undefined."],
            verify={'kind': 'solve', 'lhs': str(den), 'rhs': 0}))

    # proportionality models
    for _ in range(5):
        pw = rng.choice([1, 2, 3, sp.Rational(1, 2), -1])
        x1 = rng.choice([1, 2, 3, 4] if pw != sp.Rational(1, 2) else [4, 9, 16])
        kconst = rng.randint(1, 6)
        y1 = kconst * sp.Integer(x1)**pw
        x2 = rng.choice([v for v in ([1, 2, 3, 4, 5, 6] if pw != sp.Rational(1, 2) else [1, 4, 9, 16, 25]) if v != x1])
        y2 = kconst * sp.Integer(x2)**pw
        desc = {1: 'directly proportional to $x$', 2: 'proportional to $x^2$', 3: 'proportional to $x^3$', sp.Rational(1, 2): 'proportional to $\\sqrt{x}$', -1: 'inversely proportional to $x$'}[pw]
        out.append(numeric_problem(S, f"A quantity $y$ is {desc}, and $y = {N(y1)}$ when $x = {x1}$. Find $y$ when $x = {x2}$.", y2, difficulty=3 if pw not in (1, 2) else 2,
            hints=[f"Write the model $y = k\\,x^{{{N(pw)}}}$ and use the given pair to find the constant $k$.",
                   f"$k = {N(y1)} / {x1}^{{{N(pw)}}}$; then substitute $x = {x2}$."],
            solution=[f"$y = k x^{{{N(pw)}}}$ with ${N(y1)} = k \\cdot {x1}^{{{N(pw)}}}$ gives $k = {kconst}$.",
                      f"$y = {kconst} \\cdot {x2}^{{{N(pw)}}} = {N(y2)}$."],
            verify={'kind': 'evaluate', 'expr': f'{kconst}*x**({pw})', 'at': x2}))

    # evaluate a quadratic model: height of a thrown object
    for _ in range(5):
        v0 = rng.choice([10, 15, 20, 25, 30]); h0 = rng.choice([0, 2, 5, 10, 20])
        hh = -5 * t**2 + v0 * t + h0
        tt = rng.randint(1, 3)
        val = hh.subs(t, tt)
        out.append(numeric_problem(S, f"A ball's height in meters after $t$ seconds is modeled by $h(t) = {L(hh)}$. What is its height after ${tt}$ second{'s' if tt > 1 else ''}?", val, difficulty=1,
            hints=["This is a quadratic (polynomial) model; just substitute the time.",
                   f"Compute $-5({tt})^2$ carefully before adding the other terms."],
            solution=[f"$h({tt}) = -5({tt})^2 + {v0}({tt}) + {h0}$.", f"$= {-5*tt*tt} + {v0*tt} + {h0} = {val}$ meters."],
            verify={'kind': 'evaluate', 'expr': str(hh.subs(t, x)), 'at': tt}))

    # conceptual: which model fits a description
    descs = [("the cost of a taxi ride that charges a fixed fee plus a constant amount per kilometer", 'linear'),
             ("the area of a square as a function of its side length", 'power'),
             ("a bacteria population that doubles every hour", 'exponential'),
             ("the height of a point on a Ferris wheel as a function of time", 'trigonometric'),
             ("the time needed to fill a pool as a function of the pump's flow rate (a fixed total volume)", 'reciprocal')]
    labs = [('linear', 'linear'), ('power function', 'power'), ('exponential', 'exponential'), ('trigonometric', 'trigonometric'), ('reciprocal (inverse proportion)', 'reciprocal')]
    for d, lab in descs:
        opts = [lb for lb in labs if lb[1] == lab] + rng.sample([lb for lb in labs if lb[1] != lab], 3)
        out.append(label_mc(S, f"Which kind of mathematical model best describes {d}?", opts, lab, rng, difficulty=2,
            hints=["Think about how the output changes as the input increases by equal steps: constant change, repeated multiplication, repeating pattern, or decrease toward zero.",
                   {'linear': "A fixed start plus the same amount per unit is a line.",
                    'power': "Side squared is a power function $x^2$.",
                    'exponential': "Doubling in equal time steps is repeated multiplication by 2.",
                    'trigonometric': "Periodic up-and-down motion calls for sine or cosine.",
                    'reciprocal': "A fixed total divided by a rate is $k/x$."}[lab]],
            solution=[{'linear': "Fixed fee $b$ plus rate $m$ per km gives $C(d) = md + b$, a linear model.",
                       'power': "$A = s^2$ is a power function with exponent 2.",
                       'exponential': "Doubling every hour gives $P(t) = P_0 \\cdot 2^t$, an exponential model.",
                       'trigonometric': "Circular motion repeats, so a sine or cosine model fits.",
                       'reciprocal': "Time equals volume divided by rate, $T = V/r$, inverse proportion."}[lab],
                      "Matching a situation to a family of functions is the first step of mathematical modeling."]))
    return out


# ======================================================================
# 1.3 new-functions-from-old
# ======================================================================

def new_functions_from_old():
    S = 'new-functions-from-old'
    rng = seeded(S)
    out = []
    fams = [lambda: x**2 + rng.randint(-3, 3), lambda: nz(rng, -3, 3) * x + rng.randint(-4, 4), lambda: sp.sqrt(x + rng.randint(1, 5)),
            lambda: 1 / (x + rng.randint(1, 4)), lambda: x**3 - rng.randint(1, 3) * x, lambda: rng.randint(2, 4) * x**2 - rng.randint(1, 3)]

    # composition f(g(x)) and g(f(x))
    for i in range(12):
        f = pick(rng, fams)(); g = pick(rng, fams)()
        if f == g:
            continue
        order = 'fg' if i % 2 == 0 else 'gf'
        outer, inner = (f, g) if order == 'fg' else (g, f)
        comp = outer.subs(x, inner)
        name = 'f \\circ g' if order == 'fg' else 'g \\circ f'
        dom = (0.3, 2.5)
        out.append(equiv_problem(S, f"Let $f(x) = {L(f)}$ and $g(x) = {L(g)}$. Find $({name})(x)$. You do not need to simplify.", comp, difficulty=3 if (sp.degree(outer, x) if outer.is_polynomial(x) else 2) >= 2 and not inner.is_polynomial(x) else 2, domain=dom,
            hints=[f"$({name})(x)$ means ${'f(g(x))' if order == 'fg' else 'g(f(x))'}$: apply ${'g' if order == 'fg' else 'f'}$ first, then ${'f' if order == 'fg' else 'g'}$.",
                   f"Replace every $x$ in ${L(outer)}$ by the whole expression ${L(inner)}$."],
            solution=[f"$({name})(x) = {'f' if order == 'fg' else 'g'}\\big({L(inner)}\\big)$.",
                      f"Substituting into ${L(outer)}$ gives ${L(comp)}$."],
            verify={'kind': 'equiv', 'expected': f'({str(outer)}).subs(x, {str(inner)})' if False else str(sp.sympify(str(outer)).subs(x, sp.sympify(f'({str(inner)})')))}))

    # evaluate a composition at a number
    for _ in range(6):
        f = pick(rng, fams)(); g = pick(rng, fams)()
        at = rng.randint(0, 3)
        inner_val = g.subs(x, at)
        if not inner_val.is_rational:
            continue
        val = f.subs(x, inner_val)
        if not val.is_rational:
            continue
        out.append(numeric_problem(S, f"Let $f(x) = {L(f)}$ and $g(x) = {L(g)}$. Evaluate $f(g({at}))$.", val, difficulty=1,
            hints=["Work from the inside out: find $g$ of the number first.",
                   f"$g({at}) = {N(inner_val)}$; now feed that into $f$."],
            solution=[f"$g({at}) = {N(inner_val)}$.", f"$f(g({at})) = f({N(inner_val)}) = {N(val)}$."],
            verify={'kind': 'evaluate', 'expr': str(f.subs(x, g)), 'at': at}))

    # transformations: write the new formula
    base = [lambda: x**2, lambda: sp.sqrt(x), lambda: sp.Abs(x), lambda: 1 / x, lambda: x**3]
    for _ in range(10):
        f = pick(rng, base)()
        hs = nz(rng, -4, 4); vs = nz(rng, -4, 4); a = rng.choice([2, 3, -1, -2, sp.Rational(1, 2)])
        mode = rng.choice(['shift', 'shift', 'stretch_shift', 'reflect_shift'])
        if mode == 'shift':
            g = f.subs(x, x - hs) + vs
            desc = f"shifted {'right' if hs > 0 else 'left'} ${abs(hs)}$ unit{'s' if abs(hs) != 1 else ''} and {'up' if vs > 0 else 'down'} ${abs(vs)}$ unit{'s' if abs(vs) != 1 else ''}"
            steps = [f"Shifting {'right' if hs > 0 else 'left'} by ${abs(hs)}$ replaces $x$ with $x {signed(-hs)}$: ${L(f.subs(x, x-hs))}$.",
                     f"Shifting {'up' if vs > 0 else 'down'} by ${abs(vs)}$ adds ${vs}$: $g(x) = {L(g)}$."]
        elif mode == 'stretch_shift':
            g = a * f + vs
            desc = f"{'stretched' if abs(a) > 1 else 'compressed'} vertically by a factor of ${N(abs(a))}$ {'and reflected about the $x$-axis, ' if a < 0 else ''}then shifted {'up' if vs > 0 else 'down'} ${abs(vs)}$ unit{'s' if abs(vs) != 1 else ''}"
            steps = [f"Vertical {'stretch' if abs(a) > 1 else 'compression'} multiplies outputs by ${N(a)}$: ${L(a*f)}$.",
                     f"Then add ${vs}$: $g(x) = {L(g)}$."]
        else:
            g = -f.subs(x, x - hs)
            desc = f"reflected about the $x$-axis and shifted {'right' if hs > 0 else 'left'} ${abs(hs)}$ unit{'s' if abs(hs) != 1 else ''}"
            steps = [f"Reflecting about the $x$-axis negates the output: $-{L(f)}$.",
                     f"Shifting {'right' if hs > 0 else 'left'} by ${abs(hs)}$ replaces $x$ with $x {signed(-hs)}$: $g(x) = {L(g)}$."]
        dom = (0.5, 3) if (f.has(sp.sqrt(x)) or f == 1 / x) else (-3, 3)
        if f.has(sp.sqrt(x)) and mode != 'stretch_shift':
            dom = (hs + 0.5, hs + 3)
        out.append(equiv_problem(S, f"Start with $f(x) = {L(f)}$. Write a formula for the function $g$ whose graph is the graph of $f$ {desc}.", g, difficulty=3 if mode != 'shift' else 2, domain=dom,
            hints=["Horizontal shifts change the input ($x \\to x - c$ moves right by $c$); vertical changes act on the output.",
                   "Apply the transformations one at a time, in the order they are listed."],
            solution=steps, verify={'kind': 'equiv', 'expected': str(g)}))

    # describe transformation conceptually
    for _ in range(5):
        hs = nz(rng, -4, 4); vs = nz(rng, -4, 4)
        correct = f"shift {'right' if hs > 0 else 'left'} {abs(hs)}, {'up' if vs > 0 else 'down'} {abs(vs)}"
        wrong1 = f"shift {'left' if hs > 0 else 'right'} {abs(hs)}, {'up' if vs > 0 else 'down'} {abs(vs)}"
        wrong2 = f"shift {'right' if hs > 0 else 'left'} {abs(hs)}, {'down' if vs > 0 else 'up'} {abs(vs)}"
        wrong3 = f"shift {'left' if hs > 0 else 'right'} {abs(hs)}, {'down' if vs > 0 else 'up'} {abs(vs)}"
        opts = [(correct, 'correct'), (wrong1, 'w1'), (wrong2, 'w2'), (wrong3, 'w3')]
        out.append(label_mc(S, f"How is the graph of $y = f(x {signed(-hs)}) {signed(vs)}$ obtained from the graph of $y = f(x)$?", opts, 'correct', rng, difficulty=1,
            hints=["Inside the parentheses, $x - c$ shifts right by $c$ (the opposite of what the sign suggests).",
                   "A constant added outside the function moves the graph vertically in the direction of its sign."],
            solution=[f"$f(x {signed(-hs)})$ is $f$ shifted horizontally {'right' if hs > 0 else 'left'} by ${abs(hs)}$.",
                      f"Adding ${vs}$ then moves the graph {'up' if vs > 0 else 'down'} by ${abs(vs)}$."]))

    # decompose h = f(g(x)): find g given f (f injective)
    outers = [(sp.sqrt(x), '\\sqrt{x}'), (x**3, 'x^3'), (1 / x, '1/x'), (2**x, '2^x')]
    inners = [lambda: x**2 + rng.randint(1, 5), lambda: rng.randint(2, 5) * x - rng.randint(1, 4), lambda: x**3 + rng.randint(1, 3) * x, lambda: rng.randint(2, 4) * x**2 + 1]
    for _ in range(6):
        fo, fo_l = pick(rng, outers)
        g = pick(rng, inners)()
        hcomp = fo.subs(x, g)
        out.append(equiv_problem(S, f"Let $h(x) = {L(hcomp)}$. If $h(x) = f(g(x))$ with $f(x) = {fo_l}$, find $g(x)$.", g, difficulty=2, domain=(0.5, 2.5),
            hints=["Ask: what expression is the outer operation being applied to?",
                   f"Whatever sits where the $x$ would be in $f(x) = {fo_l}$ is $g(x)$."],
            solution=[f"$h(x) = f(g(x))$ means $h$ is ${fo_l}$ applied to $g(x)$.",
                      f"Comparing with ${L(hcomp)}$ shows $g(x) = {L(g)}$."],
            verify={'kind': 'equiv', 'expected': str(g)}))

    # sums, products, quotients of functions
    for _ in range(6):
        f = pick(rng, fams)(); g = pick(rng, fams)()
        if f == g:
            continue
        op = rng.choice(['+', '-', '*', '/'])
        if op == '/':
            at = rng.randint(1, 3)
            gv = g.subs(x, at)
            if gv == 0 or not gv.is_rational or not f.subs(x, at).is_rational:
                continue
            val = f.subs(x, at) / gv
            out.append(numeric_problem(S, f"Let $f(x) = {L(f)}$ and $g(x) = {L(g)}$. Evaluate $\\left(\\dfrac{{f}}{{g}}\\right)({at})$.", val, difficulty=1,
                hints=["$(f/g)(a)$ means $f(a)$ divided by $g(a)$.", f"Compute $f({at})$ and $g({at})$ separately first."],
                solution=[f"$f({at}) = {N(f.subs(x, at))}$ and $g({at}) = {N(gv)}$.", f"$(f/g)({at}) = {N(f.subs(x, at))}/{N(gv)} = {N(val)}$."],
                verify={'kind': 'evaluate', 'expr': f'({str(f)})/({str(g)})', 'at': at}))
        else:
            comb = {'+': f + g, '-': f - g, '*': f * g}[op]
            nm = {'+': 'f + g', '-': 'f - g', '*': 'fg'}[op]
            out.append(equiv_problem(S, f"Let $f(x) = {L(f)}$ and $g(x) = {L(g)}$. Find a formula for $({nm})(x)$.", comb, difficulty=1, domain=(0.5, 2.5),
                hints=[f"$({nm})(x)$ is defined as $f(x) {op if op != '*' else '\\cdot'} g(x)$ for each $x$.", "Combine the two formulas and collect like terms if possible."],
                solution=[f"$({nm})(x) = \\big({L(f)}\\big) {op if op != '*' else '\\cdot'} \\big({L(g)}\\big)$.", f"$= {L(sp.expand(comb))}$."],
                verify={'kind': 'equiv', 'expected': str(comb)}))

    # vertex after transformation of x^2
    for _ in range(4):
        a = nz(rng, -5, 5); b = nz(rng, -5, 5)
        g = (x + a)**2 + b
        out.append(numeric_problem(S, f"The graph of $y = {L(g)}$ is a shifted parabola. What is the $x$-coordinate of its vertex?", -a, difficulty=1,
            hints=["Compare with $y = (x - c)^2 + d$, whose vertex is at $(c, d)$.", f"Rewrite $x {signed(a)}$ as $x - ({-a})$."],
            solution=[f"$y = (x - ({-a}))^2 {signed(b)}$ is $y = x^2$ shifted {'right' if -a > 0 else 'left'} ${abs(a)}$ and {'up' if b > 0 else 'down'} ${abs(b)}$.",
                      f"The vertex moves from $(0, 0)$ to $({-a}, {b})$, so its $x$-coordinate is ${-a}$."],
            verify={'kind': 'solve', 'lhs': str(sp.diff(g, x)), 'rhs': 0}))

    # table composition
    for _ in range(4):
        xs = [1, 2, 3, 4]
        fv = [rng.randint(1, 4) for _ in xs]; gv = [rng.randint(1, 4) for _ in xs]
        at = rng.choice(xs)
        val = fv[gv[at - 1] - 1]
        table = ("\\begin{array}{c|cccc} x & 1 & 2 & 3 & 4 \\\\ \\hline f(x) & " + " & ".join(map(str, fv)) + " \\\\ g(x) & " + " & ".join(map(str, gv)) + " \\end{array}")
        out.append(numeric_problem(S, f"Use the table ${table}$ to find $(f \\circ g)({at})$.", val, difficulty=1,
            hints=["$(f \\circ g)(a) = f(g(a))$: look up $g(a)$ first.", f"$g({at}) = {gv[at-1]}$; now read $f({gv[at-1]})$ from the table."],
            solution=[f"From the table $g({at}) = {gv[at-1]}$.", f"Then $f({gv[at-1]}) = {val}$, so $(f \\circ g)({at}) = {val}$."],
            verify={'kind': 'numeric', 'value': val}))
    return out


# ======================================================================
# 1.4 exponential-functions
# ======================================================================

def exponential_functions():
    S = 'exponential-functions'
    rng = seeded(S)
    out = []

    # evaluate b^x
    for _ in range(7):
        b = rng.choice([2, 3, 4, 5, 9, 16, sp.Rational(1, 2), sp.Rational(1, 3)])
        e = sp.Integer(1) * rng.choice([-2, -1, 0, 1, 2, 3, sp.Rational(1, 2), sp.Rational(3, 2)])
        if e.q == 2 and b not in (4, 9, 16):
            e = rng.choice([-2, -1, 2, 3])
        f = b**x
        val = f.subs(x, e)
        out.append(numeric_problem(S, f"Let $f(x) = {L(f)}$. Find the exact value of $f({N(e)})$.", val, difficulty=1 if e in (0, 1, 2, 3) else 2,
            hints=["A negative exponent means reciprocal; a fractional exponent $1/2$ means square root.",
                   f"$f({N(e)}) = {L(f)}$ with $x = {N(e)}$."],
            solution=[f"$f({N(e)}) = {N(b)}^{{{N(e)}}}$.", f"$= {N(val)}$."],
            verify={'kind': 'evaluate', 'expr': str(f), 'at': e}))

    # simplify with exponent laws (single variable)
    for _ in range(8):
        b = rng.choice([2, 3, 5, sp.E])
        form = rng.choice(['prod', 'quot', 'pow', 'mixed'])
        p1, p2 = rng.randint(1, 4), rng.randint(1, 4)
        if form == 'prod':
            expr = b**(p1 * x) * b**(p2 * x + 1); res = b**((p1 + p2) * x + 1)
            law = "when multiplying powers with the same base, add the exponents"
        elif form == 'quot':
            expr = b**(p1 * x + p2) / b**x; res = b**((p1 - 1) * x + p2)
            law = "when dividing powers with the same base, subtract the exponents"
        elif form == 'pow':
            expr = (b**(p1 * x))**p2; res = b**(p1 * p2 * x)
            law = "a power of a power multiplies the exponents"
        else:
            expr = (b**x)**p1 * b**p2 / b**(2 * x); res = b**((p1 - 2) * x + p2)
            law = "apply the power rule first, then add and subtract exponents"
        res = sp.simplify(res)
        out.append(equiv_problem(S, f"Write ${L(expr)}$ as a single power of ${L(b)}$.", res, difficulty=2, domain=(-2, 2),
            hints=[f"Use the exponent laws: {law}.", "Keep the base and combine only the exponents."],
            solution=[f"${L(expr)} = {L(b)}^{{{L(sp.expand(sp.log(res, b)/sp.log(b, b)) if b != sp.E else sp.expand(sp.log(res)))}}}$ by the exponent laws.",
                      f"So the single power is ${L(res)}$."],
            verify={'kind': 'equiv', 'expected': str(expr)}))

    # doubling / tripling growth model
    for _ in range(7):
        P0 = rng.choice([50, 100, 200, 300, 500, 1000]); T = rng.choice([1, 2, 3, 4, 6]); base = rng.choice([2, 2, 3])
        tt = T * rng.randint(1, 4)
        f = P0 * sp.Integer(base)**(t / T)
        if rng.random() < 0.5:
            out.append(equiv_problem(S, f"A culture starts with ${P0}$ cells and {'doubles' if base == 2 else 'triples'} every ${T}$ hour{'s' if T > 1 else ''}. Write the population $P$ as a function of time $t$ in hours.", f, difficulty=3 if T > 1 else 2, variable='t', domain=(0, 12),
                hints=[f"Each {'doubling' if base == 2 else 'tripling'} multiplies by ${base}$; count how many {'doublings' if base == 2 else 'triplings'} happen in $t$ hours.",
                       f"After $t$ hours there have been $t/{T}$ {'doublings' if base == 2 else 'triplings'}, so the multiplier is ${base}^{{t/{T}}}$."],
                solution=[f"The population multiplies by ${base}$ every ${T}$ hours, giving ${base}^{{t/{T}}}$ after $t$ hours.",
                          f"$P(t) = {P0} \\cdot {base}^{{t/{T}}}$."],
                verify={'kind': 'equiv', 'expected': f'{P0}*{base}**(t/{T})'}))
        else:
            val = f.subs(t, tt)
            out.append(numeric_problem(S, f"A culture starts with ${P0}$ cells and {'doubles' if base == 2 else 'triples'} every ${T}$ hour{'s' if T > 1 else ''}. How many cells are there after ${tt}$ hours?", val, difficulty=1,
                hints=[f"Count the number of {'doublings' if base == 2 else 'triplings'}: ${tt}/{T} = {tt//T}$.", f"Multiply ${P0}$ by ${base}$ that many times."],
                solution=[f"$P(t) = {P0}\\cdot {base}^{{t/{T}}}$, and $t = {tt}$ gives ${base}^{{{tt//T}}} = {base**(tt//T)}$.",
                          f"$P({tt}) = {P0} \\cdot {base**(tt//T)} = {val}$."],
                verify={'kind': 'evaluate', 'expr': str(f.subs(t, x)), 'at': tt}))

    # half-life decay
    for _ in range(6):
        A0 = rng.choice([80, 100, 160, 200, 320, 500]); H = rng.choice([2, 3, 5, 8, 10])
        tt = H * rng.randint(1, 4)
        f = A0 * sp.Rational(1, 2)**(t / H)
        val = f.subs(t, tt)
        out.append(numeric_problem(S, f"A sample of ${A0}$ mg of a substance has a half-life of ${H}$ days. How many milligrams remain after ${tt}$ days?", val, difficulty=1,
            hints=["Each half-life cuts the amount in half.", f"${tt}$ days is ${tt//H}$ half-lives, so multiply by $(1/2)^{{{tt//H}}}$."],
            solution=[f"$A(t) = {A0}\\left(\\tfrac12\\right)^{{t/{H}}}$; at $t = {tt}$ the exponent is ${tt//H}$.",
                      f"$A({tt}) = {A0} \\cdot \\tfrac{{1}}{{{2**(tt//H)}}} = {N(val)}$ mg."],
            verify={'kind': 'evaluate', 'expr': str(f.subs(t, x)), 'at': tt}))

    # solve b^x = N by matching bases
    for _ in range(7):
        b = rng.choice([2, 3, 4, 5, 10]); e = sp.Integer(1) * rng.choice([-2, -1, 2, 3, 4, sp.Rational(1, 2)])
        if e == sp.Rational(1, 2) and b not in (4,):
            e = sp.Integer(3)
        rhs = sp.Integer(b)**e
        out.append(numeric_problem(S, f"Solve for $x$: ${b}^x = {N(rhs)}$.", e, difficulty=1 if e > 0 and e.q == 1 else 2,
            hints=[f"Write ${N(rhs)}$ as a power of ${b}$.", "When the bases match, the exponents must be equal."],
            solution=[f"${N(rhs)} = {b}^{{{N(e)}}}$.", f"So ${b}^x = {b}^{{{N(e)}}}$ gives $x = {N(e)}$."],
            verify={'kind': 'solve', 'lhs': f'{b}**x', 'rhs': str(rhs)}))

    # horizontal asymptote via limit
    for _ in range(6):
        a = nz(rng, -4, 4); b = rng.choice([2, 3, sp.E, sp.Rational(1, 2), sp.Rational(1, 3)]); c = nz(rng, -5, 5)
        f = a * b**x + c
        to = -sp.oo if b > 1 else sp.oo
        out.append(numeric_problem(S, f"Find the value $y = c$ of the horizontal asymptote of $y = {L(f)}$.", c, difficulty=2,
            hints=[f"The term ${L(b**x)}$ approaches $0$ as $x \\to {'-\\infty' if b > 1 else '\\infty'}$.", "The constant added at the end is what the graph levels off to."],
            solution=[f"As $x \\to {'-\\infty' if b > 1 else '\\infty'}$, ${L(a*b**x)} \\to 0$.", f"So $y \\to {c}$: the horizontal asymptote is $y = {c}$."],
            verify={'kind': 'limit', 'expr': str(f), 'to': str(to)}))

    # exponential through (0, C) and (1, Cb) or (2, ...)
    for _ in range(5):
        C = rng.choice([2, 3, 4, 5, 6]); b = rng.choice([2, 3, 4, sp.Rational(1, 2)])
        x2 = rng.choice([1, 2])
        f = C * b**x
        out.append(equiv_problem(S, f"Find the exponential function $f(x) = C b^x$ whose graph passes through $(0, {C})$ and $({x2}, {N(f.subs(x, x2))})$.", f, difficulty=2, domain=(-2, 2),
            hints=["At $x = 0$, $b^0 = 1$, so the $y$-intercept gives $C$ directly.", f"Then ${N(f.subs(x, x2))} = {C} b^{{{x2}}}$; solve for $b$."],
            solution=[f"$f(0) = C = {C}$.", f"$f({x2}) = {C} b^{{{x2}}} = {N(f.subs(x, x2))}$ gives $b^{{{x2}}} = {N(b**x2)}$, so $b = {N(b)}$.", f"$f(x) = {L(f)}$."],
            verify={'kind': 'equiv', 'expected': f'{C}*({b})**x'}))

    # range / domain interval
    for _ in range(4):
        a = rng.choice([1, 2, 3]); c = rng.randint(-4, 4); b = rng.choice([2, 3, sp.E])
        f = a * b**x + c
        out.append(interval_problem(S, f"Find the range of $f(x) = {L(f)}$. Answer in interval notation.", interval_str(c, sp.oo, True, True), f'Interval.open({c}, oo)', difficulty=2,
            hints=[f"${L(b**x)}$ takes every positive value but never $0$ or a negative value.", f"Multiplying by ${a}$ keeps it positive; adding ${c}$ shifts the whole range."],
            solution=[f"${L(a*b**x)} > 0$ for all $x$ and gets arbitrarily close to $0$ and arbitrarily large.", f"So $f(x) > {c}$ with no upper bound: range $({c}, \\infty)$."]))

    # growth comparison conceptual
    for _ in range(4):
        pw = rng.choice([5, 10, 20, 50]); b = rng.choice([sp.Rational(11, 10), sp.Rational(3, 2), 2, 3])
        opts = [(f"${L(b**x)}$", 'exp'), (f"$x^{{{pw}}}$", 'pow'), (f"${pw}x$", 'lin'), (f"$x^2 + {pw}$", 'quad')]
        out.append(label_mc(S, "For very large $x$, which of these functions is eventually the largest?", opts, 'exp', rng, difficulty=2,
            hints=["Compare how each function grows when $x$ is multiplied or increased by a fixed step.",
                   "Any exponential function with base greater than 1 eventually outgrows every power of $x$, no matter how large the exponent."],
            solution=[f"Powers like $x^{{{pw}}}$ grow by a fixed factor when $x$ is scaled, but ${L(b**x)}$ multiplies by ${N(b)}$ for every unit increase in $x$.",
                      "Eventually the exponential function exceeds any polynomial, so it is the largest for large $x$."]))

    # compound interest value
    for _ in range(4):
        Pr = rng.choice([1000, 2000, 5000]); r = rng.choice([sp.Rational(4, 100), sp.Rational(5, 100), sp.Rational(10, 100)]); yrs = rng.randint(2, 3)
        f = Pr * (1 + r)**t
        val = f.subs(t, yrs)
        out.append(numeric_problem(S, f"An account with ${Pr}$ dollars grows by ${int(r*100)}\\%$ per year, compounded annually. What is the balance after ${yrs}$ years? Round to the nearest cent.", round(float(val), 2), difficulty=3, tolerance=0.011,
            hints=["Each year multiplies the balance by $1 + r$.", f"The balance is ${Pr}(1 + {N(r)})^{{{yrs}}}$."],
            solution=[f"$A(t) = {Pr}({N(1+r)})^t$.", f"$A({yrs}) = {Pr} \\cdot {N(1+r)}^{{{yrs}}} \\approx {float(val):.2f}$."],
            verify={'kind': 'evaluate', 'expr': str(f.subs(t, x)), 'at': yrs}))
    return out


# ======================================================================
# 1.5 inverse-functions-and-logs
# ======================================================================

def inverse_functions_and_logs():
    S = 'inverse-functions-and-logs'
    rng = seeded(S)
    out = []

    # inverse of linear, cubic-type, rational
    for _ in range(10):
        form = rng.choice(['lin', 'cube', 'rat', 'root'])
        if form == 'lin':
            m = sp.Rational(nz(rng, -5, 5), rng.choice([1, 2])); b = nz(rng, -6, 6)
            f = m * x + b; inv = (x - b) / m; dom = (-3, 3)
            steps = [f"Write $y = {L(f)}$ and solve for $x$: $x = \\dfrac{{y {signed(-b)}}}{{{N(m)}}}$.", f"Swap the letters: $f^{{-1}}(x) = {L(inv)}$."]
        elif form == 'cube':
            a = nz(rng, -3, 3); b = rng.randint(-5, 5)
            f = a * x**3 + b; inv = sp.cbrt((x - b) / a) if a > 0 else sp.cbrt((b - x) / (-a)); dom = (b + 0.5, b + 3) if a > 0 else (b - 3, b - 0.5)
            steps = [f"Write $y = {L(f)}$; subtract ${b}$ and divide by ${a}$: $x^3 = \\dfrac{{y {signed(-b)}}}{{{a}}}$.", f"Take the cube root and swap letters: $f^{{-1}}(x) = {L(inv)}$."]
        elif form == 'rat':
            a, b2 = rng.randint(1, 4), nz(rng, -4, 4)
            f = (a * x + 1) / (x - b2); inv = sp.simplify((b2 * x + 1) / (x - a)); dom = (a + 0.5, a + 3)
            steps = [f"Write $y = {L(f)}$ and clear the fraction: $y(x - ({b2})) = {a}x + 1$.", f"Collect the $x$ terms: $x(y - {a}) = {b2}y + 1$, so $x = \\dfrac{{{b2}y + 1}}{{y - {a}}}$.", f"Swap letters: $f^{{-1}}(x) = {L(inv)}$."]
        else:
            a = rng.randint(1, 5); c = rng.randint(1, 4)
            f = sp.sqrt(x + a) + c; inv = (x - c)**2 - a; dom = (c, c + 3)
            steps = [f"Write $y = {L(f)}$, isolate the root: $\\sqrt{{x + {a}}} = y - {c}$ (so $y \\ge {c}$).", f"Square and solve: $x = (y - {c})^2 - {a}$; swap letters: $f^{{-1}}(x) = {L(inv)}$ for $x \\ge {c}$."]
        out.append(equiv_problem(S, f"Find a formula for the inverse function of $f(x) = {L(f)}$.", inv, difficulty={'lin': 1, 'cube': 2, 'rat': 3, 'root': 2}[form], domain=dom,
            hints=["Write $y = f(x)$, then solve the equation for $x$ in terms of $y$.", "Finally swap $x$ and $y$ to express $f^{-1}(x)$."],
            solution=steps, verify={'kind': 'inverse', 'expr': str(f)}))

    # evaluate logarithms exactly
    for _ in range(8):
        b = rng.choice([2, 3, 4, 5, 10, sp.E])
        e = sp.Integer(1) * rng.choice([-3, -2, -1, 0, 1, 2, 3, 4, sp.Rational(1, 2)])
        if e == sp.Rational(1, 2) and b not in (4,):
            e = sp.Integer(2)
        arg = sp.Integer(b)**e if b != sp.E else sp.E**e
        if b == sp.E:
            stmt = f"Evaluate $\\ln\\left({L(arg)}\\right)$." if e != 0 else "Evaluate $\\ln 1$."
            vexpr = f'log({str(arg)})'
        else:
            stmt = f"Evaluate $\\log_{{{b}}} {N(arg)}$."
            vexpr = f'log({str(arg)}, {b})'
        out.append(numeric_problem(S, stmt, e, difficulty=1 if e >= 0 else 2,
            hints=[f"$\\log_b N$ asks: to what power must ${L(b) if b != sp.E else 'e'}$ be raised to get the argument?",
                   f"Write the argument as a power of ${b}$: ${N(arg)} = {b}^{{{N(e)}}}$." if b != sp.E else "Use the cancellation equation $\\ln(e^u) = u$."],
            solution=[f"${L(arg) if b == sp.E else N(arg)} = {L(b) if b != sp.E else 'e'}^{{{N(e)}}}$.", f"Therefore the logarithm equals ${N(e)}$."],
            verify={'kind': 'numeric', 'value': vexpr}))

    # solve exponential equations with ln
    for _ in range(7):
        k_ = rng.choice([2, 3, 4, 5, -2, -3]); c = rng.choice([5, 7, 9, 10, 11, 12, 20])
        shift = rng.choice([0, 0, 1, -1, 2, 3])
        f = sp.exp(k_ * x + shift)
        sol = (sp.log(c) - shift) / k_
        lhs_l = f"e^{{{L(k_*x+shift)}}}"
        out.append(numeric_problem(S, f"Solve for $x$: ${lhs_l} = {c}$. Give an exact answer.", sol, difficulty=2 if shift == 0 else 3,
            hints=["Take the natural logarithm of both sides; $\\ln e^{u} = u$.", f"That gives ${L(k_*x+shift)} = \\ln {c}$; now solve the linear equation."],
            solution=[f"$\\ln\\left({lhs_l}\\right) = \\ln {c}$, so ${L(k_*x+shift)} = \\ln {c}$.", f"$x = {L(sol)}$."],
            verify={'kind': 'solve', 'lhs': str(f), 'rhs': c}))

    # solve logarithmic equations
    for _ in range(7):
        a = rng.randint(1, 4); b = nz(rng, -5, 5); c = rng.choice([1, 2, 3, -1])
        base = rng.choice(['e', 2, 3, 10])
        if base == 'e':
            lhs = sp.log(a * x + b); lhs_l = f"\\ln({L(a*x+b)})"; sol = sp.solve(sp.Eq(lhs, c), x)[0]; raise_ = f"e^{{{c}}}"
        else:
            lhs = sp.log(a * x + b, base); lhs_l = f"\\log_{{{base}}}({L(a*x+b)})"; sol = sp.solve(sp.Eq(lhs, c), x)[0]; raise_ = f"{base}^{{{c}}} = {N(sp.Integer(base)**c)}"
        out.append(numeric_problem(S, f"Solve for $x$: ${lhs_l} = {c}$. Give an exact answer.", sol, difficulty=2,
            hints=["Rewrite the logarithmic equation in exponential form: $\\log_b u = c$ means $u = b^c$.", f"So ${L(a*x+b)} = {raise_}$; solve for $x$."],
            solution=[f"Exponential form: ${L(a*x+b)} = {raise_}$.", f"$x = {L(sol)}$."],
            verify={'kind': 'solve', 'lhs': str(lhs), 'rhs': c}))

    # expand with log laws (single variable)
    for _ in range(6):
        p_, q_ = rng.randint(2, 5), rng.randint(1, 3); c = rng.randint(1, 5)
        form = rng.choice(['quot', 'prod_root', 'power_quot'])
        if form == 'quot':
            inner = x**p_ / (x + c); expanded = p_ * sp.log(x) - sp.log(x + c)
            law = "$\\ln(A/B) = \\ln A - \\ln B$ and $\\ln(x^p) = p\\ln x$"
        elif form == 'prod_root':
            inner = x**p_ * sp.sqrt(x + c); expanded = p_ * sp.log(x) + sp.Rational(1, 2) * sp.log(x + c)
            law = "$\\ln(AB) = \\ln A + \\ln B$ and $\\ln\\sqrt{u} = \\tfrac12 \\ln u$"
        else:
            inner = (x + c)**q_ / x**p_; expanded = q_ * sp.log(x + c) - p_ * sp.log(x)
            law = "$\\ln(A/B) = \\ln A - \\ln B$, then bring each exponent down as a factor"
        out.append(equiv_problem(S, f"Use the laws of logarithms to expand $\\ln\\left({L(inner)}\\right)$ into a sum or difference of logarithms with no powers inside.", expanded, difficulty=2, domain=(0.5, 3),
            hints=["Products become sums, quotients become differences, exponents become coefficients.", f"Here use {law}."],
            solution=[f"$\\ln\\left({L(inner)}\\right)$: apply {law}.", f"$= {L(expanded)}$."],
            verify={'kind': 'equiv', 'expected': f'log({str(inner)})'}))

    # condense to a single log
    for _ in range(5):
        p_ = rng.randint(2, 4); c = rng.randint(2, 7); d = rng.randint(1, 4)
        form = rng.choice(['a', 'b'])
        if form == 'a':
            given = p_ * sp.log(x) + sp.log(c); single = sp.log(c * x**p_)
            given_l = f"{p_}\\ln x + \\ln {c}"
        else:
            given = sp.log(x + d) - p_ * sp.log(x); single = sp.log((x + d) / x**p_)
            given_l = f"\\ln(x + {d}) - {p_}\\ln x"
        out.append(equiv_problem(S, f"Write ${given_l}$ as a single logarithm.", single, difficulty=2, domain=(0.5, 3),
            hints=["Move each coefficient back inside as an exponent first.", "Then a sum of logs is the log of a product and a difference is the log of a quotient."],
            solution=[f"Turn the coefficient into an exponent: ${given_l} = {'\\ln x^{' + str(p_) + '} + \\ln ' + str(c) if form == 'a' else '\\ln(x + ' + str(d) + ') - \\ln x^{' + str(p_) + '}'}$.",
                      f"Combine: ${L(single)}$."],
            verify={'kind': 'equiv', 'expected': str(given)}))

    # f^{-1}(a) by solving f(x) = a
    for _ in range(6):
        form = rng.choice(['cube', 'exp', 'lin'])
        if form == 'cube':
            b = rng.randint(-3, 3); r = rng.randint(1, 3); f = x**3 + b; a = f.subs(x, r)
        elif form == 'exp':
            b = rng.randint(-2, 3); r = rng.randint(0, 3); f = 2**x + b; a = f.subs(x, r)
        else:
            m = nz(rng, -4, 4); b = rng.randint(-5, 5); r = rng.randint(-3, 3); f = m * x + b; a = f.subs(x, r)
        out.append(numeric_problem(S, f"Let $f(x) = {L(f)}$. Find $f^{{-1}}({N(a)})$ without finding a formula for $f^{{-1}}$.", r, difficulty=1,
            hints=["$f^{-1}(a)$ is the input $x$ with $f(x) = a$.", f"Solve ${L(f)} = {N(a)}$."],
            solution=[f"We need $x$ with ${L(f)} = {N(a)}$.", f"Solving gives $x = {r}$, so $f^{{-1}}({N(a)}) = {r}$."],
            verify={'kind': 'solve', 'lhs': str(f), 'rhs': str(a)}))

    # inverse trig exact values
    vals = [('\\arcsin', sp.asin, [sp.Rational(1, 2), sp.sqrt(2) / 2, sp.sqrt(3) / 2, 1, 0, -sp.Rational(1, 2), -1]),
            ('\\arccos', sp.acos, [sp.Rational(1, 2), sp.sqrt(2) / 2, sp.sqrt(3) / 2, 1, 0, -1, -sp.Rational(1, 2)]),
            ('\\arctan', sp.atan, [1, sp.sqrt(3), sp.sqrt(3) / 3, 0, -1, -sp.sqrt(3)])]
    for _ in range(7):
        nm, fn, args = pick(rng, vals)
        a = pick(rng, args)
        v = fn(a)
        out.append(numeric_problem(S, f"Find the exact value of ${nm}\\left({L(a)}\\right)$.", v, difficulty=2,
            hints=[f"${nm} u$ is the angle in the principal range whose {nm[1:]}e is $u$." if nm != '\\arctan' else "$\\arctan u$ is the angle in $(-\\pi/2, \\pi/2)$ whose tangent is $u$.",
                   {"\\arcsin": "The range of $\\arcsin$ is $[-\\pi/2, \\pi/2]$; recall the special angles $\\pi/6, \\pi/4, \\pi/3$.",
                    "\\arccos": "The range of $\\arccos$ is $[0, \\pi]$; negative inputs give angles bigger than $\\pi/2$.",
                    "\\arctan": "Use the special angles whose tangent is $1$, $\\sqrt3$ or $1/\\sqrt3$."}[nm]],
            solution=[f"We need the angle $\\theta$ in the principal range with $\\{nm[4:]} \\theta = {L(a)}$.",
                      f"That angle is $\\theta = {L(v)}$, so ${nm}\\left({L(a)}\\right) = {L(v)}$."],
            verify={'kind': 'numeric', 'value': str(v)}))

    # domain of ln(ax+b)
    for _ in range(4):
        a = rng.randint(1, 4); b = nz(rng, -6, 6)
        f = sp.log(a * x + b); lo = sp.Rational(-b, a)
        out.append(interval_problem(S, f"Find the domain of $f(x) = {L(f)}$. Answer in interval notation.", interval_str(lo, sp.oo, True, True), f'{a}*x+{b} > 0', difficulty=1,
            hints=["A logarithm is defined only for positive inputs.", f"Solve ${L(a*x+b)} > 0$."],
            solution=[f"Need ${L(a*x+b)} > 0$, i.e. $x > {N(lo)}$.", f"Domain: $({N(lo)}, \\infty)$."]))

    # cancellation equations
    for _ in range(5):
        form = rng.choice(['e_ln', 'ln_e', 'log_b'])
        if form == 'e_ln':
            c = rng.randint(2, 9); expr = sp.exp(sp.log(c)); stmt = f"Simplify $e^{{\\ln {c}}}$."; val = c
            steps = ["$e^{\\ln u} = u$ for $u > 0$ because $\\ln$ and the exponential undo each other.", f"So $e^{{\\ln {c}}} = {c}$."]
        elif form == 'ln_e':
            c = rng.randint(2, 7); p_ = rng.choice([x**2, 3 * x, x + c]);
            out.append(equiv_problem(S, f"Simplify $\\ln\\left(e^{{{L(p_)}}}\\right)$.", p_, difficulty=1, domain=(-2, 2),
                hints=["$\\ln$ and $e^{(\\cdot)}$ are inverse functions.", "$\\ln(e^u) = u$ for every real $u$."],
                solution=["$\\ln(e^u) = u$ for all real $u$.", f"So $\\ln\\left(e^{{{L(p_)}}}\\right) = {L(p_)}$."],
                verify={'kind': 'equiv', 'expected': f'log(exp({str(p_)}))'}))
            continue
        else:
            b = rng.choice([2, 3, 5]); c = rng.randint(2, 6); stmt = f"Simplify ${b}^{{\\log_{{{b}}} {c}}}$."; val = c; expr = sp.Integer(b)**sp.log(c, b)
            steps = [f"$b^{{\\log_b u}} = u$ because the exponential with base $b$ undoes $\\log_b$.", f"So ${b}^{{\\log_{{{b}}} {c}}} = {c}$."]
        out.append(numeric_problem(S, stmt, val, difficulty=1, hints=["Exponential and logarithmic functions with the same base are inverses.", "Apply the cancellation equation $b^{\\log_b u} = u$ or $e^{\\ln u} = u$."], solution=steps, verify={'kind': 'numeric', 'value': str(expr)}))

    # one-to-one conceptual
    for _ in range(4):
        a = rng.randint(1, 4)
        opts = [(f"$f(x) = x^3 + {a}$", 'cube'), (f"$f(x) = x^2 - {a}$", 'sq'), (f"$f(x) = |x| + {a}$", 'abs'), (f"$f(x) = \\cos x$", 'cos')]
        out.append(label_mc(S, "Which of these functions is one-to-one on its whole domain (and therefore has an inverse)?", opts, 'cube', rng, difficulty=2,
            hints=["One-to-one means different inputs always give different outputs: no horizontal line crosses the graph twice.",
                   "Functions that are symmetric about the $y$-axis or periodic repeat output values."],
            solution=["$x^2 - a$, $|x| + a$ and $\\cos x$ all take the same value at two different inputs (for example at $x$ and $-x$), so they fail the horizontal line test.",
                      f"$x^3 + {a}$ is strictly increasing, so it is one-to-one and has the inverse $\\sqrt[3]{{x - {a}}}$."]))
    return out


def build() -> dict:
    from stewart import tidy
    return {
        'functions-basics': tidy(functions_basics()),
        'essential-functions': tidy(essential_functions()),
        'new-functions-from-old': tidy(new_functions_from_old()),
        'exponential-functions': tidy(exponential_functions()),
        'inverse-functions-and-logs': tidy(inverse_functions_and_logs()),
    }
