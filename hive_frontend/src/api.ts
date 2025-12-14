import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://ec2-52-59-134-106.eu-central-1.compute.amazonaws.com:8000/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/token/', { email, password }),
  refreshToken: (refresh: string) =>
    api.post('/token/refresh/', { refresh }),
}

export const healthCheck = () => api.get('/health/')

export const userApi = {
  getMe: () => api.get('/me/'),
  updateMe: (data: any) => api.patch('/me/', data),
}

export const timeAccountApi = {
  getMyAccount: () => api.get('/time-accounts/'),
}

