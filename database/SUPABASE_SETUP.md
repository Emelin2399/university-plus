# 🔌 Guía de conexión con Supabase

Pasos para conectar UNIVERSITY PLUS a un proyecto real de Supabase. Al terminar,
el backend persistirá datos de verdad (tablas, archivos y búsqueda vectorial)
sin cambiar nada del código: solo variables de entorno.

---

## 1. Crear el proyecto en Supabase

1. Entra a [supabase.com](https://supabase.com/) y crea una cuenta (gratis).
2. **New project** → elige nombre, contraseña de base de datos y región cercana.
3. Espera a que el proyecto termine de aprovisionarse (~2 min).

## 2. Ejecutar el esquema

1. En el panel de Supabase, abre **SQL Editor**.
2. Crea una nueva query, pega **todo** el contenido de [`schema.sql`](schema.sql) y ejecútalo (**Run**).
3. Verifica en **Table Editor** que aparecen las tablas (`profiles`, `subjects`, `documents`, `document_chunks`, etc.).

> El script activa las extensiones `pgcrypto` y `vector`, crea las tablas, los
> índices (incluido el vectorial IVFFlat), la función `match_document_chunks`,
> los triggers y todas las políticas de **Row Level Security**.

### Nota sobre pgvector y la dimensión de embeddings

El esquema usa `vector(1536)`, que coincide con:
- El modo **mock** del backend (embeddings de dimensión 1536).
- El modelo `text-embedding-3-small` de OpenAI (1536).

Si cambias a un modelo con otra dimensión, ajusta el tipo `vector(N)` en
`document_chunks.embedding` y la firma de `match_document_chunks`.

## 3. Crear el bucket de Storage

1. Ve a **Storage** → **New bucket**.
2. Nombre: `documents` (debe coincidir con `SUPABASE_STORAGE_BUCKET`).
3. Déjalo **privado** (no público).
4. (Recomendado) Añade políticas de acceso por propietario para que cada
   usuario solo acceda a los archivos bajo su prefijo `{user_id}/...`:

```sql
-- Lectura de archivos propios
create policy "read own files"
on storage.objects for select
using ( bucket_id = 'documents' and (storage.foldername(name))[1] = auth.uid()::text );

-- Subida a su propia carpeta
create policy "upload own files"
on storage.objects for insert
with check ( bucket_id = 'documents' and (storage.foldername(name))[1] = auth.uid()::text );
```

> El backend sube los archivos con la service key (que omite RLS), pero estas
> políticas protegen el acceso directo desde el cliente.

## 4. Obtener las credenciales

En **Project Settings → API**:

| Variable (.env del backend) | De dónde sale |
|-----------------------------|---------------|
| `SUPABASE_URL` | Project URL |
| `SUPABASE_ANON_KEY` | `anon` `public` key |
| `SUPABASE_SERVICE_KEY` | `service_role` key ⚠️ **SECRETA** |

Para el **frontend** (`frontend/.env`):

| Variable | Valor |
|----------|-------|
| `VITE_SUPABASE_URL` | mismo Project URL |
| `VITE_SUPABASE_ANON_KEY` | misma `anon` key (pública) |

> ⚠️ **Nunca** pongas la `service_role` key en el frontend ni la subas al repo.

## 5. Configurar el backend

```bash
cd backend
cp .env.example .env
```

Edita `.env`:

```env
APP_ENV=production
CORS_ORIGINS=http://localhost:5173

SUPABASE_URL=https://TU-PROYECTO.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_STORAGE_BUCKET=documents

# IA: empieza en mock; cambia a openai cuando tengas la key
AI_PROVIDER=mock
# AI_PROVIDER=openai
# OPENAI_API_KEY=sk-...
```

En cuanto `SUPABASE_URL` y `SUPABASE_SERVICE_KEY` estén definidos, el backend
usa automáticamente el repositorio de Supabase.

## 6. Configurar el frontend

```bash
cd frontend
cp .env.example .env
```

```env
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://TU-PROYECTO.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
```

## 7. Probar la conexión

```bash
# Terminal 1 — backend
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2 — frontend
cd frontend && npm run dev
```

1. Abre http://localhost:8000/health → debe mostrar `"supabase_configured": true`.
2. Regístrate desde el frontend; revisa que aparezca una fila en la tabla `profiles`.
3. Crea una asignatura, sube un PDF y verifica en **Table Editor** que se crean
   filas en `subjects`, `documents` y `document_chunks`.

## 8. (Opcional) Activar la IA real

1. Consigue una API key en [platform.openai.com](https://platform.openai.com/).
2. En `backend/.env`: `AI_PROVIDER=openai` y `OPENAI_API_KEY=sk-...`.
3. Reinicia el backend.

> Para controlar costos, ajusta `MAX_UPLOAD_MB`, `MAX_DOCUMENTS_PER_USER` y
> considera limitar las consultas por usuario.

---

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| `/health` muestra `supabase_configured: false` | Faltan variables | Revisa `SUPABASE_URL` y `SUPABASE_SERVICE_KEY` en `.env` |
| Error `function match_document_chunks does not exist` | No se corrió el esquema | Ejecuta `schema.sql` completo |
| Error al subir archivo | Bucket inexistente o nombre distinto | Crea el bucket `documents` |
| `new row violates row-level security` | Token de usuario inválido | Verifica el login y el header `Authorization` |
