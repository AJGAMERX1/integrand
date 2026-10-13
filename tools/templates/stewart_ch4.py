"""Stewart Chapter 4.9 and 5.1-5.4 templates (original problems, SymPy-verified):
antiderivatives (4.9), areas-and-distances (5.1), definite-integral (5.2), ftc (5.3), indefinite-integrals (5.4).
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
                     label_mc, numeric_problem, equiv_problem, interval_problem, interval_str, interval_ltx, h, y, n, k,
                     tidy, pow_form, int_ltx, indefinite_problem, definite_problem, nice_anti)

sin, cos, tan, sec, csc, cot, exp, log, sqrt, pi, E = sp.sin, sp.cos, sp.tan, sp.sec, sp.csc, sp.cot, sp.exp, sp.log, sp.sqrt, sp.pi, sp.E
i = sp.Symbol('i')


def power_rule_hint(f):
    return "Reverse the power rule: $\\displaystyle\\int x^n\\,dx = \\frac{x^{n+1}}{n+1} + C$ for $n \\ne -1$; integrate term by term."


# ======================================================================
# 4.9 antiderivatives
# ======================================================================

def antiderivatives():
    S = 'antiderivatives'
    rng = seeded(S)
    out = []

    # most general antiderivative: polynomials and powers
    for _ in range(12):
        form = rng.choice(['poly', 'poly', 'powers', 'roots', 'mixed_neg'])
        if form == 'poly':
            f = sum(rng.randint(-5, 5) * x**j for j in range(rng.randint(2, 4))) + nz(rng, -4, 4) * x**rng.randint(2, 4); dom = (-2, 2)
        elif form == 'powers':
            f = nz(rng, -6, 6) * x**rng.choice([sp.Rational(1, 2), sp.Rational(3, 2), sp.Rational(-1, 2), sp.Rational(2, 3)]) + rng.randint(-3, 3); dom = (0.5, 3)
        elif form == 'roots':
            f = rng.randint(1, 4) * sqrt(x) - rng.randint(1, 4) * sp.cbrt(x); dom = (0.5, 3)
        else:
            f = rng.randint(1, 5) / x**rng.choice([2, 3]) + nz(rng, -3, 3) * x; dom = (0.5, 3)
        F = sp.integrate(f, x)
        out.append(indefinite_problem(S, f, F, difficulty=1 if form == 'poly' else 2, domain=dom,
            stmt=f"Find the most general antiderivative of $f(x) = {L(f)}$. (Use $C$ for the constant.)",
            hints=[power_rule_hint(f), "Write roots and reciprocals as powers of $x$ first; check your answer by differentiating it."],
            solution=[f"Rewrite each term as a power of $x$: $f(x) = {pow_form(f)}$." if form != 'poly' else f"Integrate term by term, raising each exponent by one and dividing by the new exponent.",
                      f"$F(x) = {L(F)} + C$.", f"Check: $F'(x) = {L(sp.diff(F, x))} = f(x)$."]))

    # antiderivatives involving e^x, trig, 1/x, 1/(1+x^2)
    for _ in range(10):
        form = rng.choice(['exp', 'sincos', 'sec2', 'recip', 'atan', 'sectan', 'mixed'])
        a, b = nz(rng, -4, 4), nz(rng, -4, 4)
        if form == 'exp':
            f = a * exp(x) + b * x**2; dom = (-2, 2); rule = "$\\int e^x\\,dx = e^x + C$"
        elif form == 'sincos':
            f = a * sin(x) + b * cos(x); dom = (-3, 3); rule = "$\\int \\sin x\\,dx = -\\cos x + C$ and $\\int \\cos x\\,dx = \\sin x + C$"
        elif form == 'sec2':
            f = a * sec(x)**2 + b; dom = (-1, 1); rule = "$\\int \\sec^2 x\\,dx = \\tan x + C$"
        elif form == 'recip':
            f = a / x + b * x; dom = (0.5, 3); rule = "$\\int \\frac{1}{x}\\,dx = \\ln|x| + C$"
        elif form == 'atan':
            f = a / (1 + x**2) + b; dom = (-2, 2); rule = "$\\int \\frac{1}{1 + x^2}\\,dx = \\arctan x + C$"
        elif form == 'sectan':
            f = a * sec(x) * tan(x) - b * sin(x); dom = (-1, 1); rule = "$\\int \\sec x\\tan x\\,dx = \\sec x + C$"
        else:
            f = a * exp(x) - b * cos(x) + rng.randint(1, 3) / sqrt(1 - x**2); dom = (-0.8, 0.8); rule = "$\\int \\frac{1}{\\sqrt{1 - x^2}}\\,dx = \\arcsin x + C$"
        F = sp.integrate(f, x)
        out.append(indefinite_problem(S, f, F, difficulty=2, domain=dom,
            stmt=f"Find the most general antiderivative of $f(x) = {L(f)}$.",
            hints=["Each term matches a derivative you know; think of which function differentiates to it.", f"Use {rule}."],
            solution=[f"Antidifferentiate term by term using {rule}.", f"$F(x) = {L(F)} + C$."]))

    # initial value problems
    for _ in range(12):
        form = rng.choice(['poly', 'poly', 'exp', 'trig', 'power'])
        a = rng.choice([0, 1, 2, -1])
        if form == 'poly':
            fp = sum(rng.randint(-4, 4) * x**j for j in range(rng.randint(1, 3))) + nz(rng, -3, 3) * x**rng.randint(1, 3); dom = (-2, 2)
        elif form == 'exp':
            fp = rng.randint(1, 3) * exp(x) + rng.randint(-3, 3); a = 0; dom = (-1, 1)
        elif form == 'trig':
            fp = rng.randint(1, 3) * cos(x) - rng.randint(1, 3) * sin(x); a = 0; dom = (-2, 2)
        else:
            fp = rng.randint(1, 3) * sqrt(x) + rng.randint(-2, 2); a = rng.choice([1, 4]); dom = (0.5, 5)
        b = rng.randint(-5, 5)
        F0 = sp.integrate(fp, x); C = b - F0.subs(x, a); F = F0 + C
        out.append(equiv_problem(S, f"Find $f$ given that $f'(x) = {L(fp)}$ and $f({a}) = {b}$.", F, difficulty=2, domain=dom,
            hints=["First find the general antiderivative $f(x) = F(x) + C$.", f"Then use $f({a}) = {b}$ to solve for $C$."],
            solution=[f"$f(x) = {L(F0)} + C$.", f"$f({a}) = {N(F0.subs(x, a))} + C = {b}$ gives $C = {N(C)}$.", f"$f(x) = {L(F)}$."],
            verify={'kind': 'ivp', 'deriv': str(fp), 'order': 1, 'conditions': [[a, str(b), 0]]}))

    # second order initial value problems
    for _ in range(7):
        fpp = rng.choice([rng.randint(1, 4) * x + rng.randint(-3, 3), rng.randint(2, 6) * x**2 - rng.randint(1, 3), rng.randint(1, 3) * exp(x), rng.randint(1, 3) * cos(x) + rng.randint(1, 3), rng.randint(2, 12) * x**2 + rng.randint(1, 4) * x])
        fp0, f0 = rng.randint(-4, 4), rng.randint(-4, 4)
        F1 = sp.integrate(fpp, x); C1 = fp0 - F1.subs(x, 0); F1 = F1 + C1
        F2 = sp.integrate(F1, x); C2 = f0 - F2.subs(x, 0); F = F2 + C2
        out.append(equiv_problem(S, f"Find $f$ given that $f''(x) = {L(fpp)}$, $f'(0) = {fp0}$ and $f(0) = {f0}$.", F, difficulty=3, domain=(-1.5, 1.5),
            hints=["Antidifferentiate twice, keeping a separate constant each time.", "Use $f'(0)$ to fix the first constant before integrating again, then $f(0)$ for the second."],
            solution=[f"$f'(x) = {L(sp.integrate(fpp, x))} + C_1$, and $f'(0) = {fp0}$ gives $C_1 = {N(C1)}$, so $f'(x) = {L(F1)}$.",
                      f"$f(x) = {L(F2)} + C_2$, and $f(0) = {f0}$ gives $C_2 = {N(C2)}$.", f"$f(x) = {L(F)}$."],
            verify={'kind': 'ivp', 'deriv': str(fpp), 'order': 2, 'conditions': [[0, str(fp0), 1], [0, str(f0), 0]]}))

    # motion: velocity -> position, acceleration -> velocity/position
    for _ in range(8):
        form = rng.choice(['v_to_s', 'a_to_s', 'a_to_v'])
        if form == 'v_to_s':
            v = rng.randint(1, 4) * t**2 - rng.randint(1, 6) * t + rng.randint(0, 5); s0 = rng.randint(-3, 5)
            S0 = sp.integrate(v, t); s_ = S0 + (s0 - S0.subs(t, 0))
            out.append(equiv_problem(S, f"A particle moves along a line with velocity $v(t) = {L(v)}$ (m/s) and initial position $s(0) = {s0}$ m. Find its position function $s(t)$.", s_, difficulty=2, variable='t', domain=(0, 3),
                hints=["Position is an antiderivative of velocity: $s(t) = \\int v(t)\\,dt$.", "Use the initial position to determine the constant."],
                solution=[f"$s(t) = {L(S0)} + C$.", f"$s(0) = {s0}$ gives $C = {s0}$, so $s(t) = {L(s_)}$."],
                verify={'kind': 'ivp', 'deriv': str(v), 'order': 1, 'conditions': [[0, str(s0), 0]]}))
        elif form == 'a_to_v':
            acc = rng.randint(1, 6) * t + rng.randint(-4, 4); v0 = rng.randint(-5, 5)
            V0 = sp.integrate(acc, t); v_ = V0 + v0
            out.append(equiv_problem(S, f"A particle has acceleration $a(t) = {L(acc)}$ and initial velocity $v(0) = {v0}$. Find the velocity function $v(t)$.", v_, difficulty=1, variable='t', domain=(0, 3),
                hints=["Velocity is an antiderivative of acceleration.", "The constant of integration equals $v(0)$ here."],
                solution=[f"$v(t) = {L(V0)} + C$.", f"$v(0) = {v0}$ gives $C = {v0}$, so $v(t) = {L(v_)}$."],
                verify={'kind': 'ivp', 'deriv': str(acc), 'order': 1, 'conditions': [[0, str(v0), 0]]}))
        else:
            acc = rng.choice([-10, 6, rng.randint(2, 8) * t, 12 * t - 4]); v0 = rng.randint(-3, 6); s0 = rng.randint(0, 10)
            V0 = sp.integrate(acc, t) + v0; S0 = sp.integrate(V0, t) + s0
            out.append(equiv_problem(S, f"A particle has acceleration $a(t) = {L(acc)}$, initial velocity $v(0) = {v0}$ and initial position $s(0) = {s0}$. Find the position function $s(t)$.", S0, difficulty=3, variable='t', domain=(0, 3),
                hints=["Integrate acceleration to get velocity (fix the constant with $v(0)$), then integrate velocity to get position (fix the constant with $s(0)$).", f"$v(t) = {L(V0)}$."],
                solution=[f"$v(t) = \\int a(t)\\,dt = {L(V0)}$ after using $v(0) = {v0}$.", f"$s(t) = \\int v(t)\\,dt = {L(S0)}$ after using $s(0) = {s0}$."],
                verify={'kind': 'ivp', 'deriv': str(acc), 'order': 2, 'conditions': [[0, str(v0), 1], [0, str(s0), 0]]}))

    # thrown object: max height / time to land
    for _ in range(5):
        v0 = rng.choice([10, 20, 30, 40]); h0 = rng.choice([0, 5, 15, 25]); g = 10
        hgt = h0 + v0 * t - sp.Rational(g, 2) * t**2
        which = rng.choice(['max', 'time'])
        if which == 'max':
            tmax = sp.Rational(v0, g); val = hgt.subs(t, tmax)
            out.append(numeric_problem(S, f"A ball is thrown upward from a height of ${h0}$ m with initial velocity ${v0}$ m/s; take the acceleration due to gravity as $-{g}$ m/s$^2$. Find the maximum height the ball reaches (in meters).", val, difficulty=3,
                hints=[f"Antidifferentiate $a = -{g}$ twice using $v(0) = {v0}$ and $s(0) = {h0}$ to get the height function.", "The maximum occurs when the velocity is zero."],
                solution=[f"$v(t) = {v0} - {g}t$ and $s(t) = {L(hgt)}$.", f"$v = 0$ at $t = {N(tmax)}$, where $s = {N(val)}$ m."],
                verify={'kind': 'evaluate', 'expr': str(hgt.subs(t, x)), 'at': str(tmax)}))
        else:
            roots = [r for r in sp.solve(hgt, t) if r.is_real and r > 0]
            if not roots:
                continue
            out.append(numeric_problem(S, f"A ball is thrown upward from a height of ${h0}$ m with initial velocity ${v0}$ m/s; take gravity as $-{g}$ m/s$^2$. When does the ball hit the ground? Give the exact time in seconds.", roots[0], difficulty=3,
                hints=[f"Build the height function: $s(t) = {h0} + {v0}t - {g//2}t^2$.", "Solve $s(t) = 0$ and keep the positive root."],
                solution=[f"$s(t) = {L(hgt)}$.", f"$s(t) = 0$ gives $t = {L(roots[0])}$ s (the other root is negative)."],
                verify={'kind': 'solve', 'lhs': str(hgt.subs(t, x)), 'rhs': 0, 'pick': str(roots[0])}))

    # evaluate the particular antiderivative at another point
    for _ in range(5):
        fp = rng.choice([rng.randint(2, 6) * x + rng.randint(-3, 3), 3 * x**2 - rng.randint(1, 4), rng.randint(1, 3) * exp(x), cos(x) * rng.randint(1, 3)])
        a = 0; b = rng.randint(-3, 3); c = rng.choice([1, 2, -1]) if not fp.has(cos) else pi / 2
        F0 = sp.integrate(fp, x); F = F0 + (b - F0.subs(x, a)); val = sp.simplify(F.subs(x, c))
        out.append(numeric_problem(S, f"Let $F$ be the antiderivative of $f(x) = {L(fp)}$ with $F({a}) = {b}$. Find $F\\left({L(c)}\\right)$.", val, difficulty=2,
            hints=["Find the general antiderivative, use the given value to pin down $C$, then evaluate.", f"$F(x) = {L(F0)} + C$."],
            solution=[f"$F(x) = {L(F0)} + C$ and $F({a}) = {b}$ gives $C = {N(b - F0.subs(x, a))}$, so $F(x) = {L(F)}$.", f"$F({L(c)}) = {L(val)}$."],
            verify={'kind': 'evaluate', 'expr': str(F), 'at': str(c)}))

    # conceptual
    concept = [
        ("If $F$ is an antiderivative of $f$ on an interval, the most general antiderivative of $f$ is", [("$F(x) + C$ for an arbitrary constant $C$", 'ok'), ("$F(x)$ only", 'only'), ("$C\\,F(x)$", 'mult'), ("$F(x) + Cx$", 'cx')], 'ok',
         ["Two functions with the same derivative on an interval differ by a constant.", "Adding a constant does not change the derivative."],
         ["$(F + C)' = F' = f$, and any antiderivative $G$ satisfies $(G - F)' = 0$, so $G - F$ is constant.", "Hence every antiderivative has the form $F(x) + C$."]),
        ("Which function is an antiderivative of $\\dfrac{1}{x}$ on $(0, \\infty)$?", [("$\\ln x$", 'ok'), ("$-\\dfrac{1}{x^2}$", 'deriv'), ("$\\dfrac{x^0}{0}$", 'zero'), ("$e^x$", 'exp')], 'ok',
         ["The power rule fails for $n = -1$ because it would divide by zero.", "Which function has derivative $1/x$?"],
         ["$\\frac{d}{dx}\\ln x = \\frac{1}{x}$ for $x > 0$.", "So $\\ln x$ (and $\\ln|x|$ in general) is the antiderivative of $1/x$; the power rule does not apply when $n = -1$."]),
        ("An antiderivative of $\\sin x$ is", [("$-\\cos x$", 'ok'), ("$\\cos x$", 'pos'), ("$-\\sin x$", 'sin'), ("$\\tan x$", 'tan')], 'ok',
         ["Which function has derivative $\\sin x$?", "Recall $(\\cos x)' = -\\sin x$ and adjust the sign."],
         ["$\\frac{d}{dx}(-\\cos x) = \\sin x$.", "So $-\\cos x + C$ is the general antiderivative of $\\sin x$."]),
    ]
    for stmt, opts, lab, hints, sol in concept:
        out.append(label_mc(S, stmt, opts, lab, rng, difficulty=1, hints=hints, solution=sol))
    return out


# ======================================================================
# 5.1 areas-and-distances
# ======================================================================

def areas_and_distances():
    S = 'areas-and-distances'
    rng = seeded(S)
    out = []
    curves = [lambda: x**2, lambda: x**2 + rng.randint(1, 3), lambda: rng.randint(1, 3) * x + rng.randint(0, 3), lambda: x**3, lambda: rng.randint(2, 5) * x - x**2 + 1, lambda: sqrt(x), lambda: 1 / x, lambda: 8 - x**2]

    # Riemann sums with n rectangles
    for _ in range(16):
        f = pick(rng, curves)(); a = rng.choice([0, 0, 1, 2]); n_ = rng.choice([4, 4, 5, 6, 8]); b = a + rng.choice([2, 4, 1, 3])
        if f == 1 / x and a == 0:
            a = 1; b = 3
        if f == sqrt(x) and a == 0:
            b = 4; n_ = 4
        method = rng.choice(['left', 'right', 'mid'])
        dx = sp.Rational(b - a, n_)
        pts = [a + j * dx for j in range(n_)] if method == 'left' else ([a + (j + 1) * dx for j in range(n_)] if method == 'right' else [a + (j + sp.Rational(1, 2)) * dx for j in range(n_)])
        val = sum(f.subs(x, c) for c in pts) * dx
        if not sp.nsimplify(val).is_rational:
            continue
        name = {'left': 'left endpoints', 'right': 'right endpoints', 'mid': 'midpoints'}[method]
        sym = {'left': 'L', 'right': 'R', 'mid': 'M'}[method]
        out.append(numeric_problem(S, f"Estimate the area under $y = {L(f)}$ from $x = {a}$ to $x = {b}$ using ${n_}$ rectangles of equal width and {name} as sample points. (This is ${sym}_{{{n_}}}$.)", val, difficulty=2 if n_ <= 5 else 3,
            hints=[f"The width of each rectangle is $\\Delta x = \\dfrac{{{b} - {a}}}{{{n_}}} = {N(dx)}$.", f"The sample points are $x = {', '.join(N(c) for c in pts)}$; add up $f(x_i)\\,\\Delta x$."],
            solution=[f"$\\Delta x = {N(dx)}$ and the heights are $f({') + f('.join(N(c) for c in pts)}) = {' + '.join(N(f.subs(x, c)) for c in pts)}$." if n_ <= 6 else f"$\\Delta x = {N(dx)}$; the heights are $f(x_i)$ at $x_i = {', '.join(N(c) for c in pts)}$.",
                      f"${sym}_{{{n_}}} = \\Delta x \\sum f(x_i) = {N(dx)} \\cdot {N(sum(f.subs(x, c) for c in pts))} = {N(val)}$."],
            verify={'kind': 'riemann', 'expr': str(f), 'a': a, 'b': b, 'n': n_, 'method': method}))

    # sigma notation evaluation
    for _ in range(8):
        form = rng.choice(['lin', 'sq', 'const_plus', 'cube', 'alt'])
        lo, hi = rng.choice([(1, 4), (1, 5), (1, 6), (0, 4), (2, 6), (1, 10)])
        if form == 'lin':
            term = rng.randint(1, 4) * i + rng.randint(-2, 3)
        elif form == 'sq':
            term = i**2 + rng.randint(0, 2) * i
        elif form == 'const_plus':
            term = rng.randint(2, 5) + 0 * i
        elif form == 'cube':
            term = i**3; lo, hi = (1, rng.choice([3, 4]))
        else:
            term = (-1)**i * i; lo, hi = (1, rng.choice([4, 5, 6]))
        val = sp.summation(term, (i, lo, hi))
        out.append(numeric_problem(S, f"Evaluate the sum $\\displaystyle\\sum_{{i={lo}}}^{{{hi}}} \\left({L(term)}\\right)$.", val, difficulty=1,
            hints=[f"Sigma notation means: substitute $i = {lo}, {lo+1}, \\dots, {hi}$ into the formula and add the results.", f"Write out the terms: ${' + '.join('(' + N(term.subs(i, j)) + ')' for j in range(lo, min(hi, lo + 4) + 1))}{' + \\cdots' if hi - lo > 4 else ''}$."],
            solution=[f"The terms are ${', '.join(N(term.subs(i, j)) for j in range(lo, hi + 1))}$.", f"Their sum is ${N(val)}$."],
            verify={'kind': 'sum', 'term': str(term), 'var': 'i', 'lo': lo, 'hi': hi}))

    # distance from a velocity table
    for _ in range(6):
        n_ = rng.choice([4, 5]); dt = rng.choice([1, 2, 5, 10]); ts = [j * dt for j in range(n_ + 1)]
        vs = [rng.randint(0, 12) + 2 * j for j in range(n_ + 1)]
        method = rng.choice(['left', 'right'])
        used = vs[:-1] if method == 'left' else vs[1:]
        val = sum(used) * dt
        table = "\\begin{array}{c|" + "c" * (n_ + 1) + "} t\\ (\\text{s}) & " + " & ".join(map(str, ts)) + " \\\\ \\hline v\\ (\\text{m/s}) & " + " & ".join(map(str, vs)) + " \\end{array}"
        out.append(numeric_problem(S, f"The velocity of a runner was recorded every ${dt}$ seconds: ${table}$. Estimate the distance traveled during the ${ts[-1]}$ seconds using {'left' if method == 'left' else 'right'} endpoints (treat the velocity as constant on each interval).", val, difficulty=2,
            hints=["Distance is velocity times time on each short interval; add the pieces.", f"Each interval lasts ${dt}$ s; use the velocity at its {'start' if method == 'left' else 'end'}."],
            solution=[f"Distance $\\approx ({' + '.join(map(str, used))}) \\cdot {dt}$.", f"$= {sum(used)} \\cdot {dt} = {val}$ m."],
            verify={'kind': 'numeric', 'value': f'({"+".join(map(str, used))})*{dt}'}))

    # right-endpoint sum as a formula in n, and its limit
    for _ in range(8):
        form = rng.choice(['x', 'x2', 'x_on_0b', 'x2_on_0b'])
        b = rng.choice([1, 2, 3, 4]) if 'b' in form else 1
        f = x if form in ('x', 'x_on_0b') else x**2
        dx = sp.Rational(b, 1) / n
        Rn = sp.summation(f.subs(x, i * dx) * dx, (i, 1, n))
        Rn = sp.simplify(Rn)
        if rng.random() < 0.5:
            out.append(equiv_problem(S, f"For $f(x) = {L(f)}$ on $[0, {b}]$, use right endpoints and $n$ subintervals of equal width to express the Riemann sum $R_n = \\sum_{{i=1}}^{{n}} f(x_i)\\,\\Delta x$ as a closed-form expression in $n$.", Rn, difficulty=3, variable='n', domain=(1, 20),
                hints=[f"$\\Delta x = {b}/n$ and $x_i = {b}i/n$, so each term is $f({b}i/n)\\cdot {b}/n$.", "Use $\\sum_{i=1}^n i = \\frac{n(n+1)}{2}$ or $\\sum_{i=1}^n i^2 = \\frac{n(n+1)(2n+1)}{6}$."],
                solution=[f"$R_n = \\sum_{{i=1}}^n {L(f.subs(x, b*i/n))} \\cdot \\dfrac{{{b}}}{{n}} = \\dfrac{{{b**(2 if f == x else 3)}}}{{n^{{{2 if f == x else 3}}}}} \\sum_{{i=1}}^n {L(f.subs(x, i))}$.", f"Using the sum formula: $R_n = {L(Rn)}$."],
                verify={'kind': 'equiv', 'expected': f'summation(({str(f.subs(x, i*b/n))})*({b}/n), (i, 1, n))'}))
        else:
            val = sp.limit(Rn, n, sp.oo)
            out.append(numeric_problem(S, f"The right-endpoint Riemann sum for $f(x) = {L(f)}$ on $[0, {b}]$ with $n$ subintervals simplifies to $R_n = {L(Rn)}$. Find the exact area under the curve by computing $\\displaystyle\\lim_{{n \\to \\infty}} R_n$.", val, difficulty=2,
                hints=["Expand or divide through by the highest power of $n$.", "Terms like $1/n$ and $1/n^2$ vanish in the limit."],
                solution=[f"$R_n = {L(sp.expand(Rn))}$.", f"As $n \\to \\infty$ the terms with $n$ in the denominator go to $0$, leaving ${N(val)}$."],
                verify={'kind': 'limit', 'expr': str(Rn), 'to': 'oo'}, variable='n'))

    # delta x and sample points
    for _ in range(5):
        a, b = rng.choice([(0, 3), (1, 4), (2, 7), (-1, 3), (0, 10)]); n_ = rng.choice([4, 5, 6, 8, 10]); kk = rng.randint(1, n_)
        dx = sp.Rational(b - a, n_)
        which = rng.choice(['dx', 'xk'])
        if which == 'dx':
            out.append(numeric_problem(S, f"The interval $[{a}, {b}]$ is divided into ${n_}$ subintervals of equal width. What is $\\Delta x$?", dx, difficulty=1,
                hints=["$\\Delta x$ is the total length divided by the number of pieces.", f"$\\Delta x = \\dfrac{{b - a}}{{n}} = \\dfrac{{{b} - ({a})}}{{{n_}}}$."],
                solution=[f"$\\Delta x = \\dfrac{{{b} - ({a})}}{{{n_}}}$.", f"$= {N(dx)}$."],
                verify={'kind': 'numeric', 'value': f'({b} - ({a}))/{n_}'}))
        else:
            xk = a + kk * dx
            out.append(numeric_problem(S, f"The interval $[{a}, {b}]$ is divided into ${n_}$ equal subintervals with endpoints $x_0 = {a}, x_1, \\dots, x_{{{n_}}} = {b}$. Find $x_{{{kk}}}$.", xk, difficulty=1,
                hints=[f"First compute $\\Delta x = \\dfrac{{{b} - ({a})}}{{{n_}}}$.", f"Then $x_k = a + k\\,\\Delta x$ with $k = {kk}$."],
                solution=[f"$\\Delta x = {N(dx)}$.", f"$x_{{{kk}}} = {a} + {kk}\\cdot {N(dx)} = {N(xk)}$."],
                verify={'kind': 'numeric', 'value': f'{a} + {kk}*({b} - ({a}))/{n_}'}))

    # over/under estimates for monotonic functions
    for _ in range(4):
        f = rng.choice([x**2 + 1, exp(x), sqrt(x) + 1, 10 - x**2, 1 / (x + 1)])
        inc = bool(sp.diff(f, x).subs(x, 1) > 0)
        which = rng.choice(['left', 'right'])
        correct = 'under' if (inc == (which == 'left')) else 'over'
        opts = [("an underestimate of the area", 'under'), ("an overestimate of the area", 'over'), ("exactly the area", 'exact'), ("impossible to tell without computing", 'unknown')]
        out.append(label_mc(S, f"The function $f(x) = {L(f)}$ is {'increasing' if inc else 'decreasing'} on $[0, 2]$. Using {which} endpoints, is the Riemann sum $\\sum f(x_i)\\Delta x$ an underestimate or an overestimate of the area under the graph on $[0, 2]$?", opts, correct, rng, difficulty=2,
            hints=["Sketch one subinterval: does the rectangle's top sit below or above the curve?", f"For an {'increasing' if inc else 'decreasing'} function, the {'left' if inc else 'right'} endpoint gives the smallest height on each subinterval."],
            solution=[f"On each subinterval an {'increasing' if inc else 'decreasing'} function has its {'smallest' if (which == 'left') == inc else 'largest'} value at the {which} endpoint, so each rectangle lies {'inside' if correct == 'under' else 'above'} the region.", f"Therefore the {which}-endpoint sum is an {correct}estimate."]))

    # area as a limit (conceptual)
    for _ in range(4):
        f = rng.choice([x**3 + 1, sqrt(x) + x, sin(x) + 2, exp(x)]); a, b = rng.choice([(0, 2), (1, 3), (0, 1), (2, 5)])
        dxs = f"\\frac{{{b - a}}}{{n}}"
        opts = [(f"$\\displaystyle\\lim_{{n \\to \\infty}} \\sum_{{i=1}}^{{n}} f\\!\\left({a} + \\frac{{{b-a}i}}{{n}}\\right)\\frac{{{b-a}}}{{n}}$", 'ok'),
                (f"$\\displaystyle\\sum_{{i=1}}^{{n}} f\\!\\left({a} + \\frac{{{b-a}i}}{{n}}\\right)\\frac{{{b-a}}}{{n}}$ for $n = 10$", 'finite'),
                (f"$\\displaystyle\\lim_{{n \\to \\infty}} \\sum_{{i=1}}^{{n}} f(i)\\,\\frac{{{b-a}}}{{n}}$", 'badpts'),
                (f"$\\displaystyle\\lim_{{n \\to \\infty}} \\sum_{{i=1}}^{{n}} f\\!\\left(\\frac{{i}}{{n}}\\right)$", 'nodx')]
        out.append(label_mc(S, f"Let $f(x) = {L(f)}$. Which expression gives the exact area under the graph of $f$ from $x = {a}$ to $x = {b}$?", opts, 'ok', rng, difficulty=2,
            hints=[f"With $n$ equal subintervals, $\\Delta x = {dxs}$ and the right endpoints are $x_i = {a} + i\\,\\Delta x$.", "The exact area is the limit of the Riemann sums as $n \\to \\infty$, and every term needs the factor $\\Delta x$."],
            solution=[f"$\\Delta x = {dxs}$, $x_i = {a} + \\frac{{{b-a}i}}{{n}}$, so $R_n = \\sum f(x_i)\\Delta x$.", "Area $= \\lim_{n \\to \\infty} R_n$; the other options either stop at a finite $n$, use the wrong sample points, or omit $\\Delta x$."]))

    # exact area via known sums for x^2 on [0,b]
    for _ in range(3):
        b = rng.choice([1, 2, 3, 4, 5]); f = x**2
        out.append(definite_problem(S, f, 0, b, difficulty=3,
            stmt=f"Use the limit of right-endpoint Riemann sums to find the exact area under $y = x^2$ from $x = 0$ to $x = {b}$.",
            hints=[f"$R_n = \\sum_{{i=1}}^n \\left(\\frac{{{b}i}}{{n}}\\right)^2 \\frac{{{b}}}{{n}} = \\frac{{{b**3}}}{{n^3}} \\sum_{{i=1}}^n i^2$.", "Use $\\sum_{i=1}^n i^2 = \\frac{n(n+1)(2n+1)}{6}$ and let $n \\to \\infty$."],
            solution=[f"$R_n = \\dfrac{{{b**3}}}{{n^3}} \\cdot \\dfrac{{n(n+1)(2n+1)}}{{6}} = \\dfrac{{{b**3}}}{{6}} \\cdot \\dfrac{{(n+1)(2n+1)}}{{n^2}}$.", f"As $n \\to \\infty$, $\\dfrac{{(n+1)(2n+1)}}{{n^2}} \\to 2$, so the area is $\\dfrac{{{b**3}}}{{3}} = {N(sp.Rational(b**3, 3))}$."]))
    return out


# ======================================================================
# 5.2 definite-integral
# ======================================================================

def definite_integral():
    S = 'definite-integral'
    rng = seeded(S)
    out = []

    # geometry: lines, constants, semicircles, absolute values
    for _ in range(14):
        form = rng.choice(['const', 'line', 'line', 'semicircle', 'abs', 'quarter', 'line_neg'])
        if form == 'const':
            c = nz(rng, -5, 6); a, b = rng.choice([(0, 3), (-2, 2), (1, 5), (-1, 4)]); f = c + 0 * x
            why = f"The region is a rectangle of width ${b - a}$ and height $|{c}|$" + (" below the axis, so the integral is negative" if c < 0 else "")
        elif form == 'line':
            m, c = rng.randint(1, 3), rng.randint(0, 4); a, b = rng.choice([(0, 2), (0, 4), (1, 3), (0, 3)]); f = m * x + c
            why = f"The region under the line is a trapezoid with parallel sides $f({a}) = {f.subs(x, a)}$ and $f({b}) = {f.subs(x, b)}$ and width ${b - a}$"
        elif form == 'line_neg':
            m = rng.randint(1, 3); a, b = (-rng.randint(1, 3), rng.randint(1, 3)); f = m * x
            why = f"The line $y = {L(f)}$ makes a triangle below the axis on $[{a}, 0]$ (area ${N(sp.Rational(m * a * a, 2))}$, counted negative) and one above on $[0, {b}]$ (area ${N(sp.Rational(m * b * b, 2))}$)"
        elif form == 'semicircle':
            r = rng.choice([1, 2, 3, 4, 5]); a, b = -r, r; f = sqrt(r * r - x**2)
            why = f"$y = \\sqrt{{{r*r} - x^2}}$ is the upper half of the circle $x^2 + y^2 = {r*r}$, so the region is a semicircle of radius ${r}$"
        elif form == 'quarter':
            r = rng.choice([2, 3, 4, 6]); a, b = 0, r; f = sqrt(r * r - x**2)
            why = f"The region is a quarter of the disk $x^2 + y^2 \\le {r*r}$"
        else:
            c = rng.randint(-2, 2); a, b = c - rng.randint(1, 3), c + rng.randint(1, 3); f = sp.Abs(x - c)
            why = f"The graph of $|x - ({c})|$ is a V with vertex at $x = {c}$; the region is two triangles with bases ${c - a}$ and ${b - c}$ and heights ${c - a}$ and ${b - c}$"
        val = sp.integrate(f, (x, a, b)) if form != 'abs' else sp.Rational((c - a)**2 + (b - c)**2, 2)
        out.append(definite_problem(S, f, a, b, difficulty=1 if form in ('const', 'line') else 2, value=val,
            stmt=f"Evaluate ${int_ltx(f, a, b)}$ by interpreting it in terms of areas.",
            hints=["Sketch the graph on the interval and identify the geometric shape (rectangle, triangle, trapezoid, part of a circle).", "Area above the axis counts positive, area below counts negative."],
            solution=[f"{why}.", f"Its (signed) area is ${L(val)}$, so the integral equals ${L(val)}$."]))

    # properties of integrals
    for _ in range(10):
        A, B = nz(rng, -6, 8), nz(rng, -5, 7); a, b, c = sorted(rng.sample(range(0, 8), 3))
        form = rng.choice(['lin_comb', 'reverse', 'split', 'split2', 'const_plus', 'zero'])
        if form == 'lin_comb':
            p_, q_ = nz(rng, -3, 4), nz(rng, -3, 4)
            stmt = f"If $\\displaystyle\\int_{{{a}}}^{{{b}}} f(x)\\,dx = {A}$ and $\\displaystyle\\int_{{{a}}}^{{{b}}} g(x)\\,dx = {B}$, find $\\displaystyle\\int_{{{a}}}^{{{b}}} \\left[{coef(p_, 'f(x)')} {'+' if q_ > 0 else '-'} {coef(abs(q_), 'g(x)')}\\right]dx$."
            vs = f'{p_}*({A}) + ({q_})*({B})'; rule = "the integral of a sum is the sum of the integrals, and constants factor out"
        elif form == 'reverse':
            stmt = f"If $\\displaystyle\\int_{{{a}}}^{{{b}}} f(x)\\,dx = {A}$, find $\\displaystyle\\int_{{{b}}}^{{{a}}} f(x)\\,dx$."
            vs = f'-({A})'; rule = "swapping the limits of integration changes the sign"
        elif form == 'split':
            stmt = f"If $\\displaystyle\\int_{{{a}}}^{{{c}}} f(x)\\,dx = {A}$ and $\\displaystyle\\int_{{{a}}}^{{{b}}} f(x)\\,dx = {B}$, find $\\displaystyle\\int_{{{b}}}^{{{c}}} f(x)\\,dx$."
            vs = f'({A}) - ({B})'; rule = f"$\\int_{{{a}}}^{{{c}}} = \\int_{{{a}}}^{{{b}}} + \\int_{{{b}}}^{{{c}}}$"
        elif form == 'split2':
            stmt = f"If $\\displaystyle\\int_{{{a}}}^{{{b}}} f(x)\\,dx = {A}$ and $\\displaystyle\\int_{{{b}}}^{{{c}}} f(x)\\,dx = {B}$, find $\\displaystyle\\int_{{{a}}}^{{{c}}} f(x)\\,dx$."
            vs = f'({A}) + ({B})'; rule = "adjacent intervals add"
        elif form == 'const_plus':
            kk = nz(rng, -4, 5)
            stmt = f"If $\\displaystyle\\int_{{{a}}}^{{{b}}} f(x)\\,dx = {A}$, find $\\displaystyle\\int_{{{a}}}^{{{b}}} \\left[f(x) {signed(kk)}\\right]dx$."
            vs = f'({A}) + ({kk})*({b} - {a})'; rule = f"$\\int_{{{a}}}^{{{b}}} {kk}\\,dx = {kk}({b} - {a})$ (a constant integrates to constant times length)"
        else:
            stmt = f"If $\\displaystyle\\int_{{{a}}}^{{{b}}} f(x)\\,dx = {A}$, find $\\displaystyle\\int_{{{a}}}^{{{b}}} f(x)\\,dx - \\int_{{{a}}}^{{{a}}} f(x)\\,dx + \\int_{{{b}}}^{{{a}}} f(x)\\,dx$."
            vs = '0'; rule = "$\\int_a^a f = 0$ and $\\int_b^a f = -\\int_a^b f$"
        val = sp.sympify(vs)
        out.append(numeric_problem(S, stmt, val, difficulty=1 if form in ('reverse', 'lin_comb') else 2,
            hints=["Use the properties of definite integrals rather than trying to find $f$.", f"Here: {rule}."],
            solution=[f"By the property that {rule}, the integral equals ${vs.replace('*', ' \\cdot ')}$.", f"$= {N(val)}$."],
            verify={'kind': 'numeric', 'value': vs}))

    # midpoint rule
    for _ in range(7):
        f = rng.choice([x**2 + 1, 1 / x, sqrt(x), x**3, 4 - x**2, 1 / (1 + x**2)]); a, b, n_ = rng.choice([(0, 2, 4), (1, 3, 4), (0, 4, 4), (1, 5, 4), (0, 1, 5), (2, 4, 4)])
        if f == 1 / x and a == 0:
            a, b = 1, 3
        dx = sp.Rational(b - a, n_); mids = [a + (j + sp.Rational(1, 2)) * dx for j in range(n_)]
        val = sum(f.subs(x, m) for m in mids) * dx
        if not sp.nsimplify(val).is_rational:
            continue
        out.append(numeric_problem(S, f"Use the Midpoint Rule with $n = {n_}$ to approximate ${int_ltx(f, a, b)}$. Give the exact value of the approximation $M_{{{n_}}}$.", val, difficulty=3 if (n_ > 4 or not f.is_polynomial(x)) else 2,
            hints=[f"$\\Delta x = {N(dx)}$; the midpoints are ${', '.join(N(m) for m in mids)}$.", "$M_n = \\Delta x\\,[f(\\bar x_1) + \\dots + f(\\bar x_n)]$."],
            solution=[f"Heights at the midpoints: ${' + '.join(N(f.subs(x, m)) for m in mids)} = {N(val / dx)}$.", f"$M_{{{n_}}} = {N(dx)} \\cdot {N(val / dx)} = {N(val)}$."],
            verify={'kind': 'riemann', 'expr': str(f), 'a': a, 'b': b, 'n': n_, 'method': 'mid'}))

    # Riemann sum with right endpoints for a definite integral
    for _ in range(5):
        f = rng.choice([x**2 - x, 2 * x + 1, x**3, 6 - x]); a, b, n_ = rng.choice([(0, 2, 4), (0, 3, 6), (1, 3, 4), (0, 4, 8)])
        dx = sp.Rational(b - a, n_); pts = [a + (j + 1) * dx for j in range(n_)]
        val = sum(f.subs(x, c) for c in pts) * dx
        out.append(numeric_problem(S, f"Compute the Riemann sum $R_{{{n_}}}$ for ${int_ltx(f, a, b)}$ using ${n_}$ equal subintervals and right endpoints.", val, difficulty=2,
            hints=[f"$\\Delta x = {N(dx)}$ and $x_i = {a} + i\\,\\Delta x$.", "Add $f(x_i)\\Delta x$ for $i = 1, \\dots, n$; negative values of $f$ contribute negatively."],
            solution=[f"$R_{{{n_}}} = {N(dx)}\\left[{' + '.join('(' + N(f.subs(x, c)) + ')' for c in pts)}\\right]$.", f"$= {N(val)}$."],
            verify={'kind': 'riemann', 'expr': str(f), 'a': a, 'b': b, 'n': n_, 'method': 'right'}))

    # comparison property: bounds on an integral
    for _ in range(5):
        m_, M_ = sorted(rng.sample(range(-3, 8), 2)); a, b = rng.choice([(0, 4), (1, 3), (-2, 2), (0, 5)])
        lo, hi = m_ * (b - a), M_ * (b - a)
        out.append(interval_problem(S, f"Suppose ${m_} \\le f(x) \\le {M_}$ for all $x$ in $[{a}, {b}]$. Using the comparison properties of integrals, what interval must $\\displaystyle\\int_{{{a}}}^{{{b}}} f(x)\\,dx$ lie in? Answer as a closed interval $[\\text{{lower}}, \\text{{upper}}]$.", f"[{lo},{hi}]", f"Interval({lo}, {hi})", difficulty=2,
            hints=["If $m \\le f(x) \\le M$ on $[a, b]$ then $m(b - a) \\le \\int_a^b f \\le M(b - a)$.", f"The length of the interval is ${b - a}$."],
            solution=[f"Lower bound: ${m_}({b} - ({a})) = {lo}$; upper bound: ${M_}({b} - ({a})) = {hi}$.", f"So the integral lies in $[{lo}, {hi}]$."]))

    # limit of a Riemann sum as a definite integral (conceptual)
    for _ in range(4):
        f = rng.choice([x**2, sqrt(x), 1 / x, sin(x)]); a, b = rng.choice([(0, 2), (1, 4), (1, 3), (0, 3)])
        if f == 1 / x and a == 0:
            a = 1
        opts = [(f"$\\displaystyle\\int_{{{a}}}^{{{b}}} {L(f)}\\,dx$", 'ok'), (f"$\\displaystyle\\int_{{0}}^{{{b - a}}} {L(f)}\\,dx$", 'w1'), (f"$\\displaystyle\\int_{{{a}}}^{{{b}}} {L(f.subs(x, x + a))}\\,dx$" if a != 0 else f"$\\displaystyle\\int_{{{a}}}^{{{b}}} {L(f.subs(x, 2*x))}\\,dx$", 'w2'), (f"$\\displaystyle\\int_{{1}}^{{n}} {L(f)}\\,dx$", 'w3')]
        out.append(label_mc(S, f"Express $\\displaystyle\\lim_{{n \\to \\infty}} \\sum_{{i=1}}^{{n}} {L(f).replace('x', '{x_i}')}\\,\\Delta x$, where $\\Delta x = \\frac{{{b - a}}}{{n}}$ and $x_i = {a} + i\\,\\Delta x$, as a definite integral.", opts, 'ok', rng, difficulty=3,
            hints=["Read off $a$ from the formula for $x_i$ and $b$ from $a + n\\Delta x$.", "The summand $f(x_i)\\Delta x$ tells you the integrand."],
            solution=[f"$x_i = {a} + i\\Delta x$ runs from ${a}$ to ${a} + n\\Delta x = {b}$, and the summand is $f(x_i)\\Delta x$ with $f(x) = {L(f)}$.", f"By definition, the limit is $\\int_{{{a}}}^{{{b}}} {L(f)}\\,dx$."]))

    # net area of trig/polynomial with sign change, plus evaluation of x^2 via formula
    for _ in range(5):
        form = rng.choice(['sin', 'x2', 'cube_sym'])
        if form == 'sin':
            f = sin(x); a, b = 0, 2 * pi; why = "the area above the axis on $[0, \\pi]$ exactly cancels the area below on $[\\pi, 2\\pi]$"
        elif form == 'x2':
            b = rng.choice([1, 2, 3, 4]); f = x**2; a = 0; why = f"using the formula $\\int_0^b x^2\\,dx = b^3/3$ from the limit of Riemann sums"
        else:
            c = rng.choice([1, 2, 3]); f = x**3; a, b = -c, c; why = "the function is odd, so the negative area on $[-c, 0]$ cancels the positive area on $[0, c]$"
        out.append(definite_problem(S, f, a, b, difficulty=2,
            hints=["Think about the graph: where is it above and below the axis?", "A definite integral is a net (signed) area."],
            solution=[f"Here {why}.", f"So ${int_ltx(f, a, b)} = {L(sp.integrate(f, (x, a, b)))}$."]))

    # conceptual
    concept = [
        ("The definite integral $\\displaystyle\\int_a^b f(x)\\,dx$ is defined as", [("$\\displaystyle\\lim_{n \\to \\infty} \\sum_{i=1}^{n} f(x_i^*)\\,\\Delta x$, a limit of Riemann sums", 'ok'), ("$f(b) - f(a)$", 'diff'), ("the average of $f(a)$ and $f(b)$ times $b - a$", 'trap'), ("$\\sum_{i=1}^{n} f(x_i)$ for a fixed $n$", 'finite')], 'ok',
         ["Riemann sums approximate; the integral is their limit.", "Any sample points $x_i^*$ in the subintervals may be used."],
         ["$\\int_a^b f(x)\\,dx = \\lim_{n\\to\\infty}\\sum f(x_i^*)\\Delta x$ with $\\Delta x = (b-a)/n$.", "The value $f(b) - f(a)$ is not the integral (though $F(b) - F(a)$ for an antiderivative $F$ will be, by the FTC)."]),
        ("If $f(x) \\le 0$ for all $x$ in $[a, b]$, then $\\displaystyle\\int_a^b f(x)\\,dx$ is", [("the negative of the area between the graph and the $x$-axis", 'ok'), ("the area between the graph and the $x$-axis", 'pos'), ("always zero", 'zero'), ("undefined", 'undef')], 'ok',
         ["Each term $f(x_i^*)\\Delta x$ in the Riemann sum is negative or zero.", "Integrals measure signed area."],
         ["All Riemann sums are $\\le 0$, so the integral is $\\le 0$.", "Its absolute value is the area of the region below the axis."]),
        ("Which property of definite integrals is correct?", [("$\\displaystyle\\int_a^b [f(x) + g(x)]\\,dx = \\int_a^b f(x)\\,dx + \\int_a^b g(x)\\,dx$", 'ok'), ("$\\displaystyle\\int_a^b f(x)g(x)\\,dx = \\int_a^b f(x)\\,dx \\cdot \\int_a^b g(x)\\,dx$", 'prod'), ("$\\displaystyle\\int_a^b \\frac{f(x)}{g(x)}\\,dx = \\frac{\\int_a^b f(x)\\,dx}{\\int_a^b g(x)\\,dx}$", 'quot'), ("$\\displaystyle\\int_a^b [f(x)]^2\\,dx = \\left[\\int_a^b f(x)\\,dx\\right]^2$", 'sq')], 'ok',
         ["Integration is linear: it respects sums and constant multiples.", "Test the others with $f = g = 1$ on $[0, 2]$."],
         ["Sums pass through the integral because they pass through each Riemann sum.", "Products, quotients and powers do not: e.g. $\\int_0^2 1\\cdot 1\\,dx = 2$ but $\\int_0^2 1\\,dx \\cdot \\int_0^2 1\\,dx = 4$."]),
    ]
    for stmt, opts, lab, hints, sol in concept:
        out.append(label_mc(S, stmt, opts, lab, rng, difficulty=1, hints=hints, solution=sol))
    return out


# ======================================================================
# 5.3 ftc
# ======================================================================

def ftc():
    S = 'ftc'
    rng = seeded(S)
    out = []
    integrands = [lambda: sqrt(1 + t**rng.choice([2, 3])), lambda: sin(t**2), lambda: exp(-t**2), lambda: t**2 + rng.randint(1, 4), lambda: cos(t) / (t + rng.randint(2, 4)), lambda: log(1 + t**2), lambda: 1 / (1 + t**rng.choice([2, 4])), lambda: exp(t) / t]

    # FTC1: d/dx of integral with upper limit x
    for _ in range(8):
        f = pick(rng, integrands)(); a = rng.choice([0, 1, 2]) if not f.has(1 / t) else 1
        g = sp.Integral(f, (t, a, x)); d = f.subs(t, x)
        out.append(equiv_problem(S, f"Let $g(x) = \\displaystyle\\int_{{{a}}}^{{x}} {L(f)}\\,dt$. Find $g'(x)$.", d, difficulty=1, domain=(0.5, 2),
            hints=["Part 1 of the Fundamental Theorem: if $g(x) = \\int_a^x f(t)\\,dt$ then $g'(x) = f(x)$.", "Just replace $t$ by $x$ in the integrand; the lower limit does not matter."],
            solution=["By FTC1 the derivative of $\\int_a^x f(t)\\,dt$ is $f(x)$.", f"$g'(x) = {L(d)}$."],
            verify={'kind': 'derivative', 'expr': str(g)}))

    # upper limit a function of x
    for _ in range(12):
        f = pick(rng, integrands)(); a = rng.choice([0, 1, 2]) if not f.has(1 / t) else 1
        upper = rng.choice([x**2, x**3, 2 * x, sqrt(x), exp(x), sin(x), 3 * x + 1])
        if f.has(1 / t) and upper in (sin(x),):
            upper = x**2
        g = sp.Integral(f, (t, a, upper)); d = sp.diff(g, x)
        dom = (0.5, 1.5)
        out.append(equiv_problem(S, f"Find $\\dfrac{{d}}{{dx}}\\displaystyle\\int_{{{a}}}^{{{L(upper)}}} {L(f)}\\,dt$.", d, difficulty=2, domain=dom,
            hints=["The upper limit is a function $u(x)$, so combine FTC1 with the chain rule: $\\frac{d}{dx}\\int_a^{u(x)} f(t)\\,dt = f(u(x))\\,u'(x)$.", f"Here $u = {L(upper)}$ and $u' = {L(sp.diff(upper, x))}$."],
            solution=[f"Replace $t$ by $u = {L(upper)}$ in the integrand and multiply by $u' = {L(sp.diff(upper, x))}$.", f"$= {L(d)}$."],
            verify={'kind': 'derivative', 'expr': str(g)}))

    # lower limit variable or both limits variable
    for _ in range(7):
        f = pick(rng, integrands)()
        form = rng.choice(['lower', 'both'])
        if form == 'lower':
            b = rng.choice([3, 5, 10]); g = sp.Integral(f, (t, x, b)); d = sp.diff(g, x)
            stmt = f"Find $\\dfrac{{d}}{{dx}}\\displaystyle\\int_{{x}}^{{{b}}} {L(f)}\\,dt$."
            hints = ["Swap the limits (which changes the sign) so that the variable is the upper limit.", "Then apply FTC1."]
            sol = [f"$\\int_x^{{{b}}} f(t)\\,dt = -\\int_{{{b}}}^{{x}} f(t)\\,dt$.", f"Differentiating gives $-f(x) = {L(d)}$."]
        else:
            lo, hi = rng.choice([(x, 2 * x), (x, x**2), (2 * x, x**3), (sqrt(x), x), (x**2, x**3)]); g = sp.Integral(f, (t, lo, hi)); d = sp.diff(g, x)
            stmt = f"Find $\\dfrac{{d}}{{dx}}\\displaystyle\\int_{{{L(lo)}}}^{{{L(hi)}}} {L(f)}\\,dt$."
            hints = ["Split at a constant: $\\int_{u}^{v} = \\int_{c}^{v} - \\int_{c}^{u}$.", "Apply FTC1 with the chain rule to each piece: $f(v)\\,v' - f(u)\\,u'$."]
            sol = [f"$\\dfrac{{d}}{{dx}}\\int_{{{L(lo)}}}^{{{L(hi)}}} f(t)\\,dt = f({L(hi)})\\cdot({L(sp.diff(hi, x))}) - f({L(lo)})\\cdot({L(sp.diff(lo, x))})$.", f"$= {L(d)}$."]
        out.append(equiv_problem(S, stmt, d, difficulty=3 if form == 'both' else 2, domain=(0.5, 1.5), hints=hints, solution=sol, verify={'kind': 'derivative', 'expr': str(g)}))

    # FTC2 evaluation
    for _ in range(18):
        form = rng.choice(['poly', 'poly', 'power', 'exp', 'trig', 'sec2', 'recip', 'sqrt'])
        if form == 'poly':
            f = sum(rng.randint(-3, 4) * x**j for j in range(rng.randint(2, 4))) + nz(rng, -3, 3) * x**rng.randint(1, 3); a, b = rng.choice([(0, 1), (0, 2), (1, 2), (-1, 1), (1, 3)])
        elif form == 'power':
            f = rng.randint(1, 4) * x**rng.choice([-2, -3]) + rng.randint(0, 2); a, b = rng.choice([(1, 2), (1, 3), (1, 4)])
        elif form == 'exp':
            f = rng.randint(1, 3) * exp(x) + rng.randint(-2, 3) * x; a, b = rng.choice([(0, 1), (0, 2), (0, log(2)), (log(2), log(4))])
        elif form == 'trig':
            f = rng.randint(1, 3) * cos(x) + rng.randint(-2, 2) * sin(x); a, b = rng.choice([(0, pi / 2), (0, pi), (pi / 6, pi / 2), (0, pi / 3)])
        elif form == 'sec2':
            f = rng.randint(1, 3) * sec(x)**2; a, b = rng.choice([(0, pi / 4), (0, pi / 3), (pi / 6, pi / 4)])
        elif form == 'recip':
            f = rng.randint(1, 4) / x + rng.randint(0, 2) * x; a, b = rng.choice([(1, E), (1, 2), (1, E**2), (2, 4)])
        else:
            f = rng.randint(1, 3) * sqrt(x) + rng.randint(0, 2); a, b = rng.choice([(0, 4), (1, 4), (0, 1), (4, 9)])
        F = sp.integrate(f, x)
        out.append(definite_problem(S, f, a, b, difficulty=1 if form == 'poly' else (3 if form in ('recip', 'sec2', 'trig') and a != 0 else 2),
            hints=["Part 2 of the Fundamental Theorem: $\\int_a^b f(x)\\,dx = F(b) - F(a)$ for any antiderivative $F$.", f"An antiderivative is $F(x) = {L(F)}$."],
            solution=[f"$F(x) = {L(F)}$.", f"$F({L(b)}) - F({L(a)}) = {L(sp.simplify(F.subs(x, b)))} - \\left({L(sp.simplify(F.subs(x, a)))}\\right) = {L(sp.simplify(sp.integrate(f, (x, a, b))))}$."]))

    # g(x) = integral: evaluate g at a point / find g'
    for _ in range(6):
        f = rng.choice([2 * t + 1, t**2, 3 - t, t**2 - 2 * t, 4 * t**3])
        a = 0; c = rng.randint(1, 3)
        which = rng.choice(['value', 'deriv_at'])
        if which == 'value':
            out.append(definite_problem(S, f, a, c, difficulty=2, variable='t',
                stmt=f"Let $g(x) = \\displaystyle\\int_{{0}}^{{x}} \\left({L(f)}\\right)dt$. Find $g({c})$.",
                hints=["$g(c)$ is just the definite integral from $0$ to $c$.", "Evaluate it with an antiderivative (FTC2)."],
                solution=[f"$g({c}) = \\int_0^{{{c}}} ({L(f)})\\,dt = \\left[{L(sp.integrate(f, t))}\\right]_0^{{{c}}}$.", f"$= {N(sp.integrate(f, (t, 0, c)))}$."]))
        else:
            val = f.subs(t, c)
            out.append(numeric_problem(S, f"Let $g(x) = \\displaystyle\\int_{{0}}^{{x}} \\left({L(f)}\\right)dt$. Find $g'({c})$.", val, difficulty=1,
                hints=["By FTC1, $g'(x)$ equals the integrand with $t$ replaced by $x$; no integration needed.", f"$g'(x) = {L(f.subs(t, x))}$."],
                solution=[f"$g'(x) = {L(f.subs(t, x))}$ by FTC1.", f"$g'({c}) = {N(val)}$."],
                verify={'kind': 'evaluate', 'expr': str(f.subs(t, x)), 'at': c}))

    # where g is increasing / concave (via FTC1)
    for _ in range(4):
        r = rng.choice([1, 2, 3]); f = t**2 - r * r
        out.append(interval_problem(S, f"Let $g(x) = \\displaystyle\\int_{{0}}^{{x}} \\left({L(f)}\\right)dt$. On which open interval of positive $x$-values... more precisely, on which open interval between the two zeros of $g'$ is $g$ decreasing? Answer in interval notation.".replace("On which open interval of positive $x$-values... more precisely, on", "On"), interval_str(-r, r, True, True), f'{str(f.subs(t, x))} < 0', difficulty=2,
            hints=["$g'(x) = f(x)$ by FTC1; $g$ decreases where $g' < 0$.", f"Solve $x^2 - {r*r} < 0$."],
            solution=[f"$g'(x) = x^2 - {r*r} = (x - {r})(x + {r})$.", f"This is negative exactly for $-{r} < x < {r}$, so $g$ is decreasing on $(-{r}, {r})$."]))

    # conceptual
    concept = [
        ("Part 1 of the Fundamental Theorem of Calculus says that if $f$ is continuous on $[a, b]$ and $g(x) = \\displaystyle\\int_a^x f(t)\\,dt$, then", [("$g'(x) = f(x)$", 'ok'), ("$g(x) = f(x) - f(a)$", 'w1'), ("$g'(x) = f(x) - f(a)$", 'w2'), ("$g(x) = f'(x)$", 'w3')], 'ok',
         ["The theorem links differentiation and integration as inverse processes.", "The derivative of the accumulated area is the height of the curve."],
         ["FTC1: $\\frac{d}{dx}\\int_a^x f(t)\\,dt = f(x)$.", "Accumulating $f$ and then differentiating returns $f$ itself."]),
        ("Part 2 of the Fundamental Theorem says $\\displaystyle\\int_a^b f(x)\\,dx = F(b) - F(a)$ provided that", [("$F$ is any antiderivative of $f$ (and $f$ is continuous)", 'ok'), ("$F$ is the derivative of $f$", 'deriv'), ("$F(a) = 0$", 'zero'), ("$F$ is the unique antiderivative with $F(0) = 0$", 'unique')], 'ok',
         ["Different antiderivatives differ by a constant.", "That constant cancels in $F(b) - F(a)$, so any antiderivative works."],
         ["If $F' = f$ then $\\int_a^b f = F(b) - F(a)$.", "Adding a constant to $F$ changes both $F(b)$ and $F(a)$ equally, so the difference is unaffected."]),
        ("What is wrong with the computation $\\displaystyle\\int_{-1}^{2} \\frac{1}{x^2}\\,dx = \\left[-\\frac{1}{x}\\right]_{-1}^{2} = -\\frac{3}{2}$?", [("the integrand is not continuous on $[-1, 2]$ (it blows up at $0$), so the FTC does not apply", 'ok'), ("the antiderivative is wrong", 'anti'), ("the limits were substituted in the wrong order", 'order'), ("nothing; the answer is correct", 'fine')], 'ok',
         ["A positive function cannot have a negative integral.", "Check the hypotheses of the theorem."],
         ["$1/x^2 > 0$ everywhere, so the integral cannot be negative; the FTC requires continuity on the whole interval.", "Since $1/x^2$ is unbounded near $0$, the integral is improper (and in fact divergent)."]),
    ]
    for stmt, opts, lab, hints, sol in concept:
        out.append(label_mc(S, stmt, opts, lab, rng, difficulty=1, hints=hints, solution=sol))
    return out


# ======================================================================
# 5.4 indefinite-integrals (and net change)
# ======================================================================

def indefinite_integrals():
    S = 'indefinite-integrals'
    rng = seeded(S)
    out = []

    # indefinite integrals: table-based
    for _ in range(14):
        form = rng.choice(['poly', 'power', 'exp_trig', 'sec', 'recip', 'inv_trig', 'csc'])
        a, b = nz(rng, -4, 5), nz(rng, -4, 4)
        if form == 'poly':
            f = sum(rng.randint(-4, 4) * x**j for j in range(rng.randint(1, 3))) + nz(rng, -3, 3) * x**rng.randint(2, 4); dom = (-2, 2); rule = "the power rule for integrals"
        elif form == 'power':
            f = a * x**rng.choice([sp.Rational(1, 2), sp.Rational(-1, 2), sp.Rational(3, 2), -3, sp.Rational(1, 3)]) + b; dom = (0.5, 3); rule = "$\\int x^n\\,dx = \\frac{x^{n+1}}{n+1} + C$ with a fractional or negative $n$"
        elif form == 'exp_trig':
            f = a * exp(x) + b * sin(x) if rng.random() < 0.5 else a * cos(x) - b * exp(x); dom = (-2, 2); rule = "$\\int e^x = e^x$, $\\int \\sin x = -\\cos x$, $\\int \\cos x = \\sin x$"
        elif form == 'sec':
            f = a * sec(x)**2 + b * sec(x) * tan(x) if rng.random() < 0.5 else a * sec(x) * tan(x) + b * x; dom = (-1, 1); rule = "$\\int \\sec^2 x = \\tan x$ and $\\int \\sec x\\tan x = \\sec x$"
        elif form == 'recip':
            f = a / x + b * x**2; dom = (0.5, 3); rule = "$\\int \\frac{1}{x}\\,dx = \\ln|x| + C$"
        elif form == 'inv_trig':
            f = a / (1 + x**2) + b / sqrt(1 - x**2) if rng.random() < 0.5 else a / (1 + x**2) - b * x; dom = (-0.8, 0.8); rule = "$\\int \\frac{dx}{1 + x^2} = \\arctan x$ and $\\int \\frac{dx}{\\sqrt{1 - x^2}} = \\arcsin x$"
        else:
            f = a * csc(x)**2 - b * csc(x) * cot(x); dom = (0.5, 2.5); rule = "$\\int \\csc^2 x = -\\cot x$ and $\\int \\csc x\\cot x = -\\csc x$"
        F = sp.integrate(f, x)
        out.append(indefinite_problem(S, f, F, difficulty=1 if form == 'poly' else 2, domain=dom,
            hints=["Integrate term by term using the table of indefinite integrals.", f"Use {rule} (plus $C$)."],
            solution=[f"Apply {rule} to each term.", f"${int_ltx(f)} = {L(F)} + C$."]))

    # rewrite then integrate
    for _ in range(9):
        form = rng.choice(['square', 'dist', 'div_root', 'div_x', 'trig_id'])
        if form == 'square':
            c = nz(rng, -3, 3); f0 = (x + c)**2 if rng.random() < 0.5 else (sqrt(x) + c)**2; f = sp.expand(f0); dom = (0.5, 3); how = "expand the square"
        elif form == 'dist':
            c = rng.randint(1, 4); f0 = x * (x**2 + c) if rng.random() < 0.5 else x**2 * (rng.randint(2, 4) - x); f = sp.expand(f0); dom = (-2, 2); how = "multiply out"
        elif form == 'div_root':
            c = rng.randint(1, 4); f0 = (x**2 + c) / sqrt(x); f = sp.expand(f0); dom = (0.5, 3); how = "divide each term by $\\sqrt{x} = x^{1/2}$"
        elif form == 'div_x':
            c = rng.randint(1, 5); f0 = (x**3 + c * x + rng.randint(1, 3)) / x**2; f = sp.expand(f0); dom = (0.5, 3); how = "divide each term by $x^2$"
        else:
            if rng.random() < 0.5:
                f0 = sin(x) / cos(x)**2; f = sec(x) * tan(x)
            else:
                f0 = (1 + cos(x)**2) / cos(x)**2; f = sec(x)**2 + 1
            dom = (-1, 1); how = "rewrite in terms of $\\sec x$ and $\\tan x$: $\\frac{\\sin x}{\\cos^2 x} = \\sec x\\tan x$, $\\frac{1}{\\cos^2 x} = \\sec^2 x$"
        F = sp.integrate(f, x)
        if form == 'trig_id':
            F = sec(x) if f == sec(x) * tan(x) else tan(x) + x
        out.append(indefinite_problem(S, f0, F, difficulty=2, domain=dom,
            hints=[f"There is no product or quotient rule for integrals; first {how}.", "Then integrate term by term."],
            solution=[f"Rewrite: ${L(f0)} = {pow_form(f) if form != 'trig_id' else L(f)}$.", f"Integrate: ${L(F)} + C$."]))

    # definite integrals via FTC
    for _ in range(9):
        form = rng.choice(['poly', 'root', 'trig', 'exp', 'recip'])
        if form == 'poly':
            f = rng.randint(1, 3) * x**2 - rng.randint(1, 4) * x + rng.randint(0, 3); a, b = rng.choice([(0, 2), (1, 3), (-1, 2), (0, 3)])
        elif form == 'root':
            f = sqrt(x) * rng.randint(1, 3) - x; a, b = rng.choice([(0, 4), (1, 4), (0, 9)])
        elif form == 'trig':
            f = rng.randint(1, 3) * sin(x) + rng.randint(0, 2); a, b = rng.choice([(0, pi), (0, pi / 2), (pi / 2, pi)])
        elif form == 'exp':
            f = exp(x) + rng.randint(1, 3) * x**2; a, b = rng.choice([(0, 1), (0, 2), (-1, 0)])
        else:
            f = rng.randint(1, 3) / x + rng.randint(1, 3); a, b = rng.choice([(1, 3), (1, E), (2, 8)])
        F = sp.integrate(f, x)
        out.append(definite_problem(S, f, a, b, difficulty=2,
            hints=["Find an antiderivative, then subtract its values at the endpoints.", f"$F(x) = {L(F)}$."],
            solution=[f"$\\left[{L(F)}\\right]_{{{L(a)}}}^{{{L(b)}}}$.", f"$= {L(sp.simplify(F.subs(x, b)))} - \\left({L(sp.simplify(F.subs(x, a)))}\\right) = {L(sp.simplify(sp.integrate(f, (x, a, b))))}$."]))

    # net change: displacement vs distance
    for _ in range(8):
        r1, r2 = sorted(rng.sample([1, 2, 3, 4], 2)); v = sp.expand((t - r1) * (t - r2)) * rng.choice([1, 1, 2]); a, b = 0, r2 + rng.choice([0, 1])
        which = rng.choice(['disp', 'dist'])
        if which == 'disp':
            out.append(definite_problem(S, v, a, b, difficulty=2, variable='t',
                stmt=f"A particle moves along a line with velocity $v(t) = {L(v)}$ (m/s). Find the displacement over the time interval $[{a}, {b}]$.",
                hints=["Displacement is the net change in position: $\\int_a^b v(t)\\,dt$.", "Negative velocity counts negatively; no need to split the integral."],
                solution=[f"Displacement $= \\int_{{{a}}}^{{{b}}} ({L(v)})\\,dt = \\left[{L(sp.integrate(v, t))}\\right]_{{{a}}}^{{{b}}}$.", f"$= {N(sp.integrate(v, (t, a, b)))}$ m."]))
        else:
            roots = [r for r in (r1, r2) if a < r < b]
            cuts = [a] + roots + [b]
            pieces = [sp.integrate(v, (t, cuts[j], cuts[j + 1])) for j in range(len(cuts) - 1)]
            total = sum(abs(p_) for p_ in pieces)
            vs = ' + '.join(f'Abs(integrate({str(v)}, (t, {cuts[j]}, {cuts[j+1]})))' for j in range(len(cuts) - 1))
            out.append(numeric_problem(S, f"A particle moves along a line with velocity $v(t) = {L(v)}$ (m/s). Find the total distance traveled during $[{a}, {b}]$.", total, difficulty=3,
                hints=["Distance is $\\int_a^b |v(t)|\\,dt$; find where $v$ changes sign and split the integral there.", f"$v(t) = 0$ at $t = {r1}$ and $t = {r2}$; $v$ is negative between them."],
                solution=[f"Split at the sign changes: the integrals over ${', '.join(f'[{cuts[j]}, {cuts[j+1]}]' for j in range(len(cuts) - 1))}$ equal ${', '.join(N(p_) for p_ in pieces)}$.", f"Distance $= {' + '.join(N(abs(p_)) for p_ in pieces)} = {N(total)}$ m."],
                verify={'kind': 'numeric', 'value': vs}))

    # net change word problems
    for _ in range(7):
        form = rng.choice(['water', 'pop', 'cost', 'oil'])
        if form == 'water':
            r = rng.randint(10, 30) - rng.randint(1, 3) * t; a, b = 0, rng.choice([2, 4, 5]); stmt = f"Water flows into a tank at a rate of $r(t) = {L(r)}$ liters per minute. How many liters enter the tank during the first ${b}$ minutes?"; unit = "liters"
        elif form == 'pop':
            r = rng.randint(2, 6) * t + rng.randint(10, 50); a, b = rng.choice([(0, 10), (0, 5), (2, 6)]); stmt = f"A population grows at a rate of $P'(t) = {L(r)}$ individuals per year. By how much does the population increase between $t = {a}$ and $t = {b}$ years?"; unit = "individuals"
        elif form == 'cost':
            r = sp.Rational(1, rng.choice([10, 20, 50])) * t**2 + rng.randint(2, 8); a, b = rng.choice([(0, 10), (10, 20), (0, 20)]); stmt = f"The marginal cost of producing $t$ units is $C'(t) = {L(r)}$ dollars per unit. Find the cost of increasing production from ${a}$ to ${b}$ units."; unit = "dollars"
        else:
            r = rng.randint(50, 100) - rng.randint(2, 8) * t; a, b = rng.choice([(0, 4), (0, 6), (1, 5)]); stmt = f"Oil leaks from a tank at a rate of $r(t) = {L(r)}$ liters per hour. How much oil leaks out between $t = {a}$ and $t = {b}$ hours?"; unit = "liters"
        out.append(definite_problem(S, r, a, b, difficulty=2, variable='t', stmt=stmt,
            hints=["The Net Change Theorem: the integral of a rate of change over $[a, b]$ is the net change over that interval.", f"Compute $\\int_{{{a}}}^{{{b}}} ({L(r)})\\,dt$."],
            solution=[f"Net change $= \\int_{{{a}}}^{{{b}}} ({L(r)})\\,dt = \\left[{L(sp.integrate(r, t))}\\right]_{{{a}}}^{{{b}}}$.", f"$= {N(sp.integrate(r, (t, a, b)))}$ {unit}."]))

    # conceptual
    concept = [
        ("What is the difference between $\\displaystyle\\int f(x)\\,dx$ and $\\displaystyle\\int_a^b f(x)\\,dx$?", [("the first is a family of functions (antiderivatives); the second is a number", 'ok'), ("they are the same thing", 'same'), ("the first is a number; the second is a function", 'swap'), ("the first only exists when $f$ is a polynomial", 'poly')], 'ok',
         ["An indefinite integral has a $+C$; a definite integral has limits.", "Think about what kind of object each one is."],
         ["$\\int f(x)\\,dx = F(x) + C$ is the general antiderivative, a family of functions.", "$\\int_a^b f(x)\\,dx = F(b) - F(a)$ is a specific number (a net area)."]),
        ("The Net Change Theorem states that $\\displaystyle\\int_a^b F'(x)\\,dx$ equals", [("$F(b) - F(a)$, the net change in $F$ over $[a, b]$", 'ok'), ("$F'(b) - F'(a)$", 'w1'), ("the total distance traveled", 'w2'), ("$F(b) + F(a)$", 'w3')], 'ok',
         ["It is FTC2 applied to a rate of change.", "Integrating a rate gives the accumulated change."],
         ["Since $F$ is an antiderivative of $F'$, FTC2 gives $\\int_a^b F'(x)\\,dx = F(b) - F(a)$.", "Interpreting $F'$ as a rate, this is the net change in the quantity $F$."]),
        ("If $v(t)$ is the velocity of a particle, the total distance traveled over $[a, b]$ is", [("$\\displaystyle\\int_a^b |v(t)|\\,dt$", 'ok'), ("$\\displaystyle\\int_a^b v(t)\\,dt$", 'disp'), ("$v(b) - v(a)$", 'dv'), ("$\\displaystyle\\left|\\int_a^b v(t)\\,dt\\right|$", 'absdisp')], 'ok',
         ["Displacement can be smaller than distance when the particle turns around.", "Speed is $|v|$."],
         ["Distance accumulates speed $|v(t)|$, so distance $= \\int_a^b |v(t)|\\,dt$.", "$\\int_a^b v(t)\\,dt$ is the displacement, which can cancel out back-and-forth motion."]),
    ]
    for stmt, opts, lab, hints, sol in concept:
        out.append(label_mc(S, stmt, opts, lab, rng, difficulty=1, hints=hints, solution=sol))
    return out


def build() -> dict:
    return {
        'antiderivatives': tidy(antiderivatives()),
        'areas-and-distances': tidy(areas_and_distances()),
        'definite-integral': tidy(definite_integral()),
        'ftc': tidy(ftc()),
        'indefinite-integrals': tidy(indefinite_integrals()),
    }
