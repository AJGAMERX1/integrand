"""Stewart Chapter 2 templates (original problems, SymPy-verified):
tangent-and-velocity (2.1), limits-intro (2.2), limit-laws (2.3), precise-limit (2.4), continuity (2.5),
limits-at-infinity (2.6), derivatives-rates (2.7), derivative-function (2.8).
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
                     label_mc, numeric_problem, equiv_problem, interval_problem, interval_str, interval_ltx, h, y, tidy)


def cases(branches) -> str:
    """branches: list of (expr, condition_latex). Returns a LaTeX cases block."""
    return "\\begin{cases} " + " \\\\ ".join(f"{L(e)} & \\text{{if }} {c}" for e, c in branches) + " \\end{cases}"


def pw2(left, right, a, left_closed=False):
    """Two-branch piecewise: left for x<a (or <=a), right otherwise. Returns (sympy, latex)."""
    cond = (x <= a) if left_closed else (x < a)
    f = sp.Piecewise((left, cond), (right, True))
    lt = cases([(left, f"x {'\\le' if left_closed else '<'} {a}"), (right, f"x {'>' if left_closed else '\\ge'} {a}")])
    return f, lt


# ======================================================================
# 2.1 tangent-and-velocity
# ======================================================================

def tangent_and_velocity():
    S = 'tangent-and-velocity'
    rng = seeded(S)
    out = []
    curves = [lambda: x**2 + rng.randint(-3, 3), lambda: rng.randint(2, 4) * x**2 - rng.randint(1, 3) * x, lambda: x**3 - rng.randint(1, 4) * x,
              lambda: rng.randint(1, 3) * x**2 + rng.randint(1, 4), lambda: 2**x, lambda: x**3 + rng.randint(1, 3)]

    # secant slope between two points on a curve
    for _ in range(10):
        f = pick(rng, curves)(); a = rng.randint(-2, 3); b = a + rng.choice([1, 2, sp.Rational(1, 2)])
        fa, fb = f.subs(x, a), f.subs(x, b)
        m = (fb - fa) / (b - a)
        out.append(numeric_problem(S, f"Let $f(x) = {L(f)}$. Find the slope of the secant line through the points on the graph where $x = {N(a)}$ and $x = {N(b)}$.", m, difficulty=1,
            hints=["A secant line joins two points on the curve; its slope is rise over run.", f"Compute $f({N(b)})$ and $f({N(a)})$ first, then divide their difference by ${N(b)} - {N(a)}$."],
            solution=[f"$f({N(a)}) = {N(fa)}$ and $f({N(b)}) = {N(fb)}$.", f"Slope $= \\dfrac{{{N(fb)} - {N(fa)}}}{{{N(b)} - {N(a)}}} = {N(m)}$."],
            verify={'kind': 'evaluate', 'expr': f'(({str(f)}) - ({str(fa)}))/(x - ({a}))', 'at': b}))

    # average velocity
    for _ in range(10):
        form = rng.choice(['fall', 'poly'])
        if form == 'fall':
            H = rng.choice([40, 50, 80, 100, 120]); s = H - 5 * t**2
            t1 = rng.randint(0, 2); t2 = t1 + rng.choice([1, 2, sp.Rational(1, 2)])
            stmt = f"A stone is dropped from a height of ${H}$ m and its height after $t$ seconds is $s(t) = {L(s)}$. Find the average velocity over the time interval $[{N(t1)}, {N(t2)}]$ (in m/s)."
        else:
            s = t**3 - rng.randint(2, 6) * t**2 + rng.randint(1, 9) * t
            t1 = rng.randint(0, 3); t2 = t1 + rng.choice([1, 2, 3])
            stmt = f"A particle moves along a line with position $s(t) = {L(s)}$ (meters, $t$ in seconds). Find its average velocity over $[{t1}, {t2}]$."
        v = (s.subs(t, t2) - s.subs(t, t1)) / (t2 - t1)
        out.append(numeric_problem(S, stmt, v, difficulty=1,
            hints=["Average velocity is displacement divided by elapsed time.", f"Displacement is $s({N(t2)}) - s({N(t1)})$."],
            solution=[f"$s({N(t2)}) = {N(s.subs(t, t2))}$ and $s({N(t1)}) = {N(s.subs(t, t1))}$.", f"Average velocity $= \\dfrac{{{N(s.subs(t, t2))} - ({N(s.subs(t, t1))})}}{{{N(t2)} - {N(t1)}}} = {N(v)}$ m/s."],
            verify={'kind': 'evaluate', 'expr': f'(({str(s.subs(t, x))}) - ({str(s.subs(t, t1))}))/(x - ({t1}))', 'at': t2}))

    # limiting value of secant slopes (tangent slope) as h -> 0, with a table
    for _ in range(11):
        f = pick(rng, curves[:4] + [curves[5]])(); a = rng.randint(-2, 3)
        sec = (f.subs(x, a + h) - f.subs(x, a)) / h
        rows = [(hh, float(sec.subs(h, hh))) for hh in (0.5, 0.1, 0.01, 0.001)]
        table = "\\begin{array}{c|c} h & \\text{secant slope over } [" + str(a) + ", " + str(a) + "+h] \\\\ \\hline " + " \\\\ ".join(f"{hh} & {v:.4f}" for hh, v in rows) + " \\end{array}"
        val = sp.limit(sec, h, 0)
        if rng.random() < 0.5:
            stmt = f"For $f(x) = {L(f)}$, the slopes of secant lines through $P({a}, {N(f.subs(x, a))})$ and $Q({a}+h, f({a}+h))$ are tabulated: ${table}$. What is the slope of the tangent line at $P$?"
        else:
            stmt = f"Let $f(x) = {L(f)}$ and $P = ({a}, {N(f.subs(x, a))})$. Compute the slope of the secant line $PQ$ for $Q$ at $x = {a}+h$ with $h = 0.1, 0.01, 0.001$, and state the value the slopes approach (the slope of the tangent at $P$)."
        out.append(numeric_problem(S, stmt, val, difficulty=2,
            hints=["As $h$ shrinks, $Q$ slides toward $P$ and the secant line turns into the tangent line.", f"The secant slopes are {', '.join(f'{v:.4f}' for _, v in rows[1:])}; look at the number they settle on."],
            solution=[f"Secant slope $= \\dfrac{{f({a}+h) - f({a})}}{{h}} = {L(sp.cancel(sec))}$ for $h \\ne 0$.", f"As $h \\to 0$ this approaches ${N(val)}$, the slope of the tangent at $P$."],
            verify={'kind': 'limit', 'expr': str(sec), 'to': 0}, variable='h'))

    # instantaneous velocity as a limit of average velocities
    for _ in range(7):
        s = rng.choice([H := rng.choice([45, 80, 100]), 0]) + rng.choice([-5, -5, 4]) * t**2 + rng.randint(0, 20) * t
        a = rng.randint(1, 3)
        avg = (s.subs(t, a + h) - s.subs(t, a)) / h
        val = sp.limit(avg, h, 0)
        out.append(numeric_problem(S, f"The position of an object is $s(t) = {L(s)}$ (meters after $t$ seconds). By computing average velocities over $[{a}, {a}+h]$ for smaller and smaller $h$, find the instantaneous velocity at $t = {a}$.", val, difficulty=3,
            hints=["Average velocity over $[a, a+h]$ is $\\dfrac{s(a+h) - s(a)}{h}$; simplify it as an expression in $h$.", "Then see what happens to that expression as $h$ approaches $0$."],
            solution=[f"$\\dfrac{{s({a}+h) - s({a})}}{{h}} = {L(sp.cancel(avg))}$.", f"Letting $h \\to 0$ gives the instantaneous velocity ${N(val)}$ m/s."],
            verify={'kind': 'limit', 'expr': str(avg), 'to': 0}, variable='h'))

    # secant line equation
    for _ in range(5):
        f = pick(rng, curves[:4])(); a = rng.randint(-2, 2); b = a + rng.randint(1, 3)
        fa, fb = f.subs(x, a), f.subs(x, b); m = (fb - fa) / (b - a)
        line = sp.expand(fa + m * (x - a))
        out.append(equiv_problem(S, f"Find an equation $y = mx + c$ of the secant line to $y = {L(f)}$ through the points with $x = {a}$ and $x = {b}$.", line, difficulty=2,
            hints=["First find both points on the curve, then the slope between them.", "Use point-slope form with either point."],
            solution=[f"Points: $({a}, {N(fa)})$ and $({b}, {N(fb)})$; slope $m = {N(m)}$.", f"$y - ({N(fa)}) = {N(m)}(x - ({a}))$, so $y = {L(line)}$."],
            verify={'kind': 'equiv', 'expected': f'({fa}) + (({fb}) - ({fa}))/(({b}) - ({a}))*(x - ({a}))'}))

    # secant slope from a table of positions
    for _ in range(5):
        ts = [0, 1, 2, 3, 4]; vals = [rng.randint(0, 30) for _ in ts]
        i, j = sorted(rng.sample(range(5), 2))
        v = sp.Rational(vals[j] - vals[i], ts[j] - ts[i])
        table = "\\begin{array}{c|ccccc} t\\ (\\text{s}) & " + " & ".join(map(str, ts)) + " \\\\ \\hline s\\ (\\text{m}) & " + " & ".join(map(str, vals)) + " \\end{array}"
        out.append(numeric_problem(S, f"The table gives the position $s$ of a cyclist at time $t$: ${table}$. Find the average velocity over $[{ts[i]}, {ts[j]}]$.", v, difficulty=1,
            hints=["Average velocity over an interval is the change in position divided by the change in time.", f"Read $s({ts[j]})$ and $s({ts[i]})$ from the table."],
            solution=[f"$s({ts[j]}) - s({ts[i]}) = {vals[j]} - {vals[i]} = {vals[j]-vals[i]}$ m over ${ts[j]-ts[i]}$ s.", f"Average velocity $= {N(v)}$ m/s."],
            verify={'kind': 'numeric', 'value': f'({vals[j]} - {vals[i]})/({ts[j]} - {ts[i]})'}))

    # conceptual
    concept = [
        ("The slope of the tangent line to $y = f(x)$ at $x = a$ is best described as", [("the limiting value of secant slopes $\\dfrac{f(a+h)-f(a)}{h}$ as $h \\to 0$", 'limit'), ("the secant slope for $h = 1$", 'h1'), ("the value $f(a)$", 'fa'), ("the average of $f(a-1)$ and $f(a+1)$", 'avg')], 'limit',
         ["Tangent lines come from secant lines through points that get closer and closer.", "The key word is 'limit' as the second point approaches $P$."],
         ["A secant through $P(a, f(a))$ and $Q(a+h, f(a+h))$ has slope $\\frac{f(a+h)-f(a)}{h}$.", "The tangent slope is the value these secant slopes approach as $h \\to 0$."]),
        ("Instantaneous velocity at time $t = a$ is", [("the limit of average velocities over $[a, a+h]$ as $h \\to 0$", 'limit'), ("the average velocity over $[0, a]$", 'avg0'), ("the position $s(a)$", 'pos'), ("the total distance traveled divided by $a$", 'dist')], 'limit',
         ["Average velocity needs an interval; instantaneous velocity is what those averages tend to as the interval shrinks.", "Think of a speedometer reading at one instant."],
         ["Average velocity over $[a, a+h]$ is $\\frac{s(a+h)-s(a)}{h}$.", "Instantaneous velocity is its limit as $h \\to 0$, matching the tangent slope on the position graph."]),
        ("If the position of a car is graphed against time, the average velocity over $[t_1, t_2]$ is", [("the slope of the secant line between the two points on the graph", 'secant'), ("the slope of the tangent line at $t_1$", 'tan'), ("the area under the graph", 'area'), ("the height of the graph at $t_2$", 'height')], 'secant',
         ["Average velocity is a difference quotient: change in position over change in time.", "Rise over run between two points on a graph is a secant slope."],
         ["$\\frac{s(t_2)-s(t_1)}{t_2-t_1}$ is rise over run between $(t_1, s(t_1))$ and $(t_2, s(t_2))$.", "That is exactly the slope of the secant line through those points."]),
    ]
    for stmt, opts, lab, hints, sol in concept:
        out.append(label_mc(S, stmt, opts, lab, rng, difficulty=1, hints=hints, solution=sol))
    return out


# ======================================================================
# 2.2 limits-intro
# ======================================================================

def limits_intro():
    S = 'limits-intro'
    rng = seeded(S)
    out = []

    # one-sided limits of piecewise functions (numeric) and the two-sided limit (choice)
    for _ in range(15):
        a = rng.randint(-2, 3)
        left = rng.choice([x**2 + rng.randint(-3, 3), nz(rng, -3, 3) * x + rng.randint(-4, 4), rng.randint(2, 4) - x])
        right = rng.choice([nz(rng, -3, 3) * x + rng.randint(-4, 4), x**2 - rng.randint(0, 4), sp.sqrt(x + rng.randint(3, 6))])
        f, lt = pw2(left, right, a)
        lv, rv = left.subs(x, a), right.subs(x, a)
        side = rng.choice(['-', '+'])
        v = lv if side == '-' else rv
        if rng.random() < 0.55:
            out.append(numeric_problem(S, f"Let $f(x) = {lt}$. Find $\\displaystyle\\lim_{{x \\to {a}^{side}}} f(x)$.", v, difficulty=1,
                hints=[f"For $x \\to {a}^{side}$ only values of $x$ {'less' if side == '-' else 'greater'} than ${a}$ matter.", f"Use the {'first' if side == '-' else 'second'} formula and let $x$ approach ${a}$."],
                solution=[f"Near ${a}$ on the {'left' if side == '-' else 'right'}, $f(x) = {L(left if side == '-' else right)}$.", f"Substituting $x = {a}$ gives $\\lim_{{x \\to {a}^{side}}} f(x) = {N(v)}$."],
                verify={'kind': 'limit', 'expr': str(f), 'to': a, 'dir': side}))
        else:
            out.append(limit_class_mc(S, f"Let $f(x) = {lt}$. Find $\\displaystyle\\lim_{{x \\to {a}}} f(x)$.", f, a, rng, difficulty=2,
                hints=["Compute the left-hand and right-hand limits separately from the two formulas.", "A two-sided limit exists only when both one-sided limits exist and agree."],
                solution=[f"Left: $\\lim_{{x \\to {a}^-}} f(x) = {N(lv)}$. Right: $\\lim_{{x \\to {a}^+}} f(x) = {N(rv)}$.",
                          f"{'They agree, so the limit is $' + N(lv) + '$.' if sp.simplify(lv - rv) == 0 else 'They differ, so the two-sided limit does not exist.'}"],
                extra=[lv, rv] if sp.simplify(lv - rv) != 0 else None))

    # infinite limits and one-sided infinite limits
    for _ in range(10):
        a = rng.randint(-3, 3); c = nz(rng, -4, 4)
        form = rng.choice(['sq', 'one_left', 'one_right', 'sq_neg'])
        if form == 'sq':
            f = c / (x - a)**2; d = None
        elif form == 'sq_neg':
            f = c / (x - a)**2 - rng.randint(1, 3); d = None
        else:
            f = c / (x - a); d = '-' if form == 'one_left' else '+'
        stmt = f"Evaluate $\\displaystyle\\lim_{{x \\to {a}{'^' + d if d else ''}}} {L(f)}$."
        out.append(limit_class_mc(S, stmt, f, a, rng, difficulty=2, direction=d,
            hints=[f"As $x \\to {a}$ the denominator approaches $0$ while the numerator does not, so the values blow up.", "Decide the sign: is the denominator positive or negative for $x$ slightly " + ("to the left" if d == '-' else ("to the right" if d == '+' else "on either side")) + f" of ${a}$?"],
            solution=[f"Near $x = {a}$, ${L(sp.denom(sp.together(f)))}$ is tiny" + (" and positive on both sides (it is a square)" if 'sq' in form else f" and {'negative' if d == '-' else 'positive'} for $x$ {'<' if d == '-' else '>'} {a}$") + ".",
                      f"Dividing ${c}$ by a tiny {'positive' if 'sq' in form or d == '+' else 'negative'} number gives huge {'positive' if (c > 0) == ('sq' in form or d == '+') else 'negative'} values; the limit is ${'\\infty' if (c > 0) == ('sq' in form or d == '+') else '-\\infty'}$."]))

    # vertical asymptote location
    for _ in range(5):
        a = nz(rng, -5, 5); c = rng.randint(1, 4); k = rng.choice([1, 2, 3])
        f = (x + c) / (k * x - k * a)
        out.append(numeric_problem(S, f"The curve $y = {L(f)}$ has exactly one vertical asymptote. Find its equation's value $x = a$.", a, difficulty=1,
            hints=["Vertical asymptotes occur where the denominator is $0$ but the numerator is not.", "Set the denominator equal to zero and solve."],
            solution=[f"${L(sp.denom(f))} = 0$ gives $x = {a}$, and the numerator there is ${a + c} \\ne 0$.", f"So $|f(x)| \\to \\infty$ as $x \\to {a}$: the vertical asymptote is $x = {a}$."],
            verify={'kind': 'solve', 'lhs': str(sp.denom(f)), 'rhs': 0}))

    # guess a limit from a table (function with a removable hole)
    for _ in range(8):
        a = nz(rng, -3, 3); b = nz(rng, -4, 4, exclude=(0, a))
        form = rng.choice(['poly', 'root', 'trig'])
        if form == 'poly':
            f = sp.cancel((x - a) * (x - b)) / (x - a)
            f = ((x - a) * (x - b)).expand() / (x - a)
        elif form == 'root':
            a = rng.randint(1, 4); f = (sp.sqrt(x + rng.choice([0, 1, 4, 5])) - sp.sqrt(sp.Integer(a) + 0))
            c0 = rng.choice([0, 1, 4, 5]); f = (sp.sqrt(x + c0) - sp.sqrt(a + c0)) / (x - a)
        else:
            a = 0; kk = rng.randint(2, 5); f = sp.sin(kk * x) / x
        val = sp.limit(f, x, a)
        pts = [a - 0.1, a - 0.01, a - 0.001, a + 0.001, a + 0.01, a + 0.1]
        table = "\\begin{array}{c|" + "c" * 6 + "} x & " + " & ".join(f"{p:g}" for p in pts) + " \\\\ \\hline f(x) & " + " & ".join(f"{float(f.subs(x, p)):.4f}" for p in pts) + " \\end{array}"
        out.append(numeric_problem(S, f"Let $f(x) = {L(f)}$, which is undefined at $x = {a}$. Its values near ${a}$ are ${table}$. Guess the value of $\\displaystyle\\lim_{{x \\to {a}}} f(x)$.", val, difficulty=2,
            hints=["A limit describes the value $f(x)$ gets close to, not the value at the point itself.", "Read the table from both sides toward the middle and look for the common target."],
            solution=[f"From both sides the values approach ${N(val)}$ (they get closer the nearer $x$ is to ${a}$).", f"So $\\lim_{{x \\to {a}}} f(x) = {N(val)}$ even though $f({a})$ is undefined."],
            verify={'kind': 'limit', 'expr': str(f), 'to': a}, tolerance=1e-4))

    # |x-a|/(x-a) and friends
    for _ in range(5):
        a = rng.randint(-3, 3); c = nz(rng, -3, 3)
        f = c * sp.Abs(x - a) / (x - a)
        side = rng.choice([None, '-', '+'])
        if side is None:
            out.append(limit_class_mc(S, f"Evaluate $\\displaystyle\\lim_{{x \\to {a}}} {L(f)}$.", f, a, rng, difficulty=2,
                hints=["Rewrite $|x - a|$ as $x - a$ when $x > a$ and as $-(x - a)$ when $x < a$.", "Compare the one-sided limits."],
                solution=[f"For $x > {a}$: $f(x) = {c}$. For $x < {a}$: $f(x) = {-c}$.", "The one-sided limits differ, so the two-sided limit does not exist."], extra=[c, -c]))
        else:
            v = c if side == '+' else -c
            out.append(numeric_problem(S, f"Evaluate $\\displaystyle\\lim_{{x \\to {a}^{side}}} {L(f)}$.", v, difficulty=1,
                hints=[f"For $x {'<' if side == '-' else '>'} {a}$, the quantity $x - {a}$ is {'negative' if side == '-' else 'positive'}.", "Replace the absolute value with the appropriate signed expression and simplify."],
                solution=[f"For $x {'<' if side == '-' else '>'} {a}$, $|x - {a}| = {'-(x - ' + str(a) + ')' if side == '-' else 'x - ' + str(a)}$, so $f(x) = {v}$ there.", f"Hence the one-sided limit is ${v}$."],
                verify={'kind': 'limit', 'expr': str(f), 'to': a, 'dir': side}))

    # limits of sqrt near the edge of the domain
    for _ in range(4):
        a = rng.randint(-3, 3); c = rng.randint(1, 3)
        f = sp.sqrt(x - a) + c
        out.append(numeric_problem(S, f"Evaluate $\\displaystyle\\lim_{{x \\to {a}^+}} \\left({L(f)}\\right)$.", c, difficulty=1,
            hints=["From the right, $x - a$ is a small positive number, so the square root is defined.", "The square root of a number approaching $0$ approaches $0$."],
            solution=[f"For $x$ slightly larger than ${a}$, $\\sqrt{{x - ({a})}} \\to 0$.", f"So the limit is $0 + {c} = {c}$."],
            verify={'kind': 'limit', 'expr': str(f), 'to': a, 'dir': '+'}))

    # oscillating: sin(k/x) at 0 vs x sin(1/x)
    for _ in range(4):
        kk = rng.randint(1, 5)
        if rng.random() < 0.5:
            f = sp.sin(kk * sp.pi / x)
            out.append(limit_class_mc(S, f"Evaluate $\\displaystyle\\lim_{{x \\to 0}} \\sin\\left(\\dfrac{{{kk}\\pi}}{{x}}\\right)$.", f, 0, rng, difficulty=3,
                hints=["Try $x = 1, 1/2, 1/3, \\dots$ and then $x = 2/(4n+1)$-type values; what happens to the inside?", "If you can find two sequences of $x$-values approaching $0$ along which $f$ approaches different numbers, the limit does not exist."],
                solution=[f"For $x = {kk}/n$ the function is $\\sin(n\\pi) = 0$, but for $x = {2*kk}/(4n+1)$ it is $\\sin((4n+1)\\pi/2) = 1$.", "Values keep oscillating between $-1$ and $1$ no matter how close $x$ is to $0$, so the limit does not exist."], extra=[0, 1]))
        else:
            f = x * sp.sin(kk / x)
            out.append(numeric_problem(S, f"Evaluate $\\displaystyle\\lim_{{x \\to 0}} x\\sin\\left(\\dfrac{{{kk}}}{{x}}\\right)$.", 0, difficulty=3,
                hints=["The sine factor stays between $-1$ and $1$ no matter how wildly it oscillates.", "Multiplying a bounded quantity by something approaching $0$ gives something approaching $0$."],
                solution=[f"$-|x| \\le x\\sin({kk}/x) \\le |x|$ for all $x \\ne 0$.", "Both $-|x|$ and $|x|$ approach $0$, so the squeezed function does too: the limit is $0$."],
                verify={'kind': 'limit', 'expr': str(f), 'to': 0}))

    # conceptual
    for _ in range(4):
        a = rng.randint(1, 5); Lv = rng.randint(2, 9)
        opts = [(f"$f(x)$ can be made as close to ${Lv}$ as we like by taking $x$ close enough to ${a}$ (but not equal to ${a}$)", 'def'),
                (f"$f({a}) = {Lv}$", 'value'), (f"$f(x) = {Lv}$ for all $x$ near ${a}$", 'const'), (f"$f$ is defined at $x = {a}$", 'defined')]
        out.append(label_mc(S, f"Which statement is the meaning of $\\displaystyle\\lim_{{x \\to {a}}} f(x) = {Lv}$?", opts, 'def', rng, difficulty=1,
            hints=["A limit is about the values of $f$ near the point, not at the point.", "The function may even be undefined at $a$ and still have a limit there."],
            solution=["The limit statement says the outputs approach $L$ as the inputs approach $a$ from either side, with $x \\ne a$.", "It says nothing about $f(a)$ itself, which may be different or undefined."]))
    return out


# ======================================================================
# 2.3 limit-laws
# ======================================================================

def limit_laws():
    S = 'limit-laws'
    rng = seeded(S)
    out = []

    # combine given limits
    for _ in range(8):
        A, B = nz(rng, -5, 6), nz(rng, -4, 5); a = rng.randint(-2, 3)
        form = rng.choice(['lin', 'prod', 'quot', 'pow', 'root'])
        if form == 'lin':
            c1, c2 = nz(rng, -3, 3), nz(rng, -3, 3); expr_l = f"[{c1}f(x) {signed(c2)}g(x)]"; val = sp.sympify(f'{c1}*({A}) + ({c2})*({B})'); vs = f'{c1}*({A}) + ({c2})*({B})'
            law = "the sum and constant-multiple laws"
        elif form == 'prod':
            expr_l = "[f(x)\\,g(x)]"; val = A * B; vs = f'({A})*({B})'; law = "the product law"
        elif form == 'quot':
            expr_l = "\\dfrac{f(x)}{g(x)}"; val = sp.Rational(A, B); vs = f'({A})/({B})'; law = "the quotient law (allowed since the limit of $g$ is not $0$)"
        elif form == 'pow':
            expr_l = "[f(x)]^2 - g(x)"; val = A * A - B; vs = f'({A})**2 - ({B})'; law = "the power and difference laws"
        else:
            A = rng.choice([1, 4, 9, 16]); expr_l = "\\sqrt{f(x)} + g(x)"; val = sp.sqrt(A) + B; vs = f'sqrt({A}) + ({B})'; law = "the root and sum laws"
        out.append(numeric_problem(S, f"Suppose $\\displaystyle\\lim_{{x \\to {a}}} f(x) = {A}$ and $\\displaystyle\\lim_{{x \\to {a}}} g(x) = {B}$. Find $\\displaystyle\\lim_{{x \\to {a}}} {expr_l}$.", val, difficulty=1,
            hints=["Limit laws let you push the limit inside sums, products, quotients and powers.", f"Apply {law}, then substitute the given limit values."],
            solution=[f"By {law}, the limit equals the same combination of ${A}$ and ${B}$.", f"$= {N(val)}$."],
            verify={'kind': 'numeric', 'value': vs}))

    # direct substitution
    for _ in range(7):
        a = rng.randint(-3, 3)
        f = rng.choice([rng.randint(1, 3) * x**2 + nz(rng, -4, 4) * x + rng.randint(-5, 5), (x**2 + rng.randint(1, 5)) / (x + rng.choice([v for v in range(-4, 5) if v != -a])), sp.sqrt(x**2 + rng.choice([1, 4, 9, 16]) - 0)])
        if f.has(sp.sqrt) and not (f.subs(x, a)).is_rational:
            f = sp.sqrt(x**2 + 16 - a * a + 9 - 9) if False else x**3 - rng.randint(1, 4) * x
        val = f.subs(x, a)
        out.append(numeric_problem(S, f"Evaluate $\\displaystyle\\lim_{{x \\to {a}}} \\left({L(f)}\\right)$.", val, difficulty=1,
            hints=["Polynomials and rational functions are continuous wherever they are defined, so limits can be found by direct substitution.", f"Check that substituting $x = {a}$ does not make a denominator zero, then substitute."],
            solution=[f"Direct substitution is valid here because the function is defined at $x = {a}$.", f"$\\lim_{{x \\to {a}}} {L(f)} = {N(val)}$."],
            verify={'kind': 'limit', 'expr': str(f), 'to': a}))

    # factor and cancel 0/0
    for _ in range(10):
        a = nz(rng, -4, 4); b = nz(rng, -5, 5, exclude=(0, a)); k = rng.choice([1, 1, 2, 3])
        form = rng.choice(['quad_lin', 'quad_quad', 'cube'])
        if form == 'quad_lin':
            f = sp.expand(k * (x - a) * (x - b)) / (x - a); fac = f"{'' if k == 1 else k}(x {signed(-a)})(x {signed(-b)})"
            canceled = k * (x - b)
        elif form == 'quad_quad':
            c = nz(rng, -5, 5, exclude=(0, a, b)); f = sp.expand((x - a) * (x - b)) / sp.expand((x - a) * (x - c)); fac = f"(x {signed(-a)})(x {signed(-b)})"
            canceled = (x - b) / (x - c)
        else:
            f = (x**3 - a**3) / (x - a); fac = f"(x {signed(-a)})(x^2 {signed(a)}x + {a*a})"; canceled = x**2 + a * x + a * a
        val = sp.limit(f, x, a)
        out.append(numeric_problem(S, f"Evaluate $\\displaystyle\\lim_{{x \\to {a}}} {L(f)}$.", val, difficulty=2,
            hints=[f"Substituting $x = {a}$ gives $0/0$, so simplify first.", f"Factor the {'numerator' if form != 'quad_quad' else 'numerator and denominator'}; $(x {signed(-a)})$ is a common factor."],
            solution=[f"The numerator factors as ${fac}$, so for $x \\ne {a}$ the fraction equals ${L(canceled)}$.", f"Now substitute: $\\lim_{{x \\to {a}}} {L(canceled)} = {N(val)}$."],
            verify={'kind': 'limit', 'expr': str(f), 'to': a}))

    # rationalize
    for _ in range(7):
        c = rng.choice([0, 1, 2, 3, 5]); a = rng.choice([v for v in [1, 2, 3, 4, 6, 7, 9, 11, 14] if sp.sqrt(v + c).is_rational]) if any(sp.sqrt(v + c).is_rational for v in [1, 2, 3, 4, 6, 7, 9, 11, 14]) else 4
        r = sp.sqrt(a + c)
        form = rng.choice(['num', 'den'])
        if form == 'num':
            f = (sp.sqrt(x + c) - r) / (x - a)
            conj = f"\\sqrt{{x {signed(c)}}} + {N(r)}" if c else f"\\sqrt{{x}} + {N(r)}"
        else:
            f = (x - a) / (sp.sqrt(x + c) - r)
            conj = f"\\sqrt{{x {signed(c)}}} + {N(r)}" if c else f"\\sqrt{{x}} + {N(r)}"
        val = sp.limit(f, x, a)
        out.append(numeric_problem(S, f"Evaluate $\\displaystyle\\lim_{{x \\to {a}}} {L(f)}$.", val, difficulty=2,
            hints=["Direct substitution gives $0/0$; multiply numerator and denominator by the conjugate of the root expression.", f"The conjugate is ${conj}$; the product $(\\sqrt{{u}} - r)(\\sqrt{{u}} + r) = u - r^2$ removes the root."],
            solution=[f"Multiply top and bottom by ${conj}$: the {'numerator' if form == 'num' else 'denominator'} becomes $(x {signed(c)}) - {N(r*r)} = x - {a}$, which cancels with the other factor.",
                      f"What remains is ${L(sp.simplify(f * (sp.sqrt(x+c) + r) / (sp.sqrt(x+c) + r)))}$ for $x \\ne {a}$; substituting $x = {a}$ gives ${N(val)}$."],
            verify={'kind': 'limit', 'expr': str(f), 'to': a}))

    # complex fraction
    for _ in range(5):
        a = nz(rng, -4, 4)
        f = (1 / x - sp.Rational(1, a)) / (x - a)
        val = sp.limit(f, x, a)
        out.append(numeric_problem(S, f"Evaluate $\\displaystyle\\lim_{{x \\to {a}}} {L(f)}$.", val, difficulty=3,
            hints=["Combine the two fractions in the numerator over a common denominator first.", f"You should get $\\dfrac{{{a} - x}}{{{a}x}}$ on top; then the factor $x - {a}$ cancels."],
            solution=[f"$\\dfrac{{1}}{{x}} - \\dfrac{{1}}{{{a}}} = \\dfrac{{{a} - x}}{{{a}x}}$, so the expression equals $\\dfrac{{{a} - x}}{{{a}x(x - {a})}} = -\\dfrac{{1}}{{{a}x}}$.", f"Substituting $x = {a}$: $-\\dfrac{{1}}{{{a*a}}} = {N(val)}$."],
            verify={'kind': 'limit', 'expr': str(f), 'to': a}))

    # difference quotient limits in h
    for _ in range(6):
        a = rng.randint(-2, 3); p_ = rng.choice([2, 2, 3])
        f = ((a + h)**p_ - a**p_) / h
        val = sp.limit(f, h, 0)
        out.append(numeric_problem(S, f"Evaluate $\\displaystyle\\lim_{{h \\to 0}} \\dfrac{{({a}+h)^{p_} - {a**p_}}}{{h}}$.", val, difficulty=2,
            hints=[f"Expand $({a}+h)^{p_}$; the constant term cancels with ${a**p_}$.", "Every remaining term has a factor $h$ that cancels with the denominator."],
            solution=[f"$({a}+h)^{p_} - {a**p_} = {L(sp.expand((a+h)**p_ - a**p_))}$.", f"Dividing by $h$ leaves ${L(sp.cancel(f))}$, which approaches ${N(val)}$ as $h \\to 0$."],
            verify={'kind': 'limit', 'expr': str(f), 'to': 0}, variable='h'))

    # squeeze theorem with explicit bounds
    for _ in range(5):
        a = rng.randint(0, 3); Lv = rng.randint(-3, 5)
        lo = Lv + rng.randint(1, 3) * (x - a); hi = Lv + rng.randint(1, 3) * (x - a)**2
        out.append(numeric_problem(S, f"Suppose ${L(lo)} \\le f(x) \\le {L(sp.expand(hi))}$ for all $x$ near ${a}$. Find $\\displaystyle\\lim_{{x \\to {a}}} f(x)$.", Lv, difficulty=2,
            hints=["Use the Squeeze Theorem: find the limits of the two bounding functions.", "If both bounds approach the same number, $f$ is forced to approach it too."],
            solution=[f"$\\lim_{{x \\to {a}}} ({L(lo)}) = {Lv}$ and $\\lim_{{x \\to {a}}} ({L(sp.expand(hi))}) = {Lv}$.", f"By the Squeeze Theorem, $\\lim_{{x \\to {a}}} f(x) = {Lv}$."],
            verify={'kind': 'limit', 'expr': str(lo), 'to': a}))
    for _ in range(3):
        kk = rng.randint(1, 4); p_ = rng.choice([2, 4])
        f = x**p_ * sp.cos(kk / x)
        out.append(numeric_problem(S, f"Use the Squeeze Theorem to evaluate $\\displaystyle\\lim_{{x \\to 0}} x^{p_}\\cos\\left(\\dfrac{{{kk}}}{{x}}\\right)$.", 0, difficulty=3,
            hints=["$-1 \\le \\cos(\\text{anything}) \\le 1$.", f"Multiply the inequality by $x^{p_} \\ge 0$ to trap the function between $-x^{p_}$ and $x^{p_}$."],
            solution=[f"$-x^{p_} \\le x^{p_}\\cos({kk}/x) \\le x^{p_}$ for $x \\ne 0$.", f"Both $-x^{p_}$ and $x^{p_}$ approach $0$ as $x \\to 0$, so the limit is $0$."],
            verify={'kind': 'limit', 'expr': str(f), 'to': 0}))

    # one-sided with absolute value in a quotient
    for _ in range(4):
        a = nz(rng, -3, 3); side = rng.choice(['-', '+'])
        f = (x**2 - a * a) / sp.Abs(x - a)
        val = sp.limit(f, x, a, side)
        out.append(numeric_problem(S, f"Evaluate $\\displaystyle\\lim_{{x \\to {a}^{side}}} \\dfrac{{x^2 - {a*a}}}{{|x - ({a})|}}$.", val, difficulty=3,
            hints=[f"For $x {'<' if side == '-' else '>'} {a}$, $|x - ({a})| = {'-(x - (' + str(a) + '))' if side == '-' else 'x - (' + str(a) + ')'}$.", f"Factor $x^2 - {a*a} = (x - ({a}))(x + ({a}))$ and cancel."],
            solution=[f"On this side the expression equals ${'-' if side == '-' else ''}(x + ({a}))$ after canceling $x - ({a})$.", f"Substituting $x = {a}$ gives ${N(val)}$."],
            verify={'kind': 'limit', 'expr': str(f), 'to': a, 'dir': side}))

    # conceptual: when the quotient law fails
    for _ in range(3):
        a = rng.randint(1, 4)
        opts = [("the limit might still exist; simplify the expression first (for example, factor and cancel)", 'simplify'), ("the limit is $0$", 'zero'), ("the limit does not exist", 'dne'), ("the limit equals $1$", 'one')]
        out.append(label_mc(S, f"When evaluating $\\displaystyle\\lim_{{x \\to {a}}} \\dfrac{{f(x)}}{{g(x)}}$ you find that $f({a}) = 0$ and $g({a}) = 0$. What can you conclude?", opts, 'simplify', rng, difficulty=1,
            hints=["$0/0$ is called an indeterminate form; it carries no information by itself.", f"Compare $\\frac{{x - {a}}}{{x - {a}}}$ and $\\frac{{(x-{a})^2}}{{x - {a}}}$ near ${a}$."],
            solution=["The quotient law needs the denominator's limit to be nonzero, so it does not apply; but $0/0$ does not decide the answer.", "Algebra (factoring, rationalizing, combining fractions) often produces an equivalent expression whose limit can be found."]))
    return out


# ======================================================================
# 2.4 precise-limit
# ======================================================================

def precise_limit():
    S = 'precise-limit'
    rng = seeded(S)
    out = []
    epss = [sp.Rational(1, 10), sp.Rational(1, 100), sp.Rational(1, 2), sp.Rational(1, 4), sp.Rational(1, 5), sp.Rational(3, 10), sp.Rational(1, 1000), sp.Rational(1, 20)]

    # linear: largest delta for given epsilon
    for _ in range(15):
        m = nz(rng, -6, 6); b = rng.randint(-5, 5); a = rng.randint(-3, 3); eps = pick(rng, epss)
        f = m * x + b; Lv = f.subs(x, a)
        delta = eps / abs(m)
        out.append(numeric_problem(S, f"Let $f(x) = {L(f)}$, so that $\\displaystyle\\lim_{{x \\to {a}}} f(x) = {Lv}$. Given $\\varepsilon = {N(eps)}$, find the largest $\\delta > 0$ such that $|f(x) - {Lv}| < \\varepsilon$ whenever $0 < |x - ({a})| < \\delta$.", delta, difficulty=1 if abs(m) in (1, 2, 5, 10) else 2,
            hints=[f"Simplify $|f(x) - {Lv}|$; it should become a constant times $|x - ({a})|$.", f"You need $|{m}| \\cdot |x - ({a})| < {N(eps)}$; solve for $|x - ({a})|$."],
            solution=[f"$|f(x) - {Lv}| = |{L(f)} - ({Lv})| = |{L(sp.expand(f - Lv))}| = {abs(m)}\\,|x - ({a})|$.", f"This is less than ${N(eps)}$ exactly when $|x - ({a})| < {N(eps)}/{abs(m)} = {N(delta)}$, so $\\delta = {N(delta)}$."],
            verify={'kind': 'numeric', 'value': f'({eps})/Abs({m})'}))

    # linear: given delta find the epsilon it guarantees
    for _ in range(8):
        m = nz(rng, -5, 5); b = rng.randint(-5, 5); a = rng.randint(-3, 3); d = pick(rng, epss)
        f = m * x + b; Lv = f.subs(x, a)
        eps = abs(m) * d
        out.append(numeric_problem(S, f"Let $f(x) = {L(f)}$. If $0 < |x - ({a})| < {N(d)}$, what is the smallest $\\varepsilon$ for which you can guarantee $|f(x) - {Lv}| < \\varepsilon$?", eps, difficulty=2,
            hints=[f"Express $|f(x) - {Lv}|$ in terms of $|x - ({a})|$.", "Multiply the bound on $|x - a|$ by the slope's absolute value."],
            solution=[f"$|f(x) - {Lv}| = {abs(m)}|x - ({a})| < {abs(m)} \\cdot {N(d)}$.", f"So $\\varepsilon = {N(eps)}$ works, and no smaller value does."],
            verify={'kind': 'numeric', 'value': f'Abs({m})*({d})'}))

    # quadratic near a > 0: largest delta
    for _ in range(7):
        a = rng.randint(1, 4); eps = pick(rng, [sp.Rational(1, 2), sp.Rational(1, 4), sp.Rational(1, 10), 1, sp.Rational(1, 5)])
        f = x**2; Lv = a * a
        d1 = sp.sqrt(Lv + eps) - a; d2 = a - sp.sqrt(Lv - eps)
        delta = sp.Min(d1, d2)
        out.append(numeric_problem(S, f"For $f(x) = x^2$ and $\\displaystyle\\lim_{{x \\to {a}}} x^2 = {Lv}$, find the largest $\\delta$ such that $|x^2 - {Lv}| < {N(eps)}$ whenever $0 < |x - {a}| < \\delta$. Give three decimal places.", round(float(delta), 3), difficulty=3, tolerance=0.0015,
            hints=[f"$|x^2 - {Lv}| < {N(eps)}$ means ${N(Lv - eps)} < x^2 < {N(Lv + eps)}$; take square roots (for $x > 0$).", f"Measure how far each endpoint $\\sqrt{{{N(Lv-eps)}}}$ and $\\sqrt{{{N(Lv+eps)}}}$ is from ${a}$ and take the smaller distance."],
            solution=[f"The condition holds for $\\sqrt{{{N(Lv-eps)}}} < x < \\sqrt{{{N(Lv+eps)}}}$, i.e. ${float(sp.sqrt(Lv-eps)):.4f} < x < {float(sp.sqrt(Lv+eps)):.4f}$.", f"Distances from ${a}$: ${float(d2):.4f}$ (left) and ${float(d1):.4f}$ (right). The largest $\\delta$ is the smaller one, $\\delta \\approx {float(delta):.3f}$."],
            verify={'kind': 'numeric', 'value': f'Min(sqrt({Lv}+{eps}) - {a}, {a} - sqrt({Lv}-{eps}))'}))

    # infinite limit: delta for M
    for _ in range(7):
        M = rng.choice([100, 400, 1000, 10000, 25]); a = rng.randint(-2, 3); k = rng.choice([1, 2, 4])
        f = k / (x - a)**2
        delta = sp.sqrt(sp.Rational(k, M))
        out.append(numeric_problem(S, f"Let $f(x) = {L(f)}$. Find the largest $\\delta > 0$ such that $f(x) > {M}$ whenever $0 < |x - ({a})| < \\delta$.", delta, difficulty=2,
            hints=[f"Solve the inequality $\\dfrac{{{k}}}{{(x - ({a}))^2}} > {M}$ for $|x - ({a})|$.", "Flip both sides (all quantities are positive) and take a square root."],
            solution=[f"$\\dfrac{{{k}}}{{(x-({a}))^2}} > {M} \\iff (x - ({a}))^2 < \\dfrac{{{k}}}{{{M}}} \\iff |x - ({a})| < \\sqrt{{{N(sp.Rational(k, M))}}}$.", f"So $\\delta = {N(delta)}$."],
            verify={'kind': 'numeric', 'value': f'sqrt({k}/{M})'}))

    # limit at infinity: find N for epsilon
    for _ in range(5):
        eps = pick(rng, [sp.Rational(1, 10), sp.Rational(1, 100), sp.Rational(1, 1000), sp.Rational(1, 50)]); k = rng.choice([1, 2, 3, 5]); p_ = rng.choice([1, 2])
        f = k / x**p_
        Nv = (k / eps)**sp.Rational(1, p_)
        out.append(numeric_problem(S, f"Find the smallest $N$ such that $\\left|{L(f)} - 0\\right| < {N(eps)}$ for all $x > N$.", Nv, difficulty=2,
            hints=[f"For $x > 0$ the inequality is $\\dfrac{{{k}}}{{x^{p_}}} < {N(eps)}$.", f"Solve it: $x^{p_} > {k}/{N(eps)}$."],
            solution=[f"$\\dfrac{{{k}}}{{x^{p_}}} < {N(eps)} \\iff x^{p_} > {N(k/eps)}$.", f"So $x > {N(Nv)}$; the smallest such $N$ is ${N(Nv)}$."],
            verify={'kind': 'numeric', 'value': f'({k}/({eps}))**(1/{p_})'}))

    # sqrt(x) near a: largest delta
    for _ in range(4):
        a = rng.choice([1, 4, 9]); eps = pick(rng, [sp.Rational(1, 2), sp.Rational(1, 4), sp.Rational(1, 10)])
        r = sp.sqrt(a)
        d1 = (r + eps)**2 - a; d2 = a - (r - eps)**2
        delta = sp.Min(d1, d2)
        out.append(numeric_problem(S, f"For $\\displaystyle\\lim_{{x \\to {a}}} \\sqrt{{x}} = {r}$ and $\\varepsilon = {N(eps)}$, find the largest $\\delta$ such that $|\\sqrt{{x}} - {r}| < \\varepsilon$ whenever $0 < |x - {a}| < \\delta$.", delta, difficulty=3,
            hints=[f"$|\\sqrt{{x}} - {r}| < {N(eps)}$ means ${N(r-eps)} < \\sqrt{{x}} < {N(r+eps)}$; square each part.", f"Compare the distances from ${a}$ to the two endpoints and take the smaller."],
            solution=[f"Squaring: ${N((r-eps)**2)} < x < {N((r+eps)**2)}$.", f"Distances to ${a}$: ${N(d2)}$ on the left and ${N(d1)}$ on the right; $\\delta = {N(delta)}$."],
            verify={'kind': 'numeric', 'value': f'Min(({r}+{eps})**2 - {a}, {a} - ({r}-{eps})**2)'}))

    # conceptual definitions
    concept = [
        ("Which statement is the precise definition of $\\displaystyle\\lim_{x \\to a} f(x) = L$?",
         [("for every $\\varepsilon > 0$ there is $\\delta > 0$ such that $0 < |x - a| < \\delta$ implies $|f(x) - L| < \\varepsilon$", 'def'),
          ("for every $\\delta > 0$ there is $\\varepsilon > 0$ such that $|x - a| < \\delta$ implies $|f(x) - L| < \\varepsilon$", 'swap'),
          ("there is $\\varepsilon > 0$ such that for every $\\delta > 0$, $|x - a| < \\delta$ implies $|f(x) - L| < \\varepsilon$", 'order'),
          ("$f(a) = L$ and $f$ is defined near $a$", 'value')], 'def',
         ["The challenge ($\\varepsilon$, how close the outputs must be) comes first; the response ($\\delta$) is chosen afterwards.", "The condition $0 < |x - a|$ excludes $x = a$ itself."],
         ["The definition: for every $\\varepsilon > 0$ we must be able to find a $\\delta > 0$ so that all $x$ within $\\delta$ of $a$ (except $a$) have $f(x)$ within $\\varepsilon$ of $L$.", "Swapping the order of the quantifiers changes the meaning entirely."]),
        ("In the $\\varepsilon$-$\\delta$ definition of a limit, the number $\\delta$ controls",
         [("how close $x$ must be to $a$", 'x'), ("how close $f(x)$ must be to $L$", 'fx'), ("the value of $f(a)$", 'fa'), ("the slope of $f$ near $a$", 'slope')], 'x',
         ["$\\varepsilon$ measures output closeness; the other letter measures input closeness.", "$0 < |x - a| < \\delta$ is a condition on the inputs."],
         ["$\\delta$ bounds the distance $|x - a|$ between the input and $a$.", "$\\varepsilon$ bounds the distance $|f(x) - L|$ between the output and the limit."]),
        ("Which is the precise meaning of $\\displaystyle\\lim_{x \\to a} f(x) = \\infty$?",
         [("for every $M > 0$ there is $\\delta > 0$ such that $0 < |x - a| < \\delta$ implies $f(x) > M$", 'def'),
          ("for every $\\varepsilon > 0$ there is $\\delta > 0$ such that $0 < |x - a| < \\delta$ implies $|f(x) - \\infty| < \\varepsilon$", 'bad'),
          ("$f(a) = \\infty$", 'val'), ("$f(x)$ is increasing near $a$", 'inc')], 'def',
         ["Infinity is not a number, so 'within $\\varepsilon$ of $\\infty$' makes no sense.", "Replace 'close to $L$' with 'larger than any prescribed $M$'."],
         ["An infinite limit means the outputs eventually exceed any bound $M$ when $x$ is close enough to $a$.", "So the definition quantifies over all $M > 0$ with a matching $\\delta$."]),
        ("If a valid $\\delta$ has been found for a given $\\varepsilon$ in a limit proof, which other values of $\\delta$ also work?",
         [("any smaller positive $\\delta$", 'smaller'), ("any larger $\\delta$", 'larger'), ("only that exact $\\delta$", 'exact'), ("any $\\delta$ at all", 'any')], 'smaller',
         ["Shrinking the allowed $x$-window only removes points, never adds any.", "The remaining points still satisfy the output condition."],
         ["If $0 < |x - a| < \\delta'$ with $\\delta' < \\delta$ then also $0 < |x - a| < \\delta$, so $|f(x) - L| < \\varepsilon$ still holds.", "A larger window might include points where the output condition fails."]),
    ]
    for stmt, opts, lab, hints, sol in concept:
        out.append(label_mc(S, stmt, opts, lab, rng, difficulty=2, hints=hints, solution=sol))
    for i in range(2):
        a = rng.randint(1, 5); Lv = rng.randint(1, 9); m = rng.randint(2, 6)
        out.append(label_mc(S, f"To prove $\\displaystyle\\lim_{{x \\to {a}}} ({m}x {signed(Lv - m*a)}) = {Lv}$ using the definition, which choice of $\\delta$ (in terms of $\\varepsilon$) works?",
            [(f"$\\delta = \\varepsilon/{m}$", 'good'), (f"$\\delta = {m}\\varepsilon$", 'times'), ("$\\delta = \\varepsilon$", 'same'), (f"$\\delta = \\varepsilon/{m*m}$ only", 'sq')], 'good', rng, difficulty=2,
            hints=[f"Compute $|f(x) - {Lv}|$ and factor out $|x - {a}|$.", "Choose $\\delta$ so that the resulting bound is exactly $\\varepsilon$."],
            solution=[f"$|{m}x {signed(Lv - m*a)} - {Lv}| = {m}|x - {a}|$.", f"If $|x - {a}| < \\delta = \\varepsilon/{m}$ then $|f(x) - {Lv}| < \\varepsilon$, as required."]))
    return out


# ======================================================================
# 2.5 continuity
# ======================================================================

def continuity():
    S = 'continuity'
    rng = seeded(S)
    out = []

    # find c making a piecewise function continuous
    for _ in range(15):
        a = rng.randint(-2, 3)
        form = rng.choice(['cx', 'plus_c', 'cx2', 'c_times'])
        g = rng.choice([x**2 + rng.randint(-3, 3), nz(rng, -3, 3) * x + rng.randint(-4, 4), x**3 - rng.randint(1, 3), sp.sqrt(x + rng.randint(3, 6))])
        gv = g.subs(x, a)
        if not gv.is_rational:
            g = x**2 + 1; gv = g.subs(x, a)
        if form == 'cx':
            left_c = 'cx' + (signed(bb := rng.randint(-4, 4)) if True else ''); left_num = lambda c: c * a + bb
            left_l = f"cx {signed(bb)}"; lhs = f'x*({a}) + ({bb})'
        elif form == 'plus_c':
            q = rng.randint(1, 3) * x**2; left_l = f"{L(q)} + c"; lhs = f'{q.subs(x, a)} + x'
        elif form == 'cx2':
            bb = rng.randint(-3, 3); left_l = f"cx^2 {signed(bb)}"; lhs = f'x*({a*a}) + ({bb})'
        else:
            left_l = f"c({L(x + rng.randint(1, 4))})" if False else None
            kk = rng.randint(1, 4); left_l = f"c(x + {kk})"; lhs = f'x*({a + kk})'
        c_val = sp.solve(sp.Eq(sp.sympify(lhs), gv), x)
        if len(c_val) != 1:
            continue
        c_val = c_val[0]
        swap = rng.random() < 0.5
        br1 = f"{left_l} & \\text{{if }} x < {a}"; br2 = f"{L(g)} & \\text{{if }} x \\ge {a}"
        if swap:
            br1 = f"{L(g)} & \\text{{if }} x < {a}"; br2 = f"{left_l} & \\text{{if }} x \\ge {a}"
        lt = "\\begin{cases} " + br1 + " \\\\ " + br2 + " \\end{cases}"
        out.append(numeric_problem(S, f"Find the value of the constant $c$ that makes $f(x) = {lt}$ continuous on $(-\\infty, \\infty)$.", c_val, difficulty=3 if form in ('cx2', 'c_times') else 2,
            hints=[f"Both pieces are continuous on their own, so only $x = {a}$ needs checking.", f"Set the two one-sided limits at $x = {a}$ equal to each other and solve for $c$."],
            solution=[f"At $x = {a}$ the piece ${L(g)}$ gives ${N(gv)}$, and the piece with $c$ gives ${lhs.replace('x', 'c').replace('*', '')}$.", f"Setting them equal: $c = {N(c_val)}$."],
            verify={'kind': 'solve', 'lhs': lhs, 'rhs': str(gv)}))

    # classify discontinuity
    for _ in range(12):
        a = rng.randint(-2, 3)
        kind = rng.choice(['removable', 'jump', 'infinite', 'continuous'])
        if kind == 'removable':
            b = nz(rng, -4, 4, exclude=(0, a))
            if rng.random() < 0.5:
                f = sp.expand((x - a) * (x - b)) / (x - a); lt = L(f)
            else:
                g = rng.choice([x**2, 2 * x + 1, x**2 - 1]); f = sp.Piecewise((g, sp.Ne(x, a)), (g.subs(x, a) + rng.choice([1, -1, 2]), True))
                lt = cases([(g, f"x \\ne {a}")]).replace(" \\end{cases}", f" \\\\ {N(g.subs(x, a) + (f.args[1][0] - g.subs(x, a)))} & \\text{{if }} x = {a} \\end{{cases}}")
        elif kind == 'jump':
            left = x + rng.randint(-2, 2); right = x**2 + rng.randint(-3, 3)
            while sp.simplify(left.subs(x, a) - right.subs(x, a)) == 0:
                right = right + 1
            f, lt = pw2(left, right, a)
        elif kind == 'infinite':
            f = (x + rng.randint(1, 5)) / (x - a) if rng.random() < 0.5 else 1 / (x - a)**2 + rng.randint(0, 3); lt = L(f)
        else:
            left = x**2 + rng.randint(-2, 2); right = sp.expand(left.subs(x, a) + rng.randint(1, 3) * (x - a))
            f, lt = pw2(left, right, a)
        opts = [("continuous at that point", 'continuous'), ("removable discontinuity", 'removable'), ("jump discontinuity", 'jump'), ("infinite discontinuity", 'infinite')]
        out.append(label_mc(S, f"Let $f(x) = {lt}$. At $x = {a}$, is $f$ continuous, or what type of discontinuity does it have?", opts, kind, rng, difficulty=2,
            verify={'kind': 'discontinuity', 'expr': str(f), 'at': a},
            hints=["Compute the left and right limits at the point and compare them with the function value there (if defined).", "Equal finite one-sided limits that disagree with the value (or no value) mean removable; different finite one-sided limits mean jump; an unbounded limit means infinite."],
            solution=[(lambda: f"The limit as $x \\to {a}$ exists (the troublesome factor cancels or the formula nearby is continuous), but $f({a})$ is undefined or has a different value." if kind == 'removable'
                       else f"The left limit is ${N(f.args[0][0].subs(x, a))}$ while the right limit is ${N(f.args[1][0].subs(x, a))}$; they differ." if kind == 'jump'
                       else f"As $x \\to {a}$ the denominator approaches $0$ while the numerator does not, so $|f(x)| \\to \\infty$." if kind == 'infinite'
                       else f"Both pieces give ${N(f.args[0][0].subs(x, a))}$ at $x = {a}$ and the value $f({a})$ matches.")(),
                      {'removable': "So the discontinuity is removable: redefining the single value would make $f$ continuous.", 'jump': "So $f$ has a jump discontinuity.", 'infinite': "So $f$ has an infinite discontinuity (a vertical asymptote).", 'continuous': "So $f$ is continuous there."}[kind]]))

    # interval of continuity
    for _ in range(6):
        a = rng.randint(-4, 4); form = rng.choice(['ln', 'sqrt', 'sqrt_den', 'sqrt_down'])
        if form == 'ln':
            f = sp.log(x - a); ans = interval_str(a, sp.oo, True, True); exp_ = f'Interval.open({a}, oo)'; why = f"$\\ln u$ needs $u > 0$, so $x > {a}$"
        elif form == 'sqrt':
            f = sp.sqrt(x - a) + rng.randint(1, 3) * x; ans = interval_str(a, sp.oo, False, True); exp_ = f'Interval({a}, oo)'; why = f"the square root needs $x - ({a}) \\ge 0$"
        elif form == 'sqrt_den':
            f = rng.randint(1, 5) / sp.sqrt(x - a); ans = interval_str(a, sp.oo, True, True); exp_ = f'Interval.open({a}, oo)'; why = f"the root needs $x - ({a}) \\ge 0$ and the denominator must not vanish, so $x > {a}$"
        else:
            f = sp.sqrt(a - x); ans = interval_str(-sp.oo, a, True, False); exp_ = f'Interval(-oo, {a})'; why = f"the square root needs ${a} - x \\ge 0$"
        out.append(interval_problem(S, f"On what interval is $f(x) = {L(f)}$ continuous? Answer in interval notation.", ans, exp_, difficulty=1,
            hints=["Roots, logs and rational functions are continuous at every point of their domains.", "So find the domain and report it as an interval."],
            solution=[f"The domain: {why}.", f"The function is continuous on its whole domain, ${interval_ltx(*[(a if form != 'sqrt_down' else -sp.oo), (sp.oo if form != 'sqrt_down' else a), (form != 'sqrt'), (form != 'sqrt_down')])}$."]))

    # evaluate a limit by continuity of a composite
    for _ in range(7):
        a = rng.randint(-2, 3)
        f = rng.choice([sp.sqrt(x**2 + rng.choice([1, 4, 9, 16]) - a * a + a * a) if False else sp.sqrt(x**2 + rng.choice([v for v in [1, 3, 5, 7, 9, 12, 16, 20, 21, 24] if sp.sqrt(a*a + v).is_rational] or [16 - a*a if 16 - a*a > 0 else 25 - a*a])),
                        sp.exp(x - a) * (x + rng.randint(1, 3)), sp.cos(sp.pi * x) + rng.randint(1, 4) * x, sp.log(x**2 - a * a + 1) + x])
        val = sp.limit(f, x, a)
        if val.has(sp.E) or not val.is_finite:
            val = f.subs(x, a)
        out.append(numeric_problem(S, f"Use continuity to evaluate $\\displaystyle\\lim_{{x \\to {a}}} \\left({L(f)}\\right)$.", val, difficulty=1,
            hints=["Compositions, sums and products of continuous functions are continuous, so the limit is just the function value.", f"Substitute $x = {a}$ and simplify."],
            solution=[f"The function is continuous at $x = {a}$ (it is built from continuous functions and is defined there).", f"So the limit equals $f({a}) = {N(val)}$."],
            verify={'kind': 'limit', 'expr': str(f), 'to': a}))

    # define f(a) to remove a discontinuity
    for _ in range(8):
        a = nz(rng, -4, 4); b = nz(rng, -4, 4, exclude=(0, a))
        f = sp.expand((x - a) * (x - b)) / (x - a) if rng.random() < 0.6 else (x**2 - a * a) / (x - a)
        val = sp.limit(f, x, a)
        out.append(numeric_problem(S, f"The function $f(x) = {L(f)}$ is undefined at $x = {a}$. What value should be assigned to $f({a})$ so that the extended function is continuous there?", val, difficulty=2,
            hints=[f"For continuity at ${a}$ you need $f({a}) = \\lim_{{x \\to {a}}} f(x)$.", "Factor the numerator and cancel the common factor to find that limit."],
            solution=[f"For $x \\ne {a}$, $f(x) = {L(sp.cancel(f))}$.", f"The limit at ${a}$ is ${N(val)}$, so define $f({a}) = {N(val)}$."],
            verify={'kind': 'limit', 'expr': str(f), 'to': a}))

    # IVT: locate a root interval
    for _ in range(6):
        f = rng.choice([x**3 - rng.randint(2, 6) * x + 1, x**3 + x - rng.randint(1, 20), sp.cos(x) - x, x**4 - rng.randint(2, 9) * x - 1, sp.exp(x) - rng.randint(2, 5) * x - 1])
        ivals = [(0, 1), (1, 2), (2, 3), (-1, 0), (-2, -1), (3, 4)]
        good = [iv for iv in ivals if float(f.subs(x, iv[0])) * float(f.subs(x, iv[1])) < 0]
        bad = [iv for iv in ivals if float(f.subs(x, iv[0])) * float(f.subs(x, iv[1])) > 0]
        if not good or len(bad) < 3:
            continue
        g_ = good[0]; bs = rng.sample(bad, 3)
        opts = [(f"$[{g_[0]}, {g_[1]}]$", f"{g_[0]}_{g_[1]}")] + [(f"$[{b_[0]}, {b_[1]}]$", f"{b_[0]}_{b_[1]}") for b_ in bs]
        out.append(label_mc(S, f"Let $f(x) = {L(f)}$. On which of these intervals does the Intermediate Value Theorem guarantee a solution of $f(x) = 0$?", opts, f"{g_[0]}_{g_[1]}", rng, difficulty=3,
            hints=["The IVT applies when $f$ is continuous and takes values of opposite sign at the two endpoints.", "Evaluate $f$ at each endpoint (a decimal approximation is enough) and look for a sign change."],
            solution=[f"$f({g_[0]}) \\approx {float(f.subs(x, g_[0])):.3f}$ and $f({g_[1]}) \\approx {float(f.subs(x, g_[1])):.3f}$ have opposite signs, and $f$ is continuous.", f"By the IVT there is a number $c$ in $({g_[0]}, {g_[1]})$ with $f(c) = 0$. On the other listed intervals the endpoint values have the same sign, so the theorem gives no guarantee."]))

    # points of discontinuity of a rational function (two values)
    for _ in range(4):
        r1, r2 = sorted(rng.sample(range(-4, 5), 2))
        f = (x + rng.randint(1, 3)) / sp.expand((x - r1) * (x - r2))
        wrong = [f"$x = {-r1}, {-r2}$" if (-r1, -r2) != (r1, r2) else f"$x = {r1+1}, {r2+1}$", f"$x = {r1}$ only", f"$x = {r2}$ only"]
        opts = [(f"$x = {r1}, {r2}$", 'both'), (wrong[0], 'neg'), (wrong[1], 'r1'), (wrong[2], 'r2')]
        out.append(label_mc(S, f"At which values of $x$ is $f(x) = {L(f)}$ discontinuous?", opts, 'both', rng, difficulty=1,
            hints=["A rational function is continuous everywhere except where its denominator is zero.", "Factor the denominator."],
            solution=[f"${L(sp.denom(f))} = (x - ({r1}))(x - ({r2}))$ is zero at $x = {r1}$ and $x = {r2}$.", "The numerator is nonzero at both, so $f$ has infinite discontinuities at exactly those two points."]))

    # conceptual
    concept = [
        ("Which three conditions must all hold for $f$ to be continuous at $x = a$?",
         [("$f(a)$ is defined, $\\lim_{x \\to a} f(x)$ exists, and $\\lim_{x \\to a} f(x) = f(a)$", 'three'), ("$f(a)$ is defined and $f$ is increasing near $a$", 'inc'), ("$\\lim_{x \\to a} f(x)$ exists and $f(a) > 0$", 'pos'), ("$f$ is differentiable at $a$", 'diff')], 'three',
         ["Continuity means the limit and the function value agree.", "That requires both of them to exist in the first place."],
         ["Continuity at $a$: $\\lim_{x \\to a} f(x) = f(a)$, which needs both sides to exist.", "Differentiability implies continuity but is not required for it."]),
        ("A function is continuous from the right at $x = a$ when",
         [("$\\lim_{x \\to a^+} f(x) = f(a)$", 'right'), ("$\\lim_{x \\to a^-} f(x) = f(a)$", 'left'), ("$\\lim_{x \\to a^+} f(x)$ exists", 'exists'), ("$f(a) > 0$", 'pos')], 'right',
         ["'From the right' refers to the one-sided limit with $x > a$.", "The limit must equal the function value."],
         ["Right-continuity compares the right-hand limit with $f(a)$.", "For example $\\sqrt{x}$ is continuous from the right at $0$."]),
        ("If $f$ is continuous on $[1, 3]$ with $f(1) = -2$ and $f(3) = 5$, what does the Intermediate Value Theorem guarantee?",
         [("there is some $c$ in $(1, 3)$ with $f(c) = 0$", 'root'), ("$f(2) = 0$", 'mid'), ("$f$ has exactly one zero in $(1, 3)$", 'one'), ("$f$ is increasing on $[1, 3]$", 'inc')], 'root',
         ["The IVT says every value between $f(1)$ and $f(3)$ is attained somewhere in between.", "It guarantees existence, not uniqueness or location."],
         ["$0$ lies between $-2$ and $5$, so some $c \\in (1,3)$ has $f(c) = 0$.", "The theorem does not say where, nor that there is only one."]),
    ]
    for stmt, opts, lab, hints, sol in concept:
        out.append(label_mc(S, stmt, opts, lab, rng, difficulty=1, hints=hints, solution=sol))
    return out


# ======================================================================
# 2.6 limits-at-infinity
# ======================================================================

def limits_at_infinity():
    S = 'limits-at-infinity'
    rng = seeded(S)
    out = []

    # rational functions: equal degree (numeric), lower degree (0), higher degree (infinite)
    for _ in range(14):
        kind = rng.choice(['eq', 'eq', 'low', 'high'])
        to = rng.choice([sp.oo, sp.oo, -sp.oo])
        a1, a0 = nz(rng, -5, 5), rng.randint(-5, 5); b1, b0 = nz(rng, -4, 4), rng.randint(-5, 5)
        if kind == 'eq':
            dg = rng.choice([1, 2, 3]); f = (a1 * x**dg + a0 * x**(dg - 1) + rng.randint(-3, 3)) / (b1 * x**dg + b0)
            val = sp.Rational(a1, b1)
            out.append(numeric_problem(S, f"Evaluate $\\displaystyle\\lim_{{x \\to {L(to)}}} {L(f)}$.", val, difficulty=1,
                hints=[f"Divide numerator and denominator by the highest power of $x$ in the denominator, $x^{dg}$.", "Every term of the form $c/x^k$ then approaches $0$."],
                solution=[f"Dividing top and bottom by $x^{dg}$ leaves ${a1}$ plus terms that vanish, over ${b1}$ plus terms that vanish.", f"So the limit is $\\dfrac{{{a1}}}{{{b1}}} = {N(val)}$ (the ratio of leading coefficients)."],
                verify={'kind': 'limit', 'expr': str(f), 'to': str(to)}))
        elif kind == 'low':
            f = (a1 * x + a0) / (b1 * x**2 + b0 * x + rng.randint(1, 4))
            out.append(numeric_problem(S, f"Evaluate $\\displaystyle\\lim_{{x \\to {L(to)}}} {L(f)}$.", 0, difficulty=1,
                hints=["Compare the degrees of numerator and denominator.", "Divide through by $x^2$ and watch each term."],
                solution=[f"After dividing numerator and denominator by $x^2$, the numerator becomes $\\dfrac{{{a1}}}{{x}} + \\dfrac{{{a0}}}{{x^2}} \\to 0$ while the denominator approaches ${b1}$.", "So the limit is $0$: the denominator grows faster."],
                verify={'kind': 'limit', 'expr': str(f), 'to': str(to)}))
        else:
            f = (a1 * x**3 + a0 * x) / (b1 * x**2 + b0)
            out.append(limit_class_mc(S, f"Evaluate $\\displaystyle\\lim_{{x \\to {L(to)}}} {L(f)}$.", f, to, rng, difficulty=2,
                hints=["The numerator has higher degree, so the quotient grows without bound; decide the sign.", f"Divide by $x^2$: the numerator behaves like ${a1}x$ and the denominator approaches ${b1}$."],
                solution=[f"Dividing by $x^2$: $\\dfrac{{{a1}x + {a0}/x}}{{{b1} + {b0}/x^2}}$, which behaves like $\\dfrac{{{a1}}}{{{b1}}}x$ for large $|x|$.", f"As $x \\to {L(to)}$ this tends to ${'\\infty' if (sp.Rational(a1, b1) > 0) == (to == sp.oo) else '-\\infty'}$."]))

    # horizontal asymptote of a rational function
    for _ in range(5):
        a1, b1 = nz(rng, -6, 6), nz(rng, -4, 4); a0, b0 = rng.randint(-5, 5), nz(rng, -5, 5)
        f = (a1 * x + a0) / (b1 * x + b0)
        if rng.random() < 0.5:
            out.append(numeric_problem(S, f"Find the horizontal asymptote $y = c$ of the curve $y = {L(f)}$.", sp.Rational(a1, b1), difficulty=1,
                hints=["Horizontal asymptotes come from limits as $x \\to \\pm\\infty$.", "For equal degrees, that limit is the ratio of leading coefficients."],
                solution=[f"$\\lim_{{x \\to \\pm\\infty}} {L(f)} = \\dfrac{{{a1}}}{{{b1}}}$.", f"Horizontal asymptote: $y = {N(sp.Rational(a1, b1))}$."],
                verify={'kind': 'limit', 'expr': str(f), 'to': 'oo'}))
        else:
            va = sp.Rational(-b0, b1)
            out.append(numeric_problem(S, f"Find the vertical asymptote $x = c$ of the curve $y = {L(f)}$.", va, difficulty=1,
                hints=["A vertical asymptote of a rational function occurs where the denominator is zero (and the numerator is not).", "Solve the denominator equal to zero."],
                solution=[f"${L(b1*x+b0)} = 0$ gives $x = {N(va)}$.", f"The numerator is nonzero there, so $x = {N(va)}$ is a vertical asymptote."],
                verify={'kind': 'solve', 'lhs': str(b1 * x + b0), 'rhs': 0}))

    # square roots: sqrt(ax^2 + b)/(cx + d) at +/- infinity
    for _ in range(8):
        a = rng.choice([1, 4, 9, 16]); b = rng.randint(1, 9); c = nz(rng, -3, 3); d = rng.randint(-4, 4)
        to = rng.choice([sp.oo, -sp.oo])
        f = sp.sqrt(a * x**2 + b) / (c * x + d)
        val = sp.limit(f, x, to)
        out.append(numeric_problem(S, f"Evaluate $\\displaystyle\\lim_{{x \\to {L(to)}}} {L(f)}$.", val, difficulty=3 if to == -sp.oo else 2,
            hints=["Divide numerator and denominator by $x$; inside the root that means dividing by $x^2$.", f"Careful: for $x {'<' if to == -sp.oo else '>'} 0$, $\\sqrt{{x^2}} = |x| = {'-x' if to == -sp.oo else 'x'}$."],
            solution=[f"$\\sqrt{{{L(a*x**2 + b)}}} = |x|\\sqrt{{{a} + {b}/x^2}}$, and $|x| = {'-x' if to == -sp.oo else 'x'}$ for $x \\to {L(to)}$.", f"So the quotient tends to $\\dfrac{{{'-' if to == -sp.oo else ''}\\sqrt{{{a}}}}}{{{c}}} = {N(val)}$."],
            verify={'kind': 'limit', 'expr': str(f), 'to': str(to)}))

    # sqrt(x^2 + bx) - x
    for _ in range(5):
        b = nz(rng, -8, 8); c = rng.choice([0, 0, 1, 4])
        f = sp.sqrt(x**2 + b * x + c) - x
        val = sp.limit(f, x, sp.oo)
        out.append(numeric_problem(S, f"Evaluate $\\displaystyle\\lim_{{x \\to \\infty}} \\left({L(f)}\\right)$.", val, difficulty=3,
            hints=["This is $\\infty - \\infty$; multiply and divide by the conjugate $\\sqrt{x^2 + bx + c} + x$.", "After simplifying the numerator, divide top and bottom by $x$."],
            solution=[f"Multiplying by the conjugate gives $\\dfrac{{{L(sp.expand(x**2 + b*x + c - x**2))}}}{{\\sqrt{{x^2 {signed(b)}x {signed(c) if c else ''}}} + x}}$.", f"Dividing by $x$: $\\dfrac{{{b} {('+ ' + str(c) + '/x') if c else ''}}}{{\\sqrt{{1 {signed(b)}/x {('+ ' + str(c) + '/x^2') if c else ''}}} + 1}} \\to \\dfrac{{{b}}}{{2}} = {N(val)}$."],
            verify={'kind': 'limit', 'expr': str(f), 'to': 'oo'}))

    # exponentials and arctan and 1/x^k
    for _ in range(10):
        form = rng.choice(['exp_neg', 'exp_frac', 'atan', 'recip', 'sin_over_x'])
        if form == 'exp_neg':
            k = rng.randint(1, 4); c = rng.randint(-3, 3); f = c + rng.randint(1, 5) * sp.exp(-k * x); to = sp.oo
            hints = [f"$e^{{-{k}x}} = 1/e^{{{k}x}}$ and $e^{{{k}x}} \\to \\infty$.", "A constant divided by something huge approaches $0$."]
            sol = [f"$e^{{-{k}x}} \\to 0$ as $x \\to \\infty$.", f"So the limit is ${c} + 0 = {c}$."]
        elif form == 'exp_frac':
            a, b = rng.randint(1, 4), rng.randint(1, 4); cc = rng.randint(1, 3); f = (a * sp.exp(x) + b) / (sp.exp(x) + cc); to = sp.oo
            hints = ["Divide numerator and denominator by $e^x$.", "Terms like $b/e^x$ approach $0$."]
            sol = [f"Dividing by $e^x$: $\\dfrac{{{a} + {b}e^{{-x}}}}{{1 + {cc}e^{{-x}}}}$.", f"As $x \\to \\infty$, $e^{{-x}} \\to 0$, so the limit is ${a}$."]
        elif form == 'atan':
            k = rng.randint(1, 3); f = rng.randint(1, 3) * sp.atan(k * x); to = rng.choice([sp.oo, -sp.oo])
            hints = ["Recall the horizontal asymptotes of $\\arctan$: $\\pm\\pi/2$.", f"As $x \\to {L(to)}$, ${k}x \\to {L(to)}$ too."]
            sol = [f"$\\arctan u \\to {'\\pi/2' if to == sp.oo else '-\\pi/2'}$ as $u \\to {L(to)}$.", f"So the limit is ${L(sp.limit(f, x, to))}$."]
        elif form == 'recip':
            k = rng.randint(1, 3); c = rng.randint(-4, 4); f = c + rng.randint(1, 9) / x**k; to = rng.choice([sp.oo, -sp.oo])
            hints = [f"$1/x^{k} \\to 0$ as $|x| \\to \\infty$.", "Only the constant survives."]
            sol = [f"$\\dfrac{{1}}{{x^{k}}} \\to 0$.", f"Limit $= {c}$."]
        else:
            k = rng.randint(1, 4); f = sp.sin(k * x) / x; to = sp.oo
            hints = ["$\\sin$ is bounded between $-1$ and $1$.", "Squeeze: $-1/x \\le \\sin(kx)/x \\le 1/x$ for $x > 0$."]
            sol = [f"$-\\dfrac{{1}}{{x}} \\le \\dfrac{{\\sin {k}x}}{{x}} \\le \\dfrac{{1}}{{x}}$ for $x > 0$.", "Both bounds go to $0$, so the limit is $0$ by the Squeeze Theorem."]
        val = sp.limit(f, x, to)
        out.append(numeric_problem(S, f"Evaluate $\\displaystyle\\lim_{{x \\to {L(to)}}} \\left({L(f)}\\right)$.", val, difficulty=2, hints=hints, solution=sol,
            verify={'kind': 'limit', 'expr': str(f), 'to': str(to)}))

    # polynomial end behavior
    for _ in range(5):
        a = nz(rng, -3, 3); dg = rng.choice([2, 3, 4, 5]); f = a * x**dg + rng.randint(-5, 5) * x + rng.randint(-5, 5)
        to = rng.choice([sp.oo, -sp.oo])
        out.append(limit_class_mc(S, f"Evaluate $\\displaystyle\\lim_{{x \\to {L(to)}}} \\left({L(f)}\\right)$.", f, to, rng, difficulty=1,
            hints=["For large $|x|$ the leading term dominates a polynomial.", f"Consider the sign of ${a}x^{dg}$ when $x$ is a huge {'negative' if to == -sp.oo else 'positive'} number."],
            solution=[f"Factor: $x^{dg}\\left({a} + \\dots/x^{{{dg-1}}} + \\dots\\right)$, and the bracket approaches ${a}$.", f"$x^{dg} \\to {'\\infty' if (to == sp.oo or dg % 2 == 0) else '-\\infty'}$, so the limit is ${'\\infty' if ((to == sp.oo or dg % 2 == 0) == (a > 0)) else '-\\infty'}$."]))

    # conceptual
    concept = [
        ("How many horizontal asymptotes can the graph of a function have at most?", [("two", 'two'), ("one", 'one'), ("infinitely many", 'inf'), ("none; only vertical asymptotes exist", 'none')], 'two',
         ["There are two directions to go: $x \\to \\infty$ and $x \\to -\\infty$.", "Think of $\\arctan x$."],
         ["Each of the limits as $x \\to \\infty$ and as $x \\to -\\infty$ can give one horizontal asymptote.", "$\\arctan x$ has both $y = \\pi/2$ and $y = -\\pi/2$, so two is possible and is the maximum."]),
        ("For a rational function, when does $\\lim_{x \\to \\infty} f(x) = 0$?", [("when the degree of the numerator is less than the degree of the denominator", 'less'), ("when the degrees are equal", 'equal'), ("when the numerator's degree is larger", 'more'), ("never", 'never')], 'less',
         ["Divide by the highest power in the denominator and see what survives.", "A smaller numerator degree leaves only vanishing terms on top."],
         ["With a lower-degree numerator, dividing by the denominator's top power sends every numerator term to $0$.", "Equal degrees give the ratio of leading coefficients; a larger numerator degree gives an infinite limit."]),
        ("The statement $\\lim_{x \\to \\infty} f(x) = L$ means", [("$f(x)$ can be made as close to $L$ as we like by taking $x$ sufficiently large", 'def'), ("$f(L) = \\infty$", 'bad'), ("$f(x) = L$ for all large $x$", 'const'), ("$f$ is increasing for large $x$", 'inc')], 'def',
         ["It is the limit definition with 'close to $a$' replaced by 'large'.", "The function need not ever equal $L$."],
         ["Formally: for every $\\varepsilon > 0$ there is $N$ with $|f(x) - L| < \\varepsilon$ for all $x > N$.", "Graphically, $y = L$ is a horizontal asymptote."]),
    ]
    for stmt, opts, lab, hints, sol in concept:
        out.append(label_mc(S, stmt, opts, lab, rng, difficulty=1, hints=hints, solution=sol))
    return out


# ======================================================================
# 2.7 derivatives-rates
# ======================================================================

def derivatives_rates():
    S = 'derivatives-rates'
    rng = seeded(S)
    out = []
    fams = [lambda: x**2 + nz(rng, -4, 4) * x, lambda: rng.randint(2, 4) * x**2 - rng.randint(1, 5), lambda: x**3 - rng.randint(1, 4) * x, lambda: rng.randint(1, 4) / x, lambda: sp.sqrt(x + rng.randint(0, 5)), lambda: rng.randint(1, 3) * x**2 + rng.randint(1, 3) * x + 1]

    # f'(a) from the limit definition
    for _ in range(12):
        f = pick(rng, fams)(); a = rng.randint(1, 4)
        if f.has(sp.sqrt) and not f.subs(x, a).is_rational:
            f = x**2 + 2 * x
        d = sp.diff(f, x); val = d.subs(x, a)
        dq = sp.cancel((f.subs(x, a + h) - f.subs(x, a)) / h) if f.is_polynomial(x) else None
        out.append(numeric_problem(S, f"Use the definition $f'(a) = \\displaystyle\\lim_{{h \\to 0}} \\dfrac{{f(a+h) - f(a)}}{{h}}$ to find $f'({a})$ for $f(x) = {L(f)}$.", val, difficulty=2 if f.is_polynomial(x) else 3,
            hints=[f"Write out $f({a}+h) - f({a})$ and simplify until a factor of $h$ appears{' (rationalize if there is a square root; combine fractions if there is a reciprocal)' if not f.is_polynomial(x) else ''}.", "Cancel the $h$, then let $h \\to 0$."],
            solution=[f"$\\dfrac{{f({a}+h) - f({a})}}{{h}}$ simplifies (for $h \\ne 0$) to ${L(dq) if dq is not None else L(sp.simplify((f.subs(x, a+h) - f.subs(x, a))/h))}$.", f"Letting $h \\to 0$ gives $f'({a}) = {N(val)}$."],
            verify={'kind': 'evaluate', 'expr': str(d), 'at': a}))

    # tangent line at a point
    for _ in range(11):
        f = pick(rng, fams)(); a = rng.randint(1, 3)
        if f.has(sp.sqrt) and not f.subs(x, a).is_rational:
            f = x**3 - x
        d = sp.diff(f, x); m = d.subs(x, a); line = sp.expand(f.subs(x, a) + m * (x - a))
        out.append(equiv_problem(S, f"Find an equation of the tangent line to the curve $y = {L(f)}$ at the point where $x = {a}$. Give it in the form $y = mx + b$.", line, difficulty=2,
            hints=[f"The slope of the tangent is $f'({a})$, found from the limit of difference quotients.", f"Then use point-slope form through $({a}, f({a}))$."],
            solution=[f"$f({a}) = {N(f.subs(x, a))}$ and the limit of $\\dfrac{{f({a}+h) - f({a})}}{{h}}$ as $h \\to 0$ is $f'({a}) = {N(m)}$.", f"Tangent: $y - {N(f.subs(x, a))} = {N(m)}(x - {a})$, i.e. $y = {L(line)}$."],
            verify={'kind': 'tangent', 'expr': str(f), 'at': a}))

    # instantaneous velocity
    for _ in range(8):
        form = rng.choice(['fall', 'poly'])
        if form == 'fall':
            Hh = rng.choice([30, 45, 60, 80, 100]); s = Hh - sp.Rational(49, 10) * t**2; a = rng.randint(1, 3)
            stmt = f"A ball dropped from a height of ${Hh}$ m has height $s(t) = {L(s)}$ meters after $t$ seconds. Find its velocity (in m/s) at $t = {a}$."
        else:
            s = t**3 - rng.randint(2, 6) * t**2 + rng.randint(1, 10) * t; a = rng.randint(1, 4)
            stmt = f"A particle moves with position $s(t) = {L(s)}$ (meters, $t$ in seconds). Find its instantaneous velocity at $t = {a}$."
        d = sp.diff(s, t); val = d.subs(t, a)
        out.append(numeric_problem(S, stmt, val, difficulty=2,
            hints=["Instantaneous velocity is the derivative of position: the limit of average velocities over shrinking intervals.", f"Compute $\\lim_{{h \\to 0}} \\dfrac{{s({a}+h) - s({a})}}{{h}}$."],
            solution=[f"$\\dfrac{{s({a}+h) - s({a})}}{{h}} = {L(sp.cancel((s.subs(t, a+h) - s.subs(t, a))/h))}$.", f"As $h \\to 0$ this approaches $v({a}) = {N(val)}$ m/s{' (negative means downward)' if val < 0 else ''}."],
            verify={'kind': 'evaluate', 'expr': str(d.subs(t, x)), 'at': a}))

    # rates of change in applications (cost, temperature)
    for _ in range(6):
        form = rng.choice(['cost', 'temp', 'pop'])
        if form == 'cost':
            C = rng.choice([200, 500, 1000]) + rng.randint(3, 9) * x + sp.Rational(1, rng.choice([10, 20, 50])) * x**2; a = rng.choice([10, 20, 50, 100])
            stmt = f"The cost (in dollars) of producing $x$ items is $C(x) = {L(C)}$. Find the marginal cost $C'({a})$, the instantaneous rate of change of cost when $x = {a}$."
            f = C
        elif form == 'temp':
            f = rng.randint(10, 20) + rng.randint(2, 6) * x - sp.Rational(1, 2) * x**2; a = rng.randint(1, 5)
            stmt = f"The temperature of a liquid (in degrees) after $x$ minutes is $T(x) = {L(f)}$. Find the rate at which the temperature is changing at $x = {a}$ minutes."
        else:
            f = rng.choice([100, 200, 400]) + rng.randint(10, 30) * x + rng.randint(2, 5) * x**2; a = rng.randint(1, 5)
            stmt = f"A population after $x$ years is $P(x) = {L(f)}$. Find the instantaneous growth rate $P'({a})$."
        d = sp.diff(f, x); val = d.subs(x, a)
        out.append(numeric_problem(S, stmt, val, difficulty=2,
            hints=["An instantaneous rate of change is a derivative value: the limit of average rates over shorter and shorter intervals.", "Simplify the difference quotient, cancel $h$, and take the limit."],
            solution=[f"$\\dfrac{{f({a}+h) - f({a})}}{{h}} = {L(sp.cancel((f.subs(x, a+h) - f.subs(x, a))/h))}$.", f"The limit as $h \\to 0$ is ${N(val)}$ (units of output per unit of input)."],
            verify={'kind': 'evaluate', 'expr': str(d), 'at': a}))

    # recognize a limit as a derivative and evaluate it
    for _ in range(7):
        form = rng.choice(['pow', 'exp', 'sqrt', 'cos'])
        a = rng.randint(1, 4)
        if form == 'pow':
            p_ = rng.choice([3, 4, 5]); f = x**p_
            lim_l = f"\\lim_{{h \\to 0}} \\dfrac{{({a}+h)^{p_} - {a**p_}}}{{h}}"
        elif form == 'exp':
            f = sp.exp(x); a = 0
            lim_l = "\\lim_{h \\to 0} \\dfrac{e^{h} - 1}{h}"
        elif form == 'sqrt':
            a = rng.choice([1, 4, 9, 16]); f = sp.sqrt(x)
            lim_l = f"\\lim_{{x \\to {a}}} \\dfrac{{\\sqrt{{x}} - {int(sp.sqrt(a))}}}{{x - {a}}}"
        else:
            f = sp.cos(x); a = 0
            lim_l = "\\lim_{h \\to 0} \\dfrac{\\cos h - 1}{h}"
        d = sp.diff(f, x); val = d.subs(x, a)
        use_h = form != 'sqrt'
        if use_h:
            lim_expr = (f.subs(x, a + h) - f.subs(x, a)) / h
            lim_to = 0
        else:
            lim_expr = (f - f.subs(x, a)) / (x - a); lim_to = a
        out.append(numeric_problem(S, f"The limit $\\displaystyle {lim_l}$ represents the derivative of some function $f$ at a number $a$. Identify $f$ and $a$, and evaluate the limit.", val, difficulty=3,
            hints=["Match the expression to $\\dfrac{f(a+h) - f(a)}{h}$ or $\\dfrac{f(x) - f(a)}{x - a}$.", f"Here $f(x) = {L(f)}$ and $a = {a}$; the limit equals $f'({a})$."],
            solution=[f"With $f(x) = {L(f)}$ and $a = {a}$ the expression is exactly the difference quotient for $f'({a})$.", f"Evaluating the derivative gives $f'({a}) = {N(val)}$."],
            verify={'kind': 'limit', 'expr': str(lim_expr), 'to': lim_to}, variable='h' if use_h else 'x'))

    # average vs instantaneous rate
    for _ in range(5):
        f = pick(rng, fams[:3] + [fams[5]])(); a = rng.randint(0, 2); b = a + rng.randint(1, 3)
        avg = (f.subs(x, b) - f.subs(x, a)) / (b - a)
        out.append(numeric_problem(S, f"For $f(x) = {L(f)}$, find the average rate of change of $f$ over the interval $[{a}, {b}]$.", avg, difficulty=1,
            hints=["Average rate of change $= \\dfrac{f(b) - f(a)}{b - a}$.", f"Compute $f({b})$ and $f({a})$ first."],
            solution=[f"$f({b}) = {N(f.subs(x, b))}$ and $f({a}) = {N(f.subs(x, a))}$.", f"Average rate $= \\dfrac{{{N(f.subs(x, b))} - ({N(f.subs(x, a))})}}{{{b} - {a}}} = {N(avg)}$."],
            verify={'kind': 'evaluate', 'expr': f'(({str(f)}) - ({str(f.subs(x, a))}))/(x - {a})', 'at': b}))

    # read f(a) and f'(a) from a tangent line
    for _ in range(5):
        a = rng.randint(1, 5); m = nz(rng, -4, 4); b = rng.randint(-6, 6)
        which = rng.choice(['value', 'slope'])
        val = m * a + b if which == 'value' else m
        out.append(numeric_problem(S, f"The tangent line to $y = g(x)$ at the point where $x = {a}$ is $y = {L(m*x+b)}$. Find ${'g(' + str(a) + ')' if which == 'value' else 'g' + chr(39) + '(' + str(a) + ')'}$.", val, difficulty=1,
            hints=["The tangent line touches the curve at the point of tangency, and its slope equals the derivative there.", f"{'Plug $x = ' + str(a) + '$ into the line to get the point.' if which == 'value' else 'Read the slope of the line.'}"],
            solution=[f"The line passes through $({a}, g({a}))$, so $g({a}) = {m}({a}) + ({b}) = {m*a+b}$; its slope is $g'({a}) = {m}$.", f"Therefore the requested value is ${val}$."],
            verify={'kind': 'evaluate', 'expr': str(m * x + b) if which == 'value' else str(m), 'at': a}))

    # conceptual
    concept = [
        ("$f'(a)$ can be interpreted as", [("the slope of the tangent line to $y = f(x)$ at $x = a$", 'slope'), ("the $y$-coordinate of the point on the curve at $x = a$", 'y'), ("the area under the curve up to $x = a$", 'area'), ("the average rate of change of $f$ on $[0, a]$", 'avg')], 'slope',
         ["The derivative is a limit of secant slopes.", "Secant slopes approach the tangent slope."],
         ["$f'(a) = \\lim_{h \\to 0} \\frac{f(a+h) - f(a)}{h}$ is the limit of slopes of secant lines through $(a, f(a))$.", "That limit is the slope of the tangent line, also the instantaneous rate of change."]),
        ("If $s(t)$ is the position of a particle, the sign of $s'(t_0) < 0$ tells us that at time $t_0$", [("the particle is moving in the negative direction", 'neg'), ("the particle is at a negative position", 'pos'), ("the particle is slowing down", 'slow'), ("the particle is at rest", 'rest')], 'neg',
         ["$s'(t)$ is velocity, not position.", "Velocity's sign gives the direction of motion."],
         ["$s'(t_0)$ is the instantaneous velocity at $t_0$.", "Negative velocity means the position is decreasing, i.e. motion in the negative direction."]),
        ("Which expression equals $f'(a)$?", [("$\\lim_{x \\to a} \\dfrac{f(x) - f(a)}{x - a}$", 'alt'), ("$\\dfrac{f(a+1) - f(a)}{1}$", 'h1'), ("$\\lim_{x \\to a} f(x)$", 'lim'), ("$\\dfrac{f(a)}{a}$", 'ratio')], 'alt',
         ["Set $x = a + h$ in the definition; then $h \\to 0$ corresponds to $x \\to a$.", "Both forms are difference quotients with a limit."],
         ["With $x = a + h$, $\\frac{f(a+h) - f(a)}{h}$ becomes $\\frac{f(x) - f(a)}{x - a}$.", "So $f'(a) = \\lim_{x \\to a} \\frac{f(x) - f(a)}{x - a}$."]),
    ]
    for stmt, opts, lab, hints, sol in concept:
        out.append(label_mc(S, stmt, opts, lab, rng, difficulty=1, hints=hints, solution=sol))
    return out


# ======================================================================
# 2.8 derivative-function
# ======================================================================

def derivative_function():
    S = 'derivative-function'
    rng = seeded(S)
    out = []

    # f'(x) from the definition
    for _ in range(17):
        form = rng.choice(['quad', 'quad', 'cubic', 'sqrt', 'recip', 'lin'])
        if form == 'quad':
            f = nz(rng, -3, 3) * x**2 + rng.randint(-5, 5) * x + rng.randint(-4, 4); dom = (-3, 3)
        elif form == 'cubic':
            f = x**3 + rng.randint(-4, 4) * x; dom = (-3, 3)
        elif form == 'sqrt':
            c = rng.randint(0, 5); f = sp.sqrt(x + c); dom = (-c + 0.5, -c + 4)
        elif form == 'recip':
            c = rng.randint(-3, 3); k = rng.randint(1, 4); f = k / (x + c); dom = (-c + 0.5, -c + 3)
        else:
            f = nz(rng, -6, 6) * x + rng.randint(-5, 5); dom = (-3, 3)
        d = sp.diff(f, x)
        dq = sp.simplify((f.subs(x, x + h) - f) / h)
        if form == 'sqrt':
            dq = 1 / (sp.sqrt(x + h + c) + sp.sqrt(x + c))
        elif form == 'recip':
            dq = -k / ((x + h + c) * (x + c))
        out.append(equiv_problem(S, f"Use the definition of the derivative to find $f'(x)$ for $f(x) = {L(f)}$.", d, difficulty={'quad': 2, 'cubic': 3, 'sqrt': 3, 'recip': 3, 'lin': 1}[form], domain=dom,
            hints=["Form $\\dfrac{f(x+h) - f(x)}{h}$ and simplify until the $h$ in the denominator cancels" + {'sqrt': " (multiply by the conjugate).", 'recip': " (combine the fractions over a common denominator).", 'quad': " (expand $(x+h)^2$).", 'cubic': " (expand $(x+h)^3$).", 'lin': "."}[form],
                   "After canceling, let $h \\to 0$."],
            solution=[f"$\\dfrac{{f(x+h) - f(x)}}{{h}} = {L(dq)}$ for $h \\ne 0$" + (" (after multiplying by the conjugate and canceling $h$)" if form == 'sqrt' else (" (after combining fractions and canceling $h$)" if form == 'recip' else "")) + ".", f"Taking $h \\to 0$: $f'(x) = {L(d)}$."],
            verify={'kind': 'derivative', 'expr': str(f)}))

    # slope at a point from f'
    for _ in range(8):
        f = rng.choice([x**2 - rng.randint(1, 5) * x, x**3 + rng.randint(1, 3) * x, rng.randint(2, 4) * x**2 + rng.randint(1, 5), sp.sqrt(x) + rng.randint(1, 3) * x])
        a = rng.choice([1, 4]) if f.has(sp.sqrt) else rng.randint(-2, 3)
        d = sp.diff(f, x); val = d.subs(x, a)
        out.append(numeric_problem(S, f"Let $f(x) = {L(f)}$. Find the slope of the tangent line to the graph at $x = {a}$ by first finding $f'(x)$ from the definition.", val, difficulty=2,
            hints=["Find the derivative function first, then substitute the point.", f"$f'(x) = {L(d)}$."],
            solution=[f"From the definition, $f'(x) = {L(d)}$.", f"$f'({a}) = {N(val)}$."],
            verify={'kind': 'evaluate', 'expr': str(d), 'at': a}))

    # domain of f and f'
    for _ in range(5):
        a = rng.randint(-4, 4); form = rng.choice(['sqrt', 'cbrt'])
        if form == 'sqrt':
            f = sp.sqrt(x - a); ans = interval_str(a, sp.oo, True, True); exp_ = f'Interval.open({a}, oo)'
            why = f"$f$ is defined for $x \\ge {a}$, but $f'(x) = \\dfrac{{1}}{{2\\sqrt{{x - ({a})}}}}$ is undefined at $x = {a}$ (vertical tangent)"
        else:
            f = sp.cbrt(x - a); ans = interval_str(a, sp.oo, True, True); exp_ = f'Interval.open({a}, oo)'
            f = sp.sqrt(x - a) * x if False else sp.sqrt(x - a) + x; why = f"$f$ is defined for $x \\ge {a}$ and $f'(x) = \\dfrac{{1}}{{2\\sqrt{{x - ({a})}}}} + 1$ requires $x > {a}$"
        out.append(interval_problem(S, f"Find the domain of $f'$ where $f(x) = {L(f)}$. Answer in interval notation.", ans, exp_, difficulty=2,
            hints=["First find $f'(x)$ (by the definition or by recalling the derivative of a square root).", "Then find where that formula makes sense; the endpoint of the domain of $f$ usually drops out."],
            solution=[f"{why}.", f"Domain of $f'$: $({a}, \\infty)$."]))

    # not differentiable at a point
    for _ in range(5):
        a = rng.randint(-4, 4); c = rng.randint(-3, 3)
        form = rng.choice(['abs', 'cbrt'])
        f = sp.Abs(x - a) + c if form == 'abs' else sp.cbrt(x - a) + c
        out.append(numeric_problem(S, f"The function $f(x) = {L(f) if form == 'abs' else f'\\sqrt[3]{{x {signed(-a)}}} {signed(c) if c else ''}'}$ is continuous everywhere but fails to be differentiable at exactly one point. Find that $x$-value.", a, difficulty=1,
            hints=[{'abs': "An absolute value graph has a corner where the inside is zero.", 'cbrt': "A cube root graph has a vertical tangent where the inside is zero."}[form], f"Solve $x {signed(-a)} = 0$."],
            solution=[{'abs': f"For $x > {a}$ the slope is $1$ and for $x < {a}$ it is $-1$; the one-sided limits of the difference quotient disagree at $x = {a}$.", 'cbrt': f"The difference quotient at $x = {a}$ is $h^{{1/3}}/h = h^{{-2/3}} \\to \\infty$, a vertical tangent."}[form], f"So $f$ is not differentiable at $x = {a}$."],
            verify={'kind': 'solve', 'lhs': str(x - a), 'rhs': 0}))

    # second derivative
    for _ in range(6):
        f = nz(rng, -3, 3) * x**3 + rng.randint(-5, 5) * x**2 + rng.randint(-4, 4) * x + rng.randint(-3, 3)
        if rng.random() < 0.3:
            f = x**4 - rng.randint(1, 4) * x**2 + rng.randint(1, 3) * x
        d2 = sp.diff(f, x, 2)
        out.append(equiv_problem(S, f"Find the second derivative $f''(x)$ of $f(x) = {L(f)}$.", d2, difficulty=2,
            hints=["$f''$ is the derivative of $f'$: differentiate twice.", f"$f'(x) = {L(sp.diff(f, x))}$; now differentiate that."],
            solution=[f"$f'(x) = {L(sp.diff(f, x))}$.", f"$f''(x) = {L(d2)}$."],
            verify={'kind': 'equiv', 'expected': f'diff({str(f)}, x, 2)'}))

    # where f' is negative (interval)
    for _ in range(5):
        r1, r2 = sorted(rng.sample([-3, -2, -1, 0, 1, 2, 3], 2))
        d = 3 * sp.expand((x - r1) * (x - r2)); f = sp.integrate(d, x) + rng.randint(-3, 3)
        out.append(interval_problem(S, f"Let $f(x) = {L(f)}$. On which open interval is $f'(x) < 0$ (so that $f$ is decreasing)? Answer in interval notation.", interval_str(r1, r2, True, True), f'{str(d)} < 0', difficulty=3,
            hints=["Compute $f'(x)$ and factor it.", f"$f'(x) = {L(d)} = 3(x {signed(-r1)})(x {signed(-r2)})$; a product of two linear factors is negative between its roots."],
            solution=[f"$f'(x) = 3(x {signed(-r1)})(x {signed(-r2)})$ has roots ${r1}$ and ${r2}$.", f"The parabola opens upward, so $f'(x) < 0$ exactly on $({r1}, {r2})$."]))

    # dy/dx notation
    for _ in range(4):
        f = rng.randint(1, 4) * x**2 - rng.randint(1, 6) * x + rng.randint(1, 5); a = rng.randint(-2, 3)
        d = sp.diff(f, x); val = d.subs(x, a)
        out.append(numeric_problem(S, f"If $y = {L(f)}$, find $\\left.\\dfrac{{dy}}{{dx}}\\right|_{{x = {a}}}$.", val, difficulty=1,
            hints=["$\\frac{dy}{dx}$ is Leibniz notation for the derivative $f'(x)$; the vertical bar means evaluate at that $x$.", f"$\\frac{{dy}}{{dx}} = {L(d)}$."],
            solution=[f"$\\dfrac{{dy}}{{dx}} = {L(d)}$.", f"At $x = {a}$: ${N(val)}$."],
            verify={'kind': 'evaluate', 'expr': str(d), 'at': a}))

    # conceptual
    concept = [
        ("If $f$ is differentiable at $a$, which statement must be true?", [("$f$ is continuous at $a$", 'cont'), ("$f'$ is continuous at $a$", 'dcont'), ("$f$ has a maximum or minimum at $a$", 'ext'), ("$f(a) = 0$", 'zero')], 'cont',
         ["Differentiability is a stronger condition than continuity.", "The converse (continuous implies differentiable) is false: think of $|x|$ at $0$."],
         ["Theorem: differentiable at $a$ implies continuous at $a$.", "Nothing is implied about the continuity of $f'$ or about extreme values."]),
        ("The graph of $y = |x|$ shows that", [("a continuous function need not be differentiable", 'cont_not_diff'), ("a differentiable function need not be continuous", 'diff_not_cont'), ("every continuous function is differentiable", 'all'), ("the derivative of $|x|$ is $1$ everywhere", 'one')], 'cont_not_diff',
         ["$|x|$ is continuous at $0$, but what about the slopes on each side of $0$?", "Left slope $-1$, right slope $1$: the difference quotient has no limit."],
         ["$|x|$ is continuous everywhere but has a corner at $0$, where it is not differentiable.", "So continuity does not imply differentiability."]),
        ("On an interval where $f'(x) > 0$, the graph of $f$ is", [("rising (increasing)", 'inc'), ("falling (decreasing)", 'dec'), ("horizontal", 'flat'), ("concave down", 'cd')], 'inc',
         ["$f'(x)$ is the slope of the tangent line at $x$.", "Positive slopes point upward as $x$ increases."],
         ["Positive derivative means positive tangent slopes.", "So $f$ increases on that interval."]),
        ("Which situation makes $f$ fail to be differentiable at $a$ even though $f$ is continuous there?", [("a corner, a vertical tangent, or a cusp at $a$", 'all'), ("$f(a) < 0$", 'neg'), ("$f'(a) = 0$", 'zero'), ("$f$ is constant near $a$", 'const')], 'all',
         ["Think of $|x|$, $\\sqrt[3]{x}$ and $x^{2/3}$ at $x = 0$.", "A zero derivative is fine; an undefined limit of difference quotients is the problem."],
         ["At a corner the one-sided slopes disagree; at a vertical tangent or cusp the difference quotient becomes infinite.", "In each case the limit defining $f'(a)$ fails to exist."]),
    ]
    for stmt, opts, lab, hints, sol in concept:
        out.append(label_mc(S, stmt, opts, lab, rng, difficulty=1, hints=hints, solution=sol))
    return out


def build() -> dict:
    return {
        'tangent-and-velocity': tidy(tangent_and_velocity()),
        'limits-intro': tidy(limits_intro()),
        'limit-laws': tidy(limit_laws()),
        'precise-limit': tidy(precise_limit()),
        'continuity': tidy(continuity()),
        'limits-at-infinity': tidy(limits_at_infinity()),
        'derivatives-rates': tidy(derivatives_rates()),
        'derivative-function': tidy(derivative_function()),
    }
