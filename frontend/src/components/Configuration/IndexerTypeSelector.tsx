import { useState } from 'react'
import PathSelector from './PathSelector'

interface IndexerType {
  id: string
  name: string
  description: string
  icon: string
}

interface IndexerTypeSelectorProps {
  selectedType: string
  onTypeChange: (type: string) => void
  indexers: any[]
  onAddIndexer: (type: string) => void
  onRemoveIndexer: (index: number) => void
  onUpdateIndexer: (index: number, field: string, value: any) => void
}

const INDEXER_TYPES: IndexerType[] = [
  {
    id: 'codebase',
    name: 'Codebase',
    description: 'Index source code repositories',
    icon: 'fa-code'
  },
  {
    id: 'codex',
    name: 'Codex',
    description: 'Index folder structures',
    icon: 'fa-sitemap'
  },
  {
    id: 'conversations',
    name: 'Conversations',
    description: 'Index AI conversation history',
    icon: 'fa-comments'
  }
]

function IndexerTypeSelector({
  selectedType,
  onTypeChange,
  indexers,
  onAddIndexer,
  onRemoveIndexer,
  onUpdateIndexer
}: IndexerTypeSelectorProps) {
  const selectedTypeInfo = INDEXER_TYPES.find(t => t.id === selectedType)

  const getIndexerConfig = () => {
    const typeMap: Record<string, string> = {
      'codebase': 'code',
      'codex': 'codex',
      'conversations': 'chathistory'
    }
    const mappedType = typeMap[selectedType] || selectedType
    return indexers.find(idx => idx.indexer_type === mappedType || idx.indexer_type === selectedType) || null
  }

  const currentIndexer = getIndexerConfig()

  return (
    <div className="row">
      <div className="col-md-3">
        <div className="card border-0 shadow-sm sticky-top" style={{ top: '20px' }}>
          <div className="card-header">
            <h6 className="mb-0">Indexer Types</h6>
          </div>
          <div className="list-group list-group-flush">
            {INDEXER_TYPES.map((type) => {
              const typeMap: Record<string, string> = {
                'codebase': 'code',
                'codex': 'codex',
                'conversations': 'chathistory'
              }
              const mappedType = typeMap[type.id] || type.id
              const indexer = indexers.find(idx => idx.indexer_type === mappedType || idx.indexer_type === type.id)
              const isActive = selectedType === type.id
              return (
                <button
                  key={type.id}
                  className={`list-group-item list-group-item-action ${isActive ? 'active' : ''} border-0`}
                  onClick={() => onTypeChange(type.id)}
                >
                  <div className="d-flex align-items-center">
                    <i className={`fas ${type.icon} me-2`} style={{ fontSize: '1.25rem', color: 'var(--clinical-accent)' }}></i>
                    <div className="flex-grow-1">
                      <div className="fw-semibold">{type.name}</div>
                      <small className="text-muted">{type.description}</small>
                    </div>
                    {indexer && (
                      <span className="badge bg-success ms-2"><i className="fas fa-check"></i></span>
                    )}
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      <div className="col-md-9">
        {selectedTypeInfo && (
          <div className="card border-0 shadow-sm">
            <div className="card-header">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h5 className="mb-0">
                    <i className={`fas ${selectedTypeInfo.icon} me-2`}></i>
                    {selectedTypeInfo.name} Indexer
                  </h5>
                  <small className="text-muted">{selectedTypeInfo.description}</small>
                </div>
                {!currentIndexer && (
                  <button
                    className="btn btn-primary"
                    onClick={() => onAddIndexer(selectedType)}
                  >
                    Enable {selectedTypeInfo.name}
                  </button>
                )}
              </div>
            </div>
            <div className="card-body">
              {currentIndexer ? (
                <div>
                  <div className="alert alert-success mb-3">
                    <strong>✓ Configured</strong> - This indexer is active and will sync to the <code>{currentIndexer.index_name}</code> index
                  </div>
                  
                  {(selectedType === 'codebase' || selectedType === 'codex') && currentIndexer.settings?.projects && (
                    <div>
                      <h6 className="mb-3">{selectedType === 'codebase' ? 'Projects' : 'Folder Structures'}</h6>
                      {currentIndexer.settings.projects.map((item: any, idx: number) => {
                        const [name, path] = Array.isArray(item) ? item : [item.name || '', item.path || '']
                        return (
                          <div key={idx} className="card mb-2">
                            <div className="card-body">
                              <div className="row align-items-center">
                                <div className="col-md-4">
                                  <input
                                    type="text"
                                    className="form-control form-control-sm"
                                    value={name}
                                    onChange={(e) => {
                                      if (!currentIndexer) return
                                      const updated = [...currentIndexer.settings.projects]
                                      updated[idx] = [e.target.value, path]
                                      const indexerIndex = indexers.findIndex(idx => idx === currentIndexer)
                                      if (indexerIndex >= 0) {
                                        onUpdateIndexer(
                                          indexerIndex,
                                          'settings',
                                          { ...currentIndexer.settings, projects: updated }
                                        )
                                      }
                                    }}
                                    placeholder="Project name"
                                  />
                                </div>
                                <div className="col-md-7">
                                  <PathSelector
                                    value={path}
                                    onChange={(newPath) => {
                                      if (!currentIndexer) return
                                      const updated = [...currentIndexer.settings.projects]
                                      updated[idx] = [name, newPath]
                                      const indexerIndex = indexers.findIndex(idx => idx === currentIndexer)
                                      if (indexerIndex >= 0) {
                                        onUpdateIndexer(
                                          indexerIndex,
                                          'settings',
                                          { ...currentIndexer.settings, projects: updated }
                                        )
                                      }
                                    }}
                                  />
                                </div>
                                <div className="col-md-1">
                                  <button
                                    className="btn btn-sm btn-outline-danger"
                                    onClick={() => {
                                      if (!currentIndexer) return
                                      const updated = [...currentIndexer.settings.projects]
                                      updated.splice(idx, 1)
                                      const indexerIndex = indexers.findIndex(idx => idx === currentIndexer)
                                      if (indexerIndex >= 0) {
                                        onUpdateIndexer(
                                          indexerIndex,
                                          'settings',
                                          { ...currentIndexer.settings, projects: updated }
                                        )
                                      }
                                    }}
                                  >
                                    ×
                                  </button>
                                </div>
                              </div>
                            </div>
                          </div>
                        )
                      })}
                      <button
                        className="btn btn-sm btn-outline-primary"
                        onClick={() => {
                          if (!currentIndexer) return
                          const updated = [...(currentIndexer.settings.projects || [])]
                          updated.push(['', ''])
                          const indexerIndex = indexers.findIndex(idx => idx === currentIndexer)
                          if (indexerIndex >= 0) {
                            onUpdateIndexer(
                              indexerIndex,
                              'settings',
                              { ...currentIndexer.settings, projects: updated }
                            )
                          }
                        }}
                      >
                        + Add Project
                      </button>
                    </div>
                  )}

                  {selectedType === 'conversations' && currentIndexer.settings?.conversation_types && (
                    <div>
                      <h6 className="mb-3">Conversation Types</h6>
                      {currentIndexer.settings.conversation_types.map((item: any, idx: number) => {
                        const [type, path] = Array.isArray(item) ? item : [item.type || '', item.path || '']
                        return (
                          <div key={idx} className="card mb-2">
                            <div className="card-body">
                              <div className="row align-items-center">
                                <div className="col-md-4">
                                  <input
                                    type="text"
                                    className="form-control form-control-sm"
                                    value={type}
                                    onChange={(e) => {
                                      if (!currentIndexer) return
                                      const updated = [...currentIndexer.settings.conversation_types]
                                      updated[idx] = [e.target.value, path]
                                      const indexerIndex = indexers.findIndex(idx => idx === currentIndexer)
                                      if (indexerIndex >= 0) {
                                        onUpdateIndexer(
                                          indexerIndex,
                                          'settings',
                                          { ...currentIndexer.settings, conversation_types: updated }
                                        )
                                      }
                                    }}
                                    placeholder="Conversation type"
                                  />
                                </div>
                                <div className="col-md-7">
                                  <PathSelector
                                    value={path}
                                    onChange={(newPath) => {
                                      if (!currentIndexer) return
                                      const updated = [...currentIndexer.settings.conversation_types]
                                      updated[idx] = [type, newPath]
                                      const indexerIndex = indexers.findIndex(idx => idx === currentIndexer)
                                      if (indexerIndex >= 0) {
                                        onUpdateIndexer(
                                          indexerIndex,
                                          'settings',
                                          { ...currentIndexer.settings, conversation_types: updated }
                                        )
                                      }
                                    }}
                                  />
                                </div>
                                <div className="col-md-1">
                                  <button
                                    className="btn btn-sm btn-outline-danger"
                                    onClick={() => {
                                      if (!currentIndexer) return
                                      const updated = [...currentIndexer.settings.conversation_types]
                                      updated.splice(idx, 1)
                                      const indexerIndex = indexers.findIndex(idx => idx === currentIndexer)
                                      if (indexerIndex >= 0) {
                                        onUpdateIndexer(
                                          indexerIndex,
                                          'settings',
                                          { ...currentIndexer.settings, conversation_types: updated }
                                        )
                                      }
                                    }}
                                  >
                                    ×
                                  </button>
                                </div>
                              </div>
                            </div>
                          </div>
                        )
                      })}
                      <button
                        className="btn btn-sm btn-outline-primary"
                        onClick={() => {
                          if (!currentIndexer) return
                          const updated = [...(currentIndexer.settings.conversation_types || [])]
                          updated.push(['', ''])
                          const indexerIndex = indexers.findIndex(idx => idx === currentIndexer)
                          if (indexerIndex >= 0) {
                            onUpdateIndexer(
                              indexerIndex,
                              'settings',
                              { ...currentIndexer.settings, conversation_types: updated }
                            )
                          }
                        }}
                      >
                        + Add Conversation Type
                      </button>
                    </div>
                  )}

                  <div className="mt-3 pt-3 border-top">
                    <button
                      className="btn btn-outline-danger"
                      onClick={() => {
                        if (!currentIndexer) return
                        const indexerIndex = indexers.findIndex(idx => idx === currentIndexer)
                        if (indexerIndex >= 0) {
                          onRemoveIndexer(indexerIndex)
                        }
                      }}
                    >
                      Disable {selectedTypeInfo.name} Indexer
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-5">
                  <div className="mb-3">
                    <span className="display-1">{selectedTypeInfo.icon}</span>
                  </div>
                  <h5>Not Configured</h5>
                  <p className="text-muted">
                    This indexer is not currently enabled. Click "Enable {selectedTypeInfo.name}" to start configuring it.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default IndexerTypeSelector

