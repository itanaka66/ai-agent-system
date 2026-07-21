import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ReactFlow, { Background, Controls, useNodesState } from 'reactflow'
import 'reactflow/dist/style.css'
import { api } from '../api/client.js'

const RUNNABLE_TYPES = ['THINKER_AGENT', 'VALIDATOR_AGENT', 'EXECUTOR_AGENT']
const TARGETS = ['gpu_master', 'gpu_worker', 'cpu_cluster']
const TARGET_LABEL = {
  gpu_master: 'RTX 3090 (master)',
  gpu_worker: 'Intel Arc A770 (worker)',
  cpu_cluster: 'CPU クラスター',
}

const TYPE_COLOR = {
  START_NODE: '#2f9e5b',
  THINKER_AGENT: '#aa3bff',
  VALIDATOR_AGENT: '#e08a1e',
  EXECUTOR_AGENT: '#1e8fe0',
  END_NODE: '#6b7280',
}

const nodeLabel = (id, type) => (
  <div>
    <div style={{ fontSize: 10, opacity: 0.8 }}>{type}</div>
    <div style={{ fontWeight: 600 }}>{id}</div>
  </div>
)

const nodeStyle = (type) => ({
  border: `2px solid ${TYPE_COLOR[type] || '#888'}`,
  borderRadius: 8,
  padding: 8,
  background: 'var(--bg)',
  color: 'var(--text-h)',
  minWidth: 160,
})

const makeRfNode = (schemaNode) => ({
  id: schemaNode.id,
  position: { x: schemaNode.position[0], y: schemaNode.position[1] },
  data: { label: nodeLabel(schemaNode.id, schemaNode.type) },
  style: nodeStyle(schemaNode.type),
})

const csvToList = (csv, key) =>
  csv.split(',').map((s) => s.trim()).filter(Boolean).map((n) => ({ [key]: n }))

const listToCsv = (list, key) => (list || []).map((i) => i[key]).join(', ')

export default function WorkflowBuilderPage() {
  const { name } = useParams()
  const navigate = useNavigate()

  const [description, setDescription] = useState('')
  // Business data keyed by node id: type, inputs, outputs, systemPrompt, agentKey, model/target/temperature overrides
  const [nodeData, setNodeData] = useState({})
  const [nodes, setNodes, onNodesChangeBase] = useNodesState([])
  const [agents, setAgents] = useState([])
  const [selectedNodeId, setSelectedNodeId] = useState(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)

  const [testQuery, setTestQuery] = useState('')
  const [testRunning, setTestRunning] = useState(false)
  const [testResult, setTestResult] = useState(null)
  const [testError, setTestError] = useState('')

  useEffect(() => {
    (async () => {
      setLoading(true)
      setError('')
      try {
        const [wf, agentsRes] = await Promise.all([api.getWorkflow(name), api.listAgents()])
        setDescription(wf.description || '')

        const dataMap = {}
        for (const n of wf.nodes || []) {
          dataMap[n.id] = {
            id: n.id,
            type: n.type,
            inputs: n.inputs || [],
            outputs: n.outputs || [],
            systemPrompt: n.systemPrompt || '',
            agentKey: n.agentKey,
            target: n.target,
            model: n.model,
          }
        }
        setNodeData(dataMap)
        setNodes((wf.nodes || []).map(makeRfNode))
        setAgents(agentsRes.agents)
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [name])

  const edges = useMemo(() => {
    const list = Object.values(nodeData)
    const result = []
    for (const target of list) {
      for (const inp of target.inputs || []) {
        for (const source of list) {
          if (source.id === target.id) continue
          if ((source.outputs || []).some((o) => o.output === inp.input)) {
            result.push({
              id: `${source.id}->${target.id}:${inp.input}`,
              source: source.id,
              target: target.id,
              label: inp.input,
              animated: true,
            })
          }
        }
      }
    }
    return result
  }, [nodeData])

  const onNodesChange = useCallback((changes) => onNodesChangeBase(changes), [onNodesChangeBase])

  const selectedNode = selectedNodeId ? nodeData[selectedNodeId] : null

  const patchNodeData = (id, patch) => {
    setNodeData((current) => ({ ...current, [id]: { ...current[id], ...patch } }))

    if (patch.type) {
      setNodes((nds) =>
        nds.map((n) =>
          n.id === id
            ? { ...n, data: { label: nodeLabel(id, patch.type) }, style: nodeStyle(patch.type) }
            : n
        )
      )
    }
  }

  const addNode = (type) => {
    const id = `${type.toLowerCase()}_${Date.now().toString(36)}`
    const schemaNode = {
      id, type,
      position: [300 + Math.random() * 200, 300 + Math.random() * 200],
      inputs: [], outputs: [{ output: `${id}_out` }], systemPrompt: '',
    }
    setNodeData((current) => ({ ...current, [id]: schemaNode }))
    setNodes((nds) => [...nds, makeRfNode(schemaNode)])
    setSelectedNodeId(id)
  }

  const deleteSelectedNode = () => {
    if (!selectedNode || selectedNode.type === 'START_NODE' || selectedNode.type === 'END_NODE') return
    const id = selectedNodeId
    setNodeData((current) => {
      const next = { ...current }
      delete next[id]
      return next
    })
    setNodes((nds) => nds.filter((n) => n.id !== id))
    setSelectedNodeId(null)
  }

  const save = async () => {
    setError('')
    setMessage('')
    try {
      const payloadNodes = Object.values(nodeData).map((nd) => {
        const rfNode = nodes.find((n) => n.id === nd.id)
        const position = rfNode ? [rfNode.position.x, rfNode.position.y] : [0, 0]
        const node = {
          id: nd.id,
          type: nd.type,
          position,
          inputs: nd.inputs || [],
          outputs: nd.outputs || [],
        }
        if (nd.systemPrompt) node.systemPrompt = nd.systemPrompt
        if (nd.agentKey) node.agentKey = nd.agentKey
        if (nd.target) node.target = nd.target
        if (nd.model) node.model = nd.model
        return node
      })
      await api.saveWorkflow(name, { name, description, nodes: payloadNodes })
      setMessage('ワークフローを保存しました')
    } catch (e) {
      setError(e.message)
    }
  }

  const runTest = async () => {
    setTestRunning(true)
    setTestError('')
    setTestResult(null)
    try {
      const result = await api.runWorkflow(name, testQuery)
      setTestResult(result)
    } catch (e) {
      setTestError(e.message)
    } finally {
      setTestRunning(false)
    }
  }

  if (loading) return <p>読み込み中...</p>

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <button className="btn" onClick={() => navigate('/workflows')}>← 一覧に戻る</button>
          <h1 style={{ display: 'inline', marginLeft: 12 }}>{name}</h1>
        </div>
        <button className="btn btn-primary" onClick={save}>保存</button>
      </div>

      {error && <div className="banner-error">{error}</div>}
      {message && <div className="banner-success">{message}</div>}

      <div className="field" style={{ maxWidth: 480 }}>
        <label>説明</label>
        <input value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>

      <div style={{ display: 'flex', gap: 8, margin: '12px 0' }}>
        {RUNNABLE_TYPES.map((t) => (
          <button key={t} className="btn" onClick={() => addNode(t)}>+ {t}</button>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 16 }}>
        <div style={{ flex: 1, height: 480, border: '1px solid var(--border)', borderRadius: 10 }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onNodeClick={(_, node) => setSelectedNodeId(node.id)}
            onPaneClick={() => setSelectedNodeId(null)}
            fitView
          >
            <Background />
            <Controls />
          </ReactFlow>
        </div>

        <div style={{ flex: '0 0 320px' }}>
          {selectedNode ? (
            <div className="card">
              <h3>{selectedNode.id}</h3>
              <div className="field">
                <label>タイプ</label>
                {selectedNode.type === 'START_NODE' || selectedNode.type === 'END_NODE' ? (
                  <input value={selectedNode.type} disabled />
                ) : (
                  <select
                    value={selectedNode.type}
                    onChange={(e) => patchNodeData(selectedNodeId, { type: e.target.value })}
                  >
                    {RUNNABLE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                )}
              </div>

              <div className="field">
                <label>入力変数（カンマ区切り）</label>
                <input
                  value={listToCsv(selectedNode.inputs, 'input')}
                  onChange={(e) => patchNodeData(selectedNodeId, { inputs: csvToList(e.target.value, 'input') })}
                />
              </div>

              <div className="field">
                <label>出力変数（カンマ区切り、通常は1つ）</label>
                <input
                  value={listToCsv(selectedNode.outputs, 'output')}
                  onChange={(e) => patchNodeData(selectedNodeId, { outputs: csvToList(e.target.value, 'output') })}
                />
              </div>

              {RUNNABLE_TYPES.includes(selectedNode.type) && (
                <>
                  <div className="field">
                    <label>既存エージェント設定を継承（任意）</label>
                    <select
                      value={selectedNode.agentKey || ''}
                      onChange={(e) => patchNodeData(selectedNodeId, { agentKey: e.target.value || undefined })}
                    >
                      <option value="">（なし・下記を個別指定）</option>
                      {agents.map((a) => (
                        <option key={a.key} value={a.key}>{a.display_name || a.key}</option>
                      ))}
                    </select>
                  </div>

                  <div className="field">
                    <label>システムプロンプト（未指定時は継承元を使用）</label>
                    <textarea
                      value={selectedNode.systemPrompt || ''}
                      onChange={(e) => patchNodeData(selectedNodeId, { systemPrompt: e.target.value })}
                    />
                  </div>

                  <div className="field">
                    <label>実行先ノード（個別指定、未指定時は継承元 or 既定値）</label>
                    <select
                      value={selectedNode.target || ''}
                      onChange={(e) => patchNodeData(selectedNodeId, { target: e.target.value || undefined })}
                    >
                      <option value="">（継承 / 既定値）</option>
                      {TARGETS.map((t) => (
                        <option key={t} value={t}>{TARGET_LABEL[t]}</option>
                      ))}
                    </select>
                  </div>

                  <div className="field">
                    <label>モデル（個別指定、任意）</label>
                    <input
                      value={selectedNode.model || ''}
                      onChange={(e) => patchNodeData(selectedNodeId, { model: e.target.value || undefined })}
                      placeholder="例: llama3:8b（未指定時は継承元 or 既定値）"
                    />
                  </div>
                </>
              )}

              <button
                className="btn btn-danger"
                disabled={selectedNode.type === 'START_NODE' || selectedNode.type === 'END_NODE'}
                onClick={deleteSelectedNode}
              >
                ノードを削除
              </button>
            </div>
          ) : (
            <div className="card">ノードをクリックすると編集できます。</div>
          )}

          <div className="card" style={{ marginTop: 16 }}>
            <h3>テスト実行</h3>
            <div className="field">
              <label>質問</label>
              <input value={testQuery} onChange={(e) => setTestQuery(e.target.value)} placeholder="テスト用の質問を入力" />
            </div>
            <button className="btn btn-primary" onClick={runTest} disabled={testRunning || !testQuery}>
              {testRunning ? '実行中...' : '実行'}
            </button>
            <p style={{ fontSize: 12, marginTop: 8 }}>※ Ollama ノードに実際に接続できる環境でのみ動作します。</p>

            {testError && <div className="banner-error" style={{ marginTop: 12 }}>{testError}</div>}
            {testResult && (
              <div style={{ marginTop: 12, fontSize: 13 }}>
                <strong>回答:</strong>
                <p>{testResult.answer}</p>
                {testResult.validation && (
                  <p><strong>検証スコア:</strong> {JSON.stringify(testResult.validation)}</p>
                )}
                <details>
                  <summary>実行トレース</summary>
                  <pre style={{ whiteSpace: 'pre-wrap', fontSize: 11 }}>{JSON.stringify(testResult.trace, null, 2)}</pre>
                </details>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
