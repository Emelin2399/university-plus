"""Pruebas de las utilidades puras de procesamiento de documentos."""
from app.services.document_processing import (
    chunk_text,
    extract_html_text,
    is_valid_http_url,
    looks_like_pdf_url,
)


class TestChunkText:
    def test_splits_long_text_into_multiple_chunks(self):
        chunks = chunk_text("palabra " * 500, size=800, overlap=100)
        assert len(chunks) > 1

    def test_short_text_single_chunk(self):
        chunks = chunk_text("texto corto")
        assert chunks == ["texto corto"]

    def test_empty_text_no_chunks(self):
        assert chunk_text("   ") == []

    def test_overlap_preserves_context(self):
        text = "".join(str(i % 10) for i in range(2000))
        chunks = chunk_text(text, size=800, overlap=100)
        # El final de un fragmento reaparece al inicio del siguiente (solape).
        assert chunks[0][-100:] == chunks[1][:100]


class TestExtractHtmlText:
    def test_extracts_title_and_body(self):
        html = "<html><head><title>T</title></head><body><p>Hola mundo</p></body></html>"
        title, text = extract_html_text(html)
        assert title == "T"
        assert "Hola mundo" in text

    def test_ignores_script_and_style(self):
        html = (
            "<html><head><style>.a{}</style><script>evil()</script></head>"
            "<body><p>Contenido</p></body></html>"
        )
        _, text = extract_html_text(html)
        assert "Contenido" in text
        assert "evil" not in text
        assert ".a{}" not in text

    def test_empty_body(self):
        _, text = extract_html_text("<html><body></body></html>")
        assert text == ""


class TestUrlValidation:
    def test_accepts_http_and_https(self):
        assert is_valid_http_url("http://example.com")
        assert is_valid_http_url("https://example.com/path")

    def test_rejects_other_schemes(self):
        assert not is_valid_http_url("ftp://example.com")
        assert not is_valid_http_url("javascript:alert(1)")
        assert not is_valid_http_url("file:///etc/passwd")

    def test_rejects_malformed(self):
        assert not is_valid_http_url("not a url")
        assert not is_valid_http_url("")

    def test_pdf_detection_by_extension(self):
        assert looks_like_pdf_url("https://x.org/doc.pdf")
        assert not looks_like_pdf_url("https://x.org/page")

    def test_pdf_detection_by_content_type(self):
        assert looks_like_pdf_url("https://x.org/d", "application/pdf")
        assert not looks_like_pdf_url("https://x.org/d", "text/html")
