import { useState, useEffect } from 'react'
import { apiService } from '../../services/api'

interface PathSelectorProps {
  value: string
  onChange: (path: string) => void
}

function PathSelector({ value, onChange }: PathSelectorProps) {
  const [validating, setValidating] = useState(false)
  const [validation, setValidation] = useState<any>(null)

  useEffect(() => {
    if (value) {
      validatePath(value)
    } else {
      setValidation(null)
    }
  }, [value])

  const validatePath = async (path: string) => {
    if (!path) {
      setValidation(null)
      return
    }

    setValidating(true)
    try {
      const response = await apiService.validatePath(path)
      setValidation(response.data)
    } catch (err) {
      setValidation({ valid: false, error: 'Validation failed' })
    } finally {
      setValidating(false)
    }
  }

  const getValidationIcon = () => {
    if (validating) return <i className="fas fa-spinner fa-spin"></i>
    if (!validation) return null
    if (validation.valid) return <i className="fas fa-check-circle text-success"></i>
    return <i className="fas fa-times-circle text-danger"></i>
  }

  const getValidationColor = () => {
    if (!validation) return ''
    if (validation.valid) return 'is-valid'
    return 'is-invalid'
  }

  return (
    <div>
      <div className="input-group">
        <input
          type="text"
          className={`form-control ${getValidationColor()}`}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="C:\path\to\directory"
        />
        <span className="input-group-text">{getValidationIcon()}</span>
      </div>
      {validation && !validation.valid && validation.error && (
        <div className="invalid-feedback d-block">
          {validation.error}
        </div>
      )}
      {validation && validation.valid && (
        <div className="valid-feedback d-block">
          Path is valid and accessible
        </div>
      )}
    </div>
  )
}

export default PathSelector

