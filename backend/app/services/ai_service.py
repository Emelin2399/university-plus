"""Servicio de IA: embeddings, tutoría (RAG) y generación de cuestionarios.

Soporta dos proveedores:
- "mock": respuestas deterministas para desarrollo sin coste ni red.
- "openai": integra la API real (requiere OPENAI_API_KEY).

El objetivo es que el resto del backend no dependa del proveedor concreto.
"""
from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.core.config import Settings

EMBEDDING_DIM = 1536


class AIService:
    def __init__(self, settings: "Settings"):
        self.settings = settings
        self.provider = settings.ai_provider

    # ---------------------------------------------------------------
    # Embeddings
    # ---------------------------------------------------------------
    async def embed(self, text: str) -> list[float]:
        """Genera un embedding para un fragmento de texto."""
        if self.provider == "openai":
            return await self._openai_embed(text)
        return self._mock_embed(text)

    def _mock_embed(self, text: str) -> list[float]:
        """Embedding determinista derivado del hash del texto.

        No tiene significado semántico real, pero permite probar todo el
        flujo de almacenamiento/recuperación sin llamar a una API.
        """
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        i = 0
        while len(values) < EMBEDDING_DIM:
            byte = seed[i % len(seed)]
            values.append((byte / 255.0) * 2 - 1)
            i += 1
        return values

    async def _openai_embed(self, text: str) -> list[float]:
        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                json={"model": self.settings.openai_embedding_model, "input": text},
            )
            resp.raise_for_status()
            return resp.json()["data"][0]["embedding"]

    # ---------------------------------------------------------------
    # Tutor (RAG) — responde usando los fragmentos recuperados
    # ---------------------------------------------------------------
    async def answer_with_context(
        self, question: str, chunks: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Construye una respuesta del tutor a partir de los fragmentos.

        Devuelve el texto y las fuentes (trazabilidad) usadas.
        """
        sources = [
            {"document_id": c.get("document_id"), "page": c.get("page")}
            for c in chunks
        ]

        if not chunks:
            return {
                "answer": (
                    "No encontré información suficiente en tus documentos para "
                    "responder con seguridad. Prueba a cargar material relacionado "
                    "o reformula la pregunta."
                ),
                "sources": [],
            }

        if self.provider == "openai":
            answer = await self._openai_chat(question, chunks)
        else:
            context = "\n\n".join(c.get("content", "") for c in chunks[:3])
            answer = (
                f"(Respuesta de ejemplo en modo mock)\n\n"
                f"Según tus documentos, esto es lo relevante para «{question}»:\n\n"
                f"{context[:600]}\n\n"
                f"Recuerda que esta respuesta es un apoyo: revisa siempre la fuente original."
            )

        return {"answer": answer, "sources": sources}

    async def _openai_chat(self, question: str, chunks: list[dict[str, Any]]) -> str:
        import httpx

        context = "\n\n".join(
            f"[p.{c.get('page')}] {c.get('content', '')}" for c in chunks
        )
        system = (
            "Eres un tutor académico de UNIVERSITY PLUS. Responde SOLO con base "
            "en el contexto proporcionado. Si el contexto no es suficiente, dilo "
            "claramente. Cita las páginas. No inventes información."
        )
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                json={
                    "model": self.settings.openai_chat_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {
                            "role": "user",
                            "content": f"Contexto:\n{context}\n\nPregunta: {question}",
                        },
                    ],
                    "temperature": 0.2,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    # ---------------------------------------------------------------
    # Generación de cuestionarios
    # ---------------------------------------------------------------
    async def generate_quiz(
        self, text: str, num_questions: int = 5, difficulty: str = "medium"
    ) -> list[dict[str, Any]]:
        """Genera preguntas a partir de un texto. Mock devuelve ejemplos."""
        if self.provider == "openai":
            return await self._openai_quiz(text, num_questions, difficulty)

        questions: list[dict[str, Any]] = []
        for i in range(num_questions):
            questions.append(
                {
                    "statement": f"(Mock) Pregunta {i + 1} sobre el material (dificultad: {difficulty})",
                    "type": "multiple_choice",
                    "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
                    "correct_answer": "Opción A",
                    "explanation": "Explicación de ejemplo generada en modo mock.",
                    "position": i,
                }
            )
        return questions

    async def _openai_quiz(
        self, text: str, num_questions: int, difficulty: str
    ) -> list[dict[str, Any]]:
        import json

        import httpx

        system = (
            "Genera cuestionarios de estudio en JSON. Devuelve un array de objetos "
            "con las claves: statement, type (multiple_choice|true_false|open), "
            "options (array o null), correct_answer, explanation."
        )
        prompt = (
            f"Crea {num_questions} preguntas de dificultad {difficulty} basadas en "
            f"este material:\n\n{text[:4000]}"
        )
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                json={
                    "model": self.settings.openai_chat_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.4,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            items = data if isinstance(data, list) else data.get("questions", [])
            for i, q in enumerate(items):
                q["position"] = i
            return items


def get_ai_service(settings: Settings) -> AIService:
    return AIService(settings)
