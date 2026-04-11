import { useState, useEffect } from "react";
import {
  MessageSquare, Download, Database, Trash2,
  Check, ExternalLink, FileText, Activity,
  RefreshCw, Info, Keyboard, Globe,
  Facebook
} from "lucide-react";
import { fetchStats } from "@/lib/api";

const STORAGE_KEY = "1421_chat_messages";

export default function Settings() {
  const [showConfirmClear, setShowConfirmClear] = useState(false);
  const [clearSuccess, setClearSuccess] = useState(false);
  const [docCount, setDocCount] = useState<number | null>(null);

  const [exportingDocs, setExportingDocs] = useState(false);
  const [exportingChat, setExportingChat] = useState(false);

  const [feedbackName, setFeedbackName] = useState("");
  const [feedbackEmail, setFeedbackEmail] = useState("");
  const [feedbackType, setFeedbackType] = useState("General");
  const [feedbackMessage, setFeedbackMessage] = useState("");

  const [feedbackSending, setFeedbackSending] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [feedbackError, setFeedbackError] = useState("");

  useEffect(() => {
    fetchStats()
      .then((res) => setDocCount(res.documents_count))
      .catch(() => {
        // silently fail, if it doesn't work
      });
  }, []);

  const handleClearChat = () => {
    sessionStorage.removeItem(STORAGE_KEY);
    window.dispatchEvent(new Event("storage"));

    setShowConfirmClear(false);
    setClearSuccess(true);

    setTimeout(() => {
      setClearSuccess(false);
    }, 3000);
  };

  const handleExportChat = () => {
    setExportingChat(true);

    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      const parsed = raw ? JSON.parse(raw) : [];

      const payload = {
        chatHistory: parsed,
        exportDate: new Date().toISOString(),
        totalMessages: parsed.length,
      };

      const blob = new Blob(
        [JSON.stringify(payload, null, 2)],
        { type: "application/json" }
      );

      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = url;
      link.download = `1421-chat-${new Date().toISOString().split("T")[0]}.json`;
      link.click();

      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Couldn’t export chat", err);
    } finally {
      setExportingChat(false);
    }
  };

  const handleExportDocuments = async () => {
    setExportingDocs(true);

    try {
      let allDocs: object[] = [];
      let offset = 0;
      const batch = 500;
      while (true) {
        const res = await fetch(`/api/documents?limit=${batch}&offset=${offset}`);
        if (!res.ok) break;

        const data = await res.json();
        const docs = data.documents || [];

        allDocs = allDocs.concat(docs);

        if (docs.length < batch) break;
        offset += batch;
      }

      const blob = new Blob(
        [JSON.stringify({
          documents: allDocs,
          total: allDocs.length,
          exportDate: new Date().toISOString()
        }, null, 2)],
        { type: "application/json" }
      );

      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = url;
      link.download = `1421-docs-${new Date().toISOString().split("T")[0]}.json`;
      link.click();

      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Document export failed", err);
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
          name: feedbackName || "Anonymous",
          email: feedbackEmail,
          feedback_type: feedbackType,
          message: feedbackMessage,
        }),
      });

      if (!res.ok) {
        setFeedbackError("Failed to send feedback.");
        return;
      }

      setFeedbackSent(true);
      setFeedbackName("");
      setFeedbackEmail("");
      setFeedbackType("General");
      setFeedbackMessage("");

      setTimeout(() => setFeedbackSent(false), 5000);
    } catch {
      setFeedbackError("Network error — check connection?");
    } finally {
      setFeedbackSending(false);
    }
  };

  const StatusRow = ({ icon: Icon, label, sub }: any) => (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
      <div className="flex items-center gap-3">
        <Icon className="h-4 w-4 text-gray-400" />
        <div>
          <div className="text-sm text-gray-800 font-medium">{label}</div>
          <div className="text-xs text-gray-400">{sub}</div>
        </div>
      </div>
      <span className="text-xs px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 border">
        Active
      </span>
    </div>
  );


  return (
    <div className="flex flex-col h-full bg-gray-100">
      <div className="border-b px-6 py-4 bg-white">
        <h1 className="text-xl font-bold text-gray-900">Settings</h1>
        <p className="text-xs text-gray-400">
          Manage data, exports, and system info
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-2xl mx-auto space-y-6">

          <div className="bg-white rounded-xl border p-6">
            <h3 className="font-bold mb-4 flex items-center gap-2">
              <Activity className="h-4 w-4" /> System Status
            </h3>

            <div className="space-y-3">
              <StatusRow
                icon={FileText}
                label="Knowledge Base"
                sub={docCount ? `${docCount} documents indexed` : "Loading…"}
              />
              <StatusRow
                icon={Database}
                label="Vector Search"
                sub="FAISS — document-only search"
              />
              <StatusRow
                icon={MessageSquare}
                label="AI Model"
                sub="Responses grounded in indexed docs"
              />
            </div>
          </div>

          <div className="bg-white rounded-xl border p-6">
            <h3 className="font-bold mb-4 flex items-center gap-2">
              <Database className="h-4 w-4" /> Data
            </h3>

            <div className="space-y-4">
              <button onClick={() => setShowConfirmClear(true)}>
                Clear chat history
              </button>


              <button onClick={handleExportChat} disabled={exportingChat}>
                {exportingChat ? "Exporting…" : "Export chat"}
              </button>

              <button onClick={handleExportDocuments} disabled={exportingDocs}>
                {exportingDocs ? "Exporting…" : "Export documents"}
              </button>
            </div>
          </div>

          <div className="bg-white rounded-xl border p-6">
            <h3 className="font-bold mb-3 flex items-center gap-2">
              <Info className="h-4 w-4" /> About
            </h3>

            <p className="text-sm text-gray-500">
              1421 Foundation Research System — document-grounded AI platform.
            </p>

            <div className="mt-3 flex flex-col gap-2">
              <a href="https://www.1421foundation.org/" target="_blank">
                <Globe className="inline h-4 w-4" /> Website
              </a>
              <a href="https://www.facebook.com/1421foundation/" target="_blank">
                <Facebook className="inline h-4 w-4" /> Facebook
              </a>
              <a href="https://www.gavinmenzies.net/" target="_blank">
                <ExternalLink className="inline h-4 w-4" /> Gavin Menzies
              </a>
            </div>
          </div>

        </div>
      </div>

      {clearSuccess && (
        <div className="fixed bottom-6 right-6 bg-green-600 text-white px-4 py-2 rounded">
          <Check className="h-4 w-4 inline" /> Cleared
        </div>
      )}
    </div>
  );
}