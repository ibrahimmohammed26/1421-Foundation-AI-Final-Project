import { useState, useEffect } from "react";
import {
  MessageSquare, Download, Database, RefreshCw, Trash2,
  Check, ExternalLink, FileText, Activity,
} from "lucide-react";
import { fetchStats } from "@/lib/api";

const STORAGE_KEY = "1421_chat_messages";

export default function Settings() {
  const [showConfirmClear, setShowConfirmClear] = useState(false);
  const [clearSuccess, setClearSuccess]         = useState(false);
  const [reindexing, setReindexing]             = useState(false);
  const [showSuccess, setShowSuccess]           = useState(false);
  const [docCount, setDocCount]                 = useState<number | null>(null);
  const [exportingDocs, setExportingDocs]       = useState(false);

  useEffect(() => {
    fetchStats().then((s) => setDocCount(s.documents_count)).catch(() => {});
  }, []);

  const handleClearChat = () => {
    sessionStorage.removeItem(STORAGE_KEY);
    window.dispatchEvent(new Event("storage"));
    setShowConfirmClear(false);
    setClearSuccess(true);
    setTimeout(() => setClearSuccess(false), 3000);
  };

  const handleReindexDocuments = async () => {
    setReindexing(true);
    try {
      const res = await fetch("/api/documents/reindex", { method: "POST" });
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

  const handleExportDocuments = async () => {
    setExportingDocs(true);
    try {
      const allDocs: object[] = [];
      let offset = 0;
      const batchSize = 500;
      while (true) {
        const res = await fetch(`/api/documents?limit=${batchSize}&offset=${offset}`);
        if (!res.ok) break;
        const data = await res.json();
        allDocs.push(...data.documents);
        if (allDocs.length >= data.total || data.documents.length < batchSize) break;
        offset += batchSize;
      }
      const blob = new Blob(
        [JSON.stringify({ documents: allDocs, total: allDocs.length, exportDate: new Date().toISOString() }, null, 2)],
        { type: "application/json" }
      );
      const url = URL.createObjectURL(blob);
      const a   = document.createElement("a");
      a.href     = url;
      a.download = `1421-knowledge-base-${new Date().toISOString().split("T")[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Export documents failed", e);
    } finally {
      setExportingDocs(false);
    }
  };

  const handleExportData = () => {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    const chatHistory = raw ? JSON.parse(raw) : [];
    const data = {
      chatHistory,
      exportDate: new Date().toISOString(),
      totalMessages: chatHistory.length,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `1421-chat-export-${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const StatusRow = ({ icon: Icon, label, sub }: { icon: React.ElementType; label: string; sub: string }) => (
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

      <div className="flex-1 overflow-y-auto flex items-start justify-center px-6 py-6">
        <div className="w-full max-w-2xl space-y-6">

          {/* System Status */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-display font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Activity className="h-5 w-5 text-gold" />
              System Status
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
                sub="Semantic document search — knowledge base only, no web search"
              />
              <StatusRow
                icon={MessageSquare}
                label="AI Language Model"
                sub="GPT-4o-mini — answers grounded in indexed documents only"
              />
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
                    <p className="text-xs text-gray-400">Delete all your conversations from this session</p>
                  </div>
                </div>
                <button onClick={() => setShowConfirmClear(true)}
                  className="px-4 py-2 bg-red-50 text-red-600 border border-red-200 rounded-lg text-sm hover:bg-red-100 transition-colors flex items-center gap-2">
                  <Trash2 className="h-3.5 w-3.5" /> Clear
                </button>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Download className="h-4 w-4 text-gray-400" />
                  <div>
                    <span className="text-sm text-gray-800">Export chat history</span>
                    <p className="text-xs text-gray-400">Download your conversations as JSON</p>
                  </div>
                </div>
                <button onClick={handleExportData}
                  className="px-4 py-2 bg-red-50 text-gold border border-gold/30 rounded-lg text-sm hover:bg-red-100 transition-colors flex items-center gap-2">
                  <Download className="h-3.5 w-3.5" /> Export
                </button>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText className="h-4 w-4 text-gray-400" />
                  <div>
                    <span className="text-sm text-gray-800">Export knowledge base</span>
                    <p className="text-xs text-gray-400">Download all {docCount ?? "…"} documents as JSON</p>
                  </div>
                </div>
                <button onClick={handleExportDocuments} disabled={exportingDocs}
                  className="px-4 py-2 bg-red-50 text-gold border border-gold/30 rounded-lg text-sm hover:bg-red-100 transition-colors disabled:opacity-50 flex items-center gap-2">
                  {exportingDocs
                    ? <><RefreshCw className="h-3.5 w-3.5 animate-spin" /> Exporting…</>
                    : <><Download className="h-3.5 w-3.5" /> Export</>}
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
                A document-grounded research platform for exploring Chinese maritime history. All AI responses and Data Map Locations are sourced exclusively from the 1421 Foundation knowledge base.
              </p>
              <div className="flex flex-col gap-2 pt-1">
                <a href="https://www.1421foundation.org/" target="_blank" rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-gold hover:text-gold-dark transition-colors text-sm">
                  <ExternalLink className="h-4 w-4 flex-shrink-0" /> 1421 Foundation Website
                </a>
                <a href="https://www.gavinmenzies.net/" target="_blank" rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-gold hover:text-gold-dark transition-colors text-sm">
                  <ExternalLink className="h-4 w-4 flex-shrink-0" /> Gavin Menzies Official Website
                </a>
                <a href="https://www.facebook.com/1421foundation/" target="_blank" rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-gold hover:text-gold-dark transition-colors text-sm">
                  <ExternalLink className="h-4 w-4 flex-shrink-0" /> 1421 Foundation Facebook Website
                </a>
              </div>
              <div className="pt-3 text-xs text-gray-400">© 2026 1421 Foundation. All rights reserved.</div>
            </div>
          </div>
        </div>
      </div>

      {/* Confirm clear modal */}
      {showConfirmClear && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl border border-gray-200 p-6 max-w-md shadow-xl">
            <h3 className="text-lg font-display font-bold text-gray-900 mb-3">Clear Chat History?</h3>
            <p className="text-sm text-gray-600 mb-6">This will permanently delete all conversations from this session. This cannot be undone.</p>
            <div className="flex gap-3 justify-end">
              <button onClick={() => setShowConfirmClear(false)} className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700">Cancel</button>
              <button onClick={handleClearChat} className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700">Clear All</button>
            </div>
          </div>
        </div>
      )}

      {clearSuccess && (
        <div className="fixed bottom-6 right-6 bg-emerald-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <Check className="h-4 w-4" /><span className="text-sm">Chat history cleared</span>
        </div>
      )}
      {showSuccess && (
        <div className="fixed bottom-6 right-6 bg-emerald-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <Check className="h-4 w-4" /><span className="text-sm">Reindexing started</span>
        </div>
      )}
    </div>
  );
}