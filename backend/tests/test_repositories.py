"""Pruebas del repositorio en memoria, con foco en aislamiento por usuario."""


class TestSubjects:
    async def test_create_and_list(self, repos):
        s = await repos.subjects.create("u1", {"name": "Álgebra"})
        items = await repos.subjects.list("u1")
        assert len(items) == 1
        assert items[0]["id"] == s["id"]
        assert items[0]["name"] == "Álgebra"

    async def test_default_color(self, repos):
        s = await repos.subjects.create("u1", {"name": "X"})
        assert s["color"] == "#2563eb"

    async def test_isolation_between_users(self, repos):
        await repos.subjects.create("u1", {"name": "A"})
        assert await repos.subjects.list("u2") == []

    async def test_delete_only_own(self, repos):
        s = await repos.subjects.create("u1", {"name": "A"})
        assert await repos.subjects.delete("u2", s["id"]) is False
        assert await repos.subjects.delete("u1", s["id"]) is True


class TestDocuments:
    async def test_create_file_document(self, repos):
        s = await repos.subjects.create("u1", {"name": "A"})
        doc = await repos.documents.create(
            "u1", {"subject_id": s["id"], "name": "a.pdf"}
        )
        assert doc["source_type"] == "file"
        assert doc["status"] == "processing"

    async def test_create_link_document(self, repos):
        s = await repos.subjects.create("u1", {"name": "A"})
        doc = await repos.documents.create(
            "u1",
            {
                "subject_id": s["id"],
                "name": "Artículo",
                "source_type": "link",
                "source_url": "https://example.com/a",
            },
        )
        assert doc["source_type"] == "link"
        assert doc["source_url"] == "https://example.com/a"

    async def test_filter_by_subject(self, repos):
        s1 = await repos.subjects.create("u1", {"name": "A"})
        s2 = await repos.subjects.create("u1", {"name": "B"})
        await repos.documents.create("u1", {"subject_id": s1["id"], "name": "a.pdf"})
        await repos.documents.create("u1", {"subject_id": s2["id"], "name": "b.pdf"})
        assert len(await repos.documents.list("u1", s1["id"])) == 1
        assert len(await repos.documents.list("u1")) == 2

    async def test_update_status(self, repos):
        s = await repos.subjects.create("u1", {"name": "A"})
        doc = await repos.documents.create(
            "u1", {"subject_id": s["id"], "name": "a.pdf"}
        )
        await repos.documents.update_status(doc["id"], "ready", page_count=5)
        listed = await repos.documents.list("u1")
        assert listed[0]["status"] == "ready"
        assert listed[0]["page_count"] == 5


class TestChunkSearch:
    async def _seed(self, repos, ai, user, subject_id, texts):
        doc = await repos.documents.create(
            user, {"subject_id": subject_id, "name": "d.pdf"}
        )
        chunks = []
        for i, t in enumerate(texts):
            chunks.append(
                {
                    "id": f"c{i}",
                    "document_id": doc["id"],
                    "user_id": user,
                    "content": t,
                    "page": 1,
                    "chunk_index": i,
                    "embedding": await ai.embed(t),
                }
            )
        await repos.chunks.bulk_insert(chunks)
        return doc

    async def test_search_recovers_best_match(self, repos, ai):
        s = await repos.subjects.create("u1", {"name": "Bio"})
        await self._seed(repos, ai, "u1", s["id"], ["mitocondria", "fotosíntesis"])
        results = await repos.chunks.search("u1", await ai.embed("mitocondria"), 5)
        assert results[0]["content"] == "mitocondria"

    async def test_search_isolated_by_user(self, repos, ai):
        s = await repos.subjects.create("u1", {"name": "Bio"})
        await self._seed(repos, ai, "u1", s["id"], ["tema privado"])
        assert await repos.chunks.search("u2", await ai.embed("tema privado"), 5) == []

    async def test_text_for_source_concatenates(self, repos, ai):
        s = await repos.subjects.create("u1", {"name": "Bio"})
        await self._seed(repos, ai, "u1", s["id"], ["parte 1", "parte 2"])
        text = await repos.chunks.text_for_source("u1", None, s["id"])
        assert "parte 1" in text and "parte 2" in text


class TestQuizzes:
    async def test_create_and_get(self, repos):
        s = await repos.subjects.create("u1", {"name": "A"})
        quiz = await repos.quizzes.create(
            "u1",
            {"id": "q1", "subject_id": s["id"], "title": "T", "config": {},
             "questions": []},
        )
        got = await repos.quizzes.get("u1", "q1")
        assert got["title"] == "T"
        assert quiz["user_id"] == "u1"

    async def test_get_isolated_by_user(self, repos):
        s = await repos.subjects.create("u1", {"name": "A"})
        await repos.quizzes.create(
            "u1", {"id": "q1", "subject_id": s["id"], "title": "T",
                   "config": {}, "questions": []}
        )
        assert await repos.quizzes.get("intruso", "q1") is None

    async def test_create_attempt(self, repos):
        attempt = await repos.quizzes.create_attempt(
            "u1", {"id": "a1", "quiz_id": "q1", "score": 80.0}
        )
        assert attempt["user_id"] == "u1"
        assert attempt["score"] == 80.0


class TestProgressRepository:
    async def test_attempts_isolated_by_user(self, repos):
        await repos.quizzes.create_attempt(
            "u1", {"id": "a1", "quiz_id": "q1", "subject_id": "s1", "score": 70.0}
        )
        await repos.quizzes.create_attempt(
            "u2", {"id": "a2", "quiz_id": "q2", "subject_id": "s2", "score": 90.0}
        )
        u1_attempts = await repos.progress.attempts("u1")
        assert len(u1_attempts) == 1
        assert u1_attempts[0]["score"] == 70.0

    async def test_filter_by_subject(self, repos):
        await repos.quizzes.create_attempt(
            "u1", {"id": "a1", "quiz_id": "q1", "subject_id": "s1", "score": 70.0}
        )
        await repos.quizzes.create_attempt(
            "u1", {"id": "a2", "quiz_id": "q2", "subject_id": "s2", "score": 80.0}
        )
        assert len(await repos.progress.attempts("u1", "s1")) == 1

    async def test_attempts_have_timestamp(self, repos):
        await repos.quizzes.create_attempt(
            "u1", {"id": "a1", "quiz_id": "q1", "subject_id": "s1", "score": 70.0}
        )
        attempts = await repos.progress.attempts("u1")
        assert attempts[0]["finished_at"] is not None
