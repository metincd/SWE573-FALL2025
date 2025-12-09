import { useState, useRef, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import TextInput from '../components/ui/TextInput'
import PasswordInput from '../components/ui/PasswordInput'
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

const userLocationIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-yellow.png',
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

export default function Register() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    password2: '',
    first_name: '',
    last_name: '',
    address: '',
    latitude: '',
    longitude: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [mapMode, setMapMode] = useState(false)
  const [addressSuggestions, setAddressSuggestions] = useState<any[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const navigate = useNavigate()
  const addressInputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)
  const debounceTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData({
      ...formData,
      [name]: value,
    })

    if (name === 'address' && value.length > 2) {
      debounceSearchAddress(value)
    } else if (name === 'address' && value.length === 0) {
      setAddressSuggestions([])
      setShowSuggestions(false)
    }
  }

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
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
    }
  }, [])

  const mapCenter: [number, number] = useMemo(() => {
    if (formData.latitude && formData.longitude) {
      return [parseFloat(formData.latitude), parseFloat(formData.longitude)]
    }
    return [41.0082, 28.9784]
  }, [formData.latitude, formData.longitude])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    if (formData.password !== formData.password2) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    try {
      const registerData: any = {
        email: formData.email,
        password: formData.password,
        password2: formData.password2,
        first_name: formData.first_name,
        last_name: formData.last_name,
      }

      if (formData.latitude && formData.longitude) {
        registerData.latitude = formData.latitude
        registerData.longitude = formData.longitude
        if (formData.address) {
          registerData.address = formData.address
        }
      }

      await api.post('/register/', registerData)
      navigate('/login', { state: { message: 'Registration successful! Please login.' } })
    } catch (err: any) {
      const errorMessage = err.response?.data
      if (typeof errorMessage === 'object') {
        const errors = Object.values(errorMessage).flat()
        setError(errors.join(', '))
      } else {
        setError(err.response?.data?.message || 'Registration failed')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto w-full">
      <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur p-6 shadow-sm">
        <h2 className="text-xl font-bold">Sign Up</h2>
        <p className="text-sm text-gray-600 mt-1">Fair exchange with TimeBank.</p>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <TextInput
              label="First Name"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              placeholder="First Name"
            />
            <TextInput
              label="Last Name"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              placeholder="Last Name"
            />
          </div>

          <TextInput
            label="Email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="example@email.com"
            autoComplete="email"
          />

          <PasswordInput
            label="Password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="At least 8 characters"
          />

          <PasswordInput
            label="Confirm Password"
            name="password2"
            value={formData.password2}
            onChange={handleChange}
            placeholder="Re-enter your password"
          />

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
                  />
                  {showSuggestions && addressSuggestions.length > 0 && (
                    <div
                      ref={suggestionsRef}
                      className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto"
                    >
                      {addressSuggestions.map((suggestion, idx) => (
                        <div
                          key={idx}
                          onClick={() => selectAddress(suggestion)}
                          className="px-4 py-2 hover:bg-gray-100 cursor-pointer border-b last:border-b-0"
                        >
                          <div className="font-medium text-sm">{suggestion.display_name}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="h-64 rounded-lg overflow-hidden border border-gray-300">
                <MapContainer
                  center={mapCenter}
                  zoom={13}
                  style={{ height: '100%', width: '100%' }}
                >
                  <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                  <MapClickHandler onMapClick={handleMapClick} />
                  {formData.latitude && formData.longitude && (
                    <Marker
                      position={[parseFloat(formData.latitude), parseFloat(formData.longitude)]}
                      icon={userLocationIcon}
                    />
                  )}
                </MapContainer>
              </div>
            )}
            {formData.latitude && formData.longitude && (
              <p className="text-xs text-gray-500 mt-1">
                Location: {formData.address || `${formData.latitude}, ${formData.longitude}`}
              </p>
            )}
          </div>

          {error && <div className="text-sm text-red-600">{error}</div>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-2xl bg-black text-white py-3 font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <div className="text-sm text-gray-600 mt-4">
          Already have an account?{' '}
          <button onClick={() => navigate('/login')} className="underline">
            Login
          </button>
        </div>
      </div>
    </div>
  )
}
