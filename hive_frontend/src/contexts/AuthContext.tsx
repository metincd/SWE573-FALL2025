import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi, userApi } from '../lib/api'

interface User {
  id: number
  username: string
  email: string
  full_name?: string
  // Profile bilgileri
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
        username: profileData.user.username,
        email: profileData.user.email,
        full_name: profileData.user.full_name,
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
    // Sayfa yüklendiğinde token kontrolü ve user bilgisini al
    const token = localStorage.getItem('access_token')
    if (token) {
      fetchUser().finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (username: string, password: string) => {
    try {
      const response = await authApi.login(username, password)
      const { access, refresh } = response.data
      localStorage.setItem('access_token', access)
      localStorage.setItem('refresh_token', refresh)
      // Login sonrası user bilgisini al
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

