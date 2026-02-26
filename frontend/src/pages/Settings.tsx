import { useState, useEffect } from "react";
import {
  MessageSquare, Download, Database, RefreshCw,
  Check, ExternalLink, FileText, Activity,
} from "lucide-react";
import { fetchStats } from "@/lib/api";

export default function Settings() {
  const [showConfirmClear, setShowConfirmClear] = useState(false);
  const [clearSuccess, setClearSuccess] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [docCount, setDocCount] = useState<number | null>(null);

  useEffect(() => {
    fetchStats().then((s) => setDocCount(s.documents_count)).catch(() => {});
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
      const res = await fetch("http://localhost:8000/api/documents/reindex", { method: "POST" });
      if (res.ok) {
        setShowSuccess(true);
        setTimeout(() => setShowSuccess(false), 3000);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setReindexing(false);
    }
  };

  const handleExportData = () => {
    const data = {
      chatHistory: JSON.parse(localStorage.getItem("chatHistory") || "[]"),
      exportDate: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `1421-data-${new Date().toISOString().split("T")[0]}.json`;
    a.click();
  };

  const StatusRow = ({
    icon: Icon,
    label,
    sub,
  }: {
    icon: React.ElementType;
    label: string;
    sub: string;
  }) => (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100">
      <div className="flex items-center gap-3">
        <Icon className="h-4 w-4 text-gray-400" />
        <div>
          <span className="text-sm text-gray-800 font-medium">{label}</span>
          <p className="text-xs text-gray-400">{sub}</p>
        </div>
      </div>
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-700">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse inline-block" />
        Active
      </span>
    </div>
  );

  return (
    <div className="flex flex-col h-full bg-gray-100">
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm">
        <h1 className="text-xl font-display font-bold text-gray-900">Settings</h1>
        <p className="text-xs text-gray-400 mt-0.5">Manage your data and system settings</p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-2xl space-y-6">

          {/* Document Status */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-display font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Activity className="h-5 w-5 text-gold" />
              Document Status
            </h3>
            <div className="space-y-3">
              <StatusRow
                icon={FileText}
                label="Knowledge Base"
                sub={docCount !== null ? `${docCount} documents indexed` : "Loading…"}
              />
              <StatusRow
                icon={Database}
                label="Vector Store (FAISS)"
                sub="Semantic search index"
              />
              <StatusRow
                icon={MessageSquare}
                label="AI Language Model"
                sub="GPT-4o-mini via OpenAI API"
              />
            </div>
          </div>

          {/* Document Database */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-display font-bold text-gray-900 mb-4">
              Document Database
            </h3>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Database className="h-4 w-4 text-gray-400" />
                <div>
                  <span className="text-sm text-gray-800">Reindex documents</span>
                  <p className="text-xs text-gray-400">Update the database with new or changed documents</p>
                </div>
              </div>
              <button
                onClick={handleReindexDocuments}
                disabled={reindexing}
                className="px-4 py-2 bg-red-50 text-gold border border-gold/30 rounded-lg text-sm hover:bg-red-100 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${reindexing ? "animate-spin" : ""}`} />
                {reindexing ? "Reindexing…" : "Reindex"}
              </button>
            </div>
          </div>

          {/* Data Management */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-display font-bold text-gray-900 mb-4">Data Management</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <MessageSquare className="h-4 w-4 text-gray-400" />
                  <div>
                    <span className="text-sm text-gray-800">Clear chat history</span>
                    <p className="text-xs text-gray-400">Delete all your conversations</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowConfirmClear(true)}
                  className="px-4 py-2 bg-red-50 text-red-600 border border-red-200 rounded-lg text-sm hover:bg-red-100 transition-colors"
                >
                  Clear
                </button>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Download className="h-4 w-4 text-gray-400" />
                  <div>
                    <span className="text-sm text-gray-800">Export data</span>
                    <p className="text-xs text-gray-400">Download your conversations as JSON</p>
                  </div>
                </div>
                <button
                  onClick={handleExportData}
                  className="px-4 py-2 bg-red-50 text-gold border border-gold/30 rounded-lg text-sm hover:bg-red-100 transition-colors"
                >
                  Export
                </button>
              </div>
            </div>
          </div>

          {/* About */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-display font-bold text-gray-900 mb-4">About</h3>
            <div className="space-y-3">
              <p className="text-sm text-gray-700">1421 Foundation Research System v1.0.0</p>
              <p className="text-sm text-gray-500">
                A platform for exploring Chinese maritime history using vector databases and AI.
              </p>
              <a
                href="https://1421foundation.org"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-gold hover:text-gold-dark transition-colors text-sm"
              >
                Visit 1421 Foundation Website
                <ExternalLink className="h-4 w-4" />
              </a>
              <div className="pt-3 text-xs text-gray-400">
                © 2026 1421 Foundation. All rights reserved.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Confirm clear modal */}
      {showConfirmClear && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl border border-gray-200 p-6 max-w-md shadow-xl">
            <h3 className="text-lg font-display font-bold text-gray-900 mb-3">Clear Chat History?</h3>
            <p className="text-sm text-gray-600 mb-6">
              This will permanently delete all your conversations. This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowConfirmClear(false)}
                className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleClearChat}
                className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 transition-colors"
              >
                Clear All
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toasts */}
      {clearSuccess && (
        <div className="fixed bottom-6 right-6 bg-emerald-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <Check className="h-4 w-4" />
          <span className="text-sm">Chat history cleared</span>
        </div>
      )}
      {showSuccess && (
        <div className="fixed bottom-6 right-6 bg-emerald-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <Check className="h-4 w-4" />
          <span className="text-sm">Reindexing started</span>
        </div>
      )}
    </div>
  );
}