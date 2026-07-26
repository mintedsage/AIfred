// chat.js — talks only to the local FastAPI server on this machine (127.0.0.1).

const API = "";

// ---------- Tabs ----------
document.querySelectorAll(".ledger-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".ledger-tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".ledger-panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(`panel-${tab.dataset.tab}`).classList.add("active");
  });
});

// ---------- Chat ----------
const messagesEl = document.getElementById("messages");
const composer = document.getElementById("composer");
const chatInput = document.getElementById("chat-input");
const seal = document.getElementById("seal");

function addMessage(role, text) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrap.appendChild(bubble);
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function sendMessage(text) {
  if (!text) return;
  addMessage("user", text);
  chatInput.value = "";
  seal.classList.add("thinking");

  try {
    const res = await fetch(`${API}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    const reply = data.reply || "Forgive me, I did not catch that.";
    addMessage("alfred", reply);
    if (speakerOn) speakReply(reply);
  } catch (err) {
    addMessage("alfred", "I'm afraid I could not reach my own reasoning just now. Is Ollama running?");
  } finally {
    seal.classList.remove("thinking");
  }
}

composer.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = chatInput.value.trim();
  await sendMessage(text);
});

// ---------- Voice: speaker (TTS) ----------
const speakerBtn = document.getElementById("speaker-btn");
let speakerOn = false;
speakerBtn.addEventListener("click", () => {
  speakerOn = !speakerOn;
  speakerBtn.textContent = speakerOn ? "🔊" : "🔈";
  speakerBtn.classList.toggle("active", speakerOn);
});

async function speakReply(text) {
  try {
    const res = await fetch(`${API}/api/voice/speak`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.play();
    audio.onended = () => URL.revokeObjectURL(url);
  } catch (err) {
    // TTS is best-effort; silently ignore failures so chat still works.
    console.error("TTS playback failed:", err);
  }
}

// ---------- Voice: microphone (STT) ----------
// Hold the mic button to record; release to stop and transcribe.
// Recording happens via the browser's own MediaRecorder — the audio clip is
// only ever sent to this app's local server (127.0.0.1), never anywhere else.
const micBtn = document.getElementById("mic-btn");
let mediaRecorder = null;
let audioChunks = [];

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];
    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(audioChunks, { type: "audio/webm" });
      await transcribeAndSend(blob);
    };
    mediaRecorder.start();
    micBtn.classList.add("recording");
  } catch (err) {
    addMessage("alfred", "I could not access the microphone. Please check this app's permissions.");
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
  micBtn.classList.remove("recording");
}

async function transcribeAndSend(blob) {
  seal.classList.add("thinking");
  try {
    const formData = new FormData();
    formData.append("audio", blob, "clip.webm");
    const res = await fetch(`${API}/api/voice/transcribe`, { method: "POST", body: formData });
    const data = await res.json();
    const text = (data.text || "").trim();
    seal.classList.remove("thinking");
    if (text) {
      await sendMessage(text);
    } else {
      addMessage("alfred", "I'm afraid I didn't catch anything. Do try again.");
    }
  } catch (err) {
    seal.classList.remove("thinking");
    addMessage("alfred", "Transcription failed — is the voice model set up?");
  }
}

// Hold-to-talk: mouse and touch.
micBtn.addEventListener("mousedown", startRecording);
micBtn.addEventListener("mouseup", stopRecording);
micBtn.addEventListener("mouseleave", () => { if (mediaRecorder && mediaRecorder.state === "recording") stopRecording(); });
micBtn.addEventListener("touchstart", (e) => { e.preventDefault(); startRecording(); });
micBtn.addEventListener("touchend", (e) => { e.preventDefault(); stopRecording(); });

// ---------- Models ----------
async function loadModels() {
  const res = await fetch(`${API}/api/models`);
  const data = await res.json();
  const picker = document.getElementById("model-picker");
  picker.innerHTML = "";
  data.models.forEach((m) => {
    const opt = document.createElement("option");
    opt.value = m;
    opt.textContent = m;
    if (m === data.current) opt.selected = true;
    picker.appendChild(opt);
  });
}
document.getElementById("model-picker").addEventListener("change", async (e) => {
  await fetch(`${API}/api/models`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: e.target.value }),
  });
});

// ---------- Memory ----------
async function loadMemories() {
  const res = await fetch(`${API}/api/memories`);
  const data = await res.json();
  const list = document.getElementById("mem-list");
  list.innerHTML = "";
  data.memories.forEach((m) => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `<div class="meta">${m.category} · importance ${m.importance}</div>${escapeHtml(m.content)}
      <button class="remove" data-id="${m.id}">✕</button>`;
    card.querySelector(".remove").addEventListener("click", async () => {
      await fetch(`${API}/api/memories/${m.id}`, { method: "DELETE" });
      loadMemories();
    });
    list.appendChild(card);
  });
}
document.getElementById("mem-add-btn").addEventListener("click", async () => {
  const input = document.getElementById("mem-input");
  if (!input.value.trim()) return;
  await fetch(`${API}/api/memories`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content: input.value.trim() }),
  });
  input.value = "";
  loadMemories();
});

// ---------- Tasks ----------
async function loadTasks() {
  const res = await fetch(`${API}/api/tasks`);
  const data = await res.json();
  const list = document.getElementById("task-list");
  list.innerHTML = "";
  data.tasks.forEach((t) => {
    const card = document.createElement("div");
    card.className = "card" + (t.done ? " done" : "");
    card.innerHTML = `${escapeHtml(t.content)}
      <button class="remove" data-id="${t.id}">✓</button>`;
    card.querySelector(".remove").addEventListener("click", async () => {
      await fetch(`${API}/api/tasks/${t.id}/complete`, { method: "POST" });
      loadTasks();
    });
    list.appendChild(card);
  });
}
document.getElementById("task-add-btn").addEventListener("click", async () => {
  const input = document.getElementById("task-input");
  if (!input.value.trim()) return;
  await fetch(`${API}/api/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content: input.value.trim() }),
  });
  input.value = "";
  loadTasks();
});

// ---------- Notes ----------
async function loadNotes() {
  const res = await fetch(`${API}/api/notes`);
  const data = await res.json();
  const list = document.getElementById("note-list");
  list.innerHTML = "";
  data.notes.forEach((n) => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = escapeHtml(n.content);
    list.appendChild(card);
  });
}
document.getElementById("note-add-btn").addEventListener("click", async () => {
  const input = document.getElementById("note-input");
  if (!input.value.trim()) return;
  await fetch(`${API}/api/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content: input.value.trim() }),
  });
  input.value = "";
  loadNotes();
});

// ---------- Files ----------
async function loadFiles() {
  const res = await fetch(`${API}/api/documents`);
  const data = await res.json();
  const list = document.getElementById("file-list");
  list.innerHTML = "";
  data.sources.forEach((path) => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `${escapeHtml(path.split("/").pop())}<div class="meta">${escapeHtml(path)}</div>`;
    list.appendChild(card);
  });
}
document.getElementById("file-add-btn").addEventListener("click", async () => {
  const input = document.getElementById("file-input");
  if (!input.value.trim()) return;
  const res = await fetch(`${API}/api/documents/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: input.value.trim() }),
  });
  if (res.ok) {
    input.value = "";
    loadFiles();
  } else {
    alert("Alfred could not find that file. Please check the path.");
  }
});

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

loadModels();
loadMemories();
loadTasks();
loadNotes();
loadFiles();
