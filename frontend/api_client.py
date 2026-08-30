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
    r = requests.get(f"{API_BASE}{path}", params=params, timeout=120)
    r.raise_for_status()
    return r.json()


def _post(path, json=None):
    # 300s (not the old 10s): adding a brand-new exam triggers ~20-30
    # sequential Ollama calls server-side (1 syllabus + several
    # chapters x 3 difficulties of starter questions). A local model
    # is generally slower than a hosted API, so this can legitimately
    # take a few minutes the first time, especially on CPU-only setups.
    r = requests.post(f"{API_BASE}{path}", json=json, timeout=300)
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


def fetch_exams() -> list[dict]:
    return _get("/exams")


def select_exam(name: str) -> dict:
    """Looks up the exam by name. If it's new, the backend uses AI to
    generate its syllabus + a starter question bank on the spot — can
    take several seconds the first time a given exam is picked."""
    return _post("/exams", json={"name": name})


def fetch_chapters(student_id: str, exam_id: str) -> list[dict]:
    return _get("/chapters", student_id=student_id, exam_id=exam_id)


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


def fetch_plan(student_id: str, exam_id: str, budget: int) -> list[dict]:
    return _get("/plan", student_id=student_id, exam_id=exam_id, budget=budget)


def generate_diagnostic(student_id: str, uploaded_file, count: int) -> dict:
    """uploaded_file is a Streamlit UploadedFile from st.file_uploader.
    Parsing + AI generation happens server-side; give it a longer
    timeout than the other calls since it does both."""
    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
    data = {"student_id": student_id, "count": str(count)}
    # Raised from 90s: retries with increasing token budget (up to 3
    # attempts, with backoff sleep between them) can legitimately push
    # a single diagnostic generation past 90s for a longer document.
    r = requests.post(f"{API_BASE}/diagnostic/generate", files=files, data=data, timeout=180)
    r.raise_for_status()
    return r.json()


def submit_diagnostic(set_id: str, student_id: str, answers: list[dict]) -> dict:
    return _post(
        "/diagnostic/submit",
        json={"set_id": set_id, "student_id": student_id, "answers": answers},
    )
