"""Pruebas del repositorio de actividades (Planificador académico)."""


class TestActivities:
    async def test_create_defaults_pending(self, repos):
        s = await repos.subjects.create("u1", {"name": "A"})
        act = await repos.activities.create(
            "u1", {"subject_id": s["id"], "title": "Entregar ensayo"}
        )
        assert act["status"] == "pending"
        assert act["title"] == "Entregar ensayo"

    async def test_list_isolated_by_user(self, repos):
        s = await repos.subjects.create("u1", {"name": "A"})
        await repos.activities.create("u1", {"subject_id": s["id"], "title": "X"})
        assert await repos.activities.list("u2") == []
        assert len(await repos.activities.list("u1")) == 1

    async def test_filter_by_status(self, repos):
        s = await repos.subjects.create("u1", {"name": "A"})
        await repos.activities.create(
            "u1", {"subject_id": s["id"], "title": "A", "status": "pending"}
        )
        await repos.activities.create(
            "u1", {"subject_id": s["id"], "title": "B", "status": "done"}
        )
        assert len(await repos.activities.list("u1", status="done")) == 1
        assert len(await repos.activities.list("u1", status="pending")) == 1

    async def test_filter_by_subject(self, repos):
        s1 = await repos.subjects.create("u1", {"name": "A"})
        s2 = await repos.subjects.create("u1", {"name": "B"})
        await repos.activities.create("u1", {"subject_id": s1["id"], "title": "A"})
        await repos.activities.create("u1", {"subject_id": s2["id"], "title": "B"})
        assert len(await repos.activities.list("u1", subject_id=s1["id"])) == 1

    async def test_sorted_by_due_date(self, repos):
        s = await repos.subjects.create("u1", {"name": "A"})
        await repos.activities.create(
            "u1", {"subject_id": s["id"], "title": "Tarde", "due_date": "2026-12-01"}
        )
        await repos.activities.create(
            "u1", {"subject_id": s["id"], "title": "Pronto", "due_date": "2026-01-01"}
        )
        await repos.activities.create(
            "u1", {"subject_id": s["id"], "title": "Sin fecha"}
        )
        titles = [a["title"] for a in await repos.activities.list("u1")]
        assert titles == ["Pronto", "Tarde", "Sin fecha"]

    async def test_update_status(self, repos):
        s = await repos.subjects.create("u1", {"name": "A"})
        act = await repos.activities.create(
            "u1", {"subject_id": s["id"], "title": "X"}
        )
        updated = await repos.activities.update("u1", act["id"], {"status": "done"})
        assert updated["status"] == "done"

    async def test_update_only_own(self, repos):
        s = await repos.subjects.create("u1", {"name": "A"})
        act = await repos.activities.create(
            "u1", {"subject_id": s["id"], "title": "X"}
        )
        assert await repos.activities.update("intruso", act["id"], {"status": "done"}) is None

    async def test_delete_only_own(self, repos):
        s = await repos.subjects.create("u1", {"name": "A"})
        act = await repos.activities.create(
            "u1", {"subject_id": s["id"], "title": "X"}
        )
        assert await repos.activities.delete("u2", act["id"]) is False
        assert await repos.activities.delete("u1", act["id"]) is True
