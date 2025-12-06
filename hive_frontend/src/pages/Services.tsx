import { useQuery } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import Card from '../components/ui/Card'

export default function Services() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const tagFilter = searchParams.get('tag')

  const { data, isLoading, error } = useQuery({
    queryKey: ['services', tagFilter],
    queryFn: async () => {
      const url = tagFilter ? `/services/?tag=${encodeURIComponent(tagFilter)}` : '/services/'
      const response = await api.get(url)
      return response.data
    },
  })

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

  const handleTagClick = (tagSlug: string) => {
    navigate(`/services?tag=${encodeURIComponent(tagSlug)}`)
  }

  return (
    <div className="max-w-6xl mx-auto w-full">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">
          {tagFilter ? `Services tagged: #${tagFilter}` : 'All Services'}
        </h1>
        <p className="text-sm text-gray-600">
          {tagFilter 
            ? `Services with the tag "${tagFilter}"`
            : 'Services offered and needed by community members'
          }
        </p>
        {tagFilter && (
          <button
            onClick={() => navigate('/services')}
            className="mt-2 text-sm text-gray-600 hover:text-gray-900 underline"
          >
            ← Clear filter
          </button>
        )}
      </div>

      {data?.results?.length === 0 ? (
        <div className="rounded-lg border bg-white/70 backdrop-blur p-8 text-center">
          <p className="text-gray-600">No services found yet</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data?.results?.map((service: any) => (
            <Card
              key={service.id}
              title={service.title}
              subtitle={`${service.owner?.full_name || service.owner?.username || 'User'} • ${
                (service.service_type === 'offer' || service.service_type === 'OFFER') ? 'Offering' : 'Seeking'
              }`}
              desc={service.description}
              hours={service.estimated_hours}
              tags={(service.tags || []).map((t: any) =>
                typeof t === 'string' ? t : t.slug || t.name || ''
              )}
              onTagClick={handleTagClick}
              cta="View Details"
              onClick={() => navigate(`/services/${service.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
