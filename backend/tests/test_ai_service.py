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

    async def test_options_are_distinct(self, ai):
        # Mejora 1: las opciones de multiple_choice deben ser distintas.
        qs = await ai.generate_quiz("material", num_questions=4, difficulty="medium")
        for q in qs:
            if q["type"] == "multiple_choice":
                opts = q["options"]
                assert len(opts) == len(set(opts)), "hay opciones duplicadas"
                assert q["correct_answer"] in opts

    async def test_difficulty_gradient_easy_to_advanced(self, ai):
        # Mejora 2: las preguntas llegan ordenadas de fácil a avanzada.
        qs = await ai.generate_quiz("material", num_questions=6, difficulty="medium")
        labels = [q.get("difficulty") for q in qs]
        order = {"facil": 0, "medio": 1, "avanzado": 2}
        ranks = [order[label] for label in labels]
        assert ranks == sorted(ranks), "la dificultad no progresa de fácil a avanzada"
        assert labels[0] == "facil"
        assert labels[-1] == "avanzado"
        assert [q["position"] for q in qs] == list(range(len(qs)))


class TestQuizSanitizer:
    """Pruebas de la salvaguarda de deduplicación/validación de opciones."""

    def test_dedup_and_correct_answer_present(self):
        from app.services.ai_service import _sanitize_quiz_items

        items = [
            {
                "type": "multiple_choice",
                "statement": "¿Cuántos?",
                # Cuatro opciones iguales colapsan a una sola: con <2 opciones
                # distintas la pregunta se descarta (regla de robustez).
                "options": ["dieciocho", "dieciocho", "dieciocho", "dieciocho"],
                "correct_answer": "dieciocho",
            }
        ]
        out = _sanitize_quiz_items(items)
        assert out == []

    def test_dedup_keeps_question_with_two_distinct_options(self):
        from app.services.ai_service import _sanitize_quiz_items

        items = [
            {
                "type": "multiple_choice",
                "statement": "¿Cuántos?",
                "options": ["dieciocho", "dieciocho", "veinte", "veinte"],
                "correct_answer": "dieciocho",
            }
        ]
        out = _sanitize_quiz_items(items)
        opts = out[0]["options"]
        assert opts == ["dieciocho", "veinte"]
        assert out[0]["correct_answer"] in opts
        assert out[0]["position"] == 0

    def test_correct_answer_added_when_missing(self):
        from app.services.ai_service import _sanitize_quiz_items

        items = [
            {
                "type": "multiple_choice",
                "statement": "P",
                "options": ["a", "b", "c"],
                "correct_answer": "d",
            }
        ]
        out = _sanitize_quiz_items(items)
        assert "d" in out[0]["options"]

    def test_partial_dedup_keeps_question(self):
        from app.services.ai_service import _sanitize_quiz_items

        items = [
            {
                "type": "multiple_choice",
                "statement": "P",
                "options": ["x", "X ", "y", "y"],
                "correct_answer": "x",
            }
        ]
        out = _sanitize_quiz_items(items)
        # "x" y "X " colapsan (insensible a mayúsculas/espacios); queda x, y.
        assert out[0]["options"] == ["x", "y"]

    def test_position_reindexed(self):
        from app.services.ai_service import _sanitize_quiz_items

        items = [
            {"type": "open", "statement": "A", "correct_answer": "a"},
            {"type": "open", "statement": "B", "correct_answer": "b"},
        ]
        out = _sanitize_quiz_items(items)
        assert [q["position"] for q in out] == [0, 1]

    def test_true_false_bad_answer_converts_to_multiple_choice(self):
        # Bug reportado: type true_false con correct_answer "he is not".
        # Si tiene opciones válidas, se convierte a multiple_choice.
        from app.services.ai_service import _sanitize_quiz_items

        items = [
            {
                "type": "true_false",
                "statement": "He ___ at home.",
                "options": ["is", "he is not", "are", "am"],
                "correct_answer": "he is not",
            }
        ]
        out = _sanitize_quiz_items(items)
        assert len(out) == 1
        assert out[0]["type"] == "multiple_choice"
        assert out[0]["correct_answer"] in out[0]["options"]

    def test_true_false_bad_answer_without_options_is_dropped(self):
        # type true_false con respuesta no V/F y sin opciones útiles: descartar.
        from app.services.ai_service import _sanitize_quiz_items

        items = [
            {
                "type": "true_false",
                "statement": "He ___ at home.",
                "options": None,
                "correct_answer": "he is not",
            }
        ]
        out = _sanitize_quiz_items(items)
        # Sin opciones y respuesta no V/F -> solo quedaría 1 opción (la correcta)
        # -> no hay >=2 opciones usables -> se descarta.
        assert out == []

    def test_true_false_lowercase_answer_normalized(self):
        from app.services.ai_service import _sanitize_quiz_items

        items = [
            {
                "type": "true_false",
                "statement": "El agua hierve a 100°C.",
                "options": ["foo", "bar"],
                "correct_answer": "verdadero",
            }
        ]
        out = _sanitize_quiz_items(items)
        assert out[0]["type"] == "true_false"
        assert out[0]["correct_answer"] == "Verdadero"
        assert out[0]["options"] == ["Verdadero", "Falso"]

    def test_correct_answer_never_outside_options(self):
        # Garantía global: ninguna pregunta sobreviviente tiene la respuesta
        # correcta fuera de sus opciones.
        from app.services.ai_service import _sanitize_quiz_items

        items = [
            {
                "type": "true_false",
                "statement": "X",
                "options": ["alfa", "beta", "gamma"],
                "correct_answer": "he is not",
            },
            {
                "type": "multiple_choice",
                "statement": "Y",
                "options": ["a", "b", "c"],
                "correct_answer": "z",
            },
            {"type": "open", "statement": "Z", "correct_answer": "texto libre"},
        ]
        out = _sanitize_quiz_items(items)
        for q in out:
            if q.get("options"):
                assert q["correct_answer"] in q["options"]

    def test_multiple_choice_dropped_when_too_few_options(self):
        from app.services.ai_service import _sanitize_quiz_items

        items = [
            {
                "type": "multiple_choice",
                "statement": "P",
                "options": ["solo"],
                "correct_answer": "solo",
            }
        ]
        out = _sanitize_quiz_items(items)
        assert out == []

    def test_position_reindexed_after_drops(self):
        from app.services.ai_service import _sanitize_quiz_items

        items = [
            {
                "type": "multiple_choice",
                "statement": "ok1",
                "options": ["a", "b", "c"],
                "correct_answer": "a",
            },
            {
                "type": "multiple_choice",
                "statement": "roto",
                "options": ["solo"],
                "correct_answer": "solo",
            },
            {
                "type": "multiple_choice",
                "statement": "ok2",
                "options": ["x", "y"],
                "correct_answer": "x",
            },
        ]
        out = _sanitize_quiz_items(items)
        assert len(out) == 2
        assert [q["position"] for q in out] == [0, 1]
        assert [q["statement"] for q in out] == ["ok1", "ok2"]
