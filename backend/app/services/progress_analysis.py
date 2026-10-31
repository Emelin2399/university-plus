"""Lógica pura de análisis del progreso de aprendizaje.

Recibe una lista de intentos (attempts) y produce los indicadores del módulo
de Seguimiento del aprendizaje: resumen, progreso por asignatura, evolución y
temas por reforzar. Al ser puro, es reutilizable y fácil de probar.

Cada intento esperado tiene la forma:
    {
        "quiz_id": str,
        "subject_id": str | None,
        "quiz_title": str | None,
        "score": float,          # 0-100
        "finished_at": datetime | str | None,
    }
"""
from __future__ import annotations

from typing import Any

# Umbral por debajo del cual un tema se considera "por reforzar".
REINFORCE_THRESHOLD = 60.0


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def _ts(value: Any) -> str:
    """Normaliza un timestamp a string ISO para ordenar/serializar."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return value.isoformat()


def overall_summary(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    """Resumen global: total de intentos y promedio de puntaje."""
    scores = [float(a["score"]) for a in attempts if a.get("score") is not None]
    return {
        "total_attempts": len(attempts),
        "average_score": _avg(scores),
        "best_score": max(scores) if scores else 0.0,
    }


def progress_by_subject(
    attempts: list[dict[str, Any]],
    subject_names: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Promedio y conteo de intentos agrupados por asignatura."""
    names = subject_names or {}
    groups: dict[str, list[float]] = {}
    for a in attempts:
        sid = a.get("subject_id") or "sin_asignatura"
        if a.get("score") is not None:
            groups.setdefault(sid, []).append(float(a["score"]))

    result = []
    for sid, scores in groups.items():
        result.append(
            {
                "subject_id": None if sid == "sin_asignatura" else sid,
                "subject_name": names.get(sid, "Sin asignatura"),
                "attempts": len(scores),
                "average_score": _avg(scores),
            }
        )
    # Orden: menor promedio primero (lo que más necesita atención).
    return sorted(result, key=lambda r: r["average_score"])


def quiz_evolution(attempts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Serie temporal de los intentos (para graficar la evolución)."""
    ordered = sorted(attempts, key=lambda a: _ts(a.get("finished_at")))
    return [
        {
            "quiz_title": a.get("quiz_title") or "Cuestionario",
            "score": float(a["score"]),
            "finished_at": _ts(a.get("finished_at")),
        }
        for a in ordered
        if a.get("score") is not None
    ]


def topics_to_reinforce(
    attempts: list[dict[str, Any]],
    threshold: float = REINFORCE_THRESHOLD,
) -> list[dict[str, Any]]:
    """Cuestionarios cuyo mejor puntaje sigue por debajo del umbral.

    Usamos el mejor intento por cuestionario: si incluso el mejor es bajo,
    el tema necesita refuerzo.
    """
    best: dict[str, dict[str, Any]] = {}
    for a in attempts:
        if a.get("score") is None:
            continue
        qid = a.get("quiz_id")
        score = float(a["score"])
        if qid not in best or score > best[qid]["score"]:
            best[qid] = {
                "quiz_id": qid,
                "quiz_title": a.get("quiz_title") or "Cuestionario",
                "subject_id": a.get("subject_id"),
                "score": score,
            }
    weak = [b for b in best.values() if b["score"] < threshold]
    return sorted(weak, key=lambda b: b["score"])


def build_report(
    attempts: list[dict[str, Any]],
    subject_names: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Construye el reporte completo de seguimiento."""
    return {
        "summary": overall_summary(attempts),
        "by_subject": progress_by_subject(attempts, subject_names),
        "evolution": quiz_evolution(attempts),
        "to_reinforce": topics_to_reinforce(attempts),
    }
