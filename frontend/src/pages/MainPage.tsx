import { useState, useEffect, useRef } from 'react'
import type { ChangeEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, Trash2, Upload } from 'lucide-react'
import { API_BASE_URL } from '../config'
import { DeleteConfirmationModal } from '../components/DeleteConfirmationModal'
import { UploadModal } from '../components/UploadModal'

export interface CV {
  id: string
  filename: string
  file_hash: string
  status: string
  created_at: string
}

export function MainPage() {
  const navigate = useNavigate()
  const [cvs, setCvs] = useState<CV[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Pagination
  const [skip, setSkip] = useState(0)
  const limit = 10
  const [total, setTotal] = useState(0)

  // Modals
  const [cvToDelete, setCvToDelete] = useState<CV | null>(null)
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  const fetchCvs = async () => {
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE_URL}/cvs?skip=${skip}&limit=${limit}`)
      if (!res.ok) throw new Error('Failed to fetch CVs')
      const data = await res.json()
      setCvs(data.items)
      setTotal(data.total)
      setError(null)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCvs()
  }, [skip])

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      setIsUploadModalOpen(true)
      setIsUploading(false)
      setUploadError('Only PDF files are allowed.')
      return
    }

    setIsUploadModalOpen(true)
    setIsUploading(true)
    setUploadError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_BASE_URL}/cvs/upload`, {
        method: 'POST',
        body: formData,
      })
      
      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Upload failed')
      }
      
      const newCv = await res.json()
      setIsUploadModalOpen(false)
      navigate(`/cv/${newCv.id}`)
    } catch (err: any) {
      setIsUploading(false)
      setUploadError(err.message)
    } finally {
      // Clear input so the same file can be selected again
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleDelete = async () => {
    if (!cvToDelete) return
    
    const res = await fetch(`${API_BASE_URL}/cvs/${cvToDelete.id}`, {
      method: 'DELETE'
    })
    
    if (!res.ok) {
      const errData = await res.json()
      throw new Error(errData.detail || 'Deletion failed')
    }
    
    setCvToDelete(null)
    // Refresh current page
    fetchCvs()
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h2>Uploaded CVs</h2>
        <button className="btn btn-primary" onClick={handleUploadClick}>
          <Upload size={18} /> Upload CV
        </button>
        <input 
          type="file" 
          accept=".pdf,application/pdf" 
          ref={fileInputRef} 
          style={{ display: 'none' }} 
          onChange={handleFileChange}
        />
      </div>

      {error ? (
        <div className="error-alert">{error}</div>
      ) : loading && cvs.length === 0 ? (
        <div className="text-center p-8">Loading CVs...</div>
      ) : cvs.length === 0 ? (
        <div className="empty-state">
          <p>No CVs are uploaded yet.</p>
        </div>
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>File ID</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {cvs.map(cv => (
                  <tr key={cv.id}>
                    <td className="monospace-text" title={cv.id}>{cv.id.substring(0, 8)}...</td>
                    <td>{cv.filename}</td>
                    <td className="monospace-text" title={cv.file_hash}>{cv.file_hash.substring(0, 8)}...</td>
                    <td>
                      <span className={`status-badge status-${cv.status}`}>
                        {cv.status}
                      </span>
                    </td>
                    <td className="actions-cell">
                      <button 
                        className="btn-icon" 
                        title="View Details"
                        onClick={() => navigate(`/cv/${cv.id}`)}
                      >
                        <Eye size={18} />
                      </button>
                      <button 
                        className="btn-icon btn-icon-danger" 
                        title="Delete CV"
                        onClick={() => setCvToDelete(cv)}
                      >
                        <Trash2 size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {total > limit && (
            <div className="pagination">
              <button 
                disabled={skip === 0} 
                onClick={() => setSkip(s => Math.max(0, s - limit))}
                className="btn btn-secondary btn-sm"
              >
                Previous
              </button>
              <span className="page-info">
                Showing {skip + 1} - {Math.min(skip + limit, total)} of {total}
              </span>
              <button 
                disabled={skip + limit >= total} 
                onClick={() => setSkip(s => s + limit)}
                className="btn btn-secondary btn-sm"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      <DeleteConfirmationModal 
        isOpen={!!cvToDelete}
        fileName={cvToDelete?.filename || ''}
        onClose={() => setCvToDelete(null)}
        onConfirm={handleDelete}
      />
      
      <UploadModal 
        isOpen={isUploadModalOpen}
        isUploading={isUploading}
        error={uploadError}
        onClose={() => setIsUploadModalOpen(false)}
      />
    </div>
  )
}
