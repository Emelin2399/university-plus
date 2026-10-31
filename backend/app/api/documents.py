"""Módulo 2: biblioteca inteligente de documentos.

Flujo: subir -> validar -> extraer texto -> trocear -> generar embeddings ->
almacenar fragmentos para el RAG del tutor.
"""
from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.config import Settings, get_settings
from app.core.security import CurrentUser, get_current_user
from app.models.schemas import Document
from app.services.ai_service import get_ai_service

router = APIRouter(prefix="/documents", tags=["documents"])

# Almacén temporal en memoria (reemplazar por Supabase Storage + Postgres)
_docs: dict[str, dict] = {}
_chunks: dict[str, list[dict]] = {}  # document_id -> fragmentos

ALLOWED_MIME = {"application/pdf"}


def _extract_pdf_text(data: bytes) -> list[tuple[int, str]]:
    """Extrae texto por página. Devuelve [(page, text), ...]."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages, start=1):
        pages.append((i, page.extract_text() or ""))
    return pages


def _chunk_text(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    """Divide el texto en fragmentos con solape para conservar contexto."""
    text = " ".join(text.split())
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return [c for c in chunks if c.strip()]


@router.get("", response_model=list[Document])
async def list_documents(
    subject_id: str | None = None, user: CurrentUser = Depends(get_current_user)
):
    docs = [d for d in _docs.values() if d["user_id"] == user.id]
    if subject_id:
        docs = [d for d in docs if d["subject_id"] == subject_id]
    return docs


@router.post("", response_model=Document, status_code=201)
async def upload_document(
    subject_id: str = Form(...),
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    # Validación de tipo
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no permitido: {file.content_type}. Solo PDF por ahora.",
        )

    data = await file.read()

    # Validación de tamaño
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo supera el límite de {settings.max_upload_mb} MB.",
        )

    doc_id = str(uuid.uuid4())
    doc = {
        "id": doc_id,
        "subject_id": subject_id,
        "user_id": user.id,
        "name": file.filename,
        "status": "processing",
        "mime_type": file.content_type,
        "size_bytes": len(data),
        "page_count": None,
        "created_at": datetime.now(timezone.utc),
    }
    _docs[doc_id] = doc

    # Procesamiento: extracción + troceo + embeddings
    try:
        pages = _extract_pdf_text(data)
        doc["page_count"] = len(pages)
        ai = get_ai_service(settings)
        stored: list[dict] = []
        idx = 0
        for page_num, page_text in pages:
            for chunk in _chunk_text(page_text):
                embedding = await ai.embed(chunk)
                stored.append(
                    {
                        "id": str(uuid.uuid4()),
                        "document_id": doc_id,
                        "user_id": user.id,
                        "content": chunk,
                        "page": page_num,
                        "chunk_index": idx,
                        "embedding": embedding,
                    }
                )
                idx += 1
        _chunks[doc_id] = stored
        doc["status"] = "ready"
    except Exception as exc:  # pragma: no cover
        doc["status"] = "error"
        raise HTTPException(
            status_code=500, detail=f"No se pudo procesar el documento: {exc}"
        ) from exc

    return doc


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str, user: CurrentUser = Depends(get_current_user)
):
    doc = _docs.get(document_id)
    if not doc or doc["user_id"] != user.id:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    _docs.pop(document_id, None)
    _chunks.pop(document_id, None)
    return None
