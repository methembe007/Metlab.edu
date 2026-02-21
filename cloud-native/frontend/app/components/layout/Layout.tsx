import { ReactNode } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Header } from './Header'
import { Footer } from './Footer'
import { Sidebar } from './Sidebar'
import { useAuth } from '~/contexts/AuthContext'

interface LayoutProps {
  children: ReactNode
  showSidebar?: boolean
  sidebarLinks?: Array<{ to: string; label: string; icon?: string }>
}

export function Layout({
  children,
  showSidebar = false,
  sidebarLinks = [],
}: LayoutProps) {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate({ to: '/' })
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Header
        userRole={isAuthenticated ? user?.role : undefined}
        userName={isAuthenticated ? user?.fullName : undefined}
        onLogout={isAuthenticated ? handleLogout : undefined}
      />
      
      <div className="flex flex-1">
        {showSidebar && user?.role && (
          <Sidebar links={sidebarLinks} userRole={user.role} />
        )}
        
        <main className="flex-1 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </div>
        </main>
      </div>
      
      <Footer />
    </div>
  )
}
