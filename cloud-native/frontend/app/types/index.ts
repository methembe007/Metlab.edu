// User types
export interface User {
  id: string
  email?: string
  fullName: string
  role: 'teacher' | 'student'
  createdAt: string
  lastLogin?: string
}

export interface Teacher extends User {
  role: 'teacher'
  subjectArea?: string
  verified: boolean
}

export interface Student extends User {
  role: 'student'
  teacherId: string
  signinCode: string
}

// Auth types
export interface AuthResponse {
  token: string
  userId: string
  role: 'teacher' | 'student'
  expiresAt: number
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface TeacherSignupData {
  email: string
  password: string
  fullName: string
  subjectArea: string
}

export interface StudentSigninData {
  teacherName: string
  studentName: string
  signinCode: string
}

// Video types
export interface Video {
  id: string
  title: string
  description: string
  durationSeconds: number
  thumbnailUrl: string
  status: 'uploading' | 'processing' | 'ready' | 'failed'
  createdAt: string
}

export interface VideoView {
  id: string
  videoId: string
  studentId: string
  startedAt: string
  lastPositionSeconds: number
  totalWatchSeconds: number
  completed: boolean
}

// Homework types
export interface Assignment {
  id: string
  title: string
  description: string
  dueDate: string
  maxScore: number
  submissionCount: number
  createdAt: string
}

export interface Submission {
  id: string
  assignmentId: string
  studentId: string
  fileName: string
  fileSizeBytes: number
  submittedAt: string
  isLate: boolean
  status: 'submitted' | 'graded' | 'returned'
  score?: number
  feedback?: string
}

// PDF types
export interface PDF {
  id: string
  title: string
  description: string
  fileSizeBytes: number
  createdAt: string
}

// Study Group types
export interface StudyGroup {
  id: string
  name: string
  description: string
  memberCount: number
  maxMembers: number
  createdAt: string
}

// Chat types
export interface ChatRoom {
  id: string
  name: string
  createdBy: string
  createdAt: string
}

export interface ChatMessage {
  id: string
  senderId: string
  senderName: string
  messageText: string
  imageUrl?: string
  sentAt: string
}

// Analytics types
export interface DailyLoginCount {
  date: string
  count: number
}

export interface LoginStats {
  dailyCounts: DailyLoginCount[]
  totalLogins: number
  averagePerWeek: number
}

// API Error type
export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}
