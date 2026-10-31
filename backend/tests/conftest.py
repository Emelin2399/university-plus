"""Fixtures compartidos para la suite de pruebas."""
import asyncio
import inspect

import pytest

from app.repositories import memory
from app.repositories.memory import build_memory_bundle
from app.services.ai_service import AIService


# ---------------------------------------------------------------------------
# Soporte de tests `async def`.
#
# En producción se usa `pytest-asyncio` (ver requirements-dev.txt). Si el plugin
# no está instalado, este hook ejecuta las corutinas directamente, de modo que
# la suite corre igual sin dependencias adicionales.
# ---------------------------------------------------------------------------
def _asyncio_plugin_present(config) -> bool:
    return config.pluginmanager.hasplugin("asyncio")


def pytest_collection_modifyitems(config, items):
    if _asyncio_plugin_present(config):
        return
    for item in items:
        if inspect.iscoroutinefunction(getattr(item, "function", None)):
            item.add_marker(pytest.mark.asyncio)


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    if _asyncio_plugin_present(pyfuncitem.config):
        return None  # deja que pytest-asyncio lo maneje
    func = pyfuncitem.obj
    if not inspect.iscoroutinefunction(func):
        return None
    # Resolver solo los argumentos que la función declara.
    sig = inspect.signature(func)
    kwargs = {
        name: pyfuncitem.funcargs[name]
        for name in sig.parameters
        if name in pyfuncitem.funcargs
    }
    asyncio.run(func(**kwargs))
    return True


class _StubSettings:
    """Settings mínimo para el servicio de IA en modo mock (sin pydantic)."""

    ai_provider = "mock"
    openai_api_key = ""
    openai_chat_model = "gpt-4o-mini"
    openai_embedding_model = "text-embedding-3-small"


@pytest.fixture
def ai() -> AIService:
    return AIService(_StubSettings())


@pytest.fixture
def repos():
    """Bundle de repositorios en memoria, limpio en cada test."""
    # Limpiar los almacenes globales entre tests para evitar fugas de estado.
    memory._subjects.clear()
    memory._documents.clear()
    memory._chunks.clear()
    memory._quizzes.clear()
    memory._attempts.clear()
    return build_memory_bundle()
