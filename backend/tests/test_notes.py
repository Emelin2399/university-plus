"""Pruebas del repositorio de notas (MIS NOTAS PLUS)."""


class TestNotes:
    async def test_create_and_get(self, repos):
        note = await repos.notes.create(
            "u1", {"title": "Resumen clase 1", "content": "La mitosis..."}
        )
        got = await repos.notes.get("u1", note["id"])
        assert got["title"] == "Resumen clase 1"
        assert got["is_favorite"] is False

    async def test_get_isolated_by_user(self, repos):
        note = await repos.notes.create("u1", {"title": "Privada", "content": "x"})
        assert await repos.notes.get("intruso", note["id"]) is None

    async def test_list_isolated_by_user(self, repos):
        await repos.notes.create("u1", {"title": "N1", "content": "x"})
        assert await repos.notes.list("u2") == []
        assert len(await repos.notes.list("u1")) == 1

    async def test_search_by_title_and_content(self, repos):
        await repos.notes.create("u1", {"title": "Biología celular", "content": "núcleo"})
        await repos.notes.create("u1", {"title": "Historia", "content": "revolución"})
        assert len(await repos.notes.list("u1", query="biología")) == 1
        assert len(await repos.notes.list("u1", query="núcleo")) == 1
        assert len(await repos.notes.list("u1", query="revolución")) == 1
        assert len(await repos.notes.list("u1", query="inexistente")) == 0

    async def test_search_case_insensitive(self, repos):
        await repos.notes.create("u1", {"title": "FÓRMULAS", "content": "E=mc2"})
        assert len(await repos.notes.list("u1", query="fórmulas")) == 1

    async def test_update_content(self, repos):
        note = await repos.notes.create("u1", {"title": "T", "content": "viejo"})
        updated = await repos.notes.update("u1", note["id"], {"content": "nuevo"})
        assert updated["content"] == "nuevo"

    async def test_toggle_favorite(self, repos):
        note = await repos.notes.create("u1", {"title": "T", "content": "x"})
        updated = await repos.notes.update("u1", note["id"], {"is_favorite": True})
        assert updated["is_favorite"] is True

    async def test_update_only_own(self, repos):
        note = await repos.notes.create("u1", {"title": "T", "content": "x"})
        assert await repos.notes.update("intruso", note["id"], {"title": "Z"}) is None

    async def test_delete_only_own(self, repos):
        note = await repos.notes.create("u1", {"title": "T", "content": "x"})
        assert await repos.notes.delete("u2", note["id"]) is False
        assert await repos.notes.delete("u1", note["id"]) is True

    async def test_list_sorted_by_updated_desc(self, repos):
        import asyncio

        n1 = await repos.notes.create("u1", {"title": "Primera", "content": "x"})
        await asyncio.sleep(0.001)
        await repos.notes.create("u1", {"title": "Segunda", "content": "y"})
        await asyncio.sleep(0.001)
        # Actualizar la primera la pone arriba
        await repos.notes.update("u1", n1["id"], {"content": "z"})
        titles = [n["title"] for n in await repos.notes.list("u1")]
        assert titles[0] == "Primera"
