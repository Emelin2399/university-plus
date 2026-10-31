"""Dependencias de seguridad: validación del usuario autenticado vía Supabase JWT."""
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings


@dataclass
class CurrentUser:
    """Representa al estudiante autenticado."""
    id: str
    email: str | None = None


async def get_current_user(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    """Valida el token Bearer emitido por Supabase Auth y devuelve el usuario.

    El frontend obtiene el access_token de Supabase y lo envía en el header
    `Authorization: Bearer <token>`. Aquí lo verificamos contra Supabase.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el token de autenticación.",
        )

    token = authorization.split(" ", 1)[1].strip()

    # En modo desarrollo sin Supabase configurado, aceptamos un token de prueba.
    if settings.app_env == "development" and not settings.supabase_url:
        return CurrentUser(id="dev-user-0000", email="dev@universityplus.local")

    from app.services.supabase_client import get_supabase

    supabase = get_supabase(settings)
    try:
        response = supabase.auth.get_user(token)
    except Exception as exc:  # pragma: no cover - depende de red
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
        ) from exc

    user = getattr(response, "user", None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado para el token.",
        )

    return CurrentUser(id=user.id, email=getattr(user, "email", None))
