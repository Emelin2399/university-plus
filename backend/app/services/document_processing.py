"""Utilidades puras para procesar documentos: extracción y troceo de texto.

Separadas de la capa HTTP y de almacenamiento para poder testearlas y
reutilizarlas desde cualquier repositorio.
"""
from __future__ import annotations

import io


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
