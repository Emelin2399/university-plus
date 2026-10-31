import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import SubjectsPage from './pages/SubjectsPage'
import DocumentsPage from './pages/DocumentsPage'
import TutorPage from './pages/TutorPage'
import QuizzesPage from './pages/QuizzesPage'
import PlannerPage from './pages/PlannerPage'
import NotesPage from './pages/NotesPage'
import ProgressPage from './pages/ProgressPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { session, loading, devMode } = useAuth()
  if (loading) return <div className="p-8">Cargando…</div>
  if (!session && !devMode) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="subjects" element={<SubjectsPage />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="tutor" element={<TutorPage />} />
        <Route path="quizzes" element={<QuizzesPage />} />
        <Route path="planner" element={<PlannerPage />} />
        <Route path="progress" element={<ProgressPage />} />
        <Route path="notes" element={<NotesPage />} />
      </Route>
    </Routes>
  )
}
