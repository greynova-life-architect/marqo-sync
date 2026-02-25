import { useState } from 'react'
import { apiService } from '../../services/api'
import PathSelector from '../Configuration/PathSelector'

interface CreateIndexModalProps {
  show: boolean
  onClose: () => void
  onSuccess: () => void
}

const INDEXER_TYPES = [
  { id: 'code', name: 'Codebase Indexer', icon: 'fa-code', description: 'Index source code files and repositories' },
  { id: 'codex', name: 'Codex Indexer', icon: 'fa-sitemap', description: 'Index folder structures and directory layouts' },
  { id: 'chathistory', name: 'Conversation Indexer', icon: 'fa-comments', description: 'Index AI conversation history' }
]

function CreateIndexModal({ show, onClose, onSuccess }: CreateIndexModalProps) {
  const [indexName, setIndexName] = useState('')
  const [indexerType, setIndexerType] = useState('code')
  const [sourcePath, setSourcePath] = useState('')
  const [sourceName, setSourceName] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreate = async () => {
    if (!indexName.trim()) {
      setError('Index name is required')
      return
    }
    if (!sourcePath.trim()) {
      setError('Source path is required')
      return
    }
    if (!sourceName.trim()) {
      setError('Source name is required')
      return
    }

    setCreating(true)
    setError(null)

    try {
      const configResponse = await apiService.getConfig()
      const currentConfig = configResponse.data

      const updateData: any = {
        marqo_url: currentConfig.marqo_url,
        max_file_size_bytes: currentConfig.max_file_size_bytes,
        store_large_files_metadata_only: currentConfig.store_large_files_metadata_only
      }

      const existingIndexer = currentConfig.indexers?.find((idx: any) => idx.indexer_type === indexerType)
      
      if (existingIndexer) {
        if (indexerType === 'code' || indexerType === 'codex') {
          const projects = existingIndexer.settings?.projects || []
          const existingProjects = projects.map((item: any) => {
            if (Array.isArray(item)) {
              return { name: item[0], path: item[1] }
            }
            return { name: item.name || '', path: item.path || '' }
          })
          existingProjects.push({ name: sourceName, path: sourcePath })
          updateData[indexerType === 'code' ? 'codebases' : 'codex'] = existingProjects
        } else if (indexerType === 'chathistory') {
          const conversationTypes = existingIndexer.settings?.conversation_types || []
          const existingTypes = conversationTypes.map((item: any) => {
            if (Array.isArray(item)) {
              return { type: item[0], path: item[1] }
            }
            return { type: item.type || '', path: item.path || '' }
          })
          existingTypes.push({ type: sourceName, path: sourcePath })
          updateData.conversations = existingTypes
        }
      } else {
        if (indexerType === 'code') {
          updateData.codebases = [{ name: sourceName, path: sourcePath }]
        } else if (indexerType === 'codex') {
          updateData.codex = [{ name: sourceName, path: sourcePath }]
        } else if (indexerType === 'chathistory') {
          updateData.conversations = [{ type: sourceName, path: sourcePath }]
        }
      }

      await apiService.updateConfig(updateData)
      
      const generatedIndexName = `${indexerType === 'code' ? 'codebase' : indexerType === 'codex' ? 'codex' : 'conversations'}-${sourceName.toLowerCase().replace(/[^a-z0-9]/g, '-')}`
      
      const message = `Index Configuration Saved!\n\n` +
        `Folder: ${sourcePath}\n` +
        `Indexer: ${selectedIndexer?.name}\n` +
        `Index Name: ${generatedIndexName}\n\n` +
        `When you start/restart the marqo-sync service:\n` +
        `• It will use the ${selectedIndexer?.name} to process files\n` +
        `• It will create the "${generatedIndexName}" index\n` +
        `• It will start indexing files from: ${sourcePath}\n` +
        `• It will watch for file changes automatically`
      
      alert(message)
      
      onSuccess()
      handleClose()
    } catch (err: any) {
      setError(err.message || 'Failed to create index')
    } finally {
      setCreating(false)
    }
  }

  const handleClose = () => {
    setIndexName('')
    setSourcePath('')
    setSourceName('')
    setError(null)
    onClose()
  }

  const selectedIndexer = INDEXER_TYPES.find(t => t.id === indexerType)

  if (!show) return null

  return (
    <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }} tabIndex={-1}>
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">Create New Index</h5>
            <button type="button" className="btn-close" onClick={handleClose}></button>
          </div>
          <div className="modal-body">
            {error && (
              <div className="alert alert-danger" role="alert">
                {error}
              </div>
            )}

            <div className="mb-3">
              <label className="form-label">Indexer Type</label>
              <div className="row g-2">
                {INDEXER_TYPES.map((type) => (
                  <div key={type.id} className="col-md-4">
                    <div
                      className={`card h-100 cursor-pointer ${indexerType === type.id ? 'border-primary' : ''}`}
                      onClick={() => setIndexerType(type.id)}
                      style={{ cursor: 'pointer' }}
                    >
                      <div className="card-body text-center">
                        <i className={`fas ${type.icon} mb-2`} style={{ fontSize: '2rem', color: 'var(--clinical-accent)' }}></i>
                        <h6 className="mb-1">{type.name}</h6>
                        <small className="text-muted">{type.description}</small>
                        {indexerType === type.id && (
                          <div className="mt-2">
                            <span className="badge bg-primary">Selected</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mb-3">
              <label className="form-label">Source Name</label>
              <input
                type="text"
                className="form-control"
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
                placeholder={indexerType === 'chathistory' ? 'e.g., chatgpt, claude' : 'e.g., my-project, frontend'}
                required
              />
              <small className="text-muted">
                {indexerType === 'chathistory' 
                  ? 'Name for this conversation source (e.g., chatgpt, claude, gemini)'
                  : 'Name for this project/folder (e.g., my-project, frontend-app)'}
              </small>
            </div>

            <div className="mb-3">
              <label className="form-label">Source Path</label>
              <PathSelector
                value={sourcePath}
                onChange={setSourcePath}
              />
              <small className="text-muted">Select the folder to index</small>
            </div>

            <div className="mb-3">
              <label className="form-label">Index Name (Optional)</label>
              <input
                type="text"
                className="form-control"
                value={indexName}
                onChange={(e) => setIndexName(e.target.value)}
                placeholder={`Auto-generated: ${indexerType === 'code' ? 'codebase' : indexerType === 'codex' ? 'codex' : 'conversations'}-${sourceName || 'name'}`}
              />
              <small className="text-muted">
                Leave empty to auto-generate: {indexerType === 'code' ? 'codebase' : indexerType === 'codex' ? 'codex' : 'conversations'}-{sourceName || 'name'}
              </small>
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={handleClose} disabled={creating}>
              Cancel
            </button>
            <button type="button" className="btn btn-primary" onClick={handleCreate} disabled={creating || !sourceName || !sourcePath}>
              {creating ? 'Creating...' : 'Create Index'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CreateIndexModal

