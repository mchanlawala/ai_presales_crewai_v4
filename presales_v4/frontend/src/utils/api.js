const BASE = (window._env_?.REACT_APP_API_URL) || 'http://localhost:8000/api';
const WS   = BASE.replace(/^http/, 'ws').replace('/api', '/api');

const req = async (method, path, body) => {
  const r = await fetch(`${BASE}${path}`, {
    method,
    headers: {'Content-Type':'application/json'},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) {
    const e = await r.json().catch(() => ({detail: r.statusText}));
    throw new Error(e.detail || 'Request failed');
  }
  return r.json();
};

export const api = {
  start:         (query, hint)    => req('POST', '/sessions/start', {query, industry_hint: hint}),
  getSession:    (id)             => req('GET',  `/sessions/${id}`),
  listSessions:  ()               => req('GET',  '/sessions'),
  answer:        (id, answers)    => req('POST', `/sessions/${id}/answer`, {session_id:id, answers}),
  skip:          (id)             => req('POST', `/sessions/${id}/skip-questions`),
  review:        (id, dec, comments, feedback) =>
    req('POST', `/sessions/${id}/review`, {session_id:id, decision:dec, comments, document_feedback:feedback}),
  approveDoc:    (id, docId, fb)  => req('POST', `/sessions/${id}/approve-document?doc_id=${docId}&feedback=${encodeURIComponent(fb||'')}`, {}),
  publish:       (id)             => req('POST', `/sessions/${id}/publish`),
  industries:    ()               => req('GET',  '/industries'),
  createKB:      (industry, content, desc) => req('POST', '/knowledge-base', {industry, content, description:desc}),
  getKB:         (industry)       => req('GET',  `/knowledge-base/${encodeURIComponent(industry)}`),
  downloadUrl:   (id)             => `${BASE}/sessions/${id}/download`,
  docUrl:        (id, docId)      => `${BASE}/sessions/${id}/document/${docId}`,
  previewUrl:    (id, docId)      => `${BASE}/sessions/${id}/preview/${docId}`,
  ws:            (id)             => new WebSocket(`${WS}/ws/${id}`),
};
export default api;
