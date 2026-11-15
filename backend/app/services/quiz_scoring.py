"""Lógica pura de calificación de intentos de cuestionario.

Se mantiene libre de dependencias (sin FastAPI ni Pydantic) para poder
reutilizarse y probarse de forma aislada. La capa de API envuelve estos
diccionarios en los esquemas de respuesta.
"""
from __future__ import annotations

from typing import Any


def score_attempt(
    quiz: dict[str, Any], given_by_id: dict[str, str]
) -> tuple[list[dict[str, Any]], int]:
    """Calcula la retroalimentación por pregunta de un intento.

    Compara la respuesta dada con la correcta (insensible a mayúsculas y
    espacios). Devuelve una lista de detalles (un dict por pregunta, en el
    orden del cuestionario para conservar el gradiente fácil→avanzado) y el
    total de aciertos. Las preguntas sin respuesta se tratan como vacías e
    incorrectas.
    """
    details: list[dict[str, Any]] = []
    correct = 0
    for q in quiz.get("questions", []):
        given = given_by_id.get(q["id"], "")
        correct_answer = q.get("correct_answer")
        is_correct = (
            correct_answer is not None
            and given.strip().lower() == str(correct_answer).strip().lower()
        )
        if is_correct:
            correct += 1
        details.append(
            {
                "question_id": q["id"],
                "statement": q.get("statement", ""),
                "given_answer": given,
                "correct_answer": (
                    str(correct_answer) if correct_answer is not None else None
                ),
                "is_correct": is_correct,
                "explanation": q.get("explanation"),
                "options": q.get("options"),
            }
        )
    return details, correct
