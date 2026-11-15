"""Módulo 4: generador de evaluaciones y simulacros.

Genera preguntas a partir del material del estudiante, registra intentos y
calcula resultados con retroalimentación. Persiste vía repositorios.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import Settings, get_settings
from app.core.security import CurrentUser, get_current_user
from app.models.schemas import (
    AttemptAnswerDetail,
    AttemptResult,
    AttemptSubmit,
    Quiz,
    QuizCreate,
)
from app.repositories.base import RepositoryBundle
from app.repositories.factory import get_repositories
from app.services.ai_service import get_ai_service
from app.services.quiz_scoring import score_attempt

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@router.post("", response_model=Quiz, status_code=201)
async def create_quiz(
    payload: QuizCreate,
    user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ai = get_ai_service(settings)
    text = await repos.chunks.text_for_source(
        user.id, payload.document_id, payload.subject_id
    )

    generated = await ai.generate_quiz(
        text=text or "Material de estudio general.",
        num_questions=payload.num_questions,
        difficulty=payload.difficulty,
    )

    quiz_id = str(uuid.uuid4())
    questions = [{**q, "id": str(uuid.uuid4())} for q in generated]

    quiz = {
        "id": quiz_id,
        "subject_id": payload.subject_id,
        "title": payload.title,
        "config": {
            "num_questions": payload.num_questions,
            "difficulty": payload.difficulty,
            "document_id": payload.document_id,
        },
        "questions": questions,
    }
    return await repos.quizzes.create(user.id, quiz)


@router.get("/{quiz_id}", response_model=Quiz)
async def get_quiz(
    quiz_id: str,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    quiz = await repos.quizzes.get(user.id, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Cuestionario no encontrado.")
    return quiz


@router.post("/attempts", response_model=AttemptResult, status_code=201)
async def submit_attempt(
    payload: AttemptSubmit,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    quiz = await repos.quizzes.get(user.id, payload.quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Cuestionario no encontrado.")

    given_by_id = {a.question_id: a.given_answer for a in payload.answers}
    detail_dicts, correct, gradable = score_attempt(quiz, given_by_id)
    details = [AttemptAnswerDetail(**d) for d in detail_dicts]

    # La nota se calcula SOLO sobre preguntas auto-calificables
    # (multiple_choice/true_false); las abiertas se excluyen del denominador.
    # ``total`` refleja las preguntas puntuables para que ``correct/total`` y la
    # nota sean coherentes en la interfaz y en el seguimiento.
    denominator = gradable or 1
    score = round(correct / denominator * 100, 2)

    attempt_id = str(uuid.uuid4())
    await repos.quizzes.create_attempt(
        user.id,
        {
            "id": attempt_id,
            "quiz_id": payload.quiz_id,
            "subject_id": quiz.get("subject_id"),
            "quiz_title": quiz.get("title"),
            "score": score,
            "correct": correct,
            "total": gradable,
        },
    )

    return AttemptResult(
        attempt_id=attempt_id,
        score=score,
        correct=correct,
        total=gradable,
        details=details,
    )
