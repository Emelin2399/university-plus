import { useEffect, useState } from 'react'
import {
  api,
  type AttemptResult,
  type Question,
  type Quiz,
  type Subject,
} from '../lib/api'

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
          {quiz.questions.map((q, i) => {
            const detail = result?.details.find((d) => d.question_id === q.id)
            return (
              <div key={q.id}>
                <p className="font-medium text-sm mb-2 flex items-center gap-2">
                  <span>
                    {i + 1}. {q.statement}
                  </span>
                  {q.difficulty && (
                    <span className={difficultyBadge(q.difficulty)}>
                      {difficultyLabel(q.difficulty)}
                    </span>
                  )}
                </p>
                {effectiveType(q) === 'open' ? (
                  <textarea
                    className="w-full border rounded-md px-3 py-2 text-sm min-h-[90px] disabled:bg-slate-50 disabled:text-slate-500"
                    placeholder="Escribe tu respuesta…"
                    disabled={result != null}
                    value={answers[q.id] ?? ''}
                    onChange={(e) =>
                      setAnswers((a) => ({ ...a, [q.id]: e.target.value }))
                    }
                  />
                ) : (
                  <div className="space-y-1">
                    {questionOptions(q).map((opt) => {
                      const isCorrectOpt =
                        detail != null && detail.correct_answer === opt
                      const isChosenWrong =
                        detail != null &&
                        detail.given_answer === opt &&
                        detail.is_correct === false
                      return (
                        <label
                          key={opt}
                          className={`flex items-center gap-2 text-sm rounded px-1 ${
                            isCorrectOpt
                              ? 'bg-green-50 text-green-700 font-medium'
                              : isChosenWrong
                              ? 'bg-red-50 text-red-600'
                              : ''
                          }`}
                        >
                          <input
                            type="radio"
                            name={q.id}
                            disabled={result != null}
                            checked={answers[q.id] === opt}
                            onChange={() =>
                              setAnswers((a) => ({ ...a, [q.id]: opt }))
                            }
                          />
                          {opt}
                          {isCorrectOpt && ' ✓'}
                        </label>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}

          {!result && (
            <button
              onClick={submit}
              className="bg-brand text-white px-5 py-2 rounded-md text-sm"
            >
              Enviar respuestas
            </button>
          )}

          {result && (
            <div className="mt-4 space-y-3">
              <div className="p-4 bg-slate-50 rounded-lg text-sm">
                <p className="font-semibold">
                  Resultado: {result.score}% ({result.correct}/{result.total}{' '}
                  correctas)
                </p>
              </div>

              <div className="space-y-3">
                <p className="text-sm font-semibold text-slate-700">
                  En qué fallaste
                </p>
                {result.details.map((d, i) => {
                  // Preguntas abiertas: no se auto-califican, se muestran en
                  // tono neutro con la respuesta esperada para autoevaluación.
                  const isOpen = d.auto_graded === false
                  return (
                    <div
                      key={d.question_id}
                      className={`rounded-lg border p-3 text-sm ${
                        isOpen
                          ? 'border-slate-200 bg-slate-50'
                          : d.is_correct
                          ? 'border-green-200 bg-green-50'
                          : 'border-red-200 bg-red-50'
                      }`}
                    >
                      <p className="font-medium flex items-center gap-2">
                        <span>{isOpen ? '✎' : d.is_correct ? '✓' : '✗'}</span>
                        <span>
                          {i + 1}. {d.statement}
                        </span>
                        {isOpen && (
                          <span className="text-xs px-2 py-0.5 rounded-full font-normal bg-slate-200 text-slate-600">
                            Respuesta abierta
                          </span>
                        )}
                      </p>
                      <p className="mt-1 text-slate-600">
                        Tu respuesta:{' '}
                        <span
                          className={
                            isOpen
                              ? 'text-slate-700'
                              : d.is_correct
                              ? 'text-green-700'
                              : 'text-red-600'
                          }
                        >
                          {d.given_answer || '(sin responder)'}
                        </span>
                      </p>
                      {(isOpen || !d.is_correct) && (
                        <p className="text-slate-600">
                          {isOpen ? 'Respuesta de referencia: ' : 'Respuesta correcta: '}
                          <span className="font-semibold text-green-700">
                            {d.correct_answer ?? '—'}
                          </span>
                        </p>
                      )}
                      {isOpen && (
                        <p className="mt-1 text-slate-500">
                          Esta pregunta es abierta: no puntúa en la nota. Compara
                          tu respuesta con la de referencia para autoevaluarte.
                        </p>
                      )}
                      {d.explanation && (
                        <p className="mt-1 text-slate-500">{d.explanation}</p>
                      )}
                    </div>
                  )
                })}
              </div>

              <button
                onClick={generate}
                className="bg-brand-light text-white px-5 py-2 rounded-md text-sm"
              >
                Generar otro cuestionario
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * Determina el tipo efectivo de una pregunta para decidir cómo renderizarla.
 *
 * Usa `q.type` cuando está presente. Si falta, aplica un respaldo defensivo:
 * si hay opciones, se trata como opción múltiple; si no hay opciones y no es
 * abierta, se trata como verdadero/falso.
 */
function effectiveType(q: Question): 'multiple_choice' | 'true_false' | 'open' {
  if (q.type === 'open') return 'open'
  if (q.type === 'multiple_choice' || q.type === 'true_false') return q.type
  if (q.options && q.options.length > 0) return 'multiple_choice'
  return 'true_false'
}

/** Opciones a mostrar como radios según el tipo (nunca para abiertas). */
function questionOptions(q: Question): string[] {
  if (effectiveType(q) === 'true_false') return ['Verdadero', 'Falso']
  return q.options ?? []
}

/** Devuelve las clases Tailwind de la insignia de dificultad. */
function difficultyBadge(difficulty: string): string {
  const base = 'text-xs px-2 py-0.5 rounded-full font-normal'
  if (difficulty === 'facil') return `${base} bg-green-100 text-green-700`
  if (difficulty === 'avanzado') return `${base} bg-red-100 text-red-600`
  return `${base} bg-amber-100 text-amber-700`
}

/** Texto legible para la etiqueta de dificultad. */
function difficultyLabel(difficulty: string): string {
  if (difficulty === 'facil') return 'Fácil'
  if (difficulty === 'medio') return 'Medio'
  if (difficulty === 'avanzado') return 'Avanzado'
  return difficulty
}
