import { Routes, Route } from 'react-router-dom'
import './App.css'
import { MainPage } from './pages/MainPage'
import { DetailPage } from './pages/DetailPage'
import { ExecutionDetailPage } from './pages/ExecutionDetailPage'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>CV AI Pipeline</h1>
        </div>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<MainPage />} />
          <Route path="/cv/:id" element={<DetailPage />} />
          <Route path="/executions/:id" element={<ExecutionDetailPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
