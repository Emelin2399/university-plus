import { useEffect, useRef, useState } from 'react'
import { api, type Attachment, type Note } from '../lib/api'

function formatSize(bytes?: number | null): string {
  if (!bytes && bytes !== 0) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function NotesPage() {
  const [notes, setNotes] = useState<Note[]>([])
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState<Note | null>(null)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [attachments, setAttachments] = useState<Attachment[]>([])
  const [uploading, setUploading] = useState(false)
  const [attachError, setAttachError] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const load = (q?: string) => api.listNotes(q ? { q } : undefined).then(setNotes).catch(() => {})
  useEffect(() => {
    load()
  }, [])

  const openNew = () => {
    setSelected(null)
    setTitle('')
    setContent('')
    setAttachments([])
    setAttachError('')
  }

  const openNote = (n: Note) => {
    setSelected(n)
    setTitle(n.title)
    setContent(n.content)
    setAttachments(n.attachments ?? [])
    setAttachError('')
  }

  const save = async () => {
    if (!title.trim()) return
    if (selected) {
      await api.updateNote(selected.id, { title, content })
    } else {
      const created = await api.createNote({ title, content })
      // Al crear, dejamos la nota abierta para poder adjuntar archivos.
      setSelected(created)
      setAttachments(created.attachments ?? [])
    }
    await load(query || undefined)
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

  const onPickFiles = async (fileList: FileList | null) => {
    if (!selected || !fileList || fileList.length === 0) return
    setUploading(true)
    setAttachError('')
    try {
      const created = await api.uploadNoteAttachments(selected.id, fileList)
      setAttachments((prev) => [...prev, ...created])
    } catch (e) {
      setAttachError(e instanceof Error ? e.message : 'No se pudieron subir los archivos')
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const removeAttachment = async (attachmentId: string) => {
    if (!selected) return
    await api.deleteNoteAttachment(selected.id, attachmentId)
    setAttachments((prev) => prev.filter((a) => a.id !== attachmentId))
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
                  <span className="truncate flex items-center gap-1">
                    {n.title}
                    {n.attachments && n.attachments.length > 0 && (
                      <span className="text-slate-400" title="Tiene adjuntos">
                        📎{n.attachments.length}
                      </span>
                    )}
                  </span>
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

          {/* Adjuntos: cualquier tipo de archivo, varios por nota */}
          <div className="mt-6 border-t pt-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-slate-700">
                Archivos adjuntos
              </h3>
              {selected && (
                <div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    className="hidden"
                    onChange={(e) => onPickFiles(e.target.files)}
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                    className="bg-brand-light text-white px-3 py-1.5 rounded-md text-sm disabled:opacity-50"
                  >
                    {uploading ? 'Subiendo…' : '+ Adjuntar archivos'}
                  </button>
                </div>
              )}
            </div>

            {!selected ? (
              <p className="text-sm text-slate-400">
                Guarda la nota para poder adjuntar archivos.
              </p>
            ) : attachments.length === 0 ? (
              <p className="text-sm text-slate-400">Sin archivos adjuntos.</p>
            ) : (
              <ul className="space-y-1">
                {attachments.map((a) => (
                  <li
                    key={a.id}
                    className="flex items-center justify-between text-sm border rounded-md px-3 py-2"
                  >
                    <span className="truncate">
                      {a.url ? (
                        <a
                          href={a.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-brand hover:underline"
                        >
                          📎 {a.name}
                        </a>
                      ) : (
                        <span>📎 {a.name}</span>
                      )}
                      {a.size_bytes != null && (
                        <span className="text-slate-400 ml-2">
                          {formatSize(a.size_bytes)}
                        </span>
                      )}
                    </span>
                    <button
                      onClick={() => removeAttachment(a.id)}
                      className="text-red-500 hover:underline ml-3"
                    >
                      Eliminar
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {attachError && (
              <p className="text-sm text-red-500 mt-2">{attachError}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
