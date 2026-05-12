'use strict';

/* ══════════════════════════════════════════════════════════
   ACTIVITY LEVELS (mirrors Python engines/computation.py)
   ══════════════════════════════════════════════════════════ */
const ACTIVITY_LEVELS = [
  { label: 'Sedentary',         desc: 'Little or no exercise' },
  { label: 'Lightly Active',    desc: 'Light exercise 1–3 days/week' },
  { label: 'Moderately Active', desc: 'Moderate exercise 3–5 days/week' },
  { label: 'Very Active',       desc: 'Hard exercise 6–7 days/week' },
  { label: 'Extra Active',      desc: 'Very hard exercise + physical job' },
];

/* ══════════════════════════════════════════════════════════
   SEARCH TAG INPUT
   ══════════════════════════════════════════════════════════ */
class SearchTagInput {
  constructor({ inputId, dropdownId, tagsId, database, allowCustom = false }) {
    this.input     = document.getElementById(inputId);
    this.dropdown  = document.getElementById(dropdownId);
    this.tagsEl    = document.getElementById(tagsId);
    this.database  = database;
    this.allowCustom = allowCustom;
    this._tags     = [];
    this._focusIdx = -1;
    this._init();
  }

  _search(q) {
    const ql = q.toLowerCase();
    const out = [];
    for (const item of this.database) {
      if (item.toLowerCase().includes(ql)) { out.push(item); if (out.length >= 10) break; }
    }
    return out;
  }

  _showDropdown(results) {
    this._focusIdx = -1;
    this.dropdown.innerHTML = '';
    if (!results.length) {
      if (this.allowCustom && this.input.value.trim()) {
        const val = this.input.value.trim();
        const el = this._makeOpt(`Add "${val}"`, val);
        this.dropdown.appendChild(el);
      } else {
        this.dropdown.innerHTML = '<div class="sti-empty">No matches</div>';
      }
    } else {
      results.forEach(r => this.dropdown.appendChild(this._makeOpt(r, r)));
    }
    this.dropdown.classList.remove('hidden');
  }

  _makeOpt(text, val) {
    const el = document.createElement('div');
    el.className = 'sti-option'; el.dataset.val = val;
    el.textContent = text;
    el.addEventListener('mousedown', e => { e.preventDefault(); this.addTag(val); });
    return el;
  }

  _hideDropdown() { this.dropdown.classList.add('hidden'); this._focusIdx = -1; }

  _init() {
    this.input.addEventListener('input', () => {
      const q = this.input.value.trim();
      if (!q) { this._hideDropdown(); return; }
      this._showDropdown(this._search(q));
    });
    this.input.addEventListener('keydown', e => {
      const opts = [...this.dropdown.querySelectorAll('.sti-option')];
      if (e.key === 'ArrowDown') { e.preventDefault(); this._focusIdx = Math.min(this._focusIdx + 1, opts.length - 1); opts.forEach((o, i) => o.classList.toggle('focused', i === this._focusIdx)); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); this._focusIdx = Math.max(this._focusIdx - 1, 0); opts.forEach((o, i) => o.classList.toggle('focused', i === this._focusIdx)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (this._focusIdx >= 0 && opts[this._focusIdx]) this.addTag(opts[this._focusIdx].dataset.val); else if (this.allowCustom && this.input.value.trim()) this.addTag(this.input.value.trim()); }
      else if (e.key === 'Escape') this._hideDropdown();
    });
    document.addEventListener('click', e => { if (!this.input.closest('.sti-wrap').contains(e.target)) this._hideDropdown(); });
  }

  addTag(value) {
    if (!value || this._tags.includes(value)) { this.input.value = ''; this._hideDropdown(); return; }
    this._tags.push(value);
    this._renderTags(); this.input.value = ''; this._hideDropdown();
  }

  removeTag(value) { this._tags = this._tags.filter(t => t !== value); this._renderTags(); }

  _renderTags() {
    this.tagsEl.innerHTML = '';
    this._tags.forEach(tag => {
      const pill = document.createElement('div');
      pill.className = 'tag-pill';
      pill.innerHTML = `<span>${tag}</span><button class="tag-pill-x">×</button>`;
      pill.querySelector('.tag-pill-x').addEventListener('click', () => this.removeTag(tag));
      this.tagsEl.appendChild(pill);
    });
  }

  getTags()  { return [...this._tags]; }
  reset()    { this._tags = []; this._renderTags(); this._hideDropdown(); this.input.value = ''; }
}

/* ══════════════════════════════════════════════════════════
   INJURY ROWS
   ══════════════════════════════════════════════════════════ */
const InjuryManager = (() => {
  const rowsEl = document.getElementById('injuryRows');
  const addBtn = document.getElementById('injuryAddBtn');
  const D = window.AHAA_DATA || {};

  function addRow() {
    const row = document.createElement('div');
    row.className = 'injury-row';
    row.innerHTML = `
      <input class="input injury-organ" type="text" placeholder="Body part (e.g. knee)" list="bodyPartsList" />
      <input class="input injury-type"  type="text" placeholder="Type (e.g. sprain)"    list="injuryTypesList" />
      <button class="injury-del">×</button>
    `;
    row.querySelector('.injury-del').addEventListener('click', () => row.remove());
    rowsEl.appendChild(row);
  }

  function collect() {
    return Array.from(rowsEl.querySelectorAll('.injury-row')).map(r => {
      const a = r.querySelector('.injury-organ').value.trim();
      const b = r.querySelector('.injury-type').value.trim();
      return `${a} ${b}`.trim();
    }).filter(Boolean);
  }

  function reset() { rowsEl.innerHTML = ''; }

  function injectLists() {
    if (!D.BODY_PARTS) return;
    ['bodyPartsList', 'injuryTypesList'].forEach(id => { if (!document.getElementById(id)) { const dl = document.createElement('datalist'); dl.id = id; document.body.appendChild(dl); }});
    D.BODY_PARTS.forEach(p => { const o = document.createElement('option'); o.value = p; document.getElementById('bodyPartsList').appendChild(o); });
    D.INJURY_TYPES.forEach(t => { const o = document.createElement('option'); o.value = t; document.getElementById('injuryTypesList').appendChild(o); });
  }

  addBtn.addEventListener('click', addRow);
  return { collect, reset, injectLists };
})();

/* ══════════════════════════════════════════════════════════
   MARKDOWN RENDERER
   ══════════════════════════════════════════════════════════ */
function renderMarkdown(raw) {
  let t = raw
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/```[\w]*\n?([\s\S]*?)```/g,'<pre><code>$1</code></pre>');

  // Tables (line-by-line so separator rows are skipped cleanly)
  const lines = t.split('\n'); const out = []; let tbl = '', inTbl = false;
  for (const line of lines) {
    if (/^\|.+\|$/.test(line)) {
      if (!inTbl) { inTbl = true; tbl = '<table>'; }
      const cells = line.split('|').slice(1,-1).map(c => c.trim());
      if (cells.every(c => /^[-:\s]+$/.test(c))) continue;
      const isHeader = tbl === '<table>';
      tbl += '<tr>' + cells.map(c => isHeader ? `<th>${c}</th>` : `<td>${c}</td>`).join('') + '</tr>';
    } else {
      if (inTbl) { out.push(tbl + '</table>'); tbl = ''; inTbl = false; }
      out.push(line);
    }
  }
  if (inTbl) out.push(tbl + '</table>');
  t = out.join('\n');

  // Headings
  t = t.replace(/^### (.+)$/gm,'<h3>$1</h3>');
  t = t.replace(/^## (.+)$/gm,'<h2>$1</h2>');
  t = t.replace(/^# (.+)$/gm,'<h1>$1</h1>');

  // Inline formatting
  t = t.replace(/^---$/gm,'<hr/>');
  t = t.replace(/\*\*\*(.+?)\*\*\*/g,'<strong><em>$1</em></strong>');
  t = t.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');
  t = t.replace(/\*(.+?)\*/g,'<em>$1</em>');
  t = t.replace(/`([^`\n]+)`/g,'<code>$1</code>');
  t = t.replace(/^> (.+)$/gm,'<blockquote>$1</blockquote>');

  // Ordered lists — use placeholder tags to avoid bad backreferences
  t = t.replace(/^\d+\. (.+)$/gm,'<oli>$1</oli>');
  t = t.replace(/(<oli>[\s\S]*?<\/oli>)/g, block =>
    '<ol>' + block.replace(/<oli>/g,'<li>').replace(/<\/oli>/g,'</li>') + '</ol>'
  );

  // Unordered lists
  t = t.replace(/^[-*] (.+)$/gm,'<uli>$1</uli>');
  t = t.replace(/(<uli>[\s\S]*?<\/uli>)/g, block =>
    '<ul>' + block.replace(/<uli>/g,'<li>').replace(/<\/uli>/g,'</li>') + '</ul>'
  );

  // Paragraphs
  t = t.replace(/\n{2,}/g,'</p><p>').replace(/\n/g,'<br/>');
  if (!t.startsWith('<')) t = '<p>' + t + '</p>';
  return t;
}

/* ══════════════════════════════════════════════════════════
   LIVE PREVIEW
   ══════════════════════════════════════════════════════════ */
function updateLivePreview() {
  const h = parseFloat(document.getElementById('height').value);
  const w = parseFloat(document.getElementById('weight').value);
  const a = parseFloat(document.getElementById('age').value);
  const g = document.getElementById('gender').value;

  const bmiVal = document.getElementById('prevBMIVal');
  const bmiBar = document.getElementById('prevBMIBar');
  const bmiSub = document.getElementById('prevBMISub');
  const bmrVal = document.getElementById('prevBMRVal');

  if (!h || !w) { bmiVal.textContent='—'; bmiBar.style.width='0%'; bmiSub.textContent='Body Mass Index'; bmrVal.textContent='—'; return; }

  const bmi = Math.round(w / ((h/100)**2) * 10) / 10;
  bmiVal.textContent = bmi;
  const pct = Math.min(Math.max(((bmi-15)/25)*100, 0), 100);
  bmiBar.style.width = pct + '%';
  if      (bmi < 18.5) { bmiBar.style.background='#60a5fa'; bmiSub.textContent='Underweight'; }
  else if (bmi < 25)   { bmiBar.style.background='#22c55e'; bmiSub.textContent='Healthy weight'; }
  else if (bmi < 30)   { bmiBar.style.background='#f59e0b'; bmiSub.textContent='Overweight'; }
  else                 { bmiBar.style.background='#ef4444'; bmiSub.textContent='Obese'; }

  if (a && g) {
    const base = 10*w + 6.25*h - 5*a;
    const bmr = Math.round(g === 'Male' ? base+5 : g === 'Female' ? base-161 : base-78);
    bmrVal.textContent = bmr;
  } else bmrVal.textContent = '—';
}
['height','weight','age','gender'].forEach(id => document.getElementById(id).addEventListener('input', updateLivePreview));

/* ══════════════════════════════════════════════════════════
   ACTIVITY SLIDER
   ══════════════════════════════════════════════════════════ */
const slider = document.getElementById('activitySlider');
function syncSlider() {
  const lvl = ACTIVITY_LEVELS[parseInt(slider.value)];
  document.getElementById('actName').textContent = lvl.label;
  document.getElementById('actDesc').textContent = lvl.desc;
}
slider.addEventListener('input', syncSlider);
syncSlider();

/* ══════════════════════════════════════════════════════════
   GOAL CARDS
   ══════════════════════════════════════════════════════════ */
document.querySelectorAll('.goal-card').forEach(c => c.addEventListener('click', () => c.classList.toggle('selected')));
function getGoals() { return [...document.querySelectorAll('.goal-card.selected')].map(c => c.dataset.val); }

/* ══════════════════════════════════════════════════════════
   SCREEN NAVIGATION
   ══════════════════════════════════════════════════════════ */
function showErr(el, msg) { el.textContent = msg; el.classList.remove('hidden'); el.scrollIntoView({ behavior:'smooth', block:'nearest' }); }
function showScreen(n) {
  document.querySelectorAll('.screen').forEach((s,i) => s.classList.toggle('active', i===n));
  document.querySelectorAll('.step-dot').forEach((d,i) => { d.classList.toggle('active',i===n); d.classList.toggle('done',i<n); });
  document.getElementById('progressFill').style.width = [33,66,100][n]+'%';
}

document.getElementById('s0Next').addEventListener('click', () => {
  const h=parseFloat(document.getElementById('height').value), w=parseFloat(document.getElementById('weight').value),
        a=parseFloat(document.getElementById('age').value), g=document.getElementById('gender').value;
  const err=document.getElementById('s0Error');
  if (!h||h<100||h>250) { showErr(err,'Enter a valid height (100–250 cm).'); return; }
  if (!w||w<30||w>300)  { showErr(err,'Enter a valid weight (30–300 kg).'); return; }
  if (!a||a<10||a>110)  { showErr(err,'Enter a valid age (10–110).'); return; }
  if (!g)               { showErr(err,'Please select your biological sex.'); return; }
  err.classList.add('hidden'); showScreen(1);
});
document.getElementById('s1Next').addEventListener('click', () => showScreen(2));
document.getElementById('s1Back').addEventListener('click', () => showScreen(0));
document.getElementById('s2Back').addEventListener('click', () => showScreen(1));
document.getElementById('restartBtn').addEventListener('click', () => location.reload());

/* ══════════════════════════════════════════════════════════
   COLLECT DATA  (field names match Pydantic UserProfile)
   ══════════════════════════════════════════════════════════ */
function collectProfile() {
  return {
    height_cm:    parseFloat(document.getElementById('height').value),
    weight_kg:    parseFloat(document.getElementById('weight').value),
    age:          parseInt(document.getElementById('age').value),
    gender:       document.getElementById('gender').value,
    activity_level: parseInt(document.getElementById('activitySlider').value),
    goals:        getGoals(),
    conditions:   conditionSTI ? conditionSTI.getTags() : [],
    injuries:     InjuryManager.collect(),
    food_allergies: foodSTI  ? foodSTI.getTags()  : [],
    drug_allergies: drugSTI  ? drugSTI.getTags()  : [],
  };
}

/* ══════════════════════════════════════════════════════════
   RENDER METRICS  (from Flask SSE "metrics" event)
   ══════════════════════════════════════════════════════════ */
function renderMetrics(m) {
  document.getElementById('mcBMIVal').textContent = m.bmi.value;
  document.getElementById('mcBMISub').textContent = m.bmi.category;
  const pct = Math.min(Math.max(((m.bmi.value-15)/25)*100,0),100);
  const bar = document.getElementById('mcBMIBar');
  bar.style.width = pct+'%';
  bar.style.background = m.bmi.value<18.5?'#60a5fa':m.bmi.value<25?'#22c55e':m.bmi.value<30?'#f59e0b':'#ef4444';
  document.getElementById('mcBMRVal').textContent  = m.bmr;
  document.getElementById('mcTDEEVal').textContent = m.tdee;
  document.getElementById('mcTDEESub').textContent = m.activity_label;
  document.getElementById('mcCalVal').textContent  = m.adjusted_calories;
  document.getElementById('mcCalSub').textContent  = m.goal_labels.join(' + ') || 'maintenance';
}

/* ══════════════════════════════════════════════════════════
   RENDER SAFETY  (from Flask SSE "safety" event)
   ══════════════════════════════════════════════════════════ */
function renderSafety(s) {
  const sec = document.getElementById('alertsSection');
  sec.innerHTML = '';
  if (s.requires_physician) {
    const d = document.createElement('div');
    d.className = 'alert alert-danger';
    d.innerHTML = `<span class="alert-icon">🚨</span><span><strong>Physician Clearance Required</strong> before starting any exercise program.</span>`;
    sec.appendChild(d);
  }
  s.alerts.forEach(a => {
    const d = document.createElement('div');
    d.className = `alert ${a.level==='danger'?'alert-danger':'alert-warn'}`;
    d.innerHTML = `<span class="alert-icon">${a.level==='danger'?'🚨':'⚠️'}</span><span><strong>${a.condition}:</strong> ${a.message}</span>`;
    sec.appendChild(d);
  });
}

/* ══════════════════════════════════════════════════════════
   AI MESSAGES
   ══════════════════════════════════════════════════════════ */
let storedSystemPrompt = '';
const chatHistory = [];

function appendMsg(role, text, markdown=false) {
  const wrap = document.getElementById('messagesWrap');
  const div  = document.createElement('div');
  div.className = `msg ${role}`;
  div.innerHTML = `<div class="msg-avatar">${role==='assistant'?'A':'U'}</div><div class="msg-body"><div class="msg-role">${role==='assistant'?'AHAA':'YOU'}</div><div class="msg-text"></div></div>`;
  const txt = div.querySelector('.msg-text');
  if (markdown) txt.innerHTML = renderMarkdown(text); else txt.textContent = text;
  wrap.appendChild(div);
  scrollBottom();
  return txt;
}

function appendTyping() { appendLoading(''); }
function appendLoading(label = '🔄 Generating plan, please wait...') {
  const div = document.createElement('div');
  div.id='typingMsg'; div.className='msg assistant';
  const labelHtml = label ? `<span class="loading-label">${label}</span>` : '';
  div.innerHTML=`<div class="msg-avatar">A</div><div class="msg-body"><div class="msg-role">AHAA</div><div class="msg-text">${labelHtml}<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div></div>`;
  document.getElementById('messagesWrap').appendChild(div);
  scrollBottom();
}
function removeTyping() { document.getElementById('typingMsg')?.remove(); }
function scrollBottom() { const r=document.getElementById('reportArea'); r.scrollTop=r.scrollHeight; }

/* ══════════════════════════════════════════════════════════
   SSE STREAM PARSER
   ══════════════════════════════════════════════════════════ */
async function parseSSEStream(response, handlers) {
  const reader  = response.body.getReader();
  const decoder = new TextDecoder();
  let buf = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const lines = buf.split('\n');
    buf = lines.pop();
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      try {
        const evt = JSON.parse(line.slice(6));
        const fn = handlers[evt.type];
        if (fn) fn(evt);
      } catch (_) {}
    }
  }
}

/* ══════════════════════════════════════════════════════════
   GENERATE PLAN
   ══════════════════════════════════════════════════════════ */
document.getElementById('generateBtn').addEventListener('click', async () => {
  const s2Err = document.getElementById('s2Error');
  if (!getGoals().length) { showErr(s2Err, 'Select at least one health goal.'); return; }
  s2Err.classList.add('hidden');

  const profile = collectProfile();

  // Show right panel
  document.getElementById('welcomeState').classList.add('hidden');
  document.getElementById('reportArea').classList.remove('hidden');
  document.getElementById('chatBar').classList.remove('hidden');
  document.getElementById('actionBar').classList.remove('hidden');
  document.getElementById('generateBtn').disabled = true;

  appendMsg('user', 'Please generate my complete personalized health plan based on the intake data provided.');
  appendLoading('⏳ Creating your health plan...');

  let msgEl = null; let fullText = '';

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile }),
    });

    await parseSSEStream(res, {
      metrics: e => renderMetrics(e.data),
      safety:  e => renderSafety(e.data),
      system_prompt: e => { storedSystemPrompt = e.data; },
      chunk: e => { fullText += e.text; },
      error: e => {
        removeTyping();
        appendMsg('assistant', `⚠️ ${e.message}`);
      },
      done: () => {
        removeTyping();
        if (fullText) {
          chatHistory.push({ role: 'assistant', content: fullText });
          msgEl = appendMsg('assistant', fullText, true);
        }
        document.getElementById('generateBtn').disabled = false;
        scrollBottom();
      },
    });
  } catch (e) {
    removeTyping();
    appendMsg('assistant', `⚠️ Network error: ${e.message}. Is Flask running? (python app.py)`);
    document.getElementById('generateBtn').disabled = false;
  }

  chatHistory.unshift({ role: 'user', content: 'Generate my complete personalized health plan.' });
});

/* ══════════════════════════════════════════════════════════
   FOLLOW-UP CHAT
   ══════════════════════════════════════════════════════════ */
let chatBusy = false;

async function sendChat() {
  if (chatBusy || !storedSystemPrompt) return;
  const ta = document.getElementById('chatInput');
  const txt = ta.value.trim();
  if (!txt) return;
  ta.value = ''; ta.style.height = 'auto';

  chatHistory.push({ role: 'user', content: txt });
  appendMsg('user', txt);
  appendLoading('🔄 Generating response, please wait...');
  chatBusy = true;
  document.getElementById('chatSend').disabled = true;

  let fullText = ''; let msgEl = null;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: txt, history: chatHistory.slice(0,-1), system_prompt: storedSystemPrompt }),
    });

    await parseSSEStream(res, {
      chunk: e => { fullText += e.text; },
      error: e => { removeTyping(); appendMsg('assistant', `⚠️ ${e.message}`); },
      done: () => {
        removeTyping();
        if (fullText) {
          chatHistory.push({ role: 'assistant', content: fullText });
          msgEl = appendMsg('assistant', fullText, true);
        }
        chatBusy = false;
        document.getElementById('chatSend').disabled = false;
        scrollBottom();
      },
    });
  } catch (e) {
    removeTyping();
    appendMsg('assistant', `⚠️ ${e.message}`);
    chatBusy = false;
    document.getElementById('chatSend').disabled = false;
  }
}

document.getElementById('chatSend').addEventListener('click', sendChat);
document.getElementById('chatInput').addEventListener('keydown', e => { if (e.key==='Enter'&&!e.shiftKey) { e.preventDefault(); sendChat(); }});
document.getElementById('chatInput').addEventListener('input', function() { this.style.height='auto'; this.style.height=Math.min(this.scrollHeight,120)+'px'; });

/* ══════════════════════════════════════════════════════════
   INIT SEARCH INPUTS
   ══════════════════════════════════════════════════════════ */
let conditionSTI, foodSTI, drugSTI;

function initSearchInputs() {
  const D = window.AHAA_DATA;
  if (!D) return;
  conditionSTI = new SearchTagInput({ inputId:'stiConditionsInput', dropdownId:'stiConditionsDropdown', tagsId:'stiConditionsTags', database: D.DISEASE_DATABASE, allowCustom: false });
  foodSTI      = new SearchTagInput({ inputId:'stiFoodInput',       dropdownId:'stiFoodDropdown',       tagsId:'stiFoodTags',       database: D.FOOD_ALLERGENS,   allowCustom: true  });
  drugSTI      = new SearchTagInput({ inputId:'stiDrugInput',       dropdownId:'stiDrugDropdown',       tagsId:'stiDrugTags',       database: D.DRUG_ALLERGENS,   allowCustom: true  });
  InjuryManager.injectLists();
}

initSearchInputs();
