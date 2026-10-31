"""Implementación de los repositorios sobre Supabase (Postgres + Storage).

Usa el cliente con service role key. Aunque las tablas tienen RLS, aquí
filtramos SIEMPRE por `user_id` como defensa en profundidad (la service key
omite RLS, por lo que el filtro explícito es obligatorio).

Las llamadas al SDK de Supabase son síncronas; se ejecutan en un threadpool
para no bloquear el event loop de FastAPI.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from typing import TYPE_CHECKING

from anyio import to_thread

if TYPE_CHECKING:
    from app.core.config import Settings

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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SupabaseSubjectRepository(SubjectRepository):
    def __init__(self, client, settings: Settings):
        self.client = client
        self.settings = settings

    async def list(self, user_id: str) -> list[dict[str, Any]]:
        def _q():
            return (
                self.client.table("subjects")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )

        res = await to_thread.run_sync(_q)
        return res.data or []

    async def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        row = {
            "user_id": user_id,
            "name": data["name"],
            "term": data.get("term"),
            "color": data.get("color") or "#2563eb",
        }

        def _q():
            return self.client.table("subjects").insert(row).execute()

        res = await to_thread.run_sync(_q)
        return (res.data or [row])[0]

    async def delete(self, user_id: str, subject_id: str) -> bool:
        def _q():
            return (
                self.client.table("subjects")
                .delete()
                .eq("id", subject_id)
                .eq("user_id", user_id)
                .execute()
            )

        res = await to_thread.run_sync(_q)
        return bool(res.data)


class SupabaseDocumentRepository(DocumentRepository):
    def __init__(self, client, settings: Settings):
        self.client = client
        self.settings = settings
        self.bucket = settings.supabase_storage_bucket

    async def list(
        self, user_id: str, subject_id: str | None = None
    ) -> list[dict[str, Any]]:
        def _q():
            query = (
                self.client.table("documents")
                .select("*")
                .eq("user_id", user_id)
            )
            if subject_id:
                query = query.eq("subject_id", subject_id)
            return query.order("created_at", desc=True).execute()

        res = await to_thread.run_sync(_q)
        return res.data or []

    async def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        row = {
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
        }

        def _q():
            return self.client.table("documents").insert(row).execute()

        res = await to_thread.run_sync(_q)
        return (res.data or [row])[0]

    async def update_status(
        self, document_id: str, status: str, page_count: int | None = None
    ) -> None:
        patch: dict[str, Any] = {"status": status, "updated_at": _now_iso()}
        if page_count is not None:
            patch["page_count"] = page_count

        def _q():
            return (
                self.client.table("documents")
                .update(patch)
                .eq("id", document_id)
                .execute()
            )

        await to_thread.run_sync(_q)

    async def delete(self, user_id: str, document_id: str) -> bool:
        def _q():
            return (
                self.client.table("documents")
                .delete()
                .eq("id", document_id)
                .eq("user_id", user_id)
                .execute()
            )

        res = await to_thread.run_sync(_q)
        return bool(res.data)

    async def save_file(
        self, user_id: str, document_id: str, filename: str, data: bytes, mime: str
    ) -> str:
        # Ruta con prefijo del usuario: habilita políticas de Storage por owner.
        path = f"{user_id}/{document_id}/{filename}"

        def _q():
            return self.client.storage.from_(self.bucket).upload(
                path, data, {"content-type": mime, "upsert": "true"}
            )

        await to_thread.run_sync(_q)
        return path


class SupabaseChunkRepository(ChunkRepository):
    def __init__(self, client, settings: Settings):
        self.client = client
        self.settings = settings

    async def bulk_insert(self, chunks: list[dict[str, Any]]) -> None:
        if not chunks:
            return
        rows = [
            {
                "document_id": c["document_id"],
                "user_id": c["user_id"],
                "content": c["content"],
                "page": c.get("page"),
                "chunk_index": c.get("chunk_index", 0),
                "embedding": c["embedding"],
            }
            for c in chunks
        ]

        def _q():
            return self.client.table("document_chunks").insert(rows).execute()

        await to_thread.run_sync(_q)

    async def delete_by_document(self, document_id: str) -> None:
        def _q():
            return (
                self.client.table("document_chunks")
                .delete()
                .eq("document_id", document_id)
                .execute()
            )

        await to_thread.run_sync(_q)

    async def search(
        self,
        user_id: str,
        query_embedding: list[float],
        match_count: int = 5,
        subject_id: str | None = None,
    ) -> list[dict[str, Any]]:
        # Usa la función RPC match_document_chunks definida en schema.sql
        params = {
            "query_embedding": query_embedding,
            "match_count": match_count,
            "p_user_id": user_id,
            "p_subject_id": subject_id,
        }

        def _q():
            return self.client.rpc("match_document_chunks", params).execute()

        res = await to_thread.run_sync(_q)
        return res.data or []

    async def text_for_source(
        self, user_id: str, document_id: str | None, subject_id: str
    ) -> str:
        def _q():
            query = (
                self.client.table("document_chunks")
                .select("content, document_id, documents!inner(subject_id)")
                .eq("user_id", user_id)
            )
            if document_id:
                query = query.eq("document_id", document_id)
            else:
                query = query.eq("documents.subject_id", subject_id)
            return query.execute()

        res = await to_thread.run_sync(_q)
        rows = res.data or []
        return "\n".join(r["content"] for r in rows)


class SupabaseQuizRepository(QuizRepository):
    def __init__(self, client, settings: Settings):
        self.client = client
        self.settings = settings

    async def create(self, user_id: str, quiz: dict[str, Any]) -> dict[str, Any]:
        quiz_row = {
            "id": quiz["id"],
            "subject_id": quiz["subject_id"],
            "user_id": user_id,
            "title": quiz["title"],
            "config": quiz.get("config", {}),
        }

        def _insert_quiz():
            return self.client.table("quizzes").insert(quiz_row).execute()

        await to_thread.run_sync(_insert_quiz)

        question_rows = [
            {
                "id": q["id"],
                "quiz_id": quiz["id"],
                "statement": q["statement"],
                "type": q["type"],
                "options": q.get("options"),
                "correct_answer": q.get("correct_answer"),
                "explanation": q.get("explanation"),
                "position": q.get("position", i),
            }
            for i, q in enumerate(quiz.get("questions", []))
        ]
        if question_rows:
            def _insert_questions():
                return self.client.table("questions").insert(question_rows).execute()

            await to_thread.run_sync(_insert_questions)

        return {**quiz, "user_id": user_id}

    async def get(self, user_id: str, quiz_id: str) -> dict[str, Any] | None:
        def _q():
            return (
                self.client.table("quizzes")
                .select("*, questions(*)")
                .eq("id", quiz_id)
                .eq("user_id", user_id)
                .single()
                .execute()
            )

        try:
            res = await to_thread.run_sync(_q)
        except Exception:
            return None
        return res.data

    async def create_attempt(
        self, user_id: str, attempt: dict[str, Any]
    ) -> dict[str, Any]:
        row = {
            "id": attempt["id"],
            "quiz_id": attempt["quiz_id"],
            "user_id": user_id,
            "score": attempt["score"],
            "finished_at": _now_iso(),
        }

        def _q():
            return self.client.table("quiz_attempts").insert(row).execute()

        await to_thread.run_sync(_q)
        return {**attempt, "user_id": user_id}


class SupabaseActivityRepository(ActivityRepository):
    def __init__(self, client, settings: Settings):
        self.client = client
        self.settings = settings

    async def list(
        self, user_id: str, subject_id: str | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        def _q():
            query = self.client.table("activities").select("*").eq("user_id", user_id)
            if subject_id:
                query = query.eq("subject_id", subject_id)
            if status:
                query = query.eq("status", status)
            return query.order("due_date", desc=False).execute()

        res = await to_thread.run_sync(_q)
        return res.data or []

    async def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        row = {
            "user_id": user_id,
            "subject_id": data["subject_id"],
            "title": data["title"],
            "due_date": data.get("due_date"),
            "status": data.get("status", "pending"),
        }

        def _q():
            return self.client.table("activities").insert(row).execute()

        res = await to_thread.run_sync(_q)
        return (res.data or [row])[0]

    async def update(
        self, user_id: str, activity_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        patch = {
            k: v
            for k, v in data.items()
            if k in ("title", "due_date", "status", "subject_id") and v is not None
        }
        patch["updated_at"] = _now_iso()

        def _q():
            return (
                self.client.table("activities")
                .update(patch)
                .eq("id", activity_id)
                .eq("user_id", user_id)
                .execute()
            )

        res = await to_thread.run_sync(_q)
        return (res.data or [None])[0]

    async def delete(self, user_id: str, activity_id: str) -> bool:
        def _q():
            return (
                self.client.table("activities")
                .delete()
                .eq("id", activity_id)
                .eq("user_id", user_id)
                .execute()
            )

        res = await to_thread.run_sync(_q)
        return bool(res.data)


class SupabaseNoteRepository(NoteRepository):
    def __init__(self, client, settings: Settings):
        self.client = client
        self.settings = settings

    async def list(
        self, user_id: str, subject_id: str | None = None, query: str | None = None
    ) -> list[dict[str, Any]]:
        def _q():
            q = self.client.table("notes").select("*").eq("user_id", user_id)
            if subject_id:
                q = q.eq("subject_id", subject_id)
            if query:
                # Búsqueda en título o contenido (ilike)
                q = q.or_(f"title.ilike.%{query}%,content.ilike.%{query}%")
            return q.order("updated_at", desc=True).execute()

        res = await to_thread.run_sync(_q)
        return res.data or []

    async def get(self, user_id: str, note_id: str) -> dict[str, Any] | None:
        def _q():
            return (
                self.client.table("notes")
                .select("*")
                .eq("id", note_id)
                .eq("user_id", user_id)
                .single()
                .execute()
            )

        try:
            res = await to_thread.run_sync(_q)
        except Exception:
            return None
        return res.data

    async def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        row = {
            "user_id": user_id,
            "subject_id": data.get("subject_id"),
            "title": data["title"],
            "content": data.get("content", ""),
            "topic": data.get("topic"),
            "is_favorite": data.get("is_favorite", False),
        }

        def _q():
            return self.client.table("notes").insert(row).execute()

        res = await to_thread.run_sync(_q)
        return (res.data or [row])[0]

    async def update(
        self, user_id: str, note_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        patch = {
            k: v
            for k, v in data.items()
            if k in ("title", "content", "topic", "subject_id", "is_favorite")
            and v is not None
        }
        patch["updated_at"] = _now_iso()

        def _q():
            return (
                self.client.table("notes")
                .update(patch)
                .eq("id", note_id)
                .eq("user_id", user_id)
                .execute()
            )

        res = await to_thread.run_sync(_q)
        return (res.data or [None])[0]

    async def delete(self, user_id: str, note_id: str) -> bool:
        def _q():
            return (
                self.client.table("notes")
                .delete()
                .eq("id", note_id)
                .eq("user_id", user_id)
                .execute()
            )

        res = await to_thread.run_sync(_q)
        return bool(res.data)


class SupabaseProgressRepository(ProgressRepository):
    def __init__(self, client, settings: Settings):
        self.client = client
        self.settings = settings

    async def attempts(
        self, user_id: str, subject_id: str | None = None
    ) -> list[dict[str, Any]]:
        # Une intentos con su cuestionario para obtener asignatura y título.
        def _q():
            query = (
                self.client.table("quiz_attempts")
                .select("id, quiz_id, score, finished_at, quizzes!inner(subject_id, title)")
                .eq("user_id", user_id)
            )
            if subject_id:
                query = query.eq("quizzes.subject_id", subject_id)
            return query.execute()

        res = await to_thread.run_sync(_q)
        rows = res.data or []
        # Aplanar la relación anidada a la forma que espera progress_analysis.
        flattened: list[dict[str, Any]] = []
        for r in rows:
            quiz = r.get("quizzes") or {}
            flattened.append(
                {
                    "quiz_id": r.get("quiz_id"),
                    "subject_id": quiz.get("subject_id"),
                    "quiz_title": quiz.get("title"),
                    "score": r.get("score"),
                    "finished_at": r.get("finished_at"),
                }
            )
        return flattened


def build_supabase_bundle(settings: Settings) -> RepositoryBundle:
    from app.services.supabase_client import get_supabase

    client = get_supabase(settings)
    return RepositoryBundle(
        subjects=SupabaseSubjectRepository(client, settings),
        documents=SupabaseDocumentRepository(client, settings),
        chunks=SupabaseChunkRepository(client, settings),
        quizzes=SupabaseQuizRepository(client, settings),
        activities=SupabaseActivityRepository(client, settings),
        notes=SupabaseNoteRepository(client, settings),
        progress=SupabaseProgressRepository(client, settings),
    )
