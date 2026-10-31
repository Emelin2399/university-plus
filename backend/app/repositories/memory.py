"""Implementación en memoria de los repositorios (modo desarrollo).

No persiste entre reinicios. Útil para probar el flujo end-to-end sin
credenciales de Supabase.
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any

from app.repositories.base import (
    ActivityRepository,
    ChunkRepository,
    DocumentRepository,
    NoteRepository,
    ProgressRepository,
    QuizRepository,
    RepositoryBundle,
    SubjectRepository,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# Almacenes compartidos a nivel de módulo (singleton en memoria)
_subjects: dict[str, dict] = {}
_documents: dict[str, dict] = {}
_chunks: dict[str, list[dict]] = {}  # document_id -> chunks
_quizzes: dict[str, dict] = {}
_attempts: dict[str, dict] = {}
_activities: dict[str, dict] = {}
_notes: dict[str, dict] = {}


class MemorySubjectRepository(SubjectRepository):
    async def list(self, user_id: str) -> list[dict[str, Any]]:
        return [s for s in _subjects.values() if s["user_id"] == user_id]

    async def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        subject = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": data["name"],
            "term": data.get("term"),
            "color": data.get("color") or "#2563eb",
            "created_at": _now(),
        }
        _subjects[subject["id"]] = subject
        return subject

    async def delete(self, user_id: str, subject_id: str) -> bool:
        subject = _subjects.get(subject_id)
        if not subject or subject["user_id"] != user_id:
            return False
        del _subjects[subject_id]
        return True


class MemoryDocumentRepository(DocumentRepository):
    async def list(
        self, user_id: str, subject_id: str | None = None
    ) -> list[dict[str, Any]]:
        docs = [d for d in _documents.values() if d["user_id"] == user_id]
        if subject_id:
            docs = [d for d in docs if d["subject_id"] == subject_id]
        return docs

    async def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        doc = {
            "id": data.get("id") or str(uuid.uuid4()),
            "subject_id": data["subject_id"],
            "user_id": user_id,
            "name": data["name"],
            "source_type": data.get("source_type", "file"),
            "source_url": data.get("source_url"),
            "storage_path": data.get("storage_path", ""),
            "status": data.get("status", "processing"),
            "mime_type": data.get("mime_type"),
            "size_bytes": data.get("size_bytes"),
            "page_count": data.get("page_count"),
            "created_at": _now(),
        }
        _documents[doc["id"]] = doc
        return doc

    async def update_status(
        self, document_id: str, status: str, page_count: int | None = None
    ) -> None:
        doc = _documents.get(document_id)
        if doc:
            doc["status"] = status
            if page_count is not None:
                doc["page_count"] = page_count

    async def delete(self, user_id: str, document_id: str) -> bool:
        doc = _documents.get(document_id)
        if not doc or doc["user_id"] != user_id:
            return False
        _documents.pop(document_id, None)
        _chunks.pop(document_id, None)
        return True

    async def save_file(
        self, user_id: str, document_id: str, filename: str, data: bytes, mime: str
    ) -> str:
        # En memoria no guardamos el binario; devolvemos una ruta simbólica.
        return f"memory://{user_id}/{document_id}/{filename}"


class MemoryChunkRepository(ChunkRepository):
    async def bulk_insert(self, chunks: list[dict[str, Any]]) -> None:
        for chunk in chunks:
            _chunks.setdefault(chunk["document_id"], []).append(chunk)

    async def delete_by_document(self, document_id: str) -> None:
        _chunks.pop(document_id, None)

    async def search(
        self,
        user_id: str,
        query_embedding: list[float],
        match_count: int = 5,
        subject_id: str | None = None,
    ) -> list[dict[str, Any]]:
        candidates: list[dict] = []
        for doc_id, chunks in _chunks.items():
            doc = _documents.get(doc_id)
            if not doc or doc["user_id"] != user_id:
                continue
            if subject_id and doc["subject_id"] != subject_id:
                continue
            candidates.extend(chunks)
        ranked = sorted(
            candidates,
            key=lambda c: _cosine(query_embedding, c["embedding"]),
            reverse=True,
        )
        return ranked[:match_count]

    async def text_for_source(
        self, user_id: str, document_id: str | None, subject_id: str
    ) -> str:
        parts: list[str] = []
        for doc_id, chunks in _chunks.items():
            doc = _documents.get(doc_id)
            if not doc or doc["user_id"] != user_id:
                continue
            if document_id and doc_id != document_id:
                continue
            if not document_id and doc["subject_id"] != subject_id:
                continue
            parts.extend(c["content"] for c in chunks)
        return "\n".join(parts)


class MemoryQuizRepository(QuizRepository):
    async def create(self, user_id: str, quiz: dict[str, Any]) -> dict[str, Any]:
        quiz = {**quiz, "user_id": user_id}
        _quizzes[quiz["id"]] = quiz
        return quiz

    async def get(self, user_id: str, quiz_id: str) -> dict[str, Any] | None:
        quiz = _quizzes.get(quiz_id)
        if not quiz or quiz["user_id"] != user_id:
            return None
        return quiz

    async def create_attempt(
        self, user_id: str, attempt: dict[str, Any]
    ) -> dict[str, Any]:
        attempt = {**attempt, "user_id": user_id, "finished_at": _now()}
        _attempts[attempt["id"]] = attempt
        return attempt


class MemoryActivityRepository(ActivityRepository):
    async def list(
        self, user_id: str, subject_id: str | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        items = [a for a in _activities.values() if a["user_id"] == user_id]
        if subject_id:
            items = [a for a in items if a["subject_id"] == subject_id]
        if status:
            items = [a for a in items if a["status"] == status]
        # Orden por fecha límite (los sin fecha al final)
        return sorted(items, key=lambda a: (a.get("due_date") is None, a.get("due_date") or ""))

    async def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        activity = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "subject_id": data["subject_id"],
            "title": data["title"],
            "due_date": data.get("due_date"),
            "status": data.get("status", "pending"),
            "created_at": _now(),
            "updated_at": _now(),
        }
        _activities[activity["id"]] = activity
        return activity

    async def update(
        self, user_id: str, activity_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        activity = _activities.get(activity_id)
        if not activity or activity["user_id"] != user_id:
            return None
        for field in ("title", "due_date", "status", "subject_id"):
            if field in data and data[field] is not None:
                activity[field] = data[field]
        activity["updated_at"] = _now()
        return activity

    async def delete(self, user_id: str, activity_id: str) -> bool:
        activity = _activities.get(activity_id)
        if not activity or activity["user_id"] != user_id:
            return False
        del _activities[activity_id]
        return True


class MemoryNoteRepository(NoteRepository):
    async def list(
        self, user_id: str, subject_id: str | None = None, query: str | None = None
    ) -> list[dict[str, Any]]:
        items = [n for n in _notes.values() if n["user_id"] == user_id]
        if subject_id:
            items = [n for n in items if n["subject_id"] == subject_id]
        if query:
            q = query.lower()
            items = [
                n for n in items
                if q in n["title"].lower() or q in n["content"].lower()
            ]
        return sorted(items, key=lambda n: n["updated_at"], reverse=True)

    async def get(self, user_id: str, note_id: str) -> dict[str, Any] | None:
        note = _notes.get(note_id)
        if not note or note["user_id"] != user_id:
            return None
        return note

    async def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        note = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "subject_id": data.get("subject_id"),
            "title": data["title"],
            "content": data.get("content", ""),
            "topic": data.get("topic"),
            "is_favorite": data.get("is_favorite", False),
            "created_at": _now(),
            "updated_at": _now(),
        }
        _notes[note["id"]] = note
        return note

    async def update(
        self, user_id: str, note_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        note = _notes.get(note_id)
        if not note or note["user_id"] != user_id:
            return None
        for field in ("title", "content", "topic", "subject_id", "is_favorite"):
            if field in data and data[field] is not None:
                note[field] = data[field]
        note["updated_at"] = _now()
        return note

    async def delete(self, user_id: str, note_id: str) -> bool:
        note = _notes.get(note_id)
        if not note or note["user_id"] != user_id:
            return False
        del _notes[note_id]
        return True


class MemoryProgressRepository(ProgressRepository):
    async def attempts(
        self, user_id: str, subject_id: str | None = None
    ) -> list[dict[str, Any]]:
        items = [a for a in _attempts.values() if a["user_id"] == user_id]
        if subject_id:
            items = [a for a in items if a.get("subject_id") == subject_id]
        return items


def build_memory_bundle() -> RepositoryBundle:
    return RepositoryBundle(
        subjects=MemorySubjectRepository(),
        documents=MemoryDocumentRepository(),
        chunks=MemoryChunkRepository(),
        quizzes=MemoryQuizRepository(),
        activities=MemoryActivityRepository(),
        notes=MemoryNoteRepository(),
        progress=MemoryProgressRepository(),
    )
