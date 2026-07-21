const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  const isJson = res.headers.get('content-type')?.includes('application/json')
  const body = isJson ? await res.json() : await res.text()

  if (!res.ok) {
    const detail = isJson ? body.detail ?? JSON.stringify(body) : body
    throw new Error(detail || `Request failed (${res.status})`)
  }

  return body
}

export const api = {
  // Agents
  listAgents: () => request('/agents'),
  getAgent: (key) => request(`/agents/${key}`),
  createAgent: (data) => request('/agents', { method: 'POST', body: JSON.stringify(data) }),
  updateAgent: (key, data) => request(`/agents/${key}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteAgent: (key) => request(`/agents/${key}`, { method: 'DELETE' }),
  listModels: () => request('/agents/models'),

  // Workflows
  listWorkflows: () => request('/workflows'),
  getWorkflow: (name) => request(`/workflows/${name}`),
  saveWorkflow: (name, data) => request(`/workflows/${name}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteWorkflow: (name) => request(`/workflows/${name}`, { method: 'DELETE' }),
  runWorkflow: (name, query) => request(`/workflows/${name}/run`, { method: 'POST', body: JSON.stringify({ query }) }),
}
