import { createFileRoute } from '@tanstack/react-router'
import { Layout } from '~/components/layout'
import { ProtectedRoute } from '~/components/auth'

export const Route = createFileRoute('/teacher/analytics')({
  component: TeacherAnalytics,
})

function TeacherAnalytics() {
  const sidebarLinks = [
    { to: '/teacher/dashboard', label: 'Dashboard', icon: '📊' },
    { to: '/teacher/students', label: 'Students', icon: '👥' },
    { to: '/teacher/videos', label: 'Videos', icon: '🎥' },
    { to: '/teacher/pdfs', label: 'PDFs', icon: '📄' },
    { to: '/teacher/homework', label: 'Homework', icon: '📝' },
    { to: '/teacher/analytics', label: 'Analytics', icon: '📈' },
  ]

  return (
    <ProtectedRoute requiredRole="teacher" redirectTo="/teacher/login">
      <Layout showSidebar={true} sidebarLinks={sidebarLinks}>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-6">
            Analytics & Reports
          </h1>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <p className="text-gray-600">
              Student analytics and reporting functionality will be implemented here.
            </p>
          </div>
        </div>
      </Layout>
    </ProtectedRoute>
  )
}
