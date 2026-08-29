"""
build_question_bank.py

Generates question_bank.csv -- a real MCQ bank, 8 questions per chapter
across all 8 chapters (64 total), keyed to the same chapter ids used
everywhere else in the app (ch0-ch7).

Unlike build_fake_database.py, this data is NOT randomly generated --
every question and answer here was worked out by hand and is meant to
be mathematically correct. If you add more questions later, double
check the math before committing it; a wrong "correct" answer in a
quiz is worse than a missing one.

Usage:
    python build_question_bank.py
    -> writes question_bank.csv in the current directory
"""

import csv

# Each question: (chapter_id, question, [option_a, option_b, option_c, option_d],
#                  correct_letter, difficulty)
QUESTIONS = [
    # ---------------- ch0: Limits & Continuity ----------------
    ("ch0", "Evaluate lim(x\u21922) (x\u00B2\u22124)/(x\u22122)",
     ["2", "4", "0", "undefined"], "b", "easy"),
    ("ch0", "Evaluate lim(x\u21920) sin(x)/x",
     ["0", "1", "undefined", "\u221E"], "b", "medium"),
    ("ch0", "Evaluate lim(x\u2192\u221E) (3x\u00B2+2)/(x\u00B2+1)",
     ["0", "1", "3", "\u221E"], "c", "medium"),
    ("ch0", "A function f is continuous at x=a if:",
     ["f(a) exists only", "lim x\u2192a f(x) exists only",
      "f(a) = lim x\u2192a f(x)", "f is differentiable at a"], "c", "easy"),
    ("ch0", "Evaluate lim(x\u21921) (x\u00B3\u22121)/(x\u22121)",
     ["1", "2", "3", "undefined"], "c", "medium"),
    ("ch0", "Which limit is an indeterminate 0/0 form?",
     ["lim x\u21920 x/1", "lim x\u21920 sin(x)/x", "lim x\u21925 (x+1)",
      "lim x\u21922 (x\u22122)/(x+2)"], "b", "medium"),
    ("ch0", "Evaluate lim(x\u21920\u207A) 1/x",
     ["0", "1", "\u221E", "\u2212\u221E"], "c", "easy"),
    ("ch0", "The Intermediate Value Theorem requires the function to be:",
     ["Differentiable on [a,b]", "Continuous on [a,b]",
      "Increasing on [a,b]", "Bounded on [a,b]"], "b", "easy"),

    # ---------------- ch1: Differentiation Basics ----------------
    ("ch1", "Find d/dx[5x\u2074 \u2212 3x\u00B2 + 7]",
     ["20x\u00B3\u22126x", "20x\u00B3\u22123x", "5x\u00B3\u22126x", "20x\u2074\u22126x"], "a", "easy"),
    ("ch1", "Find d/dx[x\u2075]",
     ["x\u2074", "5x\u2074", "5x\u2075", "x\u2075/5"], "b", "easy"),
    ("ch1", "Find d/dx[7]",
     ["7", "0", "1", "x"], "b", "easy"),
    ("ch1", "Find d/dx[3x^(1/2)]",
     ["3/2 \u221Ax", "3/(2\u221Ax)", "3\u221Ax", "3/2 x^(3/2)"], "b", "medium"),
    ("ch1", "Find d/dx[1/x\u00B2]",
     ["\u22122/x\u00B3", "2/x\u00B3", "\u22121/x\u00B3", "1/x\u00B3"], "a", "medium"),
    ("ch1", "The derivative of a sum f(x)+g(x) is:",
     ["f'(x)\u00B7g'(x)", "f'(x)+g'(x)", "f'(x)\u2212g'(x)", "always 0"], "b", "easy"),
    ("ch1", "Find d/dx[10x\u00B2 \u2212 4x + 1]",
     ["20x\u22124", "10x\u22124", "20x+4", "10x\u00B2\u22124"], "a", "easy"),
    ("ch1", "The power rule states d/dx[x^n] =",
     ["nx^(n\u22121)", "x^(n\u22121)", "nx^n", "(n\u22121)x^n"], "a", "easy"),

    # ---------------- ch2: Chain & Implicit Rules ----------------
    ("ch2", "Find d/dx[(2x+5)\u2074]",
     ["4(2x+5)\u00B3", "8(2x+5)\u00B3", "8(2x+5)\u2074", "2(2x+5)\u00B3"], "b", "medium"),
    ("ch2", "Find d/dx[sin(3x)]",
     ["cos(3x)", "3cos(3x)", "\u22123cos(3x)", "3sin(3x)"], "b", "medium"),
    ("ch2", "Find d/dx[e^(2x)]",
     ["e^(2x)", "2e^(2x)", "2xe^(2x)", "e^(2x)/2"], "b", "medium"),
    ("ch2", "Find d/dx[ln(x\u00B2+1)]",
     ["1/(x\u00B2+1)", "2x/(x\u00B2+1)", "2x", "x/(x\u00B2+1)"], "b", "medium"),
    ("ch2", "For x\u00B2+y\u00B2=25, find dy/dx implicitly",
     ["x/y", "\u2212x/y", "\u2212y/x", "y/x"], "b", "hard"),
    ("ch2", "Find d/dx[cos(x\u00B2)]",
     ["\u22122x sin(x\u00B2)", "2x sin(x\u00B2)", "\u2212sin(x\u00B2)", "\u22122x cos(x\u00B2)"], "a", "medium"),
    ("ch2", "The chain rule states d/dx[f(g(x))] =",
     ["f'(g(x))", "f'(g(x))\u00B7g'(x)", "f'(x)\u00B7g'(x)", "f(g'(x))"], "b", "easy"),
    ("ch2", "For xy=10, find dy/dx implicitly",
     ["y/x", "\u2212y/x", "\u2212x/y", "x/y"], "b", "hard"),

    # ---------------- ch3: Applied Rates of Change ----------------
    ("ch3", "A sphere's radius grows at 3 cm/s. Find dV/dt at r=2 (V=\u2074\u2044\u2083\u03C0r\u00B3)",
     ["16\u03C0 cm\u00B3/s", "48\u03C0 cm\u00B3/s", "32\u03C0 cm\u00B3/s", "24\u03C0 cm\u00B3/s"], "b", "hard"),
    ("ch3", "s(t)=t\u00B3\u22126t\u00B2+9t. Find velocity at t=2",
     ["\u22123", "3", "0", "9"], "a", "medium"),
    ("ch3", "s(t)=t\u00B2\u22124t. Find when velocity=0",
     ["t=1", "t=2", "t=4", "t=0"], "b", "easy"),
    ("ch3", "s(t)=t\u00B2+3t (meters). Find acceleration",
     ["2 m/s\u00B2", "3 m/s\u00B2", "t m/s\u00B2", "0 m/s\u00B2"], "a", "easy"),
    ("ch3", "A 10 ft ladder's base slides away at 1 ft/s. When the base is 6 ft out, how fast does the top slide down?",
     ["\u22120.75 ft/s", "\u22121 ft/s", "0.75 ft/s", "\u22121.33 ft/s"], "a", "hard"),
    ("ch3", "Marginal cost is defined as:",
     ["Total cost \u00F7 quantity", "The derivative of the cost function",
      "The integral of the cost function", "Average cost"], "b", "easy"),
    ("ch3", "f(x)=x\u00B3 models population. Find the growth rate at x=2",
     ["6", "8", "12", "4"], "c", "medium"),
    ("ch3", "A balloon's radius grows at 0.5 cm/s. Find dSA/dt at r=4 (SA=4\u03C0r\u00B2)",
     ["8\u03C0", "16\u03C0", "4\u03C0", "32\u03C0"], "b", "hard"),

    # ---------------- ch4: Curve Sketching ----------------
    ("ch4", "For f(x)=x\u00B3\u22123x, find the critical points",
     ["x=0", "x=\u00B11", "x=\u00B13", "x=1 only"], "b", "medium"),
    ("ch4", "For f(x)=x\u00B3\u22123x, the local minimum is at",
     ["x=\u22121", "x=0", "x=1", "x=3"], "c", "medium"),
    ("ch4", "If f''(x)>0 on an interval, the graph is",
     ["Concave down", "Concave up", "Increasing", "Decreasing"], "b", "easy"),
    ("ch4", "An inflection point occurs where",
     ["f'(x)=0", "f''(x)=0 and concavity changes", "f(x)=0", "f'(x) is undefined only"], "b", "medium"),
    ("ch4", "For f(x)=x\u00B2\u22124x+3, the minimum occurs at",
     ["x=1", "x=2", "x=3", "x=4"], "b", "easy"),
    ("ch4", "If f'(x)>0 for all x in an interval, f is",
     ["Decreasing", "Constant", "Increasing", "Concave up"], "c", "easy"),
    ("ch4", "For f(x)=x\u2074\u22124x\u00B2, find the x-values of the local minima",
     ["x=0", "x=\u00B1\u221A2", "x=\u00B12", "x=\u00B11"], "b", "hard"),
    ("ch4", "The First Derivative Test is used to determine",
     ["Concavity", "Local extrema", "Points of inflection only", "Continuity"], "b", "easy"),

    # ---------------- ch5: Integration Techniques ----------------
    ("ch5", "Evaluate \u222B 3x\u00B2 dx",
     ["x\u00B3+C", "3x\u00B3+C", "x\u00B3/3+C", "6x+C"], "a", "easy"),
    ("ch5", "Evaluate \u222B\u2080\u00B2 3x\u00B2 dx",
     ["6", "8", "12", "4"], "b", "medium"),
    ("ch5", "Evaluate \u222B (1/x) dx",
     ["ln|x|+C", "1/x\u00B2+C", "x ln x \u2212 x + C", "\u22121/x\u00B2+C"], "a", "medium"),
    ("ch5", "Evaluate \u222B e^(2x) dx",
     ["e^(2x)+C", "2e^(2x)+C", "(1/2)e^(2x)+C", "(1/2)e^x+C"], "c", "medium"),
    ("ch5", "Evaluate \u222B cos(x) dx",
     ["sin(x)+C", "\u2212sin(x)+C", "cos(x)+C", "\u2212cos(x)+C"], "a", "easy"),
    ("ch5", "Using u=x\u00B2+1, evaluate \u222B 2x(x\u00B2+1)\u00B3 dx",
     ["(x\u00B2+1)\u2074+C", "(x\u00B2+1)\u2074/4+C", "4(x\u00B2+1)\u00B3+C", "(x\u00B2+1)\u00B3/3+C"], "b", "hard"),
    ("ch5", "Evaluate \u222B\u2081\u00B3 2x dx",
     ["6", "8", "9", "4"], "b", "medium"),
    ("ch5", "The integration by parts formula is",
     ["\u222Bu dv = uv \u2212 \u222Bv du", "\u222Bu dv = uv + \u222Bv du",
      "\u222Bu dv = u'v \u2212 uv'", "\u222Bu dv = \u222Bu du \u00B7 \u222Bv dv"], "a", "hard"),

    # ---------------- ch6: Differential Equations ----------------
    ("ch6", "Solve dy/dx = y, y(0)=2. Find y(1)",
     ["e\u00B2", "2/e", "2e\u00B2", "2e"], "d", "medium"),
    ("ch6", "Solve dy/dx = 3, y(0)=1. Find y(x)",
     ["y=3x", "y=3x+1", "y=x+3", "y=3x\u22121"], "b", "easy"),
    ("ch6", "Which of these is a separable differential equation?",
     ["dy/dx = x + y", "dy/dx = x\u00B7y", "dy/dx = sin(x+y)", "dy/dx = x\u00B2+y\u00B2"], "b", "medium"),
    ("ch6", "Solve dy/dx = 2x, y(0)=5. Find y(x)",
     ["y=x\u00B2", "y=x\u00B2+5", "y=2x\u00B2+5", "y=x\u00B2\u22125"], "b", "easy"),
    ("ch6", "The general solution to dy/dx = ky is",
     ["y=kx+C", "y=Ce^(kx)", "y=Cx^k", "y=k ln(x)+C"], "b", "medium"),
    ("ch6", "For dy/dx = \u22120.5y, y(0)=100, this models",
     ["Exponential growth", "Exponential decay", "Linear decay", "Logistic growth"], "b", "easy"),
    ("ch6", "Solve dy/dx = 4x\u00B3, y(1)=2. Find y(x)",
     ["y=x\u2074+1", "y=x\u2074", "y=x\u2074\u22121", "y=4x\u2074+1"], "a", "medium"),
    ("ch6", "An initial condition in a differential equation is used to",
     ["Find the general solution", "Find a particular solution by solving for C",
      "Determine the order of the equation", "Check if the equation is linear"], "b", "medium"),

    # ---------------- ch7: Applications of Integrals ----------------
    ("ch7", "Area between y=x\u00B2 and y=4, from x=\u22122 to x=2",
     ["16/3", "8/3", "64/3", "32/3"], "d", "hard"),
    ("ch7", "Find the area under y=x\u00B2 from x=0 to x=3",
     ["6", "9", "27", "3"], "b", "medium"),
    ("ch7", "The area between f(x) and g(x) (f\u2265g) from a to b is",
     ["\u222B\u2090\u1D47 [f(x)+g(x)] dx", "\u222B\u2090\u1D47 [f(x)\u2212g(x)] dx",
      "f(b)\u2212g(b)", "\u222B\u2090\u1D47 f(x)\u00B7g(x) dx"], "b", "easy"),
    ("ch7", "Revolve y=x, 0\u2264x\u22642, around the x-axis. Find the volume (disk method)",
     ["8\u03C0/3", "4\u03C0", "2\u03C0", "16\u03C0/3"], "a", "hard"),
    ("ch7", "Find the area between y=x and y=x\u00B2 from x=0 to x=1",
     ["1/6", "1/3", "1/2", "5/6"], "a", "medium"),
    ("ch7", "The average value of f(x) on [a,b] is",
     ["(1/(b\u2212a)) \u222B\u2090\u1D47 f(x) dx", "\u222B\u2090\u1D47 f(x) dx", "f(b)\u2212f(a)", "(f(a)+f(b))/2"], "a", "medium"),
    ("ch7", "Find the area under y=3x\u00B2 from x=1 to x=2",
     ["6", "7", "8", "9"], "b", "medium"),
    ("ch7", "The disk-method volume of revolution around the x-axis for f(x) from a to b is",
     ["\u03C0\u222B\u2090\u1D47 f(x) dx", "\u03C0\u222B\u2090\u1D47 [f(x)]\u00B2 dx", "2\u03C0\u222B\u2090\u1D47 f(x) dx", "\u222B\u2090\u1D47 [f(x)]\u00B2 dx"], "b", "medium"),
]


def main():
    with open("question_bank.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["question_id", "chapter_id", "question",
                          "option_a", "option_b", "option_c", "option_d",
                          "correct_option", "difficulty"])
        for i, (chapter_id, question, options, correct, difficulty) in enumerate(QUESTIONS, start=1):
            writer.writerow([f"q{i:03d}", chapter_id, question, *options, correct, difficulty])

    print(f"Wrote {len(QUESTIONS)} questions to question_bank.csv")
    from collections import Counter
    counts = Counter(q[0] for q in QUESTIONS)
    for ch_id, n in sorted(counts.items()):
        print(f"  {ch_id}: {n} questions")


if __name__ == "__main__":
    main()
