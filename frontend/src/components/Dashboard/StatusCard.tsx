interface StatusCardProps {
  status: string
}

function StatusCard({ status }: StatusCardProps) {
  const getStatusColor = () => {
    switch (status.toLowerCase()) {
      case 'running':
        return 'success'
      case 'ready':
        return 'info'
      case 'stopped':
        return 'secondary'
      case 'error':
        return 'danger'
      default:
        return 'warning'
    }
  }

  return (
    <div className="card">
      <div className="card-body">
        <h5 className="card-title">Service Status</h5>
        <p className="card-text">
          <span className={`badge bg-${getStatusColor()}`}>
            {status.toUpperCase()}
          </span>
        </p>
      </div>
    </div>
  )
}

export default StatusCard

