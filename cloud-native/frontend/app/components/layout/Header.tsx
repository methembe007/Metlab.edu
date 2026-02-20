import { Link } from '@tanstack/react-router'

interface HeaderProps {
  userRole?: 'teacher' | 'student'
  userName?: string
  onLogout?: () => void
}

export function Header({ userRole, userName, onLogout }: HeaderProps) {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center">
              <h1 className="text-2xl font-bold text-blue-600">Metlab.edu</h1>
            </Link>
          </div>

          <nav className="flex items-center space-x-4">
            {userRole && userName ? (
              <>
                <span className="text-sm text-gray-700">
                  Welcome, <span className="font-medium">{userName}</span>
                </span>
                <span className="text-xs text-gray-500 px-2 py-1 bg-gray-100 rounded">
                  {userRole}
                </span>
                {onLogout && (
                  <button
                    onClick={onLogout}
                    className="text-sm text-red-600 hover:text-red-700 font-medium"
                  >
                    Logout
                  </button>
                )}
              </>
            ) : (
              <>
                <Link
                  to="/teacher/login"
                  className="text-sm text-gray-700 hover:text-gray-900"
                >
                  Teacher Login
                </Link>
                <Link
                  to="/student/signin"
                  className="text-sm text-white bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg"
                >
                  Student Sign In
                </Link>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  )
}
