"""Cliente de Supabase (service role) para operaciones del backend.

La service key NUNCA se expone al frontend. Toda operación con permisos
elevados pasa por aquí, aplicando siempre el filtro por `user_id`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.config import Settings

# Cache del cliente a nivel de módulo (evita recrearlo en cada petición).
# No usamos lru_cache sobre Settings porque el objeto no es "hashable"
# en Pydantic v2.
_client = None


def get_supabase(settings: "Settings"):
    """Devuelve un cliente de Supabase con la service role key.

    Se importa perezosamente para no exigir la dependencia en modo mock.
    El cliente se crea una sola vez y se reutiliza.
    """
    global _client

    if not settings.supabase_url or not settings.supabase_service_key:
        raise RuntimeError(
            "Supabase no está configurado. Define SUPABASE_URL y "
            "SUPABASE_SERVICE_KEY en el archivo .env"
        )

    if _client is None:
        from supabase import create_client

        _client = create_client(
            settings.supabase_url, settings.supabase_service_key
        )
    return _client
