import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client.js'

const TYPE_LABEL = {
  chat: 'チャット',
  workflow: 'ワークフロー',
}

const STATUS_LABEL = {
  queued: '待機中',
  running: '処理中',
  done: '完了',
  error: 'エラー',
}

const STATUS_COLOR = {
  queued: 'var(--text)',
  running: 'var(--accent)',
  done: '#1c8a4b',
  error: 'var(--danger)',
}

const POLL_INTERVAL_MS = 1500

export default function QueueStatus() {
  const [jobs, setJobs] = useState([])
  const [error, setError] = useState(null)
  const timerRef = useRef(null)

  const load = async () => {
    try {
      const res = await api.listQueue()
      setJobs(res.jobs || [])
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }

  useEffect(() => {
    load()
    timerRef.current = setInterval(load, POLL_INTERVAL_MS)
    return () => clearInterval(timerRef.current)
  }, [])

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0 }}>LLM 処理キュー</h3>
        <span style={{ fontSize: 12, opacity: 0.6 }}>{jobs.length}件</span>
      </div>

      {error && <div style={{ color: 'var(--danger)', fontSize: 13, marginTop: 8 }}>{error}</div>}

      {!error && jobs.length === 0 && (
        <div style={{ opacity: 0.6, fontSize: 13, marginTop: 8 }}>キューは空です</div>
      )}

      <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
        {jobs.map((job) => (
          <div key={job.id} style={{ fontSize: 13 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span>
                <span style={{ opacity: 0.6 }}>[{TYPE_LABEL[job.type] || job.type}]</span> {job.label}
              </span>
              <span style={{ color: STATUS_COLOR[job.status], whiteSpace: 'nowrap', marginLeft: 8 }}>
                {STATUS_LABEL[job.status] || job.status} ({job.progress}%)
              </span>
            </div>
            <div
              style={{
                height: 6,
                borderRadius: 3,
                background: 'var(--bg-alt)',
                border: '1px solid var(--border)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  height: '100%',
                  width: `${job.progress}%`,
                  background: STATUS_COLOR[job.status],
                  transition: 'width 0.3s ease',
                }}
              />
            </div>
            <div style={{ opacity: 0.6, fontSize: 11, marginTop: 2 }}>
              {job.model} @ {job.target} ・ {job.elapsed_seconds}s / 推定{job.estimated_seconds}s
              {job.error ? ` ・ ${job.error}` : ''}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
