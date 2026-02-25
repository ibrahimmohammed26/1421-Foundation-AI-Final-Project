import { useState, useEffect } from "react";
import {
  Trash2,
  MessageSquare,
  Download,
  Database,
  RefreshCw,
  Check,
  ExternalLink,
  FileText,
  Activity,
} from "lucide-react";
import { fetchStats } from "@/lib/api";

export default function Settings() {
  const [showConfirmClear, setShowConfirmClear] = useState(false);
  const [clearSuccess, setClearSuccess] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [docCount, setDocCount] = useState<number | null>(null);

  // Load document count for the status card
  useEffect(() => {
    fetchStats()
      .then((s) => setDocCount(s.documents_count))
      .catch(() => {});
  }, []);

  const handleClearChat = () => {
    localStorage.removeItem("chatHistory");
    setShowConfirmClear(false);
    setClearSuccess(true);
    setTimeout(() => setClearSuccess(false), 3000);
  };

  const handleReindexDocuments = async () => {
    setReindexing(true);
    try {
      const response = await fetch("http://localhost:8000/api/documents/reindex", {
        method: "POST",
      });
      if (response.ok) {
        setShowSuccess(true);
        setTimeout(() => setShowSuccess(false), 3000);
      }
    } catch (error) {
      console.error("Error reindexing:", error);
    } finally {
      setReindexing(false);
    }
  };

  const handleExportData = () => {
    const data = {
      chatHistory: JSON.parse(localStorage.getItem("chatHistory") || "[]"),
      exportDate: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `1421-data-${new Date().toISOString().split("T")[0]}.json`;
    a.click();
  };

  return (
    <div className="flex flex-col h-full bg-navy-dark">
      <div className="border-b border-gray-800 px-6 py-4 bg-navy">
        <h1 className="text-xl font-display font-bold text-gold">Settings</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Manage your data and system settings
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6 bg-navy-dark">
        <div className="max-w-2xl space-y-6">

          {/* ── Document Status ────────────────────────────────────────── */}
          <div className="bg-navy rounded-xl border border-gray-800 p-6">
            <h3 className="text-lg font-display font-bold text-gold mb-4 flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Document Status
            </h3>
            <div className="space-y-3">
              {/* Status row */}
              <div className="flex items-center justify-between p-3 bg-navy-dark rounded-lg border border-gray-800">
                <div className="flex items-center gap-3">
                  <FileText className="h-4 w-4 text-gray-400" />
                  <div>
                    <span className="text-sm text-gray-200 font-medium">Knowledge Base</span>
                    <p className="text-xs text-gray-500">
                      {docCount !== null
                        ? `${docCount} documents indexed`
                        : "Loading…"}
                    </p>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-xs font-semibold text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block" />
                  Active
                </span>
              </div>

              {/* Vector store row */}
              <div className="flex items-center justify-between p-3 bg-navy-dark rounded-lg border border-gray-800">
                <div className="flex items-center gap-3">
                  <Database className="h-4 w-4 text-gray-400" />
                  <div>
                    <span className="text-sm text-gray-200 font-medium">Vector Store (FAISS)</span>
                    <p className="text-xs text-gray-500">Semantic search index</p>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-xs font-semibold text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block" />
                  Active
                </span>
              </div>

              {/* LLM row */}
              <div className="flex items-center justify-between p-3 bg-navy-dark rounded-lg border border-gray-800">
                <div className="flex items-center gap-3">
                  <MessageSquare className="h-4 w-4 text-gray-400" />
                  <div>
                    <span className="text-sm text-gray-200 font-medium">AI Language Model</span>
                    <p className="text-xs text-gray-500">GPT-4o-mini via OpenAI API</p>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-xs font-semibold text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block" />
                  Active
                </span>
              </div>
            </div>
          </div>

          {/* ── Document Database ──────────────────────────────────────── */}
          <div className="bg-navy rounded-xl border border-gray-800 p-6">
            <h3 className="text-lg font-display font-bold text-gold mb-4">
              Document Database
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Database className="h-4 w-4 text-gray-400" />
                  <div>
                    <span className="text-sm text-gray-200">Reindex documents</span>
                    <p className="text-xs text-gray-400">
                      Update the database with new or changed documents
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleReindexDocuments}
                  disabled={reindexing}
                  className="px-4 py-2 bg-gold/10 text-gold rounded-lg text-sm hover:bg-gold/20 transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  <RefreshCw
                    className={`h-4 w-4 ${reindexing ? "animate-spin" : ""}`}
                  />
                  {reindexing ? "Reindexing…" : "Reindex"}
                </button>
              </div>
            </div>
          </div>

          {/* ── Data Management ────────────────────────────────────────── */}
          <div className="bg-navy rounded-xl border border-gray-800 p-6">
            <h3 className="text-lg font-display font-bold text-gold mb-4">
              Data Management
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <MessageSquare className="h-4 w-4 text-gray-400" />
                  <div>
                    <span className="text-sm text-gray-200">Clear chat history</span>
                    <p className="text-xs text-gray-400">Delete all your conversations</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowConfirmClear(true)}
                  className="px-4 py-2 bg-red-500/10 text-red-400 rounded-lg text-sm hover:bg-red-500/20 transition-colors"
                >
                  Clear
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Download className="h-4 w-4 text-gray-400" />
                  <div>
                    <span className="text-sm text-gray-200">Export data</span>
                    <p className="text-xs text-gray-400">
                      Download your conversations as JSON
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleExportData}
                  className="px-4 py-2 bg-gold/10 text-gold rounded-lg text-sm hover:bg-gold/20 transition-colors"
                >
                  Export
                </button>
              </div>
            </div>
          </div>

          {/* ── About ─────────────────────────────────────────────────── */}
          <div className="bg-navy rounded-xl border border-gray-800 p-6">
            <h3 className="text-lg font-display font-bold text-gold mb-4">About</h3>
            <div className="space-y-3">
              <p className="text-sm text-gray-300">
                1421 Foundation Research System v1.0.0
              </p>
              <p className="text-sm text-gray-400">
                A platform for exploring Chinese maritime history using vector
                databases and AI.
              </p>
              <a
                href="https://1421foundation.org"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-gold hover:text-gold/80 transition-colors text-sm"
              >
                Visit 1421 Foundation Website
                <ExternalLink className="h-4 w-4" />
              </a>
              <div className="pt-3 text-xs text-gray-500">
                © 2026 1421 Foundation. All rights reserved.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Confirm clear modal */}
      {showConfirmClear && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-navy rounded-xl border border-gray-800 p-6 max-w-md">
            <h3 className="text-lg font-display font-bold text-gold mb-3">
              Clear Chat History?
            </h3>
            <p className="text-sm text-gray-300 mb-6">
              This will permanently delete all your conversations. This action
              cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowConfirmClear(false)}
                className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleClearChat}
                className="px-4 py-2 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600 transition-colors"
              >
                Clear All
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Clear success toast */}
      {clearSuccess && (
        <div className="fixed bottom-6 right-6 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <Check className="h-4 w-4" />
          <span className="text-sm">Chat history cleared successfully</span>
        </div>
      )}

      {/* Reindex success toast */}
      {showSuccess && (
        <div className="fixed bottom-6 right-6 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <Check className="h-4 w-4" />
          <span className="text-sm">Reindexing started successfully</span>
        </div>
      )}
    </div>
  );
}