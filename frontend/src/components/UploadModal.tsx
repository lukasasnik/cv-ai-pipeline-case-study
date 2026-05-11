
interface UploadModalProps {
  isOpen: boolean
  isUploading: boolean
  error: string | null
  onClose: () => void
}

export function UploadModal({
  isOpen,
  isUploading,
  error,
  onClose
}: UploadModalProps) {
  if (!isOpen) return null

  return (
    <div className="modal-overlay">
      <div className="modal-content text-center">
        {isUploading ? (
          <>
            <h2>Uploading CV...</h2>
            <div className="spinner"></div>
            <p>Please wait while your file is being uploaded.</p>
          </>
        ) : error ? (
          <>
            <h2 className="text-danger">Upload Failed</h2>
            <div className="error-alert">{error}</div>
            <div className="modal-actions justify-center">
              <button className="btn btn-primary" onClick={onClose}>
                Close
              </button>
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}
