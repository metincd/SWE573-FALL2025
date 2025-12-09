import { useQuery } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../contexts/AuthContext'
import { useState } from 'react'
import Pill from '../components/ui/Pill'

export default function Forum() {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const [searchParams] = useSearchParams()
  const tagFilter = searchParams.get('tag')
  const [searchQuery, setSearchQuery] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['threads', tagFilter, searchQuery],
    queryFn: async () => {
      const params = new URLSearchParams()
      params.append('forum_only', 'true')
      if (tagFilter) params.append('tag', tagFilter)
      if (searchQuery) params.append('search', searchQuery)
      const url = `/threads/${params.toString() ? '?' + params.toString() : ''}`
      const response = await api.get(url)
      return response.data
    },
  })

  const handleTagClick = (tagSlug: string) => {
    navigate(`/services?tag=${encodeURIComponent(tagSlug)}`)
  }

  if (!isAuthenticated) {
    navigate('/login')
    return null
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Loading forum...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-2">Error loading forum</p>
          <p className="text-sm text-gray-500">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto w-full">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold mb-2">
            {tagFilter ? `Forum: #${tagFilter}` : 'Community Forum'}
          </h1>
          <p className="text-sm text-gray-600">
            {tagFilter 
              ? `Discussions tagged "${tagFilter}"`
              : 'Share ideas, collaborate on projects, and organize activities'
            }
          </p>
        </div>
        <button
          onClick={() => navigate('/forum/create')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
        >
          New Thread
        </button>
      </div>

      <div className="mb-4">
        <input
          type="text"
          placeholder="Search threads..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {tagFilter && (
        <div className="mb-4">
          <button
            onClick={() => navigate('/forum')}
            className="text-sm text-gray-600 hover:text-gray-900 underline"
          >
            ← Clear tag filter
          </button>
        </div>
      )}

      {data?.results?.length === 0 ? (
        <div className="rounded-lg border bg-white/70 backdrop-blur p-8 text-center">
          <p className="text-gray-600">No threads found yet</p>
          <button
            onClick={() => navigate('/forum/create')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Create First Thread
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {data?.results?.map((thread: any) => (
            <div
              key={thread.id}
              onClick={() => navigate(`/forum/${thread.id}`)}
              className="rounded-lg border border-gray-200 bg-white/80 backdrop-blur shadow-sm p-6 cursor-pointer hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      {thread.author?.avatar_url ? (
                        <img
                          src={thread.author.avatar_url}
                          alt="Avatar"
                          className="w-8 h-8 rounded-full object-cover border-2 border-gray-200"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none'
                            const fallback = e.currentTarget.nextElementSibling as HTMLElement
                            if (fallback) fallback.style.display = 'flex'
                          }}
                        />
                      ) : null}
                      <div 
                        className={`w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center ${thread.author?.avatar_url ? 'hidden' : ''}`}
                      >
                        <span className="text-xs font-bold text-gray-600">
                          {(thread.author?.full_name || thread.author?.username || 'U')[0].toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900">{thread.title}</h3>
                    {thread.status === 'pinned' && (
                      <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">
                        Pinned
                      </span>
                    )}
                    {thread.status === 'closed' && (
                      <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">
                        Closed
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                    <span
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate(`/users/${thread.author?.id}`)
                      }}
                      className="hover:underline cursor-pointer font-medium"
                    >
                      {thread.author?.full_name || thread.author?.username || 'Unknown'}
                    </span>
                    <span>{new Date(thread.created_at).toLocaleDateString()}</span>
                    <span>{thread.post_count || 0} {thread.post_count === 1 ? 'reply' : 'replies'}</span>
                    <span>{thread.views_count || 0} {thread.views_count === 1 ? 'view' : 'views'}</span>
                  </div>
                  {thread.tags && thread.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {thread.tags.map((tag: any) => (
                        <Pill
                          key={tag.slug || tag}
                          active={false}
                          onClick={(e) => {
                            e?.stopPropagation()
                            handleTagClick(typeof tag === 'string' ? tag : tag.slug)
                          }}
                        >
                          #{typeof tag === 'string' ? tag : tag.slug || tag.name}
                        </Pill>
                      ))}
                    </div>
                  )}
                </div>
                {thread.last_post && (
                  <div className="text-right text-sm text-gray-500">
                    <p className="font-medium">Last reply</p>
                    <p>{new Date(thread.last_post.created_at).toLocaleDateString()}</p>
                    <p className="text-xs mt-1">
                      by {thread.last_post.author?.full_name || thread.last_post.author?.username || 'Unknown'}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

