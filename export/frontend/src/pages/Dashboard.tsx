import { useState, useEffect } from "react";
import { 
  MessageSquare, 
  Map, 
  FileText, 
  Send,
  ChevronRight,
  BookOpen,
  Compass,
  History,
  Database,
  Globe
} from "lucide-react";
import { fetchStats } from "@/lib/api";

interface Stats {
  feedback_count: number;
  locations_count: number;
  documents_count: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats>({
    feedback_count: 0,
    locations_count: 14,
    documents_count: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const data = await fetchStats();
        setStats(data);
      } catch (error) {
        console.error('Error loading stats:', error);
      } finally {
        setLoading(false);
      }
    };
    loadStats();
  }, []);

  const steps = [
    {
      icon: MessageSquare,
      title: "Chat with AI Historian",
      description: "Ask questions about Zheng He's voyages, Ming dynasty history, or the 1421 hypothesis. The AI searches both its training data and our document database.",
      example: "Try: 'What was the significance of Zheng He's voyages?'"
    },
    {
      icon: Map,
      title: "Explore the Voyage Map",
      description: "View animated routes of the treasure fleet expeditions. Click play to see the voyages unfold chronologically.",
      example: "Watch the fleet's journey from 1405 to 1433"
    },
    {
      icon: FileText,
      title: "Browse Research Documents",
      description: "Access historical documents, academic papers, and books from our vector database. Search semantically or filter by metadata.",
      example: "Search for 'Ming dynasty shipbuilding techniques'"
    },
    {
      icon: Database,
      title: "Vector Database Integration",
      description: "The system uses FAISS vector search to find relevant documents and knowledge base entries for more accurate responses.",
      example: `${stats.documents_count} documents available in the knowledge base`
    },
    {
      icon: Globe,
      title: "Web + Document Hybrid Search",
      description: "AI combines its training data with our local document database to provide comprehensive, accurate answers.",
      example: "Get responses grounded in both general knowledge and specific research documents"
    },
    {
      icon: Send,
      title: "Submit Feedback",
      description: "Share your thoughts, report issues, or suggest new features to improve the platform.",
      example: "Let us know what historical topics you'd like to learn more about"
    }
  ];

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="border-b border-gray-200 px-6 py-4 bg-white">
        <h1 className="text-xl font-display font-bold text-gold">Dashboard</h1>
        <p className="text-xs text-gray-600 mt-0.5">
          Welcome to the 1421 Foundation Research System
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 px-6 py-4 bg-white">
        <div className="bg-gray-50 rounded-xl border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-600">AI Conversations</span>
            <MessageSquare className="h-4 w-4 text-gold" />
          </div>
          <p className="text-2xl font-display font-bold text-navy-dark">0</p>
          <p className="text-xs text-gray-500 mt-1">Start a new chat</p>
        </div>
        <div className="bg-gray-50 rounded-xl border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-600">Voyage Locations</span>
            <Map className="h-4 w-4 text-gold" />
          </div>
          <p className="text-2xl font-display font-bold text-navy-dark">{stats.locations_count}</p>
          <p className="text-xs text-gray-500 mt-1">Across 3 continents</p>
        </div>
        <div className="bg-gray-50 rounded-xl border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-600">Documents</span>
            <FileText className="h-4 w-4 text-gold" />
          </div>
          <p className="text-2xl font-display font-bold text-navy-dark">{stats.documents_count}</p>
          <p className="text-xs text-gray-500 mt-1">In vector database</p>
        </div>
        <div className="bg-gray-50 rounded-xl border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-600">Feedback</span>
            <Send className="h-4 w-4 text-gold" />
          </div>
          <p className="text-2xl font-display font-bold text-navy-dark">{stats.feedback_count}</p>
          <p className="text-xs text-gray-500 mt-1">User submissions</p>
        </div>
      </div>

      {/* Welcome Card */}
      <div className="px-6 py-2">
        <div className="bg-gray-50 rounded-xl border border-gray-200 p-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-gold/20 flex items-center justify-center flex-shrink-0">
              <BookOpen className="h-6 w-6 text-gold" />
            </div>
            <div>
              <h2 className="text-lg font-display font-bold text-navy-dark mb-2">
                Welcome to the 1421 Foundation
              </h2>
              <p className="text-gray-700 text-sm leading-relaxed">
                This research platform combines a vector database of historical documents with AI to provide 
                accurate information about Chinese maritime exploration during the Ming dynasty (1368–1644), 
                particularly the voyages of Admiral Zheng He and the controversial 1421 hypothesis.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* How to Use Guide */}
      <div className="flex-1 overflow-y-auto px-6 py-4 bg-white">
        <h2 className="text-lg font-display font-bold text-navy-dark mb-4 flex items-center gap-2">
          <Compass className="h-5 w-5 text-gold" />
          How to Use Guide
        </h2>
        <div className="space-y-4">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div key={index} className="flex gap-4 bg-gray-50 rounded-xl p-4 border border-gray-200">
                <div className="relative">
                  <div className="w-10 h-10 rounded-full bg-gold/20 flex items-center justify-center flex-shrink-0">
                    <Icon className="h-5 w-5 text-gold" />
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="text-md font-semibold text-navy-dark mb-1">
                    Step {index + 1}: {step.title}
                  </h3>
                  <p className="text-sm text-gray-600 mb-2">{step.description}</p>
                  <p className="text-xs text-gold italic">{step.example}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}