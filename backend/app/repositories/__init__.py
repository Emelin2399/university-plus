"""Capa de repositorios: abstrae el acceso a datos.

Dos implementaciones intercambiables:
- `memory`: almacenamiento en RAM para desarrollo sin credenciales.
- `supabase`: persistencia real en Postgres/Supabase + Storage.

La selección es automática según la configuración (ver `get_repositories`).
"""
