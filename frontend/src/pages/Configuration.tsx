import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiService } from '../services/api'
import PathSelector from '../components/Configuration/PathSelector'

interface Project {
  name: string
  path: string
  enabled: boolean
  folders?: Array<{
    name: string
    path: string
    enabled: boolean
    status: 'active' | 'syncing' | 'error' | 'idle'
    fileCount?: number
    lastSynced?: string
    progress?: number
  }>
}

interface ConversationSource {
  type: string
  path: string
  enabled: boolean
  status: 'active' | 'syncing' | 'error' | 'idle'
  fileCount?: number
  lastSynced?: string
}

function Configuration() {
  const navigate = useNavigate()
  const [config, setConfig] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<{connected: boolean, url: string, lastTest?: string, responseTime?: number}>({connected: false, url: ''})
  const [testingConnection, setTestingConnection] = useState(false)
  const [codebaseProjects, setCodebaseProjects] = useState<Project[]>([])
  const [codexProjects, setCodexProjects] = useState<Project[]>([])
  const [conversationSources, setConversationSources] = useState<ConversationSource[]>([])
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set())
  const [showAddCodebase, setShowAddCodebase] = useState(false)
  const [showAddCodex, setShowAddCodex] = useState(false)
  const [showAddConversation, setShowAddConversation] = useState(false)
  const [newProject, setNewProject] = useState({name: '', path: '', folders: ['']})
  const [newConversation, setNewConversation] = useState({type: 'chatgpt', path: ''})

  const fetchConfig = async () => {
    try {
      setLoading(true)
      const response = await apiService.getConfig()
      const data = response.data
      setConfig(data)
      setConnectionStatus({connected: true, url: data.marqo_url || ''})
      
      const codebaseIndexer = data.indexers?.find((idx: any) => idx.indexer_type === 'code')
      if (codebaseIndexer?.settings?.projects) {
        const projects = codebaseIndexer.settings.projects.map(([name, path]: [string, string]) => ({
          name,
          path,
          enabled: codebaseIndexer.enabled !== false,
          folders: []
        }))
        setCodebaseProjects(projects)
      }
      
      const codexIndexer = data.indexers?.find((idx: any) => idx.indexer_type === 'codex')
      if (codexIndexer?.settings?.projects) {
        const projects = codexIndexer.settings.projects.map(([name, path]: [string, string]) => ({
          name,
          path,
          enabled: codexIndexer.enabled !== false,
          folders: []
        }))
        setCodexProjects(projects)
      }
      
      const convIndexer = data.indexers?.find((idx: any) => idx.indexer_type === 'chathistory' || idx.indexer_type === 'conversation')
      if (convIndexer?.settings?.conversation_types) {
        const sources = convIndexer.settings.conversation_types.map(([type, path]: [string, string]) => ({
          type,
          path,
          enabled: convIndexer.enabled !== false,
          status: 'idle' as const
        }))
        setConversationSources(sources)
      }
    } catch (err: any) {
      console.error('Failed to fetch config:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchConfig()
    const interval = setInterval(fetchConfig, 30000)
    return () => clearInterval(interval)
  }, [])

  const testConnection = async () => {
    setTestingConnection(true)
    try {
      const startTime = Date.now()
      const response = await apiService.testConnection(config?.marqo_url || '')
      const responseTime = Date.now() - startTime
      if (response.data.success) {
        setConnectionStatus({
          connected: true,
          url: config?.marqo_url || '',
          lastTest: new Date().toLocaleTimeString(),
          responseTime
        })
      } else {
        setConnectionStatus({
          connected: false,
          url: config?.marqo_url || '',
          lastTest: new Date().toLocaleTimeString()
        })
      }
    } catch (err: any) {
      setConnectionStatus({
        connected: false,
        url: config?.marqo_url || '',
        lastTest: new Date().toLocaleTimeString()
      })
    } finally {
      setTestingConnection(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const updateData: any = {
        marqo_url: config?.marqo_url,
        max_file_size_bytes: config?.max_file_size_bytes || 1048576,
        store_large_files_metadata_only: config?.store_large_files_metadata_only !== false
      }
      
      if (codebaseProjects.length > 0) {
        updateData.codebases = codebaseProjects.map(p => ({ name: p.name, path: p.path }))
      }
      
      if (codexProjects.length > 0) {
        updateData.codex = codexProjects.map(p => ({ name: p.name, path: p.path }))
      }
      
      if (conversationSources.length > 0) {
        updateData.conversations = conversationSources.map(s => ({ type: s.type, path: s.path }))
      }
      
      await apiService.updateConfig(updateData)
      await fetchConfig()
    } catch (err: any) {
      console.error('Failed to save:', err)
    } finally {
      setSaving(false)
    }
  }

  const toggleProject = (type: 'codebase' | 'codex', index: number) => {
    if (type === 'codebase') {
      const updated = [...codebaseProjects]
      updated[index].enabled = !updated[index].enabled
      setCodebaseProjects(updated)
    } else {
      const updated = [...codexProjects]
      updated[index].enabled = !updated[index].enabled
      setCodexProjects(updated)
    }
  }

  const toggleConversation = (index: number) => {
    const updated = [...conversationSources]
    updated[index].enabled = !updated[index].enabled
    setConversationSources(updated)
  }

  const removeProject = (type: 'codebase' | 'codex', index: number) => {
    if (type === 'codebase') {
      setCodebaseProjects(codebaseProjects.filter((_, i) => i !== index))
    } else {
      setCodexProjects(codexProjects.filter((_, i) => i !== index))
    }
  }

  const removeConversation = (index: number) => {
    setConversationSources(conversationSources.filter((_, i) => i !== index))
  }

  const addCodebaseProject = () => {
    if (newProject.name && newProject.path) {
      setCodebaseProjects([...codebaseProjects, {
        name: newProject.name,
        path: newProject.path,
        enabled: true,
        folders: []
      }])
      setNewProject({name: '', path: '', folders: ['']})
      setShowAddCodebase(false)
    }
  }

  const addCodexProject = () => {
    if (newProject.name && newProject.path) {
      setCodexProjects([...codexProjects, {
        name: newProject.name,
        path: newProject.path,
        enabled: true,
        folders: []
      }])
      setNewProject({name: '', path: '', folders: ['']})
      setShowAddCodex(false)
    }
  }

  const addConversationSource = () => {
    if (newConversation.type && newConversation.path) {
      setConversationSources([...conversationSources, {
        type: newConversation.type,
        path: newConversation.path,
        enabled: true,
        status: 'idle'
      }])
      setNewConversation({type: 'chatgpt', path: ''})
      setShowAddConversation(false)
    }
  }

  if (loading) {
    return <div className="text-center p-5">Loading configuration...</div>
  }

  const codebaseEnabled = codebaseProjects.some(p => p.enabled)
  const codexEnabled = codexProjects.some(p => p.enabled)
  const conversationsEnabled = conversationSources.some(s => s.enabled)

  return (
    <div className="p-4">
      <div className="clinical-header">
        <div className="container-fluid">
          <div className="row align-items-center">
            <div className="col">
              <div className="d-flex align-items-center">
                <a href="#" className="text-decoration-none me-3 text-secondary" onClick={(e) => { e.preventDefault(); navigate('/dashboard') }}>
                  <i className="fas fa-arrow-left me-2"></i>Dashboard
                </a>
                <div>
                  <h1 className="mb-1">Indexer Configuration</h1>
                  <div className="subtitle">Manage Marqo connection and indexer project synchronization</div>
                </div>
              </div>
            </div>
            <div className="col-auto">
              <div className="btn-group btn-group-sm" role="group">
                <button type="button" className="btn btn-success" disabled={saving || !config}>
                  <i className="fas fa-check me-1"></i>
                  {saving ? 'Saving...' : 'Saved'}
                </button>
                <button type="button" className="btn btn-outline-secondary" onClick={testConnection} disabled={testingConnection}>
                  <i className="fas fa-bolt me-1"></i>
                  Test Connections
                </button>
                <button type="button" className="btn btn-outline-secondary" onClick={handleSave} disabled={saving}>
                  <i className="fas fa-save me-1"></i>
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="container-fluid">
        <div className="connection-status">
          <div className="row align-items-center mb-3">
            <div className="col-md-8">
              <label className="form-label small">Marqo Server URL</label>
              <input
                type="text"
                className="form-control form-control-sm"
                value={config?.marqo_url || ''}
                onChange={(e) => setConfig({ ...config, marqo_url: e.target.value })}
                placeholder="http://localhost:8882"
              />
            </div>
            <div className="col-md-4 d-flex align-items-end">
              <button className="btn btn-sm btn-outline-secondary w-100" onClick={testConnection} disabled={testingConnection}>
                <i className={`fas fa-sync-alt me-1 ${testingConnection ? 'fa-spin' : ''}`}></i>
                Test Connection
              </button>
            </div>
          </div>
          <div className="row align-items-center">
            <div className="col">
              <div className="d-flex align-items-center">
                <i className={`fas ${connectionStatus.connected ? 'fa-check-circle text-success' : 'fa-times-circle text-danger'} me-2`}></i>
                <div>
                  <strong>Marqo {connectionStatus.connected ? 'Connected' : 'Disconnected'}</strong>
                  <span className="text-muted ms-2 font-monospace">{connectionStatus.url || 'Not configured'}</span>
                </div>
              </div>
            </div>
            <div className="col-auto">
              {connectionStatus.lastTest && (
                <small className="text-muted">
                  Last: {connectionStatus.lastTest}
                  {connectionStatus.responseTime && ` • ${connectionStatus.responseTime}ms`}
                </small>
              )}
            </div>
          </div>
        </div>

        <div className="accordion" id="indexerAccordion">
          <div className="accordion-item mb-3">
            <h2 className="accordion-header">
              <button className="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#codebaseSection" aria-expanded="true">
                <div className="d-flex justify-content-between align-items-center w-100">
                  <div className="d-flex align-items-center">
                    <i className="fas fa-code me-3 text-primary" style={{fontSize: '1.25rem'}}></i>
                    <div>
                      <h6 className="mb-1">Codebase</h6>
                      <small className="text-muted">Source code semantic search</small>
                    </div>
                  </div>
                  <div className="d-flex align-items-center gap-3 me-4">
                    <div className="d-flex align-items-center gap-2">
                      <div className="stat-item-compact">
                        <span className="stat-number">{codebaseProjects.length}</span>
                        <span className="stat-label">Projects</span>
                      </div>
                      <div className="stat-item-compact">
                        <span className="stat-number">{codebaseProjects.reduce((sum, p) => sum + (p.folders?.length || 0), 0)}</span>
                        <span className="stat-label">Folders</span>
                      </div>
                    </div>
                    <div className="form-check form-switch">
                      <input className="form-check-input" type="checkbox" checked={codebaseEnabled} onChange={() => {}} onClick={(e) => e.stopPropagation()} />
                      <label className="form-check-label text-muted small">Enable</label>
                    </div>
                  </div>
                </div>
              </button>
            </h2>
            <div id="codebaseSection" className="accordion-collapse collapse show" data-bs-parent="#indexerAccordion">
              <div className="accordion-body p-3">
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <div className="d-flex align-items-center">
                    <span className={`status-badge ${codebaseEnabled ? 'active' : 'inactive'} me-3`}>
                      <i className={`fas ${codebaseEnabled ? 'fa-check-circle' : 'fa-pause-circle'} me-1`}></i>
                      {codebaseEnabled ? 'Active' : 'Inactive'}
                    </span>
                    <small className="text-muted">
                      <i className="fas fa-database me-1"></i>
                      Index: <code>codebase</code>
                    </small>
                  </div>
                  <div className="btn-group btn-group-sm">
                    <button className="btn btn-primary btn-sm">
                      <i className="fas fa-sync-alt me-1"></i>
                      Sync All
                    </button>
                    <button className="btn btn-outline-secondary btn-sm" onClick={() => setShowAddCodebase(!showAddCodebase)}>
                      <i className="fas fa-plus me-1"></i>
                      Add Project
                    </button>
                  </div>
                </div>

                {codebaseProjects.length > 0 && (
                  <div className="mb-3">
                    <h6 className="mb-2 text-muted small text-uppercase">Active Projects</h6>
                    {codebaseProjects.map((project, pIdx) => (
                      <div key={pIdx} className="project-card mb-2">
                        <div className="d-flex justify-content-between align-items-center p-2">
                          <div className="d-flex align-items-center">
                            <div className="form-check form-switch me-2">
                              <input className="form-check-input form-check-input-sm" type="checkbox" checked={project.enabled} onChange={() => toggleProject('codebase', pIdx)} />
                            </div>
                            <div>
                              <strong className="project-name">{project.name}</strong>
                              <span className="badge bg-success badge-sm ms-2">{project.folders?.length || 0} folders</span>
                            </div>
                          </div>
                          <div className="btn-group btn-group-sm">
                            <button className="btn btn-outline-secondary btn-sm" onClick={() => {
                              const newExpanded = new Set(expandedProjects)
                              if (newExpanded.has(`codebase-${pIdx}`)) {
                                newExpanded.delete(`codebase-${pIdx}`)
                              } else {
                                newExpanded.add(`codebase-${pIdx}`)
                              }
                              setExpandedProjects(newExpanded)
                            }}>
                              <i className={`fas fa-chevron-${expandedProjects.has(`codebase-${pIdx}`) ? 'up' : 'down'}`}></i>
                            </button>
                            <button className="btn btn-outline-primary btn-sm">
                              <i className="fas fa-sync-alt"></i>
                            </button>
                            <button className="btn btn-outline-danger btn-sm" onClick={() => removeProject('codebase', pIdx)}>
                              <i className="fas fa-trash"></i>
                            </button>
                          </div>
                        </div>
                        {expandedProjects.has(`codebase-${pIdx}`) && (
                          <div className="folder-list">
                            <div className="folder-item-compact active">
                              <div className="d-flex justify-content-between align-items-center">
                                <div className="d-flex align-items-center flex-grow-1">
                                  <div className="form-check form-switch me-2">
                                    <input className="form-check-input form-check-input-sm" type="checkbox" checked={true} />
                                  </div>
                                  <div className="folder-info">
                                    <strong className="folder-name">{project.name}</strong>
                                    <div className="folder-path">{project.path}</div>
                                  </div>
                                </div>
                                <div className="folder-status">
                                  <div className="text-center">
                                    <span className="text-success small">
                                      <i className="fas fa-check-circle"></i>
                                    </span>
                                  </div>
                                </div>
                                <div className="folder-actions">
                                  <div className="btn-group btn-group-sm">
                                    <button type="button" className="btn btn-outline-secondary btn-xs">
                                      <i className="fas fa-check"></i>
                                    </button>
                                    <button type="button" className="btn btn-outline-primary btn-xs">
                                      <i className="fas fa-sync-alt"></i>
                                    </button>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {showAddCodebase && (
                  <div className="card border-primary border-2 mb-3" style={{borderStyle: 'dashed'}}>
                    <div className="card-body p-3">
                      <h6 className="mb-3">
                        <i className="fas fa-plus-circle me-2"></i>
                        Add Codebase Project
                      </h6>
                      <div className="row g-2">
                        <div className="col-md-6">
                          <label className="form-label small">Project Name</label>
                          <input type="text" className="form-control form-control-sm" placeholder="Enter project name" value={newProject.name} onChange={(e) => setNewProject({...newProject, name: e.target.value})} />
                        </div>
                        <div className="col-md-6">
                          <label className="form-label small">Base Path</label>
                          <PathSelector value={newProject.path} onChange={(path) => setNewProject({...newProject, path})} />
                        </div>
                      </div>
                      <div className="d-flex gap-2 mt-3">
                        <button type="button" className="btn btn-primary btn-sm" onClick={addCodebaseProject}>
                          <i className="fas fa-plus me-1"></i>
                          Add Project
                        </button>
                        <button type="button" className="btn btn-outline-secondary btn-sm" onClick={() => setShowAddCodebase(false)}>
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="accordion-item mb-3">
            <h2 className="accordion-header">
              <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#codexSection">
                <div className="d-flex justify-content-between align-items-center w-100">
                  <div className="d-flex align-items-center">
                    <i className="fas fa-sitemap me-3 text-info" style={{fontSize: '1.25rem'}}></i>
                    <div>
                      <h6 className="mb-1">Codex</h6>
                      <small className="text-muted">Directory structure indexing</small>
                    </div>
                  </div>
                  <div className="d-flex align-items-center gap-3 me-4">
                    <div className="d-flex align-items-center gap-2">
                      <div className="stat-item-compact">
                        <span className="stat-number">{codexProjects.length}</span>
                        <span className="stat-label">Projects</span>
                      </div>
                    </div>
                    <div className="form-check form-switch">
                      <input className="form-check-input" type="checkbox" checked={codexEnabled} onChange={() => {}} onClick={(e) => e.stopPropagation()} />
                      <label className="form-check-label text-muted small">Enable</label>
                    </div>
                  </div>
                </div>
              </button>
            </h2>
            <div id="codexSection" className="accordion-collapse collapse" data-bs-parent="#indexerAccordion">
              <div className="accordion-body p-3">
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <div className="d-flex align-items-center">
                    <span className={`status-badge ${codexEnabled ? 'active' : 'inactive'} me-3`}>
                      <i className={`fas ${codexEnabled ? 'fa-check-circle' : 'fa-pause-circle'} me-1`}></i>
                      {codexEnabled ? 'Active' : 'Inactive'}
                    </span>
                    <small className="text-muted">
                      <i className="fas fa-database me-1"></i>
                      Index: <code>codex</code>
                    </small>
                  </div>
                  <div className="btn-group btn-group-sm">
                    <button className="btn btn-primary btn-sm">
                      <i className="fas fa-sync-alt me-1"></i>
                      Sync All
                    </button>
                    <button className="btn btn-outline-secondary btn-sm" onClick={() => setShowAddCodex(!showAddCodex)}>
                      <i className="fas fa-plus me-1"></i>
                      Add Directory
                    </button>
                  </div>
                </div>

                {codexProjects.length > 0 && (
                  <div>
                    {codexProjects.map((project, pIdx) => (
                      <div key={pIdx} className="project-card mb-2">
                        <div className="d-flex justify-content-between align-items-center p-2">
                          <div className="d-flex align-items-center">
                            <div className="form-check form-switch me-2">
                              <input className="form-check-input form-check-input-sm" type="checkbox" checked={project.enabled} onChange={() => toggleProject('codex', pIdx)} />
                            </div>
                            <div>
                              <strong className="project-name">{project.name}</strong>
                              <span className="badge bg-success badge-sm ms-2">Active</span>
                            </div>
                          </div>
                          <div className="btn-group btn-group-sm">
                            <button className="btn btn-outline-primary btn-sm">
                              <i className="fas fa-sync-alt"></i>
                            </button>
                            <button className="btn btn-outline-danger btn-sm" onClick={() => removeProject('codex', pIdx)}>
                              <i className="fas fa-trash"></i>
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {showAddCodex && (
                  <div className="card border-primary border-2 mb-3" style={{borderStyle: 'dashed'}}>
                    <div className="card-body p-3">
                      <h6 className="mb-3">
                        <i className="fas fa-plus-circle me-2"></i>
                        Add Codex Directory
                      </h6>
                      <div className="row g-2">
                        <div className="col-md-6">
                          <label className="form-label small">Project Name</label>
                          <input type="text" className="form-control form-control-sm" placeholder="Enter project name" value={newProject.name} onChange={(e) => setNewProject({...newProject, name: e.target.value})} />
                        </div>
                        <div className="col-md-6">
                          <label className="form-label small">Base Path</label>
                          <PathSelector value={newProject.path} onChange={(path) => setNewProject({...newProject, path})} />
                        </div>
                      </div>
                      <div className="d-flex gap-2 mt-3">
                        <button type="button" className="btn btn-primary btn-sm" onClick={addCodexProject}>
                          <i className="fas fa-plus me-1"></i>
                          Add Directory
                        </button>
                        <button type="button" className="btn btn-outline-secondary btn-sm" onClick={() => setShowAddCodex(false)}>
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="accordion-item mb-3">
            <h2 className="accordion-header">
              <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#conversationsSection">
                <div className="d-flex justify-content-between align-items-center w-100">
                  <div className="d-flex align-items-center">
                    <i className="fas fa-comments me-3 text-warning" style={{fontSize: '1.25rem'}}></i>
                    <div>
                      <h6 className="mb-1">Conversations</h6>
                      <small className="text-muted">AI conversation history</small>
                    </div>
                  </div>
                  <div className="d-flex align-items-center gap-3 me-4">
                    <div className="d-flex align-items-center gap-2">
                      <div className="stat-item-compact">
                        <span className="stat-number">{conversationSources.length}</span>
                        <span className="stat-label">Sources</span>
                      </div>
                    </div>
                    <div className="form-check form-switch">
                      <input className="form-check-input" type="checkbox" checked={conversationsEnabled} onChange={() => {}} onClick={(e) => e.stopPropagation()} />
                      <label className="form-check-label text-muted small">Enable</label>
                    </div>
                  </div>
                </div>
              </button>
            </h2>
            <div id="conversationsSection" className="accordion-collapse collapse" data-bs-parent="#indexerAccordion">
              <div className="accordion-body p-3">
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <div className="d-flex align-items-center">
                    <span className={`status-badge ${conversationsEnabled && conversationSources.length > 0 ? 'active' : 'error'} me-3`}>
                      <i className={`fas ${conversationsEnabled && conversationSources.length > 0 ? 'fa-check-circle' : 'fa-exclamation-triangle'} me-1`}></i>
                      {conversationsEnabled && conversationSources.length > 0 ? 'Active' : 'No Sources'}
                    </span>
                    <small className="text-muted">
                      <i className="fas fa-database me-1"></i>
                      Index: <code>conversations</code>
                    </small>
                  </div>
                  <button className="btn btn-primary btn-sm" onClick={() => setShowAddConversation(!showAddConversation)}>
                    <i className="fas fa-plus me-1"></i>
                    Add Source
                  </button>
                </div>

                {conversationSources.length > 0 ? (
                  <div>
                    {conversationSources.map((source, sIdx) => (
                      <div key={sIdx} className="folder-item-compact active mb-2">
                        <div className="d-flex justify-content-between align-items-center">
                          <div className="d-flex align-items-center flex-grow-1">
                            <div className="form-check form-switch me-2">
                              <input className="form-check-input form-check-input-sm" type="checkbox" checked={source.enabled} onChange={() => toggleConversation(sIdx)} />
                            </div>
                            <div className="folder-info">
                              <strong className="folder-name">{source.type}</strong>
                              <div className="folder-path">{source.path}</div>
                            </div>
                          </div>
                          <div className="folder-actions">
                            <div className="btn-group btn-group-sm">
                              <button type="button" className="btn btn-outline-secondary btn-xs">
                                <i className="fas fa-check"></i>
                              </button>
                              <button type="button" className="btn btn-outline-primary btn-xs">
                                <i className="fas fa-sync-alt"></i>
                              </button>
                              <button type="button" className="btn btn-outline-danger btn-xs" onClick={() => removeConversation(sIdx)}>
                                <i className="fas fa-trash"></i>
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    <div className="text-center py-4">
                      <i className="fas fa-comments empty-state-icon"></i>
                      <h6 className="mt-3 text-muted">No conversation sources configured</h6>
                      <p className="text-muted mb-3 small">Add conversation export folders to enable semantic search.</p>
                      <div className="row g-2 justify-content-center">
                        <div className="col-6 col-md-3">
                          <button className="btn btn-outline-primary btn-sm w-100" onClick={() => { setNewConversation({type: 'chatgpt', path: ''}); setShowAddConversation(true) }}>
                            <i className="fas fa-robot me-1"></i>
                            ChatGPT
                          </button>
                        </div>
                        <div className="col-6 col-md-3">
                          <button className="btn btn-outline-primary btn-sm w-100" onClick={() => { setNewConversation({type: 'claude', path: ''}); setShowAddConversation(true) }}>
                            <i className="fas fa-brain me-1"></i>
                            Claude
                          </button>
                        </div>
                        <div className="col-6 col-md-3">
                          <button className="btn btn-outline-primary btn-sm w-100" onClick={() => { setNewConversation({type: 'custom', path: ''}); setShowAddConversation(true) }}>
                            <i className="fas fa-plus me-1"></i>
                            Custom
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {showAddConversation && (
                  <div className="card border-primary border-2 mb-3" style={{borderStyle: 'dashed'}}>
                    <div className="card-body p-3">
                      <h6 className="mb-3">
                        <i className="fas fa-plus-circle me-2"></i>
                        Add Conversation Source
                      </h6>
                      <div className="row g-2">
                        <div className="col-md-6">
                          <label className="form-label small">Conversation Type</label>
                          <select className="form-select form-select-sm" value={newConversation.type} onChange={(e) => setNewConversation({...newConversation, type: e.target.value})}>
                            <option value="chatgpt">ChatGPT</option>
                            <option value="claude">Claude</option>
                            <option value="custom">Custom</option>
                          </select>
                        </div>
                        <div className="col-md-6">
                          <label className="form-label small">Directory Path</label>
                          <PathSelector value={newConversation.path} onChange={(path) => setNewConversation({...newConversation, path})} />
                        </div>
                      </div>
                      <div className="d-flex gap-2 mt-3">
                        <button type="button" className="btn btn-primary btn-sm" onClick={addConversationSource}>
                          <i className="fas fa-plus me-1"></i>
                          Add Source
                        </button>
                        <button type="button" className="btn btn-outline-secondary btn-sm" onClick={() => setShowAddConversation(false)}>
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="card mt-4">
          <div className="card-header d-flex justify-content-between align-items-center py-2">
            <h6 className="mb-0">
              <i className="fas fa-chart-line me-2"></i>
              System Overview
            </h6>
          </div>
          <div className="card-body p-3">
            <div className="row">
              <div className="col-md-8">
                <h6 className="mb-2 small text-uppercase text-muted">Active Operations</h6>
                <div className="text-muted small">No active sync operations</div>
              </div>
              <div className="col-md-4">
                <h6 className="mb-2 small text-uppercase text-muted">Statistics</h6>
                <div className="stats-grid">
                  <div className="stat-item-compact">
                    <span className="stat-number">{codebaseProjects.length + codexProjects.length + conversationSources.length}</span>
                    <span className="stat-label">Total</span>
                  </div>
                  <div className="stat-item-compact">
                    <span className="stat-number">{codebaseProjects.filter(p => p.enabled).length + codexProjects.filter(p => p.enabled).length + conversationSources.filter(s => s.enabled).length}</span>
                    <span className="stat-label">Active</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Configuration
