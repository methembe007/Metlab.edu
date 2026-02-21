import { createFileRoute, Link } from '@tanstack/react-router'
import { Layout } from '~/components/layout'
import { ProtectedRoute } from '~/components/auth'
import { useAuth } from '~/contexts/AuthContext'

export const Route = createFileRoute('/teacher/dashboard')({
  component: TeacherDashboard,
})

function TeacherDashboard() {
  const { user } = useAuth()

  // Navigation links for the sidebar
  const sidebarLinks = [
    { to: '/teacher/dashboard', label: 'Dashboard', icon: '📊' },
    { to: '/teacher/students', label: 'Students', icon: '👥' },
    { to: '/teacher/videos', label: 'Videos', icon: '🎥' },
    { to: '/teacher/pdfs', label: 'PDFs', icon: '📄' },
    { to: '/teacher/homework', label: 'Homework', icon: '📝' },
    { to: '/teacher/analytics', label: 'Analytics', icon: '📈' },
  ]

  // Quick action items
  const quickActions = [
    {
      title: 'Register Students',
      description: 'Generate signin codes for new students',
      icon: '➕',
      link: '/teacher/students',
      color: 'blue',
    },
    {
      title: 'Upload Video',
      description: 'Add new video content for your classes',
      icon: '🎬',
      link: '/teacher/videos',
      color: 'purple',
    },
    {
      title: 'Upload PDF',
      description: 'Share documents with your students',
      icon: '📤',
      link: '/teacher/pdfs',
      color: 'green',
    },
    {
      title: 'Create Assignment',
      description: 'Assign homework to your students',
      icon: '✏️',
      link: '/teacher/homework',
      color: 'orange',
    },
  ]

  return (
    <ProtectedRoute requiredRole="teacher" redirectTo="/teacher/login">
      <Layout showSidebar={true} sidebarLinks={sidebarLinks}>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-6">
            Teacher Dashboard
          </h1>
          
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Welcome back, {user?.fullName}!
            </h2>
            <p className="text-gray-600">
              This is your teacher dashboard. From here you can manage your classes,
              upload content, and track student progress.
            </p>
          </div>

          {/* Class Overview Stats */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Class Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-gray-600 mb-1">
                      My Classes
                    </h3>
                    <p className="text-3xl font-bold text-gray-900">0</p>
                    <p className="text-sm text-gray-500 mt-2">Active classes</p>
                  </div>
                  <div className="text-4xl">📚</div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-gray-600 mb-1">
                      Total Students
                    </h3>
                    <p className="text-3xl font-bold text-gray-900">0</p>
                    <p className="text-sm text-gray-500 mt-2">Across all classes</p>
                  </div>
                  <div className="text-4xl">👥</div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-purple-500">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-gray-600 mb-1">
                      Pending Grading
                    </h3>
                    <p className="text-3xl font-bold text-gray-900">0</p>
                    <p className="text-sm text-gray-500 mt-2">Homework submissions</p>
                  </div>
                  <div className="text-4xl">📋</div>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {quickActions.map((action) => (
                <Link
                  key={action.title}
                  to={action.link}
                  className={`bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer border-t-4 border-${action.color}-500`}
                >
                  <div className="text-center">
                    <div className="text-4xl mb-3">{action.icon}</div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {action.title}
                    </h3>
                    <p className="text-sm text-gray-600">{action.description}</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          {/* Recent Activity Section */}
          <div className="mt-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
            <div className="bg-white rounded-lg shadow-md p-6">
              <p className="text-gray-500 text-center py-8">
                No recent activity to display. Start by registering students or uploading content.
              </p>
            </div>
          </div>
        </div>
      </Layout>
    </ProtectedRoute>
  )
}
