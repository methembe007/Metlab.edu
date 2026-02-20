import { ReactNode } from 'react'
import { Header } from './Header'
import { Footer } from './Footer'
import { Sidebar } from './Sidebar'

interface LayoutProps {
  children: ReactNode
  showSidebar?: boolean
  sidebarLinks?: Array<{ to: string; label: string; icon?: string }>
  userRole?: 'teacher' | 'student'
  userName?: string
  onLogout?: () => void
}

export function Layout({
  children,
  showSidebar = false,
  sidebarLinks = [],
  userRole,
  userName,
  onLogout,
}: LayoutProps) {
  return (
    <div className="flex flex-col min-h-screen">
      <Header userRole={userRole} userName={userName} onLogout={onLogout} />
      
      <div className="flex flex-1">
        {showSidebar && userRole && (
          <Sidebar links={sidebarLinks} userRole={userRole} />
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
