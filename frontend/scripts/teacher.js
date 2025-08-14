// teacher.js - receives ranking via WS, shows meters, fetches history and supports clear history
let ws = null;

function dbfsToPercent(dbfs) {
  if (!isFinite(dbfs)) return 0;
  const clamped = Math.max(-90, Math.min(0, dbfs));
  return Math.round(((clamped + 90) / 90) * 100);
}

function renderRanking(items) {
  const list = document.getElementById("list");
  list.innerHTML = "";
  items.forEach((s, idx) => {
    const div = document.createElement("div");
    div.className = "item" + (idx === 0 ? " highlight" : "");
    const left = document.createElement("div");
    left.innerHTML = `<b>${idx === 0 ? "⭐ " : ""}${s.name || s.clientId}</b>
      <div class="small">${s.dbfs} dBFS</div>
      <div class="meter-sm" aria-label="Level meter"><div style="width:${dbfsToPercent(s.dbfs)}%"></div></div>`;
    const right = document.createElement("div");
    right.innerHTML = s.text ? `<span class="badge">ASR</span> ${s.text}` : `<span class="small">no transcript</span>`;
    div.appendChild(left);
    div.appendChild(right);
    list.appendChild(div);
  });
}

async function fetchHistory() {
  try {
    const res = await fetch("/history");
    const data = await res.json();
    const ul = document.getElementById("history-list");
    ul.innerHTML = "";
    data.forEach(entry => {
      const li = document.createElement("li");
      li.textContent = `[${entry.time}] ${entry.name}: ${entry.text}`;
      ul.appendChild(li);
    });
  } catch (e) {
    console.warn("history fetch failed", e);
  }
}

async function clearHistory() {
  if (!confirm("Are you sure you want to clear the transcription history?")) return;
  try {
    const res = await fetch("/history/clear", { method: "POST" });
    if (res.ok) {
      await fetchHistory();
    } else {
      console.warn("clear history failed", res.status);
    }
  } catch (e) {
    console.error("clear history error", e);
  }
}

function connect() {
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  const url = `${scheme}://${window.location.host}/ws/teacher`;
  ws = new WebSocket(url);
  ws.onopen = () => { document.getElementById("status").textContent = "connected"; };
  ws.onclose = () => { document.getElementById("status").textContent = "closed"; };
  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === "ranking") renderRanking(msg.data);
    } catch (e) {}
  };
  ws.onerror = () => { document.getElementById("status").textContent = "error"; };
}

window.addEventListener("load", () => {
  document.getElementById("connect").addEventListener("click", connect);
  document.getElementById("clear-history").addEventListener("click", clearHistory);
  setInterval(fetchHistory, 3000);
  fetchHistory();
});
