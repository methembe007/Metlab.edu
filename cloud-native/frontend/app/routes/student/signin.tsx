import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { Layout } from '~/components/layout'
import { authService } from '~/lib/auth'
import { useAuth } from '~/contexts/AuthContext'

export const Route = createFileRoute('/student/signin')({
  component: StudentSignin,
})

function StudentSignin() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [formData, setFormData] = useState({
    teacher_name: '',
    student_name: '',
    signin_code: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [isLoading, setIsLoading] = useState(false)
  const [apiError, setApiError] = useState('')

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.teacher_name) {
      newErrors.teacher_name = 'Teacher name is required'
    }

    if (!formData.student_name) {
      newErrors.student_name = 'Your name is required'
    }

    if (!formData.signin_code) {
      newErrors.signin_code = 'Sign-in code is required'
    } else if (formData.signin_code.length !== 8) {
      newErrors.signin_code = 'Sign-in code must be 8 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setApiError('')

    if (!validateForm()) {
      return
    }

    setIsLoading(true)

    try {
      const response = await authService.studentSignin({
        teacher_name: formData.teacher_name,
        student_name: formData.student_name,
        signin_code: formData.signin_code.toUpperCase(),
      })

      login(response.token)
      navigate({ to: '/student/dashboard' })
    } catch (error) {
      setApiError(
        error instanceof Error
          ? error.message
          : 'Sign-in failed. Please check your information and try again.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }))
    }
  }

  return (
    <Layout>
      <div className="max-w-md mx-auto">
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2 text-center">
            Student Sign In
          </h2>
          <p className="text-sm text-gray-600 mb-6 text-center">
            Enter the sign-in code provided by your teacher
          </p>

          {apiError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{apiError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="teacher_name"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Teacher's Name
              </label>
              <input
                type="text"
                id="teacher_name"
                name="teacher_name"
                value={formData.teacher_name}
                onChange={handleChange}
                placeholder="e.g., Ms. Smith"
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 ${
                  errors.teacher_name ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={isLoading}
              />
              {errors.teacher_name && (
                <p className="mt-1 text-sm text-red-600">{errors.teacher_name}</p>
              )}
            </div>

            <div>
              <label
                htmlFor="student_name"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Your Name
              </label>
              <input
                type="text"
                id="student_name"
                name="student_name"
                value={formData.student_name}
                onChange={handleChange}
                placeholder="e.g., John Doe"
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 ${
                  errors.student_name ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={isLoading}
              />
              {errors.student_name && (
                <p className="mt-1 text-sm text-red-600">{errors.student_name}</p>
              )}
            </div>

            <div>
              <label
                htmlFor="signin_code"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Sign-In Code
              </label>
              <input
                type="text"
                id="signin_code"
                name="signin_code"
                value={formData.signin_code}
                onChange={handleChange}
                placeholder="8-character code"
                maxLength={8}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 font-mono uppercase ${
                  errors.signin_code ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={isLoading}
              />
              {errors.signin_code && (
                <p className="mt-1 text-sm text-red-600">{errors.signin_code}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                Ask your teacher for the 8-character sign-in code
              </p>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-sm text-blue-800">
              <strong>First time signing in?</strong> Your account will be created
              automatically when you use a valid sign-in code.
            </p>
          </div>
        </div>
      </div>
    </Layout>
  )
}
