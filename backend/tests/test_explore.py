"""Pruebas de EXPLORA PLUS: fuentes académicas, ruta de aprendizaje y repo."""
from app.services.academic_sources import AcademicSourceService
from app.services.learning_path import build_learning_path


class _MockSettings:
    ai_provider = "mock"
    explora_provider = "mock"


class TestAcademicSourcesMock:
    async def test_returns_results(self):
        svc = AcademicSourceService(_MockSettings())
        results = await svc.search("fotosíntesis", limit=8)
        assert len(results) > 0

    async def test_respects_limit(self):
        svc = AcademicSourceService(_MockSettings())
        results = await svc.search("tema", limit=2)
        assert len(results) <= 2

    async def test_mock_results_flagged_as_example(self):
        # Criterio de calidad: el mock debe marcar sus resultados como ejemplo.
        svc = AcademicSourceService(_MockSettings())
        results = await svc.search("tema")
        assert all(r.is_example for r in results)

    async def test_mock_never_invents_doi(self):
        # Ningún resultado de ejemplo debe presentar un DOI "real".
        svc = AcademicSourceService(_MockSettings())
        results = await svc.search("tema")
        assert all(r.doi is None for r in results)

    async def test_includes_a_video(self):
        svc = AcademicSourceService(_MockSettings())
        results = await svc.search("tema")
        assert any(r.resource_type == "video" for r in results)


class TestLearningPath:
    def test_empty_resources(self):
        assert build_learning_path([]) == []

    def test_video_goes_to_visualizar(self):
        resources = [{"resource_type": "video", "year": 2022}]
        path = build_learning_path(resources)
        assert len(path) == 1
        assert path[0]["step"] == "visualizar"

    def test_recent_open_access_is_comprender(self):
        resources = [{"resource_type": "article", "open_access": True, "year": 2023}]
        path = build_learning_path(resources)
        assert path[0]["step"] == "comprender"

    def test_old_article_is_profundizar(self):
        resources = [{"resource_type": "article", "open_access": False, "year": 2005}]
        path = build_learning_path(resources)
        assert path[0]["step"] == "profundizar"

    def test_steps_are_ordered(self):
        resources = [
            {"resource_type": "article", "year": 2000},  # profundizar
            {"resource_type": "video", "year": 2022},  # visualizar
            {"resource_type": "article", "open_access": True, "year": 2023},  # comprender
        ]
        path = build_learning_path(resources)
        steps = [p["step"] for p in path]
        assert steps == ["comprender", "visualizar", "profundizar"]
        assert [p["position"] for p in path] == [1, 2, 3]

    def test_empty_steps_omitted(self):
        resources = [{"resource_type": "video", "year": 2022}]
        path = build_learning_path(resources)
        assert len(path) == 1  # solo "visualizar"


class TestExploreRepository:
    async def test_save_and_get(self, repos):
        saved = await repos.explore.save_search(
            "u1", {"query": "mitosis", "resources": [{"title": "X"}], "path": []}
        )
        got = await repos.explore.get_search("u1", saved["id"])
        assert got["query"] == "mitosis"

    async def test_isolated_by_user(self, repos):
        saved = await repos.explore.save_search("u1", {"query": "x", "resources": []})
        assert await repos.explore.get_search("intruso", saved["id"]) is None

    async def test_list_isolated(self, repos):
        await repos.explore.save_search("u1", {"query": "a", "resources": []})
        await repos.explore.save_search("u2", {"query": "b", "resources": []})
        assert len(await repos.explore.list_searches("u1")) == 1

    async def test_update_resource_status(self, repos):
        saved = await repos.explore.save_search(
            "u1",
            {
                "query": "x",
                "resources": [
                    {"title": "R0", "status": "pending"},
                    {"title": "R1", "status": "pending"},
                ],
            },
        )
        updated = await repos.explore.update_resource_status(
            "u1", saved["id"], 1, "understood"
        )
        assert updated["resources"][1]["status"] == "understood"
        assert updated["resources"][0]["status"] == "pending"

    async def test_update_invalid_index(self, repos):
        saved = await repos.explore.save_search(
            "u1", {"query": "x", "resources": [{"title": "R0"}]}
        )
        assert await repos.explore.update_resource_status("u1", saved["id"], 9, "understood") is None

    async def test_update_status_only_own(self, repos):
        saved = await repos.explore.save_search(
            "u1", {"query": "x", "resources": [{"title": "R0"}]}
        )
        assert await repos.explore.update_resource_status("intruso", saved["id"], 0, "understood") is None
