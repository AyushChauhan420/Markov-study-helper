"""
bridge.py

The integration glue between Ayush's algorithm and Shashwat's UI.

Shashwat's Streamlit app expects a list of dicts shaped exactly like this
(from his get_default_chapters()):

    {"id": "ch0", "name": "Limits & Continuity", "weight_pct": 11, "mastery": 0.62}

This file owns that shape. It doesn't care HOW mastery was computed --
mock data, a real pyBKT model, or a hardcoded dict all work the same way.
That's the point: Ayush's function can change internally without breaking
Shashwat's UI, as long as it still hands you a {skill_id: mastery_float} dict.
"""

# ------------------------------------------------------------------
# Shashwat's own function, copied verbatim -- this is the ONE source of
# truth for chapter id / name / weight_pct, so nothing here can drift
# out of sync with his UI on its own.
#
# IMPORTANT: if Shashwat edits get_default_chapters() in his app.py
# (renames a chapter, changes a weight, adds one), copy the change here
# too. Even better -- once his filename is settled, delete this copy
# and replace it with a real import, e.g.:
#     from app import get_default_chapters
# ------------------------------------------------------------------
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


def to_chapter_format(mastery_by_skill: dict) -> list:
    """
    mastery_by_skill: {"ch0": 0.62, "ch1": 0.44, ...}  -- real mastery from
    Ayush's model, skill_id -> mastery (0-1).

    Pulls id/name/weight_pct straight from get_default_chapters() above and
    only overwrites "mastery" -- so renaming/reweighting a chapter in
    Shashwat's function is the only edit ever needed. If a skill is missing
    from Ayush's output (e.g. still training), falls back to Shashwat's own
    placeholder mastery value instead of crashing the UI.
    """
    chapters = get_default_chapters()
    return [
        {**ch, "mastery": round(mastery_by_skill.get(ch["id"], ch["mastery"]), 3)}
        for ch in chapters
    ]


def mastery_from_pybkt_predictions(predictions_df, student_id, skill_col="skill_name",
                                    user_col="user_id", pred_col="correct_predictions"):
    """
    Collapses per-attempt pyBKT predictions down to ONE mastery float per
    skill for ONE student -- exactly what to_chapter_format() needs.

    predictions_df: whatever Ayush's model.predict(...) call returns.
    Uses that student's most recent predicted probability per skill as
    the "current mastery" estimate. Ask Ayush to confirm his actual
    column names match skill_col/user_col/pred_col -- adjust the
    defaults above if his output differs.
    """
    student_rows = predictions_df[predictions_df[user_col] == student_id]
    mastery = {}
    for skill_id, group in student_rows.groupby(skill_col):
        # last attempt = most up-to-date mastery estimate for that skill
        mastery[skill_id] = float(group.iloc[-1][pred_col])
    return mastery


# ------------------------------------------------------------------
# QUICK TEST -- run this file directly to confirm the shape is right
# before Ayush's real function exists. Swap FAKE_MASTERY for
# mastery_from_pybkt_predictions(...) once his output is ready.
# ------------------------------------------------------------------
if __name__ == "__main__":
    # simulate a partially-trained model: only some skills have real mastery
    # yet, the rest should fall back to Shashwat's placeholder values
    PARTIAL_MASTERY = {"ch0": 0.71, "ch4": 0.19, "ch6": 0.55}
    chapters = to_chapter_format(PARTIAL_MASTERY)
    for c in chapters:
        print(c)
