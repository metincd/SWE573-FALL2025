import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import Card from '../components/ui/Card'

export default function Services() {
  const navigate = useNavigate()
  const { data, isLoading, error } = useQuery({
    queryKey: ['services'],
    queryFn: async () => {
      const response = await api.get('/services/')
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

  return (
    <div className="max-w-6xl mx-auto w-full">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">All Services</h1>
        <p className="text-sm text-gray-600">Services offered and needed by community members</p>
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
              cta="View Details"
              onClick={() => navigate(`/services/${service.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
