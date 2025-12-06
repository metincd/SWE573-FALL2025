import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api'
import { useAuth } from '../contexts/AuthContext'

export default function UserProfile() {
  const { userId } = useParams<{ userId: string }>()
  const navigate = useNavigate()
  const { isAuthenticated, user } = useAuth()

  const { data: profile, isLoading, error } = useQuery({
    queryKey: ['public-profile', userId],
    queryFn: async () => {
      const response = await api.get(`/profiles/${userId}/`)
      return response.data
    },
    enabled: !!userId && isAuthenticated,
  })

  if (!isAuthenticated) {
    navigate('/login')
    return null
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Loading profile...</p>
      </div>
    )
  }

  if (error || !profile) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-2">Error loading profile</p>
          <p className="text-sm text-gray-500 mb-4">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-gray-600 underline"
          >
            Go Back
          </button>
        </div>
      </div>
    )
  }

  const isMe = profile.user?.id === user?.id

  return (
    <div className="max-w-3xl mx-auto w-full">
      <button
        onClick={() => navigate(-1)}
        className="mb-4 text-sm text-gray-600 hover:text-gray-900"
      >
        ← Back
      </button>

      <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur p-6 shadow-sm mb-6">
        <div className="flex items-start gap-4">
          {/* Avatar */}
          <div className="flex-shrink-0">
            {profile.avatar_url ? (
              <img
                src={profile.avatar_url}
                alt="Profile"
                className="w-20 h-20 rounded-full object-cover border-2 border-gray-200"
                onError={(e) => {
                  e.currentTarget.style.display = 'none'
                }}
              />
            ) : (
              <div className="w-20 h-20 rounded-full bg-gray-200 flex items-center justify-center border-2 border-gray-300">
                <span className="text-2xl font-bold text-gray-500">
                  {(profile.display_name || profile.user?.full_name || profile.user?.username || 'U')[0].toUpperCase()}
                </span>
              </div>
            )}
          </div>
          <div className="flex-1">
            <h1 className="text-2xl font-bold mb-2">
              {profile.display_name || profile.user?.full_name || profile.user?.username}
            </h1>
            {isMe && (
              <p className="text-xs text-amber-700 font-semibold mb-2">(This is you)</p>
            )}
            <p className="text-sm text-gray-500 mb-4">{profile.user?.email}</p>
            {profile.bio && <p className="text-gray-700 whitespace-pre-wrap">{profile.bio}</p>}
          </div>
        </div>
      </div>
    </div>
  )
}





