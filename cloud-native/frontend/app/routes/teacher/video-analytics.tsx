import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Layout } from '~/components/layout'
import { ProtectedRoute } from '~/components/auth'
import { apiClient } from '~/lib/apiClient'
import type { Video, VideoAnalytics, StudentVideoView } from '~/types'

export const Route = createFileRoute('/teacher/video-analytics')({
  component: VideoAnalyticsPage,
})

type SortField = 'name' | 'percentage' | 'watchTime' | 'lastWatched'
type SortDirection = 'asc' | 'desc'
type FilterStatus = 'all' | 'not-started' | 'in-progress' | 'completed'

function VideoAnalyticsPage() {
  const navigate = useNavigate()
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null)
  const [sortField, setSortField] = useState<SortField>('percentage')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all')
  const [searchQuery, setSearchQuery] = useState('')

  const sidebarLinks = [
    { to: '/teacher/dashboard', label: 'Dashboard', icon: '📊' },
    { to: '/teacher/students', label: 'Students', icon: '👥' },
    { to: '/teacher/videos', label: 'Videos', icon: '🎥' },
    { to: '/teacher/pdfs', label: 'PDFs', icon: '📄' },
    { to: '/teacher/homework', label: 'Homework', icon: '📝' },
    { to: '/teacher/analytics', label: 'Analytics', icon: '📈' },
  ]

  // Fetch videos
  const { data: videos = [], isLoading: videosLoading } = useQuery<Video[]>({
    queryKey: ['videos'],
    queryFn: () => apiClient.get<Video[]>('/videos'),
  })

  // Fetch analytics for selected video
  const { data: analytics, isLoading: analyticsLoading } = useQuery<VideoAnalytics>({
    queryKey: ['video-analytics', selectedVideoId],
    queryFn: () => apiClient.get<VideoAnalytics>(`/videos/${selectedVideoId}/analytics`),
    enabled: !!selectedVideoId,
  })

  // Filter and sort student views
  const filteredAndSortedViews = useMemo(() => {
    if (!analytics?.studentViews) return []

    let filtered = analytics.studentViews

    // Apply status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter((view) => {
        if (filterStatus === 'not-started') return view.percentageWatched === 0
        if (filterStatus === 'in-progress') return view.percentageWatched > 0 && !view.completed
        if (filterStatus === 'completed') return view.completed
        return true
      })
    }

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter((view) =>
        view.studentName.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    // Sort
    const sorted = [...filtered].sort((a, b) => {
      let comparison = 0

      switch (sortField) {
        case 'name':
          comparison = a.studentName.localeCompare(b.studentName)
          break
        case 'percentage':
          comparison = a.percentageWatched - b.percentageWatched
          break
        case 'watchTime':
          comparison = a.totalWatchSeconds - b.totalWatchSeconds
          break
        case 'lastWatched':
          const aTime = a.lastWatchedAt ? new Date(a.lastWatchedAt).getTime() : 0
          const bTime = b.lastWatchedAt ? new Date(b.lastWatchedAt).getTime() : 0
          comparison = aTime - bTime
          break
      }

      return sortDirection === 'asc' ? comparison : -comparison
    })

    return sorted
  }, [analytics?.studentViews, filterStatus, searchQuery, sortField, sortDirection])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`
    }
    if (minutes > 0) {
      return `${minutes}m ${secs}s`
    }
    return `${secs}s`
  }

  const getProgressColor = (percentage: number) => {
    if (percentage === 0) return 'bg-gray-300'
    if (percentage < 50) return 'bg-red-500'
    if (percentage < 80) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const getStatusBadge = (view: StudentVideoView) => {
    if (view.percentageWatched === 0) {
      return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">Not Started</span>
    }
    if (view.completed) {
      return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Completed</span>
    }
    return <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">In Progress</span>
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <span className="text-gray-400">⇅</span>
    return sortDirection === 'asc' ? <span>↑</span> : <span>↓</span>
  }

  return (
    <ProtectedRoute requiredRole="teacher" redirectTo="/teacher/login">
      <Layout showSidebar={true} sidebarLinks={sidebarLinks}>
        <div>
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold text-gray-900">Video Analytics</h1>
            <button
              onClick={() => navigate({ to: '/teacher/videos' })}
              className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium transition-colors"
            >
              ← Back to Videos
            </button>
          </div>

          {/* Video Selection */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Video
            </label>
            {videosLoading ? (
              <div className="text-gray-600">Loading videos...</div>
            ) : (
              <select
                value={selectedVideoId || ''}
                onChange={(e) => setSelectedVideoId(e.target.value || null)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Choose a video to view analytics</option>
                {videos
                  .filter((v) => v.status === 'ready')
                  .map((video) => (
                    <option key={video.id} value={video.id}>
                      {video.title}
                    </option>
                  ))}
              </select>
            )}
          </div>

          {/* Analytics Dashboard */}
          {selectedVideoId && (
            <>
              {analyticsLoading ? (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="text-gray-600 mt-4">Loading analytics...</p>
                  </div>
                </div>
              ) : analytics ? (
                <>
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                    <div className="bg-white rounded-lg shadow-md p-6">
                      <div className="text-sm font-medium text-gray-600 mb-1">Total Views</div>
                      <div className="text-3xl font-bold text-gray-900">{analytics.totalViews}</div>
                    </div>
                    <div className="bg-white rounded-lg shadow-md p-6">
                      <div className="text-sm font-medium text-gray-600 mb-1">Average Completion</div>
                      <div className="text-3xl font-bold text-gray-900">
                        {analytics.averagePercentageWatched.toFixed(1)}%
                      </div>
                    </div>
                    <div className="bg-white rounded-lg shadow-md p-6">
                      <div className="text-sm font-medium text-gray-600 mb-1">Students Not Started</div>
                      <div className="text-3xl font-bold text-gray-900">
                        {analytics.studentViews.filter((v) => v.percentageWatched === 0).length}
                      </div>
                    </div>
                  </div>

                  {/* Filters and Search */}
                  <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                    <div className="flex flex-col md:flex-row gap-4">
                      <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Search Students
                        </label>
                        <input
                          type="text"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          placeholder="Search by student name..."
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                      <div className="w-full md:w-48">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Filter by Status
                        </label>
                        <select
                          value={filterStatus}
                          onChange={(e) => setFilterStatus(e.target.value as FilterStatus)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                          <option value="all">All Students</option>
                          <option value="not-started">Not Started</option>
                          <option value="in-progress">In Progress</option>
                          <option value="completed">Completed</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* Student Viewing Table */}
                  <div className="bg-white rounded-lg shadow-md overflow-hidden">
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50 border-b border-gray-200">
                          <tr>
                            <th
                              onClick={() => handleSort('name')}
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                            >
                              <div className="flex items-center gap-2">
                                Student Name
                                <SortIcon field="name" />
                              </div>
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Status
                            </th>
                            <th
                              onClick={() => handleSort('percentage')}
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                            >
                              <div className="flex items-center gap-2">
                                % Watched
                                <SortIcon field="percentage" />
                              </div>
                            </th>
                            <th
                              onClick={() => handleSort('watchTime')}
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                            >
                              <div className="flex items-center gap-2">
                                Watch Time
                                <SortIcon field="watchTime" />
                              </div>
                            </th>
                            <th
                              onClick={() => handleSort('lastWatched')}
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                            >
                              <div className="flex items-center gap-2">
                                Last Watched
                                <SortIcon field="lastWatched" />
                              </div>
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {filteredAndSortedViews.length === 0 ? (
                            <tr>
                              <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                                {searchQuery || filterStatus !== 'all'
                                  ? 'No students match your filters'
                                  : 'No viewing data available yet'}
                              </td>
                            </tr>
                          ) : (
                            filteredAndSortedViews.map((view) => (
                              <tr
                                key={view.studentId}
                                className={`hover:bg-gray-50 ${view.percentageWatched === 0 ? 'bg-red-50' : ''}`}
                              >
                                <td className="px-6 py-4 whitespace-nowrap">
                                  <div className="text-sm font-medium text-gray-900">
                                    {view.studentName}
                                  </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                  {getStatusBadge(view)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                  <div className="flex items-center gap-3">
                                    <div className="flex-1 bg-gray-200 rounded-full h-2 w-24">
                                      <div
                                        className={`h-2 rounded-full ${getProgressColor(view.percentageWatched)}`}
                                        style={{ width: `${view.percentageWatched}%` }}
                                      />
                                    </div>
                                    <span className="text-sm font-medium text-gray-900 w-12 text-right">
                                      {view.percentageWatched.toFixed(0)}%
                                    </span>
                                  </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                  {formatDuration(view.totalWatchSeconds)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                  {view.lastWatchedAt
                                    ? new Date(view.lastWatchedAt).toLocaleString()
                                    : 'Never'}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Results Summary */}
                  <div className="mt-4 text-sm text-gray-600 text-center">
                    Showing {filteredAndSortedViews.length} of {analytics.studentViews.length} students
                  </div>
                </>
              ) : (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <p className="text-center text-gray-600">No analytics data available for this video</p>
                </div>
              )}
            </>
          )}

          {/* Empty State */}
          {!selectedVideoId && !videosLoading && (
            <div className="bg-white rounded-lg shadow-md p-12 text-center">
              <div className="text-6xl mb-4">📊</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Video Analytics</h2>
              <p className="text-gray-600 mb-6">
                Select a video above to view detailed viewing statistics and student engagement data
              </p>
              <div className="text-sm text-gray-500">
                Track which students have watched your videos, how much they've watched, and identify students who need encouragement
              </div>
            </div>
          )}
        </div>
      </Layout>
    </ProtectedRoute>
  )
}
