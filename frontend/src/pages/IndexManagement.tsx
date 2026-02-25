import { useEffect, useState } from 'react'
import { apiService } from '../services/api'
import { useNavigate } from 'react-router-dom'
import CreateIndexModal from '../components/IndexManagement/CreateIndexModal'

interface IndexDetail {
  name: string
  type: string
  document_count: number
  size: number
  sources?: Array<{ name: string, path: string, type: string }>
  settings?: any
  error?: string
  indexer_type?: string
  indexer_name?: string
}

interface ConfiguredSource {
  name: string
  path: string
  indexerType: string
  indexerName: string
  indexName: string
  enabled: boolean
}

function IndexManagement() {
  const navigate = useNavigate()
  const [indexes, setIndexes] = useState<IndexDetail[]>([])
  const [config, setConfig] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [selectedIndex, setSelectedIndex] = useState<string | null>(null)
  const [filter, setFilter] = useState<string>('all')
  const [showCreateModal, setShowCreateModal] = useState(false)

  const fetchData = async () => {
    try {
      setLoading(true)
      const [indexesRes, configRes] = await Promise.allSettled([
        apiService.getIndexes(),
        apiService.getConfig()
      ])
      
      if (indexesRes.status === 'fulfilled') {
        const indexesData = indexesRes.value.data?.indexes || indexesRes.value.data || []
        console.log('Fetched indexes:', indexesData)
        setIndexes(Array.isArray(indexesData) ? indexesData : [])
      } else {
        console.error('Failed to fetch indexes:', indexesRes.reason)
        console.error('Error details:', indexesRes.reason?.response?.data || indexesRes.reason?.message)
        setIndexes([])
      }
      
      if (configRes.status === 'fulfilled') {
        setConfig(configRes.value.data)
      } else {
        console.error('Failed to fetch config:', configRes.reason)
        setConfig(null)
      }
    } catch (err: any) {
      console.error('Failed to fetch data:', err)
      console.error('Error details:', err?.response?.data || err?.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const getConfiguredSources = (): ConfiguredSource[] => {
    if (!config?.indexers) return []
    
    const sources: ConfiguredSource[] = []
    
    config.indexers.forEach((indexer: any) => {
      if (indexer.indexer_type === 'code' || indexer.indexer_type === 'codex') {
        if (indexer.settings?.projects) {
          indexer.settings.projects.forEach((item: any) => {
            const [name, path] = Array.isArray(item) ? item : [item.name || '', item.path || '']
            if (name && path) {
              const normalizedName = name.toLowerCase().replace(/[^a-z0-9]/g, '-')
              sources.push({
                name,
                path,
                indexerType: indexer.indexer_type,
                indexerName: getIndexerName(indexer.indexer_type),
                indexName: `${indexer.index_name}-${normalizedName}`,
                enabled: indexer.enabled
              })
            }
          })
        }
      }
      
      if (indexer.indexer_type === 'chathistory' || indexer.indexer_type === 'conversation') {
        if (indexer.settings?.conversation_types) {
          indexer.settings.conversation_types.forEach((item: any) => {
            const [type, path] = Array.isArray(item) ? item : [item.type || '', item.path || '']
            if (type && path) {
              const normalizedType = type.toLowerCase().replace(/[^a-z0-9]/g, '-')
              sources.push({
                name: type,
                path,
                indexerType: indexer.indexer_type,
                indexerName: getIndexerName(indexer.indexer_type),
                indexName: `${indexer.index_name}-${normalizedType}`,
                enabled: indexer.enabled
              })
            }
          })
        }
      }
    })
    
    return sources
  }

  const getIndexSources = (indexName: string): Array<{ name: string, path: string, type: string }> => {
    if (!config?.indexers) return []
    
    const sources: Array<{ name: string, path: string, type: string }> = []
    
    config.indexers.forEach((indexer: any) => {
      if (indexer.indexer_type === 'code' || indexer.indexer_type === 'codex') {
        if (indexer.settings?.projects) {
          indexer.settings.projects.forEach((item: any) => {
            const [name, path] = Array.isArray(item) ? item : [item.name || '', item.path || '']
            const normalizedName = name.toLowerCase().replace(/[^a-z0-9]/g, '-')
            const expectedIndexName = `${indexer.index_name}-${normalizedName}`.toLowerCase()
            if (indexName.toLowerCase() === expectedIndexName) {
              sources.push({ name, path, type: indexer.indexer_type === 'code' ? 'codebase' : 'codex' })
            }
          })
        }
      }
      
      if (indexer.indexer_type === 'chathistory' || indexer.indexer_type === 'conversation') {
        if (indexer.settings?.conversation_types) {
          indexer.settings.conversation_types.forEach((item: any) => {
            const [type, path] = Array.isArray(item) ? item : [item.type || '', item.path || '']
            const normalizedType = type.toLowerCase().replace(/[^a-z0-9]/g, '-')
            const expectedIndexName = `${indexer.index_name}-${normalizedType}`.toLowerCase()
            if (indexName.toLowerCase() === expectedIndexName) {
              sources.push({ name: type, path, type: 'conversation' })
            }
          })
        }
      }
    })
    
    return sources
  }

  const getIndexerForIndex = (indexName: string) => {
    return config?.indexers?.find((idx: any) => {
      if (idx.indexer_type === 'code' || idx.indexer_type === 'codex') {
        if (idx.settings?.projects) {
          return idx.settings.projects.some((item: any) => {
            const [name] = Array.isArray(item) ? item : [item.name || '']
            const normalizedName = name.toLowerCase().replace(/[^a-z0-9]/g, '-')
            return indexName.toLowerCase() === `${idx.index_name}-${normalizedName}`.toLowerCase()
          })
        }
      }
      if (idx.indexer_type === 'chathistory' || idx.indexer_type === 'conversation') {
        if (idx.settings?.conversation_types) {
          return idx.settings.conversation_types.some((item: any) => {
            const [type] = Array.isArray(item) ? item : [item.type || '']
            const normalizedType = type.toLowerCase().replace(/[^a-z0-9]/g, '-')
            return indexName.toLowerCase() === `${idx.index_name}-${normalizedType}`.toLowerCase()
          })
        }
      }
      return false
    })
  }

  const getTypeBadgeColor = (type: string) => {
    switch (type) {
      case 'codebase': return 'primary'
      case 'codex': return 'info'
      case 'conversations': return 'success'
      case 'profiles': return 'warning'
      case 'memories': return 'danger'
      case 'categories': return 'dark'
      default: return 'secondary'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'codebase': return 'fa-code'
      case 'codex': return 'fa-sitemap'
      case 'conversations': return 'fa-comments'
      case 'profiles': return 'fa-user'
      case 'memories': return 'fa-brain'
      case 'categories': return 'fa-tags'
      default: return 'fa-file'
    }
  }

  const getIndexerIcon = (indexerType: string) => {
    switch (indexerType) {
      case 'code': return 'fa-code'
      case 'codex': return 'fa-sitemap'
      case 'chathistory':
      case 'conversation': return 'fa-comments'
      default: return 'fa-cog'
    }
  }

  const getIndexerName = (indexerType: string) => {
    switch (indexerType) {
      case 'code': return 'Codebase'
      case 'codex': return 'Codex'
      case 'chathistory':
      case 'conversation': return 'Conversation'
      default: return 'Generic'
    }
  }

  const getTypeDescription = (indexName: string, type: string) => {
    const descriptions: Record<string, string> = {
      'codebase': 'Source code repositories and files',
      'codex': 'Folder structures and directory layouts',
      'conversations': 'AI conversation metadata and threads',
      'conversation_messages': 'Individual messages within conversations',
      'profiles': 'User, agent, and organization profiles',
      'memories': 'Agent and user memories for context',
      'categories': 'Category hierarchy and organization'
    }
    return descriptions[indexName] || descriptions[type] || 'Indexed content'
  }

  const filteredIndexes = indexes.filter(idx => {
    if (filter === 'all') return true
    if (filter === 'code') return idx.type === 'codebase' || idx.type === 'codex'
    if (filter === 'conversations') return idx.type === 'conversations' || idx.name.includes('conversation')
    if (filter === 'data') return ['profiles', 'memories', 'categories'].includes(idx.type)
    return true
  })

  const totalDocuments = indexes.reduce((sum, idx) => sum + idx.document_count, 0)
  const totalSize = indexes.reduce((sum, idx) => sum + idx.size, 0)
  const configuredSources = getConfiguredSources()

  if (loading) {
    return <div className="text-center p-5">Loading indexes...</div>
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h1 className="mb-1">Index Management</h1>
          <p className="text-muted mb-0">Manage configured sources and monitor Marqo indexes</p>
        </div>
        <div>
          <button className="btn btn-outline-secondary me-2" onClick={fetchData}>
            <i className="fas fa-sync-alt me-1"></i>Refresh
          </button>
          <button className="btn btn-success me-2" onClick={() => setShowCreateModal(true)}>
            <i className="fas fa-plus me-1"></i>Create Index
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/configuration')}>
            <i className="fas fa-cog me-1"></i>Configure Indexers
          </button>
        </div>
      </div>

      <div className="row mb-4">
        <div className="col-md-3">
          <div className="card border-0 shadow-sm">
            <div className="card-body text-center">
              <h6 className="text-muted mb-1">Configured Sources</h6>
              <h3 className="mb-0">{configuredSources.length}</h3>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card border-0 shadow-sm">
            <div className="card-body text-center">
              <h6 className="text-muted mb-1">Total Indexes</h6>
              <h3 className="mb-0">{indexes.length}</h3>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card border-0 shadow-sm">
            <div className="card-body text-center">
              <h6 className="text-muted mb-1">Total Documents</h6>
              <h3 className="mb-0">{totalDocuments.toLocaleString()}</h3>
            </div>
          </div>
        </div>
        <div className="col-md-3">
          <div className="card border-0 shadow-sm">
            <div className="card-body text-center">
              <h6 className="text-muted mb-1">Total Size</h6>
              <h3 className="mb-0">
                {totalSize > 0 ? `${(totalSize / 1024 / 1024).toFixed(2)} MB` : 'N/A'}
              </h3>
            </div>
          </div>
        </div>
      </div>

      <div className="card mb-4 border-0 shadow-sm">
        <div className="card-header d-flex justify-content-between align-items-center">
          <div>
            <h5 className="mb-0"><i className="fas fa-folder me-2"></i>Configured Sources</h5>
            <small className="text-muted">Folders and paths configured for syncing to Marqo indexes</small>
          </div>
          <button className="btn btn-sm btn-primary" onClick={() => navigate('/configuration')}>
            <i className="fas fa-cog me-1"></i>Manage Sources
          </button>
        </div>
        <div className="card-body">
          {configuredSources.length === 0 ? (
            <div className="text-center py-5">
              <h5>No Sources Configured</h5>
              <p className="text-muted">Configure folders to start syncing data to Marqo indexes.</p>
              <button className="btn btn-primary" onClick={() => navigate('/configuration')}>
                Configure Your First Source
              </button>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover mb-0">
                <thead>
                  <tr>
                    <th>Source Name</th>
                    <th>Folder Path</th>
                    <th>Indexer</th>
                    <th>Index Name</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {configuredSources.map((source, idx) => {
                    const indexExists = indexes.some(idx => idx.name.toLowerCase() === source.indexName.toLowerCase())
                    return (
                      <tr key={idx}>
                        <td>
                          <strong>{source.name}</strong>
                        </td>
                        <td>
                          <code className="small">{source.path}</code>
                        </td>
                        <td>
                          <span className="badge bg-info">
                            <i className={`fas ${getIndexerIcon(source.indexerType)} me-1`}></i>{source.indexerName}
                          </span>
                        </td>
                        <td>
                          <code className="small">{source.indexName}</code>
                        </td>
                        <td>
                          <div className="d-flex align-items-center gap-2">
                            <span className={`badge bg-${source.enabled ? 'success' : 'secondary'}`}>
                              {source.enabled ? 'Enabled' : 'Disabled'}
                            </span>
                            {indexExists ? (
                              <span className="badge bg-success">Index Exists</span>
                            ) : (
                              <span className="badge bg-warning">Index Not Created</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <div className="card mb-4 border-0 shadow-sm">
        <div className="card-header">
          <div className="d-flex justify-content-between align-items-center">
            <h5 className="mb-0"><i className="fas fa-database me-2"></i>Marqo Indexes</h5>
            <div className="btn-group" role="group">
              <button
                className={`btn btn-sm ${filter === 'all' ? 'btn-primary' : 'btn-outline-primary'}`}
                onClick={() => setFilter('all')}
              >
                All ({indexes.length})
              </button>
              <button
                className={`btn btn-sm ${filter === 'code' ? 'btn-primary' : 'btn-outline-primary'}`}
                onClick={() => setFilter('code')}
              >
                <i className="fas fa-code me-1"></i>Code ({indexes.filter(idx => idx.type === 'codebase' || idx.type === 'codex').length})
              </button>
              <button
                className={`btn btn-sm ${filter === 'conversations' ? 'btn-primary' : 'btn-outline-primary'}`}
                onClick={() => setFilter('conversations')}
              >
                <i className="fas fa-comments me-1"></i>Conversations ({indexes.filter(idx => idx.type === 'conversations' || idx.name.includes('conversation')).length})
              </button>
              <button
                className={`btn btn-sm ${filter === 'data' ? 'btn-primary' : 'btn-outline-primary'}`}
                onClick={() => setFilter('data')}
              >
                <i className="fas fa-database me-1"></i>Data ({indexes.filter(idx => ['profiles', 'memories', 'categories'].includes(idx.type)).length})
              </button>
            </div>
          </div>
        </div>
        <div className="card-body">
          {filteredIndexes.length === 0 ? (
            <div className="text-center py-5">
              <h4>No indexes found</h4>
              <p className="text-muted">Indexes will be created when you start syncing configured sources.</p>
              <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
                <i className="fas fa-plus me-1"></i>Create Your First Index
              </button>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover">
                <thead>
                  <tr>
                    <th>Index Name</th>
                    <th>Type</th>
                    <th>Indexer</th>
                    <th>Sources</th>
                    <th>Documents</th>
                    <th>Size</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredIndexes.map((index) => {
                    const indexer = getIndexerForIndex(index.name)
                    const sources = getIndexSources(index.name)
                    return (
                      <tr key={index.name}>
                        <td>
                          <div>
                            <strong>{index.name}</strong>
                            {index.error && (
                              <div className="text-danger small mt-1">{index.error}</div>
                            )}
                            <div className="small text-muted mt-1">
                              {getTypeDescription(index.name, index.type)}
                            </div>
                          </div>
                        </td>
                        <td>
                          <span className={`badge bg-${getTypeBadgeColor(index.type)}`}>
                            <i className={`fas ${getTypeIcon(index.type)} me-1`}></i>{index.type}
                          </span>
                        </td>
                        <td>
                          {indexer ? (
                            <div>
                              <span className="badge bg-info" title={`Uses ${getIndexerName(indexer.indexer_type)}`}>
                                <i className={`fas ${getIndexerIcon(indexer.indexer_type)} me-1`}></i>{getIndexerName(indexer.indexer_type)}
                              </span>
                              <div className="small text-muted mt-1">
                                Base: {indexer.index_name}
                              </div>
                            </div>
                          ) : (
                            <span className="text-muted small">N/A</span>
                          )}
                        </td>
                        <td>
                          {sources.length > 0 ? (
                            <div>
                              {sources.map((source, sIdx) => (
                                <div key={sIdx} className="mb-1">
                                  <div>
                                    <strong className="small">{source.name}</strong>
                                  </div>
                                  <code className="small text-muted">{source.path}</code>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <span className="text-muted small">No sources</span>
                          )}
                        </td>
                        <td>{index.document_count.toLocaleString()}</td>
                        <td>{index.size > 0 ? `${(index.size / 1024 / 1024).toFixed(2)} MB` : 'N/A'}</td>
                        <td>
                          <div className="btn-group" role="group">
                            <button
                              className="btn btn-sm btn-outline-primary"
                              onClick={() => setSelectedIndex(selectedIndex === index.name ? null : index.name)}
                              title="Show details"
                            >
                              {selectedIndex === index.name ? 'Hide' : 'Show'} Details
                            </button>
                            <button
                              className="btn btn-sm btn-outline-secondary"
                              onClick={async () => {
                                try {
                                  const stats = await apiService.getIndexStats(index.name)
                                  const statsStr = JSON.stringify(stats.data, null, 2)
                                  const newWindow = window.open('', '_blank')
                                  if (newWindow) {
                                    newWindow.document.write(`
                                      <html>
                                        <head><title>Index Stats: ${index.name}</title></head>
                                        <body style="font-family: monospace; padding: 20px;">
                                          <h2>Index: ${index.name}</h2>
                                          <pre>${statsStr}</pre>
                                        </body>
                                      </html>
                                    `)
                                  } else {
                                    alert(`Index Stats:\n${statsStr}`)
                                  }
                                } catch (err: any) {
                                  alert(`Error: ${err.message}`)
                                }
                              }}
                              title="View statistics"
                            >
                              <i className="fas fa-chart-bar me-1"></i>Stats
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {selectedIndex && (
        <div className="card mb-4 border-0 shadow-sm">
          <div className="card-header">
            <h5 className="mb-0">Index Details: {selectedIndex}</h5>
          </div>
          <div className="card-body">
            {(() => {
              const index = indexes.find(idx => idx.name === selectedIndex)
              if (!index) return null
              const sources = getIndexSources(index.name)
              const indexer = getIndexerForIndex(index.name)
              
              return (
                <div>
                  {sources.length > 0 ? (
                    <div>
                      <h6 className="mb-3">Indexed Sources:</h6>
                      <div className="list-group">
                        {sources.map((source, idx) => (
                          <div key={idx} className="list-group-item">
                            <div className="d-flex justify-content-between align-items-center">
                              <div>
                                <strong>{source.name}</strong>
                                <br />
                                <code className="small text-muted">{source.path}</code>
                              </div>
                              <span className={`badge bg-${getTypeBadgeColor(source.type)}`}>
                                {source.type}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="alert alert-warning mb-0">
                      No sources configured for this index. <a href="/configuration" className="alert-link">Configure sources</a>
                    </div>
                  )}
                  
                  {indexer && (
                    <div className="mt-3 pt-3 border-top">
                      <h6 className="mb-2">Indexer Information:</h6>
                      <div className="alert alert-info mb-0">
                        <strong>Indexer Type:</strong> {getIndexerName(indexer.indexer_type)}<br />
                        <strong>Base Index Name:</strong> {indexer.index_name}<br />
                        <strong>Status:</strong> <span className={`badge bg-${indexer.enabled ? 'success' : 'secondary'}`}>
                          {indexer.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )
            })()}
          </div>
        </div>
      )}

      <CreateIndexModal
        show={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => {
          fetchData()
          setShowCreateModal(false)
        }}
      />
    </div>
  )
}

export default IndexManagement
