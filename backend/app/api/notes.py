"""Módulo 8: MIS NOTAS PLUS.

Espacio personal de apuntes: crear, editar, buscar y marcar favoritos.
Las notas son privadas por defecto (aislamiento por usuario).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import CurrentUser, get_current_user
from app.models.schemas import Note, NoteCreate, NoteUpdate
from app.repositories.base import RepositoryBundle
from app.repositories.factory import get_repositories

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=list[Note])
async def list_notes(
    subject_id: str | None = None,
    q: str | None = None,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    return await repos.notes.list(user.id, subject_id, q)


@router.get("/{note_id}", response_model=Note)
async def get_note(
    note_id: str,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    note = await repos.notes.get(user.id, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Nota no encontrada.")
    return note


@router.post("", response_model=Note, status_code=201)
async def create_note(
    payload: NoteCreate,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    return await repos.notes.create(user.id, payload.model_dump())


@router.patch("/{note_id}", response_model=Note)
async def update_note(
    note_id: str,
    payload: NoteUpdate,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    updated = await repos.notes.update(
        user.id, note_id, payload.model_dump(exclude_none=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Nota no encontrada.")
    return updated


@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: str,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ok = await repos.notes.delete(user.id, note_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Nota no encontrada.")
    return None
