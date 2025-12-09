import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api'
import { useAuth } from '../contexts/AuthContext'
import { useState } from 'react'
import Pill from '../components/ui/Pill'
import ReportButton from '../components/ReportButton'

export default function ThreadDetail() {
  const { threadId } = useParams<{ threadId: string }>()
  const navigate = useNavigate()
  const { isAuthenticated, user } = useAuth()
  const queryClient = useQueryClient()
  const [newPostBody, setNewPostBody] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { data: thread, isLoading, error } = useQuery({
    queryKey: ['thread', threadId],
    queryFn: async () => {
      const response = await api.get(`/threads/${threadId}/`)
      return response.data
    },
    enabled: !!threadId && isAuthenticated,
  })

  const { data: postsData, isLoading: postsLoading } = useQuery({
    queryKey: ['posts', threadId],
    queryFn: async () => {
      const response = await api.get(`/posts/?thread=${threadId}`)
      return response.data
    },
    enabled: !!threadId && isAuthenticated,
  })

  const createPostMutation = useMutation({
    mutationFn: async (body: string) => {
      const response = await api.post('/posts/', {
        thread: threadId,
        body: body,
      })
      return response.data
    },
    onSuccess: () => {
      setNewPostBody('')
      queryClient.invalidateQueries({ queryKey: ['posts', threadId] })
      queryClient.invalidateQueries({ queryKey: ['thread', threadId] })
      queryClient.invalidateQueries({ queryKey: ['threads'] })
    },
  })

  const handleSubmitPost = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newPostBody.trim() || isSubmitting) return

    if (user?.is_banned) {
      alert(`Your account is banned. Reason: ${user.ban_reason || 'No reason provided'}. You cannot post messages.`)
      return
    }

    if (user?.is_suspended) {
      alert(`Your account is suspended. Reason: ${user.suspension_reason || 'No reason provided'}. You cannot post messages.`)
      return
    }

    setIsSubmitting(true)
    try {
      await createPostMutation.mutateAsync(newPostBody.trim())
    } catch (error: any) {
      console.error('Error creating post:', error)
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || 'Failed to create post'
      if (errorMsg.includes('banned') || errorMsg.includes('suspended')) {
        alert(errorMsg)
      } else {
        alert(errorMsg)
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleTagClick = (tagSlug: string) => {
    navigate(`/services?tag=${encodeURIComponent(tagSlug)}`)
  }

  if (!isAuthenticated) {
    navigate('/login')
    return null
  }

  if (isLoading || postsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Loading thread...</p>
      </div>
    )
  }

  if (error || !thread) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-2">Error loading thread</p>
          <button
            onClick={() => navigate('/forum')}
            className="text-sm text-gray-600 underline"
          >
            Back to Forum
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto w-full">
      <button
        onClick={() => navigate('/forum')}
        className="mb-4 text-sm text-gray-600 hover:text-gray-900"
      >
        ← Back to Forum
      </button>

      <div className="rounded-lg border border-gray-200 bg-white/80 backdrop-blur shadow-sm p-6 mb-6">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              {thread.author?.avatar_url ? (
                <img
                  src={thread.author.avatar_url}
                  alt="Avatar"
                  className="w-10 h-10 rounded-full object-cover border-2 border-gray-200"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none'
                    const fallback = e.currentTarget.nextElementSibling as HTMLElement
                    if (fallback) fallback.style.display = 'flex'
                  }}
                />
              ) : null}
              <div 
                className={`w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center ${thread.author?.avatar_url ? 'hidden' : ''}`}
              >
                <span className="text-sm font-bold text-gray-600">
                  {(thread.author?.full_name || thread.author?.username || 'U')[0].toUpperCase()}
                </span>
              </div>
              <div className="flex-1">
                <h1 className="text-2xl font-bold">{thread.title}</h1>
              </div>
              <ReportButton contentType="thread" objectId={thread.id} />
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
              <span
                onClick={() => navigate(`/users/${thread.author?.id}`)}
                className="hover:underline cursor-pointer font-medium"
              >
                {thread.author?.full_name || thread.author?.username || 'Unknown'}
              </span>
              <span>{new Date(thread.created_at).toLocaleDateString()}</span>
              <span>{thread.views_count || 0} {thread.views_count === 1 ? 'view' : 'views'}</span>
              {thread.status === 'closed' && (
                <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">Closed</span>
              )}
            </div>
            {thread.tags && thread.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {thread.tags.map((tag: any) => (
                  <Pill
                    key={tag.slug || tag}
                    active={false}
                    onClick={() => handleTagClick(typeof tag === 'string' ? tag : tag.slug)}
                  >
                    #{typeof tag === 'string' ? tag : tag.slug || tag.name}
                  </Pill>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="space-y-4 mb-6">
        {postsData?.results?.map((post: any) => (
          <div
            key={post.id}
            className="rounded-lg border border-gray-200 bg-white/80 backdrop-blur shadow-sm p-4"
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                {post.author?.avatar_url ? (
                  <img
                    src={post.author.avatar_url}
                    alt="Avatar"
                    className="w-10 h-10 rounded-full object-cover border-2 border-gray-200"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none'
                      const fallback = e.currentTarget.nextElementSibling as HTMLElement
                      if (fallback) fallback.style.display = 'flex'
                    }}
                  />
                ) : null}
                <div 
                  className={`w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center ${post.author?.avatar_url ? 'hidden' : ''}`}
                >
                  <span className="text-sm font-bold text-gray-600">
                    {(post.author?.full_name || post.author?.username || 'U')[0].toUpperCase()}
                  </span>
                </div>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span
                    onClick={() => navigate(`/users/${post.author?.id}`)}
                    className="font-semibold hover:underline cursor-pointer"
                  >
                    {post.author?.full_name || post.author?.username || 'Unknown'}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(post.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="text-gray-700 whitespace-pre-wrap">{post.body}</p>
                <div className="mt-2">
                  <ReportButton contentType="post" objectId={post.id} className="text-xs" />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {thread.status !== 'closed' && (
        <div className="rounded-lg border border-gray-200 bg-white/80 backdrop-blur shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Reply</h2>
          <form onSubmit={handleSubmitPost}>
            <textarea
              value={newPostBody}
              onChange={(e) => setNewPostBody(e.target.value)}
              placeholder="Write your reply..."
              rows={6}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
              required
            />
            <button
              type="submit"
              disabled={!newPostBody.trim() || isSubmitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {isSubmitting ? 'Posting...' : 'Post Reply'}
            </button>
          </form>
        </div>
      )}
    </div>
  )
}

