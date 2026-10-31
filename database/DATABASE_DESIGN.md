# 🗄️ Diseño de base de datos — UNIVERSITY PLUS

Motor: **PostgreSQL** (Supabase) con extensiones `pgcrypto` (UUIDs) y `vector` (pgvector para RAG).

## Principios

- **Identidad:** los usuarios se apoyan en `auth.users` de Supabase. La tabla `profiles` extiende los datos del estudiante.
- **Aislamiento por usuario:** toda tabla con datos del estudiante lleva `user_id` y se protege con **Row Level Security (RLS)**, de modo que un estudiante jamás pueda leer datos de otro.
- **Claves foráneas con `ON DELETE CASCADE`** para mantener integridad al eliminar una asignatura/documento.
- **Timestamps** `created_at` / `updated_at` en todas las tablas.

## Diagrama de relaciones (MVP)

```
profiles (1) ──< (N) subjects
                     │
                     ├──< (N) documents ──< (N) document_chunks   [embeddings RAG]
                     │                  └──< (N) summaries
                     │
                     ├──< (N) quizzes ──< (N) questions
                     │              └──< (N) quiz_attempts ──< (N) attempt_answers
                     │
                     └──< (N) activities        [tareas/exámenes]

profiles (1) ──< (N) chat_messages              [historial del tutor]
profiles (1) ──< (N) study_sessions             [opcional]
```

## Tablas

### `profiles`
Extiende `auth.users`. Identidad y datos del estudiante.

| Columna | Tipo | Notas |
|---------|------|-------|
| id | uuid (PK) | = `auth.users.id` |
| full_name | text | Nombre del estudiante |
| email | text | Correo (espejo de auth) |
| role | text | `student` \| `admin` (default `student`) |
| created_at / updated_at | timestamptz | |

### `subjects` — Asignaturas
| Columna | Tipo | Notas |
|---------|------|-------|
| id | uuid (PK) | |
| user_id | uuid (FK → profiles) | Dueño |
| name | text | Nombre de la materia |
| term | text | Periodo (ej. "2026-1") |
| color | text | Color para la UI |
| created_at / updated_at | timestamptz | |

### `documents` — Material académico
| Columna | Tipo | Notas |
|---------|------|-------|
| id | uuid (PK) | |
| subject_id | uuid (FK → subjects) | |
| user_id | uuid (FK → profiles) | Denormalizado para RLS |
| name | text | Nombre visible |
| storage_path | text | Ruta en Supabase Storage |
| mime_type | text | `application/pdf`, etc. |
| size_bytes | bigint | Validación de tamaño |
| status | text | `pending` \| `processing` \| `ready` \| `error` |
| page_count | int | |
| created_at / updated_at | timestamptz | |

### `document_chunks` — Fragmentos para RAG
| Columna | Tipo | Notas |
|---------|------|-------|
| id | uuid (PK) | |
| document_id | uuid (FK → documents) | |
| user_id | uuid (FK → profiles) | RLS |
| content | text | Texto del fragmento |
| page | int | Página/sección de origen (trazabilidad) |
| chunk_index | int | Orden dentro del documento |
| embedding | vector(1536) | Embedding del proveedor de IA |
| created_at | timestamptz | |

> Índice IVFFlat sobre `embedding` para búsqueda semántica por similitud de coseno.

### `summaries` — Resúmenes generados
| Columna | Tipo | Notas |
|---------|------|-------|
| id | uuid (PK) | |
| document_id | uuid (FK → documents) | |
| user_id | uuid (FK → profiles) | |
| content | text | Resumen / conceptos clave |
| kind | text | `summary` \| `key_concepts` \| `glossary` |
| created_at | timestamptz | |

### `quizzes` — Cuestionarios
| Columna | Tipo | Notas |
|---------|------|-------|
| id | uuid (PK) | |
| subject_id | uuid (FK → subjects) | |
| user_id | uuid (FK → profiles) | |
| title | text | |
| config | jsonb | dificultad, nº preguntas, fuente |
| created_at | timestamptz | |

### `questions` — Preguntas de un cuestionario
| Columna | Tipo | Notas |
|---------|------|-------|
| id | uuid (PK) | |
| quiz_id | uuid (FK → quizzes) | |
| statement | text | Enunciado |
| type | text | `multiple_choice` \| `true_false` \| `open` |
| options | jsonb | Lista de opciones (si aplica) |
| correct_answer | text | Respuesta/criterio |
| explanation | text | Explicación de la respuesta |
| position | int | Orden |

### `quiz_attempts` — Intentos
| Columna | Tipo | Notas |
|---------|------|-------|
| id | uuid (PK) | |
| quiz_id | uuid (FK → quizzes) | |
| user_id | uuid (FK → profiles) | |
| score | numeric | Resultado (0–100) |
| started_at / finished_at | timestamptz | |

### `attempt_answers` — Respuestas de cada intento
| Columna | Tipo | Notas |
|---------|------|-------|
| id | uuid (PK) | |
| attempt_id | uuid (FK → quiz_attempts) | |
| question_id | uuid (FK → questions) | |
| given_answer | text | Respuesta del estudiante |
| is_correct | boolean | |

### `activities` — Tareas, trabajos y exámenes
| Columna | Tipo | Notas |
|---------|------|-------|
| id | uuid (PK) | |
| subject_id | uuid (FK → subjects) | |
| user_id | uuid (FK → profiles) | |
| title | text | |
| due_date | timestamptz | Fecha límite |
| status | text | `pending` \| `in_progress` \| `done` |
| created_at / updated_at | timestamptz | |

### `chat_messages` — Historial del tutor virtual
| Columna | Tipo | Notas |
|---------|------|-------|
| id | uuid (PK) | |
| user_id | uuid (FK → profiles) | |
| subject_id | uuid (FK → subjects, null) | Contexto opcional |
| role | text | `user` \| `assistant` |
| content | text | |
| sources | jsonb | Fragmentos/páginas citadas (trazabilidad) |
| created_at | timestamptz | |

### `study_sessions` — Registro opcional de estudio
| Columna | Tipo | Notas |
|---------|------|-------|
| id | uuid (PK) | |
| user_id | uuid (FK → profiles) | |
| subject_id | uuid (FK → subjects) | |
| started_at | timestamptz | |
| duration_minutes | int | |

## Row Level Security

Todas las tablas con `user_id` activan RLS con una política base:

```sql
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id)
```

Esto garantiza que cada estudiante solo pueda ver y modificar sus propios registros, cumpliendo el requisito de privacidad de la propuesta (§14.1).

## Nota sobre escalado de versiones (v2)

Los módulos **EXPLORA PLUS** y **MIS NOTAS PLUS** añadirán tablas como `searches`, `academic_resources`, `learning_paths`, `notes` y `notebooks`. Se dejan documentadas pero fuera del esquema MVP.
