import { useEffect, useState } from 'react'
import { api, type Activity, type Subject } from '../lib/api'

const STATUS_LABEL: Record<Activity['status'], string> = {
  pending: 'Pendiente',
  in_progress: 'En progreso',
  done: 'Hecho',
}

const STATUS_STYLE: Record<Activity['status'], string> = {
  pending: 'bg-slate-100 text-slate-600',
  in_progress: 'bg-amber-100 text-amber-700',
  done: 'bg-green-100 text-green-700',
}

export default function PlannerPage() {
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [activities, setActivities] = useState<Activity[]>([])
  const [subjectId, setSubjectId] = useState('')
  const [title, setTitle] = useState('')
  const [dueDate, setDueDate] = useState('')

  const load = () => api.listActivities().then(setActivities).catch(() => {})
  useEffect(() => {
    api.listSubjects().then((s) => {
      setSubjects(s)
      if (s[0]) setSubjectId(s[0].id)
    })
    load()
  }, [])

  const subjectName = (id: string) => subjects.find((s) => s.id === id)?.name ?? '—'

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !subjectId) return
    await api.createActivity({
      subject_id: subjectId,
      title,
      due_date: dueDate ? new Date(dueDate).toISOString() : null,
    })
    setTitle('')
    setDueDate('')
    load()
  }

  const cycleStatus = async (a: Activity) => {
    const next: Activity['status'] =
      a.status === 'pending' ? 'in_progress' : a.status === 'in_progress' ? 'done' : 'pending'
    await api.updateActivity(a.id, { status: next })
    load()
  }

  const remove = async (id: string) => {
    await api.deleteActivity(id)
    load()
  }

  const isOverdue = (a: Activity) =>
    a.status !== 'done' && a.due_date && new Date(a.due_date) < new Date()

  return (
    <div>
      <h2 className="text-2xl font-bold mb-1">Planificador académico</h2>
      <p className="text-slate-500 mb-6">
        Organiza tus tareas, trabajos y exámenes con sus fechas límite.
      </p>

      <form onSubmit={handleCreate} className="bg-white rounded-xl shadow-sm p-5 mb-6 flex flex-wrap gap-3 items-center">
        <select
          className="border rounded-md px-3 py-2 text-sm"
          value={subjectId}
          onChange={(e) => setSubjectId(e.target.value)}
        >
          <option value="">Asignatura…</option>
          {subjects.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        <input
          className="flex-1 min-w-[200px] border rounded-md px-3 py-2 text-sm"
          placeholder="¿Qué tienes que hacer?"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <input
          type="date"
          className="border rounded-md px-3 py-2 text-sm"
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
        />
        <button className="bg-brand-light text-white px-4 py-2 rounded-md text-sm">
          Añadir
        </button>
      </form>

      <div className="bg-white rounded-xl shadow-sm p-5">
        {activities.length === 0 ? (
          <p className="text-sm text-slate-400">No tienes actividades registradas.</p>
        ) : (
          <ul className="divide-y">
            {activities.map((a) => (
              <li key={a.id} className="py-3 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className={`text-sm font-medium ${a.status === 'done' ? 'line-through text-slate-400' : ''}`}>
                    {a.title}
                  </p>
                  <p className="text-xs text-slate-400">
                    {subjectName(a.subject_id)}
                    {a.due_date && (
                      <span className={isOverdue(a) ? 'text-red-500 font-medium' : ''}>
                        {' · '}
                        {new Date(a.due_date).toLocaleDateString()}
                        {isOverdue(a) && ' (vencida)'}
                      </span>
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => cycleStatus(a)}
                    className={`px-2 py-0.5 rounded-full text-xs ${STATUS_STYLE[a.status]}`}
                    title="Cambiar estado"
                  >
                    {STATUS_LABEL[a.status]}
                  </button>
                  <button
                    onClick={() => remove(a.id)}
                    className="text-xs text-red-500 hover:underline"
                  >
                    Eliminar
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
