# ⚡ Quick Start — UNIVERSITY PLUS

Guía rápida para poner en marcha el proyecto en **tu máquina** con Supabase y
OpenAI reales. Sigue los pasos en orden.

> 📋 **Requisitos previos:** Python 3.11+, Node.js 18+, una cuenta de
> [Supabase](https://supabase.com/) y (opcional) una API key de
> [OpenAI](https://platform.openai.com/).

---

## Paso 1 · Clonar el repositorio

```bash
git clone https://github.com/Emelin2399/university-plus.git
cd university-plus
```

## Paso 2 · Preparar Supabase

Sigue la guía detallada en [`database/SUPABASE_SETUP.md`](database/SUPABASE_SETUP.md). En resumen:

1. Crea un proyecto en Supabase.
2. En **SQL Editor**, ejecuta todo [`database/schema.sql`](database/schema.sql).
3. En **Storage**, crea un bucket privado llamado `documents`.
4. Copia de **Project Settings → API**: la URL, la `anon` key y la `service_role` key.

## Paso 3 · Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
#  → edita .env con tus credenciales de Supabase (y OpenAI si la usarás)
```

Ejemplo de `.env` mínimo para producción:

```env
APP_ENV=production
CORS_ORIGINS=http://localhost:5173
SUPABASE_URL=https://TU-PROYECTO.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_STORAGE_BUCKET=documents
AI_PROVIDER=mock          # cámbialo a openai cuando tengas la key
# OPENAI_API_KEY=sk-...
```

### Verifica que todo está bien configurado

```bash
python scripts/check_setup.py
```

Debe mostrar ✓ en SUPABASE_URL, la conexión, y la función RPC del RAG.

### Arranca el backend

```bash
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Salud: http://localhost:8000/health → `"supabase_configured": true`

## Paso 4 · Probar el flujo completo (smoke test)

Con el backend arrancado, en **otra terminal**:

```bash
cd backend && source .venv/bin/activate
python scripts/smoke_test.py
```

> Con Supabase activo necesitas un token de usuario real:
> `python scripts/smoke_test.py --token <ACCESS_TOKEN>`
> (obtén el token iniciando sesión desde el frontend y copiándolo de la sesión de Supabase).

## Paso 5 · Frontend

```bash
cd frontend
npm install

cp .env.example .env
#  → edita con VITE_API_URL y las claves PÚBLICAS de Supabase
npm run dev
```

App en http://localhost:5173

## Paso 6 · Activar la IA real (OpenAI)

Cuando quieras pasar del modo mock a respuestas reales:

1. En `backend/.env`:
   ```env
   AI_PROVIDER=openai
   OPENAI_API_KEY=sk-...
   OPENAI_CHAT_MODEL=gpt-4o-mini
   OPENAI_EMBEDDING_MODEL=text-embedding-3-small
   ```
2. Reinicia el backend.
3. Verifica con `python scripts/check_setup.py` (debe reconocer la key).

> ⚠️ **Importante sobre embeddings:** si ya subiste documentos en modo mock,
> sus embeddings NO son compatibles con los de OpenAI. Vuelve a subir los
> documentos tras activar OpenAI para regenerar los embeddings reales.

---

## 🆘 Si algo falla

1. Ejecuta `python scripts/check_setup.py` y lee los mensajes.
2. Revisa la tabla de solución de problemas en [`database/SUPABASE_SETUP.md`](database/SUPABASE_SETUP.md).
3. Copia el error completo y compártelo para depurarlo.
