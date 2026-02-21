// Authentication service
import { apiClient } from './apiClient'

export interface User {
  id: string
  role: 'teacher' | 'student'
  fullName?: string
  email?: string
  teacherId?: string
  classIds?: string[]
}

export interface AuthResponse {
  token: string
  user_id: string
  role: 'teacher' | 'student'
  expires_at: number
}

export interface TeacherSignupData {
  email: string
  password: string
  full_name: string
  subject_area: string
}

export interface TeacherLoginData {
  email: string
  password: string
}

export interface StudentSigninData {
  teacher_name: string
  student_name: string
  signin_code: string
}

export const authService = {
  async teacherSignup(data: TeacherSignupData): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/auth/teacher/signup', data)
  },

  async teacherLogin(data: TeacherLoginData): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/auth/teacher/login', data)
  },

  async studentSignin(data: StudentSigninData): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/auth/student/signin', data)
  },

  saveToken(token: string): void {
    localStorage.setItem('auth_token', token)
  },

  getToken(): string | null {
    return localStorage.getItem('auth_token')
  },

  removeToken(): void {
    localStorage.removeItem('auth_token')
  },

  parseToken(token: string): User | null {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return {
        id: payload.sub,
        role: payload.role,
        teacherId: payload.teacher_id,
        classIds: payload.class_ids,
      }
    } catch {
      return null
    }
  },

  getCurrentUser(): User | null {
    const token = this.getToken()
    if (!token) return null
    return this.parseToken(token)
  },

  isAuthenticated(): boolean {
    const token = this.getToken()
    if (!token) return false

    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const expiresAt = payload.exp * 1000
      return Date.now() < expiresAt
    } catch {
      return false
    }
  },

  logout(): void {
    this.removeToken()
  },
}
