"""Módulo 6: Seguimiento del aprendizaje.

Agrega los resultados de los intentos de cuestionarios para mostrar el avance
del estudiante, su evolución y los temas que conviene reforzar.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security import CurrentUser, get_current_user
from app.models.schemas import ProgressReport
from app.repositories.base import RepositoryBundle
from app.repositories.factory import get_repositories
from app.services.progress_analysis import build_report

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("", response_model=ProgressReport)
async def get_progress(
    subject_id: str | None = None,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    attempts = await repos.progress.attempts(user.id, subject_id)

    # Mapa id->nombre de asignatura para enriquecer el reporte.
    subjects = await repos.subjects.list(user.id)
    subject_names = {s["id"]: s["name"] for s in subjects}

    return build_report(attempts, subject_names)
