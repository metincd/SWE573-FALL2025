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
  const [actualHours, setActualHours] = useState('')
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

  const { data: serviceRequest, isLoading: isLoadingRequest, refetch: refetchRequest } = useQuery({
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
    retry: 2,
  })

  const messages = (messagesData?.results || []).slice().reverse()

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

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
      alert(error.response?.data?.detail || 'Failed to send message')
    },
  })

  const setStatusMutation = useMutation({
    mutationFn: async (data: { status: string }) => {
      const response = await api.post(`/service-requests/${serviceRequest?.id}/set_status/`, data)
      return response.data
    },
    onSuccess: () => {
      refetchRequest()
      queryClient.invalidateQueries({ queryKey: ['service-requests'] })
    },
  })

  const approveStartMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/service-requests/${serviceRequest?.id}/approve_start/`)
      return response.data
    },
    onSuccess: () => {
      refetchRequest()
    },
  })

  const updateHoursMutation = useMutation({
    mutationFn: async (data: { actual_hours: number }) => {
      const response = await api.post(`/service-requests/${serviceRequest?.id}/update_hours/`, data)
      return response.data
    },
    onSuccess: () => {
      refetchRequest()
      setActualHours('')
    },
  })

  const approveHoursMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/service-requests/${serviceRequest?.id}/approve_hours/`)
      return response.data
    },
    onSuccess: () => {
      refetchRequest()
    },
  })

  const completeMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/service-requests/${serviceRequest?.id}/complete/`)
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

  if (isLoadingConversation || isLoadingRequest) {
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

  if (!serviceRequest) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-2">Service request not found for this conversation</p>
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
  const isOwner = serviceRequest.service?.owner?.id === user?.id
  const isRequester = serviceRequest.requester?.id === user?.id
  const canApproveStart = (isOwner && !serviceRequest.owner_approved) || (isRequester && !serviceRequest.requester_approved)
  const canUpdateHours = serviceRequest.status === 'in_progress' || serviceRequest.status === 'completed'
  const canApproveHours = serviceRequest.actual_hours && 
    ((isOwner && !serviceRequest.actual_hours_owner_approved) || (isRequester && !serviceRequest.actual_hours_requester_approved))
  const canComplete = serviceRequest.status === 'in_progress'

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
            {otherParticipant?.id ? (
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
          {otherParticipant && (
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
      <div className="rounded-3xl border border-gray-200 bg-white/80 backdrop-blur p-4 shadow-sm mb-4">
        <h2 className="font-semibold mb-2">{serviceRequest.service?.title}</h2>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span>Status: <strong className="text-gray-900">{serviceRequest.status}</strong></span>
          {serviceRequest.service?.estimated_hours && (
            <span>Estimated: <strong className="text-gray-900">{serviceRequest.service.estimated_hours}h</strong></span>
          )}
          {serviceRequest.actual_hours && (
            <span>Actual: <strong className="text-gray-900">{serviceRequest.actual_hours}h</strong></span>
          )}
        </div>
      </div>

      {/* Action Buttons */}
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

        {/* Update Hours (Both parties, when in progress or completed) */}
        {canUpdateHours && (
          <div className="space-y-2">
            <div className="flex gap-2">
              <TextInput
                type="number"
                value={actualHours}
                onChange={(e) => setActualHours(e.target.value)}
                placeholder="Actual hours worked"
                className="flex-1"
              />
              <button
                onClick={() => {
                  const hours = parseFloat(actualHours)
                  if (hours > 0) {
                    updateHoursMutation.mutate({ actual_hours: hours })
                  }
                }}
                disabled={updateHoursMutation.isPending || !actualHours || parseFloat(actualHours) <= 0}
                className="px-4 py-2 rounded-xl bg-gray-800 text-white font-semibold hover:opacity-90 disabled:opacity-50"
              >
                {updateHoursMutation.isPending ? 'Updating...' : 'Update Hours'}
              </button>
            </div>
            {serviceRequest.actual_hours && (
              <div className="text-sm text-gray-600">
                Current actual hours: <strong>{serviceRequest.actual_hours}h</strong>
                {serviceRequest.actual_hours_owner_approved && serviceRequest.actual_hours_requester_approved && (
                  <span className="ml-2 text-green-600">✓ Approved by both parties</span>
                )}
              </div>
            )}
          </div>
        )}

        {/* Approve Hours (Both parties) */}
        {canApproveHours && (
          <button
            onClick={() => approveHoursMutation.mutate()}
            disabled={approveHoursMutation.isPending}
            className="w-full px-4 py-2 rounded-xl bg-purple-600 text-white font-semibold hover:opacity-90 disabled:opacity-50"
          >
            {approveHoursMutation.isPending ? 'Processing...' : 'Approve Actual Hours'}
          </button>
        )}

        {/* Complete Service (Both parties, when in progress) */}
        {canComplete && (
          <button
            onClick={() => {
              if (confirm('Are you sure you want to mark this service as completed? This will transfer time.')) {
                completeMutation.mutate()
              }
            }}
            disabled={completeMutation.isPending}
            className="w-full px-4 py-2 rounded-xl bg-green-600 text-white font-semibold hover:opacity-90 disabled:opacity-50"
          >
            {completeMutation.isPending ? 'Processing...' : 'Mark as Completed'}
          </button>
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
                          onClick={() => navigate(`/users/${message.sender.id}`)}
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
                if (messageBody.trim() && conversationId) {
                  sendMessageMutation.mutate({
                    conversation: parseInt(conversationId),
                    body: messageBody.trim(),
                  })
                }
              }
            }}
          />
          <button
            onClick={() => {
              if (messageBody.trim() && conversationId) {
                sendMessageMutation.mutate({
                  conversation: parseInt(conversationId),
                  body: messageBody.trim(),
                })
              }
            }}
            disabled={sendMessageMutation.isPending || !messageBody.trim()}
            className="px-6 py-3 rounded-xl bg-black text-white font-semibold hover:opacity-90 disabled:opacity-50"
          >
            {sendMessageMutation.isPending ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  )
}

