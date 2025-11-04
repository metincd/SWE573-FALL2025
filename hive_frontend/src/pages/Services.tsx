import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

export default function Services() {
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
    <div className="min-h-screen p-6 bg-gray-50">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-semibold mb-6">Services</h1>

        {data?.results?.length === 0 ? (
          <div className="rounded-lg border bg-white p-8 text-center">
            <p className="text-gray-600">No services found</p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {data?.results?.map((service: any) => (
              <div
                key={service.id}
                className="rounded-lg border bg-white p-6 shadow-sm hover:shadow-md transition-shadow"
              >
                <h2 className="text-lg font-semibold mb-2">{service.title}</h2>
                <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                  {service.description}
                </p>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>{service.category}</span>
                  <span>{service.time_cost} hours</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

