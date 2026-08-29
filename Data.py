"""
data.py — every piece of mock/placeholder content lives here.

This is the ONLY file you should need to touch to swap in real data
later (a database, an API, a CSV upload, etc). Nothing in theme.py,
components.py, or tabs.py should reference hardcoded chapter names —
they all read from get_default_chapters() / QUIZ_BANK / SOURCE_LABEL.

To wire in real data later:
  - Replace get_default_chapters() with a function that loads from
    your database / API / uploaded file, returning the same shape:
    [{"id": str, "name": str, "weight_pct": float, "mastery": float}, ...]
  - Add/edit questions in question_bank.csv (see build_question_bank.py),
    keyed by chapter id. Chapters with no questions yet just show a
    "no questions" message in the Check-in tab.
  - Update SOURCE_LABEL to describe where the weighting came from.
"""

import os
import pandas as pd

SOURCE_LABEL = "AP Calculus AB · official unit weighting (placeholder)"


def get_default_chapters():
    """Returns the starting chapter list. Swap this for a real data source."""
    return [
        {"id": "ch0", "name": "Limits & Continuity", "weight_pct": 11, "mastery": 0.62},
        {"id": "ch1", "name": "Differentiation Basics", "weight_pct": 11, "mastery": 0.44},
        {"id": "ch2", "name": "Chain & Implicit Rules", "weight_pct": 11, "mastery": 0.30},
        {"id": "ch3", "name": "Applied Rates of Change", "weight_pct": 12.5, "mastery": 0.51},
        {"id": "ch4", "name": "Curve Sketching", "weight_pct": 16.5, "mastery": 0.22},
        {"id": "ch5", "name": "Integration Techniques", "weight_pct": 18.5, "mastery": 0.35},
        {"id": "ch6", "name": "Differential Equations", "weight_pct": 9, "mastery": 0.68},
        {"id": "ch7", "name": "Applications of Integrals", "weight_pct": 12.5, "mastery": 0.40},
    ]



QUESTION_BANK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "question_bank.csv")

_FALLBACK_BANK = {
    "ch0": [{"id": "fallback0", "question": "Evaluate lim(x\u21923) (x\u00B2 \u2212 9)/(x \u2212 3)",
             "options": ["9", "6", "0", "undefined"], "correct_index": 1, "difficulty": "easy"}],
    "ch1": [{"id": "fallback1", "question": "Find d/dx [4x\u00B3 \u2212 2x + 7]",
             "options": ["12x\u00B2+7", "12x\u00B2\u22122", "4x\u00B2\u22122", "12x\u00B3\u22122x"], "correct_index": 1, "difficulty": "easy"}],
    "ch2": [{"id": "fallback2", "question": "Find d/dx [(3x + 1)\u2075]",
             "options": ["5(3x+1)\u2074", "15(3x+1)\u2074", "3(3x+1)\u2074", "15(3x+1)\u2075"], "correct_index": 1, "difficulty": "easy"}],
}


def load_question_bank(path: str = QUESTION_BANK_PATH) -> dict:
    """Loads the MCQ bank from CSV, grouped by chapter_id. Letter answers
    (a/b/c/d) in the CSV are converted to 0-based option indices here."""
    if not os.path.exists(path):
        return _FALLBACK_BANK

    df = pd.read_csv(path)
    letter_to_index = {"a": 0, "b": 1, "c": 2, "d": 3}
    bank: dict = {}
    for _, row in df.iterrows():
        bank.setdefault(row["chapter_id"], []).append({
            "id": row["question_id"],
            "question": row["question"],
            "options": [row["option_a"], row["option_b"], row["option_c"], row["option_d"]],
            "correct_index": letter_to_index.get(str(row["correct_option"]).strip().lower(), 0),
            "difficulty": row.get("difficulty", "medium"),
        })
    return bank


QUESTION_BANK = load_question_bank()
