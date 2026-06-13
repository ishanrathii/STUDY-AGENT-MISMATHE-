// MISMATHE — chat frontend
'use strict';

const $ = (id) => document.getElementById(id);
const messagesEl = $('messages');
const statusEl = $('status');
const composerEl = $('composer');
const inputEl = $('input');
const sendBtn = $('sendBtn');

let state = {
  modes: [],
  mentorMode: 'friend',
  onboardingCompleted: false,
  syllabus: { subjects: [], chapters: {}, priority: {} },
};

// ----- API helpers -----
async function api(path, opts = {}) {
  const init = { credentials: 'include', headers: { 'Content-Type': 'application/json' }, ...opts };
  if (init.body && typeof init.body !== 'string') {
    init.body = JSON.stringify(init.body);
  }
  const res = await fetch(path, init);
  if (!res.ok) {
    let detail = '';
    try { detail = (await res.json()).detail || ''; } catch {}
    throw new Error(`${res.status} ${detail || res.statusText}`);
  }
  return res.json();
}

// ----- Render -----
function addMessage(role, text) {
  const wrap = document.createElement('div');
  wrap.className = `msg ${role}`;
  const who = document.createElement('div');
  who.className = 'who';
  who.textContent = role === 'user' ? 'You' : 'MISMATHE';
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;
  wrap.appendChild(who);
  wrap.appendChild(bubble);
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showTyping() {
  const wrap = document.createElement('div');
  wrap.className = 'msg assistant';
  wrap.id = 'typingIndicator';
  const who = document.createElement('div');
  who.className = 'who';
  who.textContent = 'MISMATHE';
  const bubble = document.createElement('div');
  bubble.className = 'bubble typing';
  bubble.innerHTML = '<span></span><span></span><span></span>';
  wrap.appendChild(who);
  wrap.appendChild(bubble);
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function hideTyping() {
  const t = $('typingIndicator');
  if (t) t.remove();
}

function setStatus(text, cls = '') {
  statusEl.textContent = text;
  statusEl.className = `status ${cls}`;
}

// ----- Init -----
async function loadState() {
  setStatus('connecting…');
  try {
    const [data, syllabus] = await Promise.all([
      api('/api/state'),
      api('/api/syllabus'),
    ]);
    state.modes = data.modes || [];
    state.mentorMode = data.mentor_mode;
    state.onboardingCompleted = data.onboarding_completed;
    state.syllabus = syllabus;
    $('streakValue').textContent = data.streak_days ?? 0;
    $('modeValue').textContent = data.mentor_mode;
    renderModes();
    renderSubjects();
    if (data.intro) {
      addMessage('assistant', data.intro);
    }
    setStatus('online', 'ok');
  } catch (err) {
    setStatus(`offline — ${err.message}`, 'error');
  }
}

function renderSubjects() {
  const subjSel = $('testSubject');
  const chapSel = $('testChapter');
  subjSel.innerHTML = '<option value="">Pick subject…</option>';
  state.syllabus.subjects.forEach((s) => {
    const opt = document.createElement('option');
    opt.value = s;
    opt.textContent = s;
    subjSel.appendChild(opt);
  });

  const repopulateChapters = () => {
    const subject = subjSel.value;
    chapSel.innerHTML = '<option value="">Any chapter (mock)</option>';
    if (!subject) return;
    const chapters = state.syllabus.chapters[subject] || [];
    const priority = new Set(state.syllabus.priority[subject] || []);
    chapters.forEach((c) => {
      const opt = document.createElement('option');
      opt.value = c.name;
      const star = priority.has(c.name) ? ' ⭐' : '';
      opt.textContent = `${c.name} (${c.marks}/${c.marks_with_option})${star}`;
      chapSel.appendChild(opt);
    });
  };

  subjSel.addEventListener('change', repopulateChapters);
}

function renderModes() {
  const grid = $('modeGrid');
  grid.innerHTML = '';
  state.modes.forEach((m) => {
    const btn = document.createElement('button');
    btn.textContent = `${m.emoji} ${m.label}`;
    btn.title = m.description;
    btn.dataset.mode = m.key;
    if (m.key === state.mentorMode) btn.classList.add('active');
    btn.addEventListener('click', () => switchMode(m.key));
    grid.appendChild(btn);
  });
}

async function switchMode(key) {
  try {
    const data = await api('/api/mode', { method: 'POST', body: { mode: key } });
    state.mentorMode = data.mode;
    $('modeValue').textContent = data.mode;
    renderModes();
    addMessage('assistant', `${data.emoji} Switched to ${data.label} Mode — ${data.description}`);
  } catch (err) {
    addMessage('assistant', `Couldn't switch mode: ${err.message}`);
  }
}

// ----- Chat -----
async function sendChat(text) {
  if (!text.trim()) return;
  addMessage('user', text);
  inputEl.value = '';
  inputEl.style.height = 'auto';
  sendBtn.disabled = true;
  showTyping();
  setStatus('thinking…', 'busy');
  try {
    const data = await api('/api/chat', { method: 'POST', body: { message: text } });
    hideTyping();
    addMessage('assistant', data.reply);
    if (data.onboarding === false && !state.onboardingCompleted) {
      state.onboardingCompleted = true;
    }
    setStatus('online', 'ok');
  } catch (err) {
    hideTyping();
    addMessage('assistant', `⚠️ ${err.message}`);
    setStatus('error', 'error');
  } finally {
    sendBtn.disabled = false;
    inputEl.focus();
  }
}

composerEl.addEventListener('submit', (e) => {
  e.preventDefault();
  sendChat(inputEl.value);
});

inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChat(inputEl.value);
  }
});

inputEl.addEventListener('input', () => {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 140) + 'px';
});

// ----- Quick actions -----
document.querySelectorAll('button.quick').forEach((btn) => {
  btn.addEventListener('click', async () => {
    const action = btn.dataset.action;
    sendBtn.disabled = true;
    setStatus('thinking…', 'busy');
    showTyping();
    try {
      const path = action === 'dashboard' ? '/api/dashboard' : `/api/${action}`;
      const method = action === 'dashboard' ? 'GET' : 'POST';
      const data = await api(path, { method });
      hideTyping();
      addMessage('assistant', data.reply);
      setStatus('online', 'ok');
    } catch (err) {
      hideTyping();
      addMessage('assistant', `⚠️ ${err.message}`);
      setStatus('error', 'error');
    } finally {
      sendBtn.disabled = false;
    }
  });
});

// ----- Stopwatch -----
$('swStart').addEventListener('click', async () => {
  const subject = $('swSubject').value.trim() || null;
  const chapter = $('swChapter').value.trim() || null;
  try {
    await api('/api/study/start', { method: 'POST', body: { subject, chapter } });
    $('swActive').classList.remove('hidden');
    $('swActive').textContent = `⏱ Studying${subject ? ' ' + subject : ''}${chapter ? ' → ' + chapter : ''}…`;
    $('swStart').classList.add('hidden');
    $('swStop').classList.remove('hidden');
  } catch (err) {
    addMessage('assistant', `⚠️ ${err.message}`);
  }
});

$('swStop').addEventListener('click', async () => {
  try {
    const data = await api('/api/study/stop', { method: 'POST' });
    $('swActive').classList.add('hidden');
    $('swStart').classList.remove('hidden');
    $('swStop').classList.add('hidden');
    if (data.active) {
      addMessage('assistant', `✅ Logged ${data.duration_minutes} min on ${data.subject || 'study'}${data.chapter ? ' → ' + data.chapter : ''}.`);
    }
  } catch (err) {
    addMessage('assistant', `⚠️ ${err.message}`);
  }
});

// ----- Test generation -----
$('testGen').addEventListener('click', async () => {
  const subject = $('testSubject').value;
  if (!subject) {
    addMessage('assistant', 'Pick a subject first.');
    return;
  }
  const chapter = $('testChapter').value || null;
  const difficulty = $('testDifficulty').value;
  $('testGen').disabled = true;
  setStatus('generating…', 'busy');
  showTyping();
  try {
    const data = await api('/api/test', { method: 'POST', body: { subject, chapter, difficulty, count: 10 } });
    hideTyping();
    addMessage('assistant', data.reply);
    setStatus('online', 'ok');
  } catch (err) {
    hideTyping();
    addMessage('assistant', `⚠️ ${err.message}`);
    setStatus('error', 'error');
  } finally {
    $('testGen').disabled = false;
  }
});

// ----- Sync -----
$('syncBtn').addEventListener('click', async () => {
  $('syncBtn').disabled = true;
  $('syncBtn').textContent = '📤 Syncing…';
  try {
    const data = await api('/api/sync', { method: 'POST' });
    addMessage('assistant', data.ok
      ? '✅ Memory synced to GitHub. Your progress is safe.'
      : '⚠️ Snapshots saved locally — GitHub push failed.');
  } catch (err) {
    addMessage('assistant', `⚠️ ${err.message}`);
  } finally {
    $('syncBtn').disabled = false;
    $('syncBtn').textContent = '📤 Sync memory to GitHub';
  }
});

// ----- Boot -----
loadState();
inputEl.focus();
