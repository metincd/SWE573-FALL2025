import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api'
import { useAuth } from '../contexts/AuthContext'

export default function Messages() {
  const navigate = useNavigate()
  const { isAuthenticated, user } = useAuth()
  const queryClient = useQueryClient()

  const { data: conversationsData, isLoading: isLoadingConversations, error: conversationsError } = useQuery({
    queryKey: ['conversations'],
    queryFn: async () => {
      const response = await api.get('/conversations/')
      return response.data
    },
    enabled: isAuthenticated,
  })

  const { data: requestsData } = useQuery({
    queryKey: ['service-requests', 'my'],
    queryFn: async () => {
      const response = await api.get('/service-requests/')
      return response.data
    },
    enabled: isAuthenticated,
  })

  const conversations = conversationsData?.results || []
  const serviceRequests = requestsData?.results || []

  const requestsByConversation: Record<number, any> = {}
  serviceRequests.forEach((req: any) => {
    if (req.conversation) {
      requestsByConversation[req.conversation] = req
    }
  })

  const setStatusMutation = useMutation({
    mutationFn: async ({ requestId, status }: { requestId: number; status: string }) => {
      const response = await api.post(`/service-requests/${requestId}/set_status/`, { status })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['service-requests', 'my'] })
    },
  })

  const approveStartMutation = useMutation({
    mutationFn: async ({ requestId }: { requestId: number }) => {
      const response = await api.post(`/service-requests/${requestId}/approve_start/`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['service-requests', 'my'] })
    },
  })

  if (!isAuthenticated) {
    navigate('/login')
    return null
  }

  if (isLoadingConversations) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Loading messages...</p>
      </div>
    )
  }

  if (conversationsError) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-2">Error loading messages</p>
          <p className="text-sm text-gray-500 mb-4">
            {conversationsError instanceof Error ? conversationsError.message : 'Unknown error'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto w-full">
      <h1 className="text-2xl font-bold mb-4">Messages</h1>
      <p className="text-sm text-gray-600 mb-6">
        All your private chats. You can open a conversation or manage requests directly from here.
      </p>

      {conversations.length === 0 ? (
        <p className="text-sm text-gray-500">You don't have any conversations yet.</p>
      ) : (
        <div className="space-y-4">
          {conversations.map((conv: any) => {
            const req = conv.id ? requestsByConversation[conv.id] : null
            const otherParticipant = conv.participants?.find((p: any) => p.id !== user?.id)
            const isAdminMessage = conv.title?.includes('Admin Message') || 
                                   conv.title?.includes('Account Action') || 
                                   conv.title?.includes('Report') ||
                                   conv.participants?.some((p: any) => p.is_staff && p.id !== user?.id)
            const adminParticipant = conv.participants?.find((p: any) => p.is_staff && p.id !== user?.id)
            const status = req?.status || 'unknown'
            const isOwner = req?.service?.owner?.id === user?.id
            const isRequester = req?.requester?.id === user?.id
            const canApproveStart =
              req &&
              req.status === 'accepted' &&
              ((isOwner && !req.owner_approved) || (isRequester && !req.requester_approved))

            return (
              <div
                key={conv.id}
                className="rounded-2xl border border-gray-200 bg-white/80 backdrop-blur p-4 shadow-sm"
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    {isAdminMessage && adminParticipant ? (
                      <p
                        onClick={() => navigate(`/users/${adminParticipant.id}`)}
                        className="font-semibold hover:underline cursor-pointer text-gray-900"
                      >
                        {adminParticipant?.full_name || adminParticipant?.username || 'Unknown Admin'}
                      </p>
                    ) : otherParticipant?.id ? (
                      <p
                        onClick={() => navigate(`/users/${otherParticipant.id}`)}
                        className="font-semibold hover:underline cursor-pointer text-gray-900"
                      >
                        {otherParticipant?.full_name || otherParticipant?.username || 'Unknown User'}
                      </p>
                    ) : (
                      <p className="font-semibold">
                        {otherParticipant?.full_name || otherParticipant?.username || 'Unknown User'}
                      </p>
                    )}
                    {req?.service?.title && (
                      <p className="text-sm text-gray-600">{req.service.title}</p>
                    )}
                  </div>
                  {req && (
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        status === 'pending'
                          ? 'bg-yellow-100 text-yellow-700'
                          : status === 'accepted'
                            ? 'bg-green-100 text-green-700'
                            : status === 'in_progress'
                              ? 'bg-blue-100 text-blue-700'
                              : status === 'completed'
                                ? 'bg-emerald-100 text-emerald-700'
                                : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {status}
                    </span>
                  )}
                </div>

                {conv.last_message && (
                  <p className="text-sm text-gray-700 mb-2 line-clamp-2">
                    <span className="font-semibold">
                      {conv.last_message.sender?.id === user?.id ? 'You: ' : ''}
                    </span>
                    {conv.last_message.body}
                  </p>
                )}

                <div className="flex flex-wrap gap-2 mt-2">
                  <button
                    onClick={() => navigate(`/chat/${conv.id}`)}
                    className="px-3 py-1 text-xs rounded-lg bg-black text-white hover:bg-gray-900"
                  >
                    Open Chat
                  </button>

                  {isAdminMessage && adminParticipant ? (
                    <button
                      onClick={() => navigate(`/users/${adminParticipant.id}`)}
                      className="px-3 py-1 text-xs rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50"
                    >
                      View Profile
                    </button>
                  ) : otherParticipant && (
                    <button
                      onClick={() => navigate(`/users/${otherParticipant.id}`)}
                      className="px-3 py-1 text-xs rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50"
                    >
                      View Profile
                    </button>
                  )}

                  {req && isOwner && req.status === 'pending' && (
                    <>
                      <button
                        onClick={() =>
                          setStatusMutation.mutate({ requestId: req.id, status: 'accepted' })
                        }
                        disabled={setStatusMutation.isPending}
                        className="px-3 py-1 text-xs rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
                      >
                        Accept
                      </button>
                      <button
                        onClick={() =>
                          setStatusMutation.mutate({ requestId: req.id, status: 'rejected' })
                        }
                        disabled={setStatusMutation.isPending}
                        className="px-3 py-1 text-xs rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
                      >
                        Reject
                      </button>
                    </>
                  )}

                  {req && canApproveStart && (
                    <button
                      onClick={() => approveStartMutation.mutate({ requestId: req.id })}
                      disabled={approveStartMutation.isPending}
                      className="px-3 py-1 text-xs rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                    >
                      Approve Start
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}







