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
  // Referencia al área editable (editor de texto enriquecido).
  const editorRef = useRef<HTMLDivElement>(null)

  const load = (q?: string) => api.listNotes(q ? { q } : undefined).then(setNotes).catch(() => {})
  useEffect(() => {
    load()
  }, [])

  // Carga el HTML guardado dentro del área editable cuando cambia la nota.
  // Lo hacemos de forma imperativa para que el cursor del usuario no se
  // reinicie en cada pulsación de tecla (el div no es controlado por React).
  const syncEditor = (html: string) => {
    setContent(html)
    if (editorRef.current) editorRef.current.innerHTML = html
  }

  const openNew = () => {
    setSelected(null)
    setTitle('')
    syncEditor('')
    setAttachments([])
    setAttachError('')
  }

  const openNote = (n: Note) => {
    setSelected(n)
    setTitle(n.title)
    syncEditor(n.content ?? '')
    setAttachments(n.attachments ?? [])
    setAttachError('')
  }

  const save = async () => {
    if (!title.trim()) return
    // El contenido se guarda como HTML (texto enriquecido) en el campo content.
    const html = editorRef.current?.innerHTML ?? content
    if (selected) {
      await api.updateNote(selected.id, { title, content: html })
    } else {
      const created = await api.createNote({ title, content: html })
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

  // --- Editor de texto enriquecido (contentEditable + document.execCommand) ---
  // Nota: document.execCommand está marcado como obsoleto, pero sigue
  // funcionando en todos los navegadores actuales y NO requiere instalar
  // ninguna dependencia nueva. Así la actualización de la app es más sencilla.
  const exec = (command: string, value?: string) => {
    // Mantiene el foco en el editor para que el formato se aplique a la selección.
    editorRef.current?.focus()
    document.execCommand(command, false, value)
    // Guardamos el HTML actualizado en el estado.
    if (editorRef.current) setContent(editorRef.current.innerHTML)
  }

  const onEditorInput = () => {
    if (editorRef.current) setContent(editorRef.current.innerHTML)
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
      {/* Estilos para que las listas y el contenido enriquecido se vean bien
          dentro del editor (Tailwind Preflight quita los marcadores por defecto). */}
      <style>{`
        .nota-editor ul { list-style: disc; padding-left: 1.5rem; margin: 0.25rem 0; }
        .nota-editor ol { list-style: decimal; padding-left: 1.5rem; margin: 0.25rem 0; }
        .nota-editor:empty:before { content: attr(data-placeholder); color: #94a3b8; }
        .nota-editor:focus { outline: none; }
      `}</style>

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

          {/* Barra de herramientas de formato */}
          <div className="flex flex-wrap items-center gap-1.5 border rounded-md px-2 py-2 mb-2 bg-slate-50">
            <button
              type="button"
              onClick={() => exec('bold')}
              title="Negrita"
              aria-label="Negrita"
              className="w-8 h-8 rounded-md hover:bg-slate-200 font-bold text-sm"
            >
              N
            </button>
            <button
              type="button"
              onClick={() => exec('italic')}
              title="Cursiva"
              aria-label="Cursiva"
              className="w-8 h-8 rounded-md hover:bg-slate-200 italic text-sm"
            >
              K
            </button>
            <button
              type="button"
              onClick={() => exec('underline')}
              title="Subrayado"
              aria-label="Subrayado"
              className="w-8 h-8 rounded-md hover:bg-slate-200 underline text-sm"
            >
              S
            </button>

            <span className="w-px h-6 bg-slate-300 mx-1" />

            {/* Tamaño de texto / encabezado */}
            <label className="flex items-center gap-1 text-sm text-slate-600">
              Tamaño
              <select
                onChange={(e) => {
                  if (e.target.value) exec('formatBlock', e.target.value)
                  e.target.selectedIndex = 0
                }}
                title="Tamaño del texto"
                aria-label="Tamaño del texto"
                className="border rounded-md px-1.5 py-1 text-sm bg-white"
                defaultValue=""
              >
                <option value="">Normal</option>
                <option value="H1">Título grande</option>
                <option value="H2">Título mediano</option>
                <option value="H3">Título pequeño</option>
                <option value="P">Párrafo</option>
              </select>
            </label>

            <span className="w-px h-6 bg-slate-300 mx-1" />

            {/* Color de fuente */}
            <label className="flex items-center gap-1 text-sm text-slate-600" title="Color del texto">
              Color
              <input
                type="color"
                defaultValue="#0f172a"
                aria-label="Color del texto"
                onChange={(e) => exec('foreColor', e.target.value)}
                className="w-8 h-8 p-0 border rounded-md cursor-pointer bg-white"
              />
            </label>

            {/* Resaltado */}
            <label className="flex items-center gap-1 text-sm text-slate-600" title="Color de resaltado">
              Resaltar
              <input
                type="color"
                defaultValue="#fde047"
                aria-label="Color de resaltado"
                onChange={(e) => exec('hiliteColor', e.target.value)}
                className="w-8 h-8 p-0 border rounded-md cursor-pointer bg-white"
              />
            </label>

            <span className="w-px h-6 bg-slate-300 mx-1" />

            {/* Listas */}
            <button
              type="button"
              onClick={() => exec('insertUnorderedList')}
              title="Lista con viñetas"
              aria-label="Lista con viñetas"
              className="w-8 h-8 rounded-md hover:bg-slate-200 text-sm"
            >
              • —
            </button>
            <button
              type="button"
              onClick={() => exec('insertOrderedList')}
              title="Lista numerada"
              aria-label="Lista numerada"
              className="w-8 h-8 rounded-md hover:bg-slate-200 text-sm"
            >
              1.
            </button>

            <span className="w-px h-6 bg-slate-300 mx-1" />

            {/* Quitar formato */}
            <button
              type="button"
              onClick={() => exec('removeFormat')}
              title="Quitar formato"
              aria-label="Quitar formato"
              className="px-2 h-8 rounded-md hover:bg-slate-200 text-sm text-slate-600"
            >
              Limpiar
            </button>
          </div>

          {/* Área editable: el contenido se guarda como HTML en `content`. */}
          <div
            ref={editorRef}
            className="nota-editor w-full h-72 border rounded-md p-3 text-sm overflow-auto"
            contentEditable
            suppressContentEditableWarning
            role="textbox"
            aria-multiline="true"
            aria-label="Contenido de la nota"
            data-placeholder="Escribe tus apuntes aquí…"
            onInput={onEditorInput}
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
