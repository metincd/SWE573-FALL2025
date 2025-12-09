import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api'
import { useAuth } from '../contexts/AuthContext'
import Pill from '../components/ui/Pill'

export default function CreateThread() {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [newTagName, setNewTagName] = useState('')
  const [newTagWikidataId, setNewTagWikidataId] = useState('')
  const [showNewTagForm, setShowNewTagForm] = useState(false)
  const [wikidataSearchResults, setWikidataSearchResults] = useState<any[]>([])
  const [isSearchingWikidata, setIsSearchingWikidata] = useState(false)
  const [showWikidataResults, setShowWikidataResults] = useState(false)
  const wikidataSearchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const wikidataResultsRef = useRef<HTMLDivElement>(null)

  const { data: tagsData } = useQuery({
    queryKey: ['tags'],
    queryFn: async () => {
      const response = await api.get('/tags/')
      return response.data
    },
    enabled: isAuthenticated,
  })

  const { data: popularTagsData } = useQuery({
    queryKey: ['tags', 'popular'],
    queryFn: async () => {
      const response = await api.get('/tags/popular/')
      return response.data
    },
    enabled: isAuthenticated,
  })

  const searchWikidata = async (query: string) => {
    if (!query || query.length < 2) {
      setWikidataSearchResults([])
      setShowWikidataResults(false)
      return
    }

    setIsSearchingWikidata(true)
    try {
      const url = `https://www.wikidata.org/w/api.php?action=wbsearchentities&search=${encodeURIComponent(query)}&language=en&format=json&origin=*`
      const response = await fetch(url)
      
      if (response.ok) {
        const data = await response.json()
        if (data.search) {
          setWikidataSearchResults(data.search.slice(0, 5))
          setShowWikidataResults(true)
        } else {
          setWikidataSearchResults([])
          setShowWikidataResults(false)
        }
      }
    } catch (err) {
      console.error('Wikidata search error:', err)
      setWikidataSearchResults([])
      setShowWikidataResults(false)
    } finally {
      setIsSearchingWikidata(false)
    }
  }

  const debounceWikidataSearch = (query: string) => {
    if (wikidataSearchTimeoutRef.current) {
      clearTimeout(wikidataSearchTimeoutRef.current)
    }
    wikidataSearchTimeoutRef.current = setTimeout(() => {
      searchWikidata(query)
    }, 500)
  }

  const selectWikidataEntity = (entity: any) => {
    setNewTagWikidataId(entity.id)
    setNewTagName(entity.label || newTagName)
    setShowWikidataResults(false)
  }

  const createTagMutation = useMutation({
    mutationFn: async (tagData: { name: string; wikidata_id?: string }) => {
      const response = await api.post('/tags/', tagData)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      if (!selectedTags.includes(data.slug)) {
        setSelectedTags([...selectedTags, data.slug])
      }
      setNewTagName('')
      setNewTagWikidataId('')
      setShowNewTagForm(false)
    },
  })

  const handleCreateTag = async () => {
    if (!newTagName.trim()) {
      setError('Tag name is required')
      return
    }

    try {
      const tagData: any = { name: newTagName.trim() }
      if (newTagWikidataId) {
        tagData.wikidata_id = newTagWikidataId
      }
      await createTagMutation.mutateAsync(tagData)
    } catch (err: any) {
      setError(err.response?.data?.name?.[0] || err.response?.data?.detail || 'Failed to create tag')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!title.trim()) {
      setError('Title is required')
      return
    }

    if (!body.trim()) {
      setError('Body is required')
      return
    }

    setIsSubmitting(true)
    try {
      const threadData: any = {
        title: title.trim(),
        tags: selectedTags,
      }
      const threadResponse = await api.post('/threads/', threadData)
      const threadId = threadResponse.data.id

      await api.post('/posts/', {
        thread: threadId,
        body: body.trim(),
      })

      queryClient.invalidateQueries({ queryKey: ['threads'] })
      navigate(`/forum/${threadId}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.title?.[0] || 'Failed to create thread')
    } finally {
      setIsSubmitting(false)
    }
  }

  const toggleTag = (tagSlug: string) => {
    if (selectedTags.includes(tagSlug)) {
      setSelectedTags(selectedTags.filter(t => t !== tagSlug))
    } else {
      setSelectedTags([...selectedTags, tagSlug])
    }
  }

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wikidataResultsRef.current && !wikidataResultsRef.current.contains(event.target as Node)) {
        setShowWikidataResults(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  if (!isAuthenticated) {
    navigate('/login')
    return null
  }

  return (
    <div className="max-w-4xl mx-auto w-full">
      <button
        onClick={() => navigate('/forum')}
        className="mb-4 text-sm text-gray-600 hover:text-gray-900"
      >
        ← Back to Forum
      </button>

      <h1 className="text-2xl font-bold mb-6">Create New Thread</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Title *
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter thread title..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Content *
          </label>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Write your post content..."
            rows={10}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-gray-700">
              Tags
            </label>
            <button
              type="button"
              onClick={() => setShowNewTagForm(!showNewTagForm)}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              {showNewTagForm ? 'Cancel' : '+ Create New Tag'}
            </button>
          </div>

          {showNewTagForm && (
            <div className="mb-4 p-4 border border-gray-300 rounded-lg bg-gray-50">
              <div className="space-y-3">
                <div>
                  <input
                    type="text"
                    value={newTagName}
                    onChange={(e) => {
                      setNewTagName(e.target.value)
                      debounceWikidataSearch(e.target.value)
                    }}
                    placeholder="Tag name..."
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {isSearchingWikidata && (
                    <p className="text-xs text-gray-500 mt-1">Searching Wikidata...</p>
                  )}
                  {showWikidataResults && wikidataSearchResults.length > 0 && (
                    <div ref={wikidataResultsRef} className="mt-2 border border-gray-300 rounded bg-white shadow-lg z-10">
                      {wikidataSearchResults.map((entity) => (
                        <div
                          key={entity.id}
                          onClick={() => selectWikidataEntity(entity)}
                          className="px-3 py-2 hover:bg-gray-100 cursor-pointer border-b last:border-b-0"
                        >
                          <div className="font-medium">{entity.label}</div>
                          {entity.description && (
                            <div className="text-xs text-gray-500">{entity.description}</div>
                          )}
                          <div className="text-xs text-blue-600">{entity.id}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                {newTagWikidataId && (
                  <div className="text-xs text-gray-600">
                    Wikidata ID: {newTagWikidataId}
                  </div>
                )}
                <button
                  type="button"
                  onClick={handleCreateTag}
                  className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Create Tag
                </button>
              </div>
            </div>
          )}

          {popularTagsData && popularTagsData.length > 0 && (
            <div className="mb-3">
              <p className="text-xs text-gray-600 mb-2">Popular tags:</p>
              <div className="flex flex-wrap gap-2">
                {popularTagsData.map((tag: any) => (
                  <Pill
                    key={tag.slug}
                    active={selectedTags.includes(tag.slug)}
                    onClick={() => toggleTag(tag.slug)}
                  >
                    {tag.name}
                  </Pill>
                ))}
              </div>
            </div>
          )}

          {tagsData?.results && tagsData.results.length > 0 && (
            <div>
              <p className="text-xs text-gray-600 mb-2">All tags:</p>
              <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto">
                {tagsData.results.map((tag: any) => (
                  <Pill
                    key={tag.slug}
                    active={selectedTags.includes(tag.slug)}
                    onClick={() => toggleTag(tag.slug)}
                  >
                    {tag.name}
                  </Pill>
                ))}
              </div>
            </div>
          )}

          {selectedTags.length > 0 && (
            <div className="mt-3">
              <p className="text-xs text-gray-600 mb-2">Selected tags:</p>
              <div className="flex flex-wrap gap-2">
                {selectedTags.map((tagSlug) => (
                  <Pill
                    key={tagSlug}
                    active={true}
                    onClick={() => toggleTag(tagSlug)}
                  >
                    {tagSlug}
                  </Pill>
                ))}
              </div>
            </div>
          )}
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded text-red-600 text-sm">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {isSubmitting ? 'Creating...' : 'Create Thread'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/forum')}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}

