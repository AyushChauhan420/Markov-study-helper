"""
engine.py — the actual "intelligence" of the app, now living on the
backend instead of being recomputed client-side out of session_state.

Two things used to be broken per the organizer's feedback:
  1. No backend/DB — mastery lived only in st.session_state and reset
     every time the page reloaded.
  2. Questions weren't chosen based on mastery/the Markov model at all
     — Tabs.py just sliced the first N rows of the filtered CSV
     (`active_questions = filtered_questions[:num_questions]`).

This module fixes #2: `pick_difficulty_mix` turns the *current* Markov
state into a difficulty distribution, and `select_adaptive_questions`
samples from Supabase using that mix while excluding questions the
student has already seen recently (via the `attempts` table).
"""

import random

import numpy as np

STATES = ["Confused", "Practicing", "Mastered"]

# Transition matrices, unchanged from the original prototype's
# 3-state Markov chain (Confused / Practicing / Mastered), keyed by
# how well the student just performed relative to the difficulty
# they attempted.
_TRANSITIONS = {
    "high": np.array([[0.10, 0.30, 0.60], [0.05, 0.25, 0.70], [0.00, 0.10, 0.90]]),
    "mid": np.array([[0.30, 0.50, 0.20], [0.15, 0.60, 0.25], [0.05, 0.35, 0.60]]),
    "low": np.array([[0.70, 0.20, 0.10], [0.40, 0.50, 0.10], [0.20, 0.50, 0.30]]),
}

_DIFFICULTY_WEIGHT = {"easy": 0.8, "medium": 1.0, "hard": 1.3, "mixed": 1.0}


def calculate_markov_standing(num_correct: int, total: int, difficulty: str, prior_mastery: float):
    """3-step Markov forecast of the student's state, given a just-
    completed practice set. Returns (state_name, [p_confused, p_practicing, p_mastered])."""
    if total <= 0:
        return "Practicing", [0.2, 0.6, 0.2]

    accuracy = num_correct / float(total)
    weight = _DIFFICULTY_WEIGHT.get(str(difficulty).lower(), 1.0)
    performance = min(1.0, accuracy * weight)

    v0 = np.array([max(0.0, 1.0 - prior_mastery), prior_mastery * 0.5, prior_mastery * 0.5])
    v0 = v0 / v0.sum()

    if performance >= 0.75:
        P = _TRANSITIONS["high"]
    elif performance >= 0.4:
        P = _TRANSITIONS["mid"]
    else:
        P = _TRANSITIONS["low"]

    v_future = v0 @ np.linalg.matrix_power(P, 3)
    state = STATES[int(np.argmax(v_future))]
    return state, v_future.tolist()


def update_mastery(prior_mastery: float, num_correct: int, total: int) -> float:
    """BKT-flavored mastery update: blend the prior estimate with the
    evidence from this practice set rather than overwriting it outright,
    so a single lucky/unlucky set can't swing mastery wildly."""
    if total <= 0:
        return prior_mastery
    score_frac = num_correct / total
    evidence = min(0.97, max(0.05, 0.1 + 0.85 * score_frac))
    # 60% new evidence / 40% prior — recent performance dominates but
    # doesn't erase history, similar in spirit to a BKT p(know) update.
    blended = 0.6 * evidence + 0.4 * prior_mastery
    return round(min(0.97, max(0.05, blended)), 3)


def pick_difficulty_mix(mastery: float, markov_state: str, count: int) -> dict[str, int]:
    """This is the piece that was previously missing entirely: turn
    the student's *current* mastery/Markov state into how many easy /
    medium / hard questions they get, instead of just slicing the CSV
    in file order."""
    if markov_state == "Confused" or mastery < 0.4:
        ratios = {"easy": 0.6, "medium": 0.3, "hard": 0.1}
    elif markov_state == "Mastered" or mastery >= 0.7:
        ratios = {"easy": 0.1, "medium": 0.3, "hard": 0.6}
    else:
        ratios = {"easy": 0.2, "medium": 0.6, "hard": 0.2}

    raw = {k: v * count for k, v in ratios.items()}
    mix = {k: int(v) for k, v in raw.items()}
    remainder = count - sum(mix.values())
    # hand out leftover slots to the largest fractional remainders
    for k in sorted(raw, key=lambda k: raw[k] - mix[k], reverse=True)[:remainder]:
        mix[k] += 1
    return mix


def select_adaptive_questions(all_questions: list[dict], seen_ids: set[str], mix: dict[str, int]) -> list[dict]:
    """Samples questions per the difficulty mix, preferring ones the
    student hasn't seen yet; falls back to repeats only if a chapter's
    bank is too small (keeps the demo robust on a small seeded bank)."""
    by_difficulty: dict[str, list[dict]] = {"easy": [], "medium": [], "hard": []}
    for q in all_questions:
        by_difficulty.setdefault(q["difficulty"], []).append(q)

    selected: list[dict] = []
    for difficulty, n in mix.items():
        pool = by_difficulty.get(difficulty, [])
        fresh = [q for q in pool if q["id"] not in seen_ids]
        random.shuffle(fresh)
        random.shuffle(pool)
        chosen = fresh[:n]
        if len(chosen) < n:
            backfill = [q for q in pool if q["id"] not in {c["id"] for c in chosen}]
            chosen += backfill[: n - len(chosen)]
        selected.extend(chosen)

    random.shuffle(selected)
    return selected
