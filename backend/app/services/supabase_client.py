"""Cliente de Supabase (service role) para operaciones del backend.

La service key NUNCA se expone al frontend. Toda operación con permisos
elevados pasa por aquí, aplicando siempre el filtro por `user_id`.
"""
from functools import lru_cache

from app.core.config import Settings


@lru_cache
def get_supabase(settings: Settings):
    """Devuelve un cliente de Supabase con la service role key.

    Se importa perezosamente para no exigir la dependencia en modo mock.
    """
    from supabase import create_client

    if not settings.supabase_url or not settings.supabase_service_key:
        raise RuntimeError(
            "Supabase no está configurado. Define SUPABASE_URL y "
            "SUPABASE_SERVICE_KEY en el archivo .env"
        )
    return create_client(settings.supabase_url, settings.supabase_service_key)
