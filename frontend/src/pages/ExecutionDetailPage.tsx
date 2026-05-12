import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, Download, ExternalLink, FileJson } from 'lucide-react'
import { API_BASE_URL } from '../config'

interface Artifact {
  id: number
  type: string
  file_hash: string
}

interface Execution {
  id: number
  cv_id: number
  workflow_id: string | null
  state: string
  created_at: string
  artifacts: Artifact[]
}

export function ExecutionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  
  const [execution, setExecution] = useState<Execution | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchExecution = async () => {
      try {
        setLoading(true)
        const res = await fetch(`${API_BASE_URL}/cvs/executions/${id}`)
        if (!res.ok) {
          if (res.status === 404) throw new Error('Execution not found')
          throw new Error('Failed to fetch execution details')
        }
        const data = await res.json()
        setExecution(data)
        setError(null)
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    if (id) fetchExecution()
  }, [id])

  if (loading) {
    return <div className="page-container p-8 text-center">Loading Execution Details...</div>
  }

  if (error || !execution) {
    return (
      <div className="page-container p-8 text-center">
        <div className="error-alert max-w-md mx-auto">{error || 'Unknown error occurred'}</div>
        <button className="btn btn-secondary mt-4" onClick={() => navigate(-1)}>
          <ArrowLeft size={18} /> Back
        </button>
      </div>
    )
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="flex items-center gap-4">
          <button className="btn-icon btn-secondary" onClick={() => navigate(-1)} title="Go Back">
            <ArrowLeft size={20} />
          </button>
          <h2>Execution Details</h2>
        </div>
        <div className="flex gap-2">
          <Link to={`/cv/${execution.cv_id}`} className="btn btn-secondary">
            <FileJson size={18} /> View CV Details
          </Link>
          {execution.workflow_id && (
            <a 
              href={`http://localhost:8080/namespaces/default/workflows/${execution.workflow_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-primary"
            >
              <ExternalLink size={18} /> Temporal UI
            </a>
          )}
        </div>
      </div>

      <div className="detail-card">
        <div className="detail-row">
          <span className="detail-label">Execution ID:</span>
          <span className="detail-value monospace-text">{execution.id}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">CV ID:</span>
          <span className="detail-value monospace-text">
            <Link to={`/cv/${execution.cv_id}`} className="text-primary hover:underline">
              {execution.cv_id}
            </Link>
          </span>
        </div>
        <div className="detail-row">
          <span className="detail-label">State:</span>
          <span className={`status-badge status-${execution.state}`}>{execution.state}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Workflow ID:</span>
          <span className="detail-value monospace-text">{execution.workflow_id || 'N/A'}</span>
        </div>
        <div className="detail-row">
          <span className="detail-label">Started At:</span>
          <span className="detail-value">{new Date(execution.created_at).toLocaleString()}</span>
        </div>
      </div>

      <div className="artifacts-section mt-8">
        <h3>Execution Artifacts</h3>
        {!execution.artifacts || execution.artifacts.length === 0 ? (
          <p className="text-secondary mt-2">No artifacts generated yet.</p>
        ) : (
          <div className="table-container mt-4">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Id</th>
                  <th>Type</th>
                  <th>File Id (Hash)</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {execution.artifacts.map(artifact => (
                  <tr key={artifact.id}>
                    <td>{artifact.id}</td>
                    <td>
                      <span className="monospace-text" style={{ color: 'var(--text-color)' }}>
                        {artifact.type}
                      </span>
                    </td>
                    <td>
                      <span className="monospace-text">{artifact.file_hash}</span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <a 
                        href={`${API_BASE_URL}/cvs/artifacts/${artifact.id}/download`}
                        className="btn-icon"
                        title="Download Artifact"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Download size={18} />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
