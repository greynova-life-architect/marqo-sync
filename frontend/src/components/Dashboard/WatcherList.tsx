interface WatcherListProps {
  watchers: Record<string, any>
}

function WatcherList({ watchers }: WatcherListProps) {
  return (
    <div className="card">
      <div className="card-header">
        <h5 className="mb-0">Active Watchers</h5>
      </div>
      <div className="card-body">
        {Object.keys(watchers).length === 0 ? (
          <p className="text-muted">No active watchers</p>
        ) : (
          <ul className="list-group list-group-flush">
            {Object.entries(watchers).map(([name, watcher]) => (
              <li key={name} className="list-group-item">
                <div className="d-flex justify-content-between">
                  <div>
                    <strong>{name}</strong>
                    <br />
                    <small className="text-muted">{watcher.root_dir || 'N/A'}</small>
                  </div>
                  <span className={`badge bg-${watcher.watching ? 'success' : 'secondary'}`}>
                    {watcher.watching ? 'Watching' : 'Stopped'}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

export default WatcherList

