import * as api from "./api.js";

const $ = (sel) => document.querySelector(sel);

// Stable chat session so /history stays coherent.
const sessionId = crypto.randomUUID();

// ---------- view switching ----------
function showApp(authed) {
  $("#auth-view").classList.toggle("hidden", authed);
  $("#app-view").classList.toggle("hidden", !authed);
  $("#user-bar").classList.toggle("hidden", !authed);
  $("#user-bar").classList.toggle("flex", authed);
}

function selectTab(name) {
  document.querySelectorAll(".tab").forEach((btn) => {
    const active = btn.dataset.tab === name;
    btn.classList.toggle("bg-blue-600", active);
    btn.classList.toggle("text-white", active);
    btn.classList.toggle("bg-white", !active);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.add("hidden");
  });
  $(`#${name}-tab`).classList.remove("hidden");
  if (name === "history") loadHistory();
}

// ---------- auth ----------
let authMode = "login";

function setAuthMode(mode) {
  authMode = mode;
  document.querySelectorAll(".auth-tab").forEach((btn) => {
    const active = btn.dataset.authTab === mode;
    btn.classList.toggle("border-b-2", active);
    btn.classList.toggle("border-blue-600", active);
    btn.classList.toggle("text-slate-400", !active);
  });
  $("#auth-submit-label").textContent = mode === "login" ? "Login" : "Register";
}

async function onAuthSubmit(event) {
  event.preventDefault();
  const errorEl = $("#auth-error");
  errorEl.classList.add("hidden");
  const email = $("#auth-email").value;
  const password = $("#auth-password").value;
  try {
    if (authMode === "register") {
      await api.register(email, password);
    }
    await api.login(email, password);
    $("#user-email").textContent = email;
    showApp(true);
    selectTab("upload");
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove("hidden");
  }
}

// ---------- upload ----------
async function handleFile(file) {
  const results = $("#upload-results");
  const card = document.createElement("div");
  card.className = "border rounded-lg p-3 text-sm";
  card.innerHTML = `<div class="font-medium">${file.name}</div><div class="text-slate-500">Uploading…</div>`;
  results.prepend(card);
  try {
    const res = await api.ingest(file);
    // Requirement: surface the detected document type + chunking strategy used.
    card.innerHTML = `
      <div class="font-medium">${file.name}</div>
      <div class="mt-1 flex flex-wrap gap-2">
        <span class="px-2 py-0.5 rounded bg-slate-200">type: ${res.detected_type}</span>
        <span class="px-2 py-0.5 rounded bg-indigo-100">pipeline: ${res.pipeline}</span>
        <span class="px-2 py-0.5 rounded bg-emerald-100">strategy: ${res.strategy_used}</span>
        <span class="px-2 py-0.5 rounded bg-amber-100">chunks: ${res.chunk_count}</span>
      </div>
      <div class="text-slate-400 mt-1">job ${res.job_id}</div>`;
  } catch (err) {
    card.innerHTML = `<div class="font-medium">${file.name}</div><div class="text-red-600">${err.message}</div>`;
  }
}

function wireUpload() {
  const dropzone = $("#dropzone");
  const input = $("#file-input");
  dropzone.addEventListener("click", () => input.click());
  input.addEventListener("change", () => {
    if (input.files[0]) handleFile(input.files[0]);
    input.value = "";
  });
  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("border-blue-500");
  });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("border-blue-500"));
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("border-blue-500");
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  });
}

// ---------- chat (SSE over fetch) ----------
function addMessage(role, text) {
  const el = document.createElement("div");
  const mine = role === "user";
  el.className = `p-3 rounded-lg ${mine ? "bg-blue-50 text-right" : "bg-slate-50"}`;
  el.textContent = text;
  $("#messages").append(el);
  $("#messages").scrollTop = $("#messages").scrollHeight;
  return el;
}

async function onChatSubmit(event) {
  event.preventDefault();
  const input = $("#chat-input");
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  addMessage("user", question);
  const answerEl = addMessage("assistant", "");

  try {
    const resp = await api.query(question, sessionId);
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buffer.indexOf("\n\n")) >= 0) {
        const line = buffer.slice(0, idx).trim();
        buffer = buffer.slice(idx + 2);
        if (!line.startsWith("data:")) continue;
        const data = JSON.parse(line.slice(5).trim());
        if (data.delta) {
          answerEl.textContent += data.delta;
          $("#messages").scrollTop = $("#messages").scrollHeight;
        }
      }
    }
  } catch (err) {
    answerEl.textContent = `Error: ${err.message}`;
    answerEl.classList.add("text-red-600");
  }
}

// ---------- history ----------
async function loadHistory() {
  const list = $("#history-list");
  list.innerHTML = '<p class="text-slate-400">Loading…</p>';
  try {
    const turns = await api.getHistory(sessionId);
    if (turns.length === 0) {
      list.innerHTML = '<p class="text-slate-400">No history for this session yet.</p>';
      return;
    }
    list.innerHTML = "";
    for (const turn of turns) {
      const el = document.createElement("div");
      el.className = "border rounded-lg p-3";
      el.innerHTML = `<div class="font-medium">${turn.query}</div>
        <div class="text-slate-600 mt-1">${turn.answer}</div>
        <div class="text-xs text-slate-400 mt-1">${turn.created_at}</div>`;
      list.append(el);
    }
  } catch (err) {
    list.innerHTML = `<p class="text-red-600">${err.message}</p>`;
  }
}

// ---------- init ----------
function init() {
  document.querySelectorAll(".auth-tab").forEach((btn) =>
    btn.addEventListener("click", () => setAuthMode(btn.dataset.authTab)),
  );
  document.querySelectorAll(".tab").forEach((btn) =>
    btn.addEventListener("click", () => selectTab(btn.dataset.tab)),
  );
  $("#auth-form").addEventListener("submit", onAuthSubmit);
  $("#chat-form").addEventListener("submit", onChatSubmit);
  $("#history-refresh").addEventListener("click", loadHistory);
  $("#logout-btn").addEventListener("click", () => {
    api.clearTokens();
    showApp(false);
  });

  wireUpload();
  setAuthMode("login");
  showApp(Boolean(api.getToken()));
}

init();
