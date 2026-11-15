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


def _quiz_with_open():
    """Cuestionario con una pregunta abierta además de las auto-calificables."""
    quiz = _quiz()
    quiz["questions"].append(
        {
            "id": "c",
            "statement": "Explica la forma interrogativa del verbo 'to be'.",
            "type": "open",
            "options": None,
            "correct_answer": "Se invierte el sujeto y el verbo: Am I? Are you?",
            "explanation": "En inglés, la interrogación antepone el verbo.",
        }
    )
    return quiz


class TestAttemptDetails:
    def test_marks_correct_and_incorrect(self):
        given = {"a": "4", "b": "Falso"}
        details, correct, gradable = score_attempt(_quiz(), given)
        assert correct == 1
        assert gradable == 2
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
        details, correct, _ = score_attempt(_quiz(), {"b": "  verdadero "})
        d_b = next(d for d in details if d["question_id"] == "b")
        assert d_b["is_correct"] is True
        assert correct == 1

    def test_unanswered_question_is_incorrect(self):
        details, correct, gradable = score_attempt(_quiz(), {})
        assert correct == 0
        assert gradable == 2
        d_a = next(d for d in details if d["question_id"] == "a")
        assert d_a["given_answer"] == ""
        assert d_a["is_correct"] is False

    def test_details_preserve_question_order(self):
        details, _, _ = score_attempt(_quiz(), {})
        assert [d["question_id"] for d in details] == ["a", "b"]

    def test_options_included_in_detail(self):
        details, _, _ = score_attempt(_quiz(), {})
        d_a = next(d for d in details if d["question_id"] == "a")
        assert d_a["options"] == ["3", "4", "5", "6"]

    def test_auto_gradable_questions_flagged(self):
        details, _, _ = score_attempt(_quiz(), {})
        for d in details:
            assert d["auto_graded"] is True
            assert d["is_correct"] in (True, False)


class TestOpenQuestions:
    def test_open_question_excluded_from_denominator(self):
        # Respondemos bien las dos auto-calificables y escribimos algo libre.
        given = {"a": "4", "b": "Verdadero", "c": "mi respuesta libre"}
        details, correct, gradable = score_attempt(_quiz_with_open(), given)
        # La abierta NO cuenta en el denominador ni en los aciertos.
        assert gradable == 2
        assert correct == 2
        assert len(details) == 3

    def test_open_detail_is_neutral_and_carries_reference(self):
        given = {"c": "cualquier cosa"}
        details, _, _ = score_attempt(_quiz_with_open(), given)
        d_c = next(d for d in details if d["question_id"] == "c")
        assert d_c["auto_graded"] is False
        assert d_c["is_correct"] is None
        assert d_c["given_answer"] == "cualquier cosa"
        assert (
            d_c["correct_answer"]
            == "Se invierte el sujeto y el verbo: Am I? Are you?"
        )
        assert d_c["explanation"] == "En inglés, la interrogación antepone el verbo."

    def test_open_question_does_not_affect_score(self):
        # Solo preguntas abiertas: no hay nada que puntuar (denominador 0).
        quiz = {
            "id": "q",
            "subject_id": "s",
            "title": "T",
            "questions": [
                {
                    "id": "x",
                    "statement": "Pregunta abierta",
                    "type": "open",
                    "correct_answer": "referencia",
                    "explanation": "exp",
                }
            ],
        }
        details, correct, gradable = score_attempt(quiz, {"x": "algo"})
        assert correct == 0
        assert gradable == 0
        assert details[0]["is_correct"] is None
