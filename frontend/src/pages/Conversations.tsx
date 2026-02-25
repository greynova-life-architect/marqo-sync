import { useEffect, useState } from 'react'
import { apiService } from '../services/api'

function Conversations() {
  const [conversations, setConversations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedConversation, setSelectedConversation] = useState<any>(null)
  const [filters, setFilters] = useState({ tenant_id: '', status: '', query: '' })

  const fetchConversations = async () => {
    try {
      const params = new URLSearchParams()
      if (filters.tenant_id) params.append('tenant_id', filters.tenant_id)
      if (filters.status) params.append('status', filters.status)
      if (filters.query) params.append('query', filters.query)
      
      const response = await fetch(`/api/conversations?${params}`)
      const data = await response.json()
      setConversations(data.conversations || [])
    } catch (err: any) {
      console.error('Failed to fetch conversations:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchConversationDetails = async (conversationId: string) => {
    try {
      const response = await fetch(`/api/conversations/${conversationId}`)
      const data = await response.json()
      setSelectedConversation(data)
    } catch (err: any) {
      console.error('Failed to fetch conversation details:', err)
    }
  }

  useEffect(() => {
    fetchConversations()
  }, [filters])

  if (loading) {
    return <div className="text-center p-5">Loading conversations...</div>
  }

  return (
    <div className="row">
      <div className="col-md-4">
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">Conversations</h5>
          </div>
          <div className="card-body">
            <div className="mb-3">
              <input
                type="text"
                className="form-control"
                placeholder="Search..."
                value={filters.query}
                onChange={(e) => setFilters({...filters, query: e.target.value})}
              />
            </div>
            <div className="mb-3">
              <select
                className="form-select"
                value={filters.status}
                onChange={(e) => setFilters({...filters, status: e.target.value})}
              >
                <option value="">All Status</option>
                <option value="active">Active</option>
                <option value="paused">Paused</option>
                <option value="archived">Archived</option>
              </select>
            </div>
            <div className="list-group">
              {conversations.map((conv) => (
                <button
                  key={conv._id}
                  className={`list-group-item list-group-item-action ${selectedConversation?._id === conv._id ? 'active' : ''}`}
                  onClick={() => fetchConversationDetails(conv._id)}
                >
                  <div className="d-flex justify-content-between">
                    <div>
                      <strong>{conv.topic || 'Untitled'}</strong>
                      <br />
                      <small>{conv.category || 'No category'}</small>
                    </div>
                    <span className={`badge bg-${
                      conv.status === 'active' ? 'success' :
                      conv.status === 'archived' ? 'secondary' : 'warning'
                    }`}>
                      {conv.status}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
      <div className="col-md-8">
        {selectedConversation ? (
          <div className="card">
            <div className="card-header d-flex justify-content-between">
              <h5 className="mb-0">{selectedConversation.topic || 'Conversation'}</h5>
              <span className="badge bg-secondary">{selectedConversation.status}</span>
            </div>
            <div className="card-body">
              <div className="mb-3">
                <strong>Thread ID:</strong> {selectedConversation.thread_id}
                <br />
                <strong>Total Turns:</strong> {selectedConversation.total_turns || 0}
              </div>
              <div className="border-top pt-3">
                <h6>Messages</h6>
                <div className="list-group">
                  {selectedConversation.messages?.map((msg: any) => (
                    <div key={msg._id} className="list-group-item">
                      <div className="d-flex justify-content-between mb-1">
                        <strong>{msg.role}</strong>
                        <small className="text-muted">Turn {msg.turn_number}</small>
                      </div>
                      <p className="mb-0">{msg.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="card">
            <div className="card-body text-center p-5">
              <p className="text-muted">Select a conversation to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Conversations

