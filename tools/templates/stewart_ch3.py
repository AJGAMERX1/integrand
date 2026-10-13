"""Stewart Chapter 3 templates (original problems, SymPy-verified):
power-exp-derivatives (3.1), product-quotient-rules (3.2), trig-derivatives (3.3), chain-rule (3.4),
implicit-differentiation (3.5, incl. inverse trig derivatives), log-derivatives (3.6).
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
                     label_mc, numeric_problem, equiv_problem, interval_problem, interval_str, interval_ltx, h, y, tidy, pow_form)

sin, cos, tan, sec, csc, cot, exp, log, sqrt, pi, E = sp.sin, sp.cos, sp.tan, sp.sec, sp.csc, sp.cot, sp.exp, sp.log, sp.sqrt, sp.pi, sp.E


def deriv_problem(S, f, *, difficulty, hints, solution, domain=(-3, 3), stmt=None, variable='x'):
    d = sp.diff(f, sp.Symbol(variable))
    statement = stmt or f"Find the derivative of $f(x) = {L(f)}$."
    return equiv_problem(S, statement, d, difficulty=difficulty, hints=hints, solution=solution, domain=domain,
                         variable=variable, verify={'kind': 'derivative', 'expr': str(f)})


def deriv_mc(S, f, rng, *, difficulty, hints, solution, distractors, stmt=None):
    """Multiple choice: pick the correct derivative among expression distractors (verified by kind 'choice')."""
    d = sp.diff(f, x)
    opts = [(f'${L(d)}$', P(d))] + [(f'${L(w)}$', P(w)) for w in distractors if sp.simplify(w - d) != 0][:3]
    statement = stmt or f"Which expression is the derivative of $f(x) = {L(f)}$?"
    return mc(S, statement, opts, 0, rng, difficulty=difficulty, hints=hints, solution=solution,
              verify={'kind': 'choice', 'expected': str(d)})


# ======================================================================
# 3.1 power-exp-derivatives
# ======================================================================

def power_exp_derivatives():
    S = 'power-exp-derivatives'
    rng = seeded(S)
    out = []

    # polynomials
    for _ in range(9):
        dg = rng.choice([2, 3, 3, 4, 5])
        f = sum(rng.randint(-6, 6) * x**i for i in range(dg)) + nz(rng, -5, 5) * x**dg
        out.append(deriv_problem(S, f, difficulty=1,
            hints=["Differentiate term by term: the derivative of $cx^n$ is $cnx^{n-1}$.", "The derivative of a constant is $0$, and $x$ alone has derivative $1$."],
            solution=[f"Apply the power rule to each term of ${L(f)}$.", f"$f'(x) = {L(sp.diff(f, x))}$."]))

    # negative and fractional powers (rewrite first)
    for _ in range(10):
        form = rng.choice(['recip', 'sqrt', 'root3', 'frac', 'mix'])
        a = nz(rng, -6, 6); b = rng.randint(1, 5)
        if form == 'recip':
            n_ = rng.choice([1, 2, 3, 4]); f = a / x**n_ + b * x; dom = (0.5, 3)
            rewrite = f"{L(a / x**n_)} = {a}x^{{-{n_}}}"
        elif form == 'sqrt':
            f = a * sqrt(x) + b; dom = (0.5, 4); rewrite = f"\\sqrt{{x}} = x^{{1/2}}"
        elif form == 'root3':
            f = a * sp.cbrt(x) - b * x**2; dom = (0.5, 4); rewrite = f"\\sqrt[3]{{x}} = x^{{1/3}}"
        elif form == 'frac':
            pq = rng.choice([sp.Rational(3, 2), sp.Rational(5, 2), sp.Rational(2, 3), sp.Rational(-1, 2), sp.Rational(4, 3)]); f = a * x**pq; dom = (0.5, 4)
            rewrite = f"the power rule works for any real exponent: $(x^{{{N(pq)}}})' = {N(pq)}x^{{{N(pq - 1)}}}$"
        else:
            f = b / sqrt(x) + a * x**2; dom = (0.5, 4); rewrite = f"\\dfrac{{1}}{{\\sqrt{{x}}}} = x^{{-1/2}}"
        out.append(deriv_problem(S, f, difficulty=2, domain=dom,
            hints=["Rewrite roots and reciprocals as powers of $x$ before differentiating.", f"Use ${rewrite}$." if form != 'frac' else f"Here {rewrite}."],
            solution=[f"Rewrite: $f(x) = {pow_form(f)}$ with every term as a power of $x$.", f"Power rule on each term: $f'(x) = {pow_form(sp.diff(f, x))}$, i.e. ${L(sp.diff(f, x))}$."]))

    # with e^x
    for _ in range(8):
        a = nz(rng, -4, 4); b = nz(rng, -5, 5); n_ = rng.randint(2, 4)
        f = rng.choice([a * exp(x) + b * x**n_, a * exp(x) - b * x + rng.randint(1, 5), b * x**n_ - a * exp(x) + rng.randint(1, 3) * x, a * exp(x) + b * sqrt(x)])
        dom = (0.5, 3) if f.has(sqrt(x)) else (-2, 2)
        out.append(deriv_problem(S, f, difficulty=1, domain=dom,
            hints=["$e^x$ is its own derivative.", "Handle the power terms with the power rule."],
            solution=[f"$\\dfrac{{d}}{{dx}}(e^x) = e^x$ and the remaining terms follow the power rule.", f"$f'(x) = {L(sp.diff(f, x))}$."]))

    # expand or split before differentiating
    for _ in range(7):
        if rng.random() < 0.5:
            f0 = (x**2 + rng.randint(-3, 3)) * (rng.randint(1, 3) * x - rng.randint(1, 4)); f = sp.expand(f0)
            stmt = f"Find the derivative of $f(x) = {L(f0)}$ by first expanding the product."
            hints = ["Multiply out the factors to get a polynomial.", "Then differentiate term by term."]
            sol = [f"Expanding: $f(x) = {L(f)}$.", f"$f'(x) = {L(sp.diff(f, x))}$."]
            dom = (-3, 3)
        else:
            num = rng.randint(1, 3) * x**3 + rng.randint(-5, 5) * x**2 + nz(rng, -4, 4); f0 = num / x**rng.choice([1, 2]); f = sp.expand(f0)
            stmt = f"Find the derivative of $f(x) = {L(f0)}$ by first dividing each term of the numerator by the denominator."
            hints = ["Split the fraction into separate terms, each a power of $x$.", "Negative exponents are fine: $x^{-n}$ differentiates to $-nx^{-n-1}$."]
            sol = [f"Divide: $f(x) = {pow_form(f)}$.", f"$f'(x) = {pow_form(sp.diff(f, x))} = {L(sp.diff(f, x))}$."]
            dom = (0.5, 3)
        out.append(deriv_problem(S, f, difficulty=3 if dom[0] > 0 else 2, domain=dom, stmt=stmt, hints=hints, solution=sol))

    # tangent line
    for _ in range(7):
        f = rng.choice([x**3 - rng.randint(1, 4) * x, rng.randint(1, 3) * x**2 + rng.randint(-4, 4), exp(x) + rng.randint(-2, 2) * x, sqrt(x) + rng.randint(1, 3), x**4 - rng.randint(1, 3) * x**2])
        a = rng.choice([1, 4]) if f.has(sqrt(x)) else (0 if f.has(exp(x)) else rng.randint(-2, 2))
        d = sp.diff(f, x); m = d.subs(x, a); fa = f.subs(x, a); line = sp.expand(fa + m * (x - a))
        out.append(equiv_problem(S, f"Find an equation of the tangent line to $y = {L(f)}$ at the point where $x = {a}$.", line, difficulty=2, domain=(-2, 2),
            hints=[f"Differentiate to get the slope function, then evaluate at $x = {a}$.", "Use point-slope form with the point on the curve."],
            solution=[f"$f'(x) = {L(d)}$, so the slope is $f'({a}) = {N(m)}$; the point is $({a}, {N(fa)})$.", f"$y = {N(fa)} + {N(m)}(x - {a}) = {L(line)}$."],
            verify={'kind': 'tangent', 'expr': str(f), 'at': a}))

    # horizontal tangents
    for _ in range(6):
        if rng.random() < 0.5:
            r = rng.randint(-3, 3); f = sp.expand(x**2 - 2 * r * x + rng.randint(-4, 4))
            out.append(numeric_problem(S, f"At what value of $x$ does the graph of $f(x) = {L(f)}$ have a horizontal tangent line?", r, difficulty=1,
                hints=["A horizontal tangent has slope $0$: solve $f'(x) = 0$.", f"$f'(x) = {L(sp.diff(f, x))}$."],
                solution=[f"$f'(x) = {L(sp.diff(f, x))} = 0$.", f"So $x = {r}$."],
                verify={'kind': 'solve', 'lhs': str(sp.diff(f, x)), 'rhs': 0}))
        else:
            r1, r2 = sorted(rng.sample([-3, -2, -1, 0, 1, 2, 3], 2)); d = 3 * sp.expand((x - r1) * (x - r2)); f = sp.integrate(d, x) + rng.randint(-2, 2)
            wrong = [(f"$x = {-r1}, {-r2}$" if {-r1, -r2} != {r1, r2} else f"$x = {r1+1}, {r2+1}$", 'w1'), (f"$x = {r1}$ only", 'w2'), (f"$x = {r1*r2}$", 'w3') if r1 * r2 not in (r1, r2) else (f"$x = {r1 + r2 + 5}$", 'w3')]
            out.append(label_mc(S, f"For which values of $x$ does $f(x) = {L(f)}$ have a horizontal tangent?", [(f"$x = {r1}, {r2}$", 'ok')] + wrong, 'ok', rng, difficulty=2,
                hints=["Set the derivative equal to zero.", f"$f'(x) = {L(d)}$ factors as $3(x {signed(-r1)})(x {signed(-r2)})$."],
                solution=[f"$f'(x) = {L(d)} = 3(x {signed(-r1)})(x {signed(-r2)})$.", f"$f'(x) = 0$ at $x = {r1}$ and $x = {r2}$."]))

    # slope at a point, normal line
    for _ in range(6):
        f = rng.choice([x**3 + rng.randint(-3, 3) * x**2, rng.randint(2, 4) * exp(x) - x, x**2 - rng.randint(1, 5) / x, sqrt(x) * rng.randint(2, 6)])
        a = rng.choice([1, 4]) if f.has(sqrt(x)) else (0 if f.has(exp(x)) else rng.choice([1, 2, -1]))
        d = sp.diff(f, x); m = d.subs(x, a)
        if rng.random() < 0.6 or m == 0:
            out.append(numeric_problem(S, f"Find the slope of the tangent line to $y = {L(f)}$ at $x = {a}$.", m, difficulty=1,
                hints=["Differentiate first, then substitute.", f"$f'(x) = {L(d)}$."],
                solution=[f"$f'(x) = {L(d)}$.", f"$f'({a}) = {N(m)}$."],
                verify={'kind': 'evaluate', 'expr': str(d), 'at': a}))
        else:
            fa = f.subs(x, a); nline = sp.expand(fa - (x - a) / m)
            out.append(equiv_problem(S, f"Find an equation of the normal line (perpendicular to the tangent) to $y = {L(f)}$ at $x = {a}$.", nline, difficulty=3, domain=(-2, 2),
                hints=["The normal line's slope is the negative reciprocal of the tangent slope.", f"Tangent slope: $f'({a}) = {N(m)}$."],
                solution=[f"$f'({a}) = {N(m)}$, so the normal slope is ${N(-1/m)}$; the point is $({a}, {N(fa)})$.", f"$y = {N(fa)} {N(-1/m) if -1/m < 0 else '+ ' + N(-1/m)}(x - {a})$, i.e. $y = {L(nline)}$."],
                verify={'kind': 'equiv', 'expected': f'({fa}) - (x - {a})/({m})'}))

    # higher derivatives
    for _ in range(5):
        f = nz(rng, -3, 3) * x**4 + rng.randint(-4, 4) * x**3 + rng.randint(-5, 5) * x**2 + rng.randint(-3, 3) * x
        order = rng.choice([2, 3])
        dn = sp.diff(f, x, order)
        out.append(equiv_problem(S, f"Find ${'f' + chr(39)*order}(x)$ for $f(x) = {L(f)}$.", dn, difficulty=3 if order == 3 else 2,
            hints=["Differentiate once, then differentiate the result again" + (" and again." if order == 3 else "."), f"$f'(x) = {L(sp.diff(f, x))}$."],
            solution=[f"$f'(x) = {L(sp.diff(f, x))}$, $f''(x) = {L(sp.diff(f, x, 2))}$.", f"{'$f' + chr(39)*3 + '(x) = ' + L(dn) + '$.' if order == 3 else 'So the second derivative is $' + L(dn) + '$.'}"],
            verify={'kind': 'equiv', 'expected': f'diff({str(f)}, x, {order})'}))

    # motion: velocity and acceleration
    for _ in range(5):
        s = t**3 - rng.randint(2, 6) * t**2 + rng.randint(1, 9) * t; a = rng.randint(1, 4)
        which = rng.choice(['v', 'a'])
        d = sp.diff(s, t, 1 if which == 'v' else 2); val = d.subs(t, a)
        out.append(numeric_problem(S, f"A particle has position $s(t) = {L(s)}$ (meters, seconds). Find its {'velocity' if which == 'v' else 'acceleration'} at $t = {a}$.", val, difficulty=2,
            hints=["Velocity is $s'(t)$ and acceleration is $s''(t)$.", f"{'$v(t) = ' + L(sp.diff(s, t)) + '$.' if which == 'v' else '$v(t) = ' + L(sp.diff(s, t)) + '$, then differentiate again.'}"],
            solution=[f"$v(t) = {L(sp.diff(s, t))}$" + (f", $a(t) = {L(sp.diff(s, t, 2))}$." if which == 'a' else "."), f"At $t = {a}$: ${N(val)}$ {'m/s' if which == 'v' else 'm/s$^2$'}."],
            verify={'kind': 'evaluate', 'expr': str(d.subs(t, x)), 'at': a}))

    # conceptual
    for _ in range(3):
        c = rng.choice([sp.pi**2, sp.E**3, sp.sqrt(7), sp.Rational(5, 3)])
        out.append(deriv_mc(S, c + 0 * x, rng, difficulty=1, stmt=f"What is $\\dfrac{{d}}{{dx}}\\left({L(c)}\\right)$?",
            distractors=[c, 2 * c, sp.Integer(1)],
            hints=["Is there any $x$ in the expression?", "A constant function has a horizontal graph."],
            solution=[f"${L(c)}$ is a constant (no $x$), so its graph is a horizontal line.", "The derivative of any constant is $0$."]))
    out.append(deriv_mc(S, exp(x), rng, difficulty=1, distractors=[x * exp(x - 1), exp(x - 1), exp(x) * x],
        hints=["The number $e$ is special precisely because of this derivative.", "$e^x$ is not a power function, so the power rule does not apply."],
        solution=["$\\frac{d}{dx} e^x = e^x$: the exponential function is its own derivative.", "By contrast $x^e$ would have derivative $e x^{e-1}$ by the power rule."]))
    for _ in range(2):
        n_ = rng.choice([sp.Rational(1, 2), -1, sp.Rational(3, 2), -2])
        out.append(deriv_mc(S, x**n_, rng, difficulty=2, distractors=[n_ * x**n_, x**(n_ - 1), n_ * x**(n_ + 1)],
            hints=["The power rule holds for every real exponent $n$: bring the exponent down and subtract one.", f"Here $n = {N(n_)}$, so the new exponent is ${N(n_ - 1)}$."],
            solution=[f"$\\frac{{d}}{{dx}} x^{{{N(n_)}}} = {N(n_)} x^{{{N(n_ - 1)}}}$.", f"Equivalently ${L(sp.diff(x**n_, x))}$."]))
    return out


# ======================================================================
# 3.2 product-quotient-rules
# ======================================================================

def product_quotient_rules():
    S = 'product-quotient-rules'
    rng = seeded(S)
    out = []
    simple = [lambda: x**2 + rng.randint(-3, 3), lambda: rng.randint(1, 3) * x + rng.randint(-4, 4), lambda: x**3 - rng.randint(1, 3) * x, lambda: exp(x), lambda: sqrt(x), lambda: rng.randint(2, 4) * x**2 - x, lambda: 1 + rng.randint(1, 3) * exp(x)]

    # product rule
    for _ in range(16):
        f = pick(rng, simple)(); g = pick(rng, simple)()
        if f == g:
            continue
        prod = f * g
        if prod.is_polynomial(x) and rng.random() < 0.6:
            g = exp(x) if not f.has(exp) else sqrt(x); prod = f * g
        dom = (0.5, 2.5) if prod.has(sqrt(x)) else (-2, 2)
        d = sp.diff(prod, x)
        out.append(equiv_problem(S, f"Use the product rule to differentiate $y = {L(prod)}$.", d, difficulty=2 if not prod.has(sqrt(x)) else 3, domain=dom,
            hints=["$(fg)' = f'g + fg'$: derivative of the first times the second, plus the first times derivative of the second.", f"Here $f = {L(f)}$ with $f' = {L(sp.diff(f, x))}$, and $g = {L(g)}$ with $g' = {L(sp.diff(g, x))}$."],
            solution=[f"$y' = \\big({L(sp.diff(f, x))}\\big)\\big({L(g)}\\big) + \\big({L(f)}\\big)\\big({L(sp.diff(g, x))}\\big)$.", f"Simplified: $y' = {L(sp.simplify(d))}$."],
            verify={'kind': 'derivative', 'expr': str(prod)}))

    # quotient rule
    for _ in range(15):
        form = rng.choice(['lin_lin', 'quad_lin', 'exp_x', 'x_quad', 'quad_quad', 'sqrt'])
        if form == 'lin_lin':
            num = rng.randint(1, 4) * x + rng.randint(-3, 3); den = x + rng.randint(1, 4); dom = (0.5, 3)
        elif form == 'quad_lin':
            num = x**2 + rng.randint(-3, 3); den = rng.randint(1, 3) * x - rng.randint(1, 3); dom = (2, 4)
        elif form == 'exp_x':
            num = exp(x); den = x**rng.choice([1, 2]) + rng.randint(0, 2); dom = (0.5, 2.5)
        elif form == 'x_quad':
            num = rng.randint(1, 3) * x; den = x**2 + rng.randint(1, 4); dom = (-2, 2)
        elif form == 'quad_quad':
            num = x**2 - rng.randint(1, 3); den = x**2 + rng.randint(1, 3); dom = (-2, 2)
        else:
            num = sqrt(x); den = x + rng.randint(1, 3); dom = (0.5, 3)
        q = num / den; d = sp.diff(q, x)
        out.append(equiv_problem(S, f"Use the quotient rule to differentiate $y = {L(q)}$.", d, difficulty=2 if form in ('lin_lin', 'x_quad') else 3, domain=dom,
            hints=["$\\left(\\dfrac{f}{g}\\right)' = \\dfrac{f'g - fg'}{g^2}$; the order in the numerator matters.", f"$f = {L(num)}$, $f' = {L(sp.diff(num, x))}$; $g = {L(den)}$, $g' = {L(sp.diff(den, x))}$."],
            solution=[f"$y' = \\dfrac{{\\big({L(sp.diff(num, x))}\\big)\\big({L(den)}\\big) - \\big({L(num)}\\big)\\big({L(sp.diff(den, x))}\\big)}}{{\\left({L(den)}\\right)^2}}$.", f"Simplifying the numerator: $y' = {L(sp.factor(sp.simplify(d)))}$."],
            verify={'kind': 'derivative', 'expr': str(q)}))

    # evaluate at a point
    for _ in range(8):
        form = rng.choice(['prod', 'quot'])
        if form == 'prod':
            f = (x**2 + rng.randint(-2, 3)) * (rng.randint(1, 3) * x - rng.randint(1, 4)) if rng.random() < 0.5 else (x + rng.randint(1, 3)) * exp(x)
            a = rng.randint(-1, 2) if not f.has(exp) else 0
        else:
            f = (rng.randint(1, 3) * x + rng.randint(-3, 3)) / (x**2 + rng.randint(1, 3)); a = rng.randint(-1, 2)
        d = sp.diff(f, x); val = d.subs(x, a)
        out.append(numeric_problem(S, f"Let $f(x) = {L(f)}$. Find $f'({a})$.", val, difficulty=2,
            hints=[f"Differentiate with the {'product' if form == 'prod' else 'quotient'} rule first; do not multiply out unless it helps.", f"Then substitute $x = {a}$ into the derivative (not into $f$)."],
            solution=[f"$f'(x) = {L(sp.simplify(d))}$.", f"$f'({a}) = {N(val)}$."],
            verify={'kind': 'evaluate', 'expr': str(d), 'at': a}))

    # given values of f, f', g, g'
    for _ in range(8):
        a = rng.randint(1, 5); fa, fpa, ga, gpa = nz(rng, -5, 5), nz(rng, -4, 4), nz(rng, -5, 5), nz(rng, -4, 4)
        form = rng.choice(['prod', 'quot', 'quot2', 'mixed'])
        if form == 'prod':
            q = "(fg)'"; vs = f'({fpa})*({ga}) + ({fa})*({gpa})'; rule = "$(fg)'(a) = f'(a)g(a) + f(a)g'(a)$"
        elif form == 'quot':
            q = "(f/g)'"; vs = f'(({fpa})*({ga}) - ({fa})*({gpa}))/({ga})**2'; rule = "$(f/g)'(a) = \\dfrac{f'(a)g(a) - f(a)g'(a)}{g(a)^2}$"
        elif form == 'quot2':
            q = "(g/f)'"; vs = f'(({gpa})*({fa}) - ({ga})*({fpa}))/({fa})**2'; rule = "$(g/f)'(a) = \\dfrac{g'(a)f(a) - g(a)f'(a)}{f(a)^2}$"
        else:
            q = "(x\\,f(x))'"; vs = f'({fa}) + ({a})*({fpa})'; rule = "$(xf)'(a) = 1\\cdot f(a) + a\\,f'(a)$"
        val = sp.sympify(vs)
        out.append(numeric_problem(S, f"Suppose $f({a}) = {fa}$, $f'({a}) = {fpa}$, $g({a}) = {ga}$ and $g'({a}) = {gpa}$. Find ${q}({a})$.", val, difficulty=2,
            hints=["Write the product or quotient rule at the point $a$, then plug in the four numbers.", f"Use {rule}."],
            solution=[f"{rule} with $a = {a}$.", f"$= {vs.replace('**2', '^2').replace('*', ' \\cdot ')} = {N(val)}$."],
            verify={'kind': 'numeric', 'value': vs}))

    # table values
    for _ in range(4):
        a = rng.randint(1, 3); vals = {k_: rng.randint(-4, 5) for k_ in ['f', 'fp', 'g', 'gp']}
        if vals['g'] == 0:
            vals['g'] = 2
        table = f"\\begin{{array}}{{c|cccc}} x & f(x) & f'(x) & g(x) & g'(x) \\\\ \\hline {a} & {vals['f']} & {vals['fp']} & {vals['g']} & {vals['gp']} \\end{{array}}"
        form = rng.choice(['prod', 'quot'])
        vs = f"({vals['fp']})*({vals['g']}) + ({vals['f']})*({vals['gp']})" if form == 'prod' else f"(({vals['fp']})*({vals['g']}) - ({vals['f']})*({vals['gp']}))/({vals['g']})**2"
        val = sp.sympify(vs)
        out.append(numeric_problem(S, f"Values of two functions and their derivatives are given: ${table}$. Let $u(x) = {'f(x)g(x)' if form == 'prod' else 'f(x)/g(x)'}$. Find $u'({a})$.", val, difficulty=2,
            hints=[f"Apply the {'product' if form == 'prod' else 'quotient'} rule at $x = {a}$.", "Read the four needed numbers from the table."],
            solution=[f"$u'({a}) = {'f' + chr(39) + '(' + str(a) + ')g(' + str(a) + ') + f(' + str(a) + ')g' + chr(39) + '(' + str(a) + ')' if form == 'prod' else '[f' + chr(39) + '(' + str(a) + ')g(' + str(a) + ') - f(' + str(a) + ')g' + chr(39) + '(' + str(a) + ')]/g(' + str(a) + ')^2'}$.", f"$= {N(val)}$."],
            verify={'kind': 'numeric', 'value': vs}))

    # tangent line to a quotient or product
    for _ in range(5):
        form = rng.choice(['quot', 'prod'])
        if form == 'quot':
            f = (x + rng.randint(1, 3)) / (x**2 + 1) if rng.random() < 0.5 else (rng.randint(1, 3) * x) / (x + rng.randint(1, 2)); a = rng.randint(0, 2)
        else:
            f = (x**2 + rng.randint(1, 3)) * exp(x); a = 0
        d = sp.diff(f, x); m = d.subs(x, a); fa = f.subs(x, a); line = sp.expand(fa + m * (x - a))
        out.append(equiv_problem(S, f"Find an equation of the tangent line to $y = {L(f)}$ at $x = {a}$.", line, difficulty=3, domain=(-2, 2),
            hints=[f"Use the {'quotient' if form == 'quot' else 'product'} rule to get the slope at $x = {a}$.", "Then point-slope form through the point on the curve."],
            solution=[f"$f'(x) = {L(sp.simplify(d))}$, so $f'({a}) = {N(m)}$, and $f({a}) = {N(fa)}$.", f"$y = {N(fa)} + {N(m)}(x - {a}) = {L(line)}$."],
            verify={'kind': 'tangent', 'expr': str(f), 'at': a}))

    # horizontal tangents of a quotient
    for _ in range(3):
        c = rng.choice([1, 4, 9]); f = x / (x**2 + c); r = int(sp.sqrt(c))
        out.append(label_mc(S, f"At which values of $x$ does $y = {L(f)}$ have a horizontal tangent?", [(f"$x = \\pm {r}$", 'ok'), ("$x = 0$", 'zero'), (f"$x = {r}$ only", 'pos'), (f"$x = \\pm {c}$", 'c')], 'ok', rng, difficulty=3,
            hints=["Differentiate with the quotient rule and set the numerator equal to zero.", f"The numerator of $y'$ is ${L(sp.numer(sp.together(sp.diff(f, x))))}$."],
            solution=[f"$y' = \\dfrac{{(1)(x^2 + {c}) - x(2x)}}{{(x^2 + {c})^2}} = \\dfrac{{{c} - x^2}}{{(x^2 + {c})^2}}$.", f"$y' = 0$ when $x^2 = {c}$, i.e. $x = \\pm {r}$."]))

    # conceptual
    concept = [
        ("Which formula is the product rule for $\\dfrac{d}{dx}[f(x)g(x)]$?", [("$f'(x)g(x) + f(x)g'(x)$", 'ok'), ("$f'(x)g'(x)$", 'w1'), ("$f'(x)g(x) - f(x)g'(x)$", 'w2'), ("$f(x)g'(x)$", 'w3')], 'ok',
         ["The derivative of a product is not the product of the derivatives: test with $f = g = x$.", "Each factor gets differentiated once, in separate terms that are added."],
         ["$(fg)' = f'g + fg'$.", "Check: $(x\\cdot x)' = 1\\cdot x + x\\cdot 1 = 2x$, which matches $(x^2)' = 2x$, whereas $f'g' = 1$ does not."]),
        ("Which formula is the quotient rule for $\\dfrac{d}{dx}\\left[\\dfrac{f(x)}{g(x)}\\right]$?", [("$\\dfrac{f'(x)g(x) - f(x)g'(x)}{[g(x)]^2}$", 'ok'), ("$\\dfrac{f(x)g'(x) - f'(x)g(x)}{[g(x)]^2}$", 'w1'), ("$\\dfrac{f'(x)}{g'(x)}$", 'w2'), ("$\\dfrac{f'(x)g(x) + f(x)g'(x)}{[g(x)]^2}$", 'w3')], 'ok',
         ["Think 'low d-high minus high d-low, over low squared'.", "Test on $1/x$: the answer must be $-1/x^2$."],
         ["$(f/g)' = (f'g - fg')/g^2$.", "With $f = 1, g = x$: $(0\\cdot x - 1\\cdot 1)/x^2 = -1/x^2$, correct."]),
        ("If $f(2) = 3$, $f'(2) = -1$ and $h(x) = x^2 f(x)$, then $h'(2)$ equals", [("$8$", 'ok'), ("$-4$", 'w1'), ("$12$", 'w2'), ("$-1$", 'w3')], 'ok',
         ["Product rule with $u = x^2$ and $v = f(x)$.", "$h'(x) = 2x f(x) + x^2 f'(x)$."],
         ["$h'(2) = 2(2)f(2) + 2^2 f'(2) = 4(3) + 4(-1)$.", "$= 12 - 4 = 8$."]),
    ]
    for stmt, opts, lab, hints, sol in concept:
        out.append(label_mc(S, stmt, opts, lab, rng, difficulty=1, hints=hints, solution=sol))
    return out


# ======================================================================
# 3.3 trig-derivatives
# ======================================================================

def trig_derivatives():
    S = 'trig-derivatives'
    rng = seeded(S)
    out = []
    TAN_DOM = (-1.2, 1.2); COT_DOM = (0.4, 2.7)

    # basic combinations
    for _ in range(10):
        a, b = nz(rng, -5, 5), nz(rng, -5, 5)
        form = rng.choice(['sincos', 'tan', 'sec', 'csc', 'cot', 'mix'])
        if form == 'sincos':
            f = a * sin(x) + b * cos(x); dom = (-3, 3)
        elif form == 'tan':
            f = a * tan(x) + b * x; dom = TAN_DOM
        elif form == 'sec':
            f = a * sec(x) - b * sin(x); dom = TAN_DOM
        elif form == 'csc':
            f = a * csc(x) + b * x**2; dom = COT_DOM
        elif form == 'cot':
            f = a * cot(x) + b * cos(x); dom = COT_DOM
        else:
            f = a * sec(x) + b * tan(x); dom = TAN_DOM
        out.append(deriv_problem(S, f, difficulty=1, domain=dom,
            hints=["Use the table of trig derivatives: $(\\sin x)' = \\cos x$, $(\\cos x)' = -\\sin x$, $(\\tan x)' = \\sec^2 x$, $(\\sec x)' = \\sec x\\tan x$, $(\\csc x)' = -\\csc x\\cot x$, $(\\cot x)' = -\\csc^2 x$.", "Constants multiply through; differentiate each term separately."],
            solution=[f"Differentiate term by term using the trig derivative table.", f"$f'(x) = {L(sp.diff(f, x))}$."]))

    # products
    for _ in range(9):
        form = rng.choice(['x_sin', 'exp_cos', 'x2_tan', 'sin_cos', 'x_sec', 'sqrt_sin'])
        if form == 'x_sin':
            f = rng.randint(1, 3) * x * sin(x) + rng.randint(0, 2) * cos(x); dom = (-3, 3)
        elif form == 'exp_cos':
            f = exp(x) * (cos(x) if rng.random() < 0.5 else sin(x)); dom = (-2, 2)
        elif form == 'x2_tan':
            f = x**2 * tan(x); dom = TAN_DOM
        elif form == 'sin_cos':
            f = sin(x) * cos(x) * rng.randint(1, 3); dom = (-3, 3)
        elif form == 'x_sec':
            f = x * sec(x); dom = TAN_DOM
        else:
            f = sqrt(x) * sin(x); dom = (0.5, 3)
        out.append(deriv_problem(S, f, difficulty=2, domain=dom,
            hints=["This is a product: use $(uv)' = u'v + uv'$.", "Differentiate the trig factor with the trig table and the other factor with the power or exponential rule."],
            solution=[f"Product rule: $f'(x) = {L(sp.diff(f, x))}$." if True else "", "Each term is one factor differentiated times the other left alone."]))

    # quotients
    for _ in range(8):
        form = rng.choice(['sin_over_1pcos', 'x_over_cos', '1psin_over_cos', 'cos_over_x', 'tan_over_x'])
        if form == 'sin_over_1pcos':
            f = sin(x) / (1 + cos(x)); dom = (-2, 2)
        elif form == 'x_over_cos':
            f = x / cos(x); dom = TAN_DOM
        elif form == '1psin_over_cos':
            f = (1 + sin(x)) / cos(x); dom = TAN_DOM
        elif form == 'cos_over_x':
            f = cos(x) / x; dom = (0.5, 3)
        else:
            f = tan(x) / (1 + x**2) if rng.random() < 0.5 else (x + rng.randint(1, 3)) * tan(x) / 1; dom = TAN_DOM
        out.append(deriv_problem(S, f, difficulty=3, domain=dom,
            hints=["Use the quotient rule: $\\left(\\dfrac{u}{v}\\right)' = \\dfrac{u'v - uv'}{v^2}$.", "After differentiating, look for $\\sin^2 x + \\cos^2 x = 1$ to simplify."] if not (form == 'tan_over_x' and f.is_Mul) else ["Product rule, with $(\\tan x)' = \\sec^2 x$.", "Keep the $\\sec^2 x$ factor; no need to convert to sine and cosine."],
            solution=[f"Apply the rule and simplify: $f'(x) = {L(sp.simplify(sp.diff(f, x)))}$.", "Using $\\sin^2 x + \\cos^2 x = 1$ where it appears gives the compact form."]))

    # evaluate at special angles
    for _ in range(8):
        f = rng.choice([sin(x) + rng.randint(1, 3) * cos(x), x * cos(x), tan(x), rng.randint(1, 3) * sec(x), sin(x) * cos(x), x + sin(x)])
        a = pick(rng, [0, pi / 6, pi / 4, pi / 3, pi / 2, pi])
        if f.has(tan(x)) or f.has(sec(x)):
            a = pick(rng, [0, pi / 6, pi / 4, pi / 3])
        d = sp.diff(f, x); val = sp.simplify(d.subs(x, a))
        out.append(numeric_problem(S, f"Let $f(x) = {L(f)}$. Find the exact value of $f'\\left({L(a)}\\right)$.", val, difficulty=2,
            hints=["Differentiate first, then substitute the angle.", f"$f'(x) = {L(d)}$; recall the exact values of sine and cosine at ${L(a)}$."],
            solution=[f"$f'(x) = {L(d)}$.", f"$f'({L(a)}) = {L(val)}$."],
            verify={'kind': 'evaluate', 'expr': str(d), 'at': str(a)}))

    # tangent lines
    for _ in range(5):
        f = rng.choice([sin(x), cos(x), x * sin(x), tan(x), 2 * cos(x) + x])
        a = pick(rng, [0, pi / 4, pi / 2, pi / 3]) if not f.has(tan) else pick(rng, [0, pi / 4])
        d = sp.diff(f, x); m = sp.simplify(d.subs(x, a)); fa = sp.simplify(f.subs(x, a)); line = sp.expand(fa + m * (x - a))
        out.append(equiv_problem(S, f"Find an equation of the tangent line to $y = {L(f)}$ at the point where $x = {L(a)}$.", line, difficulty=3, domain=(-2, 2),
            hints=[f"Slope $= f'({L(a)})$; the point is $({L(a)}, f({L(a)}))$.", f"$f'(x) = {L(d)}$."],
            solution=[f"$f({L(a)}) = {L(fa)}$ and $f'({L(a)}) = {L(m)}$.", f"$y = {L(fa)} + {L(m)}\\left(x - {L(a)}\\right)$, i.e. $y = {L(line)}$."],
            verify={'kind': 'tangent', 'expr': str(f), 'at': str(a)}))

    # trig limits
    for _ in range(8):
        form = rng.choice(['sin_kx', 'tan_kx', 'sin_sin', 'one_minus_cos', 'sin_over_x_sq'])
        k1, k2 = rng.randint(2, 7), rng.randint(2, 7)
        if form == 'sin_kx':
            f = sin(k1 * x) / x; why = f"$\\dfrac{{\\sin {k1}x}}{{x}} = {k1}\\cdot\\dfrac{{\\sin {k1}x}}{{{k1}x}}$ and $\\dfrac{{\\sin \\theta}}{{\\theta}} \\to 1$"
        elif form == 'tan_kx':
            f = tan(k1 * x) / x; why = f"$\\tan {k1}x = \\dfrac{{\\sin {k1}x}}{{\\cos {k1}x}}$ and $\\cos {k1}x \\to 1$, so this behaves like $\\dfrac{{\\sin {k1}x}}{{x}} \\to {k1}$"
        elif form == 'sin_sin':
            f = sin(k1 * x) / sin(k2 * x); why = f"write it as $\\dfrac{{\\sin {k1}x}}{{{k1}x}} \\cdot \\dfrac{{{k2}x}}{{\\sin {k2}x}} \\cdot \\dfrac{{{k1}}}{{{k2}}}$; the first two factors approach $1$"
        elif form == 'one_minus_cos':
            f = (1 - cos(k1 * x)) / x if rng.random() < 0.5 else (cos(x) - 1) / (k1 * x); why = f"$\\dfrac{{1 - \\cos\\theta}}{{\\theta}} \\to 0$"
        else:
            f = sin(x)**2 / x; why = "$\\dfrac{\\sin^2 x}{x} = \\sin x \\cdot \\dfrac{\\sin x}{x} \\to 0 \\cdot 1$"
        val = sp.limit(f, x, 0)
        out.append(numeric_problem(S, f"Evaluate $\\displaystyle\\lim_{{x \\to 0}} {L(f)}$.", val, difficulty=2,
            hints=["Use the special limits $\\lim_{\\theta \\to 0} \\dfrac{\\sin\\theta}{\\theta} = 1$ and $\\lim_{\\theta \\to 0} \\dfrac{\\cos\\theta - 1}{\\theta} = 0$.", "Rescale the variable so the argument of the trig function matches the denominator."],
            solution=[f"Rewrite: {why}.", f"So the limit is ${N(val)}$."],
            verify={'kind': 'limit', 'expr': str(f), 'to': 0}))

    # simple harmonic motion
    for _ in range(4):
        A, B = rng.randint(1, 4), rng.randint(1, 4)
        s = A * cos(t) + B * sin(t); a = pick(rng, [0, pi / 2, pi, pi / 6])
        which = rng.choice(['v', 'a'])
        d = sp.diff(s, t, 1 if which == 'v' else 2); val = sp.simplify(d.subs(t, a))
        out.append(numeric_problem(S, f"A mass on a spring has position $s(t) = {L(s)}$. Find its {'velocity' if which == 'v' else 'acceleration'} at $t = {L(a)}$.", val, difficulty=2,
            hints=[f"{'Velocity is the first derivative of position.' if which == 'v' else 'Acceleration is the second derivative of position.'}", "Differentiate sine and cosine, then substitute the time."],
            solution=[f"${'v' if which == 'v' else 'a'}(t) = {L(d)}$.", f"At $t = {L(a)}$: ${L(val)}$."],
            verify={'kind': 'evaluate', 'expr': str(d.subs(t, x)), 'at': str(a)}))

    # higher derivatives of sin/cos
    for _ in range(4):
        f = rng.choice([sin(x), cos(x), rng.randint(2, 4) * sin(x) - x**2, x * cos(x)])
        order = rng.choice([2, 3, 4])
        dn = sp.diff(f, x, order)
        out.append(equiv_problem(S, f"Find $f^{{({order})}}(x)$, the derivative of order ${order}$, for $f(x) = {L(f)}$.", dn, difficulty=2 if f in (sin(x), cos(x)) else 3,
            hints=["Differentiate repeatedly; sine and cosine cycle with period four.", "Keep careful track of the signs."],
            solution=[f"$f'(x) = {L(sp.diff(f, x))}$, $f''(x) = {L(sp.diff(f, x, 2))}$" + (f", $f'''(x) = {L(sp.diff(f, x, 3))}$" if order >= 3 else "") + ".", f"$f^{{({order})}}(x) = {L(dn)}$."],
            verify={'kind': 'equiv', 'expected': f'diff({str(f)}, x, {order})'}))

    # multiple choice derivative identification
    mcs = [(sec(x), [sec(x) * tan(x) * -1, sec(x)**2, tan(x)**2]), (cos(x), [sin(x), -cos(x), sec(x)]), (cot(x), [csc(x)**2, -sec(x)**2, csc(x) * cot(x)]), (tan(x), [sec(x), sec(x) * tan(x), -sec(x)**2]), (csc(x), [csc(x) * cot(x), -csc(x)**2, -sec(x) * tan(x)])]
    for f, dis in mcs:
        out.append(deriv_mc(S, f, rng, difficulty=1, distractors=dis,
            hints=["Recall the six basic trig derivatives; the co-functions (cos, cot, csc) all get a minus sign.", f"Look up $\\frac{{d}}{{dx}}{L(f)}$ in the table."],
            solution=[f"$\\frac{{d}}{{dx}}{L(f)} = {L(sp.diff(f, x))}$.", "This is one of the six standard trig derivatives worth memorizing."]))
    return out


# ======================================================================
# 3.4 chain-rule
# ======================================================================

def chain_rule():
    S = 'chain-rule'
    rng = seeded(S)
    out = []

    # single chain
    for _ in range(20):
        form = rng.choice(['pow_lin', 'sqrt_quad', 'neg_pow', 'exp_k', 'exp_quad', 'sin_k', 'cos_quad', 'tan_k', 'sin_pow', 'exp_sin', 'sin_exp', 'sqrt_cos'])
        a, b, k = nz(rng, -4, 4), rng.randint(-4, 4), rng.randint(2, 5)
        if form == 'pow_lin':
            f = (a * x + b)**rng.choice([3, 4, 5]); dom = (-2, 2); inner = a * x + b
        elif form == 'sqrt_quad':
            f = sqrt(x**2 + abs(b) + 1); dom = (-2, 2); inner = x**2 + abs(b) + 1
        elif form == 'neg_pow':
            f = (x**2 + abs(b) + 1)**(-rng.choice([1, 2, 3])); dom = (-2, 2); inner = x**2 + abs(b) + 1
        elif form == 'exp_k':
            f = rng.randint(1, 4) * exp(a * x); dom = (-1, 1); inner = a * x
        elif form == 'exp_quad':
            f = exp(x**2 + b * x) if rng.random() < 0.5 else exp(-x**2); dom = (-1.5, 1.5); inner = list(f.atoms(sp.exp))[0].args[0]
        elif form == 'sin_k':
            f = sin(k * x) * rng.randint(1, 3); dom = (-2, 2); inner = k * x
        elif form == 'cos_quad':
            f = cos(x**2 + b); dom = (-2, 2); inner = x**2 + b
        elif form == 'tan_k':
            f = tan(k * x); dom = (-0.25, 0.25); inner = k * x
        elif form == 'sin_pow':
            f = sin(x)**k; dom = (-3, 3); inner = sin(x)
        elif form == 'exp_sin':
            f = exp(sin(x)); dom = (-3, 3); inner = sin(x)
        elif form == 'sin_exp':
            f = sin(exp(x)); dom = (-2, 1); inner = exp(x)
        else:
            f = sqrt(1 + cos(x)**2) if rng.random() < 0.5 else sqrt(2 + sin(x)); dom = (-3, 3); inner = f.args[0]
        out.append(deriv_problem(S, f, difficulty=1 if form in ('pow_lin', 'exp_k', 'sin_k') else 2, domain=dom,
            hints=["Identify the outer function and the inner function; the chain rule says $\\frac{d}{dx} f(g(x)) = f'(g(x))\\,g'(x)$.", f"The inner function is $u = {L(inner)}$, whose derivative is ${L(sp.diff(inner, x))}$."],
            solution=[f"Outer derivative evaluated at the inner function, times the inner derivative ${L(sp.diff(inner, x))}$.", f"$f'(x) = {L(sp.diff(f, x))}$."]))

    # double chain
    for _ in range(6):
        form = rng.choice(['sin_cos', 'exp_sqrt', 'pow_exp', 'cos_sq_k', 'sqrt_sin_k'])
        k = rng.randint(2, 4)
        if form == 'sin_cos':
            f = sin(cos(k * x)); dom = (-2, 2)
        elif form == 'exp_sqrt':
            f = exp(sqrt(x + rng.randint(0, 3))); dom = (0.5, 3)
        elif form == 'pow_exp':
            f = (1 + exp(k * x))**rng.choice([2, 3]); dom = (-1, 0.5)
        elif form == 'cos_sq_k':
            f = cos(k * x)**2; dom = (-2, 2)
        else:
            f = sqrt(1 + sin(k * x)**2); dom = (-2, 2)
        out.append(deriv_problem(S, f, difficulty=3, domain=dom,
            hints=["There are two layers of composition; apply the chain rule twice, working from the outside in.", "Write $y = f(g(h(x)))$ and multiply the three derivatives: $f'(g(h(x)))\\cdot g'(h(x))\\cdot h'(x)$."],
            solution=[f"Peel the layers: outer derivative, then the middle, then the innermost (${L(k*x) if form != 'exp_sqrt' else L(f.args[0].args[0])}$).", f"$f'(x) = {L(sp.diff(f, x))}$."]))

    # chain + product/quotient
    for _ in range(10):
        form = rng.choice(['x_exp', 'x2_sin', 'pow_pow', 'exp_over', 'sin_over'])
        k = rng.randint(2, 4)
        if form == 'x_exp':
            f = x * exp(-k * x) if rng.random() < 0.5 else x * exp(-x**2); dom = (-1, 1)
        elif form == 'x2_sin':
            f = x**2 * sin(k * x); dom = (-2, 2)
        elif form == 'pow_pow':
            f = (2 * x + 1)**k * (x - rng.randint(1, 3))**2; dom = (-2, 2)
        elif form == 'exp_over':
            f = exp(k * x) / (1 + x**2); dom = (-1, 1)
        else:
            f = sin(k * x) / x; dom = (0.5, 3)
        out.append(deriv_problem(S, f, difficulty=3, domain=dom,
            hints=[f"Use the {'product' if form in ('x_exp', 'x2_sin', 'pow_pow') else 'quotient'} rule, and the chain rule when you differentiate the composite factor.", "Factor out common pieces at the end to simplify."],
            solution=[f"{'Product' if form in ('x_exp', 'x2_sin', 'pow_pow') else 'Quotient'} rule with the chain rule on the inner factor gives $f'(x) = {L(sp.diff(f, x))}$.", f"Factored: $f'(x) = {L(sp.factor(sp.diff(f, x)))}$."]))

    # evaluate at a point
    for _ in range(7):
        f = rng.choice([(x**2 + rng.randint(1, 3))**3, sqrt(rng.randint(2, 5) * x + 1), exp(rng.randint(2, 4) * x), sin(pi * x), cos(x**2), (1 + 2 * x)**(-2)])
        a = 0 if f.has(exp) else rng.choice([0, 1, 2]) if not f.has(sqrt) else rng.choice([0, 1] if f == sqrt(3 * x + 1) or f == sqrt(5 * x + 1) else [0])
        if f.has(sqrt) and not sp.simplify(sp.diff(f, x).subs(x, a)).is_rational:
            a = 0
        d = sp.diff(f, x); val = sp.simplify(d.subs(x, a))
        out.append(numeric_problem(S, f"Let $F(x) = {L(f)}$. Find $F'({a})$.", val, difficulty=2,
            hints=["Apply the chain rule to get $F'(x)$ before substituting.", f"$F'(x) = {L(d)}$."],
            solution=[f"$F'(x) = {L(d)}$.", f"$F'({a}) = {L(val)}$."],
            verify={'kind': 'evaluate', 'expr': str(d), 'at': a}))

    # chain rule with table values
    for _ in range(6):
        a = rng.randint(1, 3); ga = rng.randint(1, 3); gpa = nz(rng, -4, 4); fpga = nz(rng, -5, 5); fa = rng.randint(-3, 3); fpa = nz(rng, -3, 3); gfa = rng.randint(1, 3)
        form = rng.choice(['fog', 'gof'])
        if form == 'fog':
            stmt = f"Suppose $g({a}) = {ga}$, $g'({a}) = {gpa}$, $f'({ga}) = {fpga}$ and $f'({a}) = {fpa}$. If $F(x) = f(g(x))$, find $F'({a})$."
            vs = f'({fpga})*({gpa})'; sol = [f"$F'(x) = f'(g(x))\\,g'(x)$, so $F'({a}) = f'(g({a}))\\,g'({a}) = f'({ga})\\cdot g'({a})$.", f"$= ({fpga})({gpa}) = {fpga*gpa}$. (The value $f'({a})$ is a distractor.)"]
        else:
            stmt = f"Suppose $f({a}) = {gfa}$, $f'({a}) = {fpa}$, $g'({gfa}) = {gpa}$ and $g'({a}) = {fpga}$. If $G(x) = g(f(x))$, find $G'({a})$."
            vs = f'({gpa})*({fpa})'; sol = [f"$G'(x) = g'(f(x))\\,f'(x)$, so $G'({a}) = g'(f({a}))\\,f'({a}) = g'({gfa})\\cdot f'({a})$.", f"$= ({gpa})({fpa}) = {gpa*fpa}$."]
        out.append(numeric_problem(S, stmt, sp.sympify(vs), difficulty=2,
            hints=["Write the chain rule for the composite, then evaluate the outer derivative at the inner function's value.", "Be careful to use the derivative of the outer function at the right input."],
            solution=sol, verify={'kind': 'numeric', 'value': vs}))

    # tangent line to a composite
    for _ in range(5):
        f = rng.choice([sqrt(x**2 + rng.choice([5, 9, 12]) - 0), exp(rng.randint(1, 3) * x), (x**2 - rng.randint(1, 3))**3, sin(rng.randint(2, 4) * x) + 1, (rng.randint(1, 3) * x + 1)**2])
        a = 0 if (f.has(exp) or f.has(sin)) else rng.choice([2] if f.has(sqrt) else [0, 1])
        if f.has(sqrt) and not f.subs(x, a).is_rational:
            a = 0
            if not f.subs(x, a).is_rational:
                f = sqrt(x**2 + 9); a = 4
        d = sp.diff(f, x); m = sp.simplify(d.subs(x, a)); fa = sp.simplify(f.subs(x, a)); line = sp.expand(fa + m * (x - a))
        out.append(equiv_problem(S, f"Find an equation of the tangent line to $y = {L(f)}$ at $x = {a}$.", line, difficulty=3, domain=(-2, 2),
            hints=["Differentiate with the chain rule to get the slope at the point.", f"$y' = {L(d)}$."],
            solution=[f"$y({a}) = {L(fa)}$ and $y'({a}) = {L(m)}$.", f"Tangent: $y = {L(fa)} + {L(m)}(x - {a}) = {L(line)}$."],
            verify={'kind': 'tangent', 'expr': str(f), 'at': a}))

    # general exponential b^x
    for _ in range(4):
        b = rng.choice([2, 3, 5, 10]); k = rng.choice([1, 1, 2, 3])
        f = sp.Integer(b)**(k * x) if rng.random() < 0.6 else x * sp.Integer(b)**x
        out.append(deriv_problem(S, f, difficulty=2, domain=(-1, 1),
            hints=[f"Write ${b}^{{u}} = e^{{u\\ln {b}}}$, or use the formula $(b^x)' = b^x \\ln b$.", "Then apply the chain rule (and the product rule if there is another factor)."],
            solution=[f"$\\frac{{d}}{{dx}} {b}^{{u}} = {b}^{{u}} \\ln {b} \\cdot u'$.", f"$f'(x) = {L(sp.diff(f, x))}$."]))

    # conceptual
    concept = [
        ("If $y = f(u)$ and $u = g(x)$ are both differentiable, the chain rule says $\\dfrac{dy}{dx}$ equals", [("$\\dfrac{dy}{du}\\cdot\\dfrac{du}{dx}$", 'ok'), ("$\\dfrac{dy}{du} + \\dfrac{du}{dx}$", 'sum'), ("$\\dfrac{dy}{du}$", 'only'), ("$\\dfrac{du}{dx}\\big/\\dfrac{dy}{du}$", 'div')], 'ok',
         ["Think of rates multiplying: if $y$ changes 3 times as fast as $u$, and $u$ changes 2 times as fast as $x$, then $y$ changes 6 times as fast as $x$.", "In Leibniz notation the $du$'s appear to cancel."],
         ["$\\frac{dy}{dx} = \\frac{dy}{du}\\frac{du}{dx}$: outer derivative (with respect to $u$) times inner derivative.", "This is the chain rule in Leibniz form."]),
        ("To differentiate $y = \\sin(x^3)$ with the chain rule, the outer function and inner function are", [("outer $\\sin u$, inner $u = x^3$", 'ok'), ("outer $u^3$, inner $u = \\sin x$", 'swap'), ("outer $x^3$, inner $\\sin$", 'w'), ("there is no composition here", 'none')], 'ok',
         ["Which operation is applied last when you evaluate $\\sin(x^3)$ at a number?", "Cube first, then take the sine: the last operation is the outer function."],
         ["$\\sin(x^3)$ means first compute $x^3$, then take the sine, so $\\sin$ is outer and $x^3$ is inner.", "Hence $y' = \\cos(x^3)\\cdot 3x^2$. (The function $(\\sin x)^3$ would have the roles swapped.)"]),
        ("The derivative of $e^{5x}$ is", [("$5e^{5x}$", 'ok'), ("$e^{5x}$", 'same'), ("$5xe^{5x-1}$", 'pow'), ("$e^{5}$", 'const')], 'ok',
         ["The exponent is $5x$, not $x$; the chain rule brings out its derivative.", "$\\frac{d}{dx} e^{u} = e^{u} u'$."],
         ["With $u = 5x$, $u' = 5$.", "So $\\frac{d}{dx} e^{5x} = e^{5x}\\cdot 5 = 5e^{5x}$."]),
    ]
    for stmt, opts, lab, hints, sol in concept:
        out.append(label_mc(S, stmt, opts, lab, rng, difficulty=1, hints=hints, solution=sol))
    return out


# ======================================================================
# 3.5 implicit-differentiation (incl. inverse trig)
# ======================================================================

def implicit_differentiation():
    S = 'implicit-differentiation'
    rng = seeded(S)
    out = []

    # dy/dx at a point
    for _ in range(22):
        form = rng.choice(['circle', 'cubic_sum', 'xy', 'quad_mixed', 'ellipse', 'xy_sq', 'cubic_xy'])
        if form == 'circle':
            x0, y0 = pick(rng, [(3, 4), (4, 3), (-3, 4), (3, -4), (0, 5), (5, 0), (6, 8), (-8, 6), (1, 1), (2, 1), (-1, 2)])
            lhs, rhs = x**2 + y**2, x0**2 + y0**2
        elif form == 'cubic_sum':
            x0, y0 = rng.randint(-2, 2), nz(rng, -2, 2)
            lhs, rhs = x**3 + y**3, x0**3 + y0**3
        elif form == 'xy':
            x0, y0 = nz(rng, -4, 4), nz(rng, -4, 4)
            lhs, rhs = x * y + rng.randint(1, 3) * x, (x * y + 0).subs({x: x0, y: y0}) + 0
            lhs = x * y + (c := rng.randint(1, 3)) * x; rhs = x0 * y0 + c * x0
        elif form == 'quad_mixed':
            x0, y0 = nz(rng, -3, 3), nz(rng, -3, 3)
            lhs = x**2 + x * y + y**2; rhs = lhs.subs({x: x0, y: y0})
        elif form == 'ellipse':
            x0, y0 = pick(rng, [(2, 1), (-2, 1), (1, 2), (3, 2), (2, 3), (-1, 3)])
            a, b = rng.choice([1, 2, 3]), rng.choice([1, 2, 4])
            lhs = a * x**2 + b * y**2; rhs = lhs.subs({x: x0, y: y0})
        elif form == 'xy_sq':
            x0, y0 = nz(rng, -3, 3), nz(rng, -3, 3)
            lhs = x * y**2 + x**2; rhs = lhs.subs({x: x0, y: y0})
        else:
            x0, y0 = nz(rng, -2, 2), nz(rng, -2, 2)
            lhs = x**3 - x * y + y**2; rhs = lhs.subs({x: x0, y: y0})
        F = lhs - rhs
        Fy = sp.diff(F, y).subs({x: x0, y: y0})
        if Fy == 0:
            continue
        m = (-sp.diff(F, x) / sp.diff(F, y)).subs({x: x0, y: y0})
        out.append(numeric_problem(S, f"Use implicit differentiation to find $\\dfrac{{dy}}{{dx}}$ at the point $({x0}, {y0})$ on the curve ${L(lhs)} = {N(rhs)}$.", m, difficulty=2 if form in ('circle', 'cubic_sum', 'ellipse') else 3,
            hints=["Differentiate both sides with respect to $x$, treating $y$ as a function of $x$ (so $y^n$ gives $ny^{n-1}y'$ and $xy$ needs the product rule).", "Solve for $y'$, then substitute the coordinates of the point."],
            solution=[f"Differentiating: ${L(sp.diff(F, x))} + \\left({L(sp.diff(F, y))}\\right)y' = 0$, so $y' = {L(sp.simplify(-sp.diff(F, x)/sp.diff(F, y)))}$.", f"At $({x0}, {y0})$: $y' = {N(m)}$."],
            verify={'kind': 'implicit', 'lhs': str(lhs), 'rhs': str(rhs), 'x0': x0, 'y0': y0}))

    # tangent line to an implicit curve
    for _ in range(10):
        form = rng.choice(['circle', 'quad_mixed', 'cubic_sum', 'xy'])
        if form == 'circle':
            x0, y0 = pick(rng, [(3, 4), (-4, 3), (1, 1), (2, -1), (6, 8), (-1, -2)]); lhs = x**2 + y**2
        elif form == 'quad_mixed':
            x0, y0 = nz(rng, -3, 3), nz(rng, -3, 3); lhs = x**2 - x * y + y**2
        elif form == 'cubic_sum':
            x0, y0 = nz(rng, -2, 2), nz(rng, -2, 2); lhs = x**3 + y**3 - rng.randint(1, 3) * x * y
        else:
            x0, y0 = nz(rng, -3, 3), nz(rng, -3, 3); lhs = x * y + y**2
        rhs = lhs.subs({x: x0, y: y0}); F = lhs - rhs
        if sp.diff(F, y).subs({x: x0, y: y0}) == 0:
            continue
        m = (-sp.diff(F, x) / sp.diff(F, y)).subs({x: x0, y: y0}); line = sp.expand(y0 + m * (x - x0))
        out.append(equiv_problem(S, f"Find an equation of the tangent line to the curve ${L(lhs)} = {N(rhs)}$ at the point $({x0}, {y0})$.", line, difficulty=3, domain=(-3, 3),
            hints=["Find $y'$ by implicit differentiation and evaluate it at the point to get the slope.", "Then use point-slope form."],
            solution=[f"$y' = {L(sp.simplify(-sp.diff(F, x)/sp.diff(F, y)))}$, which at $({x0}, {y0})$ equals ${N(m)}$.", f"Tangent: $y - ({y0}) = {N(m)}(x - ({x0}))$, i.e. $y = {L(line)}$."],
            verify={'kind': 'equiv', 'expected': f'({y0}) + ({m})*(x - ({x0}))'}))

    # inverse trig derivatives
    for _ in range(14):
        form = rng.choice(['asin_k', 'atan_k', 'asin_sq', 'atan_sq', 'x_atan', 'acos_lin', 'atan_sqrt', 'asin_over'])
        k = rng.randint(2, 4)
        if form == 'asin_k':
            f = sp.asin(k * x); dom = (-0.2, 0.2)
        elif form == 'atan_k':
            f = sp.atan(k * x) * rng.randint(1, 3); dom = (-2, 2)
        elif form == 'asin_sq':
            f = sp.asin(x**2); dom = (-0.9, 0.9)
        elif form == 'atan_sq':
            f = sp.atan(x**2 + rng.randint(0, 2)); dom = (-2, 2)
        elif form == 'x_atan':
            f = x * sp.atan(x) if rng.random() < 0.5 else x**2 * sp.asin(x); dom = (-0.9, 0.9)
        elif form == 'acos_lin':
            f = sp.acos(x / k); dom = (-1.5, 1.5)
        elif form == 'atan_sqrt':
            f = sp.atan(sqrt(x)); dom = (0.5, 3)
        else:
            f = sp.asin(x) / x if rng.random() < 0.5 else exp(x) * sp.atan(x); dom = (0.3, 0.9)
        out.append(deriv_problem(S, f, difficulty=2 if form in ('asin_k', 'atan_k', 'acos_lin') else 3, domain=dom,
            hints=["Recall $(\\arcsin u)' = \\dfrac{u'}{\\sqrt{1-u^2}}$, $(\\arccos u)' = -\\dfrac{u'}{\\sqrt{1-u^2}}$, $(\\arctan u)' = \\dfrac{u'}{1+u^2}$.", "Apply the chain rule (and product or quotient rule if there is another factor)."],
            solution=[f"Use the inverse trig derivative formula with the chain rule on the inner function.", f"$f'(x) = {L(sp.diff(f, x))}$."]))

    # evaluate inverse trig derivative at a point
    for _ in range(7):
        f = rng.choice([sp.atan(x), sp.asin(x), sp.atan(2 * x), sp.acos(x), x * sp.atan(x)])
        a = pick(rng, [0, 1, sp.Rational(1, 2), -1]) if f.has(sp.atan) else pick(rng, [0, sp.Rational(1, 2), sp.Rational(-1, 2)])
        d = sp.diff(f, x); val = sp.simplify(d.subs(x, a))
        out.append(numeric_problem(S, f"Find the exact value of $f'\\left({L(a)}\\right)$ for $f(x) = {L(f)}$.", val, difficulty=2,
            hints=["Differentiate using the inverse trig formulas first.", f"$f'(x) = {L(d)}$."],
            solution=[f"$f'(x) = {L(d)}$.", f"$f'({L(a)}) = {L(val)}$."],
            verify={'kind': 'evaluate', 'expr': str(d), 'at': str(a)}))

    # horizontal tangent points of implicit curves
    for _ in range(3):
        c = rng.choice([3, 12, 27])
        f_l = f"x^2 + xy + y^2 = {c}"
        pts = sp.solve([x**2 + x * y + y**2 - c, 2 * x + y], [x, y])
        pts_real = [(p_[0], p_[1]) for p_ in pts if p_[0].is_real]
        p1, p2 = sorted(pts_real)
        opts = [(f"$({L(p1[0])}, {L(p1[1])})$ and $({L(p2[0])}, {L(p2[1])})$", 'ok'), (f"$({L(p1[1])}, {L(p1[0])})$ and $({L(p2[1])}, {L(p2[0])})$", 'swap'), (f"$(0, \\pm\\sqrt{{{c}}})$", 'axis'), ("there are none", 'none')],
        out.append(label_mc(S, f"At which points does the curve ${f_l}$ have a horizontal tangent?", opts[0], 'ok', rng, difficulty=3,
            hints=["Differentiate implicitly: $2x + y + xy' + 2yy' = 0$, so $y' = -\\dfrac{2x + y}{x + 2y}$.", "Horizontal tangent means $y' = 0$: set $2x + y = 0$ and substitute $y = -2x$ into the curve."],
            solution=[f"$y' = 0$ requires $y = -2x$. Substituting: $x^2 - 2x^2 + 4x^2 = 3x^2 = {c}$, so $x = \\pm{L(p2[0])}$.", f"The points are $({L(p1[0])}, {L(p1[1])})$ and $({L(p2[0])}, {L(p2[1])})$."]))

    # conceptual
    concept = [
        ("When differentiating $y^4$ with respect to $x$ (where $y$ depends on $x$), the result is", [("$4y^3\\,\\dfrac{dy}{dx}$", 'ok'), ("$4y^3$", 'nochain'), ("$4x^3$", 'wrongvar'), ("$y^4\\,\\dfrac{dy}{dx}$", 'w')], 'ok',
         ["$y$ is a function of $x$, so $y^4$ is a composite function.", "Chain rule: power rule on the outside, then multiply by $y'$."],
         ["$\\frac{d}{dx}[y^4] = 4y^3 \\cdot \\frac{dy}{dx}$ by the chain rule.", "Forgetting the factor $dy/dx$ is the most common implicit differentiation error."]),
        ("To find $\\dfrac{d}{dx}(xy)$ implicitly you need", [("the product rule: $y + x\\,\\dfrac{dy}{dx}$", 'ok'), ("just $y$", 'y'), ("just $x\\,\\dfrac{dy}{dx}$", 'x'), ("$\\dfrac{dy}{dx}$ alone", 'd')], 'ok',
         ["$x$ and $y$ are both changing, so $xy$ is a product of two functions of $x$.", "$(uv)' = u'v + uv'$ with $u = x$ and $v = y$."],
         ["$\\frac{d}{dx}(xy) = 1\\cdot y + x\\cdot y'$.", "Both terms are needed."]),
        ("The derivative of $\\arctan x$ is", [("$\\dfrac{1}{1 + x^2}$", 'ok'), ("$\\dfrac{1}{\\sqrt{1 - x^2}}$", 'asin'), ("$\\sec^2 x$", 'tan'), ("$-\\dfrac{1}{1 + x^2}$", 'neg')], 'ok',
         ["Differentiate $\\tan y = x$ implicitly: $\\sec^2 y \\cdot y' = 1$.", "Use $\\sec^2 y = 1 + \\tan^2 y = 1 + x^2$."],
         ["From $\\tan y = x$: $y' = \\frac{1}{\\sec^2 y} = \\frac{1}{1 + \\tan^2 y}$.", "Since $\\tan y = x$, $y' = \\frac{1}{1 + x^2}$."]),
    ]
    for stmt, opts, lab, hints, sol in concept:
        out.append(label_mc(S, stmt, opts, lab, rng, difficulty=1, hints=hints, solution=sol))
    return out


# ======================================================================
# 3.6 log-derivatives
# ======================================================================

def log_derivatives():
    S = 'log-derivatives'
    rng = seeded(S)
    out = []
    LD = (0.5, 3)

    # basic log derivatives
    for _ in range(22):
        form = rng.choice(['ln_lin', 'ln_quad', 'ln_sqrt', 'x_ln', 'ln_over_x', 'ln_sq', 'log_b', 'log_b_quad', 'ln_sin', 'ln_exp_mix', 'ln_ln'])
        a, b, k = rng.randint(1, 5), rng.randint(1, 5), rng.randint(2, 5)
        if form == 'ln_lin':
            f = log(a * x + b); dom = LD
        elif form == 'ln_quad':
            f = log(x**2 + b); dom = (-2, 2)
        elif form == 'ln_sqrt':
            f = log(sqrt(x + b)) if rng.random() < 0.5 else sqrt(log(x) + 1); dom = (1, 3)
        elif form == 'x_ln':
            f = x**rng.choice([1, 2, 3]) * log(x); dom = LD
        elif form == 'ln_over_x':
            f = log(x) / x**rng.choice([1, 2]); dom = LD
        elif form == 'ln_sq':
            f = log(x)**k; dom = LD
        elif form == 'log_b':
            f = log(x, rng.choice([2, 3, 10])); dom = LD
        elif form == 'log_b_quad':
            f = log(x**2 + a, rng.choice([2, 5, 10])); dom = (-2, 2)
        elif form == 'ln_sin':
            f = log(sin(x)) if rng.random() < 0.5 else log(cos(x)); dom = (0.3, 1.2)
        elif form == 'ln_exp_mix':
            f = log(1 + exp(k * x)) if rng.random() < 0.5 else exp(x) * log(x); dom = (0.5, 1.5)
        else:
            f = log(log(x)); dom = (1.5, 4)
        out.append(deriv_problem(S, f, difficulty=1 if form in ('ln_lin', 'ln_quad', 'log_b') else (3 if form in ('ln_ln', 'ln_exp_mix', 'ln_sq') else 2), domain=dom,
            hints=["$\\dfrac{d}{dx}\\ln u = \\dfrac{u'}{u}$, and $\\dfrac{d}{dx}\\log_b u = \\dfrac{u'}{u\\ln b}$.", "Combine with the product, quotient or chain rule as the structure requires."],
            solution=[f"Apply the logarithm derivative rule to the inner function, with the chain, product or quotient rule as needed.", f"$f'(x) = {L(sp.diff(f, x))}$."]))

    # simplify with log laws first
    for _ in range(9):
        form = rng.choice(['prod_pow', 'quot', 'root'])
        a, b, c = rng.randint(1, 4), rng.randint(1, 5), rng.randint(1, 5)
        if form == 'prod_pow':
            inner = x**a * (x + b)**c; expanded = a * log(x) + c * log(x + b)
        elif form == 'quot':
            inner = (x + b)**a / (x**2 + c); expanded = a * log(x + b) - log(x**2 + c)
        else:
            inner = sqrt((x + b) / (x + c)); expanded = sp.Rational(1, 2) * (log(x + b) - log(x + c))
        f = log(inner)
        out.append(deriv_problem(S, f, difficulty=2, domain=LD,
            stmt=f"Simplify with the laws of logarithms and then differentiate $y = \\ln\\left({L(inner)}\\right)$.",
            hints=["Expand the logarithm of a product, quotient or power before differentiating.", f"$\\ln\\left({L(inner)}\\right) = {L(expanded)}$."],
            solution=[f"$y = {L(expanded)}$.", f"$y' = {L(sp.diff(expanded, x))}$."]))

    # logarithmic differentiation
    for _ in range(11):
        form = rng.choice(['x_x', 'x_sqrtx', 'x_sin', 'sin_x', 'big_product', 'big_quot', 'lin_pow_x'])
        if form == 'x_x':
            f = x**x; dom = LD; why = "$\\ln y = x\\ln x$, so $\\frac{y'}{y} = \\ln x + 1$"
        elif form == 'x_sqrtx':
            f = x**sqrt(x); dom = LD; why = "$\\ln y = \\sqrt{x}\\ln x$, so $\\frac{y'}{y} = \\frac{\\ln x}{2\\sqrt{x}} + \\frac{1}{\\sqrt{x}}$"
        elif form == 'x_sin':
            f = x**sin(x); dom = LD; why = "$\\ln y = \\sin x\\ln x$, so $\\frac{y'}{y} = \\cos x \\ln x + \\frac{\\sin x}{x}$"
        elif form == 'sin_x':
            f = sin(x)**x; dom = (0.5, 2.5); why = "$\\ln y = x\\ln\\sin x$, so $\\frac{y'}{y} = \\ln\\sin x + x\\cot x$"
        elif form == 'big_product':
            a, b, c = rng.randint(2, 4), rng.randint(1, 4), rng.randint(2, 3); f = x**a * sqrt(x + b) * exp(c * x); dom = (0.5, 2); why = f"$\\ln y = {a}\\ln x + \\tfrac12\\ln(x + {b}) + {c}x$, so $\\frac{{y'}}{{y}} = \\frac{{{a}}}{{x}} + \\frac{{1}}{{2(x + {b})}} + {c}$"
        elif form == 'big_quot':
            a, b, c = rng.randint(2, 3), rng.randint(1, 3), rng.randint(1, 3); f = (x**2 + b)**a / sqrt(x**2 + c + 1); dom = (-2, 2); why = f"$\\ln y = {a}\\ln(x^2 + {b}) - \\tfrac12\\ln(x^2 + {c+1})$, so $\\frac{{y'}}{{y}} = \\frac{{{2*a}x}}{{x^2 + {b}}} - \\frac{{x}}{{x^2 + {c+1}}}$"
        else:
            a = rng.randint(1, 3); f = (1 + a * x)**x; dom = (0.5, 2); why = f"$\\ln y = x\\ln(1 + {a}x)$, so $\\frac{{y'}}{{y}} = \\ln(1 + {a}x) + \\frac{{{a}x}}{{1 + {a}x}}$"
        out.append(deriv_problem(S, f, difficulty=3, domain=dom,
            stmt=f"Use logarithmic differentiation to find $y'$ for $y = {L(f)}$.",
            hints=["Take $\\ln$ of both sides, expand with log laws, then differentiate implicitly: $\\frac{y'}{y} = \\dots$.", f"Here {why}."],
            solution=[f"{why}.", f"Multiply by $y$: $y' = {L(f)}\\left({L(sp.simplify(sp.diff(f, x)/f))}\\right)$."]))

    # evaluate at a point
    for _ in range(9):
        f = rng.choice([log(x) / x, x * log(x), log(x**2 + 1), log(rng.randint(2, 4) * x + 1), log(x)**2, x**2 * log(x), log(x) / (x + rng.randint(1, 3)), rng.randint(2, 5) * x * log(x) - x, log(x**2 + rng.randint(2, 5))])
        a = 1 if not f == log(x**2 + 1) else rng.choice([0, 1, 2])
        if f == log(x**2 + 1):
            a = rng.choice([0, 1, 2])
        d = sp.diff(f, x); val = sp.simplify(d.subs(x, a))
        out.append(numeric_problem(S, f"Let $f(x) = {L(f)}$. Find $f'({a})$.", val, difficulty=2,
            hints=["Differentiate first (remember $\\ln 1 = 0$ will simplify things at $x = 1$).", f"$f'(x) = {L(d)}$."],
            solution=[f"$f'(x) = {L(d)}$.", f"$f'({a}) = {L(val)}$."],
            verify={'kind': 'evaluate', 'expr': str(d), 'at': a}))

    # tangent lines
    for _ in range(5):
        f = rng.choice([log(x), x * log(x), log(x**2 + 1), log(rng.randint(2, 3) * x - 1), log(x) + x**2])
        a = 1 if not f.has(x**2 + 1) else 0
        if f.has(x**2 + 1):
            a = rng.choice([0, 1])
        d = sp.diff(f, x); m = sp.simplify(d.subs(x, a)); fa = sp.simplify(f.subs(x, a)); line = sp.expand(fa + m * (x - a))
        out.append(equiv_problem(S, f"Find an equation of the tangent line to $y = {L(f)}$ at $x = {a}$.", line, difficulty=2, domain=(-2, 2),
            hints=["Slope is $y'(a)$; the point is $(a, y(a))$ where $\\ln 1 = 0$ helps.", f"$y' = {L(d)}$."],
            solution=[f"$y({a}) = {L(fa)}$ and $y'({a}) = {L(m)}$.", f"Tangent: $y = {L(fa)} + {L(m)}(x - {a}) = {L(line)}$."],
            verify={'kind': 'tangent', 'expr': str(f), 'at': a}))

    # limits that are derivatives of ln (or the definition of e)
    for _ in range(3):
        k = rng.randint(1, 4)
        f = log(1 + k * x) / x
        out.append(numeric_problem(S, f"Evaluate $\\displaystyle\\lim_{{x \\to 0}} \\dfrac{{\\ln(1 + {k}x)}}{{x}}$ by recognizing it as a derivative.", k, difficulty=3,
            hints=["Compare with $\\lim_{x \\to 0} \\dfrac{g(0 + x) - g(0)}{x} = g'(0)$ for $g(x) = \\ln(1 + kx)$; note $g(0) = 0$.", "$g'(x) = \\dfrac{k}{1 + kx}$."],
            solution=[f"With $g(x) = \\ln(1 + {k}x)$, the limit is $g'(0)$.", f"$g'(x) = \\dfrac{{{k}}}{{1 + {k}x}}$, so $g'(0) = {k}$."],
            verify={'kind': 'limit', 'expr': str(f), 'to': 0}))

    # derivative of ln|x| and general log: MC
    out.append(deriv_mc(S, log(x, 10), rng, difficulty=1, stmt="Which expression is the derivative of $\\log_{10} x$?", distractors=[1 / x, sp.log(10) / x, 1 / (10 * x)],
        hints=["Change of base: $\\log_{10} x = \\dfrac{\\ln x}{\\ln 10}$.", "$\\ln 10$ is just a constant factor."],
        solution=["$\\log_{10} x = \\frac{\\ln x}{\\ln 10}$.", "Differentiating gives $\\frac{1}{x \\ln 10}$."]))
    out.append(deriv_mc(S, log(x), rng, difficulty=1, stmt="Which expression is the derivative of $\\ln|x|$ (for $x \\ne 0$)?", distractors=[1 / sp.Abs(x), sp.log(x) / x, -1 / x],
        hints=["Check the two cases $x > 0$ and $x < 0$ separately.", "For $x < 0$, $\\ln|x| = \\ln(-x)$ and the chain rule gives $\\frac{-1}{-x}$."],
        solution=["For $x > 0$, $(\\ln x)' = 1/x$; for $x < 0$, $(\\ln(-x))' = \\frac{-1}{-x} = \\frac{1}{x}$.", "So $\\frac{d}{dx}\\ln|x| = \\frac{1}{x}$ in both cases."]))
    out.append(label_mc(S, "Logarithmic differentiation is most useful for which kind of function?", [("products, quotients and powers of several factors, or a variable in both base and exponent such as $x^{\\sin x}$", 'ok'), ("polynomials", 'poly'), ("sums of sines and cosines", 'trig'), ("constant functions", 'const')], 'ok', rng, difficulty=1,
        hints=["Logs turn products into sums and powers into multiples.", "A variable exponent cannot be handled by the power rule or the exponential rule alone."],
        solution=["Taking $\\ln$ of a product of powers gives a sum of simple terms that are easy to differentiate.", "For $x^{\\sin x}$ it is the only straightforward method, since neither the power rule nor $(b^x)' = b^x\\ln b$ applies."]))
    return out


def build() -> dict:
    return {
        'power-exp-derivatives': tidy(power_exp_derivatives()),
        'product-quotient-rules': tidy(product_quotient_rules()),
        'trig-derivatives': tidy(trig_derivatives()),
        'chain-rule': tidy(chain_rule()),
        'implicit-differentiation': tidy(implicit_differentiation()),
        'log-derivatives': tidy(log_derivatives()),
    }
