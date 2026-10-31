"""Utilidades puras para procesar documentos: extracción y troceo de texto.

Separadas de la capa HTTP y de almacenamiento para poder testearlas y
reutilizarlas desde cualquier repositorio. Soporta dos orígenes de contenido:
archivos (PDF) y enlaces (PDF remoto o página web).
"""
from __future__ import annotations

import io
from html.parser import HTMLParser
from urllib.parse import urlparse


def extract_pdf_text(data: bytes) -> list[tuple[int, str]]:
    """Extrae texto por página. Devuelve [(page, text), ...]."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages, start=1):
        pages.append((i, page.extract_text() or ""))
    return pages


def chunk_text(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    """Divide el texto en fragmentos con solape para conservar contexto."""
    text = " ".join(text.split())
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return [c for c in chunks if c.strip()]


# ---------------------------------------------------------------------------
# Soporte para enlaces (URLs)
# ---------------------------------------------------------------------------

def is_valid_http_url(url: str) -> bool:
    """Valida que la URL use http/https y tenga host (evita esquemas raros)."""
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def looks_like_pdf_url(url: str, content_type: str | None = None) -> bool:
    """Heurística: ¿la URL apunta a un PDF? Por extensión o content-type."""
    if content_type and "application/pdf" in content_type.lower():
        return True
    path = urlparse(url).path.lower()
    return path.endswith(".pdf")


class _TextExtractor(HTMLParser):
    """Extrae texto visible de un HTML, ignorando script/style y el <title>."""

    _SKIP = {"script", "style", "noscript", "head", "meta", "link"}

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._title_parts: list[str] = []
        self._in_title = False
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: object) -> None:
        if tag in self._SKIP:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        if self._in_title:
            self._title_parts.append(text)
        elif self._skip_depth == 0:
            self._parts.append(text)

    @property
    def title(self) -> str:
        return " ".join(self._title_parts).strip()

    @property
    def text(self) -> str:
        return " ".join(self._parts).strip()


def extract_html_text(html: str) -> tuple[str, str]:
    """Extrae (título, texto) de un documento HTML.

    Devuelve el texto visible, descartando scripts y estilos.
    """
    parser = _TextExtractor()
    parser.feed(html)
    return parser.title, parser.text
