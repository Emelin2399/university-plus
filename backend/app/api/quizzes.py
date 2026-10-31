"""Módulo 4: generador de evaluaciones y simulacros.

Genera preguntas a partir del material del estudiante, registra intentos y
calcula resultados con retroalimentación. Persiste vía repositorios.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import Settings, get_settings
from app.core.security import CurrentUser, get_current_user
from app.models.schemas import AttemptResult, AttemptSubmit, Quiz, QuizCreate
from app.repositories.base import RepositoryBundle
from app.repositories.factory import get_repositories
from app.services.ai_service import get_ai_service

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

    by_id = {q["id"]: q for q in quiz.get("questions", [])}
    correct = 0
    for ans in payload.answers:
        q = by_id.get(ans.question_id)
        if q and q.get("correct_answer") is not None:
            if (
                ans.given_answer.strip().lower()
                == str(q["correct_answer"]).strip().lower()
            ):
                correct += 1

    total_questions = len(quiz.get("questions", []))
    total = total_questions or 1
    score = round(correct / total * 100, 2)

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
            "total": total_questions,
        },
    )

    return AttemptResult(
        attempt_id=attempt_id,
        score=score,
        correct=correct,
        total=total_questions,
    )
