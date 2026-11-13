"""Ingesta de contenido desde una URL (PDF remoto o página web).

La descarga (impura, usa red) se aísla en `fetch_url` para poder sustituirla
en pruebas. La conversión a páginas de texto es reutilizable para archivos
y enlaces por igual.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.services.document_processing import (
    extract_html_text,
    extract_pdf_text,
    is_valid_http_url,
    looks_like_pdf_url,
)

# Límite de descarga por seguridad (evita URLs gigantes).
DEFAULT_MAX_BYTES = 20 * 1024 * 1024


@dataclass
class FetchedResource:
    url: str
    content: bytes
    content_type: str | None


class UrlIngestError(Exception):
    """Error controlado durante la ingesta de una URL."""


async def fetch_url(url: str, max_bytes: int = DEFAULT_MAX_BYTES) -> FetchedResource:
    """Descarga el contenido de una URL. Lanza UrlIngestError si falla."""
    import httpx

    try:
        async with httpx.AsyncClient(
            timeout=30, follow_redirects=True
        ) as client:
            resp = await client.get(url, headers={"User-Agent": "UniversityPlus/0.1"})
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise UrlIngestError(f"No se pudo descargar la URL: {exc}") from exc

    content = resp.content
    if len(content) > max_bytes:
        raise UrlIngestError(
            f"El contenido supera el límite de {max_bytes // (1024 * 1024)} MB."
        )
    return FetchedResource(
        url=url,
        content=content,
        content_type=resp.headers.get("content-type"),
    )


def resource_to_pages(resource: FetchedResource) -> tuple[str, list[tuple[int, str]]]:
    """Convierte un recurso descargado en (nombre_sugerido, [(page, text)]).

    - PDF: usa el extractor por páginas.
    - HTML/otros: una sola "página" con el texto visible; el título se usa
      como nombre sugerido del documento.
    """
    if looks_like_pdf_url(resource.url, resource.content_type):
        pages = extract_pdf_text(resource.content)
        name = resource.url.rsplit("/", 1)[-1] or "documento.pdf"
        return name, pages

    # Tratar como HTML / texto
    try:
        html = resource.content.decode("utf-8", errors="ignore")
    except Exception as exc:  # pragma: no cover
        raise UrlIngestError(f"No se pudo decodificar el contenido: {exc}") from exc

    title, text = extract_html_text(html)
    if not text.strip():
        raise UrlIngestError("No se encontró texto legible en la página.")
    name = title or resource.url
    return name, [(1, text)]


async def ingest_url(url: str, max_bytes: int = DEFAULT_MAX_BYTES):
    """Valida, descarga y convierte una URL en páginas de texto.

    Devuelve (nombre_sugerido, páginas, content_type).
    """
    if not is_valid_http_url(url):
        raise UrlIngestError("La URL no es válida (debe empezar con http/https).")
    resource = await fetch_url(url, max_bytes=max_bytes)
    name, pages = resource_to_pages(resource)
    return name, pages, resource.content_type
