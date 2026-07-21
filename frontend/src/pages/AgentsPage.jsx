import { useEffect, useState } from 'react'
import { api } from '../api/client.js'
import NodeStatus from '../components/NodeStatus.jsx'

const ROLES = ['thinker', 'validator', 'executor']
const TARGETS = ['gpu_master', 'gpu_worker', 'cpu_cluster']
const TARGET_LABEL = {
  gpu_master: 'RTX 3090 (master)',
  gpu_worker: 'Intel Arc A770 (worker)',
  cpu_cluster: 'CPU クラスター',
}

const emptyDraft = {
  key: '',
  display_name: '',
  role: 'thinker',
  target: 'gpu_master',
  model: '',
  temperature: 0.7,
  max_tokens: 2048,
  enabled: true,
  system_prompt: '',
}

export default function AgentsPage() {
  const [agents, setAgents] = useState([])
  const [models, setModels] = useState([])
  const [selectedKey, setSelectedKey] = useState(null)
  const [draft, setDraft] = useState(null)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const [agentsRes, modelsRes] = await Promise.all([api.listAgents(), api.listModels()])
      setAgents(agentsRes.agents)
      setModels(modelsRes.models)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  useEffect(() => {
    if (!selectedKey) {
      setDraft(null)
      return
    }
    const agent = agents.find((a) => a.key === selectedKey)
    setDraft(agent ? { ...agent } : null)
  }, [selectedKey, agents])

  const selectAgent = (key) => {
    setCreating(false)
    setError('')
    setMessage('')
    setSelectedKey(key)
  }

  const startCreate = () => {
    setSelectedKey(null)
    setCreating(true)
    setError('')
    setMessage('')
    setDraft({ ...emptyDraft })
  }

  const updateDraft = (field, value) => setDraft((d) => ({ ...d, [field]: value }))

  const save = async () => {
    setError('')
    setMessage('')
    try {
      if (creating) {
        await api.createAgent(draft)
        setMessage(`エージェント '${draft.key}' を作成しました`)
      } else {
        const { key, ...fields } = draft
        await api.updateAgent(key, fields)
        setMessage(`エージェント '${key}' を更新しました`)
      }
      setCreating(false)
      await load()
      setSelectedKey(draft.key)
    } catch (e) {
      setError(e.message)
    }
  }

  const remove = async (key) => {
    if (!confirm(`エージェント '${key}' を削除しますか？`)) return
    setError('')
    try {
      await api.deleteAgent(key)
      setSelectedKey(null)
      setDraft(null)
      await load()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div>
      <h1>エージェント設定</h1>
      <p>各パイプライン段階のモデル・システムプロンプト・temperature を Web 画面から編集できます。保存後、次回のチャットリクエストから即座に反映されます。</p>

      {error && <div className="banner-error">{error}</div>}
      {message && <div className="banner-success">{message}</div>}

      <NodeStatus />

      <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start', marginTop: 16 }}>
        <div style={{ flex: '0 0 280px' }}>
          <div className="card" style={{ marginBottom: 12 }}>
            <button className="btn btn-primary" style={{ width: '100%' }} onClick={startCreate}>
              + 新規エージェント作成
            </button>
          </div>

          {loading ? (
            <p>読み込み中...</p>
          ) : (
            agents.map((a) => (
              <div
                key={a.key}
                className="card"
                style={{
                  marginBottom: 8,
                  cursor: 'pointer',
                  borderColor: selectedKey === a.key ? 'var(--accent)' : 'var(--border)',
                  opacity: a.enabled ? 1 : 0.6,
                }}
                onClick={() => selectAgent(a.key)}
              >
                <strong>{a.display_name || a.key}</strong>
                <div style={{ fontSize: 12 }}>
                  <code>{a.key}</code> · {a.role} · {a.model} · {TARGET_LABEL[a.target] || a.target}
                  {!a.enabled && ' · 無効'}
                </div>
              </div>
            ))
          )}
        </div>

        <div style={{ flex: 1 }}>
          {draft ? (
            <div className="card">
              <h3>{creating ? '新規エージェント' : draft.display_name || draft.key}</h3>

              {creating && (
                <div className="field">
                  <label>キー（半角英数字・アンダースコアのみ、一意）</label>
                  <input value={draft.key} onChange={(e) => updateDraft('key', e.target.value)} />
                </div>
              )}

              <div className="field">
                <label>表示名</label>
                <input value={draft.display_name} onChange={(e) => updateDraft('display_name', e.target.value)} />
              </div>

              <div style={{ display: 'flex', gap: 12 }}>
                <div className="field" style={{ flex: 1 }}>
                  <label>ロール</label>
                  <select value={draft.role} onChange={(e) => updateDraft('role', e.target.value)}>
                    {ROLES.map((r) => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </select>
                </div>
                <div className="field" style={{ flex: 1 }}>
                  <label>実行先ノード</label>
                  <select value={draft.target} onChange={(e) => updateDraft('target', e.target.value)}>
                    {TARGETS.map((t) => (
                      <option key={t} value={t}>{TARGET_LABEL[t]}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="field">
                <label>モデル</label>
                <select value={draft.model} onChange={(e) => updateDraft('model', e.target.value)}>
                  <option value="">選択してください</option>
                  {models.map((m) => (
                    <option key={m.model_name} value={m.model_name}>{m.model_name}</option>
                  ))}
                  {draft.model && !models.some((m) => m.model_name === draft.model) && (
                    <option value={draft.model}>{draft.model}</option>
                  )}
                </select>
              </div>

              <div style={{ display: 'flex', gap: 12 }}>
                <div className="field" style={{ flex: 1 }}>
                  <label>Temperature（{draft.temperature}）</label>
                  <input
                    type="range" min="0" max="2" step="0.1"
                    value={draft.temperature}
                    onChange={(e) => updateDraft('temperature', parseFloat(e.target.value))}
                  />
                </div>
                <div className="field" style={{ flex: 1 }}>
                  <label>Max Tokens</label>
                  <input
                    type="number" min="1" max="32768"
                    value={draft.max_tokens}
                    onChange={(e) => updateDraft('max_tokens', parseInt(e.target.value, 10) || 0)}
                  />
                </div>
              </div>

              <div className="field">
                <label>
                  <input
                    type="checkbox"
                    checked={draft.enabled}
                    onChange={(e) => updateDraft('enabled', e.target.checked)}
                  />
                  {' '}有効
                </label>
              </div>

              <div className="field">
                <label>システムプロンプト</label>
                <textarea
                  value={draft.system_prompt}
                  onChange={(e) => updateDraft('system_prompt', e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-primary" onClick={save}>保存</button>
                {!creating && (
                  <button className="btn btn-danger" onClick={() => remove(draft.key)}>削除</button>
                )}
              </div>
            </div>
          ) : (
            <p>左のリストからエージェントを選択するか、新規作成してください。</p>
          )}
        </div>
      </div>
    </div>
  )
}
