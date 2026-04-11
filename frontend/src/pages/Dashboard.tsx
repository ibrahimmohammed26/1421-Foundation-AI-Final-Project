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
  PlusCircle,
} from "lucide-react";

// main URL used to open the page
const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

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

    return messages.filter(
      (m: { role: string }) => m.role === "user"
    ).length;
  } catch (err) {
    // something went wrong parsing, just ignore
    return 0;
  }
}

// this can be changed
export default function Dashboard() {
  const [stats, setStats] = useState<Stats>({
    feedback_count: 0,
    locations_count: 52,
    documents_count: 870,
  });

  const [loading, setLoading] = useState(true);
  const [conversationCount, setConversationCount] =
    useState(getConversationCount);

  useEffect(() => {
    fetch(`${API_URL}/api/stats`)
      .then((res) => res.json())
      .then((data) => {
        setStats(data);
      })
      .catch((err) => {
        console.error("Failed to fetch stats", err);
      })
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
        "Ask questions about Zheng He's voyages or Ming dynasty history. The AI only uses the 1421 Foundation data (not the internet), so answers come from real indexed documents. You’ll see citations you can click.",
      example:
        "Example: What was the significance of Zheng He's voyages?",
    },
    {
      icon: Map,
      title: "Explore the Data Map",
      description:
        "There’s an interactive map showing key locations from the voyages. Clicking a marker shows related documents from the dataset.",
      example: "Click any marker to see related research",
    },
    {
      icon: FileText,
      title: "Browse Documents",
      description: `You can go through about ${stats.documents_count} documents from the 1421 Foundation and related sources. Each one links back to where it came from.`,
      example: "Try searching by title or author",
    },
    {
      icon: Database,
      title: "Document Search",
      description:
        "Search is powered by FAISS, so it finds documents based on meaning, not just keywords. It doesn’t pull anything from outside sources.",
      example: `${stats.documents_count} documents indexed`,
    },
    {

      icon: Globe,
      title: "Citations in Answers",
      description:
        "Responses include references like [Document X]. You can click them to jump straight to the source. If nothing relevant is found, it won’t guess.",
      example: "Click citation badges in responses",
    },
    {
      icon: PlusCircle,
      title: "Request New Data",
      description:
        "If you know a useful source that isn’t included, you can submit it. URLs help, but even just a book or article name works.",
      example: "Go to Feedback and submit a Data Request",
    },
    {
      icon: Send,
      title: "Send Feedback",
      description:
        "You can report bugs or suggest features. Feedback goes to the team directly.",
      example: "Suggest a topic you'd like added",
    },
  ];

  const statCards = [
    {
      label: "AI Conversations",
      value: String(conversationCount),
      sub:
        conversationCount === 0
          ? "No chats yet"
          : `${conversationCount} question${
              conversationCount !== 1 ? "s" : ""
            }`,
      icon: MessageSquare,
    },

    {
      label: "Map Locations",
      value: String(stats.locations_count),
      sub: "Different regions",
      icon: Map,
    },
    {
      label: "Documents",
      value: loading ? "..." : String(stats.documents_count),
      sub: "Indexed",
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
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm">
        <h1 className="text-xl font-bold text-gray-900">
          Dashboard
        </h1>
        <p className="text-xs text-gray-400">
          1421 Foundation Research System
        </p>
      </div>


      <div className="flex-1 overflow-y-auto">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 px-6 py-5">
          {statCards.map(({ label, value, sub, icon: Icon }) => (
            <div
              key={label}
              className="bg-white rounded-xl border p-4 shadow-sm"
            >
              <div className="flex justify-between mb-2">
                <span className="text-xs text-gray-400">
                  {label}
                </span>
                <Icon className="h-4 w-4 text-gold" />
              </div>

              <p className="text-2xl font-bold text-gold">
                {value}
              </p>

              <p className="text-xs text-gray-400 mt-1">
                {sub}
              </p>
            </div>
          ))}
        </div>

        {/* Intro */}
        <div className="px-6 pb-4">
          <div className="bg-white rounded-xl border p-6 shadow-sm">
            <div className="flex gap-4">
              <div className="w-12 h-12 flex items-center justify-center">
                <BookOpen className="h-6 w-6 text-gold" />
              </div>

              <div>
                <h2 className="text-lg font-bold mb-2">
                  Welcome
                </h2>
                <p className="text-gray-600 text-sm">
                  This tool gives access to the 1421 Foundation
                  dataset, including research on Zheng He and
                  Chinese exploration. Everything shown comes from
                  stored documents, not the web.
                </p>
              </div>
            </div>
          </div>
        </div>


        {/* Guide */}
        <div className="px-6 pb-6">
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <Compass className="h-5 w-5 text-gold" />
            How it works
          </h2>

          <div className="space-y-3">
            {steps.map((step, index) => {
              const Icon = step.icon;

              return (
                <div
                  key={index}
                  className="flex gap-4 bg-white rounded-xl p-4 border"
                >
                  <div className="w-10 h-10 flex items-center justify-center">
                    <Icon className="h-5 w-5 text-gold" />
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold">
                      {step.title}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {step.description}
                    </p>
                    <p className="text-xs text-gold italic">
                      {step.example}
                    </p>
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