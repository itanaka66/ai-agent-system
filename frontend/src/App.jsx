import { NavLink, Route, Routes, Navigate } from 'react-router-dom'
import './App.css'
import AgentsPage from './pages/AgentsPage.jsx'
import WorkflowsListPage from './pages/WorkflowsListPage.jsx'
import WorkflowBuilderPage from './pages/WorkflowBuilderPage.jsx'

function App() {
  return (
    <div className="app-shell">
      <nav className="app-nav">
        <span className="brand">🤖 AI Agent Console</span>
        <NavLink to="/agents" className={({ isActive }) => (isActive ? 'active' : '')}>
          エージェント設定
        </NavLink>
        <NavLink to="/workflows" className={({ isActive }) => (isActive ? 'active' : '')}>
          ワークフロービルダー
        </NavLink>
      </nav>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<Navigate to="/agents" replace />} />
          <Route path="/agents" element={<AgentsPage />} />
          <Route path="/workflows" element={<WorkflowsListPage />} />
          <Route path="/workflows/:name" element={<WorkflowBuilderPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
