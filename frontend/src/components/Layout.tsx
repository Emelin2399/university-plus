import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { to: '/', label: 'Panel', end: true },
  { to: '/subjects', label: 'Asignaturas' },
  { to: '/documents', label: 'Biblioteca' },
  { to: '/tutor', label: 'Tutor IA' },
  { to: '/quizzes', label: 'Cuestionarios' },
  { to: '/planner', label: 'Planificador' },
  { to: '/progress', label: 'Mi Progreso' },
  { to: '/notes', label: 'Mis Notas' },
]

export default function Layout() {
  const { signOut, devMode } = useAuth()
  return (
    <div className="min-h-screen flex">
      <aside className="w-60 bg-brand text-white flex flex-col">
        <div className="p-5 border-b border-white/10">
          <h1 className="text-lg font-bold">UNIVERSITY PLUS</h1>
          <p className="text-xs text-white/60">Aprende mejor</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-md text-sm transition ${
                  isActive ? 'bg-white/15 font-medium' : 'hover:bg-white/10'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-white/10">
          {devMode && (
            <p className="text-[10px] text-amber-300 mb-2">Modo desarrollo (sin Supabase)</p>
          )}
          <button
            onClick={signOut}
            className="w-full text-left px-3 py-2 text-sm rounded-md hover:bg-white/10"
          >
            Cerrar sesión
          </button>
        </div>
      </aside>
      <main className="flex-1 p-8 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
