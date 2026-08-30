"""
api_client.py — the ONLY file that talks HTTP to the backend.

This replaces data.py's local CSV/hardcoded reads. Every function here
maps 1:1 to a FastAPI endpoint in backend/main.py. Streamlit itself
never touches Supabase directly — it only ever talks to this backend.
"""

import os
import requests
import streamlit as st

API_BASE = os.environ.get("STUDY_PLANNER_API", "http://localhost:8000")


def _get(path, **params):
    r = requests.get(f"{API_BASE}{path}", params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def _post(path, json=None):
    r = requests.post(f"{API_BASE}{path}", json=json, timeout=10)
    r.raise_for_status()
    return r.json()


def get_or_create_student() -> str:
    """Creates one guest student per browser session and caches the id
    in session_state, so mastery persists across tab switches/reruns
    for the duration of the session (and in Supabase, forever)."""
    if "student_id" not in st.session_state:
        student = _post("/students", json={"name": "Guest"})
        st.session_state.student_id = student["id"]
    return st.session_state.student_id


def fetch_chapters(student_id: str) -> list[dict]:
    return _get("/chapters", student_id=student_id)


def fetch_adaptive_questions(student_id, chapter_id, count, difficulty_filter="Mixed") -> dict:
    return _get(
        "/questions/adaptive",
        student_id=student_id,
        chapter_id=chapter_id,
        count=count,
        difficulty_filter=difficulty_filter,
    )


def submit_answers(student_id, chapter_id, difficulty_filter, answers: list[dict]) -> dict:
    return _post(
        "/submit",
        json={
            "student_id": student_id,
            "chapter_id": chapter_id,
            "difficulty_filter": difficulty_filter,
            "answers": answers,
        },
    )


def fetch_plan(student_id: str, budget: int) -> list[dict]:
    return _get("/plan", student_id=student_id, budget=budget)
