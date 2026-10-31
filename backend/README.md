# Backend — UNIVERSITY PLUS API

API REST construida con **FastAPI**. Orquesta la lógica de negocio, la seguridad y la integración con la IA (RAG) y Supabase.

## Requisitos

- Python 3.11+

## Puesta en marcha

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # y completar valores
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Documentación interactiva (Swagger): http://localhost:8000/docs

## Modo de desarrollo sin servicios externos

Por defecto el backend arranca en modo **mock**:

- `AI_PROVIDER=mock` → embeddings y respuestas deterministas, sin llamar a OpenAI.
- Sin `SUPABASE_URL` → almacenamiento **en memoria** y un usuario de prueba (`dev-user-0000`).

Esto permite ejecutar y probar todo el flujo (asignaturas → documentos → tutor → cuestionarios) sin credenciales. Al configurar `.env` con Supabase y OpenAI, el mismo código usa los servicios reales.

## Estructura

```
app/
├── api/              # Routers por módulo (subjects, documents, tutor, quizzes, health)
├── core/             # config.py (settings), security.py (auth)
├── models/           # schemas.py (Pydantic)
├── repositories/     # Capa de persistencia (patrón repositorio)
│   ├── base.py       # Interfaces abstractas
│   ├── memory.py     # Implementación en memoria (dev)
│   ├── supabase_repo.py  # Implementación Supabase (producción)
│   └── factory.py    # Selección automática según config
├── services/         # ai_service.py (IA/RAG), document_processing.py, supabase_client.py
└── main.py           # App FastAPI
```

## Capa de repositorios

Los routers **no conocen** el almacenamiento concreto: dependen de las
interfaces de `repositories/base.py`. El `factory` elige la implementación:

- Si hay `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` → **Supabase** (Postgres + Storage + RPC vectorial).
- Si no → **memoria** (ideal para desarrollo y pruebas sin credenciales).

Para pasar de dev a producción **no se cambia código**, solo variables de entorno.

Consulta la guía completa de conexión en [`../database/SUPABASE_SETUP.md`](../database/SUPABASE_SETUP.md).

## Endpoints principales (MVP)

| Método | Ruta | Módulo |
|--------|------|--------|
| GET | `/health` | Salud del servicio |
| GET/POST/DELETE | `/subjects` | Asignaturas |
| GET/POST/DELETE | `/documents` | Biblioteca de documentos |
| POST | `/tutor/ask` | Tutor virtual (RAG) |
| POST/GET | `/quizzes` | Cuestionarios |
| POST | `/quizzes/attempts` | Enviar intento y calcular resultado |

## Seguridad

- Autenticación por **JWT de Supabase** (`Authorization: Bearer <token>`).
- La **service key** de Supabase y la **API key** de IA viven solo aquí, nunca en el frontend.
- Validación de tipo y tamaño de archivos en la carga.

## Nota sobre persistencia

Este esqueleto usa almacenamiento en memoria para poder correr sin infraestructura. La estructura está lista para sustituir esos `_store`/`_docs`/`_chunks` por llamadas a Supabase (ver `database/schema.sql`) sin cambiar la forma de los endpoints.
