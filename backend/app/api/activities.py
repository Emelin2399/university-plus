"""Módulo 5: Planificador académico.

Gestión de actividades (tareas, trabajos, exámenes) con fechas límite y
estado. El frontend las muestra en lista y calendario.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import CurrentUser, get_current_user
from app.models.schemas import Activity, ActivityCreate, ActivityUpdate
from app.repositories.base import RepositoryBundle
from app.repositories.factory import get_repositories

router = APIRouter(prefix="/activities", tags=["activities"])


def _serialize(activity: dict) -> dict:
    """Normaliza due_date a string ISO para el serializador de salida."""
    due = activity.get("due_date")
    if due is not None and not isinstance(due, str):
        activity = {**activity, "due_date": due.isoformat()}
    return activity


@router.get("", response_model=list[Activity])
async def list_activities(
    subject_id: str | None = None,
    status: str | None = None,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    items = await repos.activities.list(user.id, subject_id, status)
    return [_serialize(a) for a in items]


@router.post("", response_model=Activity, status_code=201)
async def create_activity(
    payload: ActivityCreate,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    data = payload.model_dump()
    if data.get("due_date") is not None:
        data["due_date"] = data["due_date"].isoformat()
    created = await repos.activities.create(user.id, data)
    return _serialize(created)


@router.patch("/{activity_id}", response_model=Activity)
async def update_activity(
    activity_id: str,
    payload: ActivityUpdate,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    data = payload.model_dump(exclude_none=True)
    if data.get("due_date") is not None:
        data["due_date"] = data["due_date"].isoformat()
    updated = await repos.activities.update(user.id, activity_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Actividad no encontrada.")
    return _serialize(updated)


@router.delete("/{activity_id}", status_code=204)
async def delete_activity(
    activity_id: str,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ok = await repos.activities.delete(user.id, activity_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Actividad no encontrada.")
    return None
