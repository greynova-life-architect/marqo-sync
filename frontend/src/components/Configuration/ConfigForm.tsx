import { useState, useEffect } from 'react'
import PathSelector from './PathSelector'
import { apiService } from '../../services/api'

interface ConfigFormProps {
  config: any
  onSave: (config: any) => void
  saving: boolean
  focusSection?: string | null
}

function ConfigForm({ config, onSave, saving, focusSection }: ConfigFormProps) {
  const [marqoUrl, setMarqoUrl] = useState('')
  const [codebases, setCodebases] = useState<Array<{name: string, path: string}>>([])
  const [codex, setCodex] = useState<Array<{name: string, path: string}>>([])
  const [conversations, setConversations] = useState<Array<{type: string, path: string}>>([])
  const [maxFileSize, setMaxFileSize] = useState(1024 * 1024)
  const [storeMetadataOnly, setStoreMetadataOnly] = useState(true)
  const [connectionStatus, setConnectionStatus] = useState<string | null>(null)

  useEffect(() => {
    if (config) {
      setMarqoUrl(config.marqo_url || '')
      setMaxFileSize(config.max_file_size_bytes || 1024 * 1024)
      setStoreMetadataOnly(config.store_large_files_metadata_only !== false)
      
      const codebaseIndexer = config.indexers?.find((idx: any) => idx.indexer_type === 'code')
      if (codebaseIndexer?.settings?.projects) {
        setCodebases(codebaseIndexer.settings.projects.map(([name, path]: [string, string]) => ({ name, path })))
      }
      
      const codexIndexer = config.indexers?.find((idx: any) => idx.indexer_type === 'codex')
      if (codexIndexer?.settings?.projects) {
        setCodex(codexIndexer.settings.projects.map(([name, path]: [string, string]) => ({ name, path })))
      }
      
      const convIndexer = config.indexers?.find((idx: any) => idx.indexer_type === 'chathistory')
      if (convIndexer?.settings?.conversation_types) {
        setConversations(convIndexer.settings.conversation_types.map(([type, path]: [string, string]) => ({ type, path })))
      }
    }
  }, [config])

  const handleTestConnection = async () => {
    setConnectionStatus('Testing...')
    try {
      const response = await apiService.testConnection(marqoUrl)
      if (response.data.success) {
        setConnectionStatus('Connection successful!')
      } else {
        setConnectionStatus(`Connection failed: ${response.data.message}`)
      }
    } catch (err: any) {
      setConnectionStatus(`Error: ${err.message}`)
    }
  }

  const handleSave = () => {
    const updateData: any = {
      marqo_url: marqoUrl,
      max_file_size_bytes: maxFileSize,
      store_large_files_metadata_only: storeMetadataOnly,
    }
    
    if (codebases.length > 0) {
      updateData.codebases = codebases
    }
    if (codex.length > 0) {
      updateData.codex = codex
    }
    if (conversations.length > 0) {
      updateData.conversations = conversations
    }
    
    onSave(updateData)
  }

  const addCodebase = () => {
    setCodebases([...codebases, { name: '', path: '' }])
  }

  const removeCodebase = (index: number) => {
    setCodebases(codebases.filter((_, i) => i !== index))
  }

  const updateCodebase = (index: number, field: 'name' | 'path', value: string) => {
    const updated = [...codebases]
    updated[index][field] = value
    setCodebases(updated)
  }

  const addCodex = () => {
    setCodex([...codex, { name: '', path: '' }])
  }

  const removeCodex = (index: number) => {
    setCodex(codex.filter((_, i) => i !== index))
  }

  const updateCodex = (index: number, field: 'name' | 'path', value: string) => {
    const updated = [...codex]
    updated[index][field] = value
    setCodex(updated)
  }

  const addConversation = () => {
    setConversations([...conversations, { type: '', path: '' }])
  }

  const removeConversation = (index: number) => {
    setConversations(conversations.filter((_, i) => i !== index))
  }

  const updateConversation = (index: number, field: 'type' | 'path', value: string) => {
    const updated = [...conversations]
    updated[index][field] = value
    setConversations(updated)
  }

  return (
    <div className="row">
      <div className="col-lg-8">
        <div className="card mb-4">
          <div className="card-header">
            <h5 className="mb-0">Marqo Connection</h5>
          </div>
          <div className="card-body">
            <div className="mb-3">
              <label className="form-label">Marqo URL</label>
              <div className="input-group">
                <input
                  type="text"
                  className="form-control"
                  value={marqoUrl}
                  onChange={(e) => setMarqoUrl(e.target.value)}
                  placeholder="http://localhost:8882"
                />
                <button className="btn btn-outline-secondary" onClick={handleTestConnection}>
                  Test Connection
                </button>
              </div>
              {connectionStatus && (
                <div className={`mt-2 small ${connectionStatus.includes('successful') ? 'text-success' : 'text-danger'}`}>
                  {connectionStatus}
                </div>
              )}
            </div>
          </div>
        </div>

        <div id="section-codebase" className="card mb-4" style={focusSection === 'codebase' ? { border: '2px solid #0d6efd' } : {}}>
          <div className="card-header d-flex justify-content-between align-items-center">
            <div>
              <h5 className="mb-0"><i className="fas fa-code me-2"></i>Codebase Indexers</h5>
              <small className="text-muted">Index your source code repositories</small>
            </div>
            <button className="btn btn-sm btn-primary" onClick={addCodebase}>+ Add Project</button>
          </div>
          <div className="card-body">
            {codebases.map((item, index) => (
              <div key={index} className="mb-3 p-3 border rounded">
                <div className="row mb-2">
                  <div className="col-md-4">
                    <label className="form-label">Project Name</label>
                    <input
                      type="text"
                      className="form-control"
                      value={item.name}
                      onChange={(e) => updateCodebase(index, 'name', e.target.value)}
                      placeholder="project-name"
                    />
                  </div>
                  <div className="col-md-8">
                    <label className="form-label">Directory Path</label>
                    <PathSelector
                      value={item.path}
                      onChange={(path) => updateCodebase(index, 'path', path)}
                    />
                  </div>
                </div>
                <button className="btn btn-sm btn-danger" onClick={() => removeCodebase(index)}>
                  Remove
                </button>
              </div>
            ))}
            {codebases.length === 0 && (
              <p className="text-muted">No codebase projects configured</p>
            )}
          </div>
        </div>

        <div id="section-codex" className="card mb-4">
          <div className="card-header d-flex justify-content-between align-items-center">
            <div>
              <h5 className="mb-0"><i className="fas fa-sitemap me-2"></i>Codex Indexers</h5>
              <small className="text-muted">Index folder structures</small>
            </div>
            <button className="btn btn-sm btn-primary" onClick={addCodex}>+ Add Project</button>
          </div>
          <div className="card-body">
            {codex.map((item, index) => (
              <div key={index} className="mb-3 p-3 border rounded">
                <div className="row mb-2">
                  <div className="col-md-4">
                    <label className="form-label">Project Name</label>
                    <input
                      type="text"
                      className="form-control"
                      value={item.name}
                      onChange={(e) => updateCodex(index, 'name', e.target.value)}
                      placeholder="project-name"
                    />
                  </div>
                  <div className="col-md-8">
                    <label className="form-label">Directory Path</label>
                    <PathSelector
                      value={item.path}
                      onChange={(path) => updateCodex(index, 'path', path)}
                    />
                  </div>
                </div>
                <button className="btn btn-sm btn-danger" onClick={() => removeCodex(index)}>
                  Remove
                </button>
              </div>
            ))}
            {codex.length === 0 && (
              <p className="text-muted">No codex projects configured</p>
            )}
          </div>
        </div>

        <div id="section-conversations" className="card mb-4" style={focusSection === 'conversations' ? { border: '2px solid #0d6efd' } : {}}>
          <div className="card-header d-flex justify-content-between align-items-center">
            <div>
              <h5 className="mb-0"><i className="fas fa-comments me-2"></i>Conversation Indexers</h5>
              <small className="text-muted">Index AI conversation history (ChatGPT, Claude, etc.)</small>
            </div>
            <button className="btn btn-sm btn-primary" onClick={addConversation}>+ Add Type</button>
          </div>
          <div className="card-body">
            {conversations.map((item, index) => (
              <div key={index} className="mb-3 p-3 border rounded">
                <div className="row mb-2">
                  <div className="col-md-4">
                    <label className="form-label">Conversation Type</label>
                    <input
                      type="text"
                      className="form-control"
                      value={item.type}
                      onChange={(e) => updateConversation(index, 'type', e.target.value)}
                      placeholder="chatgpt"
                    />
                  </div>
                  <div className="col-md-8">
                    <label className="form-label">Directory Path</label>
                    <PathSelector
                      value={item.path}
                      onChange={(path) => updateConversation(index, 'path', path)}
                    />
                  </div>
                </div>
                <button className="btn btn-sm btn-danger" onClick={() => removeConversation(index)}>
                  Remove
                </button>
              </div>
            ))}
            {conversations.length === 0 && (
              <p className="text-muted">No conversation types configured</p>
            )}
          </div>
        </div>

        <div className="card mb-4">
          <div className="card-header">
            <h5 className="mb-0">Advanced Settings</h5>
          </div>
          <div className="card-body">
            <div className="mb-3">
              <label className="form-label">Max File Size (bytes)</label>
              <input
                type="number"
                className="form-control"
                value={maxFileSize}
                onChange={(e) => setMaxFileSize(parseInt(e.target.value) || 0)}
              />
            </div>
            <div className="form-check">
              <input
                className="form-check-input"
                type="checkbox"
                checked={storeMetadataOnly}
                onChange={(e) => setStoreMetadataOnly(e.target.checked)}
                id="storeMetadataOnly"
              />
              <label className="form-check-label" htmlFor="storeMetadataOnly">
                Store large files metadata only
              </label>
            </div>
          </div>
        </div>

        <div className="d-grid">
          <button className="btn btn-primary btn-lg" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ConfigForm

