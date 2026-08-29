from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from database import get_supabase
from engine import (
    calculate_markov_standing,
    pick_difficulty_mix,
    select_adaptive_questions,
    update_mastery,
)
from models import (
    AdaptiveQuestionsResponse,
    Chapter,
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
    row = sb.table("students").select("*").eq("id", student_id).single().execute()
    if not row.data:
        raise HTTPException(404, "Student not found")
    return Student(id=row.data["id"], name=row.data["name"])


# ---------------------------------------------------------------------
# Chapters (merged with this student's live mastery/Markov state)
# ---------------------------------------------------------------------
@app.get("/chapters", response_model=list[Chapter])
def list_chapters(student_id: str = Query(...)):
    sb = get_supabase()
    chapters = sb.table("chapters").select("*").order("id").execute().data
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
def plan(student_id: str = Query(...), budget: int = Query(60, ge=10, le=200)):
    chapters = list_chapters(student_id)
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


@app.get("/health")
def health():
    return {"status": "ok"}
