import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'

interface ReportButtonProps {
  contentType: 'service' | 'user' | 'post' | 'thread'
  objectId: number
  className?: string
}

const REPORT_REASONS = [
  { value: 'spam', label: 'Spam' },
  { value: 'inappropriate', label: 'Inappropriate Content' },
  { value: 'harassment', label: 'Harassment' },
  { value: 'fraud', label: 'Fraud/Scam' },
  { value: 'violence', label: 'Violence/Threats' },
  { value: 'copyright', label: 'Copyright Violation' },
  { value: 'misinformation', label: 'Misinformation' },
  { value: 'other', label: 'Other' },
]

export default function ReportButton({ contentType, objectId, className = '' }: ReportButtonProps) {
  const [showModal, setShowModal] = useState(false)
  const [reason, setReason] = useState('')
  const [description, setDescription] = useState('')
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const createReportMutation = useMutation({
    mutationFn: async (data: { content_type: number; object_id: number; reason: string; description: string }) => {
      const response = await api.post('/reports/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      setShowModal(false)
      setReason('')
      setDescription('')
      alert('Report submitted successfully. Thank you for helping keep our community safe.')
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || 'Failed to submit report'
      if (errorMsg.includes('already')) {
        alert('You have already reported this content.')
      } else {
        alert(errorMsg)
      }
    },
  })

  const handleReport = () => {
    if (!isAuthenticated) {
      const shouldLogin = window.confirm('You need to be logged in to report content. Would you like to login?')
      if (shouldLogin) {
        navigate('/login')
      }
      return
    }

    setShowModal(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reason) {
      alert('Please select a reason for reporting.')
      return
    }

    const contentTypeMap: Record<string, string> = {
      service: 'service',
      user: 'user',
      post: 'post',
      thread: 'thread',
    }

    try {
      const modelName = contentTypeMap[contentType]
      const response = await api.get(`/contenttypes/get/?app_label=the_hive&model=${modelName}`)
      const contentTypeId = response.data.id
      
      if (!contentTypeId) {
        alert('Failed to find content type. Please try again.')
        return
      }

      createReportMutation.mutate({
        content_type: contentTypeId,
        object_id: objectId,
        reason,
        description,
      })
    } catch (error: any) {
      console.error('Error creating report:', error)
      alert(error.response?.data?.detail || 'Failed to submit report. Please try again.')
    }
  }

  useEffect(() => {
    if (showModal) {
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden'
      return () => {
        document.body.style.overflow = 'unset'
      }
    }
  }, [showModal])

  const modalContent = showModal ? (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-[99999]" 
      onClick={() => setShowModal(false)}
      style={{ zIndex: 99999 }}
    >
      <div 
        className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-2xl" 
        onClick={(e) => e.stopPropagation()}
        style={{ zIndex: 100000 }}
      >
        <h2 className="text-xl font-bold mb-4">Report Content</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reason for reporting <span className="text-red-500">*</span>
            </label>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2"
              required
            >
              <option value="">Select a reason</option>
              {REPORT_REASONS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Additional details (optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2"
              rows={4}
              placeholder="Please provide any additional information that might help us review this report..."
            />
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setShowModal(false)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createReportMutation.isPending}
              className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              {createReportMutation.isPending ? 'Submitting...' : 'Submit Report'}
            </button>
          </div>
        </form>
      </div>
    </div>
  ) : null

  return (
    <>
      {showModal && typeof document !== 'undefined' && createPortal(modalContent, document.body)}
      <button
        onClick={handleReport}
        className={`text-xs text-red-600 hover:text-red-700 hover:underline ${className}`}
        title="Report this content"
      >
        Report
      </button>
    </>
  )
}

