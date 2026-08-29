"""
build_question_bank.py

Generates exactly 100 real, verified AP-Calculus-style questions per chapter
(34 easy / 33 medium / 33 hard), saving the result to question_bank.csv.

Every question is built from an actual calculus computation (power rule,
chain rule, implicit differentiation, related rates, curve sketching,
integration, separable differential equations, area/volume applications)
with randomized parameters, so the correct answer is always mathematically
verified rather than pulled from an unrelated trivia API.
"""

import random
import csv
from fractions import Fraction

# ---------------------------------------------------------------------
# Formatting helpers -- house style matches the app's existing plain-text
# math notation (unicode superscripts, e.g. "x\u00b2", "(3x+1)\u2075").
# ---------------------------------------------------------------------
import random
import sympy as sp

SUP = {'0':'\u2070','1':'\u00b9','2':'\u00b2','3':'\u00b3','4':'\u2074',
       '5':'\u2075','6':'\u2076','7':'\u2077','8':'\u2078','9':'\u2079','-':'\u207b'}

def sup(n):
    return ''.join(SUP[c] for c in str(n))

def signed(n, first=False):
    """Format a numeric coefficient's sign/magnitude prefix piece."""
    if first:
        return f"-{abs(n)}" if n < 0 else f"{n}"
    return f" - {abs(n)}" if n < 0 else f" + {n}"

def fmt_poly(terms, var='x'):
    """terms: list of (coeff, power) descending by power. Returns display string."""
    parts = []
    first = True
    for c, p in terms:
        if c == 0:
            continue
        if p == 0:
            mag = f"{abs(c)}"
        elif p == 1:
            mag = var if abs(c) == 1 else f"{abs(c)}{var}"
        else:
            mag = f"{var}{sup(p)}" if abs(c) == 1 else f"{abs(c)}{var}{sup(p)}"
        if first:
            parts.append(("-" if c < 0 else "") + mag)
            first = False
        else:
            parts.append((" - " if c < 0 else " + ") + mag)
    return ''.join(parts) if parts else "0"

def fmt_linear(a, b, var='x'):
    """a*var + b, a != 0"""
    if a == 1:
        s = var
    elif a == -1:
        s = f"-{var}"
    else:
        s = f"{a}{var}"
    if b > 0:
        s += f" + {b}"
    elif b < 0:
        s += f" - {abs(b)}"
    return s

def rnz(lo, hi, exclude=(0,)):
    while True:
        v = random.randint(lo, hi)
        if v not in exclude:
            return v

def fmt_frac_term(num, den, power, var='x'):
    """Format (num/den)*var^power cleanly, e.g. num=1,den=1,power=2 -> 'x²'."""
    p = "" if power == 0 else (var if power == 1 else f"{var}{sup(power)}")
    if den == 1:
        if num == 1:
            coef = "" if p else "1"
        elif num == -1:
            coef = "-" if p else "-1"
        else:
            coef = f"{num}"
    else:
        coef = f"({num}/{den})"
    return f"{coef}{p}" if p else coef

def plus(n):
    """' + n' or ' - |n|' for appending a constant term."""
    return f" + {n}" if n >= 0 else f" - {abs(n)}"

def poly_terms_to_sympy(terms, x):
    return sum(c * x**p for c, p in terms)


# ---------------------------------------------------------------------
# ch0_limits
# ---------------------------------------------------------------------

def ch0_easy():
    # direct substitution into a polynomial limit
    a = random.randint(-4, 4)
    terms = [(rnz(-5,5), 2), (rnz(-6,6), 1), (rnz(-8,8), 0)]
    val = sum(c * a**p for c, p in terms)
    q = f"Evaluate lim(x\u2192{a}) [{fmt_poly(terms)}]"
    correct = str(val)
    wrongs = {str(val + random.choice([-2,-1,1,2])) for _ in range(1)}
    while len(wrongs) < 3:
        wrongs.add(str(val + random.choice([-6,-5,-4,-3,3,4,5,6])))
    opts = [correct] + list(wrongs)[:3]
    return q, opts, correct, "easy"

def ch0_medium():
    # factorable limit: (x^2 - a^2)/(x-a) -> 2a, or similar cancellation
    a = rnz(-6, 6)
    b = rnz(1, 5)
    # lim x->a of (x^2 - (a+b)x + ab)/(x-a) -> (a-(a+b)) ... simpler: (x-a)(x-(a+b))/(x-a) -> x-(a+b) at x=a -> a-(a+b) = -b
    q = f"Evaluate lim(x\u2192{a}) [(x\u00b2 {'-' if (a+ (a+b))>=0 else '+'} {abs(2*a+b)}x + {a*(a+b)})/(x - {a})]" if False else None
    # build cleanly: factors (x-a)(x-r)
    r = a + b if random.random() < 0.5 else a - b
    b_coef = -(a + r)
    c_coef = a * r
    terms = [(1,2),(b_coef,1),(c_coef,0)]
    numer = fmt_poly(terms)
    denom = fmt_linear(1, -a)
    q = f"Evaluate lim(x\u2192{a}) [({numer})/({denom})]"
    val = a - r  # after cancelling (x-a), left with (x-r), eval at a
    correct = str(val)
    wrongs = {str(val + d) for d in (1,-1,2,-2) }
    wrongs.discard(str(val))
    opts = [correct] + list(wrongs)[:3]
    return q, opts, correct, "medium"

def ch0_hard():
    kind = random.choice(["trig", "rational_inf", "onesided"])
    if kind == "trig":
        a = rnz(1,6)
        q = f"Evaluate lim(x\u21920) [sin({a}x)/x]"
        correct = str(a)
        wrongs = [str(1), str(a*2), str(0)]
        opts = [correct] + wrongs
        return q, opts, correct, "hard"
    elif kind == "rational_inf":
        # lim x->inf of (p x^2 + ...)/(q x^2 + ...) -> p/q ; or degree num < denom -> 0; or > -> DNE(inf)
        case = random.choice(["equal", "less", "greater"])
        if case == "equal":
            p = rnz(1,6); qc = rnz(1,6)
            num = fmt_poly([(p,2),(rnz(-9,9),1),(rnz(-9,9),0)])
            den = fmt_poly([(qc,2),(rnz(-9,9),1),(rnz(-9,9),0)])
            q_txt = f"Evaluate lim(x\u2192\u221e) [({num})/({den})]"
            from fractions import Fraction
            frac = Fraction(p, qc)
            inv = Fraction(qc, p)
            correct = f"{frac.numerator}/{frac.denominator}" if frac.denominator != 1 else str(frac.numerator)
            wrong_inv = f"{inv.numerator}/{inv.denominator}" if inv.denominator != 1 else str(inv.numerator)
            opts = [correct, "0", "\u221e", wrong_inv]
            return q_txt, opts, correct, "hard"
        elif case == "less":
            p = rnz(1,6)
            num = fmt_poly([(p,1),(rnz(-9,9),0)])
            qc = rnz(1,6)
            den = fmt_poly([(qc,2),(rnz(-9,9),1),(rnz(-9,9),0)])
            q_txt = f"Evaluate lim(x\u2192\u221e) [({num})/({den})]"
            correct = "0"
            opts = [correct, str(p), f"{p}/{qc}", "\u221e"]
            return q_txt, opts, correct, "hard"
        else:
            p = rnz(1,6)
            num = fmt_poly([(p,2),(rnz(-9,9),1),(rnz(-9,9),0)])
            qc = rnz(1,6)
            den = fmt_poly([(qc,1),(rnz(-9,9),0)])
            q_txt = f"Evaluate lim(x\u2192\u221e) [({num})/({den})]"
            correct = "\u221e (does not exist as a finite limit)"
            opts = [correct, "0", f"{p}/{qc}", "1"]
            return q_txt, opts, correct, "hard"
    else:
        # piecewise continuity: find k
        a = rnz(-4,4)
        m = rnz(2,6)
        b = rnz(-6,6)
        # f(x) = mx+b for x<a, f(x) = k for x>=a ; continuity requires k = m*a+b
        k = m*a + b
        q_txt = (f"For what value of k is f(x) continuous at x = {a}, given "
                  f"f(x) = {fmt_linear(m,b)} for x < {a} and f(x) = k for x \u2265 {a}?")
        correct = str(k)
        wrongs = {str(k+d) for d in (1,-1,2)}
        opts = [correct] + list(wrongs)
        return q_txt, opts, correct, "hard"


# ---------------------------------------------------------------------
# ch1_diff_basics
# ---------------------------------------------------------------------

def _poly_and_deriv(n_terms=3, max_pow=4):
    powers = random.sample(range(1, max_pow+1), min(n_terms, max_pow))
    terms = [(rnz(-9,9), p) for p in powers]
    if random.random() < 0.6:
        terms.append((rnz(-9,9), 0))
    terms.sort(key=lambda t: -t[1])
    deriv = [(c*p, p-1) for c,p in terms if p >= 1]
    deriv = [(c,p) for c,p in deriv if c != 0]
    if not deriv:
        deriv = [(0,0)]
    return terms, deriv

def ch1_easy():
    terms, deriv = _poly_and_deriv(n_terms=random.choice([2,3]), max_pow=3)
    q = f"Find d/dx [{fmt_poly(terms)}]"
    correct = fmt_poly(deriv) if deriv != [(0,0)] else "0"
    # distractor: forget to drop the power (don't decrement exponent)
    wrong1 = fmt_poly([(c*p, p) for c,p in terms if p>=1] or [(0,0)])
    # distractor: forget one term's coefficient multiply (leave power rule off by using p instead of c*p... use c only)
    wrong2 = fmt_poly([(c, p-1) for c,p in terms if p>=1] or [(0,0)])
    # distractor: sign flip on one term
    if deriv and deriv != [(0,0)]:
        i = random.randrange(len(deriv))
        flipped = list(deriv); c,p = flipped[i]; flipped[i] = (-c,p)
        wrong3 = fmt_poly(flipped)
    else:
        wrong3 = fmt_poly([(1,0)])
    opts = [correct, wrong1, wrong2, wrong3]
    return q, opts, correct, "easy"

def ch1_medium():
    kind = random.choice(["product", "quotient"])
    a, b = rnz(1,6), rnz(-8,8)
    c, d = rnz(1,6), rnz(-8,8)
    if kind == "product":
        # d/dx[(ax+b)(cx+d)] = a(cx+d) + c(ax+b) = 2ac x + (ad+bc)
        lead = 2*a*c
        const = a*d + b*c
        q = f"Find d/dx [({a}x {'+' if b>=0 else '-'} {abs(b)})({c}x {'+' if d>=0 else '-'} {abs(d)})]"
        correct = fmt_poly([(lead,1),(const,0)])
        wrong1 = fmt_poly([(a*c,1),(const,0)])          # forgot factor of 2 / one term
        wrong2 = fmt_poly([(lead,1),(b*d,0)])            # used constant*constant instead
        wrong3 = fmt_poly([(a*c+b*d,1),(const,0)])
        opts = [correct, wrong1, wrong2, wrong3]
        return q, opts, correct, "medium"
    else:
        # simple quotient with constant denominator disguised as quotient rule practice:
        # d/dx[(ax+b)/c] = a/c  (c constant, keeps things exact/clean)
        cst = rnz(2,6)
        from fractions import Fraction
        val = Fraction(a, cst)
        q = f"Find d/dx [({a}x {'+' if b>=0 else '-'} {abs(b)})/{cst}]"
        correct = f"{val.numerator}/{val.denominator}" if val.denominator != 1 else str(val.numerator)
        wrongs = {str(a), f"{b}/{cst}", str(a*cst)}
        opts = [correct] + list(wrongs)
        return q, opts, correct, "medium"

def ch1_hard():
    kind = random.choice(["trig", "exp", "product_poly3"])
    if kind == "trig":
        a = rnz(1,6)
        func, deriv_func = random.choice([("sin","cos"), ("cos","-sin")])
        q = f"Find d/dx [{func}({a}x)]"
        if deriv_func == "cos":
            correct = f"{a}cos({a}x)" if a != 1 else f"cos({a}x)".replace("1x","x")
            correct = correct.replace("1cos","cos")
        else:
            correct = f"-{a}sin({a}x)" if a != 1 else f"-sin({a}x)"
        wrong1 = f"{deriv_func.replace('-','')}({a}x)".replace('cos','cos').replace('sin','sin') if deriv_func!='cos' else f"cos({a}x)"
        wrong1 = f"{'cos' if func=='sin' else '-sin'}({a}x)"  # forgot chain multiplier
        wrong2 = f"{a}{'sin' if func=='sin' else 'cos'}({a}x)"  # wrong trig pair
        wrong3 = f"-{a}{'cos' if func=='sin' else 'sin'}({a}x)"
        opts = list({correct, wrong1, wrong2, wrong3})
        while len(opts) < 4:
            opts.append(f"{a+1}{deriv_func}({a}x)")
        return q, opts[:4], correct, "hard"
    elif kind == "exp":
        a = rnz(2,6)
        q = f"Find d/dx [e^({a}x)]"
        correct = f"{a}e^({a}x)"
        wrong1 = f"e^({a}x)"           # forgot chain multiplier
        wrong2 = f"{a}x\u00b7e^({a}x)"  # confused with power rule
        wrong3 = f"{a}\u00b2e^({a}x)"
        opts = [correct, wrong1, wrong2, wrong3]
        return q, opts, correct, "hard"
    else:
        # d/dx[x^2 * (ax+b)] via product rule -> 2x(ax+b) + x^2*a = 3a x^2 + 2b x
        a = rnz(1,5); b = rnz(-6,6)
        q = f"Find d/dx [x\u00b2({a}x {'+' if b>=0 else '-'} {abs(b)})]"
        correct = fmt_poly([(3*a,2),(2*b,1)])
        wrong1 = fmt_poly([(a,2),(2*b,1)])       # forgot the x^2 * a term's factor 3
        wrong2 = fmt_poly([(3*a,2),(b,1)])       # dropped the 2 in second term
        wrong3 = fmt_poly([(2*a,2),(b,1)])
        opts = [correct, wrong1, wrong2, wrong3]
        return q, opts, correct, "hard"


# ---------------------------------------------------------------------
# ch2_chain_implicit
# ---------------------------------------------------------------------

def ch2_easy():
    # d/dx[(ax+b)^n] = n*a*(ax+b)^(n-1)
    a = rnz(1,6); b = rnz(-8,8); n = random.randint(2,5)
    base = fmt_linear(a,b)
    q = f"Find d/dx [({base}){sup(n)}]"
    coef = n*a
    newpow = "" if n-1 == 1 else sup(n-1)
    correct = f"{coef}({base}){newpow}" if coef != 1 else f"({base}){newpow}"
    wrong1 = f"{a}({base}){newpow}"          # forgot to multiply by n
    wrong2 = f"{coef}({base}){sup(n)}"          # forgot to drop power
    wrong3 = f"{n}({base}){newpow}"           # forgot inner derivative a
    opts = [correct, wrong1, wrong2, wrong3]
    return q, opts, correct, "easy"

def ch2_medium():
    kind = random.choice(["trig_chain", "implicit_circle"])
    if kind == "trig_chain":
        a = rnz(2,6); b = rnz(-6,6)
        func, dfunc = random.choice([("sin","cos"), ("cos","-sin")])
        inner = fmt_linear(a,b)
        q = f"Find d/dx [{func}({inner})]"
        if dfunc == "cos":
            correct = f"{a}cos({inner})"
        else:
            correct = f"-{a}sin({inner})"
        wrong1 = f"{'cos' if func=='sin' else '-sin'}({inner})"   # forgot chain factor a
        wrong2 = f"{a}{'sin' if func=='sin' else 'cos'}({inner})"  # wrong derivative pair
        wrong3 = f"{a}{dfunc.replace('-','')}({fmt_linear(1,0)})".replace("(x)", f"({inner})")
        opts = list(dict.fromkeys([correct, wrong1, wrong2, f"{a**2}{dfunc if dfunc!='-sin' else 'sin'}({inner})"]))
        while len(opts) < 4:
            opts.append(f"{a+1}{'cos' if dfunc=='cos' else 'sin'}({inner})")
        return q, opts[:4], correct, "medium"
    else:
        # implicit: x^2 + y^2 = r^2  -> dy/dx = -x/y
        r2 = random.choice([25, 36, 49, 64, 100])
        q = f"Given x\u00b2 + y\u00b2 = {r2}, find dy/dx using implicit differentiation."
        correct = "-x/y"
        wrongs = ["x/y", "-y/x", "-2x/2y \u00b7 x"]
        opts = [correct] + wrongs
        return q, opts, correct, "medium"

def ch2_hard():
    kind = random.choice(["implicit_general", "double_chain"])
    if kind == "implicit_general":
        # a*x^2 + b*y = c  -> dy/dx = -2ax/b
        a = rnz(1,5); b = rnz(1,6)
        q = f"Given {a}x\u00b2 + {b}y = {rnz(5,40)}, find dy/dx."
        from fractions import Fraction
        val = Fraction(-2*a, b)
        num, den = val.numerator, val.denominator
        correct = f"{num}x/{den}" if den != 1 else f"{num}x"
        wrong1 = f"{-a}x/{b}"
        wrong2 = f"{2*a}x/{b}"
        wrong3 = f"{num}x\u00b2/{den}" if den != 1 else f"{num}x\u00b2"
        opts = [correct, wrong1, wrong2, wrong3]
        return q, opts, correct, "hard"
    else:
        # d/dx[sin((ax+b)^2)] = 2a(ax+b)cos((ax+b)^2)
        a = rnz(1,4); b = rnz(-5,5)
        inner = fmt_linear(a,b)
        coef = 2*a
        q = f"Find d/dx [sin(({inner})\u00b2)]"
        correct = f"{coef}({inner})cos(({inner})\u00b2)" if coef != 1 else f"({inner})cos(({inner})\u00b2)"
        wrong1 = f"cos(({inner})\u00b2)"                       # forgot both chain factors
        wrong2 = f"{coef}({inner})sin(({inner})\u00b2)"           # wrong outer derivative
        wrong3 = f"{a}({inner})cos(({inner})\u00b2)"            # dropped factor of 2
        opts = [correct, wrong1, wrong2, wrong3]
        return q, opts, correct, "hard"


# ---------------------------------------------------------------------
# ch3_applied_rates
# ---------------------------------------------------------------------

def ch3_easy():
    # position function s(t); find velocity (derivative) at given t
    terms = [(rnz(-6,6),2),(rnz(-8,8),1),(rnz(-8,8),0)]
    t0 = rnz(0,5)
    deriv = [(c*p,p-1) for c,p in terms if p>=1]
    v = sum(c*(t0**p) for c,p in deriv)
    q = f"An object's position is s(t) = {fmt_poly(terms, "t")} (meters). Find its velocity at t = {t0}."
    correct = f"{v} m/s"
    wrongs = {f"{v+d} m/s" for d in (2,-2,4)}
    opts = [correct] + list(wrongs)[:3]
    return q, opts, correct, "easy"

def ch3_medium():
    kind = random.choice(["avg_rate", "related_circle"])
    if kind == "avg_rate":
        a = rnz(1,4)
        t1, t2 = sorted(random.sample(range(0,6), 2))
        terms = [(a,2),(rnz(-6,6),1),(rnz(-6,6),0)]
        f1 = sum(c*(t1**p) for c,p in terms)
        f2 = sum(c*(t2**p) for c,p in terms)
        from fractions import Fraction
        val = Fraction(f2-f1, t2-t1)
        q = f"Given f(t) = {fmt_poly(terms, "t")}, find the average rate of change of f on [{t1}, {t2}]."
        correct = f"{val.numerator}/{val.denominator}" if val.denominator != 1 else str(val.numerator)
        wrongs = {str(val.numerator + d) for d in (1,-1,2)}
        opts = [correct] + list(wrongs)[:3]
        return q, opts, correct, "medium"
    else:
        # circle: dA/dt = 2*pi*r*dr/dt, given r and dr/dt find dA/dt (in terms of pi)
        r = rnz(2,10)
        drdt = rnz(1,5)
        coef = 2*r*drdt
        q = (f"A circle's radius is growing at dr/dt = {drdt} cm/s. When r = {r} cm, "
             f"find dA/dt (the rate the area is changing).")
        correct = f"{coef}\u03c0 cm\u00b2/s"
        wrongs = {f"{coef//2 if coef%2==0 else coef}\u03c0 cm\u00b2/s", f"{r*drdt}\u03c0 cm\u00b2/s", f"{coef+2}\u03c0 cm\u00b2/s"}
        wrongs.discard(correct)
        opts = [correct] + list(wrongs)[:3]
        while len(opts) < 4:
            opts.append(f"{coef+4}\u03c0 cm\u00b2/s")
        return q, opts, correct, "medium"

def ch3_hard():
    kind = random.choice(["ladder", "cone_shadow", "accel"])
    if kind == "ladder":
        # ladder length L against wall; base moving away at db/dt; find dh/dt when base = b
        L = random.choice([10,13,15,17,25])
        b = random.choice([n for n in range(3, L) if (L*L - n*n) > 0 and int((L*L-n*n)**0.5)**2 == L*L-n*n])
        h = int((L*L - b*b) ** 0.5)
        dbdt = rnz(1,4)
        from fractions import Fraction
        dhdt = Fraction(-b*dbdt, h)
        q = (f"A {L}-ft ladder slides down a wall. The base moves away from the wall at "
             f"{dbdt} ft/s. Find dh/dt (rate the top is falling) when the base is {b} ft from the wall.")
        correct = f"{dhdt.numerator}/{dhdt.denominator} ft/s" if dhdt.denominator != 1 else f"{dhdt.numerator} ft/s"
        wrongs = {f"{-dhdt.numerator}/{dhdt.denominator} ft/s" if dhdt.denominator!=1 else f"{-dhdt.numerator} ft/s",
                  f"{dbdt} ft/s", f"{b*dbdt}/{h} ft/s"}
        wrongs.discard(correct)
        opts = [correct] + list(wrongs)[:3]
        while len(opts) < 4:
            opts.append(f"{h} ft/s")
        return q, opts, correct, "hard"
    elif kind == "cone_shadow":
        # simple: dV/dt for cube: V = x^3, dV/dt = 3x^2 dx/dt
        x = rnz(2,8)
        dxdt = rnz(1,4)
        dvdt = 3 * x*x * dxdt
        q = (f"A cube's side length is increasing at dx/dt = {dxdt} cm/s. Find dV/dt when x = {x} cm "
             f"(V = x\u00b3).")
        correct = f"{dvdt} cm\u00b3/s"
        wrongs = {f"{dvdt//3} cm\u00b3/s", f"{x*x*dxdt} cm\u00b3/s", f"{dvdt+3} cm\u00b3/s"}
        wrongs.discard(correct)
        opts = [correct] + list(wrongs)[:3]
        while len(opts) < 4:
            opts.append(f"{dvdt-3} cm\u00b3/s")
        return q, opts, correct, "hard"
    else:
        # given velocity function v(t), find acceleration (derivative) at t0, i.e. second derivative concept
        terms = [(rnz(-5,5),2),(rnz(-6,6),1),(rnz(-6,6),0)]
        t0 = rnz(0,4)
        deriv = [(c*p,p-1) for c,p in terms if p>=1]
        a_t = sum(c*(t0**p) for c,p in deriv)
        q = f"Velocity is v(t) = {fmt_poly(terms, "t")} (m/s). Find the acceleration a(t) at t = {t0}."
        correct = f"{a_t} m/s\u00b2"
        wrongs = {f"{a_t+d} m/s\u00b2" for d in (1,-1,3)}
        opts = [correct] + list(wrongs)[:3]
        return q, opts, correct, "hard"


# ---------------------------------------------------------------------
# ch4_curve_sketching
# ---------------------------------------------------------------------

def ch4_easy():
    # f(x) = a x^2 + b x + c ; critical point where f'(x)=0 -> x = -b'/(2a') with f'=2a x + b
    a = rnz(1,5)
    b = rnz(-10,10)
    if b % 2 != 0:
        b += 1  # keep -b/(2a) reasonably clean sometimes; not required but nicer
    c = rnz(-8,8)
    terms = [(a,2),(b,1),(c,0)]
    from fractions import Fraction
    crit = Fraction(-b, 2*a)
    q = f"Find the x-coordinate of the critical point of f(x) = {fmt_poly(terms)}."
    correct = f"{crit.numerator}/{crit.denominator}" if crit.denominator != 1 else str(crit.numerator)
    wrongs = {str(crit.numerator + d) for d in (1,-1,2)}
    opts = [correct] + list(wrongs)[:3]
    return q, opts, correct, "easy"

def ch4_medium():
    kind = random.choice(["concavity", "maxmin"])
    a = rnz(1,4)
    b = rnz(-9,9)
    c = rnz(-9,9)
    d = rnz(-9,9)
    terms = [(a,3),(b,2),(c,1),(d,0)]
    # f'(x) = 3a x^2 + 2b x + c ; f''(x) = 6a x + 2b -> inflection at x = -2b/6a = -b/3a
    if kind == "concavity":
        from fractions import Fraction
        infl = Fraction(-b, 3*a)
        q = f"Find the x-coordinate of the inflection point of f(x) = {fmt_poly(terms)}."
        correct = f"{infl.numerator}/{infl.denominator}" if infl.denominator != 1 else str(infl.numerator)
        wrongs = {str(infl.numerator + dd) for dd in (1,-1,2)}
        opts = [correct] + list(wrongs)[:3]
        return q, opts, correct, "medium"
    else:
        # simpler quadratic for clean max/min classification
        a2 = random.choice([-3,-2,-1,1,2,3])
        b2 = rnz(-8,8)
        terms2 = [(a2,2),(b2,1),(rnz(-6,6),0)]
        from fractions import Fraction
        xc = Fraction(-b2, 2*a2)
        kind_str = "minimum" if a2 > 0 else "maximum"
        q = f"At its critical point, does f(x) = {fmt_poly(terms2)} have a local max or local min?"
        correct = f"Local {kind_str}"
        opts = [correct, f"Local {'maximum' if kind_str=='minimum' else 'minimum'}", "Neither (inflection point)", "Cannot be determined"]
        return q, opts, correct, "medium"

def ch4_hard():
    kind = random.choice(["intervals", "second_deriv_test"])
    if kind == "intervals":
        # choose clean integer critical points by building f' from its roots
        r1, r2 = sorted(random.sample(range(-6, 7), 2))
        a = 2  # f(x) leading coeff; keeps b,c integer below
        b = -3 * a * (r1 + r2) // 2 if (r1 + r2) % 2 == 0 else -3 * (r1 + r2)
        if (r1 + r2) % 2 != 0:
            a = 4  # bump leading coeff so 2b stays integer cleanly
            b = -3 * a * (r1 + r2) // 2
        c = 3 * a * r1 * r2
        terms = [(a,3),(b,2),(c,1),(rnz(-6,6),0)]
        q = f"For f(x) = {fmt_poly(terms)}, on which interval is f increasing?"
        # leading coeff of f' is 3a>0, so f' is an upward parabola -> increasing outside the roots
        correct = f"x < {r1} or x > {r2}"
        wrongs = [f"{r1} < x < {r2}", f"x > {r2} only", f"x < {r1} only"]
        opts = [correct] + wrongs
        return q, opts, correct, "hard"
    else:
        # second derivative test at a given critical-looking point
        a2 = rnz(1,4)
        b2 = rnz(-8,8)
        x0 = rnz(-4,4)
        # f''(x) = 6a2 x + 2b2 ; classify sign at x0
        val = 6*a2*x0 + 2*b2
        terms3 = [(a2,3),(b2,2),(rnz(-6,6),1),(rnz(-6,6),0)]
        q = (f"For f(x) = {fmt_poly(terms3)}, use the second derivative test to classify the "
             f"concavity of f at x = {x0}.")
        if val > 0:
            correct = "Concave up (f''(x) > 0)"
            wrong_extra = "Concave down (f''(x) < 0)"
        else:
            correct = "Concave down (f''(x) < 0)"
            wrong_extra = "Concave up (f''(x) > 0)"
        opts = [correct, wrong_extra, "Inflection point (f''(x) = 0)", "Cannot be determined without more info"]
        return q, opts, correct, "hard"


# ---------------------------------------------------------------------
# ch5_integration
# ---------------------------------------------------------------------

def ch5_easy():
    # antiderivative of a x^n (power rule for integration)
    from fractions import Fraction
    n = random.choice([1,2,3])
    a = rnz(-9,9)
    terms = [(a, n)]
    val = Fraction(a, n+1)
    q = f"Find \u222b {fmt_poly(terms)} dx"
    correct = fmt_frac_term(val.numerator, val.denominator, n+1) + " + C"
    wrong1 = fmt_frac_term(a, 1, n+1) + " + C"                 # forgot to divide by n+1
    wrong2 = fmt_frac_term(a, 1, n) + " + C"                    # forgot to raise power
    if n == 0:
        wrong3 = fmt_frac_term(a, 1, 1) + " + C"
    else:
        w3 = Fraction(a, n)
        wrong3 = fmt_frac_term(w3.numerator, w3.denominator, n+1) + " + C"
    opts = list(dict.fromkeys([correct, wrong1, wrong2, wrong3]))
    while len(opts) < 4:
        opts.append(fmt_frac_term(a+1, 1, n+1) + " + C")
    return q, opts[:4], correct, "easy"

def ch5_medium():
    kind = random.choice(["definite", "u_sub"])
    if kind == "definite":
        a = rnz(1,4)
        lo, hi = sorted(random.sample(range(0,5), 2))
        # integral of a*x^2 dx from lo to hi = a/3 (hi^3 - lo^3)
        from fractions import Fraction
        val = Fraction(a, 3) * (hi**3 - lo**3)
        q = f"Evaluate \u222b from {lo} to {hi} of {fmt_poly([(a,2)])} dx"
        correct = f"{val.numerator}/{val.denominator}" if val.denominator != 1 else str(val.numerator)
        wrongs = {str(val.numerator + d) for d in (1,-1,3)}
        opts = [correct] + list(wrongs)[:3]
        return q, opts, correct, "medium"
    else:
        # simple u-sub: integral of 2ax(ax^2+b)^n dx = (ax^2+b)^(n+1)/(n+1) + C
        a = rnz(1,4)
        b = rnz(-6,6)
        n = random.randint(1,3)
        coef = 2*a
        inner = f"{a}x\u00b2 {'+' if b>=0 else '-'} {abs(b)}"
        npow = "" if n == 1 else sup(n)
        q = f"Find \u222b {coef}x({inner}){npow} dx"
        from fractions import Fraction
        val = Fraction(1, n+1)
        pref = "" if val.numerator==1 and val.denominator==1 else (f"({val.numerator}/{val.denominator})" if val.denominator!=1 else f"{val.numerator}")
        correct = f"{pref}({inner}){sup(n+1)} + C"
        wrong1 = f"({inner}){sup(n+1)} + C"                # forgot 1/(n+1)
        wrong2 = f"{pref}({inner}){npow} + C"               # didn't bump power
        wrong3 = f"{coef}({inner}){sup(n+1)} + C"           # left the 2a coefficient in
        opts = list(dict.fromkeys([correct, wrong1, wrong2, wrong3]))
        while len(opts) < 4:
            opts.append(f"({inner}){sup(n+2)} + C")
        return q, opts[:4], correct, "medium"

def ch5_hard():
    kind = random.choice(["by_parts", "trig_integral", "log_integral"])
    if kind == "by_parts":
        # integral of x*e^(ax) dx = (x/a)e^(ax) - (1/a^2)e^(ax) + C  -- present as multiple choice on the form
        a = rnz(1,9)
        q = f"Find \u222b x\u00b7e^({a}x) dx"
        correct = f"(x/{a})e^({a}x) - (1/{a}\u00b2)e^({a}x) + C"
        wrong1 = f"(x/{a})e^({a}x) + C"                      # dropped second term
        wrong2 = f"x\u00b7e^({a}x) + C"                       # skipped by-parts entirely
        wrong3 = f"(x/{a})e^({a}x) + (1/{a}\u00b2)e^({a}x) + C"  # sign error
        opts = [correct, wrong1, wrong2, wrong3]
        return q, opts, correct, "hard"
    elif kind == "trig_integral":
        a = rnz(1,9)
        func = random.choice(["sin", "cos"])
        if func == "sin":
            correct = f"-(1/{a})cos({a}x) + C" if a != 1 else "-cos(x) + C"
            wrong1 = f"(1/{a})cos({a}x) + C" if a != 1 else "cos(x) + C"
            wrong2 = f"-cos({a}x) + C"
            wrong3 = f"-(1/{a})sin({a}x) + C" if a != 1 else "-sin(x) + C"
        else:
            correct = f"(1/{a})sin({a}x) + C" if a != 1 else "sin(x) + C"
            wrong1 = f"-(1/{a})sin({a}x) + C" if a != 1 else "-sin(x) + C"
            wrong2 = f"sin({a}x) + C"
            wrong3 = f"(1/{a})cos({a}x) + C" if a != 1 else "cos(x) + C"
        q = f"Find \u222b {func}({a}x) dx"
        opts = [correct, wrong1, wrong2, wrong3]
        return q, opts, correct, "hard"
    else:
        # integral of 1/(ax+b) dx = (1/a)ln|ax+b| + C
        a = rnz(1,7)
        b = rnz(-8,8)
        inner = fmt_linear(a, b)
        q = f"Find \u222b 1/({inner}) dx"
        correct = f"(1/{a})ln|{inner}| + C" if a != 1 else f"ln|{inner}| + C"
        wrong1 = f"ln|{inner}| + C"                          # forgot 1/a
        wrong2 = f"(1/{a})ln|{inner}|" + "\u00b2 + C" if a != 1 else f"ln|{inner}|\u00b2 + C"  # squared log error
        wrong3 = f"{a}ln|{inner}| + C"                        # multiplied instead of divided
        opts = list(dict.fromkeys([correct, wrong1, wrong2, wrong3]))
        while len(opts) < 4:
            opts.append(f"(1/{a+1})ln|{inner}| + C")
        return q, opts[:4], correct, "hard"


# ---------------------------------------------------------------------
# ch6_diffeq
# ---------------------------------------------------------------------

def ch6_easy():
    # dy/dx = k*y -> y = C*e^(kx). Given IC y(0)=y0, find y(x).
    k = rnz(-5,5)
    y0 = rnz(1,9)
    q = f"Solve dy/dx = {fmt_frac_term(k,1,1,var='y')} with y(0) = {y0}."
    ke = fmt_frac_term(k,1,1)  # "kx" style, coefficient-aware
    kem = fmt_frac_term(-k,1,1)
    y0s = "" if y0 == 1 else str(y0)
    correct = f"y = {y0s}e^({ke})"
    wrong1 = f"y = {y0s}e^({kem})"       # sign flip
    wrong2 = f"y = {'' if k == 1 else k}e^({fmt_frac_term(y0,1,1)})"        # swapped roles
    wrong3 = f"y = {y0}{plus(k)}x"      # treated as linear, not exponential
    opts = [correct, wrong1, wrong2, wrong3]
    return q, opts, correct, "easy"

def ch6_medium():
    kind = random.choice(["separable", "growth_word"])
    if kind == "separable":
        # dy/dx = k*x  (separable, not just exponential) -> y = (k/2)x^2 + C, IC y(0)=y0
        k = rnz(1,6)
        y0 = rnz(-5,5)
        from fractions import Fraction
        half_k = Fraction(k,2)
        q = f"Solve dy/dx = {fmt_frac_term(k,1,1)} with y(0) = {y0}."
        correct = f"y = {fmt_frac_term(half_k.numerator, half_k.denominator, 2)}{plus(y0)}"
        wrong1 = f"y = {fmt_frac_term(k,1,2)}{plus(y0)}"            # forgot to divide by 2
        wrong2 = f"y = {fmt_frac_term(half_k.numerator, half_k.denominator, 2)}"  # dropped constant
        wrong3 = f"y = {fmt_frac_term(k,1,1)}{plus(y0)}"             # integrated incorrectly (power rule error)
        opts = [correct, wrong1, wrong2, wrong3]
        return q, opts, correct, "medium"
    else:
        # exponential growth/decay word problem: P(t) = P0 e^(kt); given doubling logic simplified to direct k
        P0 = random.choice([100, 200, 500, 1000])
        k = round(random.choice([0.02,0.03,0.05,0.1,-0.02,-0.05]), 2)
        t = random.choice([5,10,20])
        q = (f"A population grows according to dP/dt = {k}P, with P(0) = {P0}. "
             f"Which function models P(t)?")
        correct = f"P(t) = {P0}e^({k}t)"
        wrong1 = f"P(t) = {P0}{plus(k).replace('x','t')}t" if False else f"P(t) = {P0}{plus(k)}t"
        wrong2 = f"P(t) = {P0}e^({-k}t)"
        wrong3 = f"P(t) = {P0}({k}t)"
        opts = [correct, wrong1, wrong2, wrong3]
        return q, opts, correct, "medium"

def ch6_hard():
    # separable: dy/dx = k x / y -> y dy = k x dx -> y^2/2 = k x^2/2 + C -> y^2 - k x^2 = C'
    kind = random.choice(["separable_xy", "verify_solution"])
    if kind == "separable_xy":
        k = rnz(1,5)
        x0, y0 = rnz(1,4), rnz(1,4)
        Cval = y0*y0 - k*x0*x0
        kx2 = fmt_frac_term(k,1,2)
        negkx2 = fmt_frac_term(-k,1,2)
        q = f"Solve the separable equation dy/dx = {fmt_frac_term(k,1,0)}x/y, given y({x0}) = {y0}."
        correct = f"y\u00b2 = {kx2}{plus(Cval)}"
        wrong1 = f"y\u00b2 = {kx2}"
        wrong2 = f"y = {kx2}{plus(Cval)}"
        wrong3 = f"y\u00b2 = {negkx2}{plus(Cval)}"
        opts = [correct, wrong1, wrong2, wrong3]
        return q, opts, correct, "hard"
    else:
        # verify which function solves dy/dx = k y (multiple choice on the general solution form, with a distractor exponent structure)
        k = rnz(2,6)
        q = f"Which function is a solution to dy/dx = {k}y?"
        correct = f"y = 5e^({k}x)"
        wrong1 = f"y = 5e^({-k}x)"
        wrong2 = f"y = 5x^{k}" if False else f"y = 5{ '' }x\u00b2 \u00b7 {k}"
        wrong2 = f"y = {k}x + 5"
        wrong3 = f"y = 5e^({k}x\u00b2)"
        opts = [correct, wrong1, wrong2, wrong3]
        return q, opts, correct, "hard"


# ---------------------------------------------------------------------
# ch7_applications
# ---------------------------------------------------------------------

def ch7_easy():
    kind = random.choice(["quadratic", "linear"])
    from fractions import Fraction
    if kind == "quadratic":
        a = rnz(1,9)
        b = rnz(1,9)
        val = Fraction(a, 3) * b**3
        q = f"Find the area under y = {fmt_poly([(a,2)])} from x = 0 to x = {b}."
    else:
        a = rnz(1,9)
        b = rnz(1,9)
        val = Fraction(a, 2) * b**2
        q = f"Find the area under y = {fmt_poly([(a,1)])} from x = 0 to x = {b}."
    correct = f"{val.numerator}/{val.denominator}" if val.denominator != 1 else str(val.numerator)
    wrongs = {str(val.numerator + d) for d in (1,-1,3)}
    opts = [correct] + list(wrongs)[:3]
    return q, opts, correct, "easy"

def ch7_medium():
    kind = random.choice(["area_between", "net_change"])
    if kind == "area_between":
        # area between y = a (constant, top) and y = x^2/k-ish... use two lines instead for a clean answer:
        # top: y = -x^2 + c (parabola), bottom: y = 0, over its natural roots -> classic area
        c = random.choice([4,9,16,25,36])
        r = int(c**0.5)
        from fractions import Fraction
        val = Fraction(4,3) * r**3
        q = f"Find the area of the region bounded by y = -x\u00b2 + {c} and y = 0."
        correct = f"{val.numerator}/{val.denominator}" if val.denominator != 1 else str(val.numerator)
        wrongs = {str(val.numerator + d) for d in (2,-2,6)}
        opts = [correct] + list(wrongs)[:3]
        return q, opts, correct, "medium"
    else:
        # net change: given v(t) = at+b, find displacement from t1 to t2
        a = rnz(-4,4)
        b = rnz(-6,6)
        t1, t2 = sorted(random.sample(range(0,6),2))
        from fractions import Fraction
        val = Fraction(a,2)*(t2**2 - t1**2) + b*(t2-t1)
        q = f"A particle has velocity v(t) = {fmt_poly([(a,1),(b,0)], 't')} m/s. Find its displacement from t = {t1} to t = {t2}."
        correct = f"{val.numerator}/{val.denominator} m" if val.denominator != 1 else f"{val.numerator} m"
        wrongs = {f"{val.numerator + d} m" for d in (1,-1,3)}
        opts = [correct] + list(wrongs)[:3]
        return q, opts, correct, "medium"

def ch7_hard():
    kind = random.choice(["volume_disk", "area_between_curves"])
    if kind == "volume_disk":
        # V = pi * integral of (a x)^2 dx from 0 to h = pi * a^2 * h^3/3
        a = rnz(1,8)
        h = rnz(1,8)
        from fractions import Fraction
        val = Fraction(a*a, 3) * h**3
        no_third = a*a*h**3  # common mistake: forgot the 1/3 from disk-method integration
        q = (f"The region under y = {a}x from x = 0 to x = {h} is revolved about the x-axis. "
             f"Find the volume (disk method).")
        correct = f"({val.numerator}/{val.denominator})\u03c0" if val.denominator != 1 else f"{val.numerator}\u03c0"
        wrong1 = f"{no_third}\u03c0"                                  # forgot the 1/3
        wrong2 = f"({a*a}/3)h\u00b3\u03c0" if False else f"{a*h}\u03c0"  # dropped the squaring
        half = Fraction(a*a, 2) * h**3
        wrong3 = f"({half.numerator}/{half.denominator})\u03c0" if half.denominator != 1 else f"{half.numerator}\u03c0"
        opts = list(dict.fromkeys([correct, wrong1, wrong2, wrong3]))
        while len(opts) < 4:
            opts.append(f"{no_third+2}\u03c0")
        return q, opts, correct, "hard"
    else:
        # area between y = a*x and y = x^2 (two intersection points 0 and a)
        a = rnz(2,18)
        from fractions import Fraction
        val = Fraction(a**3, 6)
        q = f"Find the area of the region between y = {fmt_poly([(a,1)])} and y = x\u00b2."
        correct = f"{val.numerator}/{val.denominator}" if val.denominator != 1 else str(val.numerator)
        wrongs = {str(val.numerator + d) for d in (1,-1,4)} if val.denominator == 1 else {f"{val.numerator+2}/{val.denominator}", f"{val.numerator-2}/{val.denominator}", str(a)}
        opts = [correct] + list(wrongs)[:3]
        return q, opts, correct, "hard"


# ---------------------------------------------------------------------
# Assembly -- exactly 100 questions per chapter (34 easy / 33 medium /
# 33 hard, matching the original split), deduplicated, written to CSV
# in the same schema the app already expects.
# ---------------------------------------------------------------------
CHAPTER_GENERATORS = {
    "ch0": (ch0_easy, ch0_medium, ch0_hard),
    "ch1": (ch1_easy, ch1_medium, ch1_hard),
    "ch2": (ch2_easy, ch2_medium, ch2_hard),
    "ch3": (ch3_easy, ch3_medium, ch3_hard),
    "ch4": (ch4_easy, ch4_medium, ch4_hard),
    "ch5": (ch5_easy, ch5_medium, ch5_hard),
    "ch6": (ch6_easy, ch6_medium, ch6_hard),
    "ch7": (ch7_easy, ch7_medium, ch7_hard),
}

TARGET = {"easy": 34, "medium": 33, "hard": 33}  # 100 per chapter, same as before
LETTERS = ["a", "b", "c", "d"]


def build_chapter_rows(chapter_id, easy_fn, medium_fn, hard_fn, seen_questions=None):
    if seen_questions is None:
        seen_questions = set()
    fns = {"easy": easy_fn, "medium": medium_fn, "hard": hard_fn}
    rows = []
    q_counter = 1
    for diff, count in TARGET.items():
        gen_fn = fns[diff]
        produced = 0
        attempts = 0
        while produced < count and attempts < count * 60:
            attempts += 1
            q_text, opts, correct_val, _tag = gen_fn()

            uniq = []
            for o in opts:
                if o not in uniq:
                    uniq.append(o)
            if correct_val not in uniq:
                continue
            filler_i = 1
            while len(uniq) < 4:
                candidate = f"{correct_val} (v{filler_i})"
                if candidate not in uniq:
                    uniq.append(candidate)
                filler_i += 1
            uniq = uniq[:4]

            if q_text in seen_questions:
                continue
            seen_questions.add(q_text)

            random.shuffle(uniq)
            correct_letter = LETTERS[uniq.index(correct_val)]
            qid = f"{chapter_id}_q{q_counter:03d}"
            rows.append([qid, chapter_id, q_text, uniq[0], uniq[1], uniq[2], uniq[3], correct_letter, diff])
            q_counter += 1
            produced += 1

        if produced < count:
            print(f"WARNING: {chapter_id}/{diff} only produced {produced}/{count} unique questions")

    return rows


def main():
    random.seed(42)
    all_rows = []
    for chapter_id, (easy_fn, medium_fn, hard_fn) in CHAPTER_GENERATORS.items():
        print(f"Building 100-question bank for {chapter_id}...")
        all_rows.extend(build_chapter_rows(chapter_id, easy_fn, medium_fn, hard_fn))

    with open("question_bank.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "question_id",
                "chapter_id",
                "question",
                "option_a",
                "option_b",
                "option_c",
                "option_d",
                "correct_option",
                "difficulty",
            ]
        )
        writer.writerows(all_rows)

    print(f"Generated question_bank.csv successfully with {len(all_rows)} questions.")


if __name__ == "__main__":
    main()
