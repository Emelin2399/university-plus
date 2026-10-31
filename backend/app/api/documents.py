"""Módulo 2: biblioteca inteligente de documentos.

Flujo: subir -> validar -> guardar archivo -> extraer texto -> trocear ->
generar embeddings -> almacenar fragmentos para el RAG del tutor.

Persiste vía la capa de repositorios (memoria o Supabase).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.config import Settings, get_settings
from app.core.security import CurrentUser, get_current_user
from app.models.schemas import Document
from app.repositories.base import RepositoryBundle
from app.repositories.factory import get_repositories
from app.services.ai_service import get_ai_service
from app.services.document_processing import chunk_text, extract_pdf_text

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_MIME = {"application/pdf"}


@router.get("", response_model=list[Document])
async def list_documents(
    subject_id: str | None = None,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    return await repos.documents.list(user.id, subject_id)


@router.post("", response_model=Document, status_code=201)
async def upload_document(
    subject_id: str = Form(...),
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    repos: RepositoryBundle = Depends(get_repositories),
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

    # Guardar el archivo original (Storage o simbólico en memoria)
    storage_path = await repos.documents.save_file(
        user.id, doc_id, file.filename or "documento.pdf", data, file.content_type
    )

    # Crear el registro del documento en estado "processing"
    doc = await repos.documents.create(
        user.id,
        {
            "id": doc_id,
            "subject_id": subject_id,
            "name": file.filename,
            "storage_path": storage_path,
            "status": "processing",
            "mime_type": file.content_type,
            "size_bytes": len(data),
        },
    )

    # Procesamiento: extracción + troceo + embeddings
    try:
        pages = extract_pdf_text(data)
        ai = get_ai_service(settings)
        to_store: list[dict] = []
        idx = 0
        for page_num, page_text in pages:
            for chunk in chunk_text(page_text):
                embedding = await ai.embed(chunk)
                to_store.append(
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

        await repos.chunks.bulk_insert(to_store)
        await repos.documents.update_status(doc_id, "ready", page_count=len(pages))
        doc["status"] = "ready"
        doc["page_count"] = len(pages)
    except Exception as exc:  # pragma: no cover
        await repos.documents.update_status(doc_id, "error")
        raise HTTPException(
            status_code=500, detail=f"No se pudo procesar el documento: {exc}"
        ) from exc

    return doc


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ok = await repos.documents.delete(user.id, document_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    return None
