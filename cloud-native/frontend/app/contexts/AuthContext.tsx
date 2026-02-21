import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authService, User } from '~/lib/auth'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (token: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check for existing authentication on mount
    const token = authService.getToken()
    if (token && authService.isAuthenticated()) {
      const currentUser = authService.getCurrentUser()
      setUser(currentUser)
    }
    setIsLoading(false)
  }, [])

  const login = (token: string) => {
    authService.saveToken(token)
    const currentUser = authService.getCurrentUser()
    setUser(currentUser)
  }

  const logout = () => {
    authService.logout()
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
