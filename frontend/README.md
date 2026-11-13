# Frontend — UNIVERSITY PLUS

SPA construida con **React + Vite + TypeScript + Tailwind CSS**.

## Requisitos

- Node.js 18+ (recomendado 20/22)

## Puesta en marcha

```bash
cd frontend
npm install
cp .env.example .env     # completar VITE_API_URL y, opcionalmente, Supabase
npm run dev
```

App en http://localhost:5173

## Modo de desarrollo sin Supabase

Si no defines `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY`, la app entra en
**modo desarrollo**: omite el login real y habla con el backend usando un token
de prueba (que el backend acepta cuando también está en modo dev). Ideal para
probar la UI contra el backend en mock.

## Estructura

```
src/
├── components/   # Layout y UI compartida
├── context/      # AuthContext (sesión Supabase)
├── lib/          # api.ts (cliente REST), supabase.ts
├── pages/        # Una página por módulo del MVP
│   ├── LoginPage.tsx
│   ├── DashboardPage.tsx       # Módulo 1: Panel
│   ├── SubjectsPage.tsx        # Asignaturas
│   ├── DocumentsPage.tsx       # Módulo 2: Biblioteca
│   ├── TutorPage.tsx           # Módulo 3: Tutor IA
│   └── QuizzesPage.tsx         # Módulo 4: Cuestionarios
├── App.tsx       # Routing
└── main.tsx      # Entry point
```

## Seguridad

- Solo usa la **anon key** pública de Supabase.
- El token de sesión se adjunta a cada petición al backend como `Bearer`.
- Ninguna clave secreta vive en el frontend.
