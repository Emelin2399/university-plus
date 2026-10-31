import { useEffect, useState } from 'react'
import { api, type Subject, type DocumentItem, type Activity } from '../lib/api'

export default function DashboardPage() {
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [activities, setActivities] = useState<Activity[]>([])

  useEffect(() => {
    api.listSubjects().then(setSubjects).catch(() => {})
    api.listDocuments().then(setDocuments).catch(() => {})
    api.listActivities({ status: 'pending' }).then(setActivities).catch(() => {})
  }, [])

  const cards = [
    { label: 'Asignaturas', value: subjects.length },
    { label: 'Documentos', value: documents.length },
    { label: 'Tareas pendientes', value: activities.length },
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold mb-1">Panel principal</h2>
      <p className="text-slate-500 mb-6">Resumen de tu actividad académica.</p>

      <div className="grid grid-cols-3 gap-4 mb-8">
        {cards.map((c) => (
          <div key={c.label} className="bg-white rounded-xl shadow-sm p-5">
            <p className="text-3xl font-bold text-brand">{c.value}</p>
            <p className="text-sm text-slate-500">{c.label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-xl shadow-sm p-5">
          <h3 className="font-semibold mb-3">Tus asignaturas</h3>
          {subjects.length === 0 ? (
            <p className="text-sm text-slate-400">
              Aún no tienes asignaturas. Crea una en la sección «Asignaturas».
            </p>
          ) : (
            <ul className="space-y-2">
              {subjects.map((s) => (
                <li key={s.id} className="flex items-center gap-2 text-sm">
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: s.color ?? '#2563eb' }}
                  />
                  {s.name}
                  {s.term && <span className="text-slate-400">· {s.term}</span>}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-sm p-5">
          <h3 className="font-semibold mb-3">Próximas tareas</h3>
          {activities.length === 0 ? (
            <p className="text-sm text-slate-400">
              Sin tareas pendientes. Agrégalas en el «Planificador».
            </p>
          ) : (
            <ul className="space-y-2">
              {activities.slice(0, 5).map((a) => (
                <li key={a.id} className="flex items-center justify-between text-sm">
                  <span className="truncate">{a.title}</span>
                  {a.due_date && (
                    <span className="text-xs text-slate-400 shrink-0 ml-2">
                      {new Date(a.due_date).toLocaleDateString()}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
