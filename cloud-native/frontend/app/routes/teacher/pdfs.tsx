import { createFileRoute } from '@tanstack/react-router'
import { useState, useRef, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Layout } from '~/components/layout'
import { ProtectedRoute } from '~/components/auth'
import { apiClient } from '~/lib/apiClient'
import type { PDF } from '~/types'

export const Route = createFileRoute('/teacher/pdfs')({
  component: TeacherPDFs,
})

interface UploadProgress {
  fileName: string
  progress: number
  status: 'uploading' | 'complete' | 'error'
  error?: string
}

interface PDFFormData {
  title: string
  description: string
  classId: string
}

function TeacherPDFs() {
  const queryClient = useQueryClient()
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null)
  const [formData, setFormData] = useState<PDFFormData>({
    title: '',
    description: '',
    classId: '',
  })
  const [editingPDF, setEditingPDF] = useState<PDF | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const sidebarLinks = [
    { to: '/teacher/dashboard', label: 'Dashboard', icon: '📊' },
    { to: '/teacher/students', label: 'Students', icon: '👥' },
    { to: '/teacher/videos', label: 'Videos', icon: '🎥' },
    { to: '/teacher/pdfs', label: 'PDFs', icon: '📄' },
    { to: '/teacher/homework', label: 'Homework', icon: '📝' },
    { to: '/teacher/analytics', label: 'Analytics', icon: '📈' },
  ]

  // Fetch PDFs
  const { data: pdfs = [], isLoading } = useQuery<PDF[]>({
    queryKey: ['pdfs'],
    queryFn: () => apiClient.get<PDF[]>('/pdfs'),
  })

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (data: { file: File; metadata: PDFFormData }) => {
      setUploadProgress({
        fileName: data.file.name,
        progress: 0,
        status: 'uploading',
      })

      const response = await apiClient.uploadFile<PDF>('/pdfs', data.file, {
        title: data.metadata.title,
        description: data.metadata.description,
        classId: data.metadata.classId,
      })

      setUploadProgress({
        fileName: data.file.name,
        progress: 100,
        status: 'complete',
      })

      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pdfs'] })
      setTimeout(() => {
        setUploadProgress(null)
        setShowUploadModal(false)
        setSelectedFile(null)
        setFormData({ title: '', description: '', classId: '' })
      }, 1500)
    },
    onError: (error: Error) => {
      setUploadProgress((prev) =>
        prev
          ? { ...prev, status: 'error', error: error.message }
          : null
      )
    },
  })

  // Update PDF metadata mutation
  const updateMutation = useMutation({
    mutationFn: async (data: { id: string; updates: Partial<PDFFormData> }) => {
      return apiClient.put<PDF>(`/pdfs/${data.id}`, data.updates)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pdfs'] })
      setEditingPDF(null)
    },
  })

  // Delete PDF mutation
  const deleteMutation = useMutation({
    mutationFn: async (pdfId: string) => {
      return apiClient.delete(`/pdfs/${pdfId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pdfs'] })
    },
  })

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    const pdfFile = files.find((file) => file.type === 'application/pdf')

    if (pdfFile) {
      if (pdfFile.size > 50 * 1024 * 1024) {
        alert('File size must be less than 50MB')
        return
      }
      setSelectedFile(pdfFile)
      setFormData((prev) => ({
        ...prev,
        title: pdfFile.name.replace(/\.[^/.]+$/, ''),
      }))
    } else {
      alert('Please upload a valid PDF file')
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.size > 50 * 1024 * 1024) {
        alert('File size must be less than 50MB')
        return
      }
      setSelectedFile(file)
      setFormData((prev) => ({
        ...prev,
        title: file.name.replace(/\.[^/.]+$/, ''),
      }))
    }
  }

  const handleUpload = () => {
    if (!selectedFile || !formData.title || !formData.classId) {
      alert('Please fill in all required fields')
      return
    }

    uploadMutation.mutate({
      file: selectedFile,
      metadata: formData,
    })
  }

  const handleUpdatePDF = () => {
    if (!editingPDF) return

    updateMutation.mutate({
      id: editingPDF.id,
      updates: {
        title: formData.title,
        description: formData.description,
      },
    })
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  return (
    <ProtectedRoute requiredRole="teacher" redirectTo="/teacher/login">
      <Layout showSidebar={true} sidebarLinks={sidebarLinks}>
        <div>
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold text-gray-900">
              PDF Management
            </h1>
            <button
              onClick={() => setShowUploadModal(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              + Upload PDF
            </button>
          </div>

          {/* Upload Progress */}
          {uploadProgress && (
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h3 className="text-lg font-semibold mb-4">
                {uploadProgress.status === 'uploading' && 'Uploading...'}
                {uploadProgress.status === 'complete' && 'Upload Complete!'}
                {uploadProgress.status === 'error' && 'Upload Failed'}
              </h3>
              <div className="mb-2">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>{uploadProgress.fileName}</span>
                  <span>{uploadProgress.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      uploadProgress.status === 'error'
                        ? 'bg-red-600'
                        : uploadProgress.status === 'complete'
                          ? 'bg-green-600'
                          : 'bg-blue-600'
                    }`}
                    style={{ width: `${uploadProgress.progress}%` }}
                  />
                </div>
              </div>
              {uploadProgress.error && (
                <p className="text-red-600 text-sm mt-2">
                  {uploadProgress.error}
                </p>
              )}
            </div>
          )}

          {/* PDF List */}
          <div className="bg-white rounded-lg shadow-md p-6">
            {isLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-gray-600 mt-4">Loading PDFs...</p>
              </div>
            ) : pdfs.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-600">
                  No PDFs uploaded yet. Click "Upload PDF" to get started.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {pdfs.map((pdf) => (
                  <div
                    key={pdf.id}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0">
                        <div className="w-16 h-16 bg-red-100 rounded-lg flex items-center justify-center">
                          <span className="text-3xl">📄</span>
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-gray-900 mb-1">
                          {pdf.title}
                        </h3>
                        {pdf.description && (
                          <p className="text-sm text-gray-600 mb-2">
                            {pdf.description}
                          </p>
                        )}
                        <div className="flex items-center gap-4 text-xs text-gray-500">
                          <span>{formatFileSize(pdf.fileSizeBytes)}</span>
                          <span>•</span>
                          <span>
                            Uploaded {new Date(pdf.createdAt).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setEditingPDF(pdf)
                            setFormData({
                              title: pdf.title,
                              description: pdf.description,
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
                                'Are you sure you want to delete this PDF?'
                              )
                            ) {
                              deleteMutation.mutate(pdf.id)
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

        {/* Upload Modal */}
        {showUploadModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Upload PDF
              </h2>

              {/* Drag and Drop Area */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  isDragging
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="application/pdf"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <div className="text-6xl mb-4">📄</div>
                {selectedFile ? (
                  <div>
                    <p className="text-lg font-semibold text-gray-900">
                      {selectedFile.name}
                    </p>
                    <p className="text-sm text-gray-600">
                      {formatFileSize(selectedFile.size)}
                    </p>
                    <p className="text-sm text-blue-600 mt-2">
                      Click to change file
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-lg font-semibold text-gray-900 mb-2">
                      Drag and drop your PDF here
                    </p>
                    <p className="text-sm text-gray-600">
                      or click to browse
                    </p>
                    <p className="text-xs text-gray-500 mt-2">
                      Supports PDF files (max 50MB)
                    </p>
                  </div>
                )}
              </div>

              {/* Form Fields */}
              {selectedFile && (
                <div className="mt-6 space-y-4">
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
                      placeholder="Enter PDF title"
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
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Enter PDF description"
                    />
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
              )}

              {/* Action Buttons */}
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowUploadModal(false)
                    setSelectedFile(null)
                    setFormData({ title: '', description: '', classId: '' })
                  }}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  disabled={
                    !selectedFile ||
                    !formData.title ||
                    !formData.classId ||
                    uploadMutation.isPending
                  }
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Edit Modal */}
        {editingPDF && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Edit PDF
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
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => {
                    setEditingPDF(null)
                    setFormData({ title: '', description: '', classId: '' })
                  }}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpdatePDF}
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
