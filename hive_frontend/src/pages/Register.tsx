import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import TextInput from '../components/ui/TextInput'
import PasswordInput from '../components/ui/PasswordInput'

export default function Register() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    password2: '',
    first_name: '',
    last_name: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    if (formData.password !== formData.password2) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    try {
      await api.post('/register/', formData)
      navigate('/login', { state: { message: 'Registration successful! Please login.' } })
    } catch (err: any) {
      const errorMessage = err.response?.data
      if (typeof errorMessage === 'object') {
        const errors = Object.values(errorMessage).flat()
        setError(errors.join(', '))
      } else {
        setError(err.response?.data?.message || 'Registration failed')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto w-full">
      <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur p-6 shadow-sm">
        <h2 className="text-xl font-bold">Sign Up</h2>
        <p className="text-sm text-gray-600 mt-1">Fair exchange with TimeBank.</p>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <TextInput
              label="First Name"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              placeholder="First Name"
            />
            <TextInput
              label="Last Name"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              placeholder="Last Name"
            />
          </div>

          <TextInput
            label="Email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="example@email.com"
            autoComplete="email"
          />

          <PasswordInput
            label="Password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="At least 8 characters"
          />

          <PasswordInput
            label="Confirm Password"
            name="password2"
            value={formData.password2}
            onChange={handleChange}
            placeholder="Re-enter your password"
          />

          {error && <div className="text-sm text-red-600">{error}</div>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-2xl bg-black text-white py-3 font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <div className="text-sm text-gray-600 mt-4">
          Already have an account?{' '}
          <button onClick={() => navigate('/login')} className="underline">
            Login
          </button>
        </div>
      </div>
    </div>
  )
}
