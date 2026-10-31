import { useEffect, useRef, useState } from 'react'
import { api, type DocumentItem, type Subject } from '../lib/api'

export default function DocumentsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [selected, setSelected] = useState('')
  const [uploading, setUploading] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const loadDocs = () => api.listDocuments().then(setDocuments).catch(() => {})
  useEffect(() => {
    api.listSubjects().then((s) => {
      setSubjects(s)
      if (s[0]) setSelected(s[0].id)
    })
    loadDocs()
  }, [])

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    const file = fileRef.current?.files?.[0]
    if (!file || !selected) return
    setUploading(true)
    try {
      await api.uploadDocument(selected, file)
      if (fileRef.current) fileRef.current.value = ''
      loadDocs()
    } finally {
      setUploading(false)
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-1">Biblioteca inteligente</h2>
      <p className="text-slate-500 mb-6">Sube PDFs y se prepararán para el tutor IA.</p>

      <form onSubmit={handleUpload} className="bg-white rounded-xl shadow-sm p-5 mb-6 flex gap-3 items-center">
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
        <input ref={fileRef} type="file" accept="application/pdf" className="text-sm flex-1" />
        <button
          disabled={uploading || !selected}
          className="bg-brand-light text-white px-4 py-2 rounded-md text-sm disabled:opacity-50"
        >
          {uploading ? 'Procesando…' : 'Subir'}
        </button>
      </form>

      <div className="bg-white rounded-xl shadow-sm p-5">
        {documents.length === 0 ? (
          <p className="text-sm text-slate-400">Aún no has subido documentos.</p>
        ) : (
          <ul className="divide-y">
            {documents.map((d) => (
              <li key={d.id} className="py-3 flex justify-between items-center text-sm">
                <span>{d.name}</span>
                <span className="flex items-center gap-3 text-xs text-slate-400">
                  {d.page_count ? `${d.page_count} págs.` : ''}
                  <StatusBadge status={d.status} />
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
  return (
    <span className={`px-2 py-0.5 rounded-full ${map[status] ?? ''}`}>{status}</span>
  )
}
