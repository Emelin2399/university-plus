"""Pruebas del análisis de progreso (seguimiento del aprendizaje)."""
from app.services.progress_analysis import (
    build_report,
    overall_summary,
    progress_by_subject,
    quiz_evolution,
    topics_to_reinforce,
)


def _attempt(quiz_id, subject_id, score, when, title="Quiz"):
    return {
        "quiz_id": quiz_id,
        "subject_id": subject_id,
        "quiz_title": title,
        "score": score,
        "finished_at": when,
    }


class TestOverallSummary:
    def test_empty(self):
        s = overall_summary([])
        assert s == {"total_attempts": 0, "average_score": 0.0, "best_score": 0.0}

    def test_average_and_best(self):
        attempts = [
            _attempt("q1", "s1", 80, "2026-01-01"),
            _attempt("q2", "s1", 60, "2026-01-02"),
        ]
        s = overall_summary(attempts)
        assert s["total_attempts"] == 2
        assert s["average_score"] == 70.0
        assert s["best_score"] == 80


class TestProgressBySubject:
    def test_groups_and_averages(self):
        attempts = [
            _attempt("q1", "s1", 90, "2026-01-01"),
            _attempt("q2", "s1", 70, "2026-01-02"),
            _attempt("q3", "s2", 50, "2026-01-03"),
        ]
        result = progress_by_subject(attempts, {"s1": "Mate", "s2": "Historia"})
        by_id = {r["subject_id"]: r for r in result}
        assert by_id["s1"]["average_score"] == 80.0
        assert by_id["s1"]["attempts"] == 2
        assert by_id["s2"]["average_score"] == 50.0

    def test_sorted_worst_first(self):
        attempts = [
            _attempt("q1", "s1", 90, "2026-01-01"),
            _attempt("q2", "s2", 40, "2026-01-02"),
        ]
        result = progress_by_subject(attempts, {"s1": "A", "s2": "B"})
        assert result[0]["subject_id"] == "s2"  # peor promedio primero

    def test_handles_missing_subject(self):
        attempts = [_attempt("q1", None, 75, "2026-01-01")]
        result = progress_by_subject(attempts)
        assert result[0]["subject_id"] is None
        assert result[0]["subject_name"] == "Sin asignatura"


class TestQuizEvolution:
    def test_ordered_by_time(self):
        attempts = [
            _attempt("q2", "s1", 60, "2026-03-01", "Segundo"),
            _attempt("q1", "s1", 80, "2026-01-01", "Primero"),
        ]
        ev = quiz_evolution(attempts)
        assert [p["quiz_title"] for p in ev] == ["Primero", "Segundo"]

    def test_includes_score_and_time(self):
        ev = quiz_evolution([_attempt("q1", "s1", 55, "2026-01-01")])
        assert ev[0]["score"] == 55
        assert ev[0]["finished_at"] == "2026-01-01"


class TestTopicsToReinforce:
    def test_flags_low_scores(self):
        attempts = [
            _attempt("q1", "s1", 45, "2026-01-01", "Débil"),
            _attempt("q2", "s1", 85, "2026-01-02", "Fuerte"),
        ]
        weak = topics_to_reinforce(attempts)
        assert len(weak) == 1
        assert weak[0]["quiz_title"] == "Débil"

    def test_uses_best_attempt_per_quiz(self):
        # Si mejoró en un reintento por encima del umbral, ya no se marca.
        attempts = [
            _attempt("q1", "s1", 40, "2026-01-01"),
            _attempt("q1", "s1", 75, "2026-01-05"),
        ]
        assert topics_to_reinforce(attempts) == []

    def test_custom_threshold(self):
        attempts = [_attempt("q1", "s1", 70, "2026-01-01")]
        assert len(topics_to_reinforce(attempts, threshold=80)) == 1
        assert topics_to_reinforce(attempts, threshold=60) == []

    def test_sorted_lowest_first(self):
        attempts = [
            _attempt("q1", "s1", 55, "2026-01-01", "Medio"),
            _attempt("q2", "s1", 30, "2026-01-02", "Bajo"),
        ]
        weak = topics_to_reinforce(attempts)
        assert weak[0]["quiz_title"] == "Bajo"


class TestBuildReport:
    def test_full_report_structure(self):
        attempts = [
            _attempt("q1", "s1", 90, "2026-01-01", "A"),
            _attempt("q2", "s2", 40, "2026-01-02", "B"),
        ]
        report = build_report(attempts, {"s1": "Mate", "s2": "Historia"})
        assert set(report) == {"summary", "by_subject", "evolution", "to_reinforce"}
        assert report["summary"]["total_attempts"] == 2
        assert len(report["evolution"]) == 2
        assert len(report["to_reinforce"]) == 1  # solo el de 40

    def test_empty_report(self):
        report = build_report([])
        assert report["summary"]["total_attempts"] == 0
        assert report["by_subject"] == []
        assert report["evolution"] == []
        assert report["to_reinforce"] == []
