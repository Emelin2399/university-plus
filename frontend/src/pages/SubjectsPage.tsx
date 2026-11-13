import { useEffect, useState } from 'react'
import { api, type Subject } from '../lib/api'

export default function SubjectsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [name, setName] = useState('')
  const [term, setTerm] = useState('')

  const load = () => api.listSubjects().then(setSubjects).catch(() => {})
  useEffect(() => {
    load()
  }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return
    await api.createSubject({ name, term: term || undefined })
    setName('')
    setTerm('')
    load()
  }

  const handleDelete = async (id: string) => {
    await api.deleteSubject(id)
    load()
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-1">Asignaturas</h2>
      <p className="text-slate-500 mb-6">Organiza tus materias por periodo.</p>

      <form onSubmit={handleCreate} className="bg-white rounded-xl shadow-sm p-5 mb-6 flex gap-3">
        <input
          className="flex-1 border rounded-md px-3 py-2 text-sm"
          placeholder="Nombre de la asignatura"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          className="w-32 border rounded-md px-3 py-2 text-sm"
          placeholder="Periodo"
          value={term}
          onChange={(e) => setTerm(e.target.value)}
        />
        <button className="bg-brand-light text-white px-4 py-2 rounded-md text-sm">
          Añadir
        </button>
      </form>

      <div className="grid grid-cols-2 gap-4">
        {subjects.map((s) => (
          <div key={s.id} className="bg-white rounded-xl shadow-sm p-4 flex justify-between items-center">
            <div className="flex items-center gap-3">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: s.color ?? '#2563eb' }} />
              <div>
                <p className="font-medium">{s.name}</p>
                {s.term && <p className="text-xs text-slate-400">{s.term}</p>}
              </div>
            </div>
            <button
              onClick={() => handleDelete(s.id)}
              className="text-xs text-red-500 hover:underline"
            >
              Eliminar
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
