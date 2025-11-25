import React, { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../api'
import Card from '../components/ui/Card'
import TextInput from '../components/ui/TextInput'

export default function Profile() {
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  const [isEditing, setIsEditing] = useState(false)
  const [editData, setEditData] = useState({
    display_name: '',
    bio: '',
  })

  // Fetch user profile
  const { data: profileData, isLoading: profileLoading } = useQuery({
    queryKey: ['profile', 'me'],
    queryFn: async () => {
      const response = await api.get('/me/')
      return response.data
    },
    enabled: isAuthenticated,
  })

  // Update editData when profileData changes
  React.useEffect(() => {
    if (profileData) {
      setEditData({
        display_name: profileData.display_name || '',
        bio: profileData.bio || '',
      })
    }
  }, [profileData])

  // Fetch time account
  const { data: timeAccountData } = useQuery({
    queryKey: ['time-account'],
    queryFn: async () => {
      const response = await api.get('/time-accounts/')
      return response.data[0]
    },
    enabled: isAuthenticated,
  })

  // Fetch user's services
  const { data: myServicesData } = useQuery({
    queryKey: ['services', 'my'],
    queryFn: async () => {
      const response = await api.get('/services/')
      const allServices = response.data.results || []
      return allServices.filter((s: any) => s.owner.id === user?.id)
    },
    enabled: isAuthenticated && !!user,
  })

  // Fetch service requests (both sent and received)
  const { data: requestsData, refetch: refetchRequests } = useQuery({
    queryKey: ['service-requests', 'my'],
    queryFn: async () => {
      const response = await api.get('/service-requests/')
      return response.data
    },
    enabled: isAuthenticated,
  })

  const handleUpdateProfile = async () => {
    try {
      await api.patch('/me/', editData)
      setIsEditing(false)
      // Invalidate to refetch
      window.location.reload()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to update profile')
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">Please login to view your profile</p>
          <button
            onClick={() => navigate('/login')}
            className="px-4 py-2 bg-black text-white rounded-lg"
          >
            Login
          </button>
        </div>
      </div>
    )
  }

  if (profileLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Loading profile...</p>
      </div>
    )
  }

  const profile = (profileData as any) || {}
  const timeAccount = (timeAccountData as any) || {}
  const myServices = myServicesData || []
  const requests = requestsData?.results || []

  // Separate requests: sent vs received
  const sentRequests = requests.filter((r: any) => {
    const requesterId = typeof r.requester === 'object' ? r.requester?.id : r.requester
    return requesterId === user?.id
  })
  
  const receivedRequests = requests.filter((r: any) => {
    // Service should now be an object with owner nested
    if (typeof r.service === 'object' && r.service?.owner) {
      const ownerId = typeof r.service.owner === 'object' ? r.service.owner.id : r.service.owner
      const matches = ownerId === user?.id
      if (matches) {
        console.log('Found received request:', r)
      }
      return matches
    }
    // Debug: log if service structure is unexpected
    if (r.service) {
      console.log('Service structure:', r.service, 'User ID:', user?.id)
    }
    return false
  })

  // Debug logs
  console.log('All requests:', requests)
  console.log('User ID:', user?.id)
  console.log('Received requests count:', receivedRequests.length)

  return (
    <div className="max-w-6xl mx-auto w-full">
      <h1 className="text-2xl font-bold mb-6">My Profile</h1>

      {/* Profile Info */}
      <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur p-6 shadow-sm mb-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h2 className="text-xl font-bold mb-2">
              {profile.display_name || user?.full_name || user?.username || 'User'}
            </h2>
            <p className="text-gray-600 mb-2">{user?.email}</p>
            {profile.bio && <p className="text-gray-700">{profile.bio}</p>}
          </div>
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="px-4 py-2 rounded-xl border border-gray-300 hover:bg-gray-50"
          >
            {isEditing ? 'Cancel' : 'Edit'}
          </button>
        </div>

        {/* Edit Form */}
        {isEditing && (
          <div className="space-y-4 pt-4 border-t">
            <TextInput
              label="Display Name"
              name="display_name"
              value={editData.display_name}
              onChange={(e) => setEditData({ ...editData, display_name: e.target.value })}
              placeholder="Your display name"
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Bio</label>
              <textarea
                name="bio"
                value={editData.bio}
                onChange={(e) => setEditData({ ...editData, bio: e.target.value })}
                placeholder="Tell us about yourself..."
                rows={3}
                className="w-full rounded-2xl border border-gray-300 bg-white/90 backdrop-blur px-4 py-3 outline-none ring-0 focus:border-gray-400 focus:outline-none"
              />
            </div>
            <button
              onClick={handleUpdateProfile}
              className="px-6 py-2 rounded-xl bg-black text-white font-semibold hover:opacity-90"
            >
              Save Changes
            </button>
          </div>
        )}

        {/* Time Account */}
        <div className="mt-4 pt-4 border-t">
          <h3 className="font-semibold mb-2">Time Account</h3>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Balance</p>
              <p className="font-bold text-lg">
                {Number(timeAccount.balance || 0).toFixed(1)} hours
              </p>
            </div>
            <div>
              <p className="text-gray-500">Total Earned</p>
              <p className="font-semibold">{Number(timeAccount.total_earned || 0).toFixed(1)}h</p>
            </div>
            <div>
              <p className="text-gray-500">Total Spent</p>
              <p className="font-semibold">{Number(timeAccount.total_spent || 0).toFixed(1)}h</p>
            </div>
          </div>
        </div>
      </div>

      {/* My Services */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">My Services</h2>
          <button
            onClick={() => navigate('/services/create')}
            className="px-4 py-2 rounded-xl bg-black text-white text-sm font-semibold hover:opacity-90"
          >
            + Create Service
          </button>
        </div>
        {myServices.length === 0 ? (
          <div className="rounded-lg border bg-white/70 backdrop-blur p-8 text-center">
            <p className="text-gray-600 mb-4">You haven't created any services yet</p>
            <button
              onClick={() => navigate('/services/create')}
              className="px-4 py-2 rounded-xl bg-black text-white text-sm font-semibold hover:opacity-90"
            >
              Create Your First Service
            </button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {myServices.map((service: any) => (
              <Card
                key={service.id}
                title={service.title}
                subtitle={`${(service.service_type === 'offer' || service.service_type === 'OFFER') ? 'Offering' : 'Seeking'} • ${
                  service.status
                }`}
                desc={service.description}
                hours={service.estimated_hours}
                tags={(service.tags || []).map((t: any) =>
                  typeof t === 'string' ? t : t.slug || t.name || ''
                )}
                cta="View Details"
                onClick={() => navigate(`/services/${service.id}`)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Service Requests */}
      <div>
        <h2 className="text-xl font-bold mb-4">Service Requests</h2>
        <div className="grid md:grid-cols-2 gap-6">
          {/* Received Requests */}
          <div>
            <h3 className="font-semibold mb-3">Received ({receivedRequests.length})</h3>
            {receivedRequests.length === 0 ? (
              <p className="text-sm text-gray-500">No requests received</p>
            ) : (
              <div className="space-y-3">
                {receivedRequests.map((request: any) => (
                  <div
                    key={request.id}
                    className="rounded-lg border bg-white/70 backdrop-blur p-4"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="font-semibold">
                          {request.requester?.full_name || request.requester?.username}
                        </p>
                        <p className="text-sm text-gray-600">{request.service?.title}</p>
                      </div>
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          request.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-700'
                            : request.status === 'accepted'
                              ? 'bg-green-100 text-green-700'
                              : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {request.status}
                      </span>
                    </div>
                    {request.message && (
                      <p className="text-sm text-gray-700 mb-2">{request.message}</p>
                    )}
                    {request.status === 'pending' && (
                      <div className="flex gap-2 mt-2">
                        <button
                          onClick={async () => {
                            try {
                              await api.post(`/service-requests/${request.id}/set_status/`, {
                                status: 'accepted',
                              })
                              refetchRequests()
                              queryClient.invalidateQueries({ queryKey: ['service-requests'] })
                            } catch (error: any) {
                              console.error('Accept request error:', error.response?.data)
                              const errorMsg = error.response?.data?.detail || error.response?.data?.message || 'Failed to accept request'
                              alert(errorMsg)
                            }
                          }}
                          className="px-3 py-1 text-xs rounded-lg bg-green-600 text-white hover:bg-green-700"
                        >
                          Accept
                        </button>
                        <button
                          onClick={async () => {
                            try {
                              await api.post(`/service-requests/${request.id}/set_status/`, {
                                status: 'rejected',
                              })
                              refetchRequests()
                            } catch (error: any) {
                              alert(error.response?.data?.detail || 'Failed to reject request')
                            }
                          }}
                          className="px-3 py-1 text-xs rounded-lg bg-red-600 text-white hover:bg-red-700"
                        >
                          Reject
                        </button>
                      </div>
                    )}
                    {request.status === 'accepted' && (
                      <div className="flex gap-2 mt-2">
                        <button
                          onClick={async () => {
                            if (!confirm('Mark this service as completed? Time will be transferred automatically.')) {
                              return
                            }
                            try {
                              await api.post(`/service-requests/${request.id}/set_status/`, {
                                status: 'completed',
                              })
                              alert('Service marked as completed! Time has been transferred.')
                              // Refetch requests
                              refetchRequests()
                              // Invalidate and refetch time account to show updated balance
                              await queryClient.invalidateQueries({ queryKey: ['time-account'] })
                              await queryClient.refetchQueries({ queryKey: ['time-account'] })
                            } catch (error: any) {
                              alert(error.response?.data?.detail || 'Failed to complete service')
                            }
                          }}
                          className="px-3 py-1 text-xs rounded-lg bg-blue-600 text-white hover:bg-blue-700"
                        >
                          Mark as Completed
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Sent Requests */}
          <div>
            <h3 className="font-semibold mb-3">Sent ({sentRequests.length})</h3>
            {sentRequests.length === 0 ? (
              <p className="text-sm text-gray-500">No requests sent</p>
            ) : (
              <div className="space-y-3">
                {sentRequests.map((request: any) => (
                  <div
                    key={request.id}
                    className="rounded-lg border bg-white/70 backdrop-blur p-4"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="font-semibold">{request.service?.title}</p>
                        <p className="text-sm text-gray-600">
                          {request.service?.owner?.full_name || request.service?.owner?.username}
                        </p>
                      </div>
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          request.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-700'
                            : request.status === 'accepted'
                              ? 'bg-green-100 text-green-700'
                              : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {request.status}
                      </span>
                    </div>
                    {request.message && (
                      <p className="text-sm text-gray-700">{request.message}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

