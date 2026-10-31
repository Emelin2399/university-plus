"""Pruebas del servicio de IA en modo mock."""
import pytest

from app.services.ai_service import EMBEDDING_DIM


class TestEmbeddings:
    async def test_embedding_dimension(self, ai):
        emb = await ai.embed("hola")
        assert len(emb) == EMBEDDING_DIM

    async def test_deterministic(self, ai):
        assert await ai.embed("mismo texto") == await ai.embed("mismo texto")

    async def test_different_text_different_embedding(self, ai):
        assert await ai.embed("texto a") != await ai.embed("texto b")

    async def test_values_in_range(self, ai):
        emb = await ai.embed("rango")
        assert all(-1.0 <= v <= 1.0 for v in emb)


class TestTutor:
    async def test_no_context_warns_insufficient(self, ai):
        res = await ai.answer_with_context("¿?", [])
        assert "suficiente" in res["answer"].lower()
        assert res["sources"] == []

    async def test_with_context_returns_sources(self, ai):
        chunks = [{"document_id": "d1", "page": 7, "content": "La célula es la unidad."}]
        res = await ai.answer_with_context("¿Qué es la célula?", chunks)
        assert res["sources"][0]["page"] == 7
        assert res["sources"][0]["document_id"] == "d1"

    async def test_answer_mentions_question(self, ai):
        chunks = [{"document_id": "d1", "page": 1, "content": "contenido"}]
        res = await ai.answer_with_context("mi pregunta única", chunks)
        assert "mi pregunta única" in res["answer"]


class TestQuizGeneration:
    @pytest.mark.parametrize("n", [1, 3, 5, 10])
    async def test_generates_requested_count(self, ai, n):
        qs = await ai.generate_quiz("material", num_questions=n, difficulty="medium")
        assert len(qs) == n

    async def test_questions_well_formed(self, ai):
        qs = await ai.generate_quiz("material", num_questions=2, difficulty="hard")
        for q in qs:
            assert "statement" in q
            assert "type" in q
            assert "correct_answer" in q
            assert "position" in q
