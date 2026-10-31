"""Interfaces (contratos) de los repositorios.

Los routers dependen de estas abstracciones, no de una implementación
concreta. Así podemos cambiar de almacenamiento en memoria a Supabase sin
tocar la lógica de la API.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SubjectRepository(ABC):
    @abstractmethod
    async def list(self, user_id: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    async def delete(self, user_id: str, subject_id: str) -> bool: ...


class DocumentRepository(ABC):
    @abstractmethod
    async def list(
        self, user_id: str, subject_id: str | None = None
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    async def update_status(
        self, document_id: str, status: str, page_count: int | None = None
    ) -> None: ...

    @abstractmethod
    async def delete(self, user_id: str, document_id: str) -> bool: ...

    @abstractmethod
    async def save_file(
        self, user_id: str, document_id: str, filename: str, data: bytes, mime: str
    ) -> str:
        """Guarda el archivo original y devuelve su ruta de almacenamiento."""
        ...


class ChunkRepository(ABC):
    @abstractmethod
    async def bulk_insert(self, chunks: list[dict[str, Any]]) -> None: ...

    @abstractmethod
    async def delete_by_document(self, document_id: str) -> None: ...

    @abstractmethod
    async def search(
        self,
        user_id: str,
        query_embedding: list[float],
        match_count: int = 5,
        subject_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Recuperación semántica (retrieval del RAG)."""
        ...

    @abstractmethod
    async def text_for_source(
        self, user_id: str, document_id: str | None, subject_id: str
    ) -> str:
        """Concatena el texto base para generar cuestionarios."""
        ...


class QuizRepository(ABC):
    @abstractmethod
    async def create(self, user_id: str, quiz: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    async def get(self, user_id: str, quiz_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def create_attempt(
        self, user_id: str, attempt: dict[str, Any]
    ) -> dict[str, Any]: ...


class RepositoryBundle:
    """Agrupa todos los repositorios de una implementación concreta."""

    def __init__(
        self,
        subjects: SubjectRepository,
        documents: DocumentRepository,
        chunks: ChunkRepository,
        quizzes: QuizRepository,
    ):
        self.subjects = subjects
        self.documents = documents
        self.chunks = chunks
        self.quizzes = quizzes
