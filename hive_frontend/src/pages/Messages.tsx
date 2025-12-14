import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api'
import { useAuth } from '../contexts/AuthContext'
import { useState } from 'react'
import Pill from '../components/ui/Pill'

export default function Messages() {
  const navigate = useNavigate()
  const { isAuthenticated, user } = useAuth()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'messages' | 'thank-you'>('messages')

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

  const { data: thankYouNotesData } = useQuery({
    queryKey: ['thank-you-notes'],
    queryFn: async () => {
      const response = await api.get('/thank-you-notes/')
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
      queryClient.invalidateQueries({ queryKey: ['service-requests'] })
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

  const thankYouNotes = thankYouNotesData?.results || []
  const receivedThankYouNotes = thankYouNotes.filter((note: any) => note.to_user?.id === user?.id)
  const sentThankYouNotes = thankYouNotes.filter((note: any) => note.from_user?.id === user?.id)

  return (
    <div className="max-w-4xl mx-auto w-full">
      <h1 className="text-2xl font-bold mb-4">Messages</h1>
      
      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <Pill
          active={activeTab === 'messages'}
          onClick={() => setActiveTab('messages')}
        >
          Messages {conversations.length > 0 && `(${conversations.length})`}
        </Pill>
        <Pill
          active={activeTab === 'thank-you'}
          onClick={() => setActiveTab('thank-you')}
        >
          Thank You Notes {(receivedThankYouNotes.length > 0 || sentThankYouNotes.length > 0) && 
            `(${receivedThankYouNotes.length + sentThankYouNotes.length})`}
        </Pill>
      </div>

      {/* Messages Tab */}
      {activeTab === 'messages' && (
        <>
          <p className="text-sm text-gray-600 mb-6">
            All your private chats. You can open a conversation or manage requests directly from here.
          </p>
          {serviceRequests.some((req: any) => req.service?.capacity > 1) && (
            <div className="mb-4 p-3 bg-blue-50 rounded-lg text-sm text-blue-800">
              💡 Some services support multiple participants. You can accept multiple requests up to the service capacity. Each participant will be charged separately when the service is completed.
            </div>
          )}

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
                      <p 
                        onClick={() => req?.service?.id && navigate(`/services/${req.service.id}`)}
                        className="text-sm text-gray-600 hover:underline cursor-pointer"
                      >
                        {req.service.title}
                      </p>
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
        </>
      )}

      {/* Thank You Notes Tab */}
      {activeTab === 'thank-you' && (
        <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur p-6 shadow-sm">
          <h2 className="text-xl font-bold mb-4">Thank You Notes</h2>
          
          {receivedThankYouNotes.length === 0 && sentThankYouNotes.length === 0 ? (
            <p className="text-sm text-gray-500">You don't have any thank you notes yet.</p>
          ) : (
            <>
              {receivedThankYouNotes.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-3">Received ({receivedThankYouNotes.length})</h3>
                  <div className="space-y-3">
                    {receivedThankYouNotes.map((note: any) => (
                      <div key={note.id} className="border-b border-gray-200 pb-3 last:border-0">
                        <div className="flex items-start justify-between mb-1">
                          <div>
                            {note.from_user?.id ? (
                              <p
                                onClick={() => navigate(`/users/${note.from_user.id}`)}
                                className="font-semibold hover:underline cursor-pointer text-gray-900"
                              >
                                {note.from_user?.full_name || note.from_user?.email || 'Anonymous'}
                              </p>
                            ) : (
                              <p className="font-semibold">
                                {note.from_user?.full_name || note.from_user?.email || 'Anonymous'}
                              </p>
                            )}
                            <p className="text-sm text-gray-500">
                              {new Date(note.created_at).toLocaleDateString()}
                            </p>
                            {note.related_service && (
                              <p className="text-xs text-gray-400 mt-1">
                                For service: <span
                                  onClick={() => navigate(`/services/${note.related_service}`)}
                                  className="hover:underline cursor-pointer"
                                >
                                  View Service
                                </span>
                              </p>
                            )}
                          </div>
                        </div>
                        <p className="text-gray-700 whitespace-pre-wrap text-sm">{note.message}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {sentThankYouNotes.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-3">Sent ({sentThankYouNotes.length})</h3>
                  <div className="space-y-3">
                    {sentThankYouNotes.map((note: any) => (
                      <div key={note.id} className="border-b border-gray-200 pb-3 last:border-0">
                        <div className="flex items-start justify-between mb-1">
                          <div>
                            {note.to_user?.id ? (
                              <p
                                onClick={() => navigate(`/users/${note.to_user.id}`)}
                                className="font-semibold hover:underline cursor-pointer text-gray-900"
                              >
                                To: {note.to_user?.full_name || note.to_user?.email || 'Anonymous'}
                              </p>
                            ) : (
                              <p className="font-semibold">
                                To: {note.to_user?.full_name || note.to_user?.email || 'Anonymous'}
                              </p>
                            )}
                            <p className="text-sm text-gray-500">
                              {new Date(note.created_at).toLocaleDateString()}
                            </p>
                            {note.related_service && (
                              <p className="text-xs text-gray-400 mt-1">
                                For service: <span
                                  onClick={() => navigate(`/services/${note.related_service}`)}
                                  className="hover:underline cursor-pointer"
                                >
                                  View Service
                                </span>
                              </p>
                            )}
                          </div>
                        </div>
                        <p className="text-gray-700 whitespace-pre-wrap text-sm">{note.message}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}







