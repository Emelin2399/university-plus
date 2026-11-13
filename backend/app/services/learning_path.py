"""EXPLORA PLUS — generador de ruta de aprendizaje (lógica pura).

Organiza los recursos encontrados en una secuencia progresiva para que el
estudiante no se abrume (Anexo 1 §6):
  1. Comprender el concepto (introductorio)
  2. Visualizar el tema (video)
  3. Profundizar (artículo/estudio)

Al ser pura, es fácil de probar y no depende de red ni del proveedor.
"""
from __future__ import annotations

from typing import Any

# Orden de prioridad de los pasos de la ruta.
STEP_ORDER = ["comprender", "visualizar", "profundizar"]

STEP_LABEL = {
    "comprender": "Comprender el concepto",
    "visualizar": "Visualizar el tema",
    "profundizar": "Profundizar",
}


def _classify(resource: dict[str, Any]) -> str:
    """Asigna un recurso a un paso de la ruta según su tipo y año."""
    rtype = resource.get("resource_type")
    if rtype == "video":
        return "visualizar"
    # Recursos de acceso abierto o recientes sirven como introducción.
    if resource.get("open_access") or (resource.get("year") or 0) >= 2020:
        return "comprender"
    return "profundizar"


def build_learning_path(resources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa los recursos en pasos ordenados de la ruta de aprendizaje.

    Devuelve una lista de pasos, cada uno con su etiqueta y sus recursos.
    Los pasos vacíos se omiten.
    """
    buckets: dict[str, list[dict[str, Any]]] = {s: [] for s in STEP_ORDER}
    for r in resources:
        buckets[_classify(r)].append(r)

    path: list[dict[str, Any]] = []
    position = 1
    for step in STEP_ORDER:
        items = buckets[step]
        if not items:
            continue
        path.append(
            {
                "position": position,
                "step": step,
                "label": STEP_LABEL[step],
                "resources": items,
            }
        )
        position += 1
    return path
