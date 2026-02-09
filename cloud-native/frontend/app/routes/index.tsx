import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: Home,
})

function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Metlab.edu
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Cloud-Native Educational Platform
        </p>
        <div className="space-x-4">
          <a
            href="/teacher/login"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Teacher Login
          </a>
          <a
            href="/student/signin"
            className="inline-block px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            Student Sign In
          </a>
        </div>
      </div>
    </div>
  )
}
