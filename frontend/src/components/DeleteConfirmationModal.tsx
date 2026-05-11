import { useState } from 'react'

interface DeleteConfirmationModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => Promise<void>
  fileName: string
}

export function DeleteConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  fileName,
}: DeleteConfirmationModalProps) {
  const [isDeleting, setIsDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleConfirm = async () => {
    setIsDeleting(true)
    setError(null)
    try {
      await onConfirm()
      // Note: we don't close here, the parent will unmount/navigate away
    } catch (err: any) {
      setError(err.message || 'An error occurred during deletion.')
      setIsDeleting(false)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Delete CV</h2>
        <p>Are you sure you want to delete the CV <strong>{fileName}</strong>?</p>
        <p className="warning-text">This action cannot be undone.</p>
        
        {error && <div className="error-alert">{error}</div>}
        
        <div className="modal-actions">
          <button 
            className="btn btn-secondary" 
            onClick={onClose} 
            disabled={isDeleting}
          >
            No, Cancel
          </button>
          <button 
            className="btn btn-danger" 
            onClick={handleConfirm} 
            disabled={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Yes, Delete'}
          </button>
        </div>
      </div>
    </div>
  )
}
