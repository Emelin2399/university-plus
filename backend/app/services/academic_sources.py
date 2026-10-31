"""EXPLORA PLUS — conectores a fuentes académicas.

Patrón de proveedores, análogo al servicio de IA:
- "mock": resultados de ejemplo claramente etiquetados, para desarrollo sin red.
- "openalex" / "crossref": consultas reales a las APIs públicas.

Criterio de calidad (Anexo 1 §10): NO se inventan referencias ni DOI. Los
conectores reales devuelven solo lo que la fuente entrega; el mock marca
explícitamente sus resultados como ejemplos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

if False:  # TYPE_CHECKING sin importar en runtime
    from app.core.config import Settings


@dataclass
class AcademicResult:
    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str | None = None  # revista / institución
    doi: str | None = None
    url: str | None = None
    source: str = "mock"  # openalex | crossref | mock
    resource_type: str = "article"  # article | video | book | other
    open_access: bool | None = None
    is_example: bool = False  # True solo en modo mock

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "venue": self.venue,
            "doi": self.doi,
            "url": self.url,
            "source": self.source,
            "resource_type": self.resource_type,
            "open_access": self.open_access,
            "is_example": self.is_example,
        }


class AcademicSourceService:
    def __init__(self, settings: "Settings"):
        self.settings = settings
        # Reutilizamos el proveedor de IA como señal: si estamos en mock,
        # las fuentes también lo están (evita llamadas de red en desarrollo).
        self.provider = getattr(settings, "explora_provider", None) or (
            "mock" if settings.ai_provider == "mock" else "openalex"
        )

    async def search(self, query: str, limit: int = 8) -> list[AcademicResult]:
        if self.provider == "openalex":
            return await self._search_openalex(query, limit)
        if self.provider == "crossref":
            return await self._search_crossref(query, limit)
        return self._search_mock(query, limit)

    # ---------------------------------------------------------------
    # Mock
    # ---------------------------------------------------------------
    def _search_mock(self, query: str, limit: int) -> list[AcademicResult]:
        base = [
            AcademicResult(
                title=f"(Ejemplo) Introducción a «{query}»",
                authors=["Autor de Ejemplo A."],
                year=2021,
                venue="Revista de Ejemplo",
                doi=None,
                url="https://example.org/intro",
                source="mock",
                resource_type="article",
                open_access=True,
                is_example=True,
            ),
            AcademicResult(
                title=f"(Ejemplo) Video educativo sobre «{query}»",
                authors=["Canal Educativo"],
                year=2022,
                venue="Plataforma de Video",
                url="https://example.org/video",
                source="mock",
                resource_type="video",
                is_example=True,
            ),
            AcademicResult(
                title=f"(Ejemplo) Estudio avanzado de «{query}»",
                authors=["Autor de Ejemplo B.", "Autor de Ejemplo C."],
                year=2023,
                venue="Universidad de Ejemplo",
                url="https://example.org/avanzado",
                source="mock",
                resource_type="article",
                open_access=False,
                is_example=True,
            ),
        ]
        return base[:limit]

    # ---------------------------------------------------------------
    # OpenAlex (https://openalex.org/)
    # ---------------------------------------------------------------
    async def _search_openalex(self, query: str, limit: int) -> list[AcademicResult]:
        import httpx

        params = {"search": query, "per_page": limit}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get("https://api.openalex.org/works", params=params)
            resp.raise_for_status()
            data = resp.json()

        results: list[AcademicResult] = []
        for w in data.get("results", []):
            authors = [
                a.get("author", {}).get("display_name")
                for a in w.get("authorships", [])
                if a.get("author")
            ]
            doi = w.get("doi")
            results.append(
                AcademicResult(
                    title=w.get("title") or "(sin título)",
                    authors=[a for a in authors if a],
                    year=w.get("publication_year"),
                    venue=(w.get("host_venue") or {}).get("display_name"),
                    doi=doi.replace("https://doi.org/", "") if doi else None,
                    url=doi or w.get("id"),
                    source="openalex",
                    resource_type="article",
                    open_access=(w.get("open_access") or {}).get("is_oa"),
                )
            )
        return results

    # ---------------------------------------------------------------
    # Crossref (https://www.crossref.org/)
    # ---------------------------------------------------------------
    async def _search_crossref(self, query: str, limit: int) -> list[AcademicResult]:
        import httpx

        params = {"query": query, "rows": limit}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get("https://api.crossref.org/works", params=params)
            resp.raise_for_status()
            items = resp.json().get("message", {}).get("items", [])

        results: list[AcademicResult] = []
        for it in items:
            authors = [
                " ".join(filter(None, [a.get("given"), a.get("family")]))
                for a in it.get("author", [])
            ]
            year = None
            issued = it.get("issued", {}).get("date-parts", [[None]])
            if issued and issued[0]:
                year = issued[0][0]
            title_list = it.get("title") or ["(sin título)"]
            results.append(
                AcademicResult(
                    title=title_list[0],
                    authors=[a for a in authors if a.strip()],
                    year=year,
                    venue=(it.get("container-title") or [None])[0],
                    doi=it.get("DOI"),
                    url=it.get("URL"),
                    source="crossref",
                    resource_type="article",
                )
            )
        return results


def get_academic_source_service(settings: "Settings") -> AcademicSourceService:
    return AcademicSourceService(settings)
