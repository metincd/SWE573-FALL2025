import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Layout() {
  const { isAuthenticated, logout, user } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gradient-to-b from-amber-100 via-white to-amber-50">
      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex flex-col group">
            <div className="text-3xl font-black tracking-tight bg-gradient-to-r from-amber-600 via-amber-500 to-amber-600 bg-clip-text text-transparent">
              The HIVE
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs font-semibold text-amber-700">Help</span>
              <span className="text-amber-500">•</span>
              <span className="text-xs font-semibold text-amber-700">Inspire</span>
              <span className="text-amber-500">•</span>
              <span className="text-xs font-semibold text-amber-700">Volunteer</span>
              <span className="text-amber-500">•</span>
              <span className="text-xs font-semibold text-amber-700">Exchange</span>
            </div>
          </Link>
          <div className="flex items-center gap-2">
            {!isAuthenticated ? (
              <>
                <button
                  onClick={() => navigate('/login')}
                  className="px-3 py-2 text-sm rounded-xl hover:bg-white/60"
                >
                  Login
                </button>
                <button
                  onClick={() => navigate('/register')}
                  className="px-3 py-2 text-sm rounded-xl bg-black text-white"
                >
                  Sign Up
                </button>
              </>
            ) : (
              <>
                <div className="text-sm text-gray-700 mr-1">
                  Hello,{' '}
                  <span className="font-semibold">
                    {user?.profile?.display_name || user?.full_name || user?.username}
                  </span>
                </div>
                <Link
                  to="/services"
                  className="px-3 py-2 text-sm rounded-xl hover:bg-white/60"
                >
                  Services
                </Link>
                <Link
                  to="/profile"
                  className="px-3 py-2 text-sm rounded-xl hover:bg-white/60"
                >
                  Profile
                </Link>
                <button
                  onClick={logout}
                  className="px-3 py-2 text-sm rounded-xl hover:bg-white/60"
                >
                  Logout
                </button>
              </>
            )}
          </div>
        </div>
      </div>
      <main className="px-4 pb-24">
        <Outlet />
      </main>
      <footer className="max-w-6xl mx-auto px-4 py-10 text-center text-xs text-gray-500">
        <div>© {new Date().getFullYear()} The Hive. Built for SWE573.</div>
      </footer>
    </div>
  )
}

