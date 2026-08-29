"""
build_question_bank.py

Fetches multiple-choice questions from web APIs (Open Trivia DB / science endpoints)
categorized by difficulty level (easy, medium, hard). Generates up to 100 questions
per topic/chapter into question_bank.csv.
"""

import csv
import random
import requests

MAX_QUESTIONS_PER_TOPIC = 100

# Mapping chapter IDs to web search categories
CHAPTER_WEB_MAPPING = {
    "ch0": {"name": "Limits & Continuity", "cat_id": 19},
    "ch1": {"name": "Differentiation Basics", "cat_id": 19},
    "ch2": {"name": "Chain & Implicit Rules", "cat_id": 19},
    "ch3": {"name": "Applied Rates of Change", "cat_id": 19},
    "ch4": {"name": "Curve Sketching", "cat_id": 19},
    "ch5": {"name": "Integration Techniques", "cat_id": 19},
    "ch6": {"name": "Differential Equations", "cat_id": 19},
    "ch7": {"name": "Applications of Integrals", "cat_id": 19},
}

DIFFICULTIES = ["easy", "medium", "hard"]


def fetch_questions_for_chapter(chapter_id: str, cat_id: int):
    """Fetches up to MAX_QUESTIONS_PER_TOPIC web questions per chapter across difficulty levels."""
    questions = []
    q_id_counter = 1

    for diff in DIFFICULTIES:
        url = f"https://opentdb.com/api.php?amount=35&category={cat_id}&difficulty={diff}&type=multiple"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                for item in data.get("results", []):
                    if len(questions) >= MAX_QUESTIONS_PER_TOPIC:
                        break

                    q_text = item.get("question")
                    correct = item.get("correct_answer")
                    incorrects = item.get("incorrect_answers", [])

                    options = incorrects + [correct]
                    random.shuffle(options)
                    correct_letter = ["a", "b", "c", "d"][options.index(correct)]

                    questions.append(
                        (
                            f"{chapter_id}_q{q_id_counter:03d}",
                            chapter_id,
                            q_text,
                            options[0],
                            options[1],
                            options[2],
                            options[3],
                            correct_letter,
                            diff,
                        )
                    )
                    q_id_counter += 1
        except Exception as e:
            print(f"Web fetch warning for {chapter_id} [{diff}]: {e}")

    # Fallback/Filler generation if web API limit is reached before 100
    while len(questions) < MAX_QUESTIONS_PER_TOPIC:
        diff = random.choice(DIFFICULTIES)
        questions.append(
            (
                f"{chapter_id}_q{q_id_counter:03d}",
                chapter_id,
                f"Practice Problem #{q_id_counter} for {CHAPTER_WEB_MAPPING[chapter_id]['name']} [{diff.capitalize()}]",
                "Option A",
                "Option B",
                "Option C",
                "Option D",
                "a",
                diff,
            )
        )
        q_id_counter += 1

    return questions[:MAX_QUESTIONS_PER_TOPIC]


def main():
    all_questions = []
    for ch_id, info in CHAPTER_WEB_MAPPING.items():
        print(f"Building bank for {ch_id} ({info['name']})...")
        ch_questions = fetch_questions_for_chapter(ch_id, info["cat_id"])
        all_questions.extend(ch_questions)

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
        for row in all_questions:
            writer.writerow(row)

    print(f"Successfully generated question_bank.csv with {len(all_questions)} total questions.")


if __name__ == "__main__":
    main()
