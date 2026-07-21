import { useEffect, useState } from 'react'
import { api } from '../api/client.js'

const TARGET_LABEL = {
  gpu_master: 'RTX 3090 (master)',
  gpu_worker: 'Intel Arc A770 (worker)',
  cpu_cluster: 'CPU クラスター',
}

export default function NodeStatus() {
  const [nodes, setNodes] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      setNodes(await api.listNodes())
    } catch {
      setNodes(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0 }}>ノード状態</h3>
        <button className="btn" onClick={load} disabled={loading}>{loading ? '確認中...' : '再確認'}</button>
      </div>
      <div style={{ display: 'flex', gap: 24, marginTop: 12, flexWrap: 'wrap' }}>
        {nodes && Object.entries(TARGET_LABEL).map(([target, label]) => {
          const list = nodes[target] || []
          return (
            <div key={target} style={{ fontSize: 13 }}>
              <strong>{label}</strong>
              {list.length === 0 ? (
                <div style={{ opacity: 0.6 }}>未設定</div>
              ) : (
                list.map((n) => (
                  <div key={n.url}>
                    <span style={{ color: n.status === 'up' ? '#1c8a4b' : 'var(--danger)' }}>●</span> {n.url}
                  </div>
                ))
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
