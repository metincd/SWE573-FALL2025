import { useState, useEffect } from 'react'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import TextInput from '../components/ui/TextInput'
import PasswordInput from '../components/ui/PasswordInput'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    if (location.state?.message) {
      setError('')
    }
  }, [location])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(username, password)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto w-full">
      <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur p-6 shadow-sm">
        <h2 className="text-xl font-bold">Login</h2>
        <p className="text-sm text-gray-600 mt-1">Join the community, discover services.</p>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <TextInput
            name="username"
            label="Email"
            type="email"
            placeholder="example@email.com"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="email"
          />

          <PasswordInput
            name="password"
            label="Password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          {error && <div className="text-sm text-red-600">{error}</div>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-2xl bg-black text-white py-3 font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="text-sm text-gray-600 mt-4">
          Don't have an account?{' '}
          <button onClick={() => navigate('/register')} className="underline">
            Sign up now
          </button>
        </div>
      </div>
    </div>
  )
}
