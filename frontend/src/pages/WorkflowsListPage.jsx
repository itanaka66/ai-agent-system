import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client.js'

const BLANK_WORKFLOW = (name) => ({
  name,
  description: '',
  nodes: [
    { id: 'start_node', type: 'START_NODE', position: [40, 160], outputs: [{ output: 'question' }] },
    { id: 'end_node', type: 'END_NODE', position: [600, 160], inputs: [{ input: 'question' }] },
  ],
})

export default function WorkflowsListPage() {
  const [workflows, setWorkflows] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  const load = async () => {
    setLoading(true)
    try {
      const res = await api.listWorkflows()
      setWorkflows(res.workflows)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const createWorkflow = async () => {
    const name = prompt('新しいワークフローの名前（半角英数字・アンダースコア・ハイフン）を入力してください')
    if (!name) return
    setError('')
    try {
      await api.saveWorkflow(name, BLANK_WORKFLOW(name))
      navigate(`/workflows/${name}`)
    } catch (e) {
      setError(e.message)
    }
  }

  const removeWorkflow = async (name, e) => {
    e.stopPropagation()
    if (!confirm(`ワークフロー '${name}' を削除しますか？`)) return
    try {
      await api.deleteWorkflow(name)
      await load()
    } catch (e2) {
      setError(e2.message)
    }
  }

  return (
    <div>
      <h1>ワークフロービルダー</h1>
      <p>ノードをドラッグして配置し、エージェント間のデータフロー（提案 → 批評 → 判定 → 検証など）を視覚的に設計できます。</p>

      {error && <div className="banner-error">{error}</div>}

      <div className="card" style={{ marginBottom: 16 }}>
        <button className="btn btn-primary" onClick={createWorkflow}>+ 新規ワークフロー作成</button>
      </div>

      {loading ? (
        <p>読み込み中...</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 12 }}>
          {workflows.map((w) => (
            <div
              key={w.name}
              className="card"
              style={{ cursor: 'pointer' }}
              onClick={() => navigate(`/workflows/${w.name}`)}
            >
              <strong>{w.display_name}</strong>
              <div style={{ fontSize: 13, margin: '6px 0' }}>{w.description || '説明なし'}</div>
              <div style={{ fontSize: 12, display: 'flex', justifyContent: 'space-between' }}>
                <span>{w.node_count} ノード ・ <code>{w.name}</code></span>
                <button className="btn btn-danger" style={{ padding: '2px 8px' }} onClick={(e) => removeWorkflow(w.name, e)}>削除</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
