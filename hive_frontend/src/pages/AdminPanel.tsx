import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../api'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Pill from '../components/ui/Pill'

export default function AdminPanel() {
  const { user, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'stats' | 'reports'>('stats')
  const [reportStatusFilter, setReportStatusFilter] = useState<'all' | 'pending' | 'under_review' | 'resolved' | 'dismissed'>('all')

  if (!isAuthenticated || !user?.is_staff) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Access denied. Only staff members can access this page.</p>
          <button onClick={() => navigate('/')} className="px-4 py-2 bg-black text-white rounded-lg">
            Go Home
          </button>
        </div>
      </div>
    )
  }

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: async () => {
      const response = await api.get('/admin/stats/')
      return response.data
    },
  })

  const { data: reportsData, isLoading: reportsLoading } = useQuery({
    queryKey: ['reports', reportStatusFilter],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (reportStatusFilter !== 'all') {
        params.append('status', reportStatusFilter)
      }
      const url = `/reports/${params.toString() ? '?' + params.toString() : ''}`
      const response = await api.get(url)
      return response.data
    },
  })

  const resolveReportMutation = useMutation({
    mutationFn: async (reportId: number) => {
      const response = await api.post(`/reports/${reportId}/resolve/`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] })
    },
  })

  const dismissReportMutation = useMutation({
    mutationFn: async (reportId: number) => {
      const response = await api.post(`/reports/${reportId}/dismiss/`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] })
    },
  })

  const banUserFromReportMutation = useMutation({
    mutationFn: async ({ reportId, reason }: { reportId: number; reason?: string }) => {
      const response = await api.post(`/reports/${reportId}/ban_user/`, { reason })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      queryClient.invalidateQueries({ queryKey: ['messages'] })
      alert(`User has been banned. Messages have been sent to both the reporter and the banned user. They can be found in the Messages section.`)
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Failed to ban user')
    },
  })

  const suspendUserFromReportMutation = useMutation({
    mutationFn: async ({ reportId, reason }: { reportId: number; reason?: string }) => {
      const response = await api.post(`/reports/${reportId}/suspend_user/`, { reason })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      queryClient.invalidateQueries({ queryKey: ['messages'] })
      alert(`User has been suspended. Messages have been sent to both the reporter and the suspended user. They can be found in the Messages section.`)
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Failed to suspend user')
    },
  })

  const deleteContentMutation = useMutation({
    mutationFn: async (reportId: number) => {
      const response = await api.post(`/reports/${reportId}/delete_content/`)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] })
      queryClient.invalidateQueries({ queryKey: ['services'] })
      queryClient.invalidateQueries({ queryKey: ['threads'] })
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      alert(data.message || 'Content deleted successfully. A message has been sent to the reporter.')
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Failed to delete content')
    },
  })


  return (
    <div className="max-w-7xl mx-auto w-full">
      <h1 className="text-3xl font-bold mb-6">Admin Panel</h1>

      <div className="flex gap-2 mb-6 flex-wrap">
        <Pill active={activeTab === 'stats'} onClick={() => setActiveTab('stats')}>
          Statistics
        </Pill>
        <Pill active={activeTab === 'reports'} onClick={() => setActiveTab('reports')}>
          Reports ({stats?.reports?.pending || 0} pending)
        </Pill>
      </div>

      {activeTab === 'stats' && (
        <div className="space-y-6">
          {statsLoading ? (
            <p>Loading statistics...</p>
          ) : (
            <>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="rounded-lg border bg-white/80 backdrop-blur p-4">
                  <p className="text-sm text-gray-600">Total Services</p>
                  <p className="text-2xl font-bold">{stats?.services?.total || 0}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {stats?.services?.active || 0} active, {stats?.services?.completed || 0} completed
                  </p>
                </div>
                <div className="rounded-lg border bg-white/80 backdrop-blur p-4">
                  <p className="text-sm text-gray-600">Total Users</p>
                  <p className="text-2xl font-bold">{stats?.users?.total || 0}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {stats?.users?.active || 0} active, {stats?.users?.banned || 0} banned
                  </p>
                </div>
                <div className="rounded-lg border bg-white/80 backdrop-blur p-4">
                  <p className="text-sm text-gray-600">Pending Reports</p>
                  <p className="text-2xl font-bold text-red-600">{stats?.reports?.pending || 0}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {stats?.reports?.total || 0} total reports
                  </p>
                </div>
                <div className="rounded-lg border bg-white/80 backdrop-blur p-4">
                  <p className="text-sm text-gray-600">Forum Activity</p>
                  <p className="text-2xl font-bold">{stats?.forum?.total_threads || 0}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {stats?.forum?.total_posts || 0} posts
                  </p>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="rounded-lg border bg-white/80 backdrop-blur p-6">
                  <h2 className="text-xl font-bold mb-4">Services Overview</h2>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Offers:</span>
                      <span className="font-semibold">{stats?.services?.offers || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Needs:</span>
                      <span className="font-semibold">{stats?.services?.needs || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Created (7 days):</span>
                      <span className="font-semibold">{stats?.services?.created_last_7_days || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Created (30 days):</span>
                      <span className="font-semibold">{stats?.services?.created_last_30_days || 0}</span>
                    </div>
                  </div>
                </div>

                <div className="rounded-lg border bg-white/80 backdrop-blur p-6">
                  <h2 className="text-xl font-bold mb-4">Reports Overview</h2>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Pending:</span>
                      <span className="font-semibold text-red-600">{stats?.reports?.pending || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Under Review:</span>
                      <span className="font-semibold">{stats?.reports?.under_review || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Resolved:</span>
                      <span className="font-semibold text-green-600">{stats?.reports?.resolved || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Dismissed:</span>
                      <span className="font-semibold">{stats?.reports?.dismissed || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Created (7 days):</span>
                      <span className="font-semibold">{stats?.reports?.created_last_7_days || 0}</span>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {activeTab === 'reports' && (
        <div className="space-y-4">
          <div className="flex gap-2 flex-wrap">
            <Pill active={reportStatusFilter === 'all'} onClick={() => setReportStatusFilter('all')}>
              All
            </Pill>
            <Pill active={reportStatusFilter === 'pending'} onClick={() => setReportStatusFilter('pending')}>
              Pending
            </Pill>
            <Pill active={reportStatusFilter === 'under_review'} onClick={() => setReportStatusFilter('under_review')}>
              Under Review
            </Pill>
            <Pill active={reportStatusFilter === 'resolved'} onClick={() => setReportStatusFilter('resolved')}>
              Resolved
            </Pill>
            <Pill active={reportStatusFilter === 'dismissed'} onClick={() => setReportStatusFilter('dismissed')}>
              Dismissed
            </Pill>
          </div>

          {reportsLoading ? (
            <p>Loading reports...</p>
          ) : reportsData?.results?.length === 0 ? (
            <p className="text-gray-600">No reports found.</p>
          ) : (
            <div className="space-y-4">
              {reportsData?.results?.map((report: any) => (
                <div key={report.id} className="rounded-lg border bg-white/80 backdrop-blur p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          report.status === 'pending' ? 'bg-red-100 text-red-700' :
                          report.status === 'under_review' ? 'bg-yellow-100 text-yellow-700' :
                          report.status === 'resolved' ? 'bg-green-100 text-green-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {report.status.toUpperCase()}
                        </span>
                        <span className="px-2 py-1 rounded text-xs bg-blue-100 text-blue-700">
                          {report.reason}
                        </span>
                        <span className="text-xs text-gray-500">
                          {report.content_type_name}
                        </span>
                      </div>
                      <p className="text-sm font-semibold mb-1">
                        Reported by: {report.reporter?.full_name || report.reporter?.username || report.reporter?.email}
                      </p>
                      {report.reported_object_author && (
                        <p className="text-sm text-gray-600 mb-1">
                          Author/Owner: {report.reported_object_author.full_name || report.reported_object_author.username || report.reported_object_author.email}
                        </p>
                      )}
                      {report.reported_object_title && (
                        <p className="text-sm font-semibold text-gray-800 mb-1">
                          Title: {report.reported_object_title}
                        </p>
                      )}
                      <p className="text-sm text-gray-700 mb-2">{report.description}</p>
                      <div className="text-xs text-gray-500 space-y-1 mb-2">
                        <p>
                          <span className="font-semibold">Content Type:</span> {report.content_type_name}
                        </p>
                        <p>
                          <span className="font-semibold">Object ID:</span> {report.object_id}
                        </p>
                        <p>
                          <span className="font-semibold">Preview:</span> {report.reported_content_preview}
                        </p>
                        {(() => {
                          const contentType = report.content_type_name?.split('.')[1] || ''
                          const objectId = report.object_id
                          let linkUrl = ''
                          let linkText = ''
                          
                          if (contentType === 'service') {
                            linkUrl = `/services/${objectId}`
                            linkText = 'View Service'
                          } else if (contentType === 'post') {
                            if (report.related_service_id) {
                              linkUrl = `/services/${report.related_service_id}`
                              linkText = 'View Service Discussion'
                            } else if (report.related_thread_id) {
                              linkUrl = `/forum/${report.related_thread_id}`
                              linkText = 'View Forum Thread'
                            }
                          } else if (contentType === 'thread') {
                            linkUrl = `/forum/${objectId}`
                            linkText = 'View Thread'
                          } else if (contentType === 'user') {
                            linkUrl = `/users/${objectId}`
                            linkText = 'View User Profile'
                          } else if (contentType === 'message') {
                            if (report.related_conversation_id) {
                              linkUrl = `/chat/${report.related_conversation_id}`
                              linkText = 'View Conversation'
                            }
                          }
                          
                          return linkUrl ? (
                            <a
                              href={linkUrl}
                              onClick={(e) => {
                                e.preventDefault()
                                navigate(linkUrl)
                              }}
                              className="text-blue-600 hover:text-blue-800 hover:underline font-semibold"
                            >
                              {linkText} →
                            </a>
                          ) : null
                        })()}
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        Created: {new Date(report.created_at).toLocaleString()}
                      </p>
                    </div>
                    {report.status === 'pending' && (
                      <div className="flex flex-col gap-2 ml-4">
                        <div className="flex gap-2 flex-wrap">
                          <button
                            onClick={() => {
                              const reason = prompt('Enter ban reason (optional):')
                              if (reason !== null) {
                                if (window.confirm(`Ban the reported user?\n\nThis will:\n- Prevent them from creating services\n- Prevent them from sending messages\n- Send notification messages to both the reporter and the banned user\n\nBoth messages will appear in the Messages section.`)) {
                                  banUserFromReportMutation.mutate({ reportId: report.id, reason: reason || undefined })
                                }
                              }
                            }}
                            className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
                          >
                            Ban User
                          </button>
                          <button
                            onClick={() => {
                              const reason = prompt('Enter suspension reason (optional):')
                              if (reason !== null) {
                                if (window.confirm(`Suspend the reported user?\n\nThis will:\n- Temporarily prevent them from creating services\n- Temporarily prevent them from sending messages\n- Send notification messages to both the reporter and the suspended user\n\nBoth messages will appear in the Messages section.`)) {
                                  suspendUserFromReportMutation.mutate({ reportId: report.id, reason: reason || undefined })
                                }
                              }
                            }}
                            className="px-3 py-1 text-xs bg-amber-600 text-white rounded hover:bg-amber-700"
                          >
                            Suspend User
                          </button>
                          {(report.content_type_name?.includes('service') || 
                             report.content_type_name?.includes('post') || 
                             report.content_type_name?.includes('thread') || 
                             report.content_type_name?.includes('message')) && (
                            <button
                              onClick={() => {
                                const contentType = report.content_type_name?.split('.')[1] || 'content'
                                if (window.confirm(`Delete the reported ${contentType}?\n\nThis will:\n- Permanently delete the ${contentType}\n- Resolve the report\n- Send a notification message to the reporter\n\nThe message will appear in the Messages section.`)) {
                                  deleteContentMutation.mutate(report.id)
                                }
                              }}
                              className="px-3 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700"
                            >
                              Delete Content
                            </button>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              if (window.confirm('Resolve this report without taking action?')) {
                                resolveReportMutation.mutate(report.id)
                              }
                            }}
                            className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                          >
                            Resolve
                          </button>
                          <button
                            onClick={() => {
                              if (window.confirm('Dismiss this report?')) {
                                dismissReportMutation.mutate(report.id)
                              }
                            }}
                            className="px-3 py-1 text-xs bg-gray-600 text-white rounded hover:bg-gray-700"
                          >
                            Dismiss
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

