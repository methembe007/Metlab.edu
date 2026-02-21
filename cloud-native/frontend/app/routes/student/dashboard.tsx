import { createFileRoute, Link } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { Layout } from '~/components/layout'
import { ProtectedRoute } from '~/components/auth'
import { useAuth } from '~/contexts/AuthContext'
import { apiClient } from '~/lib/apiClient'
import { LineChart } from '~/components/charts/LineChart'
import type { Assignment, Video, LoginStats } from '~/types'

export const Route = createFileRoute('/student/dashboard')({
  component: StudentDashboard,
})

function StudentDashboard() {
  const { user } = useAuth()

  // Fetch upcoming assignments
  const { data: assignments = [] } = useQuery<Assignment[]>({
    queryKey: ['assignments'],
    queryFn: () => apiClient.get<Assignment[]>('/homework/assignments'),
  })

  // Fetch recent videos
  const { data: videos = [] } = useQuery<Video[]>({
    queryKey: ['videos'],
    queryFn: () => apiClient.get<Video[]>('/videos'),
  })

  // Fetch login activity stats
  const { data: loginStats } = useQuery<LoginStats>({
    queryKey: ['login-stats'],
    queryFn: () => apiClient.get<LoginStats>('/analytics/login-stats?days=30'),
  })

  // Filter upcoming assignments (not past due date)
  const upcomingAssignments = assignments
    .filter(a => new Date(a.dueDate) >= new Date())
    .sort((a, b) => new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime())
    .slice(0, 5)

  // Get recent videos (last 5)
  const recentVideos = videos
    .filter(v => v.status === 'ready')
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, 5)

  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  // Format duration
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <ProtectedRoute requiredRole="student" redirectTo="/student/signin">
      <Layout showSidebar={true}>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-6">
            Student Dashboard
          </h1>

          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Welcome, {user?.fullName}!
            </h2>
            <p className="text-gray-600">
              This is your student dashboard. From here you can access your lessons,
              submit homework, and track your progress.
            </p>
          </div>

          {/* Login Activity Graph */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Login Activity (Last 30 Days)
            </h2>
            {loginStats ? (
              <div>
                <LineChart 
                  data={loginStats.dailyCounts.map(dc => ({
                    date: dc.date,
                    count: dc.count
                  }))}
                  color="#3b82f6"
                />
                <div className="grid grid-cols-2 gap-4 mt-6">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">{loginStats.totalLogins}</p>
                    <p className="text-sm text-gray-600">Total Logins</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">{loginStats.averagePerWeek.toFixed(1)}</p>
                    <p className="text-sm text-gray-600">Average per Week</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
                <p className="text-gray-500">Loading activity data...</p>
              </div>
            )}
          </div>

          {/* Upcoming Assignments */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Upcoming Assignments
            </h2>
            {upcomingAssignments.length > 0 ? (
              <div className="space-y-3">
                {upcomingAssignments.map((assignment) => (
                  <div 
                    key={assignment.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{assignment.title}</h3>
                      <p className="text-sm text-gray-600 mt-1">{assignment.description}</p>
                    </div>
                    <div className="text-right ml-4">
                      <p className="text-sm font-medium text-orange-600">
                        Due: {formatDate(assignment.dueDate)}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Max Score: {assignment.maxScore}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                No upcoming assignments
              </div>
            )}
          </div>

          {/* Recent Videos */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Recent Videos
            </h2>
            {recentVideos.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {recentVideos.map((video) => (
                  <div 
                    key={video.id}
                    className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
                  >
                    <div className="aspect-video bg-gray-200 relative">
                      {video.thumbnailUrl ? (
                        <img 
                          src={video.thumbnailUrl} 
                          alt={video.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="flex items-center justify-center h-full">
                          <span className="text-4xl">🎥</span>
                        </div>
                      )}
                      <div className="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                        {formatDuration(video.durationSeconds)}
                      </div>
                    </div>
                    <div className="p-4">
                      <h3 className="font-semibold text-gray-900 mb-2">{video.title}</h3>
                      <p className="text-sm text-gray-600 line-clamp-2">{video.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                No videos available
              </div>
            )}
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                Videos
              </h3>
              <p className="text-3xl font-bold text-blue-600">{videos.filter(v => v.status === 'ready').length}</p>
              <p className="text-sm text-gray-500 mt-2">Available to watch</p>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                Assignments
              </h3>
              <p className="text-3xl font-bold text-orange-600">{upcomingAssignments.length}</p>
              <p className="text-sm text-gray-500 mt-2">Due soon</p>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                Study Groups
              </h3>
              <p className="text-3xl font-bold text-purple-600">0</p>
              <p className="text-sm text-gray-500 mt-2">Groups joined</p>
            </div>
          </div>
        </div>
      </Layout>
    </ProtectedRoute>
  )
}
