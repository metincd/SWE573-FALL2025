import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../lib/api'
import TextInput from '../components/ui/TextInput'
import Pill from '../components/ui/Pill'

export default function CreateService() {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState({
    service_type: 'offer' as 'offer' | 'need',
    title: '',
    description: '',
    estimated_hours: 1,
    latitude: '',
    longitude: '',
    tags: [] as string[],
  })
  const [error, setError] = useState('')

  // Fetch available tags
  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: async () => {
      const response = await api.get('/tags/')
      return response.data
    },
    enabled: isAuthenticated,
  })

  // Create service mutation
  const createServiceMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/services/', data)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['services'] })
      navigate(`/services/${data.id}`)
    },
    onError: (error: any) => {
      console.error('Create service error:', error.response?.data)
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
        setError(errors || 'Failed to create service')
      } else {
        setError(error.response?.data?.detail || error.response?.data?.message || 'Failed to create service')
      }
    },
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'estimated_hours' ? parseFloat(value) || 0 : value,
    }))
  }

  const toggleTag = (tagSlug: string) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags.includes(tagSlug)
        ? prev.tags.filter((t) => t !== tagSlug)
        : [...prev.tags, tagSlug],
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!formData.title || !formData.description) {
      setError('Title and description are required')
      return
    }

    const submitData: any = {
      service_type: formData.service_type,
      title: formData.title,
      description: formData.description,
      estimated_hours: formData.estimated_hours,
    }

    // Only include tags if there are any
    if (formData.tags.length > 0) {
      submitData.tags = formData.tags
    }

    if (formData.latitude && formData.longitude) {
      submitData.latitude = parseFloat(formData.latitude)
      submitData.longitude = parseFloat(formData.longitude)
    }

    createServiceMutation.mutate(submitData)
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">Please login to create a service</p>
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

  return (
    <div className="max-w-2xl mx-auto w-full">
      <button
        onClick={() => navigate(-1)}
        className="mb-4 text-sm text-gray-600 hover:text-gray-900"
      >
        ← Back
      </button>

      <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur p-6 shadow-sm">
        <h1 className="text-2xl font-bold mb-6">Create New Service</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Service Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Service Type
            </label>
            <div className="flex gap-2">
              <Pill
                active={formData.service_type === 'offer'}
                onClick={() => setFormData((prev) => ({ ...prev, service_type: 'offer' }))}
              >
                Offer (I'm providing)
              </Pill>
              <Pill
                active={formData.service_type === 'need'}
                onClick={() => setFormData((prev) => ({ ...prev, service_type: 'need' }))}
              >
                Need (I'm seeking)
              </Pill>
            </div>
          </div>

          {/* Title */}
          <TextInput
            label="Title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="e.g. Math Tutoring, Cooking Workshop..."
            required
          />

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Describe your service in detail..."
              required
              rows={5}
              className="w-full rounded-2xl border border-gray-300 bg-white/90 backdrop-blur px-4 py-3 outline-none ring-0 focus:border-gray-400 focus:outline-none"
            />
          </div>

          {/* Estimated Hours */}
          <TextInput
            label="Estimated Hours"
            name="estimated_hours"
            type="number"
            value={formData.estimated_hours.toString()}
            onChange={handleChange}
            placeholder="1"
            required
          />

          {/* Location (Optional) */}
          <div className="grid grid-cols-2 gap-4">
            <TextInput
              label="Latitude (optional)"
              name="latitude"
              type="number"
              value={formData.latitude}
              onChange={handleChange}
              placeholder="40.7128"
            />
            <TextInput
              label="Longitude (optional)"
              name="longitude"
              type="number"
              value={formData.longitude}
              onChange={handleChange}
              placeholder="-74.0060"
            />
          </div>

          {/* Tags */}
          {tagsData && tagsData.results && tagsData.results.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
              <div className="flex flex-wrap gap-2">
                {tagsData.results.map((tag: any) => (
                  <Pill
                    key={tag.slug || tag.id}
                    active={formData.tags.includes(tag.slug || tag.id)}
                    onClick={() => toggleTag(tag.slug || tag.id)}
                  >
                    #{tag.slug || tag.name}
                  </Pill>
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="text-sm text-red-600 whitespace-pre-line bg-red-50 p-3 rounded-lg border border-red-200">
              {error}
            </div>
          )}

          <div className="flex gap-2 pt-4">
            <button
              type="submit"
              disabled={createServiceMutation.isPending}
              className="flex-1 rounded-2xl bg-black text-white py-3 font-semibold hover:opacity-90 disabled:opacity-50"
            >
              {createServiceMutation.isPending ? 'Creating...' : 'Create Service'}
            </button>
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="px-6 py-3 rounded-2xl border border-gray-300 font-semibold hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

