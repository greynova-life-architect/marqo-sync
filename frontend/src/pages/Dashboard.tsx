import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiService } from '../services/api'

function Dashboard() {
  const [status, setStatus] = useState<any>(null)
  const [indexes, setIndexes] = useState<any[]>([])
  const [config, setConfig] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const fetchData = async () => {
    try {
      if (!status && !config) {
        setLoading(true)
      }
      
      const [statusRes, indexesRes, configRes] = await Promise.allSettled([
        apiService.getStatus(),
        apiService.getIndexes(),
        apiService.getConfig()
      ])
      
      if (statusRes.status === 'fulfilled') {
        setStatus(statusRes.value.data)
      } else {
        console.error('Status API error:', statusRes.reason)
        if (!status) {
          setStatus({ status: 'unknown', indexers: {}, watchers: {} })
        }
      }
      
      if (indexesRes.status === 'fulfilled') {
        setIndexes(indexesRes.value.data?.indexes || [])
      } else {
        console.error('Indexes API error:', indexesRes.reason)
        if (indexes.length === 0) {
          setIndexes([])
        }
      }
      
      if (configRes.status === 'fulfilled') {
        setConfig(configRes.value.data)
      } else {
        console.error('Config API error:', configRes.reason)
        if (!config) {
          setConfig({ marqo_url: '', indexers: [] })
        }
      }
      
      setError(null)
    } catch (err: any) {
      console.error('Dashboard fetch error:', err)
      if (!status && !config) {
        setError(err.message || 'Failed to connect to API server. Make sure it is running on http://localhost:8000')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let mounted = true
    let intervalId: number | null = null
    
    const loadData = async () => {
      if (mounted) {
        await fetchData()
        if (mounted) {
          intervalId = window.setInterval(async () => {
            if (mounted) {
              await fetchData()
            }
          }, 30000)
        }
      }
    }
    
    loadData()
    
    return () => {
      mounted = false
      if (intervalId !== null) {
        clearInterval(intervalId)
      }
    }
  }, [])

  const hasCodebases = config?.indexers?.some((idx: any) => 
    idx.indexer_type === 'code' && idx.settings?.projects?.length > 0
  )
  const hasConversations = config?.indexers?.some((idx: any) => 
    idx.indexer_type === 'chathistory' && idx.settings?.conversation_types?.length > 0
  )
  const isConfigured = hasCodebases || hasConversations

  if (loading && !status && !config) {
    return (
      <div className="text-center p-5">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="mt-3 text-muted">Connecting to API...</p>
      </div>
    )
  }

  if (error && !status && !config) {
    return (
      <div className="container mt-5">
        <div className="alert alert-danger" role="alert">
          <h5><i className="fas fa-exclamation-triangle me-2"></i>Cannot Connect to API</h5>
          <p>{error}</p>
          <p className="small text-muted">
            Make sure the backend API server is running on <code>http://localhost:8000</code>
          </p>
          <div className="d-flex gap-2">
            <button className="btn btn-primary" onClick={fetchData}>
              Retry Connection
            </button>
            <button className="btn btn-outline-secondary" onClick={() => window.location.reload()}>
              Reload Page
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!isConfigured) {
    return (
      <div className="container mt-5">
        <div className="row justify-content-center">
          <div className="col-lg-8">
            <div className="card shadow border-0">
              <div className="card-body text-center p-5">
                <div className="mb-4">
                  <i className="fas fa-rocket" style={{ fontSize: '4rem', color: 'var(--clinical-accent)' }}></i>
                </div>
                <h2 className="mb-3" style={{ color: 'var(--clinical-text-primary)' }}>Welcome to Marqo Sync</h2>
                <p className="text-muted mb-4">
                  Get started by configuring your indexers. We'll guide you through the setup process.
                </p>
                <div className="d-grid gap-2 d-md-flex justify-content-md-center">
                  <button
                    className="btn btn-primary btn-lg"
                    onClick={() => navigate('/onboarding')}
                  >
                    Start Setup Wizard
                  </button>
                  <button
                    className="btn btn-outline-primary btn-lg"
                    onClick={() => navigate('/configuration')}
                  >
                    Manual Configuration
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 style={{ color: 'var(--clinical-text-primary)' }}>Dashboard</h1>
        <button className="btn btn-outline-secondary" onClick={fetchData}>
          <i className="fas fa-sync-alt me-1"></i>Refresh
        </button>
      </div>

      <div className="row mb-4">
        <div className="col-md-4">
          <div className="card border-0 shadow-sm">
            <div className="card-body">
              <div className="d-flex align-items-center">
                <div className="flex-grow-1">
                  <h6 className="text-muted mb-1">Service Status</h6>
                  <h4 className="mb-0">
                    <span className={`badge bg-${
                      status?.status === 'running' ? 'success' :
                      status?.status === 'ready' ? 'info' :
                      status?.status === 'stopped' ? 'secondary' : 'warning'
                    }`}>
                      {status?.status?.toUpperCase() || 'UNKNOWN'}
                    </span>
                  </h4>
                </div>
                <div className="fs-1">
                  <i className={`fas ${status?.status === 'running' ? 'fa-check-circle text-success' : 'fa-pause-circle text-muted'}`}></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="col-md-4">
          <div className="card border-0 shadow-sm">
            <div className="card-body">
              <div className="d-flex align-items-center">
                <div className="flex-grow-1">
                  <h6 className="text-muted mb-1">Total Indexes</h6>
                  <h4 className="mb-0">{indexes.length}</h4>
                </div>
                <div className="fs-1">
                  <i className="fas fa-database text-info"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="col-md-4">
          <div className="card border-0 shadow-sm">
            <div className="card-body">
              <div className="d-flex align-items-center">
                <div className="flex-grow-1">
                  <h6 className="text-muted mb-1">Active Watchers</h6>
                  <h4 className="mb-0">
                    {Object.keys(status?.watchers || {}).length}
                  </h4>
                </div>
                <div className="fs-1">
                  <i className="fas fa-eye text-warning"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="row mb-4">
        <div className="col-md-12">
          <div className="card border-0 shadow-sm">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Configured Indexers</h5>
              <button
                className="btn btn-sm btn-primary"
                onClick={() => navigate('/configuration')}
              >
                <i className="fas fa-plus me-1"></i>Add Indexer
              </button>
            </div>
            <div className="card-body">
              {config?.indexers?.length > 0 ? (
                <div className="row">
                  {config.indexers.map((indexer: any, idx: number) => {
                    const typeInfo: Record<string, {icon: string, name: string, color: string}> = {
                      'code': { icon: 'fa-code', name: 'Codebase', color: 'primary' },
                      'codex': { icon: 'fa-sitemap', name: 'Codex', color: 'info' },
                      'chathistory': { icon: 'fa-comments', name: 'Conversations', color: 'success' },
                      'conversation': { icon: 'fa-comments', name: 'Conversations', color: 'success' }
                    }
                    const info = typeInfo[indexer.indexer_type] || { icon: 'fa-file', name: indexer.indexer_type, color: 'secondary' }
                    const itemCount = indexer.settings?.projects?.length || indexer.settings?.conversation_types?.length || 0
                    
                    return (
                      <div key={idx} className="col-md-4 mb-3">
                        <div className="card h-100 border-0 shadow-sm">
                          <div className="card-body">
                            <div className="d-flex align-items-center mb-2">
                              <i className={`fas ${info.icon} me-2`} style={{ fontSize: '1.5rem', color: `var(--clinical-accent)` }}></i>
                              <div className="flex-grow-1">
                                <h6 className="mb-0">{info.name}</h6>
                                <small className="text-muted">Index: {indexer.index_name}</small>
                              </div>
                              <span className={`status-badge ${indexer.enabled ? 'active' : 'inactive'}`}>
                                {indexer.enabled ? 'Active' : 'Disabled'}
                              </span>
                            </div>
                            <div className="mt-2">
                              <small className="text-muted">
                                {itemCount > 0 ? (
                                  <span>{itemCount} {indexer.settings?.projects ? 'project(s)' : 'type(s)'} configured</span>
                                ) : (
                                  <span className="text-warning">No items configured</span>
                                )}
                              </small>
                            </div>
                            <div className="mt-3">
                              <button
                                className="btn btn-sm btn-outline-primary w-100"
                                onClick={() => navigate(`/configuration?focus=${indexer.indexer_type === 'code' ? 'codebase' : indexer.indexer_type === 'chathistory' ? 'conversations' : indexer.indexer_type}`)}
                              >
                                Configure
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-muted mb-3">No indexers configured yet</p>
                  <button
                    className="btn btn-primary"
                    onClick={() => navigate('/configuration')}
                  >
                    Configure Your First Indexer
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="row mb-4">
        <div className="col-md-6">
          <div className="card border-0 shadow-sm">
            <div className="card-header">
              <h5 className="mb-0">Quick Actions</h5>
            </div>
            <div className="card-body">
              <div className="d-grid gap-2">
                <button
                  className="btn btn-outline-secondary"
                  onClick={() => navigate('/configuration')}
                >
                  <i className="fas fa-cog me-2"></i>Configure Indexers
                </button>
                <button
                  className="btn btn-outline-secondary"
                  onClick={() => navigate('/index-management')}
                >
                  <i className="fas fa-database me-2"></i>View All Indexes
                </button>
                <button
                  className="btn btn-outline-secondary"
                  onClick={() => navigate('/profiles')}
                >
                  <i className="fas fa-user me-2"></i>Manage Profiles
                </button>
                <button
                  className="btn btn-outline-secondary"
                  onClick={() => navigate('/conversations')}
                >
                  <i className="fas fa-comments me-2"></i>View Conversations
                </button>
                <button
                  className="btn btn-outline-secondary"
                  onClick={() => navigate('/memories')}
                >
                  <i className="fas fa-brain me-2"></i>Search Memories
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="col-md-6">
          <div className="card border-0 shadow-sm">
            <div className="card-header">
              <h5 className="mb-0">Indexes Overview</h5>
            </div>
            <div className="card-body">
              {indexes.length === 0 ? (
                <p className="text-muted mb-0">No indexes found. Start indexing to create indexes.</p>
              ) : (
                <div className="list-group list-group-flush">
                  {indexes.slice(0, 3).map((index) => (
                    <div key={index.name} className="list-group-item border-0 px-0">
                      <div className="d-flex justify-content-between align-items-center">
                        <div>
                          <strong>{index.name}</strong>
                          <br />
                          <small className="text-muted">
                            {index.document_count.toLocaleString()} documents
                          </small>
                        </div>
                        <span className={`badge bg-${
                          index.type === 'codebase' ? 'primary' :
                          index.type === 'codex' ? 'info' :
                          index.type === 'conversations' ? 'success' : 'secondary'
                        }`}>
                          {index.type}
                        </span>
                      </div>
                    </div>
                  ))}
                      {indexes.length > 3 && (
                        <button
                          className="btn btn-link text-decoration-none p-0 mt-2"
                          onClick={() => navigate('/index-management')}
                        >
                          View all {indexes.length} indexes →
                        </button>
                      )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="row">
        <div className="col-md-6">
          <div className="card border-0 shadow-sm">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Active Watchers</h5>
              <span className="badge bg-primary">
                {Object.keys(status?.watchers || {}).length}
              </span>
            </div>
            <div className="card-body">
              {Object.keys(status?.watchers || {}).length === 0 ? (
                <p className="text-muted mb-0">No active watchers</p>
              ) : (
                <div className="list-group list-group-flush">
                  {Object.entries(status?.watchers || {}).map(([name, watcher]: [string, any]) => (
                    <div key={name} className="list-group-item border-0 px-0">
                      <div className="d-flex justify-content-between align-items-center">
                        <div>
                          <strong>{name}</strong>
                          <br />
                          <small className="text-muted">{watcher.root_dir || 'N/A'}</small>
                        </div>
                        <span className={`badge bg-${watcher.watching ? 'success' : 'secondary'}`}>
                          {watcher.watching ? 'Watching' : 'Stopped'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
