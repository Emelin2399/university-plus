"""Selector de implementación de repositorios.

Elige Supabase cuando está configurado; en caso contrario, usa el almacén
en memoria. Se expone como dependencia de FastAPI vía `get_repositories`.
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.repositories.base import RepositoryBundle


@lru_cache
def _build_bundle(cache_key: str) -> RepositoryBundle:
    settings = get_settings()
    if settings.supabase_url and settings.supabase_service_key:
        from app.repositories.supabase_repo import build_supabase_bundle

        return build_supabase_bundle(settings)

    from app.repositories.memory import build_memory_bundle

    return build_memory_bundle()


def get_repositories(
    settings: Settings = Depends(get_settings),
) -> RepositoryBundle:
    # El cache_key cambia solo si cambia la configuración relevante.
    key = f"{bool(settings.supabase_url)}:{bool(settings.supabase_service_key)}"
    return _build_bundle(key)
