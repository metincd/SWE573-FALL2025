import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { authApi, userApi } from '../api'

interface User {
  id: number
  email: string
  full_name?: string
  is_staff?: boolean
  is_banned?: boolean
  is_suspended?: boolean
  ban_reason?: string
  suspension_reason?: string
  profile?: {
    display_name?: string
    bio?: string
    avatar_url?: string
    latitude?: number
    longitude?: number
  }
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  loading: boolean
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchUser = async () => {
    try {
      const response = await userApi.getMe()
      const profileData = response.data
      setUser({
        id: profileData.user.id,
        email: profileData.user.email,
        full_name: profileData.user.full_name,
        is_staff: profileData.user.is_staff,
        is_banned: profileData.user.is_banned,
        is_suspended: profileData.user.is_suspended,
        ban_reason: profileData.user.ban_reason,
        suspension_reason: profileData.user.suspension_reason,
        profile: {
          display_name: profileData.display_name,
          bio: profileData.bio,
          avatar_url: profileData.avatar_url,
          latitude: profileData.latitude,
          longitude: profileData.longitude,
        },
      })
    } catch (error) {
      console.error('Failed to fetch user:', error)
      setUser(null)
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      fetchUser().finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (email: string, password: string) => {
    try {
      const response = await authApi.login(email, password)
      const { access, refresh } = response.data
      localStorage.setItem('access_token', access)
      localStorage.setItem('refresh_token', refresh)
      await fetchUser()
    } catch (error) {
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
  }

  const refreshUser = async () => {
    await fetchUser()
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        logout,
        loading,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

