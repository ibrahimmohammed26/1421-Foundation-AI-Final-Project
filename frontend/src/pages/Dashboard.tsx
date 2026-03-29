import { useState, useEffect } from "react";
import {
  MessageSquare,
  Map,
  FileText,
  Send,
  BookOpen,
  Compass,
  Database,
  Globe,
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const STORAGE_KEY = "1421_chat_messages";

interface Stats {
  feedback_count: number;
  locations_count: number;
  documents_count: number;
}

function getConversationCount(): number {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return 0;
    const messages = JSON.parse(raw);
    return messages.filter((m: { role: string }) => m.role === "user").length;
  } catch {
    return 0;
  }
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats>({
    feedback_count: 0,
    locations_count: 17,
    documents_count: 299,
  });
  const [loading, setLoading] = useState(true);
  const [conversationCount, setConversationCount] = useState(getConversationCount);

  useEffect(() => {
    fetch(`${API_URL}/api/stats`)
      .then((r) => r.json())
      .then((data) => setStats(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setConversationCount(getConversationCount());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const steps = [
    {
      icon: MessageSquare,
      title: "Chat with AI Historian",
      description:
        "Ask questions about Zheng He's voyages, Ming dynasty history, or the 1421 Foundation research. The AI searches only the 1421 Foundation knowledge base — not the web. Every answer is grounded in the indexed documents, with inline citations you can click.",
      example: "Try: 'What was the significance of Zheng He's voyages?'",
    },
    {
      icon: Map,
      title: "Explore the Data Map",
      description:
        "View key locations from Zheng He's treasure fleet expeditions on an interactive map. Click any marker to see related research documents from the knowledge base.",
      example: "Click a location marker to explore related documents",
    },
    {
      icon: FileText,
      title: "Browse Research Documents",
      description: `Access the full knowledge base of ${stats.documents_count} documents from the 1421 Foundation, Gavin Menzies' research site, and related sources. Each document links directly to its original source.`,
      example: "Search by title, author, or document number",
    },
    {
      icon: Database,
      title: "Document-Only Search",
      description:
        "The system uses FAISS vector search to find semantically relevant documents from the knowledge base. It does not use web search or external data sources — all answers come exclusively from indexed documents.",
      example: `${stats.documents_count} documents indexed and searchable`,
    },
    {
      icon: Globe,
      title: "Inline Document Citations",
      description:
        "Every AI response cites its sources inline using [Document X] badges. Click any badge to jump directly to that document. If no relevant documents are found, the system will say so rather than guessing.",
      example: "Click [Document 1] badges in chat responses to view sources",
    },
    {
      icon: Send,
      title: "Submit Feedback",
      description:
        "Share your thoughts, report issues, or suggest new features to improve the platform.",
      example: "Let us know what historical topics you'd like to learn more about",
    },
  ];

  const statCards = [
    {
      label: "AI Conversations",
      value: String(conversationCount),
      sub: conversationCount === 0 ? "Start a new chat" : `${conversationCount} question${conversationCount !== 1 ? "s" : ""} asked`,
      icon: MessageSquare,
    },
    {
      label: "Map Locations",
      value: String(stats.locations_count),
      sub: "Across 3 continents",
      icon: Map,
    },
    {
      label: "Documents",
      value: loading ? "…" : String(stats.documents_count),
      sub: "In knowledge base",
      icon: FileText,
    },
    {
      label: "Feedback",
      value: String(stats.feedback_count),
      sub: "User submissions",
      icon: Send,
    },
  ];

  return (
    <div className="flex flex-col h-full bg-gray-100">

      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm flex-shrink-0">
        <h1 className="text-xl font-display font-bold text-gray-900">Dashboard</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Welcome to the 1421 Foundation Research System
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Stat cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 px-6 py-5">
          {statCards.map(({ label, value, sub, icon: Icon }) => (
            <div
              key={label}
              className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-400">{label}</span>
                <Icon className="h-4 w-4 text-gold" />
              </div>
              <p className="text-2xl font-display font-bold text-gold">{value}</p>
              <p className="text-xs text-gray-400 mt-1">{sub}</p>
            </div>
          ))}
        </div>

        {/* Welcome card */}
        <div className="px-6 pb-4">
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-red-50 border border-gold/20 flex items-center justify-center flex-shrink-0">
                <BookOpen className="h-6 w-6 text-gold" />
              </div>
              <div>
                <h2 className="text-lg font-display font-bold text-gray-900 mb-2">
                  Welcome to the 1421 Foundation Research System
                </h2>
                <p className="text-gray-600 text-sm leading-relaxed">
                  This platform provides AI-assisted access to the 1421 Foundation's knowledge base, covering Chinese maritime exploration during the Ming dynasty (1368–1644), the voyages of Admiral Zheng He, and the research of Gavin Menzies. All AI responses are sourced exclusively from indexed documents — the system does not search the web or rely on external knowledge.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* How to use */}
        <div className="px-6 pb-6">
          <h2 className="text-lg font-display font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Compass className="h-5 w-5 text-gold" />
            How to Use Guide
          </h2>
          <div className="space-y-3">
            {steps.map((step, index) => {
              const Icon = step.icon;
              return (
                <div
                  key={index}
                  className="flex gap-4 bg-white rounded-xl p-4 border border-gray-200 shadow-sm hover:border-gold/30 hover:shadow-md transition-all"
                >
                  <div className="w-10 h-10 rounded-full bg-red-50 border border-gold/20 flex items-center justify-center flex-shrink-0">
                    <Icon className="h-5 w-5 text-gold" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-semibold text-gray-900 mb-1">{step.title}</h3>
                    <p className="text-sm text-gray-500 mb-1.5">{step.description}</p>
                    <p className="text-xs text-gold italic">{step.example}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}