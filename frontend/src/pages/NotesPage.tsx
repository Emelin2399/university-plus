import { useEffect, useState } from 'react'
import { api, type Note } from '../lib/api'

export default function NotesPage() {
  const [notes, setNotes] = useState<Note[]>([])
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState<Note | null>(null)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')

  const load = (q?: string) => api.listNotes(q ? { q } : undefined).then(setNotes).catch(() => {})
  useEffect(() => {
    load()
  }, [])

  const openNew = () => {
    setSelected(null)
    setTitle('')
    setContent('')
  }

  const openNote = (n: Note) => {
    setSelected(n)
    setTitle(n.title)
    setContent(n.content)
  }

  const save = async () => {
    if (!title.trim()) return
    if (selected) {
      await api.updateNote(selected.id, { title, content })
    } else {
      await api.createNote({ title, content })
    }
    await load(query || undefined)
    openNew()
  }

  const remove = async (id: string) => {
    await api.deleteNote(id)
    if (selected?.id === id) openNew()
    load(query || undefined)
  }

  const toggleFav = async (n: Note) => {
    await api.updateNote(n.id, { is_favorite: !n.is_favorite })
    load(query || undefined)
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-1">Mis Notas Plus</h2>
      <p className="text-slate-500 mb-6">Tu cuaderno digital de apuntes.</p>

      <div className="grid grid-cols-3 gap-4">
        {/* Lista */}
        <div className="col-span-1 bg-white rounded-xl shadow-sm p-4">
          <div className="flex gap-2 mb-3">
            <input
              className="flex-1 border rounded-md px-3 py-1.5 text-sm"
              placeholder="Buscar…"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value)
                load(e.target.value || undefined)
              }}
            />
            <button
              onClick={openNew}
              className="bg-brand-light text-white px-3 py-1.5 rounded-md text-sm"
            >
              + Nueva
            </button>
          </div>
          {notes.length === 0 ? (
            <p className="text-sm text-slate-400 py-4 text-center">Sin notas.</p>
          ) : (
            <ul className="space-y-1 max-h-[60vh] overflow-auto">
              {notes.map((n) => (
                <li
                  key={n.id}
                  className={`px-3 py-2 rounded-md cursor-pointer text-sm flex justify-between items-center ${
                    selected?.id === n.id ? 'bg-slate-100' : 'hover:bg-slate-50'
                  }`}
                  onClick={() => openNote(n)}
                >
                  <span className="truncate">{n.title}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      toggleFav(n)
                    }}
                    title="Favorita"
                  >
                    {n.is_favorite ? '⭐' : '☆'}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Editor */}
        <div className="col-span-2 bg-white rounded-xl shadow-sm p-5">
          <input
            className="w-full text-lg font-semibold border-b pb-2 mb-3 outline-none"
            placeholder="Título de la nota"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <textarea
            className="w-full h-72 border rounded-md p-3 text-sm outline-none resize-none"
            placeholder="Escribe tus apuntes aquí…"
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
          <div className="flex justify-between items-center mt-3">
            <button
              onClick={save}
              className="bg-brand text-white px-5 py-2 rounded-md text-sm"
            >
              {selected ? 'Guardar cambios' : 'Crear nota'}
            </button>
            {selected && (
              <button
                onClick={() => remove(selected.id)}
                className="text-sm text-red-500 hover:underline"
              >
                Eliminar nota
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
