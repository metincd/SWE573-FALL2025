import { useMemo, useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../api'
import TextInput from '../components/ui/TextInput'
import Pill from '../components/ui/Pill'
import Card from '../components/ui/Card'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
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

const demoTags = [
  'cooking',
  'tutoring',
  'companionship',
  'errands',
  'storytelling',
  'gardening',
  'music',
  'coding',
  'elderly-care',
]

const userLocationIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-yellow.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

function ChangeMapView({ center, zoom }: { center: [number, number], zoom: number }) {
  const map = useMap()
  useEffect(() => {
    map.setView(center, zoom)
  }, [map, center, zoom])
  return null
}

export default function Home() {
  const { isAuthenticated, user, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState<'offers' | 'needs'>('offers')
  const [query, setQuery] = useState('')
  const [activeTags, setActiveTags] = useState<string[]>([])
  const [sortOrder, setSortOrder] = useState<'newest' | 'oldest' | 'nearest' | 'farthest'>('newest')
  const [showClosed, setShowClosed] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 5

  const { data: servicesData, isLoading: servicesLoading } = useQuery({
    queryKey: ['services'],
    queryFn: async () => {
      const response = await api.get('/services/')
      return response.data
    },
    enabled: true,
  })

  const { data: timeAccountData, refetch: refetchTimeAccount } = useQuery({
    queryKey: ['time-account'],
    queryFn: async () => {
      const response = await api.get('/time-accounts/')
      return response.data[0]
    },
    enabled: isAuthenticated,
  })

  const { data: userProfile, isLoading: profileLoading } = useQuery({
    queryKey: ['profile', 'me'],
    queryFn: async () => {
      const response = await api.get('/me/')
      return response.data
    },
    enabled: isAuthenticated,
    staleTime: 0,
    gcTime: 0,
  })

  useEffect(() => {
    const handleFocus = () => {
      if (isAuthenticated) {
        refetchTimeAccount()
      }
    }
    window.addEventListener('focus', handleFocus)
    return () => window.removeEventListener('focus', handleFocus)
  }, [isAuthenticated, refetchTimeAccount])

  const { offers, needs, closedOffers, closedNeeds } = useMemo(() => {
    if (!servicesData?.results) return { offers: [], needs: [], closedOffers: [], closedNeeds: [] }

    const activeServices = servicesData.results.filter((s: any) => s.status === 'active')
    const closedServices = servicesData.results.filter((s: any) => s.status === 'inactive' || s.status === 'completed')
    
    const offersList = activeServices.filter((s: any) => s.service_type === 'offer' || s.service_type === 'OFFER')
    const needsList = activeServices.filter((s: any) => s.service_type === 'need' || s.service_type === 'NEED')
    const closedOffersList = closedServices.filter((s: any) => s.service_type === 'offer' || s.service_type === 'OFFER')
    const closedNeedsList = closedServices.filter((s: any) => s.service_type === 'need' || s.service_type === 'NEED')

    return { offers: offersList, needs: needsList, closedOffers: closedOffersList, closedNeeds: closedNeedsList }
  }, [servicesData])

  const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
    const R = 6371
    const dLat = (lat2 - lat1) * Math.PI / 180
    const dLon = (lon2 - lon1) * Math.PI / 180
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2)
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
    return R * c
  }

  const filtered = useMemo(() => {
    const activeList = mode === 'offers' ? offers : needs
    const closedList = mode === 'offers' ? closedOffers : closedNeeds
    const list = showClosed ? closedList : activeList

    let result = list.filter((item: any) => {
      const matchesQuery = query
        ? (
            item.title +
            ' ' +
            item.description +
            ' ' +
            (item.tags || []).map((t: any) => (typeof t === 'string' ? t : t.slug || t.name || '')).join(' ')
          ).toLowerCase().includes(query.toLowerCase())
        : true

      const itemTagSlugs = (item.tags || []).map((t: any) =>
        typeof t === 'string' ? t : t.slug || t.name || ''
      )
      const matchesTags =
        activeTags.length === 0 || activeTags.every((t) => itemTagSlugs.includes(t))

      return matchesQuery && matchesTags
    })

    if (userProfile?.latitude && userProfile?.longitude) {
      const userLat = parseFloat(userProfile.latitude)
      const userLng = parseFloat(userProfile.longitude)
      
      result = result.map((item: any) => {
        if (item.latitude && item.longitude) {
          const itemLat = parseFloat(item.latitude)
          const itemLng = parseFloat(item.longitude)
          const distance = calculateDistance(userLat, userLng, itemLat, itemLng)
          return { ...item, distance }
        }
        return { ...item, distance: Infinity }
      })
    }

    if (sortOrder === 'nearest' || sortOrder === 'farthest') {
      if (userProfile?.latitude && userProfile?.longitude) {
        result = result
          .filter((item: any) => item.distance !== undefined && item.distance !== Infinity)
          .sort((a: any, b: any) => 
            sortOrder === 'nearest' ? a.distance - b.distance : b.distance - a.distance
          )
      }
    } else if (sortOrder === 'newest' || sortOrder === 'oldest') {
      result = result.sort((a: any, b: any) => {
        const dateA = new Date(a.created_at).getTime()
        const dateB = new Date(b.created_at).getTime()
        return sortOrder === 'newest' ? dateB - dateA : dateA - dateB
      })
    }

    return result
  }, [mode, offers, needs, closedOffers, closedNeeds, showClosed, query, activeTags, userProfile, sortOrder])

  const paginatedServices = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage
    return filtered.slice(startIndex, endIndex)
  }, [filtered, currentPage])

  const totalPages = Math.ceil(filtered.length / itemsPerPage)

  useEffect(() => {
    setCurrentPage(1)
  }, [mode, query, activeTags, sortOrder, showClosed])

  const servicesWithLocation = useMemo(() => {
    if (!servicesData?.results) return []
    return servicesData.results.filter((s: any) => s.latitude && s.longitude && s.status !== 'completed')
  }, [servicesData])

  const mapCenter: [number, number] = useMemo(() => {
    if (!isAuthenticated) {
      return [41.0082, 28.9784]
    }
    if (profileLoading) {
      return [41.0082, 28.9784]
    }
    if (userProfile?.latitude && userProfile?.longitude) {
      return [parseFloat(userProfile.latitude), parseFloat(userProfile.longitude)]
    }
    return [41.0082, 28.9784]
  }, [servicesWithLocation, userProfile, isAuthenticated, profileLoading])

  const mapZoom = useMemo(() => {
    if (!userProfile?.latitude || !userProfile?.longitude) {
      return 10
    }
    const userLat = parseFloat(userProfile.latitude)
    const userLng = parseFloat(userProfile.longitude)
    
    const nearbyServices = servicesWithLocation
      .map((s: any) => {
        const distance = calculateDistance(userLat, userLng, parseFloat(s.latitude), parseFloat(s.longitude))
        return distance
      })
      .filter((d: number) => d < 50)
      .sort((a: number, b: number) => a - b)
    
    if (nearbyServices.length === 0) {
      return 12
    }
    
    const closestDistance = nearbyServices[0]
    if (closestDistance < 1) return 15
    if (closestDistance < 5) return 13
    if (closestDistance < 10) return 12
    if (closestDistance < 20) return 11
    return 10
  }, [userProfile, servicesWithLocation])

  function toggleTag(t: string) {
    setActiveTags((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]))
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Loading...</p>
      </div>
    )
  }

  const userHours = timeAccountData?.balance || 0
  const displayName = user?.profile?.display_name || user?.full_name || user?.email || 'Guest'

  return (
    <div className="max-w-6xl mx-auto w-full">
      {/* Hero Section */}
      <div className="rounded-3xl border border-gray-200 bg-white/70 backdrop-blur p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold">
              Hello {isAuthenticated ? displayName : 'Guest'} 👋
            </h2>
            {isAuthenticated && (
              <p className="text-sm text-gray-600 mt-1">
                Time balance:{' '}
                <span className="font-semibold">{Number(userHours).toFixed(1)} hours</span>
              </p>
            )}
          </div>
          <div className="w-full md:w-1/2">
            <TextInput
              label="Search"
              name="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. tutoring, companionship, coding…"
            />
          </div>
        </div>

        <div className="mt-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-medium text-gray-700">Popular Tags:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {demoTags.map((t) => (
              <Pill key={t} active={activeTags.includes(t)} onClick={() => toggleTag(t)}>
                #{t}
              </Pill>
            ))}
          </div>
        </div>
      </div>

      {/* Map ve Services List */}
      <div className="grid md:grid-cols-3 gap-4 mt-6">
        <div className="md:col-span-2 rounded-3xl border border-gray-200 bg-white/70 backdrop-blur overflow-hidden h-[500px]">
          {servicesWithLocation.length > 0 ? (
            <MapContainer
              center={mapCenter}
              zoom={mapZoom}
              style={{ height: '100%', width: '100%', zIndex: 0 }}
              scrollWheelZoom={true}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <ChangeMapView center={mapCenter} zoom={mapZoom} />
              {userProfile?.latitude && userProfile?.longitude && (
                <Marker
                  position={[parseFloat(userProfile.latitude), parseFloat(userProfile.longitude)]}
                  icon={userLocationIcon}
                >
                  <Popup>
                    <div className="p-2">
                      <p className="font-semibold">Your Location</p>
                      <p className="text-sm text-gray-600">{userProfile.address || 'Your address'}</p>
                    </div>
                  </Popup>
                </Marker>
              )}
              {servicesWithLocation.map((service: any) => {
                const isOffer = service.service_type === 'offer' || service.service_type === 'OFFER'
                const lat = parseFloat(service.latitude)
                const lng = parseFloat(service.longitude)
                
                const matchesFilter = filtered.some((f: any) => f.id === service.id)
                if (!matchesFilter) return null

                const filteredService = filtered.find((f: any) => f.id === service.id)
                const distance = filteredService?.distance

                return (
                  <Marker
                    key={service.id}
                    position={[lat, lng]}
                    icon={isOffer ? offerIcon : needIcon}
                  >
                    <Popup className="custom-popup" maxWidth={300} minWidth={250}>
                      <div className="p-3">
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-bold text-base text-gray-900 pr-2">{service.title}</h3>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold whitespace-nowrap ${
                            isOffer ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                          }`}>
                            {isOffer ? 'OFFER' : 'NEED'}
                          </span>
                        </div>
                        
                        <p className="text-sm text-gray-700 mb-3 line-clamp-3">{service.description}</p>
                        
                        <div className="space-y-2 mb-3">
                          <div className="flex items-center text-xs text-gray-600">
                            <span className="font-semibold mr-1">Owner:</span>
                            {service.owner?.id ? (
                              <span
                                onClick={(e) => {
                                  e.stopPropagation()
                                  navigate(`/users/${service.owner.id}`)
                                }}
                                className="hover:underline cursor-pointer font-medium text-gray-800"
                              >
                                {service.owner?.full_name || service.owner?.email || 'Unknown'}
                              </span>
                            ) : (
                              <span>{service.owner?.full_name || service.owner?.username || 'Unknown'}</span>
                            )}
                          </div>
                          <div className="flex items-center text-xs text-gray-600">
                            <span className="font-semibold mr-1">Hours:</span>
                            <span>⏱️ {service.estimated_hours || 'N/A'} hours</span>
                          </div>
                          {distance !== undefined && distance !== Infinity && (
                            <div className="flex items-center text-xs text-gray-600">
                              <span className="font-semibold mr-1">Distance:</span>
                              <span>📍 {distance.toFixed(1)} km</span>
                            </div>
                          )}
                          {service.tags && service.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {service.tags.slice(0, 3).map((tag: any) => {
                                const tagSlug = typeof tag === 'string' ? tag : tag.slug || tag.id
                                const tagName = typeof tag === 'string' ? tag : tag.slug || tag.name
                                return (
                                  <span
                                    key={tagSlug}
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      navigate(`/services?tag=${encodeURIComponent(tagSlug)}`)
                                    }}
                                    className="px-1.5 py-0.5 text-xs rounded border border-gray-300 bg-white/70 hover:bg-gray-100 cursor-pointer"
                                  >
                                    #{tagName}
                                  </span>
                                )
                              })}
                              {service.tags.length > 3 && (
                                <span className="px-1.5 py-0.5 text-xs text-gray-500">
                                  +{service.tags.length - 3} more
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                        
                        <button
                          onClick={() => navigate(`/services/${service.id}`)}
                          className="w-full px-4 py-2 text-sm font-semibold bg-black text-white rounded-lg hover:opacity-90 transition-opacity"
                        >
                          View Full Details
                        </button>
                      </div>
                    </Popup>
                  </Marker>
                )
              })}
            </MapContainer>
          ) : (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="text-sm text-gray-500">Map Area</div>
                <div className="text-xs text-gray-400 mt-1">
                  {servicesLoading
                    ? 'Loading services...'
                    : 'No services with location data yet. Add location when creating a service.'}
                </div>
              </div>
            </div>
          )}
        </div>
        <div className="flex flex-col gap-3">
          <div className="space-y-3">
            <div className="flex items-center gap-2 flex-wrap">
              <Pill active={mode === 'offers'} onClick={() => setMode('offers')}>
                Offers ({offers.length})
              </Pill>
              <Pill active={mode === 'needs'} onClick={() => setMode('needs')}>
                Needs ({needs.length})
              </Pill>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-medium text-gray-700">Status:</span>
              <Pill active={!showClosed} onClick={() => setShowClosed(false)}>
                Active
              </Pill>
              <Pill active={showClosed} onClick={() => setShowClosed(true)}>
                Closed ({mode === 'offers' ? closedOffers.length : closedNeeds.length})
              </Pill>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-medium text-gray-700">Sort:</span>
              <Pill active={sortOrder === 'newest'} onClick={() => setSortOrder('newest')}>
                Newest First
              </Pill>
              <Pill active={sortOrder === 'oldest'} onClick={() => setSortOrder('oldest')}>
                Oldest First
              </Pill>
              {isAuthenticated && userProfile?.latitude && userProfile?.longitude && (
                <>
                  <Pill active={sortOrder === 'nearest'} onClick={() => setSortOrder('nearest')}>
                    Nearest First
                  </Pill>
                  <Pill active={sortOrder === 'farthest'} onClick={() => setSortOrder('farthest')}>
                    Farthest First
                  </Pill>
                </>
              )}
            </div>
          </div>
          {servicesLoading ? (
            <div className="text-center text-gray-500 py-8">Loading...</div>
          ) : filtered.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              {query || activeTags.length > 0
                ? 'No results found matching your search criteria'
                : mode === 'offers'
                  ? 'No services offered yet'
                  : 'No services needed yet'}
            </div>
          ) : (
            <>
              {paginatedServices.map((item: any) => (
                <Card
                  key={item.id}
                  title={item.title}
                  subtitle={`${(item.service_type === 'offer' || item.service_type === 'OFFER') ? 'Offering' : 'Seeking'}`}
                  ownerName={item.owner?.full_name || item.owner?.email || 'User'}
                  desc={item.description}
                  hours={item.estimated_hours}
                  distanceKm={item.distance}
                  tags={(item.tags || []).map((t: any) =>
                    typeof t === 'string' ? t : t.slug || t.name || ''
                  )}
                  onTagClick={(tag) => navigate(`/services?tag=${encodeURIComponent(tag)}`)}
                  onOwnerClick={(ownerId) => {
                    console.log('Navigating to user:', ownerId)
                    navigate(`/users/${ownerId}`)
                  }}
                  ownerId={item.owner?.id}
                  cta={(item.service_type === 'offer' || item.service_type === 'OFFER') ? 'Request' : 'Help'}
                  onClick={() => navigate(`/services/${item.id}`)}
                />
              ))}
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-4">
                  <button
                    onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="px-3 py-1 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-gray-600">
                    Page {currentPage} of {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Floating create button */}
      {isAuthenticated && (
        <div className="fixed bottom-6 right-6">
          <button
            onClick={() => navigate('/services/create')}
            className="rounded-full px-5 py-3 bg-black text-white shadow-lg hover:opacity-90"
          >
            + New Listing (Offer/Need)
          </button>
        </div>
      )}
    </div>
  )
}

