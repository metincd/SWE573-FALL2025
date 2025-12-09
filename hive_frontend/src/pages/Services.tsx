import { useQuery } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import Card from '../components/ui/Card'
import { useState, useMemo } from 'react'
import Pill from '../components/ui/Pill'

export default function Services() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const tagFilter = searchParams.get('tag')
  
  const [serviceTypeFilter, setServiceTypeFilter] = useState<'all' | 'offer' | 'need'>('all')
  const [statusFilters, setStatusFilters] = useState<Set<'active' | 'inactive' | 'completed'>>(new Set(['active', 'inactive']))

  const { data: allDataForStats } = useQuery({
    queryKey: ['services-all-for-stats', tagFilter],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (tagFilter) params.append('tag', tagFilter)
      const url = `/services/${params.toString() ? '?' + params.toString() : ''}`
      const response = await api.get(url)
      return response.data
    },
  })

  const { data, isLoading, error } = useQuery({
    queryKey: ['services', tagFilter, serviceTypeFilter, Array.from(statusFilters).sort().join(',')],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (tagFilter) params.append('tag', tagFilter)
      if (serviceTypeFilter !== 'all') params.append('type', serviceTypeFilter)
      const url = `/services/${params.toString() ? '?' + params.toString() : ''}`
      const response = await api.get(url)
      return response.data
    },
  })

  const filteredServices = useMemo(() => {
    if (!data?.results) return []
    return data.results.filter((service: any) => {
      const status = (service.status || '').toLowerCase().trim()
      return statusFilters.has(status as any)
    })
  }, [data, statusFilters])

  const stats = useMemo(() => {
    const results = allDataForStats?.results || []
    return {
      offer: results.filter((s: any) => {
        const type = (s.service_type || '').toLowerCase()
        return type === 'offer'
      }).length,
      need: results.filter((s: any) => {
        const type = (s.service_type || '').toLowerCase()
        return type === 'need'
      }).length,
      active: results.filter((s: any) => {
        const status = (s.status || '').toLowerCase().trim()
        return status === 'active'
      }).length,
      inactive: results.filter((s: any) => {
        const status = (s.status || '').toLowerCase().trim()
        return status === 'inactive'
      }).length,
      completed: results.filter((s: any) => {
        const status = (s.status || '').toLowerCase().trim()
        return status === 'completed'
      }).length,
    }
  }, [allDataForStats])

  const handleTagClick = (tagSlug: string) => {
    navigate(`/services?tag=${encodeURIComponent(tagSlug)}`)
  }

  const toggleStatusFilter = (status: 'active' | 'inactive' | 'completed') => {
    setStatusFilters((prev) => {
      const newSet = new Set(prev)
      if (status === 'inactive') {
        const hasInactive = newSet.has('inactive')
        const hasCompleted = newSet.has('completed')
        if (hasInactive && hasCompleted) {
          newSet.delete('inactive')
          newSet.delete('completed')
        } else {
          newSet.add('inactive')
          newSet.add('completed')
        }
      } else {
        if (newSet.has(status)) {
          newSet.delete(status)
        } else {
          newSet.add(status)
        }
      }
      if (newSet.size === 0) {
        return prev
      }
      return newSet
    })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Loading services...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-2">Error loading services</p>
          <p className="text-sm text-gray-500">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto w-full">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">
          {tagFilter ? `Services tagged: #${tagFilter}` : 'All Services'}
        </h1>
        <p className="text-sm text-gray-600 mb-4">
          {tagFilter 
            ? `Services with the tag "${tagFilter}"`
            : 'Services offered and needed by community members'
          }
        </p>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 mb-4">
          {/* Service Type Filter */}
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">Type:</span>
            <Pill
              active={serviceTypeFilter === 'all'}
              onClick={() => setServiceTypeFilter('all')}
            >
              All ({stats.offer + stats.need})
            </Pill>
            <Pill
              active={serviceTypeFilter === 'offer'}
              onClick={() => setServiceTypeFilter('offer')}
            >
              Offers ({stats.offer})
            </Pill>
            <Pill
              active={serviceTypeFilter === 'need'}
              onClick={() => setServiceTypeFilter('need')}
            >
              Needs ({stats.need})
            </Pill>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">Status:</span>
            <Pill
              active={statusFilters.has('active')}
              onClick={() => toggleStatusFilter('active')}
            >
              Active ({stats.active})
            </Pill>
            <Pill
              active={statusFilters.has('inactive') && statusFilters.has('completed')}
              onClick={() => toggleStatusFilter('inactive')}
            >
              Closed ({stats.inactive + stats.completed})
            </Pill>
            <Pill
              active={statusFilters.has('completed')}
              onClick={() => toggleStatusFilter('completed')}
            >
              Completed ({stats.completed})
            </Pill>
          </div>
        </div>

        {tagFilter && (
          <button
            onClick={() => navigate('/services')}
            className="mb-4 text-sm text-gray-600 hover:text-gray-900 underline"
          >
            ← Clear tag filter
          </button>
        )}
      </div>

      {filteredServices?.length === 0 ? (
        <div className="rounded-lg border bg-white/70 backdrop-blur p-8 text-center">
          <p className="text-gray-600">No services found with the selected filters</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredServices?.map((service: any) => (
            <Card
              key={service.id}
              title={service.title}
              subtitle={`${(service.service_type === 'offer' || service.service_type === 'OFFER') ? 'Offering' : 'Seeking'}`}
              ownerName={service.owner?.full_name || service.owner?.username || 'User'}
              desc={service.description}
              hours={service.estimated_hours}
              tags={(service.tags || []).map((t: any) =>
                typeof t === 'string' ? t : t.slug || t.name || ''
              )}
              onTagClick={handleTagClick}
              onOwnerClick={(ownerId) => {
                console.log('Navigating to user:', ownerId)
                navigate(`/users/${ownerId}`)
              }}
              ownerId={service.owner?.id}
              cta="View Details"
              onClick={() => navigate(`/services/${service.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
