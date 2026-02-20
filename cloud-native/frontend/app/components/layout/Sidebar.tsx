import { Link } from '@tanstack/react-router'

interface SidebarLink {
  to: string
  label: string
  icon?: string
}

interface SidebarProps {
  links: SidebarLink[]
  userRole: 'teacher' | 'student'
}

export function Sidebar({ links, userRole }: SidebarProps) {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen">
      <div className="p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 capitalize">
          {userRole} Dashboard
        </h2>
        <nav className="space-y-1">
          {links.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              activeProps={{
                className: 'bg-blue-50 text-blue-700 font-medium',
              }}
            >
              {link.icon && <span className="mr-2">{link.icon}</span>}
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </aside>
  )
}
