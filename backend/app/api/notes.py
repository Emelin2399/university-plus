"""Módulo 8: MIS NOTAS PLUS.

Espacio personal de apuntes: crear, editar, buscar y marcar favoritos.
Las notas son privadas por defecto (aislamiento por usuario).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.config import Settings, get_settings
from app.core.security import CurrentUser, get_current_user
from app.models.schemas import Attachment, Note, NoteCreate, NoteUpdate
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


# ------------------------- Adjuntos de la nota -------------------------
# Se permite adjuntar CUALQUIER tipo de archivo y VARIOS por nota.
@router.get("/{note_id}/attachments", response_model=list[Attachment])
async def list_note_attachments(
    note_id: str,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    attachments = await repos.notes.list_attachments(user.id, note_id)
    if attachments is None:
        raise HTTPException(status_code=404, detail="Nota no encontrada.")
    return attachments


@router.post(
    "/{note_id}/attachments", response_model=list[Attachment], status_code=201
)
async def upload_note_attachments(
    note_id: str,
    files: list[UploadFile] = File(...),
    user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Sube uno o varios archivos adjuntos a una nota propia.

    No se restringe el tipo de archivo; solo se valida el tamaño máximo.
    """
    max_bytes = settings.max_upload_mb * 1024 * 1024
    created: list[dict] = []
    for file in files:
        data = await file.read()
        if len(data) > max_bytes:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"El archivo «{file.filename}» supera el límite de "
                    f"{settings.max_upload_mb} MB."
                ),
            )
        attachment = await repos.notes.add_attachment(
            user.id,
            note_id,
            file.filename or "archivo",
            data,
            file.content_type or "application/octet-stream",
        )
        if attachment is None:
            raise HTTPException(status_code=404, detail="Nota no encontrada.")
        created.append(attachment)
    return created


@router.delete("/{note_id}/attachments/{attachment_id}", status_code=204)
async def delete_note_attachment(
    note_id: str,
    attachment_id: str,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ok = await repos.notes.delete_attachment(user.id, note_id, attachment_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado.")
    return None
