import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api'
import { useAuth } from '../contexts/AuthContext'
import { useState, useMemo, useEffect } from 'react'
import Card from '../components/ui/Card'
import Pill from '../components/ui/Pill'
import ReportButton from '../components/ReportButton'

export default function UserProfile() {
  const { userId } = useParams<{ userId: string }>()
  const navigate = useNavigate()
  const { isAuthenticated, user } = useAuth()
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'closed'>('all')

  const { data: profile, isLoading, error } = useQuery({
    queryKey: ['public-profile', userId],
    queryFn: async () => {
      const response = await api.get(`/profiles/${userId}/`)
      return response.data
    },
    enabled: !!userId && isAuthenticated,
  })

  const { data: userServicesData, isLoading: servicesLoading } = useQuery({
    queryKey: ['user-services', userId],
    queryFn: async () => {
      const response = await api.get(`/services/?owner=${userId}`)
      return response.data.results || []
    },
    enabled: !!userId && isAuthenticated,
  })

  const filteredServices = useMemo(() => {
    if (!userServicesData) return []
    if (statusFilter === 'all') return userServicesData
    if (statusFilter === 'closed') {
      return userServicesData.filter((service: any) => {
        const status = (service.status || '').toLowerCase().trim()
        return status === 'inactive' || status === 'completed'
      })
    }
    return userServicesData.filter((service: any) => {
      const status = (service.status || '').toLowerCase().trim()
      return status === statusFilter
    })
  }, [userServicesData, statusFilter])

  const stats = useMemo(() => {
    if (!userServicesData) return { total: 0, active: 0, inactive: 0, completed: 0 }
    return {
      total: userServicesData.length,
      active: userServicesData.filter((s: any) => {
        const status = (s.status || '').toLowerCase().trim()
        return status === 'active'
      }).length,
      inactive: userServicesData.filter((s: any) => {
        const status = (s.status || '').toLowerCase().trim()
        return status === 'inactive'
      }).length,
      completed: userServicesData.filter((s: any) => {
        const status = (s.status || '').toLowerCase().trim()
        return status === 'completed'
      }).length,
    }
  }, [userServicesData])

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
    }
  }, [isAuthenticated, navigate])

  if (!isAuthenticated) {
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
            <div className="flex items-start justify-between mb-2">
              <div>
                <h1 className="text-2xl font-bold">
                  {profile.display_name || profile.user?.full_name || profile.user?.username}
                </h1>
                {isMe && (
                  <p className="text-xs text-amber-700 font-semibold mt-1">(This is you)</p>
                )}
              </div>
              {profile.user?.id && !isMe && (
                <ReportButton contentType="user" objectId={profile.user.id} />
              )}
            </div>
            <p className="text-sm text-gray-500 mb-4">{profile.user?.email}</p>
            {profile.bio && <p className="text-gray-700 whitespace-pre-wrap">{profile.bio}</p>}
          </div>
        </div>

        {/* Stats */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h3 className="font-semibold mb-3">Service Statistics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Total Services</p>
              <p className="font-bold text-lg">{stats.total}</p>
            </div>
            <div>
              <p className="text-gray-500">Active</p>
              <p className="font-semibold text-green-600">{stats.active}</p>
            </div>
            <div>
              <p className="text-gray-500">Closed</p>
              <p className="font-semibold text-gray-600">{stats.inactive + stats.completed}</p>
            </div>
            <div>
              <p className="text-gray-500">Completed</p>
              <p className="font-semibold text-blue-600">{stats.completed}</p>
            </div>
          </div>
        </div>
      </div>

      {/* User's Services */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Services</h2>
          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <Pill
              active={statusFilter === 'all'}
              onClick={() => setStatusFilter('all')}
            >
              All ({stats.total})
            </Pill>
            <Pill
              active={statusFilter === 'active'}
              onClick={() => setStatusFilter('active')}
            >
              Active ({stats.active})
            </Pill>
            <Pill
              active={statusFilter === 'closed'}
              onClick={() => setStatusFilter('closed')}
            >
              Closed ({stats.inactive + stats.completed})
            </Pill>
          </div>
        </div>

        {servicesLoading ? (
          <p className="text-gray-600">Loading services...</p>
        ) : filteredServices.length === 0 ? (
          <div className="rounded-lg border bg-white/70 backdrop-blur p-8 text-center">
            <p className="text-gray-600">
              {statusFilter === 'all' 
                ? 'No services yet' 
                : `No ${statusFilter} services`}
            </p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredServices.map((service: any) => (
              <Card
                key={service.id}
                title={service.title}
                subtitle={`${(service.service_type === 'offer' || service.service_type === 'OFFER') ? 'Offering' : 'Seeking'} • ${service.status?.toUpperCase() || 'UNKNOWN'}`}
                ownerName={profile.display_name || profile.user?.full_name || profile.user?.username || 'User'}
                desc={service.description}
                hours={service.estimated_hours}
                tags={(service.tags || []).map((t: any) =>
                  typeof t === 'string' ? t : t.slug || t.name || ''
                )}
                onTagClick={(tag) => navigate(`/services?tag=${encodeURIComponent(tag)}`)}
                onOwnerClick={(ownerId) => navigate(`/users/${ownerId}`)}
                ownerId={profile.user?.id}
                cta="View Details"
                onClick={() => navigate(`/services/${service.id}`)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}





