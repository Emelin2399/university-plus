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


class TestNoteAttachments:
    async def test_add_list_and_delete(self, repos):
        note = await repos.notes.create("u1", {"title": "Con adjuntos", "content": "x"})
        att = await repos.notes.add_attachment(
            "u1", note["id"], "apuntes.pdf", b"%PDF-1.4", "application/pdf"
        )
        assert att is not None
        assert att["name"] == "apuntes.pdf"
        assert att["note_id"] == note["id"]
        assert att["size_bytes"] == len(b"%PDF-1.4")

        listed = await repos.notes.list_attachments("u1", note["id"])
        assert len(listed) == 1
        assert listed[0]["id"] == att["id"]

        assert await repos.notes.delete_attachment("u1", note["id"], att["id"]) is True
        assert await repos.notes.list_attachments("u1", note["id"]) == []

    async def test_multiple_and_any_type(self, repos):
        note = await repos.notes.create("u1", {"title": "Varios", "content": "x"})
        await repos.notes.add_attachment(
            "u1", note["id"], "foto.png", b"img", "image/png"
        )
        await repos.notes.add_attachment(
            "u1", note["id"], "hoja.xlsx", b"xls",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        await repos.notes.add_attachment(
            "u1", note["id"], "notas.txt", b"texto", "text/plain"
        )
        listed = await repos.notes.list_attachments("u1", note["id"])
        assert len(listed) == 3
        names = {a["name"] for a in listed}
        assert names == {"foto.png", "hoja.xlsx", "notas.txt"}

    async def test_attachments_included_in_note(self, repos):
        note = await repos.notes.create("u1", {"title": "Nota", "content": "x"})
        await repos.notes.add_attachment(
            "u1", note["id"], "a.pdf", b"data", "application/pdf"
        )
        got = await repos.notes.get("u1", note["id"])
        assert len(got["attachments"]) == 1
        assert got["attachments"][0]["name"] == "a.pdf"
        listed = await repos.notes.list("u1")
        assert len(listed[0]["attachments"]) == 1

    async def test_add_attachment_isolated_by_user(self, repos):
        note = await repos.notes.create("u1", {"title": "Privada", "content": "x"})
        # Un intruso no puede adjuntar a una nota ajena.
        assert (
            await repos.notes.add_attachment(
                "intruso", note["id"], "x.pdf", b"d", "application/pdf"
            )
            is None
        )

    async def test_list_attachments_isolated_by_user(self, repos):
        note = await repos.notes.create("u1", {"title": "Privada", "content": "x"})
        await repos.notes.add_attachment(
            "u1", note["id"], "x.pdf", b"d", "application/pdf"
        )
        # Un intruso no puede listar los adjuntos de una nota ajena.
        assert await repos.notes.list_attachments("intruso", note["id"]) is None

    async def test_delete_attachment_isolated_by_user(self, repos):
        note = await repos.notes.create("u1", {"title": "Privada", "content": "x"})
        att = await repos.notes.add_attachment(
            "u1", note["id"], "x.pdf", b"d", "application/pdf"
        )
        # Un intruso no puede borrar un adjunto ajeno.
        assert (
            await repos.notes.delete_attachment("intruso", note["id"], att["id"])
            is False
        )
        # El dueño sí puede.
        assert await repos.notes.delete_attachment("u1", note["id"], att["id"]) is True

    async def test_delete_note_cascades_attachments(self, repos):
        note = await repos.notes.create("u1", {"title": "Nota", "content": "x"})
        await repos.notes.add_attachment(
            "u1", note["id"], "x.pdf", b"d", "application/pdf"
        )
        assert await repos.notes.delete("u1", note["id"]) is True
        # Tras borrar la nota, sus adjuntos ya no existen.
        assert await repos.notes.list_attachments("u1", note["id"]) is None
