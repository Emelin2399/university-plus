import { supabase } from './supabase'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

/**
 * Cliente HTTP que adjunta el token de Supabase a cada petición al backend.
 */
async function authHeader(): Promise<Record<string, string>> {
  if (!supabase) {
    // Modo desarrollo sin Supabase: token de prueba aceptado por el backend.
    return { Authorization: 'Bearer dev-token' }
  }
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    ...(await authHeader()),
    ...(options.headers ?? {}),
  }
  const res = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error(detail.detail ?? `Error ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  // Asignaturas
  listSubjects: () => request<Subject[]>('/subjects'),
  createSubject: (body: { name: string; term?: string; color?: string }) =>
    request<Subject>('/subjects', { method: 'POST', body: JSON.stringify(body) }),
  deleteSubject: (id: string) =>
    request<void>(`/subjects/${id}`, { method: 'DELETE' }),

  // Documentos
  listDocuments: (subjectId?: string) =>
    request<DocumentItem[]>(
      `/documents${subjectId ? `?subject_id=${subjectId}` : ''}`,
    ),
  uploadDocument: async (subjectId: string, file: File) => {
    const form = new FormData()
    form.append('subject_id', subjectId)
    form.append('file', file)
    const res = await fetch(`${API_URL}/documents`, {
      method: 'POST',
      headers: await authHeader(),
      body: form,
    })
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}))
      throw new Error(detail.detail ?? 'No se pudo subir el documento')
    }
    return res.json() as Promise<DocumentItem>
  },
  addDocumentFromUrl: (body: { subject_id: string; url: string; name?: string }) =>
    request<DocumentItem>('/documents/from-url', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  deleteDocument: (id: string) =>
    request<void>(`/documents/${id}`, { method: 'DELETE' }),

  // Tutor
  askTutor: (question: string, subjectId?: string) =>
    request<TutorAnswer>('/tutor/ask', {
      method: 'POST',
      body: JSON.stringify({ question, subject_id: subjectId }),
    }),

  // Planificador (actividades)
  listActivities: (params?: { subject_id?: string; status?: string }) => {
    const qs = new URLSearchParams()
    if (params?.subject_id) qs.set('subject_id', params.subject_id)
    if (params?.status) qs.set('status', params.status)
    const suffix = qs.toString() ? `?${qs}` : ''
    return request<Activity[]>(`/activities${suffix}`)
  },
  createActivity: (body: {
    subject_id: string
    title: string
    due_date?: string | null
    status?: string
  }) => request<Activity>('/activities', { method: 'POST', body: JSON.stringify(body) }),
  updateActivity: (id: string, body: Partial<{ title: string; due_date: string | null; status: string }>) =>
    request<Activity>(`/activities/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteActivity: (id: string) =>
    request<void>(`/activities/${id}`, { method: 'DELETE' }),

  // Seguimiento del aprendizaje
  getProgress: (subjectId?: string) =>
    request<ProgressReport>(
      `/progress${subjectId ? `?subject_id=${subjectId}` : ''}`,
    ),

  // EXPLORA PLUS
  exploreSearch: (query: string, limit = 8) =>
    request<ExploreResult>('/explore/search', {
      method: 'POST',
      body: JSON.stringify({ query, limit }),
    }),
  exploreHistory: () => request<ExploreSearchSummary[]>('/explore/history'),
  getExploreSearch: (id: string) => request<ExploreResult>(`/explore/${id}`),
  updateResourceStatus: (id: string, resource_index: number, status: string) =>
    request<ExploreResult>(`/explore/${id}/resource`, {
      method: 'PATCH',
      body: JSON.stringify({ resource_index, status }),
    }),

  // MIS NOTAS PLUS
  listNotes: (params?: { subject_id?: string; q?: string }) => {
    const qs = new URLSearchParams()
    if (params?.subject_id) qs.set('subject_id', params.subject_id)
    if (params?.q) qs.set('q', params.q)
    const suffix = qs.toString() ? `?${qs}` : ''
    return request<Note[]>(`/notes${suffix}`)
  },
  createNote: (body: { title: string; content?: string; subject_id?: string; topic?: string }) =>
    request<Note>('/notes', { method: 'POST', body: JSON.stringify(body) }),
  updateNote: (id: string, body: Partial<{ title: string; content: string; is_favorite: boolean; topic: string }>) =>
    request<Note>(`/notes/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteNote: (id: string) => request<void>(`/notes/${id}`, { method: 'DELETE' }),

  // Cuestionarios
  createQuiz: (body: {
    subject_id: string
    title: string
    num_questions: number
    difficulty: string
    document_id?: string
  }) => request<Quiz>('/quizzes', { method: 'POST', body: JSON.stringify(body) }),
  submitAttempt: (body: {
    quiz_id: string
    answers: { question_id: string; given_answer: string }[]
  }) =>
    request<AttemptResult>('/quizzes/attempts', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
}

// ----------------------------- Tipos -----------------------------
export interface Subject {
  id: string
  name: string
  term?: string
  color?: string
}

export interface DocumentItem {
  id: string
  subject_id: string
  name: string
  status: string
  source_type?: 'file' | 'link'
  source_url?: string
  page_count?: number
}

export interface TutorAnswer {
  answer: string
  sources: { document_id?: string; page?: number }[]
}

export interface Question {
  id: string
  statement: string
  type: string
  options?: string[]
  explanation?: string
}

export interface Quiz {
  id: string
  subject_id: string
  title: string
  questions: Question[]
}

export interface AttemptResult {
  attempt_id: string
  score: number
  correct: number
  total: number
}

export interface Activity {
  id: string
  subject_id: string
  title: string
  due_date?: string | null
  status: 'pending' | 'in_progress' | 'done'
}

export interface Note {
  id: string
  subject_id?: string | null
  title: string
  content: string
  topic?: string | null
  is_favorite: boolean
  created_at?: string
  updated_at?: string
}

export interface ProgressReport {
  summary: { total_attempts: number; average_score: number; best_score: number }
  by_subject: {
    subject_id?: string | null
    subject_name: string
    attempts: number
    average_score: number
  }[]
  evolution: { quiz_title: string; score: number; finished_at: string }[]
  to_reinforce: {
    quiz_id?: string | null
    quiz_title: string
    subject_id?: string | null
    score: number
  }[]
}

export interface AcademicResource {
  title: string
  authors: string[]
  year?: number | null
  venue?: string | null
  doi?: string | null
  url?: string | null
  source: string
  resource_type: string
  open_access?: boolean | null
  is_example: boolean
  status: 'pending' | 'reviewing' | 'understood'
}

export interface LearningStep {
  position: number
  step: string
  label: string
  resources: AcademicResource[]
}

export interface ExploreResult {
  id: string
  query: string
  resources: AcademicResource[]
  path: LearningStep[]
}

export interface ExploreSearchSummary {
  id: string
  query: string
  created_at?: string
}
