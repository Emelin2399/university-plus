# 🎓 UNIVERSITY PLUS

> Aprende mejor, organiza tu tiempo y alcanza tus metas.

Plataforma web educativa con herramientas de inteligencia artificial para estudiantes universitarios. Integra organización académica, gestión de documentos, tutoría asistida por IA (RAG), generación de cuestionarios y seguimiento del progreso.

## 📐 Arquitectura

Arquitectura web cliente-servidor:

```
┌─────────────┐      HTTPS/REST      ┌──────────────┐      ┌───────────────┐
│   Frontend  │ ───────────────────> │   Backend    │ ───> │   Supabase    │
│  React (SPA)│ <─────────────────── │   FastAPI    │      │  Postgres +   │
└─────────────┘                      └──────┬───────┘      │  pgvector +   │
                                            │              │  Storage +    │
                                            │              │  Auth         │
                                            v              └───────────────┘
                                     ┌──────────────┐
                                     │  Proveedor   │
                                     │  de IA (API) │
                                     └──────────────┘
```

| Componente | Tecnología | Responsabilidad |
|------------|-----------|-----------------|
| Frontend | React + Vite + TypeScript + Tailwind | Interfaz, navegación, formularios y paneles |
| Backend | Python + FastAPI | API, lógica de negocio, validaciones, orquestación de IA |
| Base de datos | PostgreSQL / Supabase (+ pgvector) | Usuarios, asignaturas, documentos, actividades, resultados, embeddings |
| Almacenamiento | Supabase Storage | Archivos académicos con acceso controlado |
| IA | API de un proveedor de modelos (p. ej. OpenAI) | Resúmenes, explicaciones, generación de preguntas, tutoría |

> ⚠️ **Seguridad:** las claves de servicios externos (API de IA, service keys de Supabase) viven **solo en el backend** y nunca se exponen al navegador.

## 🧩 Módulos

**Los 8 módulos de la propuesta están implementados** (backend + frontend + tests).

| # | Módulo | Estado |
|---|--------|:---:|
| 1 | Panel principal del estudiante | ✅ |
| 2 | Biblioteca inteligente de documentos (archivos **y enlaces**) | ✅ |
| 3 | Tutor virtual con IA (RAG) | ✅ |
| 4 | Generador de evaluaciones y simulacros | ✅ |
| 5 | Planificador académico | ✅ |
| 6 | Seguimiento del aprendizaje | ✅ |
| 7 | EXPLORA PLUS (investigación académica) | ✅ |
| 8 | MIS NOTAS PLUS (apuntes) | ✅ |

## 📁 Estructura del repositorio

```
university-plus/
├── backend/            # API FastAPI (Python)
│   ├── app/
│   │   ├── api/            # Routers: subjects, documents, tutor, quizzes,
│   │   │                   #          activities, notes, progress, explore
│   │   ├── core/           # Config, seguridad
│   │   ├── models/         # Esquemas Pydantic
│   │   ├── repositories/   # Capa de persistencia (memoria | Supabase)
│   │   ├── services/       # IA/RAG, docs, URLs, progreso, fuentes académicas
│   │   └── main.py
│   ├── scripts/            # check_setup.py, smoke_test.py
│   ├── tests/              # Suite pytest (95 pruebas)
│   ├── requirements.txt
│   └── .env.example
├── frontend/           # SPA React + Vite + TS
│   ├── src/
│   │   ├── pages/          # Una página por módulo
│   │   ├── components/     # Layout y UI
│   │   ├── context/        # AuthContext
│   │   └── lib/            # api.ts, supabase.ts
│   └── package.json
├── database/           # Esquema SQL, diseño y guía de Supabase
│   ├── schema.sql
│   ├── DATABASE_DESIGN.md
│   └── SUPABASE_SETUP.md
├── QUICKSTART.md
└── README.md
```

## 🚀 Puesta en marcha

👉 **Empieza por la guía rápida: [`QUICKSTART.md`](QUICKSTART.md)**

Guías detalladas por parte:
- Backend → [`backend/README.md`](backend/README.md)
- Frontend → [`frontend/README.md`](frontend/README.md)
- Base de datos → [`database/DATABASE_DESIGN.md`](database/DATABASE_DESIGN.md)
- Conexión con Supabase → [`database/SUPABASE_SETUP.md`](database/SUPABASE_SETUP.md)

## 🎯 Alcance del MVP

1. Registro e inicio de sesión de usuarios.
2. Creación de asignaturas y carga de documentos.
3. Tutor de preguntas y respuestas basado en los documentos cargados (RAG).
4. Generación de cuestionarios y visualización de resultados.

## 🔒 Principios de seguridad y privacidad

- Autenticación segura y contraseñas protegidas (hash).
- Aislamiento por usuario: cada estudiante solo accede a sus propios datos.
- Validación de tipo y tamaño de archivos.
- Claves secretas solo en el servidor.
- La IA es **apoyo** al aprendizaje, no sustituye el criterio del estudiante; las respuestas incluyen trazabilidad a las fuentes.
