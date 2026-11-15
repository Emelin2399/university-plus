"""Lógica pura de calificación de intentos de cuestionario.

Se mantiene libre de dependencias (sin FastAPI ni Pydantic) para poder
reutilizarse y probarse de forma aislada. La capa de API envuelve estos
diccionarios en los esquemas de respuesta.
"""
from __future__ import annotations

from typing import Any


def score_attempt(
    quiz: dict[str, Any], given_by_id: dict[str, str]
) -> tuple[list[dict[str, Any]], int, int]:
    """Calcula la retroalimentación por pregunta de un intento.

    Compara la respuesta dada con la correcta (insensible a mayúsculas y
    espacios). Devuelve una terna con:

    - la lista de detalles (un dict por pregunta, en el orden del cuestionario
      para conservar el gradiente fácil→avanzado),
    - el total de aciertos auto-calificables,
    - el número de preguntas auto-calificables (denominador de la nota).

    Las preguntas de tipo "open" (respuesta abierta) NO se pueden calificar de
    forma fiable por comparación exacta, así que se EXCLUYEN de la nota: no
    cuentan en el denominador y su detalle se marca con ``is_correct = None`` y
    ``auto_graded = False``. Aun así se devuelven su respuesta correcta y su
    explicación para que el estudiante pueda autoevaluarse.

    Las preguntas sin respuesta (de tipos auto-calificables) se tratan como
    vacías e incorrectas.
    """
    details: list[dict[str, Any]] = []
    correct = 0
    gradable = 0
    for q in quiz.get("questions", []):
        given = given_by_id.get(q["id"], "")
        correct_answer = q.get("correct_answer")
        is_open = q.get("type") == "open"

        if is_open:
            # Respuesta abierta: no se auto-califica, se excluye de la nota.
            auto_graded = False
            is_correct: bool | None = None
        else:
            auto_graded = True
            gradable += 1
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
                "auto_graded": auto_graded,
                "explanation": q.get("explanation"),
                "options": q.get("options"),
            }
        )
    return details, correct, gradable
