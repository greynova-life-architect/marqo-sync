import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiService } from '../services/api'

function Onboarding() {
  const [step, setStep] = useState(1)
  const [marqoUrl, setMarqoUrl] = useState('http://localhost:8882')
  const [connectionStatus, setConnectionStatus] = useState<string | null>(null)
  const [testing, setTesting] = useState(false)
  const navigate = useNavigate()

  const totalSteps = 4

  const handleTestConnection = async () => {
    setTesting(true)
    setConnectionStatus('Testing...')
    try {
      const response = await apiService.testConnection(marqoUrl)
      if (response.data.success) {
        setConnectionStatus('success')
      } else {
        setConnectionStatus('error')
      }
    } catch (err: any) {
      setConnectionStatus('error')
    } finally {
      setTesting(false)
    }
  }

  const handleNext = () => {
    if (step < totalSteps) {
      setStep(step + 1)
    } else {
      navigate('/dashboard')
    }
  }

  const handleSkip = () => {
    navigate('/dashboard')
  }

  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-lg-8">
          <div className="card shadow">
            <div className="card-header" style={{ background: 'linear-gradient(135deg, var(--clinical-bg-secondary) 0%, var(--clinical-bg-tertiary) 100%)' }}>
              <h3 className="mb-0" style={{ color: 'var(--clinical-text-primary)' }}>Marqo Sync Setup Wizard</h3>
              <div className="progress mt-3" style={{ height: '8px' }}>
                <div
                  className="progress-bar"
                  role="progressbar"
                  style={{ width: `${(step / totalSteps) * 100}%` }}
                />
              </div>
            </div>
            <div className="card-body p-5">
              {step === 1 && (
                <div>
                  <h4 className="mb-4">Step 1: Connect to Marqo</h4>
                  <p className="text-muted mb-4">
                    Enter your Marqo server URL to begin. This is where your indexes will be stored.
                  </p>
                  <div className="mb-3">
                    <label className="form-label fw-bold">Marqo Server URL</label>
                    <div className="input-group">
                      <input
                        type="text"
                        className="form-control form-control-lg"
                        value={marqoUrl}
                        onChange={(e) => {
                          setMarqoUrl(e.target.value)
                          setConnectionStatus(null)
                        }}
                        placeholder="http://localhost:8882"
                      />
                      <button
                        className="btn btn-primary"
                        onClick={handleTestConnection}
                        disabled={testing}
                      >
                        {testing ? 'Testing...' : 'Test Connection'}
                      </button>
                    </div>
                    {connectionStatus === 'success' && (
                      <div className="alert alert-success mt-3">
                        <i className="fas fa-check-circle me-2"></i>Connection successful! You can proceed to the next step.
                      </div>
                    )}
                    {connectionStatus === 'error' && (
                      <div className="alert alert-danger mt-3">
                        <i className="fas fa-times-circle me-2"></i>Connection failed. Please check your Marqo server URL and ensure it's running.
                      </div>
                    )}
                  </div>
                  <div className="d-flex justify-content-between mt-4">
                    <button className="btn btn-link" onClick={handleSkip}>
                      Skip Setup
                    </button>
                    <button
                      className="btn btn-primary"
                      onClick={handleNext}
                      disabled={connectionStatus !== 'success'}
                    >
                      Next: Configure Indexers →
                    </button>
                  </div>
                </div>
              )}

              {step === 2 && (
                <div>
                  <h4 className="mb-4">Step 2: Configure Codebase Indexer</h4>
                  <p className="text-muted mb-4">
                    Add the code repositories you want to index. These will be searchable in the 'codebase' index.
                  </p>
                  <div className="alert alert-info">
                    <strong>Tip:</strong> You can add multiple projects. Each project will be tagged with its name in the index.
                  </div>
                  <div className="text-center mt-4">
                    <button className="btn btn-primary btn-lg" onClick={() => navigate('/configuration?focus=codebase')}>
                      Go to Configuration →
                    </button>
                  </div>
                  <div className="d-flex justify-content-between mt-4">
                    <button className="btn btn-secondary" onClick={() => setStep(step - 1)}>
                      ← Back
                    </button>
                    <button className="btn btn-primary" onClick={handleNext}>
                      Next: Configure Conversations →
                    </button>
                  </div>
                </div>
              )}

              {step === 3 && (
                <div>
                  <h4 className="mb-4">Step 3: Configure Conversation Indexer</h4>
                  <p className="text-muted mb-4">
                    Add directories containing your AI conversation history (ChatGPT, Claude, etc.)
                  </p>
                  <div className="alert alert-info">
                    <strong>Tip:</strong> These conversations will be indexed and searchable alongside your codebase.
                  </div>
                  <div className="text-center mt-4">
                    <button className="btn btn-primary btn-lg" onClick={() => navigate('/configuration?focus=conversations')}>
                      Go to Configuration →
                    </button>
                  </div>
                  <div className="d-flex justify-content-between mt-4">
                    <button className="btn btn-secondary" onClick={() => setStep(step - 1)}>
                      ← Back
                    </button>
                    <button className="btn btn-primary" onClick={handleNext}>
                      Next: Review & Start →
                    </button>
                  </div>
                </div>
              )}

              {step === 4 && (
                <div>
                  <h4 className="mb-4">Step 4: Review & Start Syncing</h4>
                  <p className="text-muted mb-4">
                    Review your configuration and start the sync service.
                  </p>
                  <div className="card mb-3">
                    <div className="card-body">
                      <h6>Configuration Summary</h6>
                      <ul className="list-unstyled">
                        <li><i className="fas fa-check-circle text-success me-2"></i>Marqo Server: {marqoUrl}</li>
                        <li><i className="fas fa-check-circle text-success me-2"></i>Codebase indexer configured</li>
                        <li><i className="fas fa-check-circle text-success me-2"></i>Conversation indexer configured</li>
                      </ul>
                    </div>
                  </div>
                  <div className="alert alert-success">
                    <strong>Ready to go!</strong> Your configuration is complete. You can now start syncing your files.
                  </div>
                  <div className="d-flex justify-content-between mt-4">
                    <button className="btn btn-secondary" onClick={() => setStep(step - 1)}>
                      ← Back
                    </button>
                    <button className="btn btn-success btn-lg" onClick={handleNext}>
                      Complete Setup →
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Onboarding

