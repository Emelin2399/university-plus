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

from anyio import to_thread

from app.core.config import Settings
from app.repositories.base import (
    ChunkRepository,
    DocumentRepository,
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


def build_supabase_bundle(settings: Settings) -> RepositoryBundle:
    from app.services.supabase_client import get_supabase

    client = get_supabase(settings)
    return RepositoryBundle(
        subjects=SupabaseSubjectRepository(client, settings),
        documents=SupabaseDocumentRepository(client, settings),
        chunks=SupabaseChunkRepository(client, settings),
        quizzes=SupabaseQuizRepository(client, settings),
    )
