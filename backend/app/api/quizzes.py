"""Módulo 4: generador de evaluaciones y simulacros.

Genera preguntas a partir del material del estudiante, registra intentos y
calcula resultados con retroalimentación.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api import documents as docs_module
from app.core.config import Settings, get_settings
from app.core.security import CurrentUser, get_current_user
from app.models.schemas import (
    AttemptResult,
    AttemptSubmit,
    Quiz,
    QuizCreate,
)
from app.services.ai_service import get_ai_service

router = APIRouter(prefix="/quizzes", tags=["quizzes"])

_quizzes: dict[str, dict] = {}
_attempts: dict[str, dict] = {}


def _source_text(user_id: str, document_id: str | None, subject_id: str) -> str:
    """Reúne el texto base para generar las preguntas."""
    parts: list[str] = []
    for doc_id, chunks in docs_module._chunks.items():
        doc = docs_module._docs.get(doc_id)
        if not doc or doc["user_id"] != user_id:
            continue
        if document_id and doc_id != document_id:
            continue
        if not document_id and doc["subject_id"] != subject_id:
            continue
        parts.extend(c["content"] for c in chunks)
    return "\n".join(parts)


@router.post("", response_model=Quiz, status_code=201)
async def create_quiz(
    payload: QuizCreate,
    user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    ai = get_ai_service(settings)
    text = _source_text(user.id, payload.document_id, payload.subject_id)

    generated = await ai.generate_quiz(
        text=text or "Material de estudio general.",
        num_questions=payload.num_questions,
        difficulty=payload.difficulty,
    )

    quiz_id = str(uuid.uuid4())
    questions = []
    for q in generated:
        questions.append({**q, "id": str(uuid.uuid4())})

    quiz = {
        "id": quiz_id,
        "subject_id": payload.subject_id,
        "user_id": user.id,
        "title": payload.title,
        "config": {
            "num_questions": payload.num_questions,
            "difficulty": payload.difficulty,
            "document_id": payload.document_id,
        },
        "questions": questions,
    }
    _quizzes[quiz_id] = quiz
    return quiz


@router.get("/{quiz_id}", response_model=Quiz)
async def get_quiz(quiz_id: str, user: CurrentUser = Depends(get_current_user)):
    quiz = _quizzes.get(quiz_id)
    if not quiz or quiz["user_id"] != user.id:
        raise HTTPException(status_code=404, detail="Cuestionario no encontrado.")
    return quiz


@router.post("/attempts", response_model=AttemptResult, status_code=201)
async def submit_attempt(
    payload: AttemptSubmit, user: CurrentUser = Depends(get_current_user)
):
    quiz = _quizzes.get(payload.quiz_id)
    if not quiz or quiz["user_id"] != user.id:
        raise HTTPException(status_code=404, detail="Cuestionario no encontrado.")

    by_id = {q["id"]: q for q in quiz["questions"]}
    correct = 0
    for ans in payload.answers:
        q = by_id.get(ans.question_id)
        if q and q.get("correct_answer") is not None:
            if ans.given_answer.strip().lower() == str(q["correct_answer"]).strip().lower():
                correct += 1

    total = len(quiz["questions"]) or 1
    score = round(correct / total * 100, 2)

    attempt_id = str(uuid.uuid4())
    _attempts[attempt_id] = {
        "id": attempt_id,
        "quiz_id": payload.quiz_id,
        "user_id": user.id,
        "score": score,
    }

    return AttemptResult(
        attempt_id=attempt_id, score=score, correct=correct, total=len(quiz["questions"])
    )
