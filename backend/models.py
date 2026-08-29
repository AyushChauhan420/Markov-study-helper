from typing import Optional
from pydantic import BaseModel, Field


class StudentCreate(BaseModel):
    name: str = Field(default="Guest", max_length=80)


class Student(BaseModel):
    id: str
    name: str


class Chapter(BaseModel):
    id: str
    name: str
    weight_pct: float
    mastery: float
    markov_state: str


class Question(BaseModel):
    id: str
    chapter_id: str
    question: str
    options: list[str]
    difficulty: str
    # correct_index is intentionally omitted from the response the
    # frontend gets *before* grading — the backend grades, not the client.


class AdaptiveQuestionsResponse(BaseModel):
    chapter_id: str
    mastery: float
    markov_state: str
    difficulty_mix: dict[str, int]
    questions: list[Question]


class AnswerIn(BaseModel):
    question_id: str
    selected_index: int  # 0..3


class SubmitIn(BaseModel):
    student_id: str
    chapter_id: str
    difficulty_filter: Optional[str] = "Mixed"
    answers: list[AnswerIn]


class SubmitResult(BaseModel):
    num_correct: int
    total: int
    mastery: float
    markov_state: str
    state_probs: list[float]
    per_question: list[dict]


class PlanChapter(BaseModel):
    id: str
    name: str
    weight_pct: float
    mastery: float
    problems: int
