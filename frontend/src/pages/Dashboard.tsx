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

interface Stats {
  feedback_count: number;
  locations_count: number;
  documents_count: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats>({
    feedback_count: 0,
    locations_count: 14,
    documents_count: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/stats")
      .then((r) => r.json())
      .then((data) => setStats(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const steps = [
    {
      icon: MessageSquare,
      title: "Chat with AI Historian",
      description:
        "Ask questions about Zheng He's voyages, Ming dynasty history, or the 1421 Foundation research. The AI searches both its training data and our document database.",
      example: "Try: 'What was the significance of Zheng He's voyages?'",
    },
    {
      icon: Map,
      title: "Explore the Voyage Map",
      description:
        "View animated routes of the treasure fleet expeditions. Click play to see the voyages unfold chronologically.",
      example: "Watch the fleet's journey from 1368 to 1421",
    },
    {
      icon: FileText,
      title: "Browse Research Documents",
      description: `Access historical documents, academic papers, and books from our vector database. Currently ${stats.documents_count} documents available.`,
      example: "Search for 'Ming dynasty shipbuilding techniques'",
    },
    {
      icon: Database,
      title: "Vector Database Integration",
      description:
        "The system uses FAISS vector search to find relevant documents and knowledge base entries for more accurate responses.",
      example: `${stats.documents_count} documents indexed and searchable`,
    },
    {
      icon: Globe,
      title: "Web + Document Hybrid Search",
      description:
        "AI combines its training data with our local document database to provide comprehensive, accurate answers.",
      example:
        "Get responses grounded in both general knowledge and specific research documents",
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
    { label: "AI Conversations", value: "0",    sub: "Start a new chat",    icon: MessageSquare },
    { label: "Voyage Locations", value: String(stats.locations_count), sub: "Across 3 continents", icon: Map },
    { label: "Documents",        value: loading ? "…" : String(stats.documents_count), sub: "In vector database", icon: FileText },
    { label: "Feedback",         value: String(stats.feedback_count), sub: "User submissions",   icon: Send },
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
                  Welcome to the 1421 Foundation
                </h2>
                <p className="text-gray-600 text-sm leading-relaxed">
                  This research platform combines a vector database of historical documents with AI
                  to provide accurate information about Chinese maritime exploration during the Ming
                  dynasty (1368–1644), particularly the voyages of Admiral Zheng He and the 1421
                  Foundation.
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