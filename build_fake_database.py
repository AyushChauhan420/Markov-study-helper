"""
build_fake_database.py

Builds the team's "fake database" as a set of linked CSV files -- this is
what the plan meant by "Database: CSV files loaded via Pandas."

Produces, inside ./mock_db/:

    chapters.csv           -- id, name, weight_pct (reference table)
    students.csv            -- student_id, display_name, cohort
    attempts.csv             -- user_id, skill_name, correct, order_id, timestamp
                                 (long-format quiz log -- feed this to Ayush's pyBKT script)
    mastery_snapshot.csv    -- student_id, chapter_id, mastery
                                 (precomputed fallback -- Shashwat can demo against
                                 this directly via bridge.to_chapter_format() even
                                 if Ayush's live pyBKT pipeline isn't finished yet)

Everything keys off the SAME chapter ids as bridge.py's get_default_chapters(),
so there's exactly one chapter list for the whole team, not four slightly
different copies.

Usage:
    python build_fake_database.py
"""

import os
import csv
import random
from datetime import datetime, timedelta

random.seed(42)  # reproducible -- same "database" every time you regenerate it

OUTPUT_DIR = "mock_db"

# ------------------------------------------------------------------
# Chapters -- pulled from bridge.py if it's sitting next to this script,
# so there is truly one source of truth. Falls back to an inline copy
# (kept identical to bridge.py's get_default_chapters()) if bridge.py
# isn't importable yet, so this script never blocks on file order.
# ------------------------------------------------------------------
try:
    from bridge import get_default_chapters
    CHAPTERS = [{k: v for k, v in ch.items() if k != "mastery"} for ch in get_default_chapters()]
except ImportError:
    CHAPTERS = [
        {"id": "ch0", "name": "Limits & Continuity", "weight_pct": 11},
        {"id": "ch1", "name": "Differentiation Basics", "weight_pct": 11},
        {"id": "ch2", "name": "Chain & Implicit Rules", "weight_pct": 11},
        {"id": "ch3", "name": "Applied Rates of Change", "weight_pct": 12.5},
        {"id": "ch4", "name": "Curve Sketching", "weight_pct": 16.5},
        {"id": "ch5", "name": "Integration Techniques", "weight_pct": 18.5},
        {"id": "ch6", "name": "Differential Equations", "weight_pct": 9},
        {"id": "ch7", "name": "Applications of Integrals", "weight_pct": 12.5},
    ]

# prereq map used only to shape realistic mock attempt data (not part of
# Shashwat's UI format) -- chapter_id -> prereq_chapter_id or None
PREREQS = {
    "ch0": None, "ch1": None,
    "ch2": "ch1", "ch3": "ch1",
    "ch4": "ch2", "ch5": "ch0",
    "ch6": "ch5", "ch7": "ch5",
}

N_STUDENTS = 40
FIRST_NAMES = ["Aarav", "Diya", "Vihaan", "Ananya", "Kabir", "Ishita", "Reyansh", "Myra",
               "Aditya", "Sara", "Arjun", "Anika", "Vivaan", "Kiara", "Rohan", "Zara",
               "Kian", "Naina", "Yash", "Riya"]

MIN_ATTEMPTS = 5
MAX_ATTEMPTS = 10


def clamp(v, lo=0.02, hi=0.97):
    return max(lo, min(hi, v))


def build_students():
    rows = []
    for i in range(1, N_STUDENTS + 1):
        name = f"{random.choice(FIRST_NAMES)} {chr(65 + (i % 26))}."
        cohort = random.choice(["Morning", "Evening"])
        rows.append({"student_id": f"student_{i:03d}", "display_name": name, "cohort": cohort})
    return rows


def simulate_student_attempts(student_id, start_time):
    """One student's full attempt log across all chapters, with a per-attempt
    learning curve and a prerequisite boost when a prereq chapter is already
    'mastered' (3 correct in a row) -- gives pyBKT (and the demo) a real
    learning signal instead of noise."""
    rows = []
    mastered = {ch["id"]: False for ch in CHAPTERS}
    order = [ch["id"] for ch in CHAPTERS]
    random.shuffle(order)
    t = start_time

    for chapter_id in order:
        prereq = PREREQS.get(chapter_id)
        base_prob = 0.20 + random.random() * 0.20  # 0.20-0.40 starting point, varies per student
        prereq_boost = 0.15 if (prereq and mastered.get(prereq)) else 0.0
        p_correct = clamp(base_prob + prereq_boost)
        streak = 0

        n_attempts = random.randint(MIN_ATTEMPTS, MAX_ATTEMPTS)
        for attempt in range(1, n_attempts + 1):
            is_correct = 1 if random.random() < p_correct else 0
            t += timedelta(minutes=random.randint(1, 4))
            rows.append({
                "user_id": student_id,
                "skill_name": chapter_id,
                "correct": is_correct,
                "order_id": attempt,
                "timestamp": t.isoformat(timespec="minutes"),
            })
            if is_correct:
                p_correct = clamp(p_correct + 0.09)
                streak += 1
            else:
                p_correct = clamp(p_correct - 0.04)
                streak = 0
            if streak >= 3:
                mastered[chapter_id] = True

    return rows, mastered


def build_attempts_and_snapshot(students):
    attempt_rows = []
    snapshot_rows = []
    start = datetime(2026, 8, 29, 9, 0)

    for s in students:
        rows, mastered_flags = simulate_student_attempts(s["student_id"], start)
        attempt_rows.extend(rows)

        # mastery_snapshot: average correctness over each student's LAST 3
        # attempts per chapter -- a cheap, explainable stand-in for a real
        # BKT posterior, good enough for a demo fallback
        for ch in CHAPTERS:
            chapter_attempts = [r["correct"] for r in rows if r["skill_name"] == ch["id"]]
            recent = chapter_attempts[-3:] if chapter_attempts else []
            mastery = sum(recent) / len(recent) if recent else 0.3
            # nudge mastered chapters up so the snapshot visually agrees with
            # the "mastered" flag used to drive prereq boosts above
            if mastered_flags[ch["id"]]:
                mastery = clamp(max(mastery, 0.75))
            snapshot_rows.append({
                "student_id": s["student_id"],
                "chapter_id": ch["id"],
                "mastery": round(mastery, 3),
            })

    return attempt_rows, snapshot_rows


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    students = build_students()
    attempts, snapshot = build_attempts_and_snapshot(students)

    write_csv(os.path.join(OUTPUT_DIR, "chapters.csv"), CHAPTERS, ["id", "name", "weight_pct"])
    write_csv(os.path.join(OUTPUT_DIR, "students.csv"), students, ["student_id", "display_name", "cohort"])
    write_csv(os.path.join(OUTPUT_DIR, "attempts.csv"), attempts,
              ["user_id", "skill_name", "correct", "order_id", "timestamp"])
    write_csv(os.path.join(OUTPUT_DIR, "mastery_snapshot.csv"), snapshot,
              ["student_id", "chapter_id", "mastery"])

    print(f"Wrote fake database to ./{OUTPUT_DIR}/")
    print(f"  chapters.csv          {len(CHAPTERS)} rows")
    print(f"  students.csv          {len(students)} rows")
    print(f"  attempts.csv          {len(attempts)} rows")
    print(f"  mastery_snapshot.csv  {len(snapshot)} rows")


if __name__ == "__main__":
    main()
