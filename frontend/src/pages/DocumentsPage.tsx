import { useEffect, useRef, useState } from 'react'
import { api, type DocumentItem, type Subject } from '../lib/api'

type Tab = 'file' | 'link'

export default function DocumentsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [selected, setSelected] = useState('')
  const [tab, setTab] = useState<Tab>('file')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [url, setUrl] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  const loadDocs = () => api.listDocuments().then(setDocuments).catch(() => {})
  useEffect(() => {
    api.listSubjects().then((s) => {
      setSubjects(s)
      if (s[0]) setSelected(s[0].id)
    })
    loadDocs()
  }, [])

  const handleUploadFile = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    const file = fileRef.current?.files?.[0]
    if (!file || !selected) return
    setBusy(true)
    try {
      await api.uploadDocument(selected, file)
      if (fileRef.current) fileRef.current.value = ''
      loadDocs()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al subir')
    } finally {
      setBusy(false)
    }
  }

  const handleAddLink = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!url.trim() || !selected) return
    setBusy(true)
    try {
      await api.addDocumentFromUrl({ subject_id: selected, url: url.trim() })
      setUrl('')
      loadDocs()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al agregar el enlace')
    } finally {
      setBusy(false)
    }
  }

  const handleDelete = async (id: string) => {
    await api.deleteDocument(id)
    loadDocs()
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-1">Biblioteca inteligente</h2>
      <p className="text-slate-500 mb-6">
        Añade material desde un archivo PDF o desde un enlace (PDF o página web).
        Se preparará para el tutor IA.
      </p>

      <div className="bg-white rounded-xl shadow-sm p-5 mb-6">
        <div className="flex items-center gap-4 mb-4">
          <select
            className="border rounded-md px-3 py-2 text-sm"
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
          >
            <option value="">Elige asignatura…</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>

          <div className="flex rounded-md overflow-hidden border text-sm">
            <button
              type="button"
              onClick={() => setTab('file')}
              className={`px-4 py-2 ${tab === 'file' ? 'bg-brand-light text-white' : 'bg-white text-slate-600'}`}
            >
              📄 Archivo
            </button>
            <button
              type="button"
              onClick={() => setTab('link')}
              className={`px-4 py-2 ${tab === 'link' ? 'bg-brand-light text-white' : 'bg-white text-slate-600'}`}
            >
              🔗 Enlace
            </button>
          </div>
        </div>

        {tab === 'file' ? (
          <form onSubmit={handleUploadFile} className="flex gap-3 items-center">
            <input
              ref={fileRef}
              type="file"
              accept="application/pdf"
              className="text-sm flex-1"
            />
            <button
              disabled={busy || !selected}
              className="bg-brand-light text-white px-4 py-2 rounded-md text-sm disabled:opacity-50"
            >
              {busy ? 'Procesando…' : 'Subir PDF'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleAddLink} className="flex gap-3 items-center">
            <input
              type="url"
              placeholder="https://ejemplo.com/articulo o .../apunte.pdf"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="flex-1 border rounded-md px-3 py-2 text-sm"
            />
            <button
              disabled={busy || !selected}
              className="bg-brand-light text-white px-4 py-2 rounded-md text-sm disabled:opacity-50"
            >
              {busy ? 'Procesando…' : 'Agregar enlace'}
            </button>
          </form>
        )}

        {error && <p className="text-sm text-red-600 mt-3">{error}</p>}
      </div>

      <div className="bg-white rounded-xl shadow-sm p-5">
        {documents.length === 0 ? (
          <p className="text-sm text-slate-400">Aún no has añadido documentos.</p>
        ) : (
          <ul className="divide-y">
            {documents.map((d) => (
              <li key={d.id} className="py-3 flex justify-between items-center text-sm">
                <span className="flex items-center gap-2">
                  <span>{d.source_type === 'link' ? '🔗' : '📄'}</span>
                  {d.source_url ? (
                    <a
                      href={d.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-brand-light hover:underline"
                    >
                      {d.name}
                    </a>
                  ) : (
                    <span>{d.name}</span>
                  )}
                </span>
                <span className="flex items-center gap-3 text-xs text-slate-400">
                  {d.page_count ? `${d.page_count} págs.` : ''}
                  <StatusBadge status={d.status} />
                  <button
                    onClick={() => handleDelete(d.id)}
                    className="text-red-500 hover:underline"
                  >
                    Eliminar
                  </button>
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    ready: 'bg-green-100 text-green-700',
    processing: 'bg-amber-100 text-amber-700',
    pending: 'bg-slate-100 text-slate-600',
    error: 'bg-red-100 text-red-700',
  }
  return <span className={`px-2 py-0.5 rounded-full ${map[status] ?? ''}`}>{status}</span>
}
