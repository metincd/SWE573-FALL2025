import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Home() {
  const { isAuthenticated, logout, user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Loading...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-xl mx-auto">
        <div className="rounded-2xl border bg-white shadow-sm p-8">
          <h1 className="text-2xl font-semibold mb-2">The Hive</h1>
          <p className="text-gray-600 mb-6">Community-Oriented Service Platform</p>
          
          {isAuthenticated && user && (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Hoş geldin,</p>
              <p className="font-semibold">{user.full_name || user.username}</p>
              <p className="text-xs text-gray-500 mt-1">{user.email}</p>
            </div>
          )}

          <div className="grid gap-3">
            {isAuthenticated ? (
              <>
                <Link
                  to="/services"
                  className="inline-flex items-center justify-center rounded-lg bg-gray-900 text-white px-4 py-2 text-sm font-medium hover:bg-gray-800"
                >
                  Explore Services
                </Link>
                <button
                  onClick={logout}
                  className="inline-flex items-center justify-center rounded-lg border px-4 py-2 text-sm font-medium hover:bg-gray-50"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/register"
                  className="inline-flex items-center justify-center rounded-lg border px-4 py-2 text-sm font-medium hover:bg-gray-50"
                >
                  Sign Up
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center justify-center rounded-lg bg-gray-900 text-white px-4 py-2 text-sm font-medium hover:bg-gray-800"
                >
                  Login
                </Link>
                <Link
                  to="/services"
                  className="inline-flex items-center justify-center rounded-lg border px-4 py-2 text-sm font-medium hover:bg-gray-50"
                >
                  Explore Services
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

