import { useState, useEffect, useRef, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../api'
import TextInput from '../components/ui/TextInput'
import Pill from '../components/ui/Pill'
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

const locationIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

function MapClickHandler({ onMapClick }: { onMapClick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click: (e) => {
      onMapClick(e.latlng.lat, e.latlng.lng)
    },
  })
  return null
}

export default function CreateService() {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState({
    service_type: 'offer' as 'offer' | 'need',
    title: '',
    description: '',
    estimated_hours: 1,
    address: '',
    latitude: '',
    longitude: '',
    tags: [] as string[],
  })
  const [error, setError] = useState('')
  const [addressError, setAddressError] = useState('')
  const [addressSuggestions, setAddressSuggestions] = useState<any[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [mapMode, setMapMode] = useState(false)
  const addressInputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)

  // Fetch available tags
  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: async () => {
      const response = await api.get('/tags/')
      return response.data
    },
    enabled: isAuthenticated,
  })

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

    if (name === 'address' && value.length > 2) {
      debounceSearchAddress(value)
    } else if (name === 'address' && value.length === 0) {
      setAddressSuggestions([])
      setShowSuggestions(false)
    }
  }

  const debounceTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const debounceSearchAddress = (query: string) => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
    }
    debounceTimeoutRef.current = setTimeout(() => {
      searchAddress(query)
    }, 300)
  }

  const searchAddress = async (query: string) => {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&addressdetails=1`,
        {
          headers: {
            'User-Agent': 'TheHive-SWE573/1.0',
          },
        }
      )

      if (response.ok) {
        const data = await response.json()
        setAddressSuggestions(data)
        setShowSuggestions(true)
      }
    } catch (err) {
      console.error('Address search error:', err)
    }
  }

  const selectAddress = (suggestion: any) => {
    const roundedLat = parseFloat(suggestion.lat).toFixed(6)
    const roundedLng = parseFloat(suggestion.lon).toFixed(6)
    
    setFormData((prev) => ({
      ...prev,
      address: suggestion.display_name || suggestion.name || formData.address,
      latitude: roundedLat,
      longitude: roundedLng,
    }))
    setAddressSuggestions([])
    setShowSuggestions(false)
    setAddressError('')
  }

  const handleMapClick = (lat: number, lng: number) => {
    const roundedLat = lat.toFixed(6)
    const roundedLng = lng.toFixed(6)
    
    setFormData((prev) => ({
      ...prev,
      latitude: roundedLat,
      longitude: roundedLng,
    }))
    
    reverseGeocode(lat, lng)
  }

  const reverseGeocode = async (lat: number, lng: number) => {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&addressdetails=1`,
        {
          headers: {
            'User-Agent': 'TheHive-SWE573/1.0',
          },
        }
      )

      if (response.ok) {
        const data = await response.json()
        if (data.display_name) {
          setFormData((prev) => ({
            ...prev,
            address: data.display_name,
          }))
        }
      }
    } catch (err) {
      console.error('Reverse geocoding error:', err)
    }
  }

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        addressInputRef.current &&
        !addressInputRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  const toggleTag = (tagSlug: string) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags.includes(tagSlug)
        ? prev.tags.filter((t) => t !== tagSlug)
        : [...prev.tags, tagSlug],
    }))
  }

  const mapCenter: [number, number] = useMemo(() => {
    if (formData.latitude && formData.longitude) {
      return [parseFloat(formData.latitude), parseFloat(formData.longitude)]
    }
    return [41.0082, 28.9784]
  }, [formData.latitude, formData.longitude])

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
      // Round to 6 decimal places to match backend validation
      submitData.latitude = parseFloat(parseFloat(formData.latitude).toFixed(6))
      submitData.longitude = parseFloat(parseFloat(formData.longitude).toFixed(6))
    }

    // Include address if provided
    if (formData.address && formData.address.trim()) {
      submitData.address = formData.address.trim()
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
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Location (Optional)
              </label>
              <button
                type="button"
                onClick={() => setMapMode(!mapMode)}
                className="text-xs text-gray-600 hover:text-gray-900 underline"
              >
                {mapMode ? 'Use Address Search' : 'Click on Map Instead'}
              </button>
            </div>

            {!mapMode ? (
              <div className="space-y-2">
                <div className="relative">
                  <TextInput
                    ref={addressInputRef}
                    label=""
                    name="address"
                    value={formData.address}
                    onChange={handleChange}
                    onFocus={() => {
                      if (addressSuggestions.length > 0) {
                        setShowSuggestions(true)
                      }
                    }}
                    placeholder="Type address to search..."
                    className="flex-1"
                  />
                  {showSuggestions && addressSuggestions.length > 0 && (
                    <div
                      ref={suggestionsRef}
                      className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto"
                    >
                      {addressSuggestions.map((suggestion, index) => (
                        <button
                          key={index}
                          type="button"
                          onClick={() => selectAddress(suggestion)}
                          className="w-full text-left px-4 py-2 hover:bg-gray-100 border-b border-gray-200 last:border-b-0"
                        >
                          <div className="font-medium text-sm">{suggestion.display_name}</div>
                          {suggestion.address && (
                            <div className="text-xs text-gray-500 mt-1">
                              {suggestion.address.city || suggestion.address.town || ''}
                              {suggestion.address.country ? `, ${suggestion.address.country}` : ''}
                            </div>
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                {addressError && (
                  <p className="text-sm text-red-600">{addressError}</p>
                )}
                {formData.latitude && formData.longitude && (
                  <p className="text-sm text-green-600">
                    ✓ Location set: {parseFloat(formData.latitude).toFixed(6)}, {parseFloat(formData.longitude).toFixed(6)}
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-2">
                <div className="rounded-lg border border-gray-300 overflow-hidden h-[300px]">
                  <MapContainer
                    center={mapCenter}
                    zoom={13}
                    style={{ height: '100%', width: '100%', zIndex: 0 }}
                    scrollWheelZoom={true}
                  >
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    <MapClickHandler onMapClick={handleMapClick} />
                    {formData.latitude && formData.longitude && (
                      <Marker
                        position={[parseFloat(formData.latitude), parseFloat(formData.longitude)]}
                        icon={locationIcon}
                      />
                    )}
                  </MapContainer>
                </div>
                <p className="text-xs text-gray-600">
                  Click on the map to set location. {formData.latitude && formData.longitude && 'Location set!'}
                </p>
                {formData.latitude && formData.longitude && (
                  <p className="text-sm text-green-600">
                    ✓ Location: {parseFloat(formData.latitude).toFixed(6)}, {parseFloat(formData.longitude).toFixed(6)}
                  </p>
                )}
              </div>
            )}
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

