// Thin client for the api-gateway. The frontend talks ONLY to the gateway.
const API_BASE = window.RAG_API_BASE ?? "http://localhost:8080";

const TOKEN_KEY = "rag_access_token";
const REFRESH_KEY = "rag_refresh_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setTokens({ access_token, refresh_token }) {
  if (access_token) localStorage.setItem(TOKEN_KEY, access_token);
  if (refresh_token) localStorage.setItem(REFRESH_KEY, refresh_token);
}

export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

function authHeaders(extra = {}) {
  const headers = { ...extra };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

async function asError(resp) {
  let detail = `HTTP ${resp.status}`;
  try {
    const body = await resp.json();
    if (body.detail) detail = body.detail;
  } catch {
    /* non-JSON body */
  }
  return new Error(detail);
}

export async function register(email, password) {
  const resp = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!resp.ok) throw await asError(resp);
}

export async function login(email, password) {
  const resp = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!resp.ok) throw await asError(resp);
  setTokens(await resp.json());
}

export async function ingest(file) {
  const form = new FormData();
  form.append("file", file);
  const resp = await fetch(`${API_BASE}/ingest`, {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  if (!resp.ok) throw await asError(resp);
  return resp.json();
}

// Returns the raw Response so the caller can read the SSE stream.
export async function query(question, sessionId) {
  const resp = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ query: question, session_id: sessionId }),
  });
  if (!resp.ok) throw await asError(resp);
  return resp;
}

export async function getHistory(sessionId) {
  const resp = await fetch(`${API_BASE}/history/${sessionId}`, {
    headers: authHeaders(),
  });
  if (!resp.ok) throw await asError(resp);
  return resp.json();
}
