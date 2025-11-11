import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../lib/api'
import TextInput from '../components/ui/TextInput'
import Pill from '../components/ui/Pill'
import Card from '../components/ui/Card'

const demoTags = [
  'cooking',
  'tutoring',
  'companionship',
  'errands',
  'storytelling',
  'gardening',
  'music',
  'coding',
  'eldercare',
]

export default function Home() {
  const { isAuthenticated, user, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState<'offers' | 'needs'>('offers')
  const [query, setQuery] = useState('')
  const [activeTags, setActiveTags] = useState<string[]>([])

  // Fetch services
  const { data: servicesData, isLoading: servicesLoading } = useQuery({
    queryKey: ['services'],
    queryFn: async () => {
      const response = await api.get('/services/')
      return response.data
    },
    enabled: true, // Always load
  })

  // Fetch time account (only for authenticated users)
  const { data: timeAccountData } = useQuery({
    queryKey: ['time-account'],
    queryFn: async () => {
      const response = await api.get('/time-accounts/')
      return response.data[0] // TimeAccountViewSet returns list
    },
    enabled: isAuthenticated,
  })

  // Separate services into offers and needs
  const { offers, needs } = useMemo(() => {
    if (!servicesData?.results) return { offers: [], needs: [] }

    const allServices = servicesData.results
    const offersList = allServices.filter((s: any) => s.service_type === 'OFFER')
    const needsList = allServices.filter((s: any) => s.service_type === 'NEED')

    return { offers: offersList, needs: needsList }
  }, [servicesData])

  // Filtering
  const list = mode === 'offers' ? offers : needs

  const filtered = useMemo(() => {
    return list.filter((item: any) => {
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
  }, [list, query, activeTags])

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
  const displayName = user?.profile?.display_name || user?.full_name || user?.username || 'Guest'

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

        {/* Tags */}
        <div className="mt-4 flex flex-wrap gap-2">
          {demoTags.map((t) => (
            <Pill key={t} active={activeTags.includes(t)} onClick={() => toggleTag(t)}>
              #{t}
            </Pill>
          ))}
        </div>

        {/* Mode Toggle */}
        <div className="mt-4 flex items-center gap-2 text-sm">
          <Pill active={mode === 'offers'} onClick={() => setMode('offers')}>
            Offers ({offers.length})
          </Pill>
          <Pill active={mode === 'needs'} onClick={() => setMode('needs')}>
            Needs ({needs.length})
          </Pill>
        </div>
      </div>

      {/* Map placeholder ve Services List */}
      <div className="grid md:grid-cols-3 gap-4 mt-6">
        <div className="md:col-span-2 rounded-3xl border border-gray-200 bg-white/70 backdrop-blur p-4 h-[340px] flex items-center justify-center">
          <div className="text-center">
            <div className="text-sm text-gray-500">Map Area (Mock)</div>
            <div className="text-xs text-gray-400 mt-1">
              (Offers & Needs pins will appear here)
            </div>
          </div>
        </div>
        <div className="flex flex-col gap-3">
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
            filtered.map((item: any) => (
              <Card
                key={item.id}
                title={item.title}
                subtitle={`${item.owner?.full_name || item.owner?.username || 'User'} • ${
                  item.service_type === 'OFFER' ? 'Offering' : 'Seeking'
                }`}
                desc={item.description}
                hours={item.estimated_hours}
                tags={(item.tags || []).map((t: any) =>
                  typeof t === 'string' ? t : t.slug || t.name || ''
                )}
                cta={item.service_type === 'OFFER' ? 'Request' : 'Help'}
                onClick={() => navigate(`/services/${item.id}`)}
              />
            ))
          )}
        </div>
      </div>

      {/* Forums / Commons preview */}
      <div className="mt-6 grid md:grid-cols-3 gap-4">
        {['Announcements', 'Workshops', 'Community Chat'].map((col) => (
          <div key={col} className="rounded-3xl border border-gray-200 bg-white/70 backdrop-blur p-4">
            <div className="text-sm font-semibold mb-2">{col}</div>
            <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
              <li>Community rules updated.</li>
              <li>Collective picnic this weekend.</li>
              <li>Next week "storytelling" gathering.</li>
            </ul>
          </div>
        ))}
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
