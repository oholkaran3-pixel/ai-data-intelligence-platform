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

# Production Interactive Portal with Real Multi-Tenant Auth
@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    return """<!DOCTYPE html>
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

  <!-- ================= AUTH MODAL (LOGIN & REGISTRATION) ================= -->
  <div id="authModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md px-4">
    <div class="max-w-md w-full bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl relative overflow-hidden">
      <!-- Glow effect -->
      <div class="absolute -top-16 -left-16 w-36 h-36 bg-blue-600/20 rounded-full blur-3xl pointer-events-none"></div>
      <div class="absolute -bottom-16 -right-16 w-36 h-36 bg-indigo-600/20 rounded-full blur-3xl pointer-events-none"></div>

      <div class="flex items-center space-x-3 mb-6 relative">
        <div class="h-11 w-11 bg-blue-600 rounded-2xl flex items-center justify-center text-white text-xl shadow-lg shadow-blue-500/30">
          <i class="fa-solid fa-brain"></i>
        </div>
        <div>
          <h2 class="text-lg font-bold text-white tracking-tight">AI Data Intelligence</h2>
          <p class="text-[11px] text-slate-400">Enterprise Data Analytics & Multi-Agent BI</p>
        </div>
      </div>

      <!-- Auth Switch Tabs -->
      <div class="flex border-b border-slate-800 mb-6 relative">
        <button id="tabLogin" onclick="switchAuthMode('login')" class="flex-1 pb-3 font-semibold text-xs transition border-b-2 border-blue-500 text-blue-400">
          Sign In
        </button>
        <button id="tabRegister" onclick="switchAuthMode('register')" class="flex-1 pb-3 font-semibold text-xs transition border-b-2 border-transparent text-slate-400 hover:text-slate-200">
          Create Account
        </button>
      </div>

      <!-- Form Error / Success Notification -->
      <div id="authNotice" class="hidden mb-4 p-3 rounded-xl text-xs border"></div>

      <form id="authForm" onsubmit="handleAuthSubmit(event)" class="space-y-4 relative">
        <div id="nameFieldGroup" class="hidden">
          <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Full Name</label>
          <input type="text" id="authFullName" placeholder="e.g. Karan Ohol" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 transition" />
        </div>

        <div>
          <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Work Email</label>
          <input type="email" id="authEmail" required placeholder="analyst@company.com" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 transition" />
        </div>

        <div>
          <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Password</label>
          <input type="password" id="authPassword" required placeholder="••••••••••••" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 transition" />
        </div>

        <button type="submit" id="authSubmitBtn" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2.5 px-4 rounded-xl text-xs transition flex items-center justify-center space-x-2 shadow-lg shadow-blue-600/30 mt-2">
          <span id="authBtnLabel">Access Private Workspace</span>
          <i class="fa-solid fa-arrow-right text-[11px]"></i>
        </button>
      </form>

      <div class="mt-6 pt-4 border-t border-slate-800/80 text-[11px] text-slate-500 text-center flex items-center justify-center gap-1.5">
        <i class="fa-solid fa-shield-halved text-emerald-400"></i>
        <span>100% Private Isolated Workspace per Account</span>
      </div>
    </div>
  </div>

  <!-- ================= TOP NAVIGATION BAR ================= -->
  <header class="border-b border-slate-800 bg-slate-900/70 backdrop-blur px-8 py-3.5 flex items-center justify-between sticky top-0 z-40">
    <div class="flex items-center space-x-3">
      <div class="h-9 w-9 bg-blue-600 rounded-xl flex items-center justify-center text-white text-base shadow-lg shadow-blue-500/20">
        <i class="fa-solid fa-brain"></i>
      </div>
      <div>
        <h1 class="text-base font-bold text-white tracking-tight flex items-center gap-2">
          AI Data Intelligence Platform
          <span class="text-[9px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full font-mono">SAAS SECURE</span>
        </h1>
        <p class="text-[11px] text-slate-400">Autonomous Ingestion, Profiling, DuckDB Analytics & Multi-Agent BI</p>
      </div>
    </div>
    
    <div class="flex items-center space-x-4">
      <div id="authStatusBadge" class="text-xs text-slate-300 bg-slate-800/80 px-3.5 py-1.5 rounded-xl border border-slate-700 flex items-center gap-2">
        <i class="fa-solid fa-user-check text-emerald-400"></i>
        <span>Account: <strong id="headerUserEmail" class="text-white">--</strong></span>
        <button onclick="handleLogout()" title="Logout" class="ml-2 text-rose-400 hover:text-rose-300 text-[11px] font-semibold border-l border-slate-700 pl-2 transition">
          <i class="fa-solid fa-right-from-bracket mr-1"></i> Logout
        </button>
      </div>
      <a href="/docs" target="_blank" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-xl border border-slate-700 transition">
        <i class="fa-solid fa-book mr-1 text-slate-400"></i> API Docs
      </a>
    </div>
  </header>

  <!-- ================= MAIN WORKSPACE CANVAS ================= -->
  <div class="flex-1 flex overflow-hidden">
    <!-- Sidebar: Workspaces & Data Ingest -->
    <aside class="w-80 border-r border-slate-800 bg-slate-900/40 p-5 flex flex-col justify-between overflow-y-auto custom-scroll">
      <div class="space-y-6">
        <div>
          <div class="flex items-center justify-between mb-2">
            <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Workspace</h2>
            <span class="text-[10px] text-blue-400 font-mono" id="workspaceCount">1 Project</span>
          </div>
          <select id="projectSelect" onchange="onWorkspaceChange()" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500">
            <!-- Dynamically populated per authenticated user -->
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
          <div id="uploadFeedback" class="text-[11px] mt-2 hidden"></div>
        </div>

        <!-- Verified Datasets Switcher -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Your Private Datasets</h2>
            <span class="text-[10px] text-slate-500">Click to switch</span>
          </div>
          <div id="datasetList" class="space-y-2">
            <!-- Dynamically populated for this user only -->
          </div>
        </div>
      </div>

      <div class="pt-4 border-t border-slate-800/80 text-[11px] text-slate-500 flex items-center gap-1.5">
        <i class="fa-solid fa-lock text-emerald-400"></i>
        <span>User-Specific Data Isolation Enforced</span>
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

      <!-- Tabular Data Preview Accordion -->
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
        <div class="flex items-center justify-between cursor-pointer" onclick="toggleDataPreview()">
          <div class="flex items-center space-x-2.5">
            <div class="h-8 w-8 bg-blue-600/20 border border-blue-500/30 rounded-lg flex items-center justify-center text-blue-400 text-sm">
              <i class="fa-solid fa-table"></i>
            </div>
            <div>
              <h2 class="text-sm font-bold text-white">Live Tabular Data Inspector</h2>
              <p class="text-[11px] text-slate-400">Preview parsed columns and rows directly in the browser</p>
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
            placeholder="Ask a question about the active dataset (e.g. 'Show total records', 'Average sales by category', 'Distribution')" 
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
    let currentToken = localStorage.getItem("token") || null;
    let currentUser = null;
    try {
      const uStr = localStorage.getItem("user");
      if (uStr) currentUser = JSON.parse(uStr);
    } catch(e) {}

    let currentWorkspaces = [];
    let activeProjectId = null;
    let activeDatasetId = null;
    let activeDatasets = [];
    let chatMemory = {};
    let authMode = "login";

    // Switch between Login and Register tabs
    function switchAuthMode(mode) {
      authMode = mode;
      const tabL = document.getElementById("tabLogin");
      const tabR = document.getElementById("tabRegister");
      const nameGrp = document.getElementById("nameFieldGroup");
      const btnLabel = document.getElementById("authBtnLabel");
      const notice = document.getElementById("authNotice");
      notice.className = "hidden";

      if (mode === "register") {
        tabR.className = "flex-1 pb-3 font-semibold text-xs transition border-b-2 border-blue-500 text-blue-400";
        tabL.className = "flex-1 pb-3 font-semibold text-xs transition border-b-2 border-transparent text-slate-400 hover:text-slate-200";
        nameGrp.classList.remove("hidden");
        btnLabel.innerText = "Create Isolated Account";
      } else {
        tabL.className = "flex-1 pb-3 font-semibold text-xs transition border-b-2 border-blue-500 text-blue-400";
        tabR.className = "flex-1 pb-3 font-semibold text-xs transition border-b-2 border-transparent text-slate-400 hover:text-slate-200";
        nameGrp.classList.add("hidden");
        btnLabel.innerText = "Access Private Workspace";
      }
    }

    // Handle Login or Registration
    async function handleAuthSubmit(e) {
      e.preventDefault();
      const email = document.getElementById("authEmail").value.trim();
      const password = document.getElementById("authPassword").value.trim();
      const fullName = document.getElementById("authFullName").value.trim();
      const notice = document.getElementById("authNotice");
      const btn = document.getElementById("authSubmitBtn");

      notice.className = "hidden";
      btn.disabled = true;
      btn.classList.add("opacity-50");

      try {
        const endpoint = authMode === "login" ? "/api/v1/auth/login" : "/api/v1/auth/register";
        const payload = authMode === "login" ? { email, password } : { email, password, full_name: fullName || email.split("@")[0] };

        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || "Authentication failed");
        }

        currentToken = data.access_token;
        currentUser = data.user;
        localStorage.setItem("token", currentToken);
        localStorage.setItem("user", JSON.stringify(currentUser));

        notice.className = "mb-4 p-3 rounded-xl text-xs bg-emerald-950/40 border border-emerald-800 text-emerald-400";
        notice.innerText = authMode === "login" ? "Login successful! Loading workspace..." : "Account created! Initializing private workspace...";

        setTimeout(() => {
          document.getElementById("authModal").classList.add("hidden");
          startUserSession();
        }, 600);

      } catch (err) {
        notice.className = "mb-4 p-3 rounded-xl text-xs bg-rose-950/40 border border-rose-800 text-rose-400";
        notice.innerText = err.message;
      } finally {
        btn.disabled = false;
        btn.classList.remove("opacity-50");
      }
    }

    function handleLogout() {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      currentToken = null;
      currentUser = null;
      activeDatasets = [];
      activeDatasetId = null;
      currentWorkspaces = [];
      activeProjectId = null;
      chatMemory = {};
      
      document.getElementById("headerUserEmail").innerText = "--";
      document.getElementById("authModal").classList.remove("hidden");
      switchAuthMode("login");
      resetCanvasToBlank();
    }

    function resetCanvasToBlank() {
      document.getElementById("metricScore").innerText = "--";
      document.getElementById("metricGrade").innerText = "Awaiting dataset selection";
      document.getElementById("metricRows").innerText = "--";
      document.getElementById("metricCols").innerText = "-- Columns";
      document.getElementById("metricFormat").innerText = "--";
      document.getElementById("metricVersion").innerText = "Current Version: v1";
      document.getElementById("datasetList").innerHTML = '<div class="text-[11px] text-slate-500 italic p-2 bg-slate-950/30 rounded-lg">No datasets uploaded in this workspace.</div>';
      document.getElementById("aiChatFeed").innerHTML = "";
      document.getElementById("plotlyChartContainer").classList.add("hidden");
      document.getElementById("previewTable").innerHTML = "";
    }

    // Bootstrap user workspace and datasets after authentication
    async function startUserSession() {
      if (!currentToken || !currentUser) {
        document.getElementById("authModal").classList.remove("hidden");
        return;
      }

      document.getElementById("authModal").classList.add("hidden");
      document.getElementById("headerUserEmail").innerText = currentUser.email;

      // Load user projects
      try {
        const res = await fetch("/api/v1/projects", {
          headers: { "Authorization": `Bearer ${currentToken}` }
        });
        if (res.status === 401) {
          handleLogout();
          return;
        }
        currentWorkspaces = await res.json();
        
        const sel = document.getElementById("projectSelect");
        sel.innerHTML = "";
        
        if (currentWorkspaces.length === 0) {
          // If for any reason no project exists, create one on the fly
          const pRes = await fetch("/api/v1/projects", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${currentToken}` },
            body: JSON.stringify({ title: `${currentUser.full_name || 'My'}'s Private Workspace`, description: "Default private workspace" })
          });
          const newP = await pRes.json();
          currentWorkspaces = [newP];
        }

        currentWorkspaces.forEach(p => {
          const opt = document.createElement("option");
          opt.value = p.id;
          opt.innerText = p.title;
          sel.appendChild(opt);
        });

        document.getElementById("workspaceCount").innerText = `${currentWorkspaces.length} Project${currentWorkspaces.length > 1 ? 's' : ''}`;
        activeProjectId = currentWorkspaces[0].id;

        await loadDatasets();

      } catch (e) {
        console.error("Workspace initialization error:", e);
      }
    }

    async function onWorkspaceChange() {
      const sel = document.getElementById("projectSelect");
      activeProjectId = parseInt(sel.value);
      await loadDatasets();
    }

    async function loadDatasets(preferredDatasetId = null) {
      if (!activeProjectId || !currentToken) return;
      try {
        const res = await fetch(`/api/v1/datasets?project_id=${activeProjectId}`, {
          headers: { 'Authorization': `Bearer ${currentToken}` }
        });
        if (res.status === 401) {
          handleLogout();
          return;
        }
        activeDatasets = await res.json();
        renderDatasetList();

        if (activeDatasets && activeDatasets.length > 0) {
          const targetId = preferredDatasetId || activeDatasets[0].id;
          selectDataset(targetId);
        } else {
          resetCanvasToBlank();
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
        el.innerHTML = '<div class="text-[11px] text-slate-500 italic p-2 bg-slate-950/30 rounded-lg">No datasets in this workspace. Upload your first dataset above!</div>';
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

    function selectDataset(id) {
      activeDatasetId = id;
      renderDatasetList();
      const dataset = activeDatasets.find(d => d.id === id);
      if (!dataset) return;

      document.getElementById('metricScore').innerText = dataset.quality_score + '%';
      document.getElementById('metricGrade').innerText = 'Audit Grade: ' + (dataset.quality_summary?.grade || 'Verified');
      document.getElementById('metricRows').innerText = (dataset.row_count || 0).toLocaleString();
      document.getElementById('metricCols').innerText = (dataset.column_count || 0) + ' Dimensions';
      document.getElementById('metricFormat').innerText = dataset.original_filename;
      document.getElementById('metricVersion').innerText = `Current Version: v${dataset.current_version}`;

      renderChatFeedForActiveDataset();
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
        
        input.value = '';

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

    async function launchExcel() {
      await generateAndOpenReport('xlsx');
    }

    async function launchPowerPoint() {
      await generateAndOpenReport('pptx');
    }

    async function launchPDF() {
      await generateAndOpenReport('pdf');
    }

    async function launchPowerBI() {
      await generateAndOpenReport('xlsx');
      alert("Power BI Data Model exported! Opening file. In Power BI Desktop: Click Get Data and choose this file to import all cleaned tables.");
    }

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
        stat.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${type.toUpperCase()} generated! <a href="${rep.download_url}" target="_blank" class="underline font-bold text-white ml-2">Click to Open/Download</a>`;
        window.open(rep.download_url, '_blank');
      } catch (err) {
        stat.innerText = "Report generation failed: " + err.message;
      }
    }

    // Initialize session check on load
    window.addEventListener('DOMContentLoaded', () => {
      startUserSession();
    });
  </script>
</body>
</html>
"""
