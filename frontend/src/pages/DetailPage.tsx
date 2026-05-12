import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, Trash2, Play, ExternalLink } from 'lucide-react'
import { API_BASE_URL } from '../config'
import type { CV } from './MainPage'
import { DeleteConfirmationModal } from '../components/DeleteConfirmationModal'

export function DetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  
  const [cv, setCv] = useState<CV | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [processing, setProcessing] = useState(false)

  useEffect(() => {
    const fetchCv = async () => {
      try {
        setLoading(true)
        const res = await fetch(`${API_BASE_URL}/cvs/${id}`)
        if (!res.ok) {
          if (res.status === 404) throw new Error('CV not found')
          throw new Error('Failed to fetch CV details')
        }
        const data = await res.json()
        setCv(data)
        setError(null)
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    if (id) fetchCv()
  }, [id])

  const handleDelete = async () => {
    if (!cv) return
    const res = await fetch(`${API_BASE_URL}/cvs/${cv.id}`, {
      method: 'DELETE'
    })
    
    if (!res.ok) {
      const errData = await res.json()
      throw new Error(errData.detail || 'Deletion failed')
    }
    
    // Successfully deleted
    navigate('/')
  }

  const handleProcess = async () => {
    if (!cv) return
    try {
      setProcessing(true)
      const res = await fetch(`${API_BASE_URL}/cvs/${cv.id}/process`, {
        method: 'POST'
      })
      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Processing failed')
      }
      alert('CV processing started successfully!')
    } catch (err: any) {
      alert(err.message)
    } finally {
      setProcessing(false)
    }
  }

  if (loading) {
    return <div className="page-container p-8 text-center">Loading CV Details...</div>
  }

  if (error || !cv) {
    return (
      <div className="page-container p-8 text-center">
        <div className="error-alert max-w-md mx-auto">{error || 'Unknown error occurred'}</div>
        <button className="btn btn-secondary mt-4" onClick={() => navigate('/')}>
          <ArrowLeft size={18} /> Back to List
        </button>
      </div>
    )
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="flex items-center gap-4">
          <button className="btn-icon btn-secondary" onClick={() => navigate('/')} title="Back to List">
            <ArrowLeft size={20} />
          </button>
          <h2>CV Details</h2>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-primary" onClick={handleProcess} disabled={processing}>
            <Play size={18} /> {processing ? 'Starting...' : 'Process CV'}
          </button>
          <button className="btn btn-danger" onClick={() => setIsDeleteModalOpen(true)}>
            <Trash2 size={18} /> Delete CV
          </button>
        </div>
      </div>

      <div className="detail-card">
        <div className="detail-row">
          <span className="detail-label">ID:</span>
          <span className="detail-value monospace-text">{cv.id}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Filename:</span>
          <span className="detail-value">{cv.filename}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">File Hash:</span>
          <span className="detail-value monospace-text">{cv.file_hash}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Status:</span>
          <span className={`status-badge status-${cv.status}`}>{cv.status}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Uploaded At:</span>
          <span className="detail-value">{new Date(cv.created_at).toLocaleString()}</span>
        </div>
      </div>
      
      <div className="executions-section mt-8">
        <h3>Executions</h3>
        {!cv.executions || cv.executions.length === 0 ? (
          <p className="text-secondary mt-2">No executions yet.</p>
        ) : (
          <div className="table-container mt-4">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Id</th>
                  <th>Workflow Id</th>
                  <th>State</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {cv.executions.map(exec => (
                  <tr key={exec.id}>
                    <td>
                      <Link to={`/executions/${exec.id}`} className="text-primary hover:underline" style={{ color: 'var(--primary-color)', textDecoration: 'none', fontWeight: 600 }}>
                        {exec.id}
                      </Link>
                    </td>
                    <td className="monospace-text">
                      {exec.workflow_id ? (
                        <a 
                          href={`http://localhost:8080/namespaces/default/workflows/${exec.workflow_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-primary hover:underline"
                          style={{ color: 'var(--primary-color)', textDecoration: 'none' }}
                        >
                          {exec.workflow_id} <ExternalLink size={14} />
                        </a>
                      ) : (
                        <span className="text-secondary">N/A</span>
                      )}
                    </td>
                    <td>
                      <span className={`status-badge status-${exec.state}`}>
                        {exec.state}
                      </span>
                    </td>
                    <td>{new Date(exec.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <DeleteConfirmationModal
        isOpen={isDeleteModalOpen}
        fileName={cv.filename}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={handleDelete}
      />
    </div>
  )
}
