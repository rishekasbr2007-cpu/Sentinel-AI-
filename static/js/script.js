// SentinelAI - shared front-end logic

// Global historical buffer for line/bar charts
let defaultHistory = { 
  times: [], safe: [], warn: [], danger: [], quantum: [],
  totalSafe: 180, totalSuspicious: 25, totalFraud: 8, totalQuantum: 2,
  vectors: { "Brute Force": 12, "Impossible Travel": 8, "Bad IP": 10, "Quantum": 2 },
  lastSeenRefNum: 0
};
  try {
    const cachedHistory = sessionStorage.getItem("sentinel_history");
    if (cachedHistory) {
      let parsed = JSON.parse(cachedHistory);
      // Migrate old cache structure to prevent NaN/undefined
      if (parsed.totalSafe === undefined || parsed.lastSeenRefNum === undefined) {
        window.historyBuffer = defaultHistory;
      } else {
        window.historyBuffer = parsed;
      }
    } else {
      window.historyBuffer = defaultHistory;
    }
  } catch (e) {
    window.historyBuffer = defaultHistory;
  }

if (typeof Chart !== 'undefined') {
  Chart.defaults.color = '#7a8699';
  Chart.defaults.font.family = '"Fira Code", monospace';
  Chart.defaults.plugins.tooltip.backgroundColor = '#111827';
  Chart.defaults.plugins.tooltip.titleColor = '#00fff2';
  Chart.defaults.plugins.tooltip.borderColor = 'rgba(0, 255, 242, 0.2)';
  Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.scale.grid.color = 'rgba(0, 255, 242, 0.05)';
  Chart.defaults.scale.ticks.color = '#7a8699';
  Chart.defaults.animation = false; // Disable to prevent jerky redraws on polling
}
// Highlight active sidebar link
document.addEventListener("DOMContentLoaded", () => {
  const path = window.location.pathname;
  document.querySelectorAll(".sidebar nav a").forEach(a => {
    if (a.getAttribute("href") === path) a.classList.add("active");
  });
});

// Calls the new background simulator live feed
async function runAnalysis(batchSize, onDone) {
  const btn = document.getElementById("runBtn");
  if (btn) { btn.disabled = true; btn.innerText = "Fetching live feed..."; }

  try {
    const res = await fetch(`/api/live-stream?n=${batchSize || 50}`);
    const data = await res.json();

    if (!res.ok) {
      alert(data.error || "Something went wrong.");
      return;
    }
    
    console.log(`[Sentinel] API Response -> Fetched ${data.transactions ? data.transactions.length : 0} total records. Summary Totals (from server):`, data.summary);
    
    // Update history buffer by processing new transactions (for spiky line graphs) and accumulating totals (for growing bar/pie charts)
    if (data.transactions) {
      let newSafe = 0, newWarn = 0, newDanger = 0, newQuantum = 0;
      let newCount = 0;
      
      // Iterate in chronological order (data.transactions is already oldest to newest)
      data.transactions.forEach(t => {
        let match = t.ref.match(/TX-SIM-(\d+)/);
        let refNum = match ? parseInt(match[1]) : 0;
        if (refNum > window.historyBuffer.lastSeenRefNum) {
          window.historyBuffer.lastSeenRefNum = refNum;
          newCount++;
          
          let isSafe = (t.risk_level === "Low" && !t.early_warning);
          let isWarn = (t.risk_level === "Medium" || t.early_warning);
          let isDanger = (t.risk_level === "High");
          
          if (isSafe) newSafe++;
          if (isWarn) newWarn++;
          if (isDanger) newDanger++;
          if (t.quantum_flag) newQuantum++;
          
          window.historyBuffer.totalSafe += isSafe ? 1 : 0;
          window.historyBuffer.totalSuspicious += isWarn ? 1 : 0;
          window.historyBuffer.totalFraud += isDanger ? 1 : 0;
          window.historyBuffer.totalQuantum += t.quantum_flag ? 1 : 0;
          
          if (!isSafe) {
            let exp = (t.explanation || "").toLowerCase();
            if (exp.includes("brute") || exp.includes("failed") || exp.includes("login")) window.historyBuffer.vectors["Brute Force"]++;
            if (exp.includes("travel")) window.historyBuffer.vectors["Impossible Travel"]++;
            if (exp.includes("ip")) window.historyBuffer.vectors["Bad IP"]++;
            if (t.quantum_flag) window.historyBuffer.vectors["Quantum"]++;
          }
        }
      });
      
      // If no new transactions (because we just loaded cached data), don't push flatlines, just reuse last point if needed, or push 0s
      // Wait, if it's a live fetch, we always push to time series so the graph marches forward
      const time = new Date().toLocaleTimeString();
      window.historyBuffer.times.push(time);
      window.historyBuffer.safe.push(newSafe);
      window.historyBuffer.warn.push(newWarn);
      window.historyBuffer.danger.push(newDanger);
      window.historyBuffer.quantum.push(newQuantum);
      
      if (window.historyBuffer.times.length > 20) {
        window.historyBuffer.times.shift();
        window.historyBuffer.safe.shift();
        window.historyBuffer.warn.shift();
        window.historyBuffer.danger.shift();
        window.historyBuffer.quantum.shift();
      }
      
      // Overwrite data.summary with accumulating totals so pie charts shift and top metrics grow!
      data.summary.safe = window.historyBuffer.totalSafe;
      data.summary.suspicious = window.historyBuffer.totalSuspicious;
      data.summary.fraud_alerts = window.historyBuffer.totalFraud;
      data.summary.quantum_flags = window.historyBuffer.totalQuantum;
      data.vectors = window.historyBuffer.vectors;
      
      console.log(`[Sentinel] Processed ${newCount} completely new transactions this cycle. Global Safe: ${window.historyBuffer.totalSafe}, Suspicious: ${window.historyBuffer.totalSuspicious}. Updating charts now...`);
      
      try { sessionStorage.setItem("sentinel_history", JSON.stringify(window.historyBuffer)); } catch(e) {}
    }
    
    // Save to sessionStorage for instant cross-page rendering
    try { sessionStorage.setItem("sentinel_cachedData", JSON.stringify(data)); } catch(e) {}

    if (onDone) onDone(data);
  } catch (err) {
    alert("Could not reach the server: " + err);
  } finally {
    if (btn) { btn.disabled = false; btn.innerText = "Fetch Latest Feed"; }
  }
}

function riskPillClass(level) {
  if (level === "High") return "pill pill-high";
  if (level === "Medium") return "pill pill-medium";
  return "pill pill-low";
}

// ---------- Live Mode: auto-refresh the analysis on an interval to feel real-time ----------
let globalLiveModeTimer = null;

async function globalFetchTick() {
  console.log("[Sentinel] Background Timer Tick -> Triggering fetch...");
  let localRender = null;
  const checkbox = document.querySelector('input[type="checkbox"][onchange^="toggleLiveMode"]');
  if (checkbox) {
    const match = checkbox.getAttribute("onchange").match(/toggleLiveMode\([^,]+,\s*(\d+),\s*([a-zA-Z0-9_]+)\)/);
    if (match) {
      localRender = window[match[2]];
    }
  }
  await runAnalysis(200, localRender);
}

function toggleLiveMode(checkbox, batchSize, renderFn) {
  const isOn = checkbox ? checkbox.checked : false;
  sessionStorage.setItem("globalLiveMode", isOn ? "true" : "false");
  
  if (isOn) {
    console.log("[Sentinel] Live Mode ON -> Starting 15s background polling");
    if(!globalLiveModeTimer) {
      runAnalysis(200, renderFn);
      globalLiveModeTimer = setInterval(globalFetchTick, 15000);
    }
  } else {
    console.log("[Sentinel] Live Mode OFF -> Stopping background polling");
    if (globalLiveModeTimer) {
      clearInterval(globalLiveModeTimer);
      globalLiveModeTimer = null;
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const isLive = sessionStorage.getItem("globalLiveMode") === "true";
  const checkbox = document.querySelector('input[type="checkbox"][onchange^="toggleLiveMode"]');
  const runBtn = document.getElementById("runBtn");
  
  let renderFn = null;
  if (checkbox && runBtn) {
    const match = checkbox.getAttribute("onchange").match(/toggleLiveMode\([^,]+,\s*(\d+),\s*([a-zA-Z0-9_]+)\)/);
    if (match) {
      const renderFnName = match[2];
      renderFn = window[renderFnName];
      
      checkbox.setAttribute("onchange", `toggleLiveMode(this, 200, ${renderFnName})`);
      runBtn.setAttribute("onclick", `runAnalysis(200, ${renderFnName})`);
      checkbox.checked = isLive;
    }
  }

  // INSTANT RENDER FROM CACHE
  try {
    const cachedStr = sessionStorage.getItem("sentinel_cachedData");
    if (cachedStr && renderFn) {
      const cachedData = JSON.parse(cachedStr);
      window.currentBatchData = cachedData.transactions ? [...cachedData.transactions] : [];
      renderFn(cachedData);
    }
  } catch(e) {}
  
  // Start global polling if live mode is enabled, regardless of whether current page has a checkbox
  if (isLive) {
    if(!globalLiveModeTimer) {
      globalLiveModeTimer = setInterval(globalFetchTick, 15000);
      globalFetchTick();
    }
  } else if (renderFn && !sessionStorage.getItem("sentinel_cachedData")) {
    runAnalysis(200, renderFn);
  }
});

// Global utility for submitting feedback
async function submitFeedback(ref, feedback, btnElement) {
  try {
    // Disable buttons
    const container = btnElement.parentElement;
    container.innerHTML = `<span style="font-size:11px; color:var(--muted); font-family:var(--font-mono);">Recording...</span>`;
    
    const res = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ref, feedback })
    });
    
    if (res.ok) {
      container.innerHTML = `<span class="pill ${feedback === 'Confirmed' ? 'pill-high' : 'pill-low'}" style="font-size:10px; padding:2px 6px;">${feedback}</span>`;
      // Optional: trigger global stat refresh if function exists
      if(typeof refreshGlobalStats === "function") refreshGlobalStats();
    } else {
      container.innerHTML = `<span style="color:#ff2e63; font-size:11px;">Error</span>`;
    }
  } catch (err) {
    console.error(err);
  }
}

// Global utility for downloading charts
function downloadChart(canvasId, fileName) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  
  const tempCanvas = document.createElement('canvas');
  tempCanvas.width = canvas.width;
  tempCanvas.height = canvas.height;
  const ctx = tempCanvas.getContext('2d');
  
  ctx.fillStyle = '#0a0e17';
  ctx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
  ctx.drawImage(canvas, 0, 0);
  
  const url = tempCanvas.toDataURL("image/png");
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName || (canvasId + "-export.png");
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// Global utility for downloading data as CSV (and PNGs if charts exist)
function downloadData() {
  const timestamp = new Date().getTime();
  const pageName = window.location.pathname.replace('/', '') || 'export';
  
  // 1. Download charts (PNG)
  document.querySelectorAll('canvas').forEach(canvas => {
    if (canvas.id) {
      downloadChart(canvas.id, `${pageName}-${canvas.id}-${timestamp}.png`);
    }
  });

  // 2. Download data (CSV)
  let csvContent = "data:text/csv;charset=utf-8,";
  let hasData = false;
  
  if (window.currentBatchData && window.currentBatchData.length > 0) {
    const data = window.currentBatchData;
    const keys = Object.keys(data[0]);
    csvContent += keys.join(",") + "\n"
      + data.map(row => keys.map(k => {
        let val = row[k] === null || row[k] === undefined ? "" : row[k].toString();
        val = val.replace(/"/g, '""');
        return `"${val}"`;
      }).join(",")).join("\n");
    hasData = true;
  } else {
    // Fallback: Scrape tables on the page
    const tables = document.querySelectorAll('table');
    tables.forEach((table, index) => {
      if (index > 0) csvContent += "\n\n";
      const rows = table.querySelectorAll('tr');
      rows.forEach(row => {
        const cols = row.querySelectorAll('th, td');
        const rowData = Array.from(cols).map(col => `"${col.innerText.replace(/"/g, '""')}"`);
        csvContent += rowData.join(",") + "\n";
      });
      hasData = true;
    });
  }

  if (!hasData) {
    alert("No data available to download.");
    return;
  }
  
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `${pageName}-data-${timestamp}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}


// End of script.js
