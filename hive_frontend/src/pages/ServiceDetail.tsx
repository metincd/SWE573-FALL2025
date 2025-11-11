import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../lib/api'
import Card from '../components/ui/Card'
import { useState } from 'react'
import TextInput from '../components/ui/TextInput'

export default function ServiceDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { isAuthenticated, user } = useAuth()
  const queryClient = useQueryClient()
  const [requestMessage, setRequestMessage] = useState('')
  const [showRequestForm, setShowRequestForm] = useState(false)

  // Fetch service details
  const { data: service, isLoading, error } = useQuery({
    queryKey: ['service', id],
    queryFn: async () => {
      const response = await api.get(`/services/${id}/`)
      return response.data
    },
    enabled: !!id,
  })

  // Fetch reviews for this service
  const { data: reviewsData } = useQuery({
    queryKey: ['reviews', 'service', id],
    queryFn: async () => {
      const response = await api.get(`/reviews/?service=${id}`)
      return response.data
    },
    enabled: !!id && isAuthenticated,
  })

  // Check if user already has a request for this service
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

  // Create service request mutation
  const createRequestMutation = useMutation({
    mutationFn: async (data: { service_id: number; message: string }) => {
      const response = await api.post('/service-requests/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['service-requests'] })
      queryClient.invalidateQueries({ queryKey: ['service-requests', 'my'] })
      setShowRequestForm(false)
      setRequestMessage('')
      alert('Service request sent successfully!')
    },
    onError: (error: any) => {
      console.error('Service request error:', error.response?.data)
      const errorMessage = error.response?.data
      if (typeof errorMessage === 'object') {
        // Handle validation errors
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
      navigate('/login')
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

  if (error || !service) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-2">Service not found</p>
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

  const isOwner = service.owner.id === user?.id
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
            <h1 className="text-3xl font-bold mb-2">{service.title}</h1>
            <p className="text-gray-600 mb-4">{service.description}</p>
          </div>
        </div>

        {/* Service Info */}
        <div className="grid md:grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-sm text-gray-500 mb-1">Owner</p>
            <p className="font-semibold">
              {service.owner?.full_name || service.owner?.username || 'Unknown'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">Estimated Hours</p>
            <p className="font-semibold">⏱️ {service.estimated_hours} hours</p>
          </div>
        </div>

        {/* Tags */}
        {service.tags && service.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {service.tags.map((tag: any) => (
              <span
                key={typeof tag === 'string' ? tag : tag.slug || tag.id}
                className="px-2 py-1 text-xs rounded-full border border-gray-300 bg-white/70"
              >
                #{typeof tag === 'string' ? tag : tag.slug || tag.name || tag}
              </span>
            ))}
          </div>
        )}

        {/* Request Service Button */}
        {existingRequest && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm text-blue-800">
            You already have a <strong>{existingRequest.status}</strong> request for this service.
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

      {/* Reviews Section */}
      {reviewsData && reviewsData.results && reviewsData.results.length > 0 && (
        <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur p-6 shadow-sm">
          <h2 className="text-xl font-bold mb-4">Reviews</h2>
          <div className="space-y-4">
            {reviewsData.results.map((review: any) => (
              <div key={review.id} className="border-b border-gray-200 pb-4 last:border-0">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-semibold">
                      {review.reviewer?.full_name || review.reviewer?.username || 'Anonymous'}
                    </p>
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

