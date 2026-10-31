"""Esquemas Pydantic de entrada/salida de la API."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


# --------------------------- Subjects ---------------------------
class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    term: str | None = None
    color: str | None = "#2563eb"


class Subject(BaseModel):
    id: str
    user_id: str
    name: str
    term: str | None = None
    color: str | None = None
    created_at: datetime | None = None


# --------------------------- Documents --------------------------
class Document(BaseModel):
    id: str
    subject_id: str
    name: str
    status: str
    source_type: str = "file"  # "file" | "link"
    source_url: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    page_count: int | None = None
    created_at: datetime | None = None


class DocumentFromUrl(BaseModel):
    subject_id: str
    url: HttpUrl
    name: str | None = None


# --------------------------- Tutor ------------------------------
class TutorQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    subject_id: str | None = None


class TutorSource(BaseModel):
    document_id: str | None = None
    page: int | None = None


class TutorAnswer(BaseModel):
    answer: str
    sources: list[TutorSource] = []


# --------------------------- Quizzes ----------------------------
class QuizCreate(BaseModel):
    subject_id: str
    title: str = Field(min_length=1, max_length=200)
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    document_id: str | None = None


class Question(BaseModel):
    id: str | None = None
    statement: str
    type: str
    options: list[str] | None = None
    correct_answer: str | None = None
    explanation: str | None = None
    position: int = 0


class Quiz(BaseModel):
    id: str
    subject_id: str
    title: str
    config: dict[str, Any] = {}
    questions: list[Question] = []


class AttemptAnswerIn(BaseModel):
    question_id: str
    given_answer: str


class AttemptSubmit(BaseModel):
    quiz_id: str
    answers: list[AttemptAnswerIn]


class AttemptResult(BaseModel):
    attempt_id: str
    score: float
    correct: int
    total: int


# --------------------------- Activities (Planificador) ---------
class ActivityCreate(BaseModel):
    subject_id: str
    title: str = Field(min_length=1, max_length=300)
    due_date: datetime | None = None
    status: Literal["pending", "in_progress", "done"] = "pending"


class ActivityUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    due_date: datetime | None = None
    status: Literal["pending", "in_progress", "done"] | None = None
    subject_id: str | None = None


class Activity(BaseModel):
    id: str
    subject_id: str
    title: str
    due_date: datetime | None = None
    status: str
    created_at: datetime | None = None


# --------------------------- Notes (MIS NOTAS PLUS) -------------
class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    content: str = ""
    subject_id: str | None = None
    topic: str | None = None
    is_favorite: bool = False


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    content: str | None = None
    subject_id: str | None = None
    topic: str | None = None
    is_favorite: bool | None = None


class Note(BaseModel):
    id: str
    subject_id: str | None = None
    title: str
    content: str = ""
    topic: str | None = None
    is_favorite: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


# --------------------------- Progress (Seguimiento) ------------
class ProgressSummary(BaseModel):
    total_attempts: int
    average_score: float
    best_score: float


class SubjectProgress(BaseModel):
    subject_id: str | None = None
    subject_name: str
    attempts: int
    average_score: float


class EvolutionPoint(BaseModel):
    quiz_title: str
    score: float
    finished_at: str


class ReinforceItem(BaseModel):
    quiz_id: str | None = None
    quiz_title: str
    subject_id: str | None = None
    score: float


class ProgressReport(BaseModel):
    summary: ProgressSummary
    by_subject: list[SubjectProgress]
    evolution: list[EvolutionPoint]
    to_reinforce: list[ReinforceItem]


# --------------------------- EXPLORA PLUS ----------------------
class ExploreQuery(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    limit: int = Field(default=8, ge=1, le=20)


class AcademicResource(BaseModel):
    title: str
    authors: list[str] = []
    year: int | None = None
    venue: str | None = None
    doi: str | None = None
    url: str | None = None
    source: str = "mock"
    resource_type: str = "article"
    open_access: bool | None = None
    is_example: bool = False
    status: str = "pending"  # pending | reviewing | understood


class LearningStep(BaseModel):
    position: int
    step: str
    label: str
    resources: list[AcademicResource] = []


class ExploreResult(BaseModel):
    id: str
    query: str
    resources: list[AcademicResource]
    path: list[LearningStep]


class ExploreSearchSummary(BaseModel):
    id: str
    query: str
    created_at: datetime | None = None


class ResourceStatusUpdate(BaseModel):
    resource_index: int = Field(ge=0)
    status: Literal["pending", "reviewing", "understood"]
