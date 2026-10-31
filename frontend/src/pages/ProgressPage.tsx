import { useEffect, useState } from 'react'
import { api, type ProgressReport } from '../lib/api'

export default function ProgressPage() {
  const [report, setReport] = useState<ProgressReport | null>(null)

  useEffect(() => {
    api.getProgress().then(setReport).catch(() => {})
  }, [])

  if (!report) return <div className="text-sm text-slate-400">Cargando…</div>

  const { summary, by_subject, evolution, to_reinforce } = report
  const hasData = summary.total_attempts > 0

  return (
    <div>
      <h2 className="text-2xl font-bold mb-1">Seguimiento del aprendizaje</h2>
      <p className="text-slate-500 mb-6">
        Tu avance a partir de los cuestionarios resueltos.
      </p>

      {!hasData ? (
        <div className="bg-white rounded-xl shadow-sm p-8 text-center text-sm text-slate-400">
          Aún no tienes resultados. Resuelve cuestionarios en la sección
          «Cuestionarios» para ver aquí tu progreso.
        </div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-4 mb-8">
            <Card label="Cuestionarios resueltos" value={summary.total_attempts} />
            <Card label="Promedio general" value={`${summary.average_score}%`} />
            <Card label="Mejor resultado" value={`${summary.best_score}%`} />
          </div>

          <div className="grid grid-cols-2 gap-4 mb-8">
            {/* Progreso por asignatura */}
            <div className="bg-white rounded-xl shadow-sm p-5">
              <h3 className="font-semibold mb-4">Progreso por asignatura</h3>
              <ul className="space-y-3">
                {by_subject.map((s) => (
                  <li key={s.subject_id ?? s.subject_name}>
                    <div className="flex justify-between text-sm mb-1">
                      <span>{s.subject_name}</span>
                      <span className="text-slate-500">{s.average_score}%</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${s.average_score}%`,
                          backgroundColor:
                            s.average_score < 60
                              ? '#ef4444'
                              : s.average_score < 80
                                ? '#f59e0b'
                                : '#22c55e',
                        }}
                      />
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            {/* Evolución */}
            <div className="bg-white rounded-xl shadow-sm p-5">
              <h3 className="font-semibold mb-4">Evolución</h3>
              <EvolutionChart points={evolution.map((e) => e.score)} />
            </div>
          </div>

          {/* Temas por reforzar */}
          <div className="bg-white rounded-xl shadow-sm p-5">
            <h3 className="font-semibold mb-3">Temas por reforzar</h3>
            {to_reinforce.length === 0 ? (
              <p className="text-sm text-green-600">
                ¡Bien! No hay temas por debajo del umbral de refuerzo. 🎉
              </p>
            ) : (
              <ul className="space-y-2">
                {to_reinforce.map((t) => (
                  <li
                    key={t.quiz_id ?? t.quiz_title}
                    className="flex justify-between items-center text-sm"
                  >
                    <span>{t.quiz_title}</span>
                    <span className="px-2 py-0.5 rounded-full bg-red-100 text-red-700 text-xs">
                      {t.score}%
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  )
}

function Card({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-5">
      <p className="text-3xl font-bold text-brand">{value}</p>
      <p className="text-sm text-slate-500">{label}</p>
    </div>
  )
}

/** Mini gráfico de líneas en SVG, sin dependencias externas. */
function EvolutionChart({ points }: { points: number[] }) {
  if (points.length === 0) return <p className="text-sm text-slate-400">Sin datos.</p>
  if (points.length === 1) {
    return (
      <p className="text-sm text-slate-600">
        Un solo intento: <strong>{points[0]}%</strong>. Resuelve más para ver la
        tendencia.
      </p>
    )
  }

  const w = 320
  const h = 120
  const pad = 10
  const max = 100
  const step = (w - pad * 2) / (points.length - 1)
  const coords = points.map((p, i) => {
    const x = pad + i * step
    const y = h - pad - (p / max) * (h - pad * 2)
    return [x, y] as const
  })
  const path = coords.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x},${y}`).join(' ')

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-32">
      <line x1={pad} y1={h - pad} x2={w - pad} y2={h - pad} stroke="#e2e8f0" />
      <path d={path} fill="none" stroke="#2563eb" strokeWidth="2" />
      {coords.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r="3" fill="#2563eb" />
      ))}
    </svg>
  )
}
