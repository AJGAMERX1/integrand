"""Daily Integral banks, tiers 3-6 (original problems, SymPy-verified), written to data/problems/daily-tier-<n>.json.

tier 3 -> skill antiderivatives            (power-rule antiderivatives, simple definite integrals)
tier 4 -> skill substitution               (u-substitution)
tier 5 -> skill transcendental-integrals   (exponential, log, trig, inverse trig, with substitution)
tier 6 -> skill integration-by-parts       (by parts, trig integrals, trig substitution, partial fractions)

build() returns {'daily-tier-<n>': [problems]} (the key is the bank file name, data/problems/daily-tier-<n>.json);
every problem carries the owning node in its skill field, plus tier and tags ['daily'].
A generator should write these with problemkit.write_bank(problems[0]['skill'], problems, filename=key).
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
from stewart import (P, L, N, coef, signed, nz, pick, label_mc, numeric_problem, equiv_problem, tidy, pow_form, int_ltx,
                     indefinite_problem, definite_problem, nice_anti)
from stewart_ch5 import Item, pool_usub, pool_transc, take, definite_from_item, du_ltx, lin_dom

sin, cos, tan, sec, csc, cot, exp, log, sqrt, pi, E, R = sp.sin, sp.cos, sp.tan, sp.sec, sp.csc, sp.cot, sp.exp, sp.log, sp.sqrt, sp.pi, sp.E, sp.Rational
TAGS = ['daily']


def stamp(problems, tier):
    for p in problems:
        p['tier'] = tier
        p['tags'] = TAGS
        # ids must be unique across all banks; the same integral may also appear in the owning node's bank
        p['id'] = f"daily-tier-{tier}-" + p['id'].split('-')[-1]
    return problems


# ======================================================================
# tier 3: power-rule antiderivatives and simple definite integrals
# ======================================================================

def tier3():
    S = 'antiderivatives'
    rng = seeded('daily-tier-3')
    out = []
    verbs = ["Evaluate", "Find", "Compute"]

    # indefinite: polynomials / powers / rewrites
    for j in range(46):
        form = rng.choice(['poly', 'poly', 'power', 'root', 'recip', 'expand', 'divide', 'table'])
        if form == 'poly':
            f = sum(rng.randint(-5, 5) * x**q for q in range(rng.randint(1, 3))) + nz(rng, -4, 4) * x**rng.randint(2, 5); dom = (-2, 2); diff = 1
            hints = ["Integrate term by term with the power rule $\\int x^n\\,dx = \\frac{x^{n+1}}{n+1} + C$.", "Constants come along for the ride; do not forget $+C$."]
            how = "Apply the power rule to each term."
        elif form == 'power':
            f = nz(rng, -6, 6) * x**rng.choice([R(1, 2), R(3, 2), R(-1, 2), R(2, 3), R(5, 2), -2, -3, R(-1, 3)]); dom = (0.5, 3); diff = 2
            hints = ["The power rule works for any exponent except $-1$: add one to the exponent and divide by the new exponent.", f"Here the exponent becomes ${N(sp.degree(f, x) + 1) if f.is_polynomial(x) else N(list(f.atoms(sp.Pow))[0].exp + 1)}$."]
            how = "Add one to the exponent and divide by it."
        elif form == 'root':
            f = rng.randint(1, 4) * sqrt(x) + nz(rng, -3, 3) * sp.cbrt(x) if rng.random() < 0.5 else rng.randint(1, 5) / sqrt(x) + rng.randint(1, 3); dom = (0.5, 3); diff = 2
            hints = ["Rewrite roots as fractional powers: $\\sqrt{x} = x^{1/2}$, $\\sqrt[3]{x} = x^{1/3}$, $1/\\sqrt{x} = x^{-1/2}$.", "Then use the power rule on each term."]
            how = f"Rewrite: ${pow_form(f)}$, then apply the power rule."
        elif form == 'recip':
            f = rng.randint(1, 6) / x**rng.choice([2, 3, 4]) + nz(rng, -3, 3) * x**rng.choice([1, 2]); dom = (0.5, 3); diff = 2
            hints = ["Write $\\dfrac{1}{x^n}$ as $x^{-n}$ before integrating.", "The power rule then gives $\\dfrac{x^{-n+1}}{-n+1}$."]
            how = f"Rewrite: ${pow_form(f)}$, then apply the power rule."
        elif form == 'expand':
            f0 = rng.choice([(x + rng.randint(1, 4))**2, x * (x**2 - rng.randint(1, 4)), (2 * x - 1) * (x + rng.randint(1, 3)), (sqrt(x) + rng.randint(1, 3))**2, x**2 * (rng.randint(1, 3) - x)**1]); f = sp.expand(f0); dom = (0.5, 3); diff = 2
            hints = ["There is no product rule for integrals: multiply out first.", f"Expanded: ${L(f)}$."]
            how = f"Expand: ${L(f0)} = {L(f)}$, then integrate term by term."
            F = sp.integrate(f, x)
            out.append(indefinite_problem(S, f0, F, difficulty=diff, domain=dom, stmt=f"{pick(rng, verbs)} ${int_ltx(f0)}$.", hints=hints, solution=[how, f"${L(F)} + C$."]))
            continue
        elif form == 'divide':
            num = rng.randint(1, 3) * x**3 + rng.randint(-5, 5) * x + rng.randint(1, 4); den = rng.choice([x, x**2, sqrt(x)]); f0 = num / den; f = sp.expand(f0); dom = (0.5, 3); diff = 3
            hints = ["Divide each term of the numerator by the denominator to get a sum of powers of $x$.", f"That gives ${pow_form(f)}$."]
            how = f"Split the fraction: ${L(f0)} = {pow_form(f)}$."
            F = sp.integrate(f, x)
            out.append(indefinite_problem(S, f0, F, difficulty=diff, domain=dom, stmt=f"{pick(rng, verbs)} ${int_ltx(f0)}$.", hints=hints, solution=[how, f"Integrate term by term: ${L(F)} + C$."]))
            continue
        else:
            a, b = nz(rng, -4, 4), nz(rng, -4, 4)
            f = rng.choice([a * exp(x) + b * x, a * sin(x) + b * x**2, a * cos(x) - b, a * sec(x)**2 + b * x, a / x + b * x**2]); dom = (0.5, 1.2); diff = 2
            hints = ["Use the table of basic antiderivatives: $e^x$, $\\sin x \\to -\\cos x$, $\\cos x \\to \\sin x$, $\\sec^2 x \\to \\tan x$, $1/x \\to \\ln|x|$.", "Handle the power term with the power rule."]
            how = "Each term is a basic antiderivative from the table."
        F = sp.integrate(f, x).subs(sin(x) / cos(x), tan(x))
        out.append(indefinite_problem(S, f, F, difficulty=diff, domain=dom, stmt=f"{pick(rng, verbs)} ${int_ltx(f)}$.", hints=hints, solution=[how, f"${L(F)} + C$.", f"Check: differentiating ${L(F)}$ gives back ${L(f)}$."]))

    # definite integrals
    for j in range(30):
        form = rng.choice(['poly', 'poly', 'power', 'root', 'table'])
        if form == 'poly':
            f = rng.randint(1, 4) * x**rng.randint(1, 3) + rng.randint(-4, 4) * x + rng.randint(-3, 3); a, b = rng.choice([(0, 1), (0, 2), (1, 2), (-1, 1), (1, 3), (0, 3), (-2, 0)]); diff = 1
        elif form == 'power':
            f = rng.randint(1, 4) / x**rng.choice([2, 3]) + rng.randint(0, 2); a, b = rng.choice([(1, 2), (1, 3), (2, 4), (1, 4)]); diff = 2
        elif form == 'root':
            f = rng.randint(1, 3) * sqrt(x) + rng.randint(-2, 2) * x; a, b = rng.choice([(0, 1), (0, 4), (1, 4), (4, 9)]); diff = 2
        else:
            f = rng.choice([rng.randint(1, 3) * exp(x) + rng.randint(0, 3), rng.randint(1, 3) * cos(x), rng.randint(1, 3) * sin(x) + 1, sec(x)**2 * rng.randint(1, 2), rng.randint(1, 3) / x])
            a, b = {True: rng.choice([(0, 1), (0, log(2)), (0, log(3))]), False: None}[bool(f.has(exp))] or (rng.choice([(0, pi / 2), (0, pi), (0, pi / 6)]) if (f.has(sin) or f.has(cos)) else (rng.choice([(0, pi / 4), (0, pi / 3)]) if f.has(sec) else rng.choice([(1, E), (1, 2), (1, E**2)]))); diff = 3
        F = sp.integrate(f, x); val = sp.simplify(sp.integrate(f, (x, a, b)))
        out.append(definite_problem(S, f, a, b, difficulty=diff, value=val, stmt=f"{pick(rng, verbs)} ${int_ltx(f, a, b)}$.",
            hints=["Find an antiderivative $F$, then compute $F(b) - F(a)$ (FTC2).", f"$F(x) = {L(F)}$."],
            solution=[f"An antiderivative is $F(x) = {L(F)}$.", f"$F({L(b)}) - F({L(a)}) = {L(sp.simplify(F.subs(x, b)))} - \\left({L(sp.simplify(F.subs(x, a)))}\\right) = {L(val)}$."]))
    return stamp(out, 3)


# ======================================================================
# tier 4: u-substitution
# ======================================================================

def tier4():
    S = 'substitution'
    rng = seeded('daily-tier-4')
    out = []
    items = take(rng, pool_usub(rng) + pool_usub(rng) + pool_usub(rng), 52)
    for it in items:
        out.append(indefinite_problem(S, it.f, it.F, difficulty=it.diff, domain=it.dom, hints=it.hints(), solution=it.solution()))
    count = 0
    for it in take(rng, pool_usub(rng) + pool_usub(rng), 80):
        p = definite_from_item(S, it, rng)
        if p:
            out.append(p); count += 1
        if count >= 22:
            break
    return stamp(out, 4)


# ======================================================================
# tier 5: exponential, logarithmic, trigonometric integrals
# ======================================================================

def tier5():
    S = 'transcendental-integrals'
    rng = seeded('daily-tier-5')
    out = []
    items = take(rng, pool_transc(rng) + pool_transc(rng) + pool_transc(rng), 54)
    for it in items:
        out.append(indefinite_problem(S, it.f, it.F, difficulty=it.diff, domain=it.dom, hints=it.hints(), solution=it.solution()))
    count = 0
    for it in take(rng, pool_transc(rng) + pool_transc(rng), 90):
        p = definite_from_item(S, it, rng)
        if p:
            out.append(p); count += 1
        if count >= 22:
            break
    return stamp(out, 5)


# ======================================================================
# tier 6: integration by parts, trig integrals, trig substitution, partial fractions
# ======================================================================

class T6:
    """f: integrand, F: antiderivative (hand-written where sympy's form is clumsy), dom, difficulty, hints, solution."""
    def __init__(self, f, F, dom, diff, hints, sol, cat):
        self.f, self.F, self.dom, self.diff, self.h, self.s, self.cat = sp.sympify(f), nice_anti(sp.sympify(F)), dom, diff, hints, sol, cat


def by_parts(f, uu, dv, dom, diff, extra=None):
    """Build a by-parts item from the choice u = uu, dv = dv dx."""
    du = sp.diff(uu, x); v = sp.integrate(dv, x)
    F = sp.simplify(uu * v - sp.integrate(v * du, x))
    du_l = 'dx' if du == 1 else (f"\\left({L(du)}\\right)dx" if isinstance(du, sp.Add) else f"{L(du)}\\,dx")
    hints = [f"Integrate by parts with $u = {L(uu)}$ and $dv = {L(dv)}\\,dx$.", f"Then $du = {du_l}$ and $v = {L(v)}$; use $\\int u\\,dv = uv - \\int v\\,du$."]
    sol = [f"Let $u = {L(uu)}$, $dv = {L(dv)}\\,dx$, so $du = {du_l}$ and $v = {L(v)}$.",
           f"$\\displaystyle\\int u\\,dv = uv - \\int v\\,du = {L(uu * v)} - \\int {L(sp.simplify(v * du))}\\,dx$."] + (extra or []) + [f"$= {L(F)} + C$."]
    return T6(f, F, dom, diff, hints, sol, 'parts')


def pool_t6(rng):
    k = rng.randint(2, 4); c = rng.randint(1, 4); a = rng.choice([1, 2, 3]); n_ = rng.randint(2, 4)
    items = []
    # ---- integration by parts ----
    items += [
        by_parts(x * exp(k * x), x, exp(k * x), (-1, 1), 1),
        by_parts(x * exp(-x), x, exp(-x), (-1, 1), 1),
        by_parts(x * sin(k * x), x, sin(k * x), (-2, 2), 1),
        by_parts(x * cos(a * x), x, cos(a * x), (-2, 2), 1),
        by_parts(x * log(x), log(x), x, (0.5, 3), 2),
        by_parts(log(x), log(x), 1 + 0 * x, (0.5, 3), 1),
        by_parts(x**n_ * log(x), log(x), x**n_, (0.5, 3), 2),
        by_parts(sp.atan(x), sp.atan(x), 1 + 0 * x, (-2, 2), 2),
        by_parts(sp.asin(x), sp.asin(x), 1 + 0 * x, (-0.9, 0.9), 2),
        by_parts(x * sec(x)**2, x, sec(x)**2, (-1, 1), 2),
        by_parts(log(x) / x**2, log(x), x**(-2), (0.5, 3), 2),
        by_parts(sqrt(x) * log(x), log(x), sqrt(x), (0.5, 3), 2),
        by_parts(x * exp(x) * 1, x, exp(x), (-1, 1), 1),
        by_parts(log(x)**2, log(x)**2, 1 + 0 * x, (0.5, 3), 3, extra=["The remaining integral $\\int 2\\ln x\\,dx$ needs a second integration by parts: $2(x\\ln x - x)$."]),
        by_parts(x**2 * exp(x), x**2, exp(x), (-1, 1), 3, extra=["The remaining integral $\\int 2xe^x\\,dx$ needs a second integration by parts, giving $2xe^x - 2e^x$."]),
        by_parts(x**2 * cos(x), x**2, cos(x), (-2, 2), 3, extra=["Integrate $\\int 2x\\sin x\\,dx$ by parts again: $-2x\\cos x + 2\\sin x$."]),
        by_parts(x**2 * sin(x), x**2, sin(x), (-2, 2), 3, extra=["Integrate $\\int 2x\\cos x\\,dx$ by parts again: $2x\\sin x + 2\\cos x$."]),
        by_parts(log(c + x) if False else log(x + c), log(x + c), 1 + 0 * x, (0.5, 3), 2),
        by_parts(x * log(x)**1 * 2, 2 * log(x), x, (0.5, 3), 2),
        by_parts(x * cos(x)**1 * 1 + 0, x, cos(x), (-2, 2), 1),
        by_parts(x**2 * log(x) * 1, log(x), x**2, (0.5, 3), 2),
        by_parts(sp.atan(x) * x, sp.atan(x), x, (-2, 2), 3, extra=["Simplify $\\int \\frac{x^2}{2(1 + x^2)}\\,dx = \\frac{1}{2}\\int \\left(1 - \\frac{1}{1 + x^2}\\right)dx = \\frac{x}{2} - \\frac{\\arctan x}{2}$."]),
    ]
    for f, F, extra in [(exp(x) * sin(x), exp(x) * (sin(x) - cos(x)) / 2, "Apply parts twice (with $u = e^x$ both times); the original integral reappears. Solve the resulting equation $I = e^x\\sin x - e^x\\cos x - I$."),
                        (exp(x) * cos(x), exp(x) * (sin(x) + cos(x)) / 2, "Apply parts twice; the original integral $I$ reappears: $I = e^x\\sin x + e^x\\cos x - I$, so $I = \\frac{e^x(\\sin x + \\cos x)}{2}$."),
                        (exp(k * x) * sin(x), exp(k * x) * (k * sin(x) - cos(x)) / (k * k + 1), f"Apply parts twice with $u = e^{{{k}x}}$; the original integral $I$ reappears and $I = \\dfrac{{e^{{{k}x}}({k}\\sin x - \\cos x)}}{{{k*k+1}}}$.")]:
        items.append(T6(f, F, (-1, 1), 3, ["This needs integration by parts twice; keep $u$ as the exponential each time.", "After the second round the original integral reappears on the right; move it to the left and solve."],
                        [extra, f"$= {L(F)} + C$."], 'parts'))

    # ---- trigonometric integrals ----
    trig = [
        (sin(x)**3, cos(x)**3 / 3 - cos(x), (-3, 3), 2, ["Odd power of sine: save one $\\sin x$ and convert the rest with $\\sin^2 x = 1 - \\cos^2 x$.", "Then substitute $u = \\cos x$."], ["$\\sin^3 x = (1 - \\cos^2 x)\\sin x$; let $u = \\cos x$, $du = -\\sin x\\,dx$.", "$\\int (1 - u^2)(-du) = -u + \\frac{u^3}{3}$."]),
        (cos(x)**3, sin(x) - sin(x)**3 / 3, (-3, 3), 2, ["Odd power of cosine: save one $\\cos x$ and convert the rest with $\\cos^2 x = 1 - \\sin^2 x$.", "Substitute $u = \\sin x$."], ["$\\cos^3 x = (1 - \\sin^2 x)\\cos x$; let $u = \\sin x$.", "$\\int (1 - u^2)\\,du = u - \\frac{u^3}{3}$."]),
        (sin(x)**2, x / 2 - sin(2 * x) / 4, (-3, 3), 2, ["Use the half-angle identity $\\sin^2 x = \\frac{1 - \\cos 2x}{2}$.", "Then integrate term by term."], ["$\\sin^2 x = \\frac{1}{2} - \\frac{1}{2}\\cos 2x$.", "$\\int \\frac{1}{2}\\,dx - \\int \\frac{\\cos 2x}{2}\\,dx = \\frac{x}{2} - \\frac{\\sin 2x}{4}$."]),
        (cos(x)**2, x / 2 + sin(2 * x) / 4, (-3, 3), 2, ["Use the half-angle identity $\\cos^2 x = \\frac{1 + \\cos 2x}{2}$.", "Then integrate term by term."], ["$\\cos^2 x = \\frac{1}{2} + \\frac{1}{2}\\cos 2x$.", "$\\int \\frac{1}{2}\\,dx + \\int \\frac{\\cos 2x}{2}\\,dx = \\frac{x}{2} + \\frac{\\sin 2x}{4}$."]),
        (cos(k * x)**2, x / 2 + sin(2 * k * x) / (4 * k), (-3, 3), 2, [f"Use $\\cos^2\\theta = \\frac{{1 + \\cos 2\\theta}}{{2}}$ with $\\theta = {k}x$.", f"Then $\\int \\cos({2*k}x)\\,dx = \\frac{{\\sin {2*k}x}}{{{2*k}}}$."], [f"$\\cos^2({k}x) = \\frac{{1}}{{2}} + \\frac{{1}}{{2}}\\cos({2*k}x)$.", f"Integrating: $\\frac{{x}}{{2}} + \\frac{{\\sin {2*k}x}}{{{4*k}}}$."]),
        (sin(x)**2 * cos(x)**3, sin(x)**3 / 3 - sin(x)**5 / 5, (-3, 3), 3, ["The cosine power is odd: keep one $\\cos x$ and write $\\cos^2 x = 1 - \\sin^2 x$.", "Substitute $u = \\sin x$."], ["$\\sin^2 x\\cos^3 x = \\sin^2 x(1 - \\sin^2 x)\\cos x$; with $u = \\sin x$ this is $\\int (u^2 - u^4)\\,du$.", "$= \\frac{u^3}{3} - \\frac{u^5}{5}$."]),
        (sin(x)**3 * cos(x)**2, cos(x)**5 / 5 - cos(x)**3 / 3, (-3, 3), 3, ["The sine power is odd: keep one $\\sin x$ and write $\\sin^2 x = 1 - \\cos^2 x$.", "Substitute $u = \\cos x$, $du = -\\sin x\\,dx$."], ["$\\int (1 - \\cos^2 x)\\cos^2 x\\sin x\\,dx = -\\int (u^2 - u^4)\\,du$ with $u = \\cos x$.", "$= -\\frac{u^3}{3} + \\frac{u^5}{5}$."]),
        (tan(x)**2, tan(x) - x, (-1, 1), 2, ["Use $\\tan^2 x = \\sec^2 x - 1$.", "Both pieces are basic antiderivatives."], ["$\\int (\\sec^2 x - 1)\\,dx$.", "$= \\tan x - x$."]),
        (sec(x)**4, tan(x) + tan(x)**3 / 3, (-1, 1), 3, ["Even power of secant: save $\\sec^2 x$ and write the rest as $1 + \\tan^2 x$.", "Substitute $u = \\tan x$, $du = \\sec^2 x\\,dx$."], ["$\\sec^4 x = (1 + \\tan^2 x)\\sec^2 x$; with $u = \\tan x$ this is $\\int (1 + u^2)\\,du$.", "$= u + \\frac{u^3}{3}$."]),
        (tan(x) * sec(x)**3, sec(x)**3 / 3, (-1, 1), 2, ["Save a factor $\\sec x\\tan x$ (the derivative of $\\sec x$).", "Substitute $u = \\sec x$."], ["$\\tan x\\sec^3 x = \\sec^2 x\\cdot(\\sec x\\tan x)$; with $u = \\sec x$ this is $\\int u^2\\,du$.", "$= \\frac{u^3}{3}$."]),
        (tan(x)**3, tan(x)**2 / 2 + log(cos(x)), (-1, 1), 3, ["Write $\\tan^3 x = \\tan x(\\sec^2 x - 1)$.", "The first piece uses $u = \\tan x$; the second is $\\int \\tan x\\,dx = -\\ln|\\cos x|$."], ["$\\int \\tan x\\sec^2 x\\,dx - \\int \\tan x\\,dx$.", "$= \\frac{\\tan^2 x}{2} + \\ln|\\cos x|$."]),
        (sin(2 * x) * cos(3 * x), cos(x) / 2 - cos(5 * x) / 10, (-3, 3), 3, ["Use the product-to-sum identity $\\sin A\\cos B = \\frac{1}{2}[\\sin(A - B) + \\sin(A + B)]$.", "Then integrate the two sines."], ["$\\sin 2x\\cos 3x = \\frac{1}{2}[\\sin(-x) + \\sin 5x] = \\frac{1}{2}[\\sin 5x - \\sin x]$.", "$\\int = \\frac{1}{2}\\left[-\\frac{\\cos 5x}{5} + \\cos x\\right]$."]),
        (sin(x)**2 * cos(x)**2, x / 8 - sin(4 * x) / 32, (-3, 3), 3, ["Use $\\sin x\\cos x = \\frac{1}{2}\\sin 2x$, then a half-angle identity.", "$\\sin^2 2x = \\frac{1 - \\cos 4x}{2}$."], ["$\\sin^2 x\\cos^2 x = \\frac{1}{4}\\sin^2 2x = \\frac{1}{8}(1 - \\cos 4x)$.", "$\\int = \\frac{x}{8} - \\frac{\\sin 4x}{32}$."]),
        (sec(x)**2 * tan(x)**2, tan(x)**3 / 3, (-1, 1), 2, ["$\\sec^2 x\\,dx$ is the differential of $\\tan x$.", "Substitute $u = \\tan x$."], ["With $u = \\tan x$, $du = \\sec^2 x\\,dx$: $\\int u^2\\,du$.", "$= \\frac{u^3}{3}$."]),
        (cos(x)**5, sin(x) - 2 * sin(x)**3 / 3 + sin(x)**5 / 5, (-3, 3), 3, ["Odd power: $\\cos^5 x = (1 - \\sin^2 x)^2\\cos x$.", "Substitute $u = \\sin x$ and expand."], ["$\\int (1 - u^2)^2\\,du = \\int (1 - 2u^2 + u^4)\\,du$.", "$= u - \\frac{2u^3}{3} + \\frac{u^5}{5}$."]),
        (sin(a * x)**3 if a > 1 else sin(2 * x)**3, (cos(a * x)**3 / 3 - cos(a * x)) / a if a > 1 else (cos(2 * x)**3 / 3 - cos(2 * x)) / 2, (-3, 3), 3, ["Odd power of sine: keep one sine factor and convert the rest to cosines.", "Substitute $u = \\cos(\\cdot)$ and remember the inner constant."], ["Write $\\sin^3\\theta = (1 - \\cos^2\\theta)\\sin\\theta$ with $\\theta$ the inner multiple of $x$.", "With $u = \\cos\\theta$, $du = -\\sin\\theta\\,d\\theta$, the integral is $\\frac{1}{(\\text{inner constant})}\\left(\\frac{u^3}{3} - u\\right)$."]),
        (sec(x), log(sec(x) + tan(x)), (-1, 1), 3, ["Multiply numerator and denominator by $\\sec x + \\tan x$.", "The numerator then equals the derivative of the denominator."], ["$\\sec x = \\frac{\\sec x(\\sec x + \\tan x)}{\\sec x + \\tan x}$; let $u = \\sec x + \\tan x$, $du = (\\sec x\\tan x + \\sec^2 x)\\,dx$.", "$\\int \\frac{du}{u} = \\ln|\\sec x + \\tan x|$."]),
        (sin(x)**4, 3 * x / 8 - sin(2 * x) / 4 + sin(4 * x) / 32, (-3, 3), 3, ["Apply the half-angle identity twice: $\\sin^4 x = \\left(\\frac{1 - \\cos 2x}{2}\\right)^2$.", "Expand and use $\\cos^2 2x = \\frac{1 + \\cos 4x}{2}$."], ["$\\sin^4 x = \\frac{1}{4}(1 - 2\\cos 2x + \\cos^2 2x) = \\frac{3}{8} - \\frac{\\cos 2x}{2} + \\frac{\\cos 4x}{8}$.", "Integrate: $\\frac{3x}{8} - \\frac{\\sin 2x}{4} + \\frac{\\sin 4x}{32}$."]),
    ]
    for f, F, dom, diff, hints, sol in trig:
        items.append(T6(f, F, dom, diff, hints, sol + [f"Result: ${L(F)} + C$."], 'trig'))

    # ---- trigonometric substitution ----
    aa = rng.choice([1, 2, 3])
    tsub = [
        (sqrt(aa**2 - x**2), x * sqrt(aa**2 - x**2) / 2 + aa**2 * sp.asin(x / aa) / 2, (-0.9 * aa, 0.9 * aa), 3, f"x = {aa}\\sin\\theta", f"the integral becomes $\\int {aa**2}\\cos^2\\theta\\,d\\theta = \\frac{{{aa**2}}}{{2}}(\\theta + \\sin\\theta\\cos\\theta)$"),
        (x**2 / sqrt(aa**2 - x**2), -x * sqrt(aa**2 - x**2) / 2 + aa**2 * sp.asin(x / aa) / 2, (-0.9 * aa, 0.9 * aa), 3, f"x = {aa}\\sin\\theta", f"the integral becomes $\\int {aa**2}\\sin^2\\theta\\,d\\theta = \\frac{{{aa**2}}}{{2}}(\\theta - \\sin\\theta\\cos\\theta)$"),
        (1 / (aa**2 + x**2)**R(3, 2), x / (aa**2 * sqrt(aa**2 + x**2)), (-2, 2), 3, f"x = {aa}\\tan\\theta", f"$({aa**2} + x^2)^{{3/2}} = {aa**3}\\sec^3\\theta$ and $dx = {aa}\\sec^2\\theta\\,d\\theta$, so the integral becomes $\\frac{{1}}{{{aa**2}}}\\int \\cos\\theta\\,d\\theta = \\frac{{\\sin\\theta}}{{{aa**2}}}$"),
        (1 / (x**2 * sqrt(x**2 + aa**2)), -sqrt(x**2 + aa**2) / (aa**2 * x), (0.5, 3), 3, f"x = {aa}\\tan\\theta", f"the integral becomes $\\frac{{1}}{{{aa**2}}}\\int \\frac{{\\cos\\theta}}{{\\sin^2\\theta}}\\,d\\theta = -\\frac{{1}}{{{aa**2}\\sin\\theta}}$"),
        (1 / sqrt(x**2 + aa**2), log(x + sqrt(x**2 + aa**2)), (-2, 2), 3, f"x = {aa}\\tan\\theta", "the integral becomes $\\int \\sec\\theta\\,d\\theta = \\ln|\\sec\\theta + \\tan\\theta|$"),
        (1 / sqrt(x**2 - aa**2), log(x + sqrt(x**2 - aa**2)), (aa + 0.5, aa + 3), 3, f"x = {aa}\\sec\\theta", "the integral becomes $\\int \\sec\\theta\\,d\\theta = \\ln|\\sec\\theta + \\tan\\theta|$"),
        (sqrt(x**2 + aa**2), x * sqrt(x**2 + aa**2) / 2 + aa**2 * log(x + sqrt(x**2 + aa**2)) / 2, (-2, 2), 3, f"x = {aa}\\tan\\theta", f"the integral becomes ${aa**2}\\int \\sec^3\\theta\\,d\\theta = \\frac{{{aa**2}}}{{2}}(\\sec\\theta\\tan\\theta + \\ln|\\sec\\theta + \\tan\\theta|)$"),
        (1 / (x**2 * sqrt(aa**2 - x**2)), -sqrt(aa**2 - x**2) / (aa**2 * x), (0.3 * aa, 0.9 * aa), 3, f"x = {aa}\\sin\\theta", f"the integral becomes $\\frac{{1}}{{{aa**2}}}\\int \\csc^2\\theta\\,d\\theta = -\\frac{{\\cot\\theta}}{{{aa**2}}}$"),
        (x**2 / sqrt(x**2 + aa**2), x * sqrt(x**2 + aa**2) / 2 - aa**2 * log(x + sqrt(x**2 + aa**2)) / 2, (-2, 2), 3, f"x = {aa}\\tan\\theta", f"the integral becomes ${aa**2}\\int \\tan^2\\theta\\sec\\theta\\,d\\theta = {aa**2}\\int(\\sec^3\\theta - \\sec\\theta)\\,d\\theta$"),
        (sqrt(aa**2 - x**2) / x**2, -sqrt(aa**2 - x**2) / x - sp.asin(x / aa), (0.3 * aa, 0.9 * aa), 3, f"x = {aa}\\sin\\theta", "the integral becomes $\\int \\cot^2\\theta\\,d\\theta = \\int(\\csc^2\\theta - 1)\\,d\\theta = -\\cot\\theta - \\theta$"),
        (1 / sqrt(4 * aa**2 - x**2) if aa < 3 else 1 / sqrt(16 - x**2), sp.asin(x / (2 * aa)) if aa < 3 else sp.asin(x / 4), (-1.5 * aa, 1.5 * aa) if aa < 3 else (-3, 3), 2, f"x = {2*aa if aa < 3 else 4}\\sin\\theta", "the integral becomes $\\int d\\theta = \\theta$"),
        (x**3 / sqrt(x**2 + aa**2), (x**2 - 2 * aa**2) * sqrt(x**2 + aa**2) / 3, (-2, 2), 3, f"u = x^2 + {aa**2}", "(a plain substitution also works here) the integral becomes $\\frac{1}{2}\\int \\frac{u - a^2}{\\sqrt{u}}\\,du$"),
    ]
    for f, F, dom, diff, subst, how in tsub:
        items.append(T6(f, F, dom, diff, [f"Use the trigonometric substitution ${subst}$ and simplify the root with a Pythagorean identity.", "After integrating in $\\theta$, draw the reference triangle to convert back to $x$."],
                        [f"With ${subst}$, {how}.", f"Returning to $x$ via the triangle: ${L(F)} + C$."], 'trigsub'))

    # ---- partial fractions ----
    p_, q_ = sorted(rng.sample([-3, -2, -1, 1, 2, 3, 4], 2))
    pf = []
    def pf_item(f, dom, diff, decomposition):
        F = sp.integrate(sp.apart(f, x), x)
        pf.append(T6(f, F, dom, diff, ["Factor the denominator and write the integrand as a sum of partial fractions.", f"The decomposition is ${L(decomposition)}$."],
                     [f"Partial fractions: ${L(f)} = {L(decomposition)}$.", "Integrate each term (each gives a logarithm, a power, or an arctangent).", f"$= {L(F)} + C$."], 'pf'))
    f = 1 / ((x - p_) * (x - q_)); pf_item(f, (q_ + 0.5, q_ + 3), 2, sp.apart(f, x))
    f = (x + c) / ((x - p_) * (x - q_)); pf_item(f, (q_ + 0.5, q_ + 3), 2, sp.apart(f, x))
    f = 1 / (x**2 - aa**2); pf_item(f, (aa + 0.5, aa + 3), 2, sp.apart(f, x))
    f = (2 * x + c) / (x * (x + k)); pf_item(f, (0.5, 3), 2, sp.apart(f, x))
    f = x**2 / (x**2 - 1); pf_item(f, (1.5, 4), 3, sp.apart(f, x))
    f = 1 / (x * (x**2 + 1)); pf_item(f, (0.5, 3), 3, sp.apart(f, x))
    f = (x - 1) / (x**2 + 2 * x) if True else None; pf_item(f, (0.5, 3), 2, sp.apart(f, x))
    f = (x**2 + 1) / (x * (x - 1)**2); pf_item(f, (1.5, 4), 3, sp.apart(f, x))
    f = (x + 2) / (x**2 + 4 * x + 3); pf_item(f, (0.5, 3), 2, sp.apart(f, x))
    f = (3 * x + 1) / ((x - 1) * (x + 2)) if True else None; pf_item(f, (1.5, 4), 2, sp.apart(f, x))
    f = 1 / (x**2 * (x + 1)); pf_item(f, (0.5, 3), 3, sp.apart(f, x))
    f = (x**3 + 1) / (x**2 - 4) if True else None; pf_item(f, (2.5, 5), 3, sp.apart(f, x))
    f = (5 * x - 1) / (x**2 - x - 2); pf_item(f, (2.5, 5), 2, sp.apart(f, x))
    f = 1 / (x**3 + x) * 2 if False else (x + 3) / (x**3 + x); pf_item(f, (0.5, 3), 3, sp.apart(f, x))
    items += pf
    return items


def tier6():
    S = 'integration-by-parts'
    rng = seeded('daily-tier-6')
    out = []
    items = pool_t6(rng) + pool_t6(rng)
    rng.shuffle(items)
    seen = set()
    for it in items:
        key = str(it.f)
        if key in seen:
            continue
        seen.add(key)
        out.append(indefinite_problem(S, it.f, it.F, difficulty=it.diff, domain=it.dom, hints=it.h, solution=it.s))

    # definite versions with clean values
    defs = [
        (x * exp(x), 0, 1, 'parts'), (log(x), 1, E, 'parts'), (x * sin(x), 0, pi, 'parts'), (sp.atan(x), 0, 1, 'parts'), (x * cos(x), 0, pi / 2, 'parts'),
        (x * exp(-x), 0, 1, 'parts'), (x * log(x), 1, E, 'parts'), (x**2 * exp(x), 0, 1, 'parts'), (log(x) / x**2, 1, E, 'parts'),
        (sin(x)**2, 0, pi / 2, 'trig'), (cos(x)**3, 0, pi / 2, 'trig'), (sin(x)**3, 0, pi, 'trig'), (tan(x)**2, 0, pi / 4, 'trig'), (sec(x)**4, 0, pi / 4, 'trig'), (cos(x)**2, 0, pi, 'trig'), (sin(x)**2 * cos(x)**3, 0, pi / 2, 'trig'),
        (sqrt(4 - x**2), 0, 2, 'trigsub'), (sqrt(9 - x**2), 0, 3, 'trigsub'), (1 / (1 + x**2)**R(3, 2), 0, 1, 'trigsub'), (x**2 / sqrt(1 - x**2), 0, R(1, 2), 'trigsub'), (1 / sqrt(x**2 + 1), 0, 1, 'trigsub'), (sqrt(1 - x**2), 0, 1, 'trigsub'),
        (1 / ((x + 1) * (x + 2)), 0, 1, 'pf'), (1 / (x**2 - 1), 2, 3, 'pf'), ((x + 1) / (x * (x + 3)), 1, 2, 'pf'), (x**2 / (x**2 - 1), 2, 3, 'pf'), (1 / (x * (x**2 + 1)), 1, 2, 'pf'), ((2 * x + 1) / (x**2 + 3 * x + 2), 0, 1, 'pf'),
    ]
    for f, a, b, cat in defs:
        val = sp.simplify(sp.integrate(f, (x, a, b)))
        F = nice_anti(sp.integrate(sp.apart(f, x) if cat == 'pf' else f, x))
        method = {'parts': 'integration by parts', 'trig': 'a trigonometric identity (or saving one factor and substituting)', 'trigsub': 'a trigonometric substitution', 'pf': 'partial fractions'}[cat]
        out.append(definite_problem(S, f, a, b, difficulty=3, value=val,
            hints=[f"Find an antiderivative using {method}, then apply FTC2.", f"An antiderivative is $F(x) = {L(F)}$."],
            solution=[f"Using {method}, $F(x) = {L(F)}$.", f"$F({L(b)}) - F({L(a)}) = {L(val)}$."]))
    return stamp(out, 6)


def build() -> dict:
    return {
        'daily-tier-3': tidy(tier3()),
        'daily-tier-4': tidy(tier4()),
        'daily-tier-5': tidy(tier5()),
        'daily-tier-6': tidy(tier6()),
    }
