"""Pruebas de la ingesta desde URL (sin red: se mockea la descarga)."""
import pytest

from app.services import url_ingest
from app.services.url_ingest import (
    FetchedResource,
    UrlIngestError,
    ingest_url,
    resource_to_pages,
)


class TestResourceToPages:
    def test_html_resource_single_page(self):
        html = b"<html><head><title>Tema</title></head><body><p>Texto visible</p></body></html>"
        res = FetchedResource(url="https://x.org/a", content=html, content_type="text/html")
        name, pages = resource_to_pages(res)
        assert name == "Tema"
        assert len(pages) == 1
        assert "Texto visible" in pages[0][1]

    def test_html_without_title_uses_url(self):
        html = b"<html><body><p>Solo cuerpo</p></body></html>"
        res = FetchedResource(url="https://x.org/articulo", content=html, content_type="text/html")
        name, pages = resource_to_pages(res)
        assert name == "https://x.org/articulo"

    def test_empty_html_raises(self):
        res = FetchedResource(url="https://x.org/a", content=b"<html></html>", content_type="text/html")
        with pytest.raises(UrlIngestError):
            resource_to_pages(res)


class TestIngestUrlValidation:
    async def test_rejects_invalid_url(self):
        with pytest.raises(UrlIngestError):
            await ingest_url("javascript:alert(1)")

    async def test_rejects_non_http(self):
        with pytest.raises(UrlIngestError):
            await ingest_url("ftp://x.org/a")


class TestIngestUrlWithMockedFetch:
    async def test_ingests_html_page(self, monkeypatch):
        async def fake_fetch(url, max_bytes=None):
            return FetchedResource(
                url=url,
                content=b"<html><head><title>Wiki</title></head><body><p>Contenido educativo.</p></body></html>",
                content_type="text/html; charset=utf-8",
            )

        monkeypatch.setattr(url_ingest, "fetch_url", fake_fetch)
        name, pages, content_type = await ingest_url("https://es.wikipedia.org/wiki/X")
        assert name == "Wiki"
        assert "Contenido educativo" in pages[0][1]
        assert "text/html" in content_type
