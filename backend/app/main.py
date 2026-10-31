"""UNIVERSITY PLUS — API backend (FastAPI).

Punto de entrada de la aplicación. Registra los routers de cada módulo del MVP.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import documents, health, quizzes, subjects, tutor
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="UNIVERSITY PLUS API",
    description="Plataforma educativa con IA para estudiantes universitarios.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers de los módulos
app.include_router(health.router)
app.include_router(subjects.router)
app.include_router(documents.router)
app.include_router(tutor.router)
app.include_router(quizzes.router)


@app.get("/", tags=["root"])
async def root():
    return {
        "name": "UNIVERSITY PLUS API",
        "version": "0.1.0",
        "docs": "/docs",
    }
