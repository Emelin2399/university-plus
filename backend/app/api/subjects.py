"""Módulo 1/2: gestión de asignaturas del estudiante.

Nota: en este esqueleto se usa un repositorio en memoria cuando Supabase no
está configurado, para poder ejecutar y probar el flujo end-to-end. Al
configurar Supabase, sustituir `_store` por llamadas al cliente real.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import CurrentUser, get_current_user
from app.models.schemas import Subject, SubjectCreate

router = APIRouter(prefix="/subjects", tags=["subjects"])

# Almacén temporal en memoria (reemplazar por Supabase en producción)
_store: dict[str, dict] = {}


@router.get("", response_model=list[Subject])
async def list_subjects(user: CurrentUser = Depends(get_current_user)):
    return [s for s in _store.values() if s["user_id"] == user.id]


@router.post("", response_model=Subject, status_code=201)
async def create_subject(
    payload: SubjectCreate, user: CurrentUser = Depends(get_current_user)
):
    subject = {
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "name": payload.name,
        "term": payload.term,
        "color": payload.color,
        "created_at": datetime.now(timezone.utc),
    }
    _store[subject["id"]] = subject
    return subject


@router.delete("/{subject_id}", status_code=204)
async def delete_subject(
    subject_id: str, user: CurrentUser = Depends(get_current_user)
):
    subject = _store.get(subject_id)
    if not subject or subject["user_id"] != user.id:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada.")
    del _store[subject_id]
    return None
