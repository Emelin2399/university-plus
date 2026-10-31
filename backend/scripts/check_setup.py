#!/usr/bin/env python3
"""Verifica que el entorno esté listo para conectar Supabase y OpenAI.

Uso:
    cd backend
    source .venv/bin/activate
    python scripts/check_setup.py

No modifica nada: solo comprueba configuración y conectividad.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Permite importar app.* al ejecutar desde backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"{GREEN}✓{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"{YELLOW}!{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"{RED}✗{RESET} {msg}")


def main() -> int:
    print("\n=== Verificación de entorno — UNIVERSITY PLUS ===\n")
    errors = 0

    # 1. ¿Existe .env?
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        ok(f".env encontrado en {env_path}")
    else:
        fail(".env no existe. Copia .env.example a .env y complétalo.")
        return 1

    # 2. Cargar settings
    try:
        from app.core.config import get_settings

        settings = get_settings()
        ok("Configuración cargada correctamente")
    except Exception as exc:
        fail(f"No se pudo cargar la configuración: {exc}")
        return 1

    # 3. Variables de Supabase
    print("\n-- Supabase --")
    if settings.supabase_url and settings.supabase_url.startswith("https://"):
        ok(f"SUPABASE_URL: {settings.supabase_url}")
    else:
        fail("SUPABASE_URL vacío o inválido (debe empezar con https://)")
        errors += 1

    if settings.supabase_service_key and len(settings.supabase_service_key) > 20:
        ok("SUPABASE_SERVICE_KEY presente")
    else:
        fail("SUPABASE_SERVICE_KEY vacío o demasiado corto")
        errors += 1

    if settings.supabase_anon_key:
        ok("SUPABASE_ANON_KEY presente")
    else:
        warn("SUPABASE_ANON_KEY vacío (necesario para validar tokens de usuario)")

    # 4. Probar conexión a Supabase
    if settings.supabase_url and settings.supabase_service_key:
        print("\n-- Conexión a Supabase --")
        try:
            from app.services.supabase_client import get_supabase

            client = get_supabase(settings)
            # Consulta mínima a una tabla del esquema
            client.table("profiles").select("id").limit(1).execute()
            ok("Conexión a Supabase OK y tabla 'profiles' accesible")
        except Exception as exc:
            fail(f"No se pudo conectar / consultar Supabase: {exc}")
            warn("¿Ejecutaste schema.sql? ¿Las keys son correctas?")
            errors += 1

        # 5. Verificar la función RPC del RAG
        try:
            dummy = [0.0] * 1536
            client.rpc(
                "match_document_chunks",
                {"query_embedding": dummy, "match_count": 1,
                 "p_user_id": "00000000-0000-0000-0000-000000000000",
                 "p_subject_id": None},
            ).execute()
            ok("Función RPC 'match_document_chunks' disponible")
        except Exception as exc:
            fail(f"RPC 'match_document_chunks' no disponible: {exc}")
            warn("Revisa que schema.sql se haya ejecutado completo.")
            errors += 1

    # 6. IA
    print("\n-- Inteligencia Artificial --")
    ok(f"AI_PROVIDER = {settings.ai_provider}")
    if settings.ai_provider == "openai":
        if settings.openai_api_key.startswith("sk-"):
            ok("OPENAI_API_KEY presente")
            print("   (La validación real de la key ocurre en la primera llamada.)")
        else:
            fail("AI_PROVIDER=openai pero OPENAI_API_KEY no parece válida")
            errors += 1
    else:
        warn("Modo mock: la IA usa respuestas simuladas (sin coste).")

    # Resultado
    print("\n" + "=" * 50)
    if errors == 0:
        ok("Todo listo. Puedes arrancar el backend: uvicorn app.main:app --reload")
        return 0
    fail(f"{errors} problema(s) encontrado(s). Revisa los mensajes de arriba.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
