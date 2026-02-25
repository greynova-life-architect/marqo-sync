import { useEffect, useState } from 'react'
import { apiService } from '../services/api'

function Profiles() {
  const [profiles, setProfiles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState({ tenant_id: '', profile_type: '', query: '' })

  const fetchProfiles = async () => {
    try {
      const params = new URLSearchParams()
      if (filter.tenant_id) params.append('tenant_id', filter.tenant_id)
      if (filter.profile_type) params.append('profile_type', filter.profile_type)
      if (filter.query) params.append('query', filter.query)
      
      const response = await fetch(`/api/profiles?${params}`)
      const data = await response.json()
      setProfiles(data.profiles || [])
    } catch (err: any) {
      console.error('Failed to fetch profiles:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProfiles()
  }, [filter])

  if (loading) {
    return <div className="text-center p-5">Loading profiles...</div>
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h1 className="mb-1">Profiles</h1>
          <p className="text-muted mb-0">Manage user, agent, and organization profiles</p>
        </div>
        <button className="btn btn-primary">+ New Profile</button>
      </div>

      <div className="card mb-4">
        <div className="card-body">
          <div className="row g-3">
            <div className="col-md-4">
              <label className="form-label">Search</label>
              <input
                type="text"
                className="form-control"
                value={filter.query}
                onChange={(e) => setFilter({...filter, query: e.target.value})}
                placeholder="Search profiles..."
              />
            </div>
            <div className="col-md-4">
              <label className="form-label">Tenant ID</label>
              <input
                type="text"
                className="form-control"
                value={filter.tenant_id}
                onChange={(e) => setFilter({...filter, tenant_id: e.target.value})}
                placeholder="Filter by tenant..."
              />
            </div>
            <div className="col-md-4">
              <label className="form-label">Profile Type</label>
              <select
                className="form-select"
                value={filter.profile_type}
                onChange={(e) => setFilter({...filter, profile_type: e.target.value})}
              >
                <option value="">All Types</option>
                <option value="user">User</option>
                <option value="agent">Agent</option>
                <option value="organization">Organization</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="row">
        {profiles.map((profile) => (
          <div key={profile._id} className="col-md-4 mb-4">
            <div className="card">
              <div className="card-body">
                <h5 className="card-title">{profile.name || profile.profile_id}</h5>
                <p className="text-muted small mb-2">
                  <span className="badge bg-secondary">{profile.profile_type}</span>
                  {profile.tenant_id && (
                    <span className="badge bg-info ms-2">Tenant: {profile.tenant_id}</span>
                  )}
                </p>
                {profile.description && (
                  <p className="card-text">{profile.description}</p>
                )}
                {profile.email && (
                  <p className="card-text small"><strong>Email:</strong> {profile.email}</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {profiles.length === 0 && (
        <div className="text-center p-5">
          <p className="text-muted">No profiles found</p>
        </div>
      )}
    </div>
  )
}

export default Profiles

