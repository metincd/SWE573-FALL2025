import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../api'
import { useState, useMemo } from 'react'
import TextInput from '../components/ui/TextInput'
import ReportButton from '../components/ReportButton'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

const offerIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

const needIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

export default function ServiceDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { isAuthenticated, user } = useAuth()
  const queryClient = useQueryClient()
  const [requestMessage, setRequestMessage] = useState('')
  const [showRequestForm, setShowRequestForm] = useState(false)

  const { data: service, isLoading, error } = useQuery({
    queryKey: ['service', id],
    queryFn: async () => {
      const response = await api.get(`/services/${id}/`)
      return response.data
    },
    enabled: !!id,
  })

  const { data: reviewsData } = useQuery({
    queryKey: ['reviews', 'service', id],
    queryFn: async () => {
      const response = await api.get(`/reviews/?service=${id}`)
      return response.data
    },
    enabled: !!id && isAuthenticated,
  })

  const { data: myRequestsData } = useQuery({
    queryKey: ['service-requests', 'my'],
    queryFn: async () => {
      const response = await api.get('/service-requests/')
      return response.data
    },
    enabled: !!id && isAuthenticated && !!service,
  })

  const existingRequest = myRequestsData?.results?.find(
    (req: any) => req.service?.id === service?.id
  )

  const { data: discussionThread, refetch: refetchThread } = useQuery({
    queryKey: ['thread', service?.discussion_thread],
    queryFn: async () => {
      if (!service?.discussion_thread) return null
      const response = await api.get(`/threads/${service.discussion_thread}/`)
      return response.data
    },
    enabled: !!service?.discussion_thread,
  })

  const { data: postsData, refetch: refetchPosts } = useQuery({
    queryKey: ['posts', 'thread', discussionThread?.id],
    queryFn: async () => {
      if (!discussionThread?.id) return null
      const response = await api.get(`/posts/?thread=${discussionThread.id}`)
      return response.data
    },
    enabled: !!discussionThread?.id,
  })

  const [newPostBody, setNewPostBody] = useState('')

  const createPostMutation = useMutation({
    mutationFn: async (data: { thread: number; body: string }) => {
      const response = await api.post('/posts/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts', 'thread', discussionThread?.id] })
      queryClient.invalidateQueries({ queryKey: ['thread', service?.discussion_thread] })
      setNewPostBody('')
      refetchPosts()
      refetchThread()
    },
  })

  const hasLocation = service?.latitude && service?.longitude
  const mapCenter: [number, number] = useMemo(() => {
    if (hasLocation && service?.latitude && service?.longitude) {
      const lat = typeof service.latitude === 'string' ? parseFloat(service.latitude) : service.latitude
      const lng = typeof service.longitude === 'string' ? parseFloat(service.longitude) : service.longitude
      if (!isNaN(lat) && !isNaN(lng)) {
        return [lat, lng]
      }
    }
    return [41.0082, 28.9784]
  }, [service?.latitude, service?.longitude, hasLocation])

  const isOffer = service?.service_type === 'offer' || service?.service_type === 'OFFER'

  // Create service request mutation
  const createRequestMutation = useMutation({
    mutationFn: async (data: { service_id: number; message: string }) => {
      const response = await api.post('/service-requests/', data)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['service-requests'] })
      queryClient.invalidateQueries({ queryKey: ['service-requests', 'my'] })
      setShowRequestForm(false)
      setRequestMessage('')
      if (data?.conversation) {
        navigate(`/chat/${data.conversation}`)
      } else {
        alert('Service request sent successfully!')
      }
    },
    onError: (error: any) => {
      console.error('Service request error:', error.response?.data)
      const errorMessage = error.response?.data
      if (typeof errorMessage === 'object') {
        const errors = Object.entries(errorMessage)
          .map(([key, value]) => {
            if (Array.isArray(value)) {
              return `${key}: ${value.join(', ')}`
            }
            return `${key}: ${value}`
          })
          .join('\n')
        alert(errors || 'Failed to send request')
      } else {
        alert(error.response?.data?.detail || error.response?.data?.message || 'Failed to send request')
      }
    },
  })

  const handleRequestService = () => {
    if (!isAuthenticated) {
      const shouldLogin = window.confirm(
        'You need to be a member to request this service.\n\nClick "OK" to sign up or login.'
      )
      if (shouldLogin) {
        navigate('/login', { state: { returnTo: `/services/${id}`, message: 'Please login or sign up to request this service.' } })
      }
      return
    }

    if (user?.is_banned) {
      alert(`Your account is banned. Reason: ${user.ban_reason || 'No reason provided'}. You cannot request services.`)
      return
    }

    if (user?.is_suspended) {
      alert(`Your account is suspended. Reason: ${user.suspension_reason || 'No reason provided'}. You cannot request services.`)
      return
    }

    if (!service) return

    if ((service.service_type === 'need' || service.service_type === 'NEED') && service.owner.id === user?.id) {
      alert('You cannot request your own service')
      return
    }

    if ((service.service_type === 'offer' || service.service_type === 'OFFER') && service.owner.id === user?.id) {
      alert('You cannot request your own service')
      return
    }

    createRequestMutation.mutate({
      service_id: service.id,
      message: requestMessage || 'I would like to request this service.',
    })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Loading service details...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-2">Error loading service</p>
          <p className="text-sm text-gray-500 mb-4">{error instanceof Error ? error.message : 'Unknown error'}</p>
          <button
            onClick={() => navigate('/services')}
            className="text-sm text-gray-600 underline"
          >
            Back to Services
          </button>
        </div>
      </div>
    )
  }

  if (!service) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-2">Service not found</p>
          <button
            onClick={() => navigate('/services')}
            className="text-sm text-gray-600 underline"
          >
            Back to Services
          </button>
        </div>
      </div>
    )
  }

  const isOwner = service.owner?.id === user?.id
  const canRequest = isAuthenticated && !isOwner && !existingRequest && (service.status === 'active' || service.status === 'ACTIVE')

  return (
    <div className="max-w-4xl mx-auto w-full">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="mb-4 text-sm text-gray-600 hover:text-gray-900"
      >
        ← Back
      </button>

      {/* Service Header */}
      <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur p-6 shadow-sm mb-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span
                className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  (service.service_type === 'offer' || service.service_type === 'OFFER')
                    ? 'bg-green-100 text-green-700'
                    : 'bg-blue-100 text-blue-700'
                }`}
              >
                {(service.service_type === 'offer' || service.service_type === 'OFFER') ? 'OFFERING' : 'SEEKING'}
              </span>
              <span
                className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  (service.status === 'active' || service.status === 'ACTIVE')
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-700'
                }`}
              >
                {service.status?.toUpperCase() || 'UNKNOWN'}
              </span>
            </div>
            <div className="flex items-start justify-between mb-2">
              <h1 className="text-3xl font-bold">{service.title}</h1>
              <ReportButton contentType="service" objectId={service.id} />
            </div>
            <p className="text-gray-600 mb-4">{service.description}</p>
            
            {/* Tags - Below Description */}
            {service.tags && service.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {service.tags.map((tag: any) => {
                  const tagName = typeof tag === 'string' ? tag : tag.slug || tag.name || tag
                  const tagSlug = typeof tag === 'string' ? tag : tag.slug || tag.id
                  const tagUrl = typeof tag === 'object' && tag.wikidata_url ? tag.wikidata_url : null
                  return (
                    <span
                      key={typeof tag === 'string' ? tag : tag.slug || tag.id}
                      className="px-2 py-1 text-xs rounded-full border border-gray-300 bg-white/70 hover:bg-gray-100 cursor-pointer"
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate(`/services?tag=${encodeURIComponent(tagSlug)}`)
                      }}
                      title={`View all services with tag: ${tagName}`}
                    >
                      #{tagName}
                      {tagUrl && (
                        <span
                          className="ml-1 text-xs opacity-60"
                          onClick={(e) => {
                            e.stopPropagation()
                            window.open(tagUrl, '_blank')
                          }}
                          title={`View on Wikidata: ${tagUrl}`}
                        >
                          🔗
                        </span>
                      )}
                    </span>
                  )
                })}
              </div>
            )}
            
            {/* Service Image - Below Tags */}
            {service.image_url && (
              <div className="mb-4">
                <img
                  src={service.image_url}
                  alt={service.title}
                  className="w-full h-64 md:h-96 object-cover rounded-lg border border-gray-200"
                />
              </div>
            )}
          </div>
        </div>

        {/* Service Info */}
        <div className="grid md:grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-sm text-gray-500 mb-1">Owner</p>
            {service.owner?.id ? (
              <p
                onClick={() => navigate(`/users/${service.owner.id}`)}
                className="font-semibold hover:underline cursor-pointer text-gray-900"
              >
                {service.owner?.full_name || service.owner?.username || 'Unknown'}
              </p>
            ) : (
              <p className="font-semibold">
                {service.owner?.full_name || service.owner?.username || 'Unknown'}
              </p>
            )}
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">Estimated Hours</p>
            <p className="font-semibold">⏱️ {service.estimated_hours} hours</p>
          </div>
        </div>

        {/* Request Service Button */}
        {existingRequest && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm text-blue-800">
            You already have a <strong>{existingRequest.status}</strong> request for this service.
          </div>
        )}
        {!isAuthenticated && (service.status === 'active' || service.status === 'ACTIVE') && (
          <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-sm font-semibold text-amber-800 mb-2">
              You need to be a member to request this service.
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => navigate('/login', { state: { returnTo: `/services/${id}` } })}
                className="px-4 py-2 bg-black text-white rounded-lg hover:opacity-90 text-sm font-medium"
              >
                Login
              </button>
              <button
                onClick={() => navigate('/register', { state: { returnTo: `/services/${id}` } })}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm font-medium"
              >
                Sign Up
              </button>
            </div>
          </div>
        )}
        {canRequest && (
          <div className="mt-4">
            {!showRequestForm ? (
              <button
                onClick={() => setShowRequestForm(true)}
                className="w-full md:w-auto px-6 py-3 rounded-xl bg-black text-white font-semibold hover:opacity-90"
              >
                Request Service
              </button>
            ) : (
              <div className="space-y-3">
                <TextInput
                  label="Message (optional)"
                  name="message"
                  value={requestMessage}
                  onChange={(e) => setRequestMessage(e.target.value)}
                  placeholder="Add a message to your request..."
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleRequestService}
                    disabled={createRequestMutation.isPending}
                    className="px-6 py-3 rounded-xl bg-black text-white font-semibold hover:opacity-90 disabled:opacity-50"
                  >
                    {createRequestMutation.isPending ? 'Sending...' : 'Send Request'}
                  </button>
                  <button
                    onClick={() => {
                      setShowRequestForm(false)
                      setRequestMessage('')
                    }}
                    className="px-6 py-3 rounded-xl border border-gray-300 font-semibold hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {isOwner && (
          <div className="mt-4 p-3 bg-amber-50 rounded-lg text-sm text-amber-800">
            This is your service. You can manage requests from your profile.
          </div>
        )}
      </div>

      {/* Map Section */}
      {hasLocation && (
        <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur overflow-hidden shadow-sm mb-6">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-xl font-bold">Location</h2>
            <p className="text-sm text-gray-600 mt-1">Service location on map</p>
          </div>
          <div className="h-[400px] w-full">
            <MapContainer
              center={mapCenter}
              zoom={15}
              style={{ height: '100%', width: '100%', zIndex: 0 }}
              scrollWheelZoom={true}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <Marker
                position={mapCenter}
                icon={isOffer ? offerIcon : needIcon}
              >
                <Popup>
                  <div className="p-2">
                    <h3 className="font-semibold text-sm mb-1">{service.title}</h3>
                    {service.owner?.id ? (
                      <p
                        onClick={() => navigate(`/users/${service.owner.id}`)}
                        className="text-xs text-gray-600 mb-2 hover:underline cursor-pointer font-medium"
                      >
                        {service.owner?.full_name || service.owner?.username || 'Unknown'}
                      </p>
                    ) : (
                      <p className="text-xs text-gray-600 mb-2">
                        {service.owner?.full_name || service.owner?.username || 'Unknown'}
                      </p>
                    )}
                    <span className={`px-2 py-0.5 rounded-full text-xs ${
                      isOffer ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                    }`}>
                      {isOffer ? 'OFFER' : 'NEED'}
                    </span>
                  </div>
                </Popup>
              </Marker>
            </MapContainer>
          </div>
        </div>
      )}

      {/* Discussions Section */}
      {discussionThread && (
        <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur p-6 shadow-sm mb-6">
          <h2 className="text-xl font-bold mb-4">Discussions</h2>
          <p className="text-sm text-gray-600 mb-4">
            Public discussion about this service. Everyone can participate.
          </p>
          
          {/* Posts List */}
          {postsData?.results && postsData.results.length > 0 && (
            <div className="space-y-4 mb-6">
              {postsData.results.map((post: any) => (
                <div key={post.id} className="border-b border-gray-200 pb-4 last:border-0">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      {post.author?.id ? (
                        <p
                          onClick={() => navigate(`/users/${post.author.id}`)}
                          className="font-semibold hover:underline cursor-pointer text-gray-900"
                        >
                          {post.author?.full_name || post.author?.username || 'Anonymous'}
                        </p>
                      ) : (
                        <p className="font-semibold">
                          {post.author?.full_name || post.author?.username || 'Anonymous'}
                        </p>
                      )}
                      <p className="text-sm text-gray-500">
                        {new Date(post.created_at).toLocaleDateString()} at{' '}
                        {new Date(post.created_at).toLocaleTimeString()}
                      </p>
                    </div>
                    {isAuthenticated && post.author?.id !== user?.id && (
                      <ReportButton contentType="post" objectId={post.id} className="ml-2" />
                    )}
                  </div>
                  <p className="text-gray-700 whitespace-pre-wrap">{post.body}</p>
                </div>
              ))}
            </div>
          )}

          {/* New Post Form */}
          {isAuthenticated && (
            <div className="space-y-3">
              <TextInput
                label="Add a comment"
                name="post_body"
                value={newPostBody}
                onChange={(e) => setNewPostBody(e.target.value)}
                placeholder="Share your thoughts about this service..."
                multiline
                rows={3}
              />
              <button
                onClick={() => {
                  if (user?.is_banned) {
                    alert(`Your account is banned. Reason: ${user.ban_reason || 'No reason provided'}. You cannot post messages.`)
                    return
                  }

                  if (user?.is_suspended) {
                    alert(`Your account is suspended. Reason: ${user.suspension_reason || 'No reason provided'}. You cannot post messages.`)
                    return
                  }

                  if (discussionThread?.id && newPostBody.trim()) {
                    createPostMutation.mutate({
                      thread: discussionThread.id,
                      body: newPostBody.trim(),
                    })
                  }
                }}
                disabled={createPostMutation.isPending || !newPostBody.trim() || user?.is_banned || user?.is_suspended}
                className="px-6 py-2 rounded-xl bg-black text-white font-semibold hover:opacity-90 disabled:opacity-50"
              >
                {createPostMutation.isPending ? 'Posting...' : 'Post Comment'}
              </button>
            </div>
          )}

          {!isAuthenticated && (
            <p className="text-sm text-gray-500 italic">
              Please log in to participate in discussions.
            </p>
          )}
        </div>
      )}

      {/* Reviews Section */}
      {reviewsData && reviewsData.results && reviewsData.results.length > 0 && (
        <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur p-6 shadow-sm">
          <h2 className="text-xl font-bold mb-4">Reviews</h2>
          <div className="space-y-4">
            {reviewsData.results.map((review: any) => (
              <div key={review.id} className="border-b border-gray-200 pb-4 last:border-0">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    {review.reviewer?.id ? (
                      <p
                        onClick={() => navigate(`/users/${review.reviewer.id}`)}
                        className="font-semibold hover:underline cursor-pointer text-gray-900"
                      >
                        {review.reviewer?.full_name || review.reviewer?.username || 'Anonymous'}
                      </p>
                    ) : (
                      <p className="font-semibold">
                        {review.reviewer?.full_name || review.reviewer?.username || 'Anonymous'}
                      </p>
                    )}
                    <p className="text-sm text-gray-500">
                      {new Date(review.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="text-amber-500">⭐ {review.rating}/5</div>
                </div>
                <p className="text-gray-700">{review.comment}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

