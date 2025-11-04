import { Link, Outlet } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Layout() {
  const { isAuthenticated, logout } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="border-b bg-white">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/" className="text-lg font-semibold">
            The Hive
          </Link>
          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <>
                <Link
                  to="/services"
                  className="text-sm text-gray-700 hover:text-gray-900"
                >
                  Services
                </Link>
                <button
                  onClick={logout}
                  className="text-sm text-gray-700 hover:text-gray-900"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link
                to="/login"
                className="text-sm text-gray-700 hover:text-gray-900"
              >
                Login
              </Link>
            )}
          </div>
        </div>
      </nav>
      <main>
        <Outlet />
      </main>
    </div>
  )
}

