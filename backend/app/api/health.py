"""Endpoint de salud para verificar que el servicio está vivo."""
from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(settings: Settings = Depends(get_settings)):
    return {
        "status": "ok",
        "env": settings.app_env,
        "ai_provider": settings.ai_provider,
        "supabase_configured": bool(settings.supabase_url),
    }
