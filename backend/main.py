import os
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import auth, projects, datasets, cleaning, ai_assistant, reports, powerbi_api, history, admin

# Create tables in database
Base.metadata.create_all(bind=engine)

# Ensure essential storage directories exist
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.REPORT_DIR, exist_ok=True)
os.makedirs(settings.EXPORT_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.STORAGE_DIR, "parquet"), exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise AI-Powered Automated Data Analytics Platform Backend API"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(projects.router, prefix=settings.API_V1_STR)
app.include_router(datasets.router, prefix=settings.API_V1_STR)
app.include_router(cleaning.router, prefix=settings.API_V1_STR)
app.include_router(ai_assistant.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(powerbi_api.router, prefix=settings.API_V1_STR)
app.include_router(history.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)

# Production Self-Contained Interactive Dashboard Portal
@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Data Intelligence Platform</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <style>
    body { background-color: #0b0f19; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .custom-scroll::-webkit-scrollbar { width: 6px; }
    .custom-scroll::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }
  </style>
</head>
<body class="min-h-screen flex flex-col">

  <!-- Navigation Bar -->
  <header class="border-b border-slate-800 bg-slate-900/70 backdrop-blur px-8 py-4 flex items-center justify-between sticky top-0 z-50">
    <div class="flex items-center space-x-3">
      <div class="h-10 w-10 bg-blue-600 rounded-xl flex items-center justify-center text-white text-lg shadow-lg shadow-blue-500/20">
        <i class="fa-solid fa-brain"></i>
      </div>
      <div>
        <h1 class="text-lg font-bold text-white tracking-tight flex items-center gap-2">
          AI Data Intelligence Platform
          <span class="text-[10px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full font-mono">v1.0 ONLINE</span>
        </h1>
        <p class="text-xs text-slate-400">Autonomous Ingestion, Profiling, DuckDB Analytics & Multi-Agent BI</p>
      </div>
    </div>
    
    <div class="flex items-center space-x-4">
      <div id="authStatus" class="text-xs text-slate-300 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
        <i class="fa-solid fa-user-shield text-blue-400 mr-1.5"></i> Connected: <span id="userEmail" class="font-semibold text-white">admin@intel.ai</span>
      </div>
      <a href="/docs" target="_blank" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700 transition">
        <i class="fa-solid fa-book mr-1 text-slate-400"></i> API Docs
      </a>
    </div>
  </header>

  <!-- Main Grid Workspace -->
  <div class="flex-1 flex overflow-hidden">
    <!-- Sidebar: Workspaces & Data Ingest -->
    <aside class="w-80 border-r border-slate-800 bg-slate-900/40 p-5 flex flex-col justify-between overflow-y-auto custom-scroll">
      <div class="space-y-6">
        <div>
          <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Active Workspace</h2>
          <select id="projectSelect" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500">
            <option value="1">Supply Chain & Operations</option>
          </select>
        </div>

        <!-- Ingest Raw Dataset -->
        <div>
          <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Ingest New Dataset</h2>
          <div class="border-2 border-dashed border-slate-700 hover:border-blue-500 rounded-2xl p-4 text-center bg-slate-950/50 transition">
            <i class="fa-solid fa-cloud-arrow-up text-2xl text-blue-400 mb-2"></i>
            <p class="text-xs font-medium text-slate-300">Choose dataset file</p>
            <p class="text-[10px] text-slate-500 mt-1 mb-3">CSV, XLSX, JSON, Parquet</p>
            <input 
              type="file" 
              id="fileUploadInput" 
              accept=".csv,.xlsx,.xls,.json,.parquet,.txt" 
              class="block w-full text-xs text-slate-400 file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500 cursor-pointer mb-2"
            />
            <button 
              type="button" 
              onclick="startUploadProcess()" 
              id="uploadSubmitBtn" 
              class="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2 px-3 rounded-xl text-xs transition flex items-center justify-center space-x-1.5 shadow-md shadow-blue-600/30"
            >
              <i class="fa-solid fa-upload"></i>
              <span>Upload & Analyze Dataset</span>
            </button>
          </div>
          <div id="uploadFeedback" class="text-[11px] text-emerald-400 mt-2 hidden"></div>
        </div>

        <!-- Verified Datasets Switcher -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Your Datasets</h2>
            <span class="text-[10px] text-slate-500">Click to switch</span>
          </div>
          <div id="datasetList" class="space-y-2">
            <!-- Dynamically populated -->
          </div>
        </div>
      </div>

      <div class="pt-4 border-t border-slate-800/80 text-[11px] text-slate-500">
        <i class="fa-solid fa-shield-halved text-emerald-400 mr-1"></i> Isolated Workspace Storage
      </div>
    </aside>

    <!-- Center Canvas -->
    <main class="flex-1 p-8 overflow-y-auto custom-scroll space-y-6">
      
      <!-- Top Metrics Banner -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div class="flex items-center justify-between text-slate-400 text-xs font-medium uppercase">
            <span>Data Health Score</span>
            <i class="fa-solid fa-gauge-high text-blue-400"></i>
          </div>
          <div id="metricScore" class="text-3xl font-extrabold text-blue-400 mt-2">--</div>
          <div id="metricGrade" class="text-[11px] text-slate-400 mt-1">Awaiting dataset selection</div>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div class="flex items-center justify-between text-slate-400 text-xs font-medium uppercase">
            <span>Verified Records</span>
            <i class="fa-solid fa-database text-emerald-400"></i>
          </div>
          <div id="metricRows" class="text-3xl font-extrabold text-emerald-400 mt-2">--</div>
          <div id="metricCols" class="text-[11px] text-slate-400 mt-1">-- Columns</div>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div class="flex items-center justify-between text-slate-400 text-xs font-medium uppercase">
            <span>Active Dataset File</span>
            <i class="fa-solid fa-file-lines text-purple-400"></i>
          </div>
          <div id="metricFormat" class="text-base font-bold text-white mt-3 truncate">--</div>
          <div id="metricVersion" class="text-[11px] text-slate-400 mt-1">Current Version: v1</div>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm flex flex-col justify-between">
          <div class="flex items-center justify-between text-slate-400 text-xs font-medium uppercase">
            <span>Governed Cleaning</span>
            <i class="fa-solid fa-wand-magic-sparkles text-amber-400"></i>
          </div>
          <button onclick="cleanDuplicates()" class="bg-amber-600/20 hover:bg-amber-600/30 border border-amber-500/30 text-amber-300 text-xs font-semibold py-2 px-3 rounded-xl transition flex items-center justify-center space-x-2 mt-2">
            <i class="fa-solid fa-bolt"></i>
            <span>Deduplicate & Re-Profile</span>
          </button>
        </div>
      </div>

      <!-- Tabular Data Preview Modal/Accordion -->
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
        <div class="flex items-center justify-between cursor-pointer" onclick="toggleDataPreview()">
          <div class="flex items-center space-x-2.5">
            <div class="h-8 w-8 bg-blue-600/20 border border-blue-500/30 rounded-lg flex items-center justify-center text-blue-400 text-sm">
              <i class="fa-solid fa-table"></i>
            </div>
            <div>
              <h2 class="text-sm font-bold text-white">Live Tabular Data Inspector</h2>
              <p class="text-[11px] text-slate-400">Preview raw & parsed columns directly in the browser</p>
            </div>
          </div>
          <button class="text-xs text-blue-400 hover:text-blue-300 flex items-center space-x-1">
            <span id="previewToggleText">Expand Table</span>
            <i id="previewToggleIcon" class="fa-solid fa-chevron-down text-[10px]"></i>
          </button>
        </div>
        
        <div id="dataPreviewBox" class="mt-4 hidden overflow-x-auto custom-scroll max-h-72 border border-slate-800 rounded-xl">
          <table id="previewTable" class="w-full text-left text-[11px] text-slate-300 border-collapse">
            <!-- Table data -->
          </table>
        </div>
      </div>

      <!-- Multi-Agent AI Analyst -->
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center space-x-2.5">
            <div class="h-8 w-8 bg-indigo-600/20 border border-indigo-500/30 rounded-lg flex items-center justify-center text-indigo-400 text-sm">
              <i class="fa-solid fa-robot"></i>
            </div>
            <div>
              <h2 class="text-sm font-bold text-white">Multi-Agent AI Data Analyst</h2>
              <p class="text-[11px] text-slate-400">Natural language questions converted to validated DuckDB SQL</p>
            </div>
          </div>
          <button onclick="clearChatHistory()" class="text-[11px] text-slate-500 hover:text-slate-300 border border-slate-800 px-2.5 py-1 rounded-lg">
            <i class="fa-solid fa-rotate-left mr-1"></i> Clear Chat
          </button>
        </div>

        <div class="flex space-x-2">
          <input 
            type="text" 
            id="aiInput" 
            placeholder="Ask a question about the active dataset (e.g. 'Average Red Bull sales by coolers', 'Show total records', 'Distribution')" 
            class="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500" 
            onkeydown="if(event.key==='Enter') askAI()"
          />
          <button onclick="askAI()" id="aiBtn" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-5 py-2.5 rounded-xl transition flex items-center space-x-2 shadow-lg shadow-indigo-600/20">
            <i class="fa-solid fa-paper-plane"></i>
            <span>Ask Analyst</span>
          </button>
        </div>

        <!-- Dynamic Chart Rendering Container -->
        <div id="plotlyChartContainer" class="mt-4 bg-slate-950 border border-slate-800 rounded-xl p-4 hidden">
          <div id="plotlyChart" style="height: 320px;"></div>
        </div>

        <!-- AI Chat Log -->
        <div id="aiChatFeed" class="mt-4 space-y-3">
          <!-- Dynamic AI Responses for active dataset -->
        </div>
      </div>

      <!-- Executive Deliverables & 1-Click Launch Hub -->
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm">
        <div class="flex items-center space-x-2.5 mb-2">
          <div class="h-8 w-8 bg-emerald-600/20 border border-emerald-500/30 rounded-lg flex items-center justify-center text-emerald-400 text-sm">
            <i class="fa-solid fa-file-export"></i>
          </div>
          <div>
            <h2 class="text-sm font-bold text-white">Deliverables & 1-Click App Launch</h2>
            <p class="text-[11px] text-slate-400">Generate and launch results directly in Power BI, Excel, or PDF</p>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mt-4">
          <!-- Launch in Excel -->
          <button onclick="launchExcel()" class="bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-emerald-500/50 p-4 rounded-xl text-left transition group">
            <div class="text-emerald-400 text-xl mb-2 group-hover:scale-110 transition-transform"><i class="fa-solid fa-file-excel"></i></div>
            <div class="text-xs font-bold text-white">Open in Excel (.xlsx)</div>
            <div class="text-[10px] text-slate-400 mt-1">Multi-sheet workbook ready for pivot tables & formulas</div>
          </button>

          <!-- Launch in Power BI -->
          <button onclick="launchPowerBI()" class="bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-amber-500/50 p-4 rounded-xl text-left transition group">
            <div class="text-amber-400 text-xl mb-2 group-hover:scale-110 transition-transform"><i class="fa-solid fa-chart-pie"></i></div>
            <div class="text-xs font-bold text-white">Connect to Power BI</div>
            <div class="text-[10px] text-slate-400 mt-1">1-click download of cleaned model file + connection guide</div>
          </button>

          <!-- PowerPoint Deck -->
          <button onclick="launchPowerPoint()" class="bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-orange-500/50 p-4 rounded-xl text-left transition group">
            <div class="text-orange-400 text-xl mb-2 group-hover:scale-110 transition-transform"><i class="fa-solid fa-file-powerpoint"></i></div>
            <div class="text-xs font-bold text-white">Open in PowerPoint (.pptx)</div>
            <div class="text-[10px] text-slate-400 mt-1">16:9 corporate deck with data health cards & insights</div>
          </button>

          <!-- PDF Audit -->
          <button onclick="launchPDF()" class="bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-red-500/50 p-4 rounded-xl text-left transition group">
            <div class="text-red-400 text-xl mb-2 group-hover:scale-110 transition-transform"><i class="fa-solid fa-file-pdf"></i></div>
            <div class="text-xs font-bold text-white">Open PDF Audit</div>
            <div class="text-[10px] text-slate-400 mt-1">Formal verification brief and data quality certification</div>
          </button>
        </div>

        <div id="reportStatus" class="mt-3 text-xs text-emerald-400 hidden"></div>
      </div>

    </main>
  </div>

  <script>
    let currentToken = null;
    let activeProjectId = 1;
    let activeDatasetId = null;
    let activeDatasets = [
      {"id": 2, "project_id": 1, "name": "EMRECo Red Bull Data", "original_filename": "EMRECo Red Bull Data.xlsx", "file_format": "xlsx", "row_count": 150, "column_count": 11, "quality_score": 81.5, "quality_summary": {"score": 81.5, "grade": "Good", "total_rows": 150, "total_columns": 11, "total_missing_cells": 203, "missing_ratio_pct": 12.3, "duplicate_rows": 0, "duplicate_ratio_pct": 0.0, "total_outliers_detected": 0, "score_breakdown": {"base_score": 100.0, "missing_penalty": 18.5, "duplicate_penalty": 0.0, "outlier_penalty": 0.0}}, "current_version": 1},
      {"id": 1, "project_id": 1, "name": "sample_sales_data", "original_filename": "sample_sales_data.csv", "file_format": "csv", "row_count": 15, "column_count": 7, "quality_score": 96.0, "quality_summary": {"score": 96.0, "grade": "Excellent", "total_rows": 15, "total_columns": 7, "total_missing_cells": 0, "missing_ratio_pct": 0.0, "duplicate_rows": 0, "duplicate_ratio_pct": 0.0, "total_outliers_detected": 6, "score_breakdown": {"base_score": 100.0, "missing_penalty": 0.0, "duplicate_penalty": 0.0, "outlier_penalty": 4.0}}, "current_version": 2}
    ];
    let chatMemory = {};

    async function initAuth() {
      try {
        console.log("Authenticating...");
        const res = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: 'admin@intel.ai', password: 'AdminPassword123!' })
        });
        const data = await res.json();
        console.log("Auth response:", data);
        if (data.access_token) {
          currentToken = data.access_token;
          await loadDatasets();
        } else {
          console.error("Login did not return access_token:", data);
        }
      } catch (err) {
        console.error("Auth error:", err);
      }
    }

    async function loadDatasets(preferredDatasetId = null) {
      try {
        console.log("Fetching datasets for project:", activeProjectId, "Token:", currentToken ? "Present" : "Missing");
        const res = await fetch(`/api/v1/datasets?project_id=${activeProjectId}`, {
          headers: { 'Authorization': `Bearer ${currentToken}` }
        });
        activeDatasets = await res.json();
        console.log("Datasets loaded from API:", activeDatasets);
        renderDatasetList();

        if (activeDatasets && activeDatasets.length > 0) {
          const targetId = preferredDatasetId || activeDatasets[0].id;
          selectDataset(targetId);
        } else {
          console.log("No datasets returned for this project.");
        }
      } catch (e) {
        console.error("Failed to load datasets:", e);
      }
    }

    function renderDatasetList() {
      const el = document.getElementById('datasetList');
      if (!el) return;
      el.innerHTML = '';
      if (!activeDatasets || activeDatasets.length === 0) {
        el.innerHTML = '<div class="text-[11px] text-slate-500 italic p-2 bg-slate-950/30 rounded-lg">No datasets uploaded yet. Click Choose File above.</div>';
        return;
      }
      activeDatasets.forEach(d => {
        const isSelected = d.id === activeDatasetId;
        const card = document.createElement('div');
        card.className = `p-3 rounded-xl border text-xs cursor-pointer transition flex items-center justify-between ${
          isSelected ? 'bg-blue-600/20 border-blue-500/40 text-blue-300' : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:border-slate-700'
        }`;
        card.onclick = () => selectDataset(d.id);
        card.innerHTML = `
          <div class="truncate pr-2">
            <div class="font-bold text-white truncate">${d.name}</div>
            <div class="text-[10px] text-slate-500">${(d.row_count || 0).toLocaleString()} rows • ${d.quality_score}% Quality</div>
          </div>
          <span class="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-300 uppercase">${d.file_format}</span>
        `;
        el.appendChild(card);
      });
    }

    // Switch dataset and FRESHEN the workspace
    function selectDataset(id) {
      activeDatasetId = id;
      renderDatasetList();
      const dataset = activeDatasets.find(d => d.id === id);
      if (!dataset) return;

      // Update header metrics
      document.getElementById('metricScore').innerText = dataset.quality_score + '%';
      document.getElementById('metricGrade').innerText = 'Audit Grade: ' + (dataset.quality_summary?.grade || 'Verified');
      document.getElementById('metricRows').innerText = (dataset.row_count || 0).toLocaleString();
      document.getElementById('metricCols').innerText = (dataset.column_count || 0) + ' Dimensions';
      document.getElementById('metricFormat').innerText = dataset.original_filename;
      document.getElementById('metricVersion').innerText = `Current Version: v${dataset.current_version}`;

      // Reset / Clear chat feed for this new file context
      renderChatFeedForActiveDataset();

      // Load tabular preview
      loadTabularPreview(id);
    }

    async function loadTabularPreview(id) {
      try {
        const res = await fetch(`/api/v1/datasets/${id}/preview?limit=15`, {
          headers: { 'Authorization': `Bearer ${currentToken}` }
        });
        const json = await res.json();
        const table = document.getElementById('previewTable');
        if (!json.columns || json.columns.length === 0) {
          table.innerHTML = '<tr><td class="p-3 text-slate-500">No data records previewable.</td></tr>';
          return;
        }

        let html = '<thead class="bg-slate-950 text-slate-400 font-semibold sticky top-0 border-b border-slate-800"><tr>';
        json.columns.forEach(c => {
          html += `<th class="px-3 py-2 whitespace-nowrap">${c}</th>`;
        });
        html += '</tr></thead><tbody>';

        json.data.forEach((row, idx) => {
          html += `<tr class="${idx % 2 === 0 ? 'bg-slate-900/50' : 'bg-slate-900/20'} border-b border-slate-800/40">`;
          json.columns.forEach(c => {
            const val = row[c] !== null && row[c] !== undefined ? row[c] : '<span class="text-slate-600">null</span>';
            html += `<td class="px-3 py-1.5 whitespace-nowrap">${val}</td>`;
          });
          html += '</tr>';
        });
        html += '</tbody>';
        table.innerHTML = html;
      } catch (e) {
        console.error("Preview load error:", e);
      }
    }

    function toggleDataPreview() {
      const box = document.getElementById('dataPreviewBox');
      const text = document.getElementById('previewToggleText');
      const icon = document.getElementById('previewToggleIcon');
      if (box.classList.contains('hidden')) {
        box.classList.remove('hidden');
        text.innerText = "Collapse Table";
        icon.className = "fa-solid fa-chevron-up text-[10px]";
      } else {
        box.classList.add('hidden');
        text.innerText = "Expand Table";
        icon.className = "fa-solid fa-chevron-down text-[10px]";
      }
    }

    function renderChatFeedForActiveDataset() {
      const feed = document.getElementById('aiChatFeed');
      const chartBox = document.getElementById('plotlyChartContainer');
      feed.innerHTML = '';
      chartBox.classList.add('hidden');

      const messages = chatMemory[activeDatasetId] || [];
      if (messages.length === 0) {
        feed.innerHTML = '<div class="text-[11px] text-slate-500 italic p-3 bg-slate-950/40 border border-slate-800/50 rounded-xl">Clean session started for this dataset. Ask any analytical question above.</div>';
        return;
      }

      messages.forEach(m => {
        const box = document.createElement('div');
        box.className = 'bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs space-y-2';
        box.innerHTML = `
          <div class="flex items-center justify-between">
            <span class="font-bold text-indigo-400 uppercase tracking-wider text-[10px]">${m.agent_name || 'AI Analyst'}</span>
            ${m.sql_query ? `<span class="font-mono bg-slate-900 border border-slate-800 px-2 py-0.5 rounded text-slate-400 text-[10px]">SQL: ${m.sql_query}</span>` : ''}
          </div>
          <p class="text-slate-200 leading-relaxed">${m.content}</p>
        `;
        feed.appendChild(box);
      });

      // Render chart of last message if present
      const lastWithChart = [...messages].reverse().find(m => m.chart_spec);
      if (lastWithChart) {
        renderChart(lastWithChart.chart_spec);
      }
    }

    function clearChatHistory() {
      if (activeDatasetId) {
        chatMemory[activeDatasetId] = [];
        renderChatFeedForActiveDataset();
      }
    }

    async function startUploadProcess() {
      const input = document.getElementById('fileUploadInput');
      const file = input && input.files && input.files[0];
      if (!file) {
        alert("Please choose a file first by clicking 'Choose File'.");
        return;
      }

      const fd = new FormData();
      fd.append('file', file);
      fd.append('project_id', activeProjectId);
      fd.append('name', file.name.replace(/\\.[^/.]+$/, ""));

      const fb = document.getElementById('uploadFeedback');
      fb.classList.remove('hidden');
      fb.className = "text-[11px] text-blue-400 mt-2 p-2 bg-blue-950/40 border border-blue-800/50 rounded-lg";
      fb.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Processing <b>' + file.name + '</b>...';

      const btn = document.getElementById('uploadSubmitBtn');
      btn.disabled = true;
      btn.classList.add('opacity-50');

      try {
        if (!currentToken) {
          const authRes = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: 'admin@intel.ai', password: 'AdminPassword123!' })
          });
          const authData = await authRes.json();
          currentToken = authData.access_token;
        }

        const res = await fetch('/api/v1/datasets/upload', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${currentToken}` },
          body: fd
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({ detail: 'Upload failed' }));
          throw new Error(errData.detail || 'Server error ' + res.status);
        }

        const newD = await res.json();
        fb.className = "text-[11px] text-emerald-400 mt-2 p-2 bg-emerald-950/40 border border-emerald-800/50 rounded-lg";
        fb.innerHTML = `<i class="fa-solid fa-circle-check mr-1"></i> Successfully Analyzed <b>${newD.name}</b> (${newD.quality_score}% Quality, ${newD.row_count} rows)`;
        
        // Reset file input
        input.value = '';

        // Reload datasets list from server and immediately select the new one
        await loadDatasets(newD.id);
      } catch (err) {
        fb.className = "text-[11px] text-rose-400 mt-2 p-2 bg-rose-950/40 border border-rose-800/50 rounded-lg";
        fb.innerHTML = `<i class="fa-solid fa-circle-xmark mr-1"></i> ${err.message}`;
        alert("Upload error: " + err.message);
      } finally {
        btn.disabled = false;
        btn.classList.remove('opacity-50');
      }
    }

    async function cleanDuplicates() {
      if (!activeDatasetId) return;
      const res = await fetch('/api/v1/cleaning/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentToken}` },
        body: JSON.stringify({ dataset_id: activeDatasetId, operation_type: 'drop_duplicates' })
      });
      const updated = await res.json();
      alert(`Cleaned duplicate records! Active rows: ${updated.row_count}, Quality score: ${updated.quality_score}%`);
      await loadDatasets(updated.id);
    }

    async function askAI() {
      const input = document.getElementById('aiInput');
      const q = input.value.trim();
      if (!q || !activeDatasetId) return;

      const btn = document.getElementById('aiBtn');
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';

      try {
        const res = await fetch('/api/v1/ai/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentToken}` },
          body: JSON.stringify({ project_id: activeProjectId, dataset_id: activeDatasetId, question: q })
        });
        const data = await res.json();

        if (!chatMemory[activeDatasetId]) {
          chatMemory[activeDatasetId] = [];
        }
        chatMemory[activeDatasetId].unshift(data);
        renderChatFeedForActiveDataset();
        input.value = '';
      } catch (err) {
        alert("AI Assistant error: " + err.message);
      } finally {
        btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Ask Analyst';
      }
    }

    function renderChart(spec) {
      const container = document.getElementById('plotlyChartContainer');
      container.classList.remove('hidden');

      if (spec.type === 'bar') {
        const trace = {
          x: spec.x,
          y: spec.y,
          type: 'bar',
          marker: { color: '#3b82f6' }
        };
        const layout = {
          title: { text: spec.title || 'Analysis Chart', font: { color: '#f1f5f9', size: 14 } },
          paper_bgcolor: '#020617',
          plot_bgcolor: '#020617',
          font: { color: '#94a3b8' },
          margin: { t: 40, b: 60, l: 60, r: 20 }
        };
        Plotly.newPlot('plotlyChart', [trace], layout, { responsive: true });
      } else if (spec.type === 'pie') {
        const trace = {
          labels: spec.labels,
          values: spec.values,
          type: 'pie',
          marker: { colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'] }
        };
        const layout = {
          title: { text: spec.title || 'Distribution Chart', font: { color: '#f1f5f9', size: 14 } },
          paper_bgcolor: '#020617',
          font: { color: '#94a3b8' },
          margin: { t: 40, b: 20, l: 20, r: 20 }
        };
        Plotly.newPlot('plotlyChart', [trace], layout, { responsive: true });
      }
    }

    // 1-Click Launchers
    async function launchExcel() {
      await generateAndOpenReport('xlsx');
    }

    async function launchPowerPoint() {
      await generateAndOpenReport('pptx');
    }

    async function launchPDF() {
      await generateAndOpenReport('pdf');
    }

    async function launchPowerBI() {{
      await generateAndOpenReport('xlsx');
      alert("Power BI Data Model exported! Opening file. In Power BI Desktop: Click Get Data and choose this file to import all cleaned tables.");
    }}

    async function generateAndOpenReport(type) {
      if (!activeDatasetId) { alert("Please select a dataset first."); return; }
      const stat = document.getElementById('reportStatus');
      stat.classList.remove('hidden');
      stat.innerText = `Compiling and launching ${type.toUpperCase()} artifact...`;

      try {
        const dataset = activeDatasets.find(d => d.id === activeDatasetId);
        const res = await fetch('/api/v1/reports/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentToken}` },
          body: JSON.stringify({
            project_id: activeProjectId,
            dataset_id: activeDatasetId,
            report_type: type,
            title: `Executive Performance Report - ${dataset ? dataset.name : 'Dataset'}`
          })
        });
        const rep = await res.json();
        stat.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${type.toUpperCase()} successfully generated! <a href="${rep.download_url}" target="_blank" class="underline font-bold text-white ml-2">Click to Open/Download</a>`;
        
        // Automatically open the generated file in a new tab/application
        window.open(rep.download_url, '_blank');
      } catch (err) {
        stat.innerText = "Report generation failed: " + err.message;
      }
    }

    // Direct Bootstrapping: Instantly render datasets from initial state
    renderDatasetList();
    if (activeDatasets && activeDatasets.length > 0) {
      selectDataset(activeDatasets[0].id);
    }

    window.addEventListener('DOMContentLoaded', () => {
      initAuth();
    });
    // Fallback trigger in case DOMContentLoaded already fired
    setTimeout(() => {
      if (!currentToken) {
        initAuth();
      }
    }, 500);
  </script>
</body>
</html>
    """
