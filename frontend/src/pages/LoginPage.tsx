import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { signIn, signUp, devMode } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (devMode) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <div className="max-w-md text-center space-y-4">
          <h1 className="text-2xl font-bold text-brand">UNIVERSITY PLUS</h1>
          <p className="text-slate-600">
            Supabase no está configurado, así que la app corre en{' '}
            <strong>modo desarrollo</strong> sin autenticación real.
          </p>
          <button
            onClick={() => navigate('/')}
            className="bg-brand-light text-white px-5 py-2 rounded-md"
          >
            Entrar al panel
          </button>
        </div>
      </div>
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      if (mode === 'login') await signIn(email, password)
      else await signUp(email, password, fullName)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error de autenticación')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="w-full max-w-sm bg-white rounded-xl shadow p-8">
        <h1 className="text-xl font-bold text-brand mb-1">UNIVERSITY PLUS</h1>
        <p className="text-sm text-slate-500 mb-6">
          {mode === 'login' ? 'Inicia sesión' : 'Crea tu cuenta'}
        </p>
        <form onSubmit={handleSubmit} className="space-y-3">
          {mode === 'signup' && (
            <input
              className="w-full border rounded-md px-3 py-2 text-sm"
              placeholder="Nombre completo"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
          )}
          <input
            className="w-full border rounded-md px-3 py-2 text-sm"
            type="email"
            placeholder="Correo"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            className="w-full border rounded-md px-3 py-2 text-sm"
            type="password"
            placeholder="Contraseña"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={busy}
            className="w-full bg-brand-light text-white py-2 rounded-md text-sm disabled:opacity-50"
          >
            {busy ? 'Procesando…' : mode === 'login' ? 'Entrar' : 'Registrarme'}
          </button>
        </form>
        <button
          onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}
          className="mt-4 text-sm text-brand-light hover:underline"
        >
          {mode === 'login'
            ? '¿No tienes cuenta? Regístrate'
            : '¿Ya tienes cuenta? Inicia sesión'}
        </button>
      </div>
    </div>
  )
}
