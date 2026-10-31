import { useState } from 'react'
import { api, type AcademicResource, type ExploreResult } from '../lib/api'

const STATUS_CYCLE: Record<AcademicResource['status'], AcademicResource['status']> = {
  pending: 'reviewing',
  reviewing: 'understood',
  understood: 'pending',
}

const STATUS_LABEL: Record<AcademicResource['status'], string> = {
  pending: 'Pendiente',
  reviewing: 'En revisión',
  understood: 'Comprendido',
}

const STATUS_STYLE: Record<AcademicResource['status'], string> = {
  pending: 'bg-slate-100 text-slate-600',
  reviewing: 'bg-amber-100 text-amber-700',
  understood: 'bg-green-100 text-green-700',
}

export default function ExplorePage() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<ExploreResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = async (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim().length < 2) return
    setBusy(true)
    setError(null)
    try {
      setResult(await api.exploreSearch(query.trim()))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error en la búsqueda')
    } finally {
      setBusy(false)
    }
  }

  // El índice del recurso dentro del array plano result.resources
  const cycleStatus = async (resource: AcademicResource) => {
    if (!result) return
    const index = result.resources.indexOf(resource)
    if (index < 0) return
    const next = STATUS_CYCLE[resource.status]
    const updated = await api.updateResourceStatus(result.id, index, next)
    setResult(updated)
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-1">Explora Plus</h2>
      <p className="text-slate-500 mb-6">
        De una duda a una ruta confiable de aprendizaje. Busca fuentes
        académicas y organízalas por pasos.
      </p>

      <form onSubmit={search} className="bg-white rounded-xl shadow-sm p-5 mb-6 flex gap-3">
        <input
          className="flex-1 border rounded-md px-3 py-2 text-sm"
          placeholder="Escribe un tema o pega una pregunta…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          disabled={busy}
          className="bg-brand-light text-white px-5 py-2 rounded-md text-sm disabled:opacity-50"
        >
          {busy ? 'Buscando…' : 'Explorar'}
        </button>
      </form>

      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      {result && result.resources.some((r) => r.is_example) && (
        <div className="mb-4 text-xs bg-amber-50 text-amber-800 border border-amber-200 rounded-md px-3 py-2">
          Resultados de ejemplo (modo demostración). Con las fuentes reales
          conectadas verás publicaciones verificables con su DOI.
        </div>
      )}

      {result && (
        <div className="space-y-6">
          {result.path.map((step) => (
            <div key={step.position} className="bg-white rounded-xl shadow-sm p-5">
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-brand text-white text-xs flex items-center justify-center">
                  {step.position}
                </span>
                {step.label}
              </h3>
              <ul className="space-y-3">
                {step.resources.map((r, i) => (
                  <li key={i} className="border rounded-lg p-3">
                    <div className="flex justify-between items-start gap-3">
                      <div className="min-w-0">
                        <p className="text-sm font-medium">
                          {r.resource_type === 'video' ? '🎬 ' : '📄 '}
                          {r.url ? (
                            <a href={r.url} target="_blank" rel="noreferrer" className="text-brand-light hover:underline">
                              {r.title}
                            </a>
                          ) : (
                            r.title
                          )}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          {r.authors.slice(0, 3).join(', ')}
                          {r.year && ` · ${r.year}`}
                          {r.venue && ` · ${r.venue}`}
                        </p>
                        <p className="text-xs text-slate-400 mt-1 flex gap-2 flex-wrap">
                          <span>Fuente: {r.source}</span>
                          {r.doi && <span>DOI: {r.doi}</span>}
                          {r.open_access && <span className="text-green-600">Acceso abierto</span>}
                        </p>
                      </div>
                      <button
                        onClick={() => cycleStatus(r)}
                        className={`shrink-0 px-2 py-0.5 rounded-full text-xs ${STATUS_STYLE[r.status]}`}
                        title="Cambiar estado"
                      >
                        {STATUS_LABEL[r.status]}
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
