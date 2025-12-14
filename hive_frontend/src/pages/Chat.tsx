import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../api'
import TextInput from '../components/ui/TextInput'

export default function Chat() {
  const { conversationId } = useParams<{ conversationId: string }>()
  const navigate = useNavigate()
  const { isAuthenticated, user } = useAuth()
  const queryClient = useQueryClient()
  const [messageBody, setMessageBody] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: conversation, isLoading: isLoadingConversation, error: conversationError } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: async () => {
      const response = await api.get(`/conversations/${conversationId}/`)
      return response.data
    },
    enabled: !!conversationId && isAuthenticated,
    retry: 2,
  })

  const { data: serviceRequest, refetch: refetchRequest } = useQuery({
    queryKey: ['service-request', 'by-conversation', conversationId],
    queryFn: async () => {
      const response = await api.get(`/service-requests/?conversation=${conversationId}`)
      const results = response.data?.results || []
      return results.length > 0 ? results[0] : null
    },
    enabled: !!conversationId && isAuthenticated,
    retry: 2,
  })

  const { data: messagesData, isLoading: isLoadingMessages, refetch: refetchMessages } = useQuery({
    queryKey: ['messages', conversationId],
    queryFn: async () => {
      const response = await api.get(`/messages/?conversation=${conversationId}`)
      return response.data
    },
    enabled: !!conversationId && isAuthenticated,
    refetchInterval: 3000, // Poll every 3 seconds
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
    retry: 2,
  })

  const messages = (messagesData?.results || []).slice().reverse()

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (conversationId && isAuthenticated) {
      refetchMessages()
    }
  }, [conversationId, isAuthenticated, refetchMessages])

  const sendMessageMutation = useMutation({
    mutationFn: async (data: { conversation: number; body: string }) => {
      const response = await api.post('/messages/', data)
      return response.data
    },
    onSuccess: () => {
      setMessageBody('')
      setTimeout(() => {
        refetchMessages()
        queryClient.invalidateQueries({ queryKey: ['messages', conversationId] })
        queryClient.invalidateQueries({ queryKey: ['conversation', conversationId] })
      }, 100)
    },
    onError: (error: any) => {
      console.error('Error sending message:', error)
      const errorMsg = error.response?.data?.detail || 'Failed to send message'
      if (errorMsg.includes('banned') || errorMsg.includes('suspended')) {
        alert(errorMsg)
      } else {
        alert(errorMsg)
      }
    },
  })

  const handleSendMessage = () => {
    if (user?.is_banned) {
      alert(`Your account is banned. Reason: ${user.ban_reason || 'No reason provided'}. You cannot send messages.`)
      return
    }

    if (user?.is_suspended) {
      alert(`Your account is suspended. Reason: ${user.suspension_reason || 'No reason provided'}. You cannot send messages.`)
      return
    }

    if (messageBody.trim() && conversationId) {
      sendMessageMutation.mutate({
        conversation: parseInt(conversationId),
        body: messageBody.trim(),
      })
    }
  }

  const setStatusMutation = useMutation({
    mutationFn: async (data: { status: string }) => {
      if (!serviceRequest?.id) throw new Error('Service request not found')
      const response = await api.post(`/service-requests/${serviceRequest.id}/set_status/`, data)
      return response.data
    },
    onSuccess: () => {
      refetchRequest()
      queryClient.invalidateQueries({ queryKey: ['service-requests'] })
    },
  })

  const approveStartMutation = useMutation({
    mutationFn: async () => {
      if (!serviceRequest?.id) throw new Error('Service request not found')
      const response = await api.post(`/service-requests/${serviceRequest.id}/approve_start/`)
      return response.data
    },
    onSuccess: () => {
      refetchRequest()
      queryClient.invalidateQueries({ queryKey: ['service-requests'] })
      queryClient.invalidateQueries({ queryKey: ['service-requests', 'my'] })
      queryClient.invalidateQueries({ queryKey: ['service-request'] })
    },
  })

  const completeMutation = useMutation({
    mutationFn: async () => {
      if (!serviceRequest?.id) throw new Error('Service request not found')
      const response = await api.post(`/service-requests/${serviceRequest.id}/complete/`)
      return response.data
    },
    onSuccess: () => {
      refetchRequest()
      queryClient.invalidateQueries({ queryKey: ['service-requests'] })
    },
  })

  if (!isAuthenticated) {
    navigate('/login')
    return null
  }

  if (isLoadingConversation) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-2">Loading chat...</p>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
        </div>
      </div>
    )
  }

  if (conversationError) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-2">Error loading conversation</p>
          <p className="text-sm text-gray-500 mb-4">
            {conversationError instanceof Error ? conversationError.message : 'Unknown error'}
          </p>
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-gray-600 underline"
          >
            Go Back
          </button>
        </div>
      </div>
    )
  }

  if (!conversation) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-2">Conversation not found</p>
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-gray-600 underline"
          >
            Go Back
          </button>
        </div>
      </div>
    )
  }

  const otherParticipant = conversation.participants?.find((p: any) => p.id !== user?.id)
  const isAdminMessage = conversation.title?.includes('Admin Message') || 
                         conversation.title?.includes('Account Action') || 
                         conversation.title?.includes('Report') ||
                         conversation.participants?.some((p: any) => p.is_staff && p.id !== user?.id)
  const adminParticipant = conversation.participants?.find((p: any) => p.is_staff && p.id !== user?.id)
  
  const isOwner = serviceRequest?.service?.owner?.id === user?.id
  const isRequester = serviceRequest?.requester?.id === user?.id
  const canApproveStart = serviceRequest && (isOwner && !serviceRequest.owner_approved) || (isRequester && !serviceRequest.requester_approved)
  const canComplete = serviceRequest && serviceRequest.status === 'in_progress'
  const canMarkCompleted = canComplete && (
    (isOwner && !serviceRequest.owner_completed) || 
    (isRequester && !serviceRequest.requester_completed)
  )
  const bothCompleted = serviceRequest && serviceRequest.owner_completed && serviceRequest.requester_completed

  return (
    <div className="max-w-4xl mx-auto w-full">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <button
          onClick={() => navigate(-1)}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          ← Back
        </button>
            <div className="flex items-center gap-3">
          <div>
            <h1 className="text-2xl font-bold">Chat</h1>
            {isAdminMessage && adminParticipant ? (
              <p
                onClick={() => navigate(`/users/${adminParticipant.id}`)}
                className="text-sm text-gray-600 hover:underline cursor-pointer font-medium"
              >
                {adminParticipant?.full_name || adminParticipant?.username || 'Unknown Admin'}
              </p>
            ) : otherParticipant?.id ? (
              <p
                onClick={() => navigate(`/users/${otherParticipant.id}`)}
                className="text-sm text-gray-600 hover:underline cursor-pointer font-medium"
              >
                {otherParticipant?.full_name || otherParticipant?.username || 'Unknown User'}
              </p>
            ) : (
              <p className="text-sm text-gray-600">
                {otherParticipant?.full_name || otherParticipant?.username || 'Unknown User'}
              </p>
            )}
          </div>
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
        </div>
      </div>

      {/* Service Info */}
      {serviceRequest && (
        <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur p-4 shadow-sm mb-4">
          <h2 
            onClick={() => serviceRequest.service?.id && navigate(`/services/${serviceRequest.service.id}`)}
            className="font-semibold mb-2 hover:underline cursor-pointer"
          >
            {serviceRequest.service?.title}
          </h2>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span>Status: <strong className="text-gray-900">{serviceRequest.status}</strong></span>
            {serviceRequest.service?.estimated_hours && (
              <span>Hours: <strong className="text-gray-900">{serviceRequest.service.estimated_hours}h</strong></span>
            )}
            {serviceRequest.service?.capacity && serviceRequest.service.capacity > 1 && (
              <span>Capacity: <strong className="text-gray-900">{serviceRequest.service.capacity} participants</strong></span>
            )}
          </div>
          {serviceRequest.service?.capacity && serviceRequest.service.capacity > 1 && (
            <p className="text-xs text-gray-500 mt-2">
              💡 This service supports multiple participants. Each participant will be charged {serviceRequest.service.estimated_hours}h when completed.
            </p>
          )}
        </div>
      )}

      {/* Admin Message Info */}
      {isAdminMessage && conversation.title && (
        <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur p-4 shadow-sm mb-4">
          <h2 
            onClick={() => conversation.related_service && navigate(`/services/${conversation.related_service}`)}
            className={`font-semibold mb-2 ${conversation.related_service ? 'hover:underline cursor-pointer' : ''}`}
          >
            {conversation.title}
          </h2>
          {adminParticipant && (
            <p className="text-sm text-gray-600">
              Admin: {adminParticipant.full_name || adminParticipant.username || adminParticipant.email}
            </p>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {serviceRequest && (
      <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur p-4 shadow-sm mb-4 space-y-3">
        {/* Approve/Reject (Owner only, when pending) */}
        {isOwner && serviceRequest.status === 'pending' && (
          <div className="flex gap-2">
            <button
              onClick={() => setStatusMutation.mutate({ status: 'accepted' })}
              disabled={setStatusMutation.isPending}
              className="flex-1 px-4 py-2 rounded-xl bg-green-600 text-white font-semibold hover:opacity-90 disabled:opacity-50"
            >
              {setStatusMutation.isPending ? 'Processing...' : 'Accept Request'}
            </button>
            <button
              onClick={() => setStatusMutation.mutate({ status: 'rejected' })}
              disabled={setStatusMutation.isPending}
              className="flex-1 px-4 py-2 rounded-xl bg-red-600 text-white font-semibold hover:opacity-90 disabled:opacity-50"
            >
              {setStatusMutation.isPending ? 'Processing...' : 'Reject Request'}
            </button>
          </div>
        )}

        {/* Approve Start (Both parties, when accepted) */}
        {serviceRequest.status === 'accepted' && canApproveStart && (
          <button
            onClick={() => approveStartMutation.mutate()}
            disabled={approveStartMutation.isPending}
            className="w-full px-4 py-2 rounded-xl bg-blue-600 text-white font-semibold hover:opacity-90 disabled:opacity-50"
          >
            {approveStartMutation.isPending ? 'Processing...' : 'Approve to Start Service'}
          </button>
        )}

        {/* Complete Service (Both parties, when in progress) */}
        {canMarkCompleted && (
          <div className="space-y-2">
            <button
              onClick={() => {
                if (confirm('Mark this service as completed? Time will be transferred when both parties confirm.')) {
                  completeMutation.mutate()
                }
              }}
              disabled={completeMutation.isPending}
              className="w-full px-4 py-2 rounded-xl bg-green-600 text-white font-semibold hover:opacity-90 disabled:opacity-50"
            >
              {completeMutation.isPending ? 'Processing...' : 'Mark as Completed'}
            </button>
            <div className="text-sm text-gray-600">
              {serviceRequest.owner_completed && (
                <div className="text-green-600">✓ Service owner confirmed</div>
              )}
              {serviceRequest.requester_completed && (
                <div className="text-green-600">✓ Requester confirmed</div>
              )}
              {!bothCompleted && (
                <div className="text-gray-500">Waiting for both parties to confirm...</div>
              )}
            </div>
          </div>
        )}
        {bothCompleted && (
          <div className="text-sm text-green-600 font-semibold">
            ✓ Service completed! Time has been transferred.
          </div>
        )}

        {/* Status Display */}
        {serviceRequest.status === 'in_progress' && (
          <div className="text-sm text-gray-600">
            {serviceRequest.owner_approved && serviceRequest.requester_approved ? (
              <span className="text-green-600">✓ Service started - both parties approved</span>
            ) : (
              <span>Waiting for both parties to approve start...</span>
            )}
          </div>
        )}

        {serviceRequest.status === 'completed' && (
          <div className="text-sm text-green-600 font-semibold">
            ✓ Service completed - Time transferred
          </div>
        )}
      </div>
      )}

      {/* Messages */}
      <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur p-4 shadow-sm mb-4">
        <h2 className="font-semibold mb-4">Messages</h2>
        {isLoadingMessages ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900 mx-auto mb-2"></div>
            <p className="text-gray-500 text-sm">Loading messages...</p>
          </div>
        ) : (
          <div className="space-y-4 max-h-[500px] overflow-y-auto">
            {messages.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No messages yet. Start the conversation!</p>
            ) : (
              messages.map((message: any) => {
                const isOwn = message.sender?.id === user?.id
                return (
                  <div
                    key={message.id}
                    className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[70%] rounded-2xl p-3 ${
                        isOwn
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      {isOwn ? (
                        <p className="text-xs font-semibold mb-1">You</p>
                      ) : message.sender?.id ? (
                        <p
                          onClick={() => {
                            if (isAdminMessage && message.sender?.is_staff) {
                              navigate(`/users/${message.sender.id}`)
                            } else {
                              navigate(`/users/${message.sender.id}`)
                            }
                          }}
                          className="text-xs font-semibold mb-1 hover:underline cursor-pointer"
                        >
                          {message.sender?.full_name || message.sender?.username || 'Unknown'}
                        </p>
                      ) : (
                        <p className="text-xs font-semibold mb-1">
                          {message.sender?.full_name || message.sender?.username || 'Unknown'}
                        </p>
                      )}
                      <p className="whitespace-pre-wrap">{message.body}</p>
                      <p className="text-xs mt-1 opacity-70">
                        {new Date(message.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                )
              })
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Send Message */}
      <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur p-4 shadow-sm">
        <div className="flex gap-2">
          <TextInput
            value={messageBody}
            onChange={(e) => setMessageBody(e.target.value)}
            placeholder="Type a message..."
            className="flex-1"
            onKeyDown={(e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSendMessage()
              }
            }}
          />
          <button
            onClick={handleSendMessage}
            disabled={sendMessageMutation.isPending || !messageBody.trim() || user?.is_banned || user?.is_suspended}
            className="px-6 py-3 rounded-xl bg-black text-white font-semibold hover:opacity-90 disabled:opacity-50"
          >
            {sendMessageMutation.isPending ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  )
}

