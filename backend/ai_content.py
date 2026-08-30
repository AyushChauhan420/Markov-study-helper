"""
ai_content.py — the "Fetcher": the only place that talks to an LLM.

Three jobs, all driven by the same pattern (ask for strict JSON, parse
defensively, validate every row before it touches the database):

  1. generate_exam_syllabus   — chapters + exam weightage for an exam
                                 the student picks that we don't have
                                 seeded yet (Feature 1: exam switcher).
  2. generate_questions       — a handful of starter MCQs per chapter/
                                 difficulty so a newly-added exam has
                                 something for /questions/adaptive to
                                 serve immediately.
  3. generate_diagnostic_questions — MCQs grounded in a student's own
                                 uploaded notes/question bank, not in
                                 general exam knowledge (Feature 2).

This is intentionally a single synchronous call per job rather than a
full agentic/RAG pipeline — enough to make the three features real for
a hackathon demo without pulling in a vector DB or an orchestration
framework. Swap providers later without changing the function
signatures below; nothing else in the app calls the LLM directly.

Backed by a local Ollama server instead of Google Gemini — no API key
required, but Ollama must be installed and running with the target
model pulled (see backend/.env.example).

IMPORTANT: unlike Gemini's response_mime_type="application/json" mode
(which could be paired with a strict response schema), Ollama's plain
format="json" only guarantees *valid* JSON — not any particular shape.
Left alone, local models frequently wrap a requested bare array in an
object (e.g. {"chapters": [...]}) or drift on key names, which used to
make every _ask_json() call quietly return zero usable rows instead of
erroring. Every caller below now passes a strict JSON Schema as the
`format`, which Ollama enforces via grammar-constrained decoding — the
model literally cannot emit a shape that doesn't match. _extract_json()
still keeps a tolerant unwrap/fallback path as a second line of
defense for older Ollama versions that ignore the schema.
"""

import json
import os
import re
import time

from dotenv import load_dotenv
import requests

# Loaded here too (not just in database.py) because ai_content.py can
# be imported before database.py in main.py's import order — without
# this, OLLAMA_MODEL/OLLAMA_HOST may not be in os.environ yet when
# _MODEL is computed below, silently falling back to the default.
load_dotenv()

_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
_REQUEST_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "120"))


def _ensure_configured():
    """Ollama needs no API key, but fail fast (with a helpful message)
    if the server isn't reachable at all, rather than letting the
    first real request time out mysteriously."""
    try:
        resp = requests.get(f"{_HOST}/api/tags", timeout=5)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(
            f"Couldn't reach Ollama at {_HOST} ({e}). Make sure Ollama is "
            f"installed and running (`ollama serve`) and that the model "
            f"\"{_MODEL}\" has been pulled (`ollama pull {_MODEL}`)."
        ) from e


# ---------------------------------------------------------------------
# JSON Schemas — one per job. Passed as Ollama's `format` field so the
# model is grammar-constrained to emit exactly this shape (a bare
# array of objects with these required keys), instead of just "some
# valid JSON". This is what actually fixes the "syllabus generation
# quietly returns []" failure: previously the model was free to wrap
# the array in an object or rename keys and still pass format="json".
# ---------------------------------------------------------------------
_SYLLABUS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "weight_pct": {"type": "number"},
        },
        "required": ["name", "weight_pct"],
    },
}

_MCQ_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "question": {"type": "string"},
            "option_a": {"type": "string"},
            "option_b": {"type": "string"},
            "option_c": {"type": "string"},
            "option_d": {"type": "string"},
            "correct_option": {"type": "string"},
            "difficulty": {"type": "string"},
        },
        "required": ["question", "option_a", "option_b", "option_c", "option_d", "correct_option"],
    },
}

_DIAGNOSTIC_MCQ_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "concept": {"type": "string"},
            "question": {"type": "string"},
            "option_a": {"type": "string"},
            "option_b": {"type": "string"},
            "option_c": {"type": "string"},
            "option_d": {"type": "string"},
            "correct_option": {"type": "string"},
            "difficulty": {"type": "string"},
        },
        "required": ["concept", "question", "option_a", "option_b", "option_c", "option_d", "correct_option"],
    },
}


def _ask_json(prompt: str, schema: dict, max_tokens: int = 2000, _retries: int = 3):
    """Calls the local Ollama model and parses the JSON response,
    retrying with backoff on empty/malformed/empty-after-validation
    responses. `schema` is passed as Ollama's structured-outputs
    format so the model is constrained to the exact shape the caller
    expects — this is what prevents the "valid JSON, wrong shape,
    quietly parses to []" failure mode. Exam creation fires many calls
    back-to-back (1 syllabus + several chapters), and local models can
    still occasionally return truncated JSON under load — each retry
    also raises the token budget, since a truncated response usually
    means the budget was too tight for that particular prompt, not
    just a random blip."""
    _ensure_configured()
    last_err = None
    for attempt in range(_retries):
        budget = max(max_tokens, 2048) * (attempt + 1)  # 1x, 2x, 3x
        try:
            resp = requests.post(
                f"{_HOST}/api/generate",
                json={
                    "model": _MODEL,
                    "prompt": prompt,
                    "format": schema,
                    "stream": False,
                    "options": {
                        "num_predict": budget,
                        "temperature": 0.3,
                    },
                },
                timeout=_REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            last_err = f"request failed ({e}), budget={budget}"
            time.sleep(2 * (attempt + 1))
            continue

        text = (resp.json().get("response") or "").strip()
        if text:
            try:
                data = _extract_json(text)
            except json.JSONDecodeError as e:
                last_err = f"malformed JSON ({e}), budget={budget}, raw={text[:300]!r}"
                time.sleep(2 * (attempt + 1))
                continue
            if data:
                return data
            last_err = f"model returned a validly-shaped but empty result, budget={budget}, raw={text[:300]!r}"
        else:
            last_err = f"empty response, budget={budget}"
        time.sleep(2 * (attempt + 1))  # back off before retrying
    raise RuntimeError(f"Ollama call failed after {_retries} attempts: {last_err}")


def _extract_json(text: str):
    """Models occasionally wrap JSON in a ```json fence, or add a
    stray sentence before/after it, even when told not to — strip
    that before parsing instead of failing the request.

    Also tolerates the model wrapping the requested array in an
    object (e.g. {"chapters": [...]}) despite the enforced schema —
    unwraps the first list value found in that case. This is a
    fallback safety net; the schema passed to _ask_json() is the
    primary fix and should make this unwrap unnecessary on Ollama
    versions that support structured outputs (0.5+)."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    else:
        # Fall back to grabbing the outermost [...] or {...} block in
        # case the model added prose around the JSON despite the
        # format request.
        bracket = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
        if bracket:
            text = bracket.group(1).strip()
    data = json.loads(text)
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                return value
        return []
    return data


def generate_exam_syllabus(exam_name: str) -> list[dict]:
    """Returns [{"name": str, "weight_pct": float}, ...] — the real
    chapter/unit breakdown of the named exam, weighted by how much of
    the exam each chapter is worth. 6-10 chapters, weights ~sum to 100."""
    prompt = f"""You are an expert on the syllabus and marks weightage of the exam "{exam_name}".

Return a JSON array of this exam's main chapters/units, each with its
approximate share of the exam by marks/weightage. Aim for 6-10
chapters. Weightages should sum to approximately 100.

Each item must have exactly these fields: "name" (string) and
"weight_pct" (number)."""
    data = _ask_json(prompt, schema=_SYLLABUS_SCHEMA, max_tokens=1200)
    out = []
    for c in data:
        if "name" in c and "weight_pct" in c:
            try:
                out.append({"name": str(c["name"]).strip(), "weight_pct": float(c["weight_pct"])})
            except (TypeError, ValueError):
                continue
    return out


def generate_questions_for_chapter(exam_name: str, chapter_name: str, mix: dict[str, int]) -> list[dict]:
    """Returns [{"question","option_a".."option_d","correct_option",
    "difficulty"}, ...] for ALL difficulties in one call instead of
    one call per difficulty. Keeps exam creation fast even on a local
    model by not firing 3x the requests per chapter."""
    mix = {d: n for d, n in mix.items() if n > 0}
    if not mix:
        return []
    counts_desc = ", ".join(f"{n} {d}-difficulty" for d, n in mix.items())
    total = sum(mix.values())
    prompt = f"""Write multiple-choice practice questions for the "{chapter_name}"
chapter of the exam "{exam_name}": {counts_desc} questions ({total} total).

Return a JSON array. Each item must have exactly these fields:
"question", "option_a", "option_b", "option_c", "option_d"
(all strings), "correct_option" (one of "a","b","c","d"), and
"difficulty" (one of "easy","medium","hard", matching the difficulty
you were asked to write that question at). Keep each question and
option concise. Make wrong options plausible, not silly."""
    data = _ask_json(prompt, schema=_MCQ_SCHEMA, max_tokens=400 + total * 220)
    return _validate_mcqs(data, extra_fields={"difficulty": "medium"})


def generate_questions(exam_name: str, chapter_name: str, difficulty: str, count: int) -> list[dict]:
    """Returns [{"question","option_a".."option_d","correct_option"}, ...]
    for one chapter at one difficulty. Kept for any other callers —
    exam creation now uses generate_questions_for_chapter() instead to
    cut API calls."""
    if count <= 0:
        return []
    prompt = f"""Write {count} original {difficulty}-difficulty multiple-choice
practice questions for the "{chapter_name}" chapter of the exam "{exam_name}".

Return a JSON array. Each item must have exactly these fields:
"question", "option_a", "option_b", "option_c", "option_d" (all
strings), and "correct_option" (one of "a","b","c","d"). Keep each
question and option concise. Make wrong options plausible, not silly."""
    data = _ask_json(prompt, schema=_MCQ_SCHEMA, max_tokens=400 + count * 220)
    return _validate_mcqs(data, extra_fields={})


def generate_diagnostic_questions(source_text: str, count: int) -> list[dict]:
    """Grounds questions in material the student uploaded rather than
    general exam knowledge, so the diagnostic tests THEIR notes/
    question bank, not what the model already knows about the subject.
    Returns [{"concept","question","option_a".."option_d",
    "correct_option","difficulty"}, ...]."""
    if count <= 0:
        return []
    prompt = f"""Below is study material a student uploaded. Write {count}
multiple-choice questions that test understanding of concepts ACTUALLY
PRESENT in this material — don't invent unrelated questions, and don't
rely on outside knowledge the material doesn't cover. Tag each question
with the short concept/topic name (from the material) that it tests.

Return a JSON array. Each item must have exactly these fields:
"concept" (short topic name string), "question", "option_a",
"option_b", "option_c", "option_d" (all strings), "correct_option"
(one of "a","b","c","d"), and "difficulty" (one of
"easy","medium","hard").

MATERIAL:
\"\"\"
{source_text}
\"\"\""""
    data = _ask_json(prompt, schema=_DIAGNOSTIC_MCQ_SCHEMA, max_tokens=500 + count * 250)
    return _validate_mcqs(data, extra_fields={"concept": "General", "difficulty": "medium"})


def _validate_mcqs(data, extra_fields: dict) -> list[dict]:
    required = ("question", "option_a", "option_b", "option_c", "option_d", "correct_option")
    out = []
    for q in data:
        if not isinstance(q, dict) or not all(k in q for k in required):
            continue
        opt = str(q["correct_option"]).strip().lower()
        if opt not in ("a", "b", "c", "d"):
            continue
        row = {k: q[k] for k in required}
        row["correct_option"] = opt
        for field, default in extra_fields.items():
            row[field] = str(q.get(field, default)).strip().lower() if field == "difficulty" else str(q.get(field, default)).strip()
            if not row[field]:
                row[field] = default
        out.append(row)
    return out