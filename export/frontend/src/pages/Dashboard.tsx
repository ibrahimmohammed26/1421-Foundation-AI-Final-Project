import { useState } from "react";
import { 
  MessageSquare, 
  Map, 
  FileText, 
  Send,
  ChevronRight,
  BookOpen,
  Compass,
  History
} from "lucide-react";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<"overview" | "guide">("overview");

  const steps = [
    {
      icon: MessageSquare,
      title: "Ask the AI Historian",
      description: "Go to the Chat page and ask questions about Zheng He's voyages, Ming dynasty history, or the 1421 hypothesis.",
      example: "Try: 'What was the significance of Zheng He's voyages?'"
    },
    {
      icon: Map,
      title: "Explore the Voyage Map",
      description: "View all locations visited during the treasure fleet expeditions. Toggle between terrain and satellite views.",
      example: "Zoom in on Southeast Asia to see detailed route information"
    },
    {
      icon: FileText,
      title: "Browse Research Documents",
      description: "Access historical documents, academic papers, and books about Chinese maritime exploration.",
      example: "Filter documents by type or search for specific topics"
    },
    {
      icon: History,
      title: "View Analytics",
      description: "Explore voyage statistics, timeline data, and historical insights from the expeditions.",
      example: "See distribution of voyages by year and region"
    },
    {
      icon: Send,
      title: "Submit Feedback",
      description: "Share your thoughts, report issues, or suggest new features to improve the platform.",
      example: "Let us know what historical topics you'd like to learn more about"
    }
  ];

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-gray-700 px-6 py-4">
        <h1 className="text-xl font-display font-bold text-gold">Dashboard</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Welcome to the 1421 Foundation Research System
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-700 px-6">
        <div className="flex gap-6">
          <button
            onClick={() => setActiveTab("overview")}
            className={`py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "overview"
                ? "border-gold text-gold"
                : "border-transparent text-gray-400 hover:text-gray-300"
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab("guide")}
            className={`py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "guide"
                ? "border-gold text-gold"
                : "border-transparent text-gray-400 hover:text-gray-300"
            }`}
          >
            How to Use Guide
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        {activeTab === "overview" ? (
          /* Overview Section */
          <div className="space-y-6">
            {/* Welcome Card */}
            <div className="bg-navy rounded-xl border border-gray-700 p-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-gold/20 flex items-center justify-center flex-shrink-0">
                  <BookOpen className="h-6 w-6 text-gold" />
                </div>
                <div>
                  <h2 className="text-lg font-display font-bold text-gold mb-2">
                    Welcome to the 1421 Foundation
                  </h2>
                  <p className="text-gray-300 text-sm leading-relaxed">
                    This research platform is dedicated to exploring Chinese maritime exploration during 
                    the Ming dynasty (1368–1644), particularly the voyages of Admiral Zheng He and the 
                    controversial 1421 hypothesis by Gavin Menzies. Use the AI historian to ask questions, 
                    explore interactive maps, and access research documents.
                  </p>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-navy rounded-xl border border-gray-700 p-5">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm text-gray-400">AI Conversations</h3>
                  <MessageSquare className="h-4 w-4 text-gold" />
                </div>
                <p className="text-2xl font-display font-bold text-gold">0</p>
                <p className="text-xs text-gray-500 mt-1">Start a new chat</p>
              </div>
              <div className="bg-navy rounded-xl border border-gray-700 p-5">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm text-gray-400">Voyage Locations</h3>
                  <Map className="h-4 w-4 text-gold" />
                </div>
                <p className="text-2xl font-display font-bold text-gold">14</p>
                <p className="text-xs text-gray-500 mt-1">Across 3 continents</p>
              </div>
              <div className="bg-navy rounded-xl border border-gray-700 p-5">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm text-gray-400">Research Documents</h3>
                  <FileText className="h-4 w-4 text-gold" />
                </div>
                <p className="text-2xl font-display font-bold text-gold">5</p>
                <p className="text-xs text-gray-500 mt-1">And growing</p>
              </div>
            </div>
          </div>
        ) : (
          /* How to Use Guide Section */
          <div className="space-y-6">
            <div className="bg-navy rounded-xl border border-gray-700 p-6">
              <h2 className="text-lg font-display font-bold text-gold mb-4 flex items-center gap-2">
                <Compass className="h-5 w-5" />
                Getting Started Guide
              </h2>
              <div className="space-y-6">
                {steps.map((step, index) => {
                  const Icon = step.icon;
                  return (
                    <div key={index} className="flex gap-4">
                      <div className="relative">
                        <div className="w-8 h-8 rounded-full bg-gold/20 flex items-center justify-center flex-shrink-0">
                          <Icon className="h-4 w-4 text-gold" />
                        </div>
                        {index < steps.length - 1 && (
                          <div className="absolute top-8 left-4 w-0.5 h-12 bg-gray-700" />
                        )}
                      </div>
                      <div className="flex-1 pb-6">
                        <h3 className="text-md font-semibold text-gray-200 mb-1">
                          Step {index + 1}: {step.title}
                        </h3>
                        <p className="text-sm text-gray-400 mb-2">{step.description}</p>
                        <p className="text-xs text-gold italic">{step.example}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="bg-navy rounded-xl border border-gray-700 p-6">
              <h3 className="text-md font-semibold text-gray-200 mb-3">Pro Tips</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li className="flex items-start gap-2">
                  <ChevronRight className="h-4 w-4 text-gold flex-shrink-0 mt-0.5" />
                  <span>Use specific historical questions for better AI responses</span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight className="h-4 w-4 text-gold flex-shrink-0 mt-0.5" />
                  <span>Toggle map layers to see different types of geographical data</span>
                </li>
                <li className="flex items-start gap-2">
                  <ChevronRight className="h-4 w-4 text-gold flex-shrink-0 mt-0.5" />
                  <span>Save interesting documents for later reference</span>
                </li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}