import { createFileRoute } from '@tanstack/react-router'
import { Layout } from '~/components/layout'

export const Route = createFileRoute('/')({
  component: Home,
})

function Home() {
  return (
    <Layout>
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to Metlab.edu
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Cloud-Native Educational Platform
          </p>
          <p className="text-gray-500 mb-8 max-w-2xl mx-auto">
            A modern learning management system built with microservices architecture,
            enabling teachers to create engaging content and students to learn at their own pace.
          </p>
          <div className="space-x-4">
            <a
              href="/teacher/login"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Teacher Login
            </a>
            <a
              href="/student/signin"
              className="inline-block px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Student Sign In
            </a>
          </div>
        </div>
      </div>
    </Layout>
  )
}
