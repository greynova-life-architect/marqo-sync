import { useEffect, useState } from 'react'
import { apiService } from '../services/api'

function Indexes() {
  const [indexes, setIndexes] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchIndexes = async () => {
    try {
      const response = await apiService.getIndexes()
      setIndexes(response.data.indexes)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch indexes')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchIndexes()
    const interval = setInterval(fetchIndexes, 10000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return <div className="text-center p-5">Loading indexes...</div>
  }

  if (error) {
    return (
      <div className="alert alert-danger" role="alert">
        Error: {error}
      </div>
    )
  }

  const getTypeBadgeColor = (type: string) => {
    switch (type) {
      case 'codebase':
        return 'primary'
      case 'codex':
        return 'info'
      case 'conversations':
        return 'success'
      case 'profiles':
        return 'warning'
      case 'memories':
        return 'danger'
      case 'categories':
        return 'dark'
      default:
        return 'secondary'
    }
  }
  
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'codebase':
        return 'fa-code'
      case 'codex':
        return 'fa-sitemap'
      case 'conversations':
        return 'fa-comments'
      case 'profiles':
        return 'fa-user'
      case 'memories':
        return 'fa-brain'
      case 'categories':
        return 'fa-tags'
      default:
        return 'fa-file'
    }
  }

  const totalDocuments = indexes.reduce((sum, idx) => sum + idx.document_count, 0)

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h1 className="mb-1">Indexes</h1>
          <p className="text-muted mb-0">Manage and monitor your Marqo indexes</p>
        </div>
        <button className="btn btn-outline-secondary" onClick={fetchIndexes}>
          <i className="fas fa-sync-alt me-1"></i>Refresh
        </button>
      </div>

      {indexes.length > 0 && (
        <div className="row mb-4">
          <div className="col-md-4">
            <div className="card border-0 shadow-sm">
              <div className="card-body">
                <h6 className="text-muted mb-1">Total Indexes</h6>
                <h3 className="mb-0">{indexes.length}</h3>
              </div>
            </div>
          </div>
          <div className="col-md-4">
            <div className="card border-0 shadow-sm">
              <div className="card-body">
                <h6 className="text-muted mb-1">Total Documents</h6>
                <h3 className="mb-0">{totalDocuments.toLocaleString()}</h3>
              </div>
            </div>
          </div>
          <div className="col-md-4">
            <div className="card border-0 shadow-sm">
              <div className="card-body">
                <h6 className="text-muted mb-1">Index Types</h6>
                <h3 className="mb-0">
                  {new Set(indexes.map(idx => idx.type)).size}
                </h3>
              </div>
            </div>
          </div>
        </div>
      )}

      {indexes.length === 0 ? (
        <div className="card border-0 shadow-sm">
          <div className="card-body text-center p-5">
            <div className="mb-3">
              <i className="fas fa-database" style={{ fontSize: '4rem', color: 'var(--clinical-accent)' }}></i>
            </div>
            <h4>No Indexes Found</h4>
            <p className="text-muted">
              Indexes will be created automatically when you configure and start your indexers, or when you use features like Profiles, Memories, or Conversations.
            </p>
            <div className="d-flex gap-2 justify-content-center">
              <button className="btn btn-primary" onClick={() => window.location.href = '/configuration'}>
                Go to Configuration
              </button>
              <button className="btn btn-outline-primary" onClick={fetchIndexes}>
                Refresh
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="card border-0 shadow-sm">
          <div className="card-body">
            <div className="table-responsive">
              <table className="table table-hover mb-0">
            <thead>
              <tr>
                <th>Index Name</th>
                <th>Type</th>
                <th>Documents</th>
                <th>Size</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {indexes.map((index) => (
                <tr key={index.name}>
                  <td>
                    <div>
                      <strong>{index.name}</strong>
                      {index.error && (
                        <div className="text-danger small mt-1">{index.error}</div>
                      )}
                      <div className="small text-muted mt-1">
                        {index.name === 'codebase' && 'Source code repositories'}
                        {index.name === 'codex' && 'Folder structures'}
                        {index.name === 'conversations' && 'AI conversation history'}
                        {index.name === 'conversation_messages' && 'Individual conversation messages'}
                        {index.name === 'profiles' && 'User and agent profiles'}
                        {index.name === 'memories' && 'Agent and user memories'}
                        {index.name === 'categories' && 'Category hierarchy'}
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className={`badge bg-${getTypeBadgeColor(index.type)}`}>
                      <i className={`fas ${getTypeIcon(index.type)} me-1`}></i>{index.type}
                    </span>
                  </td>
                  <td>{index.document_count.toLocaleString()}</td>
                  <td>{index.size ? `${(index.size / 1024 / 1024).toFixed(2)} MB` : 'N/A'}</td>
                  <td>
                    <div className="btn-group" role="group">
                      <button
                        className="btn btn-sm btn-outline-primary"
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
                        title="View detailed statistics"
                      >
                        <i className="fas fa-chart-bar me-1"></i>Stats
                      </button>
                      <button
                        className="btn btn-sm btn-outline-secondary"
                        onClick={() => {
                          if (confirm(`Are you sure you want to search in the "${index.name}" index?`)) {
                            window.location.href = `/?search=${index.name}`
                          }
                        }}
                        title="Search this index"
                      >
                        🔍 Search
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Indexes

