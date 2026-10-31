"""Módulo 3: tutor virtual con IA (RAG).

Recupera los fragmentos más relevantes de los documentos del estudiante y
construye una respuesta con trazabilidad a las fuentes (documento y página).
"""
from __future__ import annotations

import math

from fastapi import APIRouter, Depends

from app.api import documents as docs_module
from app.core.config import Settings, get_settings
from app.core.security import CurrentUser, get_current_user
from app.models.schemas import TutorAnswer, TutorQuestion
from app.services.ai_service import get_ai_service

router = APIRouter(prefix="/tutor", tags=["tutor"])


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


@router.post("/ask", response_model=TutorAnswer)
async def ask_tutor(
    payload: TutorQuestion,
    user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    ai = get_ai_service(settings)
    query_embedding = await ai.embed(payload.question)

    # Reunir fragmentos del usuario (filtrando por asignatura si se indica)
    candidates: list[dict] = []
    for doc_id, chunks in docs_module._chunks.items():
        doc = docs_module._docs.get(doc_id)
        if not doc or doc["user_id"] != user.id:
            continue
        if payload.subject_id and doc["subject_id"] != payload.subject_id:
            continue
        candidates.extend(chunks)

    # Recuperar los 5 fragmentos más similares (retrieval del RAG)
    ranked = sorted(
        candidates,
        key=lambda c: _cosine(query_embedding, c["embedding"]),
        reverse=True,
    )
    top = ranked[:5]

    result = await ai.answer_with_context(payload.question, top)
    return result
