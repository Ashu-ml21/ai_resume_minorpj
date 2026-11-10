const $ = (id) => document.getElementById(id);
let resumeId = null;
let currentQuestion = null;
let chatHistory = []; 
const charts = {};

// --- THEME TOGGLE LOGIC ---
const themeToggle = document.getElementById("theme-toggle");
const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
const currentTheme = localStorage.getItem('theme');

if (currentTheme === 'light' || (!currentTheme && !prefersDark)) {
  document.body.classList.add("light-mode");
  if(themeToggle) themeToggle.checked = false;
  updateChartColors(true);
} else {
  if(themeToggle) themeToggle.checked = true;
  updateChartColors(false);
}

if(themeToggle) {
  themeToggle.addEventListener("change", (e) => {
    if (e.target.checked) {
      document.body.classList.remove("light-mode");
      localStorage.setItem("theme", "dark");
      updateChartColors(false);
    } else {
      document.body.classList.add("light-mode");
      localStorage.setItem("theme", "light");
      updateChartColors(true);
    }
  });
}

function updateChartColors(isLight) {
  Chart.defaults.color = isLight ? '#656d76' : '#8b949e';
  Chart.defaults.borderColor = isLight ? '#d0d7de' : '#30363d';
  Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
  
  for (let id in charts) {
    if (charts[id]) {
      const chart = charts[id];
      if (chart.options.scales) {
        if (chart.options.scales.x) {
          chart.options.scales.x.grid.color = isLight ? '#d0d7de' : '#30363d';
          chart.options.scales.x.ticks.color = isLight ? '#656d76' : '#8b949e';
        }
        if (chart.options.scales.y) {
          chart.options.scales.y.grid.color = isLight ? '#d0d7de' : '#30363d';
          chart.options.scales.y.ticks.color = isLight ? '#656d76' : '#8b949e';
        }
        if (chart.options.scales.r) {
          chart.options.scales.r.grid.color = isLight ? '#d0d7de' : '#30363d';
          chart.options.scales.r.angleLines.color = isLight ? '#d0d7de' : '#30363d';
          chart.options.scales.r.pointLabels.color = isLight ? '#1f2328' : '#c9d1d9';
        }
      }
      if (chart.options.plugins && chart.options.plugins.legend && chart.options.plugins.legend.labels) {
         chart.options.plugins.legend.labels.color = isLight ? '#1f2328' : '#c9d1d9';
      }
      chart.update();
    }
  }
}

// --- REST OF THE APP LOGIC ---
function setStatus(text, ok = true) {
  const s = $("upload-status");
  if (s) { s.textContent = text; s.className = "status-bar " + (ok ? "ok" : "err"); }
}

function formatJSON(id, data) {
  const el = $(id);
  if (!el) return;
  el.classList.remove("hidden");
  let html = "";
  
  if (data.pass !== undefined) {
      html += `<div style="margin-bottom:16px; font-weight:bold; font-size:1.1rem; color: ${data.pass ? '#238636' : '#da3633'};">
        ${data.pass ? '✅ ATS Compatible' : '❌ ATS Issues Detected'}</div>`;
      if (data.issues && data.issues.length > 0) {
          html += `<ul style="margin-left:20px; color:var(--text-main); margin-bottom:12px;">`;
          data.issues.forEach(i => html += `<li style="margin-bottom:4px;">${i}</li>`);
          html += `</ul>`;
      }
  }

  for (const [key, value] of Object.entries(data)) {
    if (key === 'pass' || key === 'issues') continue;
    if (Array.isArray(value)) {
      html += `<strong style="color: var(--accent); text-transform: capitalize; display:block; margin-top:12px; margin-bottom:4px;">${key.replace(/_/g, ' ')}:</strong><ul style="margin-left:20px; margin-bottom:12px; color:var(--text-main);">`;
      value.forEach(item => {
        if (typeof item === 'object') html += `<li style="margin-bottom:6px;">${Object.values(item).join(" - ")}</li>`;
        else html += `<li style="margin-bottom:6px;">${item}</li>`;
      });
      html += `</ul>`;
    } else if (typeof value === 'object' && value !== null) {
       html += `<strong style="color: var(--accent); text-transform: capitalize; display:block; margin-top:12px;">${key.replace(/_/g, ' ')}:</strong><div style="margin-left:16px; margin-bottom:12px; padding-left:12px; border-left:2px solid var(--border);">`;
       for (const [k, v] of Object.entries(value)) {
         html += `<div style="color:var(--text-main); margin-bottom:4px;"><em>${k}:</em> ${typeof v === 'object' ? JSON.stringify(v) : v}</div>`;
       }
       html += `</div>`;
    } else {
      html += `<div style="margin-bottom:8px;"><strong style="color: var(--accent); text-transform: capitalize;">${key.replace(/_/g, ' ')}:</strong> <span style="color:var(--text-main);">${value}</span></div>`;
    }
  }
  el.innerHTML = html;
}

function jd() {
  const v = $("jd").value.trim();
  if (!v) throw new Error("Please paste a job description first.");
  return v;
}

async function fetchAPI(url, body, isForm = false) {
  try {
    const opts = isForm ? { method: "POST", body } : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
    const res = await fetch(url, opts);
    if (!res.ok) throw new Error("HTTP " + res.status);
    return await res.json();
  } catch (e) { console.error("API Error on", url, e); return null; }
}

$("file").addEventListener("change", (e) => {
  $("file-name").textContent = e.target.files[0] ? e.target.files[0].name : "No file chosen";
});

$("btn-upload").addEventListener("click", async () => {
  const f = $("file").files[0];
  if (!f) return setStatus("Choose a file first.", false);
  try { jd(); } catch (e) { return setStatus(e.message, false); }

  setStatus("Uploading and parsing…");
  const fd = new FormData(); fd.append("file", f);
  const up = await fetchAPI("/api/resume/upload", fd, true);
  if (!up) return setStatus("Upload failed", false);
  
  resumeId = up.resume_id;
  setStatus(`Uploaded. Generating Live Reasoning...`);
  
  $("live-card").hidden = false; 
  $("live-out").textContent = "";
  
  await runStream();

  setStatus("Reasoning complete. Running analytics…");

  fetchAPI("/api/analytics", { resume_id: resumeId, job_description: jd() }).then(r => { if(r) drawCharts(r); });
  fetchAPI("/api/ats/" + resumeId, {}).then(r => { if(r) { $("ats-card").hidden = false; formatJSON("ats-out", r); } });
  fetchAPI("/api/gaps", { resume_id: resumeId, job_description: jd() }).then(r => { if(r) { $("gaps-card").hidden = false; formatJSON("gaps-out", r); } });
  fetchAPI("/api/quality", { resume_id: resumeId, job_description: jd() }).then(r => { if(r) { $("quality-card").hidden = false; formatJSON("quality-out", r); } });
  fetchAPI("/api/interview/questions", { resume_id: resumeId, job_description: jd() }).then(r => {
    if(r) { $("interview-card").hidden = false; renderQuestions(r); }
  });

  setStatus("Analysis Complete", true);
});

async function runStream() {
  try {
    const res = await fetch("/api/analyse/stream", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ resume_id: resumeId, job_description: jd() }) });
    const reader = res.body.getReader(); const decoder = new TextDecoder(); let buffer = "";
    while (true) {
      const { done, value } = await reader.read(); if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n"); buffer = parts.pop();
      for (const part of parts) {
        if (!part.startsWith("data: ")) continue;
        const chunk = part.slice(6);
        if (chunk === "[DONE]") return;
        $("live-out").textContent += chunk; $("live-out").scrollTop = $("live-out").scrollHeight;
      }
    }
  } catch(e) { console.log("Stream error", e); }
}

function renderQuestions(r) {
  const list = $("question-list"); list.innerHTML = "";
  (r.questions || []).forEach(q => {
    const div = document.createElement("div");
    div.className = "q-item";
    div.innerHTML = `<span class="q-cat">${q.category || "q"}</span>${q.question}`;
    div.addEventListener("click", () => { currentQuestion = q.question; $("chat-input").placeholder = "Answering: " + q.question; $("chat-input").focus(); });
    list.appendChild(div);
  });
}

function appendChatMessage(role, text) {
  const box = $("chat-messages");
  const div = document.createElement("div");
  div.className = "chat-bubble " + (role === 'user' ? 'user-bubble' : 'ai-bubble');
  div.innerHTML = `<strong>${role === 'user' ? 'You' : 'AI Coach'}:</strong> ${text}`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

$("btn-chat-send").addEventListener("click", async () => {
  const input = $("chat-input");
  const msg = input.value.trim();
  if (!msg) return;
  if (!resumeId) return alert("Please upload a resume first.");

  appendChatMessage("user", msg);
  input.value = "";
  
  appendChatMessage("ai", "<em>Typing...</em>");
  const box = $("chat-messages");
  
  const r = await fetchAPI("/api/interview/chat", {
    resume_id: resumeId,
    message: msg,
    history: chatHistory
  });
  
  box.removeChild(box.lastChild);
  
  if (r && r.reply) {
    appendChatMessage("ai", r.reply);
    chatHistory.push({ role: "user", content: msg });
    chatHistory.push({ role: "assistant", content: r.reply });
    if (chatHistory.length > 10) chatHistory = chatHistory.slice(-10);
  } else {
    appendChatMessage("ai", "Error connecting to AI.");
  }
});

$("chat-input").addEventListener("keypress", (e) => {
  if (e.key === "Enter") $("btn-chat-send").click();
});

$("btn-export").addEventListener("click", () => window.open("/api/export/csv", "_blank"));

function buildChart(id, type, data, options) {
  const canvas = $(id); if (!canvas) return;
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart(canvas, { type, data, options: options || {} });
}

function drawCharts(r) {
  if (!r || !r.benchmarks) return;
  $("charts-card").hidden = false;
  const b = r.benchmarks;

  $("b-ats").textContent = (b.ats_parseability || 0).toFixed(1);
  $("b-kw").textContent  = (b.keyword_match || 0).toFixed(1);
  $("b-imp").textContent = (b.impact_density || 0).toFixed(1);
  $("b-sen").textContent = (b.seniority_alignment || 0).toFixed(1);
  $("b-evi").textContent = (b.evidence_integrity || 0).toFixed(1);

  $("ideal-score").textContent = (r.ideal_match || 0) + "%";
  $("ideal-bar").style.width = (r.ideal_match || 0) + "%";
  $("ideal-bar").style.backgroundColor = r.ideal_match > 75 ? "#238636" : r.ideal_match > 50 ? "#d29922" : "#da3633";

  const isLight = document.body.classList.contains("light-mode");
  const gridColor = isLight ? '#d0d7de' : '#30363d';
  const textColor = isLight ? '#656d76' : '#8b949e';
  const labelColor = isLight ? '#1f2328' : '#c9d1d9';

  const baseOpts = { plugins: { legend: { display: false, labels: { color: labelColor } } }, scales: { x: { grid: { color: gridColor }, ticks: { color: textColor } }, y: { grid: { color: gridColor }, ticks: { color: textColor } } } };
  const radarOpts = { scales: { r: { beginAtZero: true, max: 100, grid: { color: gridColor }, angleLines: { color: gridColor }, pointLabels: { color: labelColor }, ticks: { display: false } } }, plugins: { legend: { display: false, labels: { color: labelColor } } } };

  // 1. Radar Base
  buildChart("chart-radar", "radar", { 
    labels: ["ATS", "Keywords", "Impact", "Seniority", "Evidence"], 
    datasets: [{ data: [b.ats_parseability, b.keyword_match, b.impact_density, b.seniority_alignment, b.evidence_integrity], backgroundColor: "rgba(88, 166, 255, 0.2)", borderColor: "#58a6ff" }] 
  }, radarOpts);

  // 2. Coverage
  buildChart("chart-coverage", "bar", { 
    labels: ["Must-have", "Nice-to-have"], 
    datasets: [{ data: [r.must_have_coverage || 0, r.nice_to_have_coverage || 0], backgroundColor: ["#58a6ff", "#1f6feb"] }] 
  }, { ...baseOpts, scales: { ...baseOpts.scales, y: { beginAtZero: true, max: 100, grid: { color: gridColor } } } });

  // 3. Evidence Breakdown
  buildChart("chart-evidence", "doughnut", { 
    labels: Object.keys(r.evidence_breakdown || {}), 
    datasets: [{ data: Object.values(r.evidence_breakdown || {}), backgroundColor: ["#238636", "#d29922", "#da3633"], borderColor: isLight ? "#fff" : "#161b22" }] 
  }, { plugins: { legend: { labels: { color: labelColor } } } });

  // 4. Skill Gaps
  buildChart("chart-gaps", "bar", { 
    labels: (r.gap_severity || []).map((g) => g.skill), 
    datasets: [{ data: (r.gap_severity || []).map((g) => g.severity), backgroundColor: "#da3633" }] 
  }, { ...baseOpts, indexAxis: "y" });

  // 5. Score History
  buildChart("chart-history", "line", { 
    labels: (r.score_history || []).map((h) => new Date(h.created_at).toLocaleTimeString()), 
    datasets: [{ data: (r.score_history || []).map((h) => h.total_score), borderColor: "#58a6ff", backgroundColor: "rgba(88, 166, 255, 0.15)", tension: 0.3, fill: true }] 
  }, { ...baseOpts, scales: { ...baseOpts.scales, y: { beginAtZero: true, max: 100, grid: { color: gridColor } } } });

  // 6. Keyword Density
  const kwLabels = Object.keys(r.keyword_density || {}); 
  const kwColors = kwLabels.map(k => r.keyword_density[k] === "matched" ? "#238636" : "#da3633");
  buildChart("chart-keywords", "bar", { labels: kwLabels, datasets: [{ data: kwLabels.map(() => 100), backgroundColor: kwColors }] }, { ...baseOpts, indexAxis: "y" });

  // 7. Bullet Impact (With AXIS LABELS)
  buildChart("chart-impact", "scatter", { 
    datasets: [{ data: (r.bullet_metrics || []).map(b => ({ x: b.word_count, y: b.impact_score })), backgroundColor: "#58a6ff" }] 
  }, { ...baseOpts, scales: { 
        x: { title: {display:true, text:"Word Count", color: textColor}, grid: { color: gridColor } }, 
        y: { title: {display:true, text:"Impact Score", color: textColor}, min:0, max:100, grid: { color: gridColor } } 
      } });

  // 8. Timeline
  buildChart("chart-timeline", "bar", { 
    labels: (r.timeline || []).map(t => t.company), 
    datasets: [{ data: (r.timeline || []).map(t => t.duration_years), backgroundColor: "#8957e5" }] 
  }, { ...baseOpts, indexAxis: "y" });

  // 9. Completeness
  buildChart("chart-completeness", "bar", { 
    labels: Object.keys(r.completeness || {}), 
    datasets: [{ data: Object.values(r.completeness || {}), backgroundColor: "#58a6ff" }] 
  }, { ...baseOpts, indexAxis: "y", scales: { ...baseOpts.scales, x: {max:100, grid: { color: gridColor }} } });

  // 10. Confidence (With AXIS LABELS)
  buildChart("chart-confidence", "bar", { 
    labels: ["0-20%", "21-40%", "41-60%", "61-80%", "81-100%"], 
    datasets: [{ data: r.confidence_distribution || [0,0,0,0,0], backgroundColor: "#d29922" }] 
  }, { ...baseOpts, plugins: { legend: { display: false } }, scales: { x: {title: {display:true, text:"Confidence Range", color: textColor}, grid: { color: gridColor }}, y: {title: {display:true, text:"Matches", color: textColor}, beginAtZero: true, grid: { color: gridColor }}}});

  // 11. Radar Compare
  buildChart("chart-radar-compare", "radar", { 
    labels: ["ATS", "Keywords", "Impact", "Seniority", "Evidence"], 
    datasets: [{ label: "You", data: [b.ats_parseability, b.keyword_match, b.impact_density, b.seniority_alignment, b.evidence_integrity], borderColor: "#58a6ff", backgroundColor: "rgba(88, 166, 255, 0.2)" }, { label: "Ideal", data: [100, 100, 100, 100, 100], borderColor: "#da3633", borderDash: [5,5] }] 
  }, { ...radarOpts, plugins: { legend: { display: true, labels: { color: labelColor } } } });
}