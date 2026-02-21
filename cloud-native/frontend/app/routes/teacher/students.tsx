import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { Layout } from '~/components/layout'
import { ProtectedRoute } from '~/components/auth'
import { apiClient } from '~/lib/apiClient'
import { authService } from '~/lib/auth'
import type { Student } from '~/types'

export const Route = createFileRoute('/teacher/students')({
  component: TeacherStudents,
})

interface SigninCodeResponse {
  code: string
  expires_at: number
}

function TeacherStudents() {
  const [generatedCode, setGeneratedCode] = useState<string | null>(null)
  const [expiresAt, setExpiresAt] = useState<number | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copySuccess, setCopySuccess] = useState(false)
  const [students, setStudents] = useState<Student[]>([])
  const [isLoadingStudents, setIsLoadingStudents] = useState(false)

  const sidebarLinks = [
    { to: '/teacher/dashboard', label: 'Dashboard', icon: '📊' },
    { to: '/teacher/students', label: 'Students', icon: '👥' },
    { to: '/teacher/videos', label: 'Videos', icon: '🎥' },
    { to: '/teacher/pdfs', label: 'PDFs', icon: '📄' },
    { to: '/teacher/homework', label: 'Homework', icon: '📝' },
    { to: '/teacher/analytics', label: 'Analytics', icon: '📈' },
  ]

  const handleGenerateCode = async () => {
    setIsGenerating(true)
    setError(null)
    setCopySuccess(false)

    try {
      const user = authService.getCurrentUser()
      if (!user) {
        throw new Error('User not authenticated')
      }

      // For now, we'll use a default class_id. In a full implementation,
      // the teacher would select which class to generate a code for
      const response = await apiClient.post<SigninCodeResponse>(
        '/auth/codes/generate',
        {
          teacher_id: user.id,
          class_id: user.classIds?.[0] || 'default-class',
        }
      )

      setGeneratedCode(response.code)
      setExpiresAt(response.expires_at)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate code')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleCopyCode = async () => {
    if (!generatedCode) return

    try {
      await navigator.clipboard.writeText(generatedCode)
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 2000)
    } catch (err) {
      setError('Failed to copy code to clipboard')
    }
  }

  const loadStudents = async () => {
    setIsLoadingStudents(true)
    setError(null)

    try {
      const user = authService.getCurrentUser()
      if (!user) {
        throw new Error('User not authenticated')
      }

      // Fetch students for this teacher
      const response = await apiClient.get<Student[]>(
        `/students?teacher_id=${user.id}`
      )
      setStudents(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load students')
    } finally {
      setIsLoadingStudents(false)
    }
  }

  const formatExpiryDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <ProtectedRoute requiredRole="teacher" redirectTo="/teacher/login">
      <Layout showSidebar={true} sidebarLinks={sidebarLinks}>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-6">
            Student Management
          </h1>

          {/* Generate Signin Code Section */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Generate Student Signin Code
            </h2>
            <p className="text-gray-600 mb-4">
              Generate a unique signin code for students to register for your
              class. Each code is valid for 30 days.
            </p>

            <button
              onClick={handleGenerateCode}
              disabled={isGenerating}
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isGenerating ? 'Generating...' : 'Generate New Code'}
            </button>

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-800 text-sm">{error}</p>
              </div>
            )}

            {generatedCode && (
              <div className="mt-6 p-6 bg-green-50 border-2 border-green-200 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-800 mb-2">
                  Your Signin Code
                </h3>
                <div className="flex items-center gap-4 mb-3">
                  <div className="flex-1 bg-white p-4 rounded-lg border-2 border-green-300">
                    <p className="text-3xl font-mono font-bold text-center text-gray-900 tracking-wider">
                      {generatedCode}
                    </p>
                  </div>
                  <button
                    onClick={handleCopyCode}
                    className="bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center gap-2"
                  >
                    {copySuccess ? (
                      <>
                        <span>✓</span>
                        <span>Copied!</span>
                      </>
                    ) : (
                      <>
                        <span>📋</span>
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>
                {expiresAt && (
                  <p className="text-sm text-gray-600">
                    Expires: {formatExpiryDate(expiresAt)}
                  </p>
                )}
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
                  <p className="text-sm text-blue-800">
                    <strong>Instructions for students:</strong> Students should
                    use this code along with your name and their name to sign
                    in to the platform.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Registered Students Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-800">
                Registered Students
              </h2>
              <button
                onClick={loadStudents}
                disabled={isLoadingStudents}
                className="bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
              >
                {isLoadingStudents ? 'Loading...' : 'Refresh List'}
              </button>
            </div>

            {students.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 mb-2">
                  No students registered yet.
                </p>
                <p className="text-sm text-gray-400">
                  Generate a signin code and share it with your students to get
                  started.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Signin Code Used
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Registered On
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Last Login
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {students.map((student) => (
                      <tr key={student.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            {student.fullName}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-mono text-gray-600">
                            {student.signinCode}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-600">
                            {new Date(student.createdAt).toLocaleDateString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-600">
                            {student.lastLogin
                              ? new Date(student.lastLogin).toLocaleDateString()
                              : 'Never'}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </Layout>
    </ProtectedRoute>
  )
}
