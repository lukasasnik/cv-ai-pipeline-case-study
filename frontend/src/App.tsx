import { useEffect, useState } from 'react'
import './App.css'

interface ApiStatus {
  status: string
  message: string
}

function App() {
  const [apiStatus, setApiStatus] = useState<ApiStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkApi = async () => {
      try {
        // In Docker (Nginx), requests go through /api/ proxy.
        // In dev mode, use the direct URL.
        const baseUrl = import.meta.env.DEV ? 'http://localhost:8002' : '/api'
        const response = await fetch(`${baseUrl}/`)
        const data = await response.json()
        setApiStatus(data)
      } catch {
        setError('Unable to connect to API')
      } finally {
        setLoading(false)
      }
    }

    checkApi()
  }, [])

  return (
    <div className="app">
      <div className="hero">
        <div className="hero-content">
          <h1>CV AI Pipeline</h1>
          <p className="subtitle">
            Intelligent CV processing powered by AI
          </p>

          <div className="status-card">
            <div className="status-header">
              <span className="status-icon">
                {loading ? '⏳' : apiStatus ? '🟢' : '🔴'}
              </span>
              <h3>API Status</h3>
            </div>
            <div className="status-body">
              {loading && <p className="status-text">Checking connection...</p>}
              {apiStatus && (
                <p className="status-text success">{apiStatus.message}</p>
              )}
              {error && <p className="status-text error">{error}</p>}
            </div>
          </div>

          <div className="features">
            <div className="feature-card">
              <span className="feature-icon">📄</span>
              <h3>Upload CVs</h3>
              <p>Upload PDF and document files for processing</p>
            </div>
            <div className="feature-card">
              <span className="feature-icon">🤖</span>
              <h3>AI Analysis</h3>
              <p>Automated CV parsing and data extraction</p>
            </div>
            <div className="feature-card">
              <span className="feature-icon">⚡</span>
              <h3>Pipeline</h3>
              <p>Temporal-powered reliable workflow execution</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
