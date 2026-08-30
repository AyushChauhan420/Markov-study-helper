"""
seed.py — run once after applying schema.sql:

    python seed.py

Loads chapters.csv and question_bank.csv (same files the old
hardcoded prototype shipped with) into Supabase so the backend has
real data to serve from instead of an in-memory dict.
"""

import os
import pandas as pd
from database import get_supabase

HERE = os.path.dirname(os.path.abspath(__file__))


DEFAULT_EXAM_ID = "ap-calc-ab"


def seed_exams(sb):
    sb.table("exams").upsert(
        {
            "id": DEFAULT_EXAM_ID,
            "name": "AP Calculus AB",
            "description": "The prototype's original exam — chapters.csv / question_bank.csv.",
            "source": "seed",
        }
    ).execute()
    print(f"seeded default exam: {DEFAULT_EXAM_ID}")


def seed_chapters(sb):
    df = pd.read_csv(os.path.join(HERE, "chapters.csv"))
    df["exam_id"] = DEFAULT_EXAM_ID
    rows = df.to_dict(orient="records")
    sb.table("chapters").upsert(rows).execute()
    print(f"seeded {len(rows)} chapters")


def seed_questions(sb):
    df = pd.read_csv(os.path.join(HERE, "question_bank.csv"))
    rows = []
    for _, r in df.iterrows():
        rows.append(
            {
                "id": r["question_id"],
                "chapter_id": r["chapter_id"],
                "question": r["question"],
                "option_a": r["option_a"],
                "option_b": r["option_b"],
                "option_c": r["option_c"],
                "option_d": r["option_d"],
                "correct_option": str(r["correct_option"]).strip().lower(),
                "difficulty": str(r.get("difficulty", "medium")).strip().lower(),
            }
        )
    # batch insert to stay well under request size limits
    batch_size = 200
    for i in range(0, len(rows), batch_size):
        sb.table("questions").upsert(rows[i : i + batch_size]).execute()
    print(f"seeded {len(rows)} questions")


if __name__ == "__main__":
    sb = get_supabase()
    seed_exams(sb)
    seed_chapters(sb)
    seed_questions(sb)
    print("done.")
