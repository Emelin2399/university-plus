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
            # Gradiente de dificultad: fácil al principio, avanzado al final.
            label = _difficulty_label(i, num_questions)
            questions.append(
                {
                    "statement": (
                        f"(Mock) Pregunta {i + 1} sobre el material "
                        f"(dificultad: {label})"
                    ),
                    "type": "multiple_choice",
                    "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
                    "correct_answer": "Opción A",
                    "explanation": "Explicación de ejemplo generada en modo mock.",
                    "difficulty": label,
                }
            )
        return _sanitize_quiz_items(questions)

    async def _openai_quiz(
        self, text: str, num_questions: int, difficulty: str
    ) -> list[dict[str, Any]]:
        import json

        import httpx

        system = (
            "Eres un generador de cuestionarios de estudio para UNIVERSITY PLUS. "
            "Devuelve SIEMPRE un objeto JSON con la clave \"questions\", que es un "
            "array de objetos. Cada objeto tiene las claves: statement, type "
            "(multiple_choice|true_false|open), options (array de strings o null), "
            "correct_answer, explanation, difficulty (facil|medio|avanzado).\n\n"
            "REGLAS OBLIGATORIAS:\n"
            "1. En las preguntas multiple_choice incluye EXACTAMENTE 4 opciones "
            "DISTINTAS entre sí: una correcta y tres incorrectas pero plausibles. "
            "Nunca repitas una opción ni pongas la misma respuesta cuatro veces. "
            "correct_answer debe ser idéntica (mismo texto) a una de las options.\n"
            "2. Ordena las preguntas de la MÁS FÁCIL a la MÁS AVANZADA, formando un "
            "gradiente de dificultad. La primera debe ser la más sencilla y la "
            "última la más difícil. Etiqueta cada pregunta con su difficulty.\n"
            "3. Para preguntas verdadero/falso las opciones son EXACTAMENTE "
            "Verdadero/Falso y la respuesta correcta DEBE ser Verdadero o Falso; "
            "nunca mezcles tipos (si la respuesta no es Verdadero/Falso, usa "
            "multiple_choice con 4 opciones distintas). En open deja options en "
            "null.\n"
            "4. La respuesta correcta SIEMPRE debe estar entre las opciones y, en "
            "opción múltiple, debe haber 4 opciones distintas.\n"
            "5. Redacta todo en español, con explicaciones claras y breves."
        )
        prompt = (
            f"Crea {num_questions} preguntas (dificultad general: {difficulty}) "
            f"basadas en este material. Devuélvelas YA ORDENADAS de más fácil a más "
            f"avanzada y con opciones distintas:\n\n{text[:4000]}"
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
            return _sanitize_quiz_items(items)


def _difficulty_label(index: int, total: int) -> str:
    """Asigna una etiqueta de dificultad según la posición en el gradiente.

    Reparte las preguntas en tres tramos: fácil, medio y avanzado, de modo que
    el orden refleje una progresión de fácil a avanzado.
    """
    if total <= 1:
        return "facil"
    ratio = index / (total - 1)
    if ratio < 1 / 3:
        return "facil"
    if ratio < 2 / 3:
        return "medio"
    return "avanzado"


# Par verdadero/falso canónico que usa la interfaz.
_TRUE_FALSE_OPTIONS = ["Verdadero", "Falso"]
# Valores que, normalizados, se consideran verdadero/falso válidos.
_TRUE_VALUES = {"verdadero", "true", "v"}
_FALSE_VALUES = {"falso", "false", "f"}


def _norm(value: Any) -> str:
    """Normaliza un texto para comparaciones insensibles a mayúsculas/espacios."""
    return str(value).strip().lower()


def _normalize_true_false(correct: Any) -> str | None:
    """Devuelve "Verdadero"/"Falso" si el valor es un verdadero/falso reconocible.

    Si no corresponde a ninguno de los dos, devuelve None (la pregunta estaba
    mal tipada como true_false).
    """
    if correct is None:
        return None
    key = _norm(correct)
    if key in _TRUE_VALUES:
        return "Verdadero"
    if key in _FALSE_VALUES:
        return "Falso"
    return None


def _dedup_options(options: list[Any], correct: Any) -> tuple[list[str], str | None]:
    """Deduplica opciones (insensible a mayúsculas/espacios) y asegura la correcta.

    Devuelve la lista de opciones limpias y la respuesta correcta tal como quedó
    representada entre las opciones (para que coincida exactamente).
    """
    seen: set[str] = set()
    deduped: list[str] = []
    for opt in options:
        key = _norm(opt)
        if key and key not in seen:
            seen.add(key)
            deduped.append(str(opt))
    correct_text: str | None = None
    if correct is not None:
        correct_key = _norm(correct)
        if correct_key:
            if correct_key not in seen:
                # La respuesta correcta faltaba: insertarla entre las opciones.
                deduped.append(str(correct))
                seen.add(correct_key)
                correct_text = str(correct)
            else:
                # Recuperar el texto exacto de la opción que coincide.
                for opt in deduped:
                    if _norm(opt) == correct_key:
                        correct_text = opt
                        break
    return deduped, correct_text


def _sanitize_quiz_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Valida y normaliza las preguntas generadas antes de persistirlas.

    Salvaguardas (robustez ante respuestas imperfectas del modelo). El objetivo
    es que nunca llegue a la interfaz una pregunta cuyo correct_answer no pueda
    ser elegido por el estudiante (tipo/opciones/respuesta incoherentes):

    - true_false: las opciones se fijan a ["Verdadero", "Falso"] y la respuesta
      se normaliza a exactamente "Verdadero" o "Falso". Si la respuesta NO es un
      verdadero/falso reconocible (p. ej. "he is not"), la pregunta estaba mal
      tipada: se CONVIERTE a multiple_choice si tiene >=2 opciones distintas
      útiles (incluida la correcta); si no las tiene, se DESCARTA.
    - multiple_choice: deduplica opciones (insensible a mayúsculas/espacios),
      inserta la respuesta correcta si falta y DESCARTA la pregunta si quedan
      menos de 2 opciones distintas.
    - open: se deja tal cual (no necesita opciones).
    - Tras limpiar, reindexa position (0-based) sobre las preguntas que
      sobreviven, preservando el orden fácil→avanzado.

    Nunca lanza excepción por una pregunta inválida: la descarta y continúa.
    """
    clean: list[dict[str, Any]] = []
    for q in items:
        if not isinstance(q, dict):
            continue
        qtype = q.get("type")
        correct = q.get("correct_answer")

        if qtype == "true_false":
            normalized = _normalize_true_false(correct)
            if normalized is not None:
                # Verdadero/falso coherente: fijar opciones canónicas.
                q["options"] = list(_TRUE_FALSE_OPTIONS)
                q["correct_answer"] = normalized
                clean.append(q)
                continue
            # Mal tipada como true_false: intentar convertir a multiple_choice.
            options = q.get("options")
            if not isinstance(options, list):
                options = []
            deduped, correct_text = _dedup_options(options, correct)
            if len(deduped) >= 2 and correct_text is not None:
                q["type"] = "multiple_choice"
                q["options"] = deduped
                q["correct_answer"] = correct_text
                clean.append(q)
            # Sin opciones adecuadas: se descarta (mejor menos y correctas).
            continue

        if qtype == "multiple_choice":
            options = q.get("options")
            if not isinstance(options, list):
                options = []
            deduped, correct_text = _dedup_options(options, correct)
            if len(deduped) < 2 or correct_text is None:
                # No hay forma de que el estudiante elija la correcta: descartar.
                continue
            q["options"] = deduped
            q["correct_answer"] = correct_text
            clean.append(q)
            continue

        # open u otros tipos: se dejan como están (no requieren opciones).
        clean.append(q)

    # Reindexar position sobre las preguntas que sobrevivieron.
    for i, q in enumerate(clean):
        q["position"] = i
    return clean


def get_ai_service(settings: Settings) -> AIService:
    return AIService(settings)
