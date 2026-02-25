import { useState } from 'react'
import PathSelector from './PathSelector'

interface IndexerItem {
  id: string
  name: string
  path: string
}

interface IndexerConfigCardProps {
  title: string
  description: string
  icon: string
  items: IndexerItem[]
  onAdd: () => void
  onRemove: (id: string) => void
  onUpdate: (id: string, field: 'name' | 'path', value: string) => void
  nameLabel: string
  pathLabel: string
  emptyMessage: string
}

function IndexerConfigCard({
  title,
  description,
  icon,
  items,
  onAdd,
  onRemove,
  onUpdate,
  nameLabel,
  pathLabel,
  emptyMessage
}: IndexerConfigCardProps) {
  return (
    <div className="card mb-4 border-0 shadow-sm">
      <div className="card-header d-flex justify-content-between align-items-center">
        <div>
          <h5 className="mb-0">
            <span className="me-2">{icon}</span>
            {title}
          </h5>
          <small className="text-muted">{description}</small>
        </div>
        <button className="btn btn-sm btn-primary" onClick={onAdd}>
          + Add
        </button>
      </div>
      <div className="card-body">
        {items.length === 0 ? (
          <div className="text-center py-4">
            <p className="text-muted mb-3">{emptyMessage}</p>
            <button className="btn btn-outline-primary" onClick={onAdd}>
              Add Your First Item
            </button>
          </div>
        ) : (
          <div className="list-group">
            {items.map((item) => (
              <div key={item.id} className="list-group-item">
                <div className="row g-3 align-items-end">
                  <div className="col-md-4">
                    <label className="form-label small">{nameLabel}</label>
                    <input
                      type="text"
                      className="form-control form-control-sm"
                      value={item.name}
                      onChange={(e) => onUpdate(item.id, 'name', e.target.value)}
                      placeholder="Enter name..."
                    />
                  </div>
                  <div className="col-md-7">
                    <label className="form-label small">{pathLabel}</label>
                    <PathSelector
                      value={item.path}
                      onChange={(path) => onUpdate(item.id, 'path', path)}
                    />
                  </div>
                  <div className="col-md-1">
                    <button
                      className="btn btn-sm btn-outline-danger"
                      onClick={() => onRemove(item.id)}
                      title="Remove"
                    >
                      ×
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default IndexerConfigCard

