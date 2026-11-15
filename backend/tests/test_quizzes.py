"""Pruebas del flujo de cuestionarios: retroalimentación por pregunta.

Usan la función pura ``score_attempt`` (sin FastAPI ni Pydantic) para poder
ejecutarse en cualquier entorno de pruebas.
"""
from app.services.quiz_scoring import score_attempt


def _quiz():
    return {
        "id": "q1",
        "subject_id": "s1",
        "title": "T",
        "questions": [
            {
                "id": "a",
                "statement": "¿2 + 2?",
                "type": "multiple_choice",
                "options": ["3", "4", "5", "6"],
                "correct_answer": "4",
                "explanation": "Dos más dos son cuatro.",
            },
            {
                "id": "b",
                "statement": "El agua hierve a 100°C a nivel del mar.",
                "type": "true_false",
                "options": ["Verdadero", "Falso"],
                "correct_answer": "Verdadero",
                "explanation": "A presión de 1 atm.",
            },
        ],
    }


class TestAttemptDetails:
    def test_marks_correct_and_incorrect(self):
        given = {"a": "4", "b": "Falso"}
        details, correct = score_attempt(_quiz(), given)
        assert correct == 1
        assert len(details) == 2

        d_a = next(d for d in details if d["question_id"] == "a")
        assert d_a["is_correct"] is True
        assert d_a["given_answer"] == "4"
        assert d_a["correct_answer"] == "4"
        assert d_a["explanation"] == "Dos más dos son cuatro."

        d_b = next(d for d in details if d["question_id"] == "b")
        assert d_b["is_correct"] is False
        assert d_b["given_answer"] == "Falso"
        assert d_b["correct_answer"] == "Verdadero"
        assert d_b["explanation"] == "A presión de 1 atm."

    def test_case_and_space_insensitive(self):
        details, correct = score_attempt(_quiz(), {"b": "  verdadero "})
        d_b = next(d for d in details if d["question_id"] == "b")
        assert d_b["is_correct"] is True
        assert correct == 1

    def test_unanswered_question_is_incorrect(self):
        details, correct = score_attempt(_quiz(), {})
        assert correct == 0
        d_a = next(d for d in details if d["question_id"] == "a")
        assert d_a["given_answer"] == ""
        assert d_a["is_correct"] is False

    def test_details_preserve_question_order(self):
        details, _ = score_attempt(_quiz(), {})
        assert [d["question_id"] for d in details] == ["a", "b"]

    def test_options_included_in_detail(self):
        details, _ = score_attempt(_quiz(), {})
        d_a = next(d for d in details if d["question_id"] == "a")
        assert d_a["options"] == ["3", "4", "5", "6"]
