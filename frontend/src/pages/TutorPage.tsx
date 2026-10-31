import { useState } from 'react'
import { api, type TutorAnswer } from '../lib/api'

interface Msg {
  role: 'user' | 'assistant'
  content: string
  sources?: TutorAnswer['sources']
}

export default function TutorPage() {
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)

  const send = async (e: React.FormEvent) => {
    e.preventDefault()
    const q = input.trim()
    if (!q) return
    setMessages((m) => [...m, { role: 'user', content: q }])
    setInput('')
    setBusy(true)
    try {
      const res = await api.askTutor(q)
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: res.answer, sources: res.sources },
      ])
    } catch {
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: 'Ocurrió un error al consultar al tutor.' },
      ])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <h2 className="text-2xl font-bold mb-1">Tutor virtual con IA</h2>
      <p className="text-slate-500 mb-4">
        Pregunta sobre tus documentos. Las respuestas citan la fuente.
      </p>

      <div className="flex-1 bg-white rounded-xl shadow-sm p-5 overflow-auto space-y-4">
        {messages.length === 0 && (
          <p className="text-sm text-slate-400">
            Haz una pregunta para empezar. El tutor responde con base en el material que subiste.
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>
            <div
              className={`inline-block px-4 py-2 rounded-2xl text-sm max-w-[80%] ${
                m.role === 'user'
                  ? 'bg-brand-light text-white'
                  : 'bg-slate-100 text-slate-800'
              }`}
            >
              <p className="whitespace-pre-wrap">{m.content}</p>
              {m.sources && m.sources.length > 0 && (
                <p className="mt-2 text-xs opacity-70">
                  Fuentes: {m.sources.map((s) => `p.${s.page ?? '?'}`).join(', ')}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={send} className="mt-4 flex gap-3">
        <input
          className="flex-1 border rounded-md px-4 py-2 text-sm"
          placeholder="Escribe tu pregunta…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button
          disabled={busy}
          className="bg-brand-light text-white px-5 py-2 rounded-md text-sm disabled:opacity-50"
        >
          {busy ? '…' : 'Enviar'}
        </button>
      </form>
    </div>
  )
}
