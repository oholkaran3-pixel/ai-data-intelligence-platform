"use client";

import React, { useState, useEffect } from "react";
import { 
  BarChart3, Upload, Cpu, Database, FileSpreadsheet, Presentation, 
  CheckCircle2, ArrowRight, ShieldCheck, Zap, Layers, Sparkles 
} from "lucide-react";
import { apiRequest } from "@/lib/api";

export default function App() {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<any>(null);
  
  // Auth state
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("admin@intel.ai");
  const [password, setPassword] = useState("AdminPassword123!");
  const [fullName, setFullName] = useState("Enterprise Lead");
  const [authError, setAuthError] = useState("");

  // Projects & Datasets
  const [projects, setProjects] = useState<any[]>([]);
  const [activeProject, setActiveProject] = useState<any>(null);
  const [newProjectTitle, setNewProjectTitle] = useState("");
  const [datasets, setDatasets] = useState<any[]>([]);
  const [activeDataset, setActiveDataset] = useState<any>(null);

  // AI & Analytics
  const [aiQuestion, setAiQuestion] = useState("");
  const [aiResponses, setAiResponses] = useState<any[]>([]);
  const [isAiLoading, setIsAiLoading] = useState(false);

  // Reports
  const [reportStatus, setReportStatus] = useState<string | null>(null);

  useEffect(() => {
    const savedToken = localStorage.getItem("token");
    if (savedToken) {
      setToken(savedToken);
      fetchProjects();
    }
  }, []);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError("");
    try {
      const endpoint = authMode === "login" ? "/auth/login" : "/auth/register";
      const payload = authMode === "login" 
        ? { email, password } 
        : { email, password, full_name: fullName };

      const res = await apiRequest(endpoint, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      localStorage.setItem("token", res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      fetchProjects();
    } catch (err: any) {
      setAuthError(err.message);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
    setProjects([]);
    setActiveProject(null);
    setDatasets([]);
  };

  const fetchProjects = async () => {
    try {
      const data = await apiRequest("/projects");
      setProjects(data);
      if (data.length > 0) {
        selectProject(data[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const createProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectTitle.trim()) return;
    try {
      const proj = await apiRequest("/projects", {
        method: "POST",
        body: JSON.stringify({ title: newProjectTitle, description: "Operational intelligence analysis" }),
      });
      setProjects([proj, ...projects]);
      setActiveProject(proj);
      setNewProjectTitle("");
      fetchDatasets(proj.id);
    } catch (err: any) {
      alert("Error: " + err.message);
    }
  };

  const selectProject = (proj: any) => {
    setActiveProject(proj);
    fetchDatasets(proj.id);
  };

  const fetchDatasets = async (projectId: number) => {
    try {
      const list = await apiRequest(`/datasets?project_id=${projectId}`);
      setDatasets(list);
      if (list.length > 0) {
        setActiveDataset(list[0]);
      } else {
        setActiveDataset(null);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !activeProject) return;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("project_id", activeProject.id.toString());
    formData.append("name", file.name.replace(/\.[^/.]+$/, ""));

    try {
      const newDataset = await apiRequest("/datasets/upload", {
        method: "POST",
        body: formData,
      });
      setDatasets([newDataset, ...datasets]);
      setActiveDataset(newDataset);
      alert(`Dataset '${newDataset.name}' uploaded successfully with quality score: ${newDataset.quality_score}%`);
    } catch (err: any) {
      alert("Upload failed: " + err.message);
    }
  };

  const cleanDuplicates = async () => {
    if (!activeDataset) return;
    try {
      const res = await apiRequest("/cleaning/apply", {
        method: "POST",
        body: JSON.stringify({
          dataset_id: activeDataset.id,
          operation_type: "drop_duplicates",
        }),
      });
      setActiveDataset(res);
      fetchDatasets(activeProject.id);
      alert(`Duplicates cleaned! Current active rows: ${res.row_count}, Quality score: ${res.quality_score}%`);
    } catch (err: any) {
      alert("Cleaning failed: " + err.message);
    }
  };

  const askAi = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aiQuestion.trim() || !activeProject) return;

    setIsAiLoading(true);
    try {
      const res = await apiRequest("/ai/ask", {
        method: "POST",
        body: JSON.stringify({
          project_id: activeProject.id,
          dataset_id: activeDataset?.id,
          question: aiQuestion,
        }),
      });
      setAiResponses([res, ...aiResponses]);
      setAiQuestion("");
    } catch (err: any) {
      alert("AI Assistant error: " + err.message);
    } finally {
      setIsAiLoading(false);
    }
  };

  const generateReport = async (type: "pptx" | "pdf" | "xlsx") => {
    if (!activeProject || !activeDataset) return;
    setReportStatus(`Generating ${type.toUpperCase()} artifact...`);
    try {
      const res = await apiRequest("/reports/generate", {
        method: "POST",
        body: JSON.stringify({
          project_id: activeProject.id,
          dataset_id: activeDataset.id,
          report_type: type,
          title: `Executive Performance Report - ${activeDataset.name}`,
        }),
      });
      setReportStatus(`Report generated successfully!`);
      window.open(`http://localhost:8000${res.download_url}`, "_blank");
    } catch (err: any) {
      alert("Failed to generate report: " + err.message);
      setReportStatus(null);
    }
  };

  // If not authenticated, render Login/Register portal
  if (!token) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col justify-center items-center px-4">
        <div className="max-w-md w-full bg-slate-800 border border-slate-700 rounded-2xl p-8 shadow-2xl">
          <div className="flex items-center space-x-3 mb-6">
            <div className="h-10 w-10 bg-blue-600 rounded-xl flex items-center justify-center text-white">
              <Cpu className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">AI Data Intelligence</h1>
              <p className="text-xs text-slate-400">Enterprise Autonomous Analytics SaaS</p>
            </div>
          </div>

          <div className="flex border-b border-slate-700 mb-6">
            <button
              onClick={() => setAuthMode("login")}
              className={`flex-1 pb-2 font-medium text-sm transition-colors ${
                authMode === "login" ? "text-blue-400 border-b-2 border-blue-400" : "text-slate-400"
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setAuthMode("register")}
              className={`flex-1 pb-2 font-medium text-sm transition-colors ${
                authMode === "register" ? "text-blue-400 border-b-2 border-blue-400" : "text-slate-400"
              }`}
            >
              Create Account
            </button>
          </div>

          {authError && (
            <div className="mb-4 p-3 bg-red-950/50 border border-red-500/40 rounded-lg text-xs text-red-300">
              {authError}
            </div>
          )}

          <form onSubmit={handleAuth} className="space-y-4">
            {authMode === "register" && (
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Corporate Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                required
              />
            </div>

            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2.5 rounded-lg text-sm transition-colors flex items-center justify-center space-x-2 mt-4"
            >
              <span>{authMode === "login" ? "Access Workspace" : "Register Enterprise Account"}</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Authenticated SaaS Dashboard
  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-100">
      {/* Sidebar Navigation */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/50 flex flex-col justify-between">
        <div className="p-4">
          <div className="flex items-center space-x-3 mb-8">
            <div className="h-9 w-9 bg-blue-600 rounded-xl flex items-center justify-center text-white">
              <Cpu className="h-5 w-5" />
            </div>
            <div>
              <span className="font-bold text-sm text-white block">AI Intelligence</span>
              <span className="text-[10px] text-emerald-400 font-semibold tracking-wider uppercase">SaaS Active</span>
            </div>
          </div>

          <div className="space-y-1">
            <div className="px-3 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">Workspaces</div>
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => selectProject(p)}
                className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center justify-between ${
                  activeProject?.id === p.id ? "bg-blue-600/20 text-blue-400 border border-blue-500/30" : "text-slate-300 hover:bg-slate-800"
                }`}
              >
                <span className="truncate">{p.title}</span>
                <span className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">{p.dataset_count || 0}</span>
              </button>
            ))}
          </div>

          <form onSubmit={createProject} className="mt-4">
            <input
              type="text"
              placeholder="+ New Workspace..."
              value={newProjectTitle}
              onChange={(e) => setNewProjectTitle(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500 placeholder-slate-500"
            />
          </form>
        </div>

        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center justify-between">
            <div className="truncate pr-2">
              <p className="text-xs font-medium text-white truncate">{user?.email || "analyst@intel.ai"}</p>
              <p className="text-[10px] text-slate-400">Security: Role-Based</p>
            </div>
            <button
              onClick={handleLogout}
              className="text-xs text-rose-400 hover:text-rose-300 font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </aside>

      {/* Main Analytics Canvas */}
      <main className="flex-1 overflow-y-auto p-8">
        <header className="flex items-center justify-between mb-8 pb-4 border-b border-slate-800">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              {activeProject?.title || "Analytics Studio"}
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Autonomous Ingestion, Quality Profiling, DuckDB SQL Execution & Multi-Agent BI
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <label className="cursor-pointer bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors">
              <Upload className="h-4 w-4" />
              <span>Ingest Raw Dataset</span>
              <input type="file" className="hidden" onChange={handleFileUpload} />
            </label>
          </div>
        </header>

        {/* Dataset Health Overview & Profiling */}
        {activeDataset ? (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                <span className="text-xs font-semibold text-slate-400 uppercase">Quality Integrity</span>
                <div className="text-2xl font-bold text-blue-400 mt-1">{activeDataset.quality_score}%</div>
                <div className="text-[10px] text-slate-400 mt-1">Grade: {activeDataset.quality_summary?.grade || "Verified"}</div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                <span className="text-xs font-semibold text-slate-400 uppercase">Active Records</span>
                <div className="text-2xl font-bold text-emerald-400 mt-1">{activeDataset.row_count?.toLocaleString()}</div>
                <div className="text-[10px] text-slate-400 mt-1">{activeDataset.column_count} Dimensions</div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                <span className="text-xs font-semibold text-slate-400 uppercase">File Metadata</span>
                <div className="text-lg font-bold text-white truncate mt-1">{activeDataset.original_filename}</div>
                <div className="text-[10px] text-slate-400 mt-1">Format: .{activeDataset.file_format?.toUpperCase()} | v{activeDataset.current_version}</div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase">Lineage Operations</span>
                <button
                  onClick={cleanDuplicates}
                  className="bg-amber-600/20 hover:bg-amber-600/30 border border-amber-500/30 text-amber-300 text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors mt-2"
                >
                  ⚡ Auto-Clean Duplicates
                </button>
              </div>
            </div>

            {/* AI Analyst & Natural Language Query */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center space-x-2 mb-4">
                <Sparkles className="h-5 w-5 text-indigo-400" />
                <h2 className="text-base font-bold text-white">Multi-Agent AI Analyst</h2>
              </div>

              <form onSubmit={askAi} className="flex space-x-2">
                <input
                  type="text"
                  placeholder="Ask any analytical question (e.g., 'Which product has the highest revenue?')"
                  value={aiQuestion}
                  onChange={(e) => setAiQuestion(e.target.value)}
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
                <button
                  type="submit"
                  disabled={isAiLoading}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-5 py-2.5 rounded-lg transition-colors"
                >
                  {isAiLoading ? "Analyzing..." : "Ask Assistant"}
                </button>
              </form>

              {aiResponses.length > 0 && (
                <div className="mt-4 space-y-3">
                  {aiResponses.map((r, i) => (
                    <div key={i} className="bg-slate-950 border border-slate-800/80 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">{r.agent_name}</span>
                        {r.sql_query && (
                          <span className="text-[10px] font-mono bg-slate-900 px-2 py-0.5 rounded text-slate-400">
                            SQL: {r.sql_query}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-200 leading-relaxed">{r.content}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Executive Report & Export Suite */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h2 className="text-base font-bold text-white mb-2">Executive Deliverables & Export Suite</h2>
              <p className="text-xs text-slate-400 mb-4">
                Produce presentation-ready corporate decks, multi-worksheet audit tables, and verified PDFs.
              </p>

              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => generateReport("pptx")}
                  className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white text-xs font-semibold px-4 py-2.5 rounded-lg flex items-center space-x-2 transition-colors"
                >
                  <Presentation className="h-4 w-4 text-orange-400" />
                  <span>Export PowerPoint Deck (.pptx)</span>
                </button>

                <button
                  onClick={() => generateReport("xlsx")}
                  className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white text-xs font-semibold px-4 py-2.5 rounded-lg flex items-center space-x-2 transition-colors"
                >
                  <FileSpreadsheet className="h-4 w-4 text-emerald-400" />
                  <span>Export Cleaned Excel (.xlsx)</span>
                </button>

                <button
                  onClick={() => generateReport("pdf")}
                  className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white text-xs font-semibold px-4 py-2.5 rounded-lg flex items-center space-x-2 transition-colors"
                >
                  <ShieldCheck className="h-4 w-4 text-red-400" />
                  <span>Export Executive Audit (.pdf)</span>
                </button>
              </div>

              {reportStatus && (
                <div className="mt-3 text-xs text-emerald-400 flex items-center space-x-1.5">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>{reportStatus}</span>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="bg-slate-900/60 border border-dashed border-slate-800 rounded-2xl p-12 text-center">
            <Database className="h-12 w-12 text-slate-600 mx-auto mb-4" />
            <h3 className="text-base font-bold text-white">No Datasets Ingested Yet</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-6">
              Upload any CSV, Excel, Parquet, or JSON file to initiate autonomous profiling, cleaning, and predictive modeling.
            </p>
            <label className="cursor-pointer bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-5 py-2.5 rounded-lg inline-flex items-center space-x-2 transition-colors">
              <Upload className="h-4 w-4" />
              <span>Choose Dataset File</span>
              <input type="file" className="hidden" onChange={handleFileUpload} />
            </label>
          </div>
        )}
      </main>
    </div>
  );
}
