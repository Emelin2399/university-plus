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

| # | Módulo | Estado MVP |
|---|--------|:---:|
| 1 | Panel principal del estudiante | ✅ |
| 2 | Biblioteca inteligente de documentos | ✅ |
| 3 | Tutor virtual con IA (RAG) | ✅ |
| 4 | Generador de evaluaciones y simulacros | ✅ |
| 5 | Planificador académico | 🔜 v2 |
| 6 | Seguimiento del aprendizaje | 🔜 v2 |
| 7 | EXPLORA PLUS (investigación académica) | 🔜 v2 |
| 8 | MIS NOTAS PLUS (apuntes) | 🔜 v2 |

## 📁 Estructura del repositorio

```
university-plus/
├── backend/            # API FastAPI (Python)
│   ├── app/
│   │   ├── api/        # Routers por módulo
│   │   ├── core/       # Config, seguridad
│   │   ├── models/     # Esquemas Pydantic
│   │   ├── services/   # Lógica de negocio e IA/RAG
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/           # SPA React + Vite + TS
│   ├── src/
│   └── package.json
├── database/           # Esquema SQL, migraciones y diseño
│   ├── schema.sql
│   └── DATABASE_DESIGN.md
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
