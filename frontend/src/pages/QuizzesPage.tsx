import { useEffect, useState } from 'react'
import { api, type AttemptResult, type Quiz, type Subject } from '../lib/api'

export default function QuizzesPage() {
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [subjectId, setSubjectId] = useState('')
  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [result, setResult] = useState<AttemptResult | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.listSubjects().then((s) => {
      setSubjects(s)
      if (s[0]) setSubjectId(s[0].id)
    })
  }, [])

  const generate = async () => {
    if (!subjectId) return
    setBusy(true)
    setResult(null)
    setAnswers({})
    try {
      const q = await api.createQuiz({
        subject_id: subjectId,
        title: 'Cuestionario de práctica',
        num_questions: 5,
        difficulty: 'medium',
      })
      setQuiz(q)
    } finally {
      setBusy(false)
    }
  }

  const submit = async () => {
    if (!quiz) return
    const payload = {
      quiz_id: quiz.id,
      answers: quiz.questions.map((q) => ({
        question_id: q.id,
        given_answer: answers[q.id] ?? '',
      })),
    }
    const res = await api.submitAttempt(payload)
    setResult(res)
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-1">Cuestionarios</h2>
      <p className="text-slate-500 mb-6">
        Genera un cuestionario a partir de tu material y comprueba tu progreso.
      </p>

      <div className="bg-white rounded-xl shadow-sm p-5 mb-6 flex gap-3 items-center">
        <select
          className="border rounded-md px-3 py-2 text-sm"
          value={subjectId}
          onChange={(e) => setSubjectId(e.target.value)}
        >
          <option value="">Elige asignatura…</option>
          {subjects.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        <button
          onClick={generate}
          disabled={busy || !subjectId}
          className="bg-brand-light text-white px-4 py-2 rounded-md text-sm disabled:opacity-50"
        >
          {busy ? 'Generando…' : 'Generar cuestionario'}
        </button>
      </div>

      {quiz && (
        <div className="bg-white rounded-xl shadow-sm p-5 space-y-5">
          {quiz.questions.map((q, i) => (
            <div key={q.id}>
              <p className="font-medium text-sm mb-2">
                {i + 1}. {q.statement}
              </p>
              <div className="space-y-1">
                {(q.options ?? ['Verdadero', 'Falso']).map((opt) => (
                  <label key={opt} className="flex items-center gap-2 text-sm">
                    <input
                      type="radio"
                      name={q.id}
                      checked={answers[q.id] === opt}
                      onChange={() => setAnswers((a) => ({ ...a, [q.id]: opt }))}
                    />
                    {opt}
                  </label>
                ))}
              </div>
            </div>
          ))}

          <button
            onClick={submit}
            className="bg-brand text-white px-5 py-2 rounded-md text-sm"
          >
            Enviar respuestas
          </button>

          {result && (
            <div className="mt-4 p-4 bg-slate-50 rounded-lg text-sm">
              <p className="font-semibold">
                Resultado: {result.score}% ({result.correct}/{result.total} correctas)
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
