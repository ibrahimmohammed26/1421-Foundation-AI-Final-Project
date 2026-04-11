import { useState, useEffect } from "react";
import {
  MessageSquare, Download, Database, Trash2,
  Check, ExternalLink, FileText, Activity,
  RefreshCw, Info, Keyboard, BookOpen, Globe,
  Facebook, Mail, Send,
} from "lucide-react";
import { fetchStats } from "@/lib/api";

const STORAGE_KEY = "1421_chat_messages";

// main function for settings
export default function Settings() {
  const [showConfirmClear, setShowConfirmClear] = useState(false);
  const [clearSuccess,     setClearSuccess]     = useState(false);
  const [showSuccess,      setShowSuccess]      = useState(false);
  const [docCount,         setDocCount]         = useState<number | null>(null);
  const [exportingDocs,    setExportingDocs]    = useState(false);
  const [exportingChat,    setExportingChat]    = useState(false);
  // Feedback form
  const [feedbackName,    setFeedbackName]    = useState("");
  const [feedbackEmail,   setFeedbackEmail]   = useState("");
  const [feedbackType,    setFeedbackType]    = useState("General");
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [feedbackSending, setFeedbackSending] = useState(false);
  const [feedbackSent,    setFeedbackSent]    = useState(false);
  const [feedbackError,   setFeedbackError]   = useState("");

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

  const handleExportChat = () => {
    setExportingChat(true);
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      const chatHistory = raw ? JSON.parse(raw) : [];
      const data = { chatHistory, exportDate: new Date().toISOString(), totalMessages: chatHistory.length };
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href     = url;
      a.download = `1421-chat-export-${new Date().toISOString().split("T")[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Export chat failed", e);
    } finally {
      setExportingChat(false);
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

  const handleSendFeedback = async () => {
    if (!feedbackEmail.trim() || !feedbackMessage.trim()) {
      setFeedbackError("Email and message are required.");
      return;
    }
    setFeedbackError("");
    setFeedbackSending(true);
    try {
      const res = await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name:          feedbackName || "Anonymous",
          email:         feedbackEmail,
          feedback_type: feedbackType,
          message:       feedbackMessage,
        }),
      });
      if (res.ok) {
        setFeedbackSent(true);
        setFeedbackName(""); setFeedbackEmail("");
        setFeedbackType("General"); setFeedbackMessage("");
        setTimeout(() => setFeedbackSent(false), 5000);
      } else {
        setFeedbackError("Failed to send feedback. Please try again.");
      }
    } catch {
      setFeedbackError("Network error. Please check your connection.");
    } finally {
      setFeedbackSending(false);
    }
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

  const DataSourceRow = ({
    icon: Icon, label, sub, count, color,
  }: { icon: React.ElementType; label: string; sub: string; count?: string; color: string }) => (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-100">
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${color}`}>
        <Icon className="h-4 w-4 text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <span className="text-sm text-gray-800 font-medium">{label}</span>
        <p className="text-xs text-gray-400">{sub}</p>
      </div>
      {count && (
        <span className="text-xs font-semibold text-gold bg-red-50 border border-gold/20 px-2 py-0.5 rounded-full flex-shrink-0">
          {count}
        </span>
      )}
    </div>
  );

  return (
    <div className="flex flex-col h-full bg-gray-100">
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm">
        <h1 className="text-xl font-display font-bold text-gray-900">Settings</h1>
        <p className="text-xs text-gray-400 mt-0.5">Manage your data, view system status, and submit feedback</p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-2xl mx-auto space-y-6">

          {/* ── System Status ─────────────────────────────────────────── */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h3 className="text-base font-display font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Activity className="h-4 w-4 text-gold" /> System Status
            </h3>
            <div className="space-y-3">
              <StatusRow
                icon={FileText}
                label="Knowledge Base"
                sub={docCount !== null ? `${docCount.toLocaleString()} documents indexed` : "Loading…"}
              />
              <StatusRow
                icon={Database}
                label="Vector Store (FAISS)"
                sub="Semantic search — knowledge base only, no web search"
              />
              <StatusRow
                icon={MessageSquare}
                label="AI Language Model"
                sub="GPT-4o-mini — answers grounded in indexed documents only"
              />
            </div>
          </div>

          {/* ── Data Management ───────────────────────────────────────── */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h3 className="text-base font-display font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Database className="h-4 w-4 text-gold" /> Data Management
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Trash2 className="h-4 w-4 text-gray-400" />
                  <div>
                    <span className="text-sm text-gray-800">Clear chat history</span>
                    <p className="text-xs text-gray-400">Delete all conversations from this session</p>
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
                <button onClick={handleExportChat} disabled={exportingChat}
                  className="px-4 py-2 bg-red-50 text-gold border border-gold/30 rounded-lg text-sm hover:bg-red-100 transition-colors disabled:opacity-50 flex items-center gap-2">
                  {exportingChat
                    ? <><RefreshCw className="h-3.5 w-3.5 animate-spin" /> Exporting…</>
                    : <><Download className="h-3.5 w-3.5" /> Export</>}
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText className="h-4 w-4 text-gray-400" />
                  <div>
                    <span className="text-sm text-gray-800">Export knowledge base</span>
                    <p className="text-xs text-gray-400">Download all {docCount?.toLocaleString() ?? "…"} documents as JSON</p>
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

          {/* ── Keyboard Shortcuts ────────────────────────────────────── */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h3 className="text-base font-display font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Keyboard className="h-4 w-4 text-gold" /> Keyboard Shortcuts
            </h3>
            <div className="space-y-2">
              {[
                { keys: ["Enter"],           action: "Send chat message" },
                { keys: ["Shift", "Enter"],  action: "New line in chat" },
              ].map(({ keys, action }) => (
                <div key={action} className="flex items-center justify-between py-1.5">
                  <span className="text-sm text-gray-600">{action}</span>
                  <div className="flex items-center gap-1">
                    {keys.map((k) => (
                      <kbd key={k} className="px-2 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs font-mono text-gray-700">
                        {k}
                      </kbd>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ── Submit Feedback ───────────────────────────────────────── */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h3 className="text-base font-display font-bold text-gray-900 mb-1 flex items-center gap-2">
              <Mail className="h-4 w-4 text-gold" /> Submit Feedback
            </h3>
            <p className="text-xs text-gray-400 mb-4">
              Share your thoughts, report issues, or suggest improvements. Feedback is sent directly to the development team.
            </p>
            <div className="space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Name (optional)</label>
                  <input type="text" value={feedbackName}
                    onChange={(e) => setFeedbackName(e.target.value)}
                    placeholder="Your name"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gold/30 focus:border-gold" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Email <span className="text-red-500">*</span></label>
                  <input type="email" value={feedbackEmail}
                    onChange={(e) => setFeedbackEmail(e.target.value)}
                    placeholder="your@email.com"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gold/30 focus:border-gold" />
                </div>
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Feedback Type</label>
                <select value={feedbackType} onChange={(e) => setFeedbackType(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-gold/30 focus:border-gold">
                  <option>General</option>
                  <option>Bug Report</option>
                  <option>Feature Request</option>
                  <option>Document Issue</option>
                  <option>AI Response Quality</option>
                  <option>Data Map Issue</option>
                  <option>Other</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Message <span className="text-red-500">*</span></label>
                <textarea value={feedbackMessage}
                  onChange={(e) => setFeedbackMessage(e.target.value)}
                  placeholder="Describe your feedback…"
                  rows={4}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gold/30 focus:border-gold resize-none" />
              </div>
              {feedbackError && (
                <p className="text-xs text-red-600">{feedbackError}</p>
              )}
              {feedbackSent && (
                <div className="flex items-center gap-2 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
                  <Check className="h-3.5 w-3.5" /> Feedback sent — thank you!
                </div>
              )}
              <button onClick={handleSendFeedback} disabled={feedbackSending}
                className="w-full py-2.5 bg-gold text-white rounded-lg text-sm font-medium hover:bg-gold-light transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
                {feedbackSending
                  ? <><RefreshCw className="h-4 w-4 animate-spin" /> Sending…</>
                  : <><Send className="h-4 w-4" /> Send Feedback</>}
              </button>
            </div>
          </div>

          {/* ── About ─────────────────────────────────────────────────── */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h3 className="text-base font-display font-bold text-gray-900 mb-3 flex items-center gap-2">
              <Info className="h-4 w-4 text-gold" /> About
            </h3>
            <p className="text-sm text-gray-700 mb-1 font-medium">1421 Foundation Research System v1.0.0</p>
            <p className="text-sm text-gray-500 mb-4">
              A document-grounded AI research platform for exploring Chinese maritime history and the 1421 hypothesis.
              All AI responses and Data Map locations are sourced exclusively from the 1421 Foundation knowledge base.
            </p>
            <div className="flex flex-col gap-2">
              <a href="https://www.1421foundation.org/" target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-gold hover:text-gold-dark transition-colors text-sm">
                <Globe className="h-4 w-4 flex-shrink-0" /> 1421 Foundation Website
              </a>
              <a href="https://www.facebook.com/1421foundation/" target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-gold hover:text-gold-dark transition-colors text-sm">
                <Facebook className="h-4 w-4 flex-shrink-0" /> 1421 Foundation Facebook Page
              </a>
              <a href="https://www.gavinmenzies.net/" target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-gold hover:text-gold-dark transition-colors text-sm">
                <ExternalLink className="h-4 w-4 flex-shrink-0" /> Gavin Menzies Official Website
              </a>
            </div>
            <p className="mt-4 text-xs text-gray-400">© 2026 1421 Foundation. All rights reserved.</p>
          </div>

        </div>
      </div>

      {/* ── Confirm clear modal ───────────────────────────────────────── */}
      {showConfirmClear && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl border border-gray-200 p-6 max-w-md shadow-xl mx-4">
            <h3 className="text-base font-display font-bold text-gray-900 mb-3">Clear Chat History?</h3>
            <p className="text-sm text-gray-600 mb-6">This will permanently delete all conversations from this session.</p>
            <div className="flex gap-3 justify-end">
              <button onClick={() => setShowConfirmClear(false)}
                className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700">Cancel</button>
              <button onClick={handleClearChat}
                className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700">Clear All</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Toast notifications ───────────────────────────────────────── */}
      {clearSuccess && (
        <div className="fixed bottom-6 right-6 bg-emerald-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2 z-50">
          <Check className="h-4 w-4" /><span className="text-sm">Chat history cleared</span>
        </div>
      )}
      {showSuccess && (
        <div className="fixed bottom-6 right-6 bg-emerald-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2 z-50">
          <Check className="h-4 w-4" /><span className="text-sm">Operation completed</span>
        </div>
      )}
    </div>
  );
}