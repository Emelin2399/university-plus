"""Módulo 7: EXPLORA PLUS — investigación y profundización académica.

De una duda a una ruta confiable: busca fuentes académicas, las organiza en
una ruta de aprendizaje y permite seguir el avance de cada recurso.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import Settings, get_settings
from app.core.security import CurrentUser, get_current_user
from app.models.schemas import (
    ExploreQuery,
    ExploreResult,
    ExploreSearchSummary,
    ResourceStatusUpdate,
)
from app.repositories.base import RepositoryBundle
from app.repositories.factory import get_repositories
from app.services.academic_sources import get_academic_source_service
from app.services.learning_path import build_learning_path

router = APIRouter(prefix="/explore", tags=["explore"])


@router.post("/search", response_model=ExploreResult, status_code=201)
async def search(
    payload: ExploreQuery,
    user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    repos: RepositoryBundle = Depends(get_repositories),
):
    service = get_academic_source_service(settings)
    try:
        results = await service.search(payload.query, payload.limit)
    except Exception as exc:  # pragma: no cover - depende de red
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo consultar las fuentes académicas: {exc}",
        ) from exc

    resources = [r.to_dict() for r in results]
    for r in resources:
        r["status"] = "pending"

    path = build_learning_path(resources)

    saved = await repos.explore.save_search(
        user.id, {"query": payload.query, "resources": resources, "path": path}
    )
    return {
        "id": saved["id"],
        "query": saved["query"],
        "resources": resources,
        "path": path,
    }


@router.get("/history", response_model=list[ExploreSearchSummary])
async def history(
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    searches = await repos.explore.list_searches(user.id)
    return [
        {"id": s["id"], "query": s["query"], "created_at": s.get("created_at")}
        for s in searches
    ]


@router.get("/{search_id}", response_model=ExploreResult)
async def get_search(
    search_id: str,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    search = await repos.explore.get_search(user.id, search_id)
    if not search:
        raise HTTPException(status_code=404, detail="Búsqueda no encontrada.")
    return {
        "id": search["id"],
        "query": search["query"],
        "resources": search.get("resources", []),
        "path": search.get("path", []),
    }


@router.patch("/{search_id}/resource", response_model=ExploreResult)
async def update_resource_status(
    search_id: str,
    payload: ResourceStatusUpdate,
    user: CurrentUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    search = await repos.explore.update_resource_status(
        user.id, search_id, payload.resource_index, payload.status
    )
    if not search:
        raise HTTPException(
            status_code=404, detail="Búsqueda o recurso no encontrado."
        )
    return {
        "id": search["id"],
        "query": search["query"],
        "resources": search.get("resources", []),
        "path": search.get("path", []),
    }
