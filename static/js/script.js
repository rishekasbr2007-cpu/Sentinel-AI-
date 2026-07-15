// SentinelAI - shared front-end logic

// Global historical buffer for line/bar charts
let defaultHistory = { times: [], safe: [], warn: [], danger: [], quantum: [] };
try {
  let saved = sessionStorage.getItem("sentinel_history");
  window.historyBuffer = saved ? JSON.parse(saved) : defaultHistory;
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
    
    // Store current data for download export
    window.currentBatchData = data.transactions ? [...data.transactions] : [];

    // Reverse so the newest items are at the top of the table
    if (data.transactions) {
      data.transactions.reverse();
    }
    
    // Save to sessionStorage for instant cross-page rendering
    try { sessionStorage.setItem("sentinel_cachedData", JSON.stringify(data)); } catch(e) {}
    
    // Update history buffer
    if (data.summary) {
      const time = new Date().toLocaleTimeString();
      window.historyBuffer.times.push(time);
      window.historyBuffer.safe.push(data.summary.safe);
      window.historyBuffer.warn.push(data.summary.suspicious);
      window.historyBuffer.danger.push(data.summary.fraud_alerts);
      window.historyBuffer.quantum.push(data.summary.quantum_flags);
      
      if (window.historyBuffer.times.length > 20) {
        window.historyBuffer.times.shift();
        window.historyBuffer.safe.shift();
        window.historyBuffer.warn.shift();
        window.historyBuffer.danger.shift();
        window.historyBuffer.quantum.shift();
      }
      try { sessionStorage.setItem("sentinel_history", JSON.stringify(window.historyBuffer)); } catch(e) {}
    }

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
let liveModeTimer = null;

function toggleLiveMode(checkbox, batchSize, renderFn) {
  if (checkbox) {
    localStorage.setItem("liveMode_" + window.location.pathname, checkbox.checked ? "true" : "false");
  }
  
  if (checkbox && checkbox.checked) {
    runAnalysis(batchSize, renderFn); 
    if(liveModeTimer) clearInterval(liveModeTimer);
    liveModeTimer = setInterval(() => runAnalysis(batchSize, renderFn), 15000); 
  } else {
    if (liveModeTimer) clearInterval(liveModeTimer);
    liveModeTimer = null;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // Auto-initialize any page that has a live toggle
  const checkbox = document.querySelector('input[type="checkbox"][onchange^="toggleLiveMode"]');
  const runBtn = document.getElementById("runBtn");
  
  if (checkbox && runBtn) {
    const match = checkbox.getAttribute("onchange").match(/toggleLiveMode\([^,]+,\s*(\d+),\s*([a-zA-Z0-9_]+)\)/);
    if (match) {
      const renderFnName = match[2];
      const renderFn = window[renderFnName];
      
      // Override attributes to strictly use 200 for global consistency
      checkbox.setAttribute("onchange", `toggleLiveMode(this, 200, ${renderFnName})`);
      runBtn.setAttribute("onclick", `runAnalysis(200, ${renderFnName})`);
      
      const isLive = localStorage.getItem("liveMode_" + window.location.pathname) === "true";
      checkbox.checked = isLive;
      
      // INSTANT RENDER: Pull globally cached data and render immediately so charts don't flicker/blank
      try {
        const cachedStr = sessionStorage.getItem("sentinel_cachedData");
        if (cachedStr) {
          const cachedData = JSON.parse(cachedStr);
          window.currentBatchData = cachedData.transactions ? [...cachedData.transactions] : [];
          // Some specific render functions (like live monitoring) need riskScoreHistory preserved
          renderFn(cachedData);
        }
      } catch(e) {}
      
      if (isLive) {
        toggleLiveMode(checkbox, 200, renderFn);
      } else {
        runAnalysis(200, renderFn);
      }
    }
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
