"""Módulo 3: tutor virtual con IA (RAG).

Recupera los fragmentos más relevantes de los documentos del estudiante
(vía el repositorio) y construye una respuesta con trazabilidad a las
fuentes (documento y página).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.core.security import CurrentUser, get_current_user
from app.models.schemas import TutorAnswer, TutorQuestion
from app.repositories.base import RepositoryBundle
from app.repositories.factory import get_repositories
from app.services.ai_service import get_ai_service

router = APIRouter(prefix="/tutor", tags=["tutor"])


@router.post("/ask", response_model=TutorAnswer)
async def ask_tutor(
    payload: TutorQuestion,
    user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ai = get_ai_service(settings)
    query_embedding = await ai.embed(payload.question)

    # Recuperación semántica de los 5 fragmentos más relevantes (RAG)
    top = await repos.chunks.search(
        user_id=user.id,
        query_embedding=query_embedding,
        match_count=5,
        subject_id=payload.subject_id,
    )

    return await ai.answer_with_context(payload.question, top)
