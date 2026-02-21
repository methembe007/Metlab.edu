import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Layout } from '~/components/layout'
import { ProtectedRoute } from '~/components/auth'
import { apiClient } from '~/lib/apiClient'
import type { Assignment } from '~/types'

export const Route = createFileRoute('/teacher/homework')({
  component: TeacherHomework,
})

interface AssignmentFormData {
  title: string
  description: string
  dueDate: string
  maxScore: number
  classId: string
}

function TeacherHomework() {
  const queryClient = useQueryClient()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingAssignment, setEditingAssignment] = useState<Assignment | null>(null)
  const [formData, setFormData] = useState<AssignmentFormData>({
    title: '',
    description: '',
    dueDate: '',
    maxScore: 100,
    classId: '',
  })

  const sidebarLinks = [
    { to: '/teacher/dashboard', label: 'Dashboard', icon: '📊' },
    { to: '/teacher/students', label: 'Students', icon: '👥' },
    { to: '/teacher/videos', label: 'Videos', icon: '🎥' },
    { to: '/teacher/pdfs', label: 'PDFs', icon: '📄' },
    { to: '/teacher/homework', label: 'Homework', icon: '📝' },
    { to: '/teacher/analytics', label: 'Analytics', icon: '📈' },
  ]

  // Fetch assignments
  const { data: assignments = [], isLoading } = useQuery<Assignment[]>({
    queryKey: ['assignments'],
    queryFn: () => apiClient.get<Assignment[]>('/homework/assignments'),
  })

  // Create assignment mutation
  const createMutation = useMutation({
    mutationFn: async (data: AssignmentFormData) => {
      return apiClient.post<Assignment>('/homework/assignments', {
        title: data.title,
        description: data.description,
        due_date: new Date(data.dueDate).toISOString(),
        max_score: data.maxScore,
        class_id: data.classId,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
      setShowCreateModal(false)
      setFormData({
        title: '',
        description: '',
        dueDate: '',
        maxScore: 100,
        classId: '',
      })
    },
  })

  // Update assignment mutation
  const updateMutation = useMutation({
    mutationFn: async (data: { id: string; updates: Partial<AssignmentFormData> }) => {
      return apiClient.put<Assignment>(`/homework/assignments/${data.id}`, {
        title: data.updates.title,
        description: data.updates.description,
        due_date: data.updates.dueDate ? new Date(data.updates.dueDate).toISOString() : undefined,
        max_score: data.updates.maxScore,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
      setEditingAssignment(null)
      setFormData({
        title: '',
        description: '',
        dueDate: '',
        maxScore: 100,
        classId: '',
      })
    },
  })

  // Delete assignment mutation
  const deleteMutation = useMutation({
    mutationFn: async (assignmentId: string) => {
      return apiClient.delete(`/homework/assignments/${assignmentId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
    },
  })

  const handleCreateAssignment = () => {
    if (!formData.title || !formData.dueDate || !formData.classId) {
      alert('Please fill in all required fields')
      return
    }

    createMutation.mutate(formData)
  }

  const handleUpdateAssignment = () => {
    if (!editingAssignment) return

    updateMutation.mutate({
      id: editingAssignment.id,
      updates: {
        title: formData.title,
        description: formData.description,
        dueDate: formData.dueDate,
        maxScore: formData.maxScore,
      },
    })
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const isOverdue = (dueDate: string) => {
    return new Date(dueDate) < new Date()
  }

  const getMinDateTime = () => {
    const now = new Date()
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
    return now.toISOString().slice(0, 16)
  }

  return (
    <ProtectedRoute requiredRole="teacher" redirectTo="/teacher/login">
      <Layout showSidebar={true} sidebarLinks={sidebarLinks}>
        <div>
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold text-gray-900">
              Homework Management
            </h1>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              + Create Assignment
            </button>
          </div>

          {/* Assignment List */}
          <div className="bg-white rounded-lg shadow-md p-6">
            {isLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-gray-600 mt-4">Loading assignments...</p>
              </div>
            ) : assignments.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-600">
                  No assignments created yet. Click "Create Assignment" to get started.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {assignments.map((assignment) => (
                  <div
                    key={assignment.id}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">
                            {assignment.title}
                          </h3>
                          {isOverdue(assignment.dueDate) && (
                            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                              Overdue
                            </span>
                          )}
                        </div>
                        {assignment.description && (
                          <p className="text-gray-600 mb-3">
                            {assignment.description}
                          </p>
                        )}
                        <div className="flex flex-wrap gap-4 text-sm text-gray-500">
                          <div className="flex items-center gap-1">
                            <span className="font-medium">Due:</span>
                            <span className={isOverdue(assignment.dueDate) ? 'text-red-600 font-medium' : ''}>
                              {formatDateTime(assignment.dueDate)}
                            </span>
                          </div>
                          <div className="flex items-center gap-1">
                            <span className="font-medium">Max Score:</span>
                            <span>{assignment.maxScore} points</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <span className="font-medium">Submissions:</span>
                            <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full font-medium">
                              {assignment.submissionCount}
                            </span>
                          </div>
                          <div className="flex items-center gap-1">
                            <span className="font-medium">Created:</span>
                            <span>{formatDate(assignment.createdAt)}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2 ml-4">
                        <button
                          onClick={() => {
                            window.location.href = `/teacher/homework-submissions?assignmentId=${assignment.id}`
                          }}
                          className="bg-blue-100 hover:bg-blue-200 text-blue-700 px-3 py-2 rounded text-sm font-medium transition-colors"
                        >
                          View Submissions
                        </button>
                        <button
                          onClick={() => {
                            setEditingAssignment(assignment)
                            setFormData({
                              title: assignment.title,
                              description: assignment.description,
                              dueDate: new Date(assignment.dueDate).toISOString().slice(0, 16),
                              maxScore: assignment.maxScore,
                              classId: '',
                            })
                          }}
                          className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded text-sm font-medium transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => {
                            if (
                              confirm(
                                'Are you sure you want to delete this assignment? This will also delete all submissions.'
                              )
                            ) {
                              deleteMutation.mutate(assignment.id)
                            }
                          }}
                          className="bg-red-100 hover:bg-red-200 text-red-700 px-3 py-2 rounded text-sm font-medium transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Create Assignment Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Create Assignment
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Title *
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) =>
                      setFormData({ ...formData, title: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter assignment title"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        description: e.target.value,
                      })
                    }
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter assignment description and instructions"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Due Date *
                    </label>
                    <input
                      type="datetime-local"
                      value={formData.dueDate}
                      min={getMinDateTime()}
                      onChange={(e) =>
                        setFormData({ ...formData, dueDate: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Score *
                    </label>
                    <input
                      type="number"
                      value={formData.maxScore}
                      min={1}
                      max={1000}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          maxScore: parseInt(e.target.value) || 100,
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Class *
                  </label>
                  <select
                    value={formData.classId}
                    onChange={(e) =>
                      setFormData({ ...formData, classId: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select a class</option>
                    <option value="class-1">Math 101</option>
                    <option value="class-2">Science 201</option>
                    <option value="class-3">History 301</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowCreateModal(false)
                    setFormData({
                      title: '',
                      description: '',
                      dueDate: '',
                      maxScore: 100,
                      classId: '',
                    })
                  }}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateAssignment}
                  disabled={
                    !formData.title ||
                    !formData.dueDate ||
                    !formData.classId ||
                    createMutation.isPending
                  }
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Assignment'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Edit Assignment Modal */}
        {editingAssignment && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Edit Assignment
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Title
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) =>
                      setFormData({ ...formData, title: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        description: e.target.value,
                      })
                    }
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Due Date
                    </label>
                    <input
                      type="datetime-local"
                      value={formData.dueDate}
                      min={getMinDateTime()}
                      onChange={(e) =>
                        setFormData({ ...formData, dueDate: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Score
                    </label>
                    <input
                      type="number"
                      value={formData.maxScore}
                      min={1}
                      max={1000}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          maxScore: parseInt(e.target.value) || 100,
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => {
                    setEditingAssignment(null)
                    setFormData({
                      title: '',
                      description: '',
                      dueDate: '',
                      maxScore: 100,
                      classId: '',
                    })
                  }}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpdateAssignment}
                  disabled={updateMutation.isPending}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        )}
      </Layout>
    </ProtectedRoute>
  )
}
