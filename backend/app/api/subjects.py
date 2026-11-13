"""Módulo 1/2: gestión de asignaturas del estudiante.

Usa la capa de repositorios: en memoria (dev) o Supabase (producción),
seleccionada automáticamente según la configuración.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import CurrentUser, get_current_user
from app.models.schemas import Subject, SubjectCreate
from app.repositories.base import RepositoryBundle
from app.repositories.factory import get_repositories

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=list[Subject])
async def list_subjects(
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    return await repos.subjects.list(user.id)


@router.post("", response_model=Subject, status_code=201)
async def create_subject(
    payload: SubjectCreate,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    return await repos.subjects.create(user.id, payload.model_dump())


@router.delete("/{subject_id}", status_code=204)
async def delete_subject(
    subject_id: str,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ok = await repos.subjects.delete(user.id, subject_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada.")
    return None
