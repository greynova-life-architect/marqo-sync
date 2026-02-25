interface IndexerListProps {
  indexers: Record<string, any>
}

function IndexerList({ indexers }: IndexerListProps) {
  return (
    <div className="card">
      <div className="card-header">
        <h5 className="mb-0">Active Indexers</h5>
      </div>
      <div className="card-body">
        {Object.keys(indexers).length === 0 ? (
          <p className="text-muted">No active indexers</p>
        ) : (
          <ul className="list-group list-group-flush">
            {Object.entries(indexers).map(([name, indexer]) => (
              <li key={name} className="list-group-item">
                <div className="d-flex justify-content-between">
                  <div>
                    <strong>{name}</strong>
                    <br />
                    <small className="text-muted">{indexer.type}</small>
                  </div>
                  <span className="badge bg-success">Active</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

export default IndexerList

