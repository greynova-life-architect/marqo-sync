function Navbar() {
  return (
    <nav style={{
      backgroundColor: 'var(--clinical-bg-secondary)',
      borderBottom: '2px solid var(--clinical-border)',
      padding: '0.75rem 1.5rem'
    }}>
      <div className="container-fluid d-flex justify-content-between align-items-center">
        <span style={{
          color: 'var(--clinical-text-primary)',
          fontSize: '1.25rem',
          fontWeight: 600
        }}>
          Marqo Sync
        </span>
        <div>
          <span style={{
            color: 'var(--clinical-text-secondary)',
            fontSize: '0.875rem'
          }}>
            Configuration & Management
          </span>
        </div>
      </div>
    </nav>
  )
}

export default Navbar

