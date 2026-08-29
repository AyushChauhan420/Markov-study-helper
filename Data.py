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
  - Replace QUIZ_BANK with real questions, keyed by chapter id.
  - Update SOURCE_LABEL to describe where the weighting came from.
"""

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


# Keyed by chapter id. Chapters without an entry here just skip the
# quiz step in the Check-in tab (self-rating only) — see tabs.py.
QUIZ_BANK = {
    "ch0": {
        "question": "Evaluate lim(x→3) (x² − 9)/(x − 3)",
        "options": ["9", "6", "0", "undefined"],
        "correct_index": 1,
    },
    "ch1": {
        "question": "Find d/dx [4x³ − 2x + 7]",
        "options": ["12x²+7", "12x²−2", "4x²−2", "12x³−2x"],
        "correct_index": 1,
    },
    "ch2": {
        "question": "Find d/dx [(3x + 1)⁵]",
        "options": ["5(3x+1)⁴", "15(3x+1)⁴", "3(3x+1)⁴", "15(3x+1)⁵"],
        "correct_index": 1,
    },
}
