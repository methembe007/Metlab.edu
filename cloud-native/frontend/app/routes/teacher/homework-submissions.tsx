import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Layout } from '~/components/layout'
import { ProtectedRoute } from '~/components/auth'
import { apiClient } from '~/lib/apiClient'
import type { Submission, Assignment, ClassAverageStats, Grade } from '~/types'

export const Route = createFileRoute('/teacher/homework-submissions' as any)({
  component: HomeworkSubmissions,
})

interface GradeFormData {
  score: number
  feedback: string
}

function HomeworkSubmissions() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  // Get assignmentId from URL search params
  const searchParams = new URLSearchParams(window.location.search)
  const assignmentId = searchParams.get('assignmentId') || ''
  
  const [selectedSubmission, setSelectedSubmission] = useState<Submission | null>(null)
  const [showGradeModal, setShowGradeModal] = useState(false)
  const [gradeFormData, setGradeFormData] = useState<GradeFormData>({
    score: 0,
    feedback: '',
  })
  const [filterStatus, setFilterStatus] = useState<'all' | 'submitted' | 'graded'>('all')
  const [sortBy, setSortBy] = useState<'date' | 'name' | 'status'>('date')

  const sidebarLinks = [
    { to: '/teacher/dashboard', label: 'Dashboard', icon: '📊' },
    { to: '/teacher/students', label: 'Students', icon: '👥' },
    { to: '/teacher/videos', label: 'Videos', icon: '🎥' },
    { to: '/teacher/pdfs', label: 'PDFs', icon: '📄' },
    { to: '/teacher/homework', label: 'Homework', icon: '📝' },
    { to: '/teacher/analytics', label: 'Analytics', icon: '📈' },
  ]

  // Fetch assignment details
  const { data: assignment } = useQuery<Assignment>({
    queryKey: ['assignment', assignmentId],
    queryFn: () => apiClient.get<Assignment>(`/homework/assignments/${assignmentId}`),
    enabled: !!assignmentId,
  })

  // Fetch submissions
  const { data: submissions = [], isLoading } = useQuery<Submission[]>({
    queryKey: ['submissions', assignmentId],
    queryFn: () => apiClient.get<Submission[]>(`/homework/submissions?assignmentId=${assignmentId}`),
    enabled: !!assignmentId,
  })

  // Fetch class average stats
  const { data: classStats } = useQuery<ClassAverageStats>({
    queryKey: ['classStats', assignmentId],
    queryFn: () => apiClient.get<ClassAverageStats>(`/homework/assignments/${assignmentId}/stats`),
    enabled: !!assignmentId,
  })

  // Fetch grading history for a submission
  const { data: gradingHistory = [] } = useQuery<Grade[]>({
    queryKey: ['gradingHistory', selectedSubmission?.id],
    queryFn: () => apiClient.get<Grade[]>(`/homework/submissions/${selectedSubmission?.id}/history`),
    enabled: !!selectedSubmission?.id && showGradeModal,
  })

  // Grade submission mutation
  const gradeMutation = useMutation({
    mutationFn: async (data: { submissionId: string; score: number; feedback: string }) => {
      return apiClient.post(`/homework/submissions/${data.submissionId}/grade`, {
        score: data.score,
        feedback: data.feedback,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submissions', assignmentId] })
      queryClient.invalidateQueries({ queryKey: ['classStats', assignmentId] })
      setShowGradeModal(false)
      setSelectedSubmission(null)
      setGradeFormData({ score: 0, feedback: '' })
    },
  })

  // Download submission file
  const handleDownloadFile = async (submissionId: string, fileName: string) => {
    try {
      const API_URL = typeof window !== 'undefined' && (window as any).ENV?.VITE_API_URL 
        ? (window as any).ENV.VITE_API_URL 
        : 'http://localhost:8080/api'
      const token = localStorage.getItem('auth_token')
      const response = await fetch(
        `${API_URL}/homework/submissions/${submissionId}/file`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      if (!response.ok) throw new Error('Download failed')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = fileName
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      alert('Failed to download file')
      console.error(error)
    }
  }

  const handleGradeSubmission = () => {
    if (!selectedSubmission) return
    
    if (gradeFormData.score < 0 || gradeFormData.score > (assignment?.maxScore || 100)) {
      alert(`Score must be between 0 and ${assignment?.maxScore || 100}`)
      return
    }

    gradeMutation.mutate({
      submissionId: selectedSubmission.id,
      score: gradeFormData.score,
      feedback: gradeFormData.feedback,
    })
  }

  const openGradeModal = (submission: Submission) => {
    setSelectedSubmission(submission)
    setGradeFormData({
      score: submission.score || 0,
      feedback: submission.feedback || '',
    })
    setShowGradeModal(true)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  // Filter and sort submissions
  const filteredSubmissions = submissions
    .filter((sub) => {
      if (filterStatus === 'all') return true
      if (filterStatus === 'submitted') return sub.status === 'submitted'
      if (filterStatus === 'graded') return sub.status === 'graded'
      return true
    })
    .sort((a, b) => {
      if (sortBy === 'date') {
        return new Date(b.submittedAt).getTime() - new Date(a.submittedAt).getTime()
      }
      if (sortBy === 'name') {
        return a.studentName.localeCompare(b.studentName)
      }
      if (sortBy === 'status') {
        return a.status.localeCompare(b.status)
      }
      return 0
    })

  const ungradedCount = submissions.filter((s) => s.status === 'submitted').length
  const gradedCount = submissions.filter((s) => s.status === 'graded').length

  if (!assignmentId) {
    return (
      <ProtectedRoute requiredRole="teacher" redirectTo="/teacher/login">
        <Layout showSidebar={true} sidebarLinks={sidebarLinks}>
          <div className="text-center py-12">
            <p className="text-gray-600">No assignment selected</p>
            <button
              onClick={() => navigate({ to: '/teacher/homework' })}
              className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
            >
              ← Back to Homework
            </button>
          </div>
        </Layout>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute requiredRole="teacher" redirectTo="/teacher/login">
      <Layout showSidebar={true} sidebarLinks={sidebarLinks}>
        <div>
          {/* Header */}
          <div className="mb-6">
            <button
              onClick={() => navigate({ to: '/teacher/homework' })}
              className="text-blue-600 hover:text-blue-700 font-medium mb-3 inline-flex items-center"
            >
              ← Back to Homework
            </button>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {assignment?.title || 'Assignment Submissions'}
            </h1>
            {assignment && (
              <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                <span>Due: {formatDate(assignment.dueDate)}</span>
                <span>Max Score: {assignment.maxScore} points</span>
              </div>
            )}
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow-md p-4">
              <div className="text-sm text-gray-600 mb-1">Total Submissions</div>
              <div className="text-2xl font-bold text-gray-900">{submissions.length}</div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-4">
              <div className="text-sm text-gray-600 mb-1">Ungraded</div>
              <div className="text-2xl font-bold text-orange-600">{ungradedCount}</div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-4">
              <div className="text-sm text-gray-600 mb-1">Graded</div>
              <div className="text-2xl font-bold text-green-600">{gradedCount}</div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-4">
              <div className="text-sm text-gray-600 mb-1">Class Average</div>
              <div className="text-2xl font-bold text-blue-600">
                {classStats && classStats.gradedSubmissions > 0
                  ? `${classStats.averageScore.toFixed(1)}%`
                  : 'N/A'}
              </div>
            </div>
          </div>

          {/* Filters and Sort */}
          <div className="bg-white rounded-lg shadow-md p-4 mb-6">
            <div className="flex flex-wrap gap-4 items-center">
              <div>
                <label className="text-sm font-medium text-gray-700 mr-2">Filter:</label>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value as 'all' | 'submitted' | 'graded')}
                  className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="all">All Submissions</option>
                  <option value="submitted">Ungraded Only</option>
                  <option value="graded">Graded Only</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mr-2">Sort by:</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'date' | 'name' | 'status')}
                  className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="date">Submission Date</option>
                  <option value="name">Student Name</option>
                  <option value="status">Status</option>
                </select>
              </div>
            </div>
          </div>

          {/* Submissions List */}
          <div className="bg-white rounded-lg shadow-md p-6">
            {isLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-gray-600 mt-4">Loading submissions...</p>
              </div>
            ) : filteredSubmissions.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-600">
                  {filterStatus === 'all'
                    ? 'No submissions yet'
                    : `No ${filterStatus} submissions`}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredSubmissions.map((submission) => (
                  <div
                    key={submission.id}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">
                            {submission.studentName}
                          </h3>
                          <span
                            className={`px-2 py-1 text-xs font-semibold rounded-full ${
                              submission.status === 'graded'
                                ? 'bg-green-100 text-green-800'
                                : 'bg-orange-100 text-orange-800'
                            }`}
                          >
                            {submission.status === 'graded' ? 'Graded' : 'Pending'}
                          </span>
                          {submission.isLate && (
                            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                              Late
                            </span>
                          )}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-gray-600 mb-3">
                          <div>
                            <span className="font-medium">File:</span> {submission.fileName}
                          </div>
                          <div>
                            <span className="font-medium">Size:</span>{' '}
                            {formatFileSize(submission.fileSizeBytes)}
                          </div>
                          <div>
                            <span className="font-medium">Submitted:</span>{' '}
                            {formatDate(submission.submittedAt)}
                          </div>
                          {submission.status === 'graded' && (
                            <>
                              <div>
                                <span className="font-medium">Score:</span>{' '}
                                <span className="text-blue-600 font-semibold">
                                  {submission.score}/{assignment?.maxScore}
                                </span>
                              </div>
                              {submission.gradedAt && (
                                <div>
                                  <span className="font-medium">Graded:</span>{' '}
                                  {formatDate(submission.gradedAt)}
                                </div>
                              )}
                            </>
                          )}
                        </div>

                        {submission.feedback && (
                          <div className="bg-gray-50 rounded p-3 mb-3">
                            <div className="text-sm font-medium text-gray-700 mb-1">
                              Feedback:
                            </div>
                            <div className="text-sm text-gray-600">{submission.feedback}</div>
                          </div>
                        )}
                      </div>

                      <div className="flex flex-col gap-2 ml-4">
                        <button
                          onClick={() => handleDownloadFile(submission.id, submission.fileName)}
                          className="bg-blue-100 hover:bg-blue-200 text-blue-700 px-3 py-2 rounded text-sm font-medium transition-colors whitespace-nowrap"
                        >
                          📥 Download
                        </button>
                        <button
                          onClick={() => openGradeModal(submission)}
                          className={`px-3 py-2 rounded text-sm font-medium transition-colors whitespace-nowrap ${
                            submission.status === 'graded'
                              ? 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                              : 'bg-green-100 hover:bg-green-200 text-green-700'
                          }`}
                        >
                          {submission.status === 'graded' ? '✏️ Edit Grade' : '✓ Grade'}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Grade Submission Modal */}
        {showGradeModal && selectedSubmission && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Grade Submission - {selectedSubmission.studentName}
              </h2>

              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">File:</span>{' '}
                    <span className="text-gray-600">{selectedSubmission.fileName}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Submitted:</span>{' '}
                    <span className="text-gray-600">
                      {formatDate(selectedSubmission.submittedAt)}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Status:</span>{' '}
                    <span
                      className={`font-medium ${
                        selectedSubmission.isLate ? 'text-red-600' : 'text-green-600'
                      }`}
                    >
                      {selectedSubmission.isLate ? 'Late' : 'On Time'}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Max Score:</span>{' '}
                    <span className="text-gray-600">{assignment?.maxScore} points</span>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Score * (0 - {assignment?.maxScore || 100})
                  </label>
                  <input
                    type="number"
                    value={gradeFormData.score}
                    min={0}
                    max={assignment?.maxScore || 100}
                    onChange={(e) =>
                      setGradeFormData({
                        ...gradeFormData,
                        score: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter score"
                  />
                  <div className="mt-1 text-sm text-gray-500">
                    Percentage:{' '}
                    {assignment?.maxScore
                      ? ((gradeFormData.score / assignment.maxScore) * 100).toFixed(1)
                      : 0}
                    %
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Feedback
                  </label>
                  <textarea
                    value={gradeFormData.feedback}
                    onChange={(e) =>
                      setGradeFormData({
                        ...gradeFormData,
                        feedback: e.target.value,
                      })
                    }
                    rows={6}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Provide feedback to the student (optional)"
                  />
                </div>

                {selectedSubmission.status === 'graded' && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <div className="text-sm text-blue-800">
                      <strong>Note:</strong> This submission has already been graded. Saving will
                      update the existing grade.
                    </div>
                  </div>
                )}

                {/* Grading History */}
                {gradingHistory.length > 0 && (
                  <div className="border-t pt-4">
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">Grading History</h3>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {gradingHistory.map((grade, index) => (
                        <div
                          key={grade.id}
                          className="bg-gray-50 rounded p-3 text-sm"
                        >
                          <div className="flex justify-between items-start mb-1">
                            <span className="font-medium text-gray-900">
                              Version {gradingHistory.length - index}
                            </span>
                            <span className="text-gray-600">
                              {formatDate(grade.gradedAt)}
                            </span>
                          </div>
                          <div className="text-gray-700">
                            <span className="font-medium">Score:</span> {grade.score}/
                            {assignment?.maxScore}
                          </div>
                          {grade.feedback && (
                            <div className="text-gray-600 mt-1">
                              <span className="font-medium">Feedback:</span> {grade.feedback}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowGradeModal(false)
                    setSelectedSubmission(null)
                    setGradeFormData({ score: 0, feedback: '' })
                  }}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleGradeSubmission}
                  disabled={gradeMutation.isPending}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {gradeMutation.isPending ? 'Saving...' : 'Save Grade'}
                </button>
              </div>
            </div>
          </div>
        )}
      </Layout>
    </ProtectedRoute>
  )
}
