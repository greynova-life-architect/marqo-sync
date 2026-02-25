import { useEffect, useState } from 'react'
import { apiService } from '../services/api'

function Memories() {
  const [memories, setMemories] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState({
    tenant_id: '',
    agent_id: '',
    user_id: '',
    memory_type: '',
    min_importance: '0.0'
  })

  const fetchMemories = async () => {
    try {
      const params = new URLSearchParams()
      params.append('query', query || '')
      if (filters.tenant_id) params.append('tenant_id', filters.tenant_id)
      if (filters.agent_id) params.append('agent_id', filters.agent_id)
      if (filters.user_id) params.append('user_id', filters.user_id)
      if (filters.memory_type) params.append('memory_type', filters.memory_type)
      if (filters.min_importance) params.append('min_importance', filters.min_importance)
      
      const response = await fetch(`/api/memories?${params}`)
      const data = await response.json()
      setMemories(data.memories || [])
    } catch (err: any) {
      console.error('Failed to fetch memories:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (query) {
      fetchMemories()
    } else {
      setMemories([])
      setLoading(false)
    }
  }, [query, filters])

  if (loading) {
    return <div className="text-center p-5">Loading memories...</div>
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h1 className="mb-1">Memories</h1>
          <p className="text-muted mb-0">Search and manage agent memories</p>
        </div>
      </div>

      <div className="card mb-4">
        <div className="card-body">
          <div className="mb-3">
            <label className="form-label">Search Query</label>
            <input
              type="text"
              className="form-control"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter search query..."
            />
          </div>
          <div className="row g-3">
            <div className="col-md-3">
              <label className="form-label">Tenant ID</label>
              <input
                type="text"
                className="form-control"
                value={filters.tenant_id}
                onChange={(e) => setFilters({...filters, tenant_id: e.target.value})}
              />
            </div>
            <div className="col-md-3">
              <label className="form-label">Agent ID</label>
              <input
                type="text"
                className="form-control"
                value={filters.agent_id}
                onChange={(e) => setFilters({...filters, agent_id: e.target.value})}
              />
            </div>
            <div className="col-md-3">
              <label className="form-label">Memory Type</label>
              <select
                className="form-select"
                value={filters.memory_type}
                onChange={(e) => setFilters({...filters, memory_type: e.target.value})}
              >
                <option value="">All Types</option>
                <option value="short_term">Short Term</option>
                <option value="long_term">Long Term</option>
                <option value="semantic">Semantic</option>
                <option value="procedural">Procedural</option>
              </select>
            </div>
            <div className="col-md-3">
              <label className="form-label">Min Importance</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="1"
                className="form-control"
                value={filters.min_importance}
                onChange={(e) => setFilters({...filters, min_importance: e.target.value})}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="row">
        {memories.map((memory) => (
          <div key={memory._id} className="col-md-6 mb-3">
            <div className="card">
              <div className="card-body">
                <div className="d-flex justify-content-between align-items-start mb-2">
                  <span className="badge bg-primary">{memory.memory_type}</span>
                  <span className="badge bg-info">Importance: {memory.importance_score?.toFixed(2)}</span>
                </div>
                <p className="card-text">{memory.content}</p>
                <div className="small text-muted">
                  {memory.agent_id && <span>Agent: {memory.agent_id} </span>}
                  {memory.user_id && <span>User: {memory.user_id} </span>}
                  {memory.access_count && <span>Accessed: {memory.access_count} times</span>}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {query && memories.length === 0 && (
        <div className="text-center p-5">
          <p className="text-muted">No memories found for your query</p>
        </div>
      )}

      {!query && (
        <div className="text-center p-5">
          <p className="text-muted">Enter a search query to retrieve memories</p>
        </div>
      )}
    </div>
  )
}

export default Memories

