import { Link, useLocation } from 'react-router-dom'

function Sidebar() {
  const location = useLocation()
  
  const navItems = [
    { path: '/', label: 'Dashboard', icon: 'fa-chart-bar' },
    { path: '/configuration', label: 'Configuration', icon: 'fa-cog' },
    { path: '/index-management', label: 'Index Management', icon: 'fa-database' },
    { path: '/profiles', label: 'Profiles', icon: 'fa-user' },
    { path: '/conversations', label: 'Conversations', icon: 'fa-comments' },
    { path: '/memories', label: 'Memories', icon: 'fa-brain' },
    { path: '/logs', label: 'Logs', icon: 'fa-file-alt' },
  ]
  
  const isOnboarding = location.pathname === '/onboarding'
  
  if (isOnboarding) {
    return null
  }
  
  return (
    <div style={{ 
      width: '250px', 
      minHeight: '100vh',
      backgroundColor: 'var(--clinical-bg-secondary)',
      borderRight: '1px solid var(--clinical-border)'
    }}>
      <div className="p-3">
        <h5 className="mb-3" style={{ color: 'var(--clinical-text-primary)', fontWeight: 600 }}>Navigation</h5>
        <ul className="nav nav-pills flex-column">
          {navItems.map(item => {
            const isActive = location.pathname === item.path
            return (
              <li key={item.path} className="nav-item mb-1">
                <Link
                  to={item.path}
                  className="nav-link"
                  style={{
                    backgroundColor: isActive ? 'var(--clinical-accent)' : 'transparent',
                    color: isActive ? 'var(--clinical-text-primary)' : 'var(--clinical-text-secondary)',
                    border: '1px solid',
                    borderColor: isActive ? 'var(--clinical-accent)' : 'transparent',
                    borderRadius: '6px',
                    padding: '0.5rem 1rem',
                    textDecoration: 'none',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.backgroundColor = 'var(--clinical-bg-tertiary)'
                      e.currentTarget.style.borderColor = 'var(--clinical-border)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.backgroundColor = 'transparent'
                      e.currentTarget.style.borderColor = 'transparent'
                    }
                  }}
                >
                  <i className={`fas ${item.icon} me-2`}></i>
                  {item.label}
                </Link>
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}

export default Sidebar

