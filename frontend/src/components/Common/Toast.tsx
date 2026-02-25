import { useEffect } from 'react'

interface ToastProps {
  message: string
  type: 'success' | 'error' | 'info'
  onClose: () => void
  duration?: number
}

function Toast({ message, type, onClose, duration = 3000 }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose()
    }, duration)
    return () => clearTimeout(timer)
  }, [duration, onClose])

  const getBgColor = () => {
    if (type === 'success') return 'rgba(34, 197, 94, 0.15)'
    if (type === 'error') return 'rgba(239, 68, 68, 0.15)'
    return 'rgba(14, 165, 233, 0.15)'
  }

  const getTextColor = () => {
    if (type === 'success') return 'var(--status-active)'
    if (type === 'error') return 'var(--status-error)'
    return 'var(--status-syncing)'
  }

  return (
    <div
      className="toast show position-fixed top-0 end-0 m-3"
      role="alert"
      style={{ 
        zIndex: 9999,
        backgroundColor: getBgColor(),
        border: `1px solid ${getTextColor()}`,
        color: getTextColor()
      }}
    >
      <div className="toast-header" style={{ backgroundColor: 'var(--clinical-bg-tertiary)', borderBottom: '1px solid var(--clinical-border)' }}>
        <strong className="me-auto">{type === 'success' ? 'Success' : type === 'error' ? 'Error' : 'Info'}</strong>
        <button
          type="button"
          className="btn-close btn-close-white"
          onClick={onClose}
          style={{ filter: 'invert(1)' }}
        ></button>
      </div>
      <div className="toast-body">{message}</div>
    </div>
  )
}

export default Toast

