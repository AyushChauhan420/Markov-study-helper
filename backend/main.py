import re

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from ai_content import (
    generate_diagnostic_questions,
    generate_exam_syllabus,
    generate_questions_for_chapter,
)
from database import get_supabase
from engine import (
    calculate_markov_standing,
    pick_difficulty_mix,
    select_adaptive_questions,
    update_mastery,
)
from file_parser import chunk_text, extract_text
from models import (
    AdaptiveQuestionsResponse,
    Chapter,
    DiagnosticSetResponse,
    DiagnosticSubmitIn,
    DiagnosticSubmitResult,
    Exam,
    ExamSelectIn,
    PlanChapter,
    Question,
    Student,
    StudentCreate,
    SubmitIn,
    SubmitResult,
)

app = FastAPI(title="Study Planner API", version="1.0")

# Streamlit runs on a different port/origin during dev — wide open here
# since this is a hackathon demo; tighten allow_origins for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LETTER_TO_INDEX = {"a": 0, "b": 1, "c": 2, "d": 3}
DEFAULT_EXAM_ID = "ap-calc-ab"


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug[:60] or "exam"


# ---------------------------------------------------------------------
# Exams — Feature 1: switch which exam you're prepping for. Known
# exams are just read from Supabase; an unseen exam name triggers the
# "Fetcher" (ai_content.py) to generate its syllabus + a starter
# question bank on the spot.
# ---------------------------------------------------------------------
@app.get("/exams", response_model=list[Exam])
def list_exams():
    sb = get_supabase()
    rows = sb.table("exams").select("*").order("name").execute().data
    return [Exam(**r) for r in rows]


@app.post("/exams", response_model=Exam)
def select_or_create_exam(body: ExamSelectIn):
    sb = get_supabase()
    exam_id = _slugify(body.name)

    existing = sb.table("exams").select("*").eq("id", exam_id).maybe_single().execute()
    existing = existing.data if existing else None
    if existing:
        return Exam(**existing)

    syllabus = generate_exam_syllabus(body.name)
    if not syllabus:
        raise HTTPException(502, "Couldn't generate a syllabus for that exam right now — try again.")

    sb.table("exams").insert({"id": exam_id, "name": body.name.strip(), "source": "ai-generated"}).execute()

    chapter_rows = [
        {
            "id": f"{exam_id}__{_slugify(c['name'])}",
            "exam_id": exam_id,
            "name": c["name"],
            "weight_pct": c["weight_pct"],
        }
        for c in syllabus
    ]
    sb.table("chapters").insert(chapter_rows).execute()

    # Seed a small starter bank per chapter/difficulty so
    # /questions/adaptive has something to serve immediately, instead
    # of the student landing on an empty Practice tab.
    question_rows = []
    for chapter, chapter_row in zip(syllabus, chapter_rows):
        # One call per CHAPTER (all difficulties combined) instead of
        # one call per chapter x difficulty — cuts total Ollama calls
        # 3x, which matters a lot on slower local hardware.
        try:
            generated = generate_questions_for_chapter(
                body.name, chapter["name"], {"easy": 2, "medium": 2, "hard": 1}
            )
        except Exception as e:
            # Don't let one failed chapter abort the ENTIRE exam
            # creation — previously an exception here meant
            # question_rows never got inserted at all (insert happens
            # once, after the full loop), leaving every chapter with
            # zero questions even though the exam/chapters themselves
            # were already saved. Log and skip instead, so the
            # student still gets whatever generated successfully.
            print(f"[select_or_create_exam] question gen failed for {chapter_row['id']}: {e}")
            continue
        counters = {"easy": 0, "medium": 0, "hard": 0}
        for q in generated:
            difficulty = q.get("difficulty", "medium")
            if difficulty not in counters:
                difficulty = "medium"
            counters[difficulty] += 1
            question_rows.append(
                {
                    "id": f"{chapter_row['id']}_q{difficulty[0]}{counters[difficulty]}",
                    "chapter_id": chapter_row["id"],
                    "question": q["question"],
                    "option_a": q["option_a"],
                    "option_b": q["option_b"],
                    "option_c": q["option_c"],
                    "option_d": q["option_d"],
                    "correct_option": q["correct_option"],
                    "difficulty": difficulty,
                }
            )
    if question_rows:
        sb.table("questions").insert(question_rows).execute()

    # Self-heal instead of leaving a broken "zombie" exam behind: if
    # ANY chapter ended up with zero questions, the exam is unusable
    # (Practice tab 404s on that chapter forever) and previously
    # needed someone to manually delete it from Supabase. Instead,
    # roll the whole thing back and return a clean, retryable error —
    # any exam name, not just ones we've seen before, self-cleans on
    # a failed generation.
    chapters_with_questions = {row["chapter_id"] for row in question_rows}
    chapter_ids = [c["id"] for c in chapter_rows]
    if any(cid not in chapters_with_questions for cid in chapter_ids):
        sb.table("questions").delete().in_("chapter_id", chapter_ids).execute()
        sb.table("chapters").delete().eq("exam_id", exam_id).execute()
        sb.table("exams").delete().eq("id", exam_id).execute()
        raise HTTPException(
            502,
            f"Couldn't fully generate questions for \"{body.name.strip()}\" — "
            "this can happen if the AI is rate-limited. Please try again.",
        )

    return Exam(id=exam_id, name=body.name.strip(), source="ai-generated")


# ---------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------
@app.post("/students", response_model=Student)
def create_student(body: StudentCreate):
    sb = get_supabase()
    row = sb.table("students").insert({"name": body.name}).execute()
    return Student(id=row.data[0]["id"], name=row.data[0]["name"])


@app.get("/students/{student_id}", response_model=Student)
def get_student(student_id: str):
    sb = get_supabase()
    # .single() throws a hard exception (ugly 500) if no row matches,
    # instead of returning empty data — use .maybe_single() so a
    # missing/stale student_id cleanly hits the 404 below instead.
    row = sb.table("students").select("*").eq("id", student_id).maybe_single().execute()
    row_data = row.data if row else None
    if not row_data:
        raise HTTPException(404, "Student not found")
    return Student(id=row_data["id"], name=row_data["name"])


# ---------------------------------------------------------------------
# Chapters (merged with this student's live mastery/Markov state)
# ---------------------------------------------------------------------
@app.get("/chapters", response_model=list[Chapter])
def list_chapters(student_id: str = Query(...), exam_id: str = Query(DEFAULT_EXAM_ID)):
    sb = get_supabase()
    chapters = sb.table("chapters").select("*").eq("exam_id", exam_id).order("id").execute().data
    mastery_rows = (
        sb.table("student_mastery").select("*").eq("student_id", student_id).execute().data
    )
    mastery_by_chapter = {m["chapter_id"]: m for m in mastery_rows}

    out = []
    for c in chapters:
        m = mastery_by_chapter.get(c["id"])
        out.append(
            Chapter(
                id=c["id"],
                name=c["name"],
                weight_pct=float(c["weight_pct"]),
                mastery=float(m["mastery"]) if m else 0.3,
                markov_state=m["markov_state"] if m else "Practicing",
            )
        )
    return out


# ---------------------------------------------------------------------
# Adaptive question selection — the piece that was missing entirely
# ---------------------------------------------------------------------
@app.get("/questions/adaptive", response_model=AdaptiveQuestionsResponse)
def adaptive_questions(
    student_id: str = Query(...),
    chapter_id: str = Query(...),
    count: int = Query(10, ge=1, le=100),
    difficulty_filter: str = Query("Mixed"),
):
    sb = get_supabase()

    mastery_row = (
        sb.table("student_mastery")
        .select("*")
        .eq("student_id", student_id)
        .eq("chapter_id", chapter_id)
        .maybe_single()
        .execute()
    )
    mastery_row = mastery_row.data if mastery_row else None
    mastery = float(mastery_row["mastery"]) if mastery_row else 0.3
    markov_state = mastery_row["markov_state"] if mastery_row else "Practicing"

    all_questions = (
        sb.table("questions").select("*").eq("chapter_id", chapter_id).execute().data
    )
    if not all_questions:
        raise HTTPException(404, f"No questions found for chapter {chapter_id}")

    if difficulty_filter != "Mixed":
        all_questions = [q for q in all_questions if q["difficulty"] == difficulty_filter.lower()] or all_questions

    seen = (
        sb.table("attempts")
        .select("question_id")
        .eq("student_id", student_id)
        .eq("chapter_id", chapter_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
        .data
    )
    seen_ids = {row["question_id"] for row in seen}

    count = min(count, len(all_questions))
    mix = pick_difficulty_mix(mastery, markov_state, count)
    picked = select_adaptive_questions(all_questions, seen_ids, mix)

    questions = [
        Question(
            id=q["id"],
            chapter_id=q["chapter_id"],
            question=q["question"],
            options=[q["option_a"], q["option_b"], q["option_c"], q["option_d"]],
            difficulty=q["difficulty"],
        )
        for q in picked
    ]

    return AdaptiveQuestionsResponse(
        chapter_id=chapter_id,
        mastery=mastery,
        markov_state=markov_state,
        difficulty_mix=mix,
        questions=questions,
    )


# ---------------------------------------------------------------------
# Submit / grade — updates mastery + Markov state in Supabase
# ---------------------------------------------------------------------
@app.post("/submit", response_model=SubmitResult)
def submit(body: SubmitIn):
    sb = get_supabase()

    q_ids = [a.question_id for a in body.answers]
    questions = (
        sb.table("questions").select("*").in_("id", q_ids).execute().data
    )
    questions_by_id = {q["id"]: q for q in questions}

    mastery_row = (
        sb.table("student_mastery")
        .select("*")
        .eq("student_id", body.student_id)
        .eq("chapter_id", body.chapter_id)
        .maybe_single()
        .execute()
    )
    mastery_row = mastery_row.data if mastery_row else None
    prior_mastery = float(mastery_row["mastery"]) if mastery_row else 0.3

    per_question = []
    num_correct = 0
    attempt_rows = []
    for ans in body.answers:
        q = questions_by_id.get(ans.question_id)
        if not q:
            continue
        correct_index = LETTER_TO_INDEX[q["correct_option"]]
        is_correct = ans.selected_index == correct_index
        num_correct += int(is_correct)
        per_question.append(
            {
                "question_id": q["id"],
                "correct": is_correct,
                "correct_index": correct_index,
            }
        )
        attempt_rows.append(
            {
                "student_id": body.student_id,
                "chapter_id": body.chapter_id,
                "question_id": q["id"],
                "selected_option": "abcd"[ans.selected_index] if 0 <= ans.selected_index < 4 else None,
                "is_correct": is_correct,
                "difficulty": q["difficulty"],
            }
        )

    total = len(per_question)
    if total == 0:
        raise HTTPException(400, "No matching questions to grade")

    new_mastery = update_mastery(prior_mastery, num_correct, total)
    markov_state, probs = calculate_markov_standing(
        num_correct, total, body.difficulty_filter or "mixed", new_mastery
    )

    if attempt_rows:
        sb.table("attempts").insert(attempt_rows).execute()

    sb.table("student_mastery").upsert(
        {
            "student_id": body.student_id,
            "chapter_id": body.chapter_id,
            "mastery": new_mastery,
            "markov_state": markov_state,
            "state_probs": probs,
        }
    ).execute()

    return SubmitResult(
        num_correct=num_correct,
        total=total,
        mastery=new_mastery,
        markov_state=markov_state,
        state_probs=probs,
        per_question=per_question,
    )


# ---------------------------------------------------------------------
# Study plan — priority order + problem allocation, driven by live mastery
# ---------------------------------------------------------------------
@app.get("/plan", response_model=list[PlanChapter])
def plan(
    student_id: str = Query(...),
    exam_id: str = Query(DEFAULT_EXAM_ID),
    budget: int = Query(60, ge=10, le=200),
):
    chapters = list_chapters(student_id, exam_id)
    priority = sorted(chapters, key=lambda c: -(c.weight_pct * (1 - c.mastery)))
    total_gap = sum(c.weight_pct * (1 - c.mastery) for c in priority) or 1

    return [
        PlanChapter(
            id=c.id,
            name=c.name,
            weight_pct=c.weight_pct,
            mastery=c.mastery,
            problems=round(budget * (c.weight_pct * (1 - c.mastery)) / total_gap),
        )
        for c in priority
    ]


# ---------------------------------------------------------------------
# Diagnostic tests from uploaded material — Feature 2. A student
# uploads notes/a question bank/random material; we extract the text,
# hand it to the AI to write MCQs grounded in THAT material, store the
# generated set (so grading is deterministic even though the questions
# were generated on the fly), and grade it the same way /submit does.
# ---------------------------------------------------------------------
@app.post("/diagnostic/generate", response_model=DiagnosticSetResponse)
async def diagnostic_generate(
    student_id: str = Form(...),
    count: int = Form(8),
    file: UploadFile = File(...),
):
    content = await file.read()
    try:
        text = extract_text(file.filename, content)
    except ValueError as e:
        raise HTTPException(400, str(e))

    text = chunk_text(text)
    if len(text.strip()) < 50:
        raise HTTPException(400, "Couldn't find enough readable text in that file.")

    questions = generate_diagnostic_questions(text, count)
    if not questions:
        raise HTTPException(502, "The AI couldn't generate questions from this material — try a different file.")

    sb = get_supabase()
    set_row = sb.table("diagnostic_sets").insert(
        {"student_id": student_id, "source_name": file.filename}
    ).execute()
    set_id = set_row.data[0]["id"]

    q_rows = [
        {
            "id": f"diag_{set_id}_{i + 1}",
            "set_id": set_id,
            "concept": q["concept"],
            "question": q["question"],
            "option_a": q["option_a"],
            "option_b": q["option_b"],
            "option_c": q["option_c"],
            "option_d": q["option_d"],
            "correct_option": q["correct_option"],
            "difficulty": q["difficulty"],
        }
        for i, q in enumerate(questions)
    ]
    sb.table("diagnostic_questions").insert(q_rows).execute()

    return DiagnosticSetResponse(
        set_id=set_id,
        source_name=file.filename,
        questions=[
            {
                "id": r["id"],
                "concept": r["concept"],
                "question": r["question"],
                "options": [r["option_a"], r["option_b"], r["option_c"], r["option_d"]],
                "difficulty": r["difficulty"],
            }
            for r in q_rows
        ],
    )


@app.post("/diagnostic/submit", response_model=DiagnosticSubmitResult)
def diagnostic_submit(body: DiagnosticSubmitIn):
    sb = get_supabase()
    q_ids = [a.question_id for a in body.answers]
    rows = sb.table("diagnostic_questions").select("*").in_("id", q_ids).execute().data
    by_id = {r["id"]: r for r in rows}

    per_question = []
    num_correct = 0
    concept_breakdown: dict[str, dict] = {}
    for ans in body.answers:
        q = by_id.get(ans.question_id)
        if not q:
            continue
        correct_index = LETTER_TO_INDEX[q["correct_option"]]
        is_correct = ans.selected_index == correct_index
        num_correct += int(is_correct)

        concept = q["concept"] or "General"
        bucket = concept_breakdown.setdefault(concept, {"correct": 0, "total": 0})
        bucket["total"] += 1
        bucket["correct"] += int(is_correct)

        per_question.append(
            {
                "question_id": q["id"],
                "correct": is_correct,
                "correct_index": correct_index,
                "concept": concept,
            }
        )

    total = len(per_question)
    if total == 0:
        raise HTTPException(400, "No matching questions to grade")

    return DiagnosticSubmitResult(
        num_correct=num_correct,
        total=total,
        per_question=per_question,
        concept_breakdown=concept_breakdown,
    )


@app.get("/health")
def health():
    return {"status": "ok"}
