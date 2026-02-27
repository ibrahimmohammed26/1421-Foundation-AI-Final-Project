import { useState, useRef, useEffect } from "react";
import { Send, Copy, Check, FileText, ExternalLink } from "lucide-react";
import { streamChat, sendChatMessage } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  streaming?: boolean;
}

interface Source {
  title: string;
  author: string;
  year: number;
  type: string;
  similarity?: number;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const [expandedSources, setExpandedSources] = useState<number[]>([]);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;

    const userMsg: Message = { role: "user", content: input.trim() };
    const newMsgs = [...messages, userMsg];
    setMessages(newMsgs);
    setInput("");
    setIsTyping(true);

    // Add placeholder assistant message while streaming
    const assistantIdx = newMsgs.length;
    setMessages([...newMsgs, { role: "assistant", content: "", streaming: true }]);

    let content = "";

    await streamChat(
      newMsgs.map((m) => ({ role: m.role, content: m.content })),
      (chunk) => {
        content += chunk;
        setMessages([
          ...newMsgs,
          { role: "assistant", content, streaming: true },
        ]);
      },
      async () => {
        // Streaming done — now fetch sources via non-streaming endpoint
        setIsTyping(false);
        try {
          const full = await sendChatMessage(
            newMsgs.map((m) => ({ role: m.role, content: m.content })),
            undefined,
            true
          );
          // Update message with sources, mark streaming done
          setMessages([
            ...newMsgs,
            {
              role: "assistant",
              content,          // keep streamed text
              sources: full.sources || [],
              streaming: false,
            },
          ]);
        } catch {
          // Sources fetch failed — still show message without sources
          setMessages([
            ...newMsgs,
            { role: "assistant", content, streaming: false },
          ]);
        }
      },
      (err) => {
        setIsTyping(false);
        setMessages([
          ...newMsgs,
          { role: "assistant", content: `Error: ${err}`, streaming: false },
        ]);
      }
    );
  };

  const handleCopy = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  const toggleSources = (idx: number) => {
    setExpandedSources((prev) =>
      prev.includes(idx) ? prev.filter((i) => i !== idx) : [...prev, idx]
    );
  };

  const STARTERS = [
    "What was the significance of Zheng He's voyages?",
    "Describe Ming Dynasty naval technology",
    "Is there evidence of Chinese ships reaching America?",
    "How did Chinese navigation compare to European methods?",
  ];

  return (
    <div className="flex flex-col h-full bg-gray-100">

      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm flex-shrink-0">
        <h1 className="text-xl font-display font-bold text-black">1421 AI Chat</h1>
        <p className="text-xs text-black mt-0.5">
          Ask about Chinese exploration &amp; the 1421 theory
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
        {messages.length === 0 && !isTyping && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-20 h-20 rounded-2xl bg-gold flex items-center justify-center mb-5 shadow-md">
              <span className="text-xl font-display font-bold text-white tracking-tight leading-none">
                1421
              </span>
            </div>
            <h2 className="text-2xl font-display font-bold text-black mb-2">
              Welcome to 1421 AI
            </h2>
            <p className="text-black max-w-md mb-6">
              Ask any question about Chinese maritime exploration.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
              {STARTERS.map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="text-left rounded-xl border border-gray-200 bg-white p-3 text-sm text-black hover:border-gold hover:bg-red-50 transition-all shadow-sm"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[75%] rounded-2xl px-5 py-4 ${
                msg.role === "user"
                  ? "bg-gold text-white rounded-br-md shadow-sm"
                  : "bg-white border border-gray-200 text-black rounded-bl-md shadow-sm"
              }`}
            >
              {/* Message text */}
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>

              {/* Typing indicator inside bubble while streaming */}
              {msg.streaming && msg.content === "" && (
                <div className="flex items-center gap-1.5 py-1">
                  <div className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: "0ms" }} />
                  <div className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: "150ms" }} />
                  <div className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              )}

              {/* Actions — only show when streaming is done */}
              {msg.role === "assistant" && !msg.streaming && msg.content && (
                <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-3 flex-wrap">

                  {/* Copy button */}
                  <button
                    onClick={() => handleCopy(msg.content, idx)}
                    className="flex items-center gap-1.5 text-xs text-black hover:text-gold transition-colors font-medium"
                  >
                    {copiedIdx === idx ? (
                      <><Check className="h-3.5 w-3.5 text-emerald-600" /><span className="text-emerald-600">Copied</span></>
                    ) : (
                      <><Copy className="h-3.5 w-3.5" /> Copy</>
                    )}
                  </button>

                  {/* Sources / document link button */}
                  {msg.sources && msg.sources.length > 0 && (
                    <button
                      onClick={() => toggleSources(idx)}
                      className="flex items-center gap-1.5 text-xs text-gold hover:text-gold-dark transition-colors font-medium border border-gold/30 rounded-lg px-2.5 py-1 bg-red-50 hover:bg-red-100"
                    >
                      <FileText className="h-3.5 w-3.5" />
                      {expandedSources.includes(idx)
                        ? "Hide sources"
                        : `View ${msg.sources.length} source${msg.sources.length > 1 ? "s" : ""}`}
                    </button>
                  )}
                </div>
              )}

              {/* Sources panel — expands below the action row */}
              {msg.role === "assistant" &&
                !msg.streaming &&
                msg.sources &&
                expandedSources.includes(idx) && (
                  <div className="mt-3 space-y-2">
                    {msg.sources.map((src, sIdx) => (
                      <div
                        key={sIdx}
                        className="bg-gray-50 rounded-lg border border-gray-200 px-3 py-2"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-center gap-2 min-w-0">
                            <FileText className="h-3.5 w-3.5 text-gold flex-shrink-0 mt-0.5" />
                            <div className="min-w-0">
                              <p className="text-xs font-semibold text-black leading-snug truncate">
                                {src.title}
                              </p>
                              <p className="text-xs text-black mt-0.5">
                                {[
                                  src.author !== "Unknown" && src.author,
                                  src.year > 0 && src.year,
                                  src.type && src.type !== "unknown" && src.type,
                                ]
                                  .filter(Boolean)
                                  .join(" · ")}
                              </p>
                            </div>
                          </div>
                          {/* Similarity score */}
                          {src.similarity != null && (
                            <span className="text-xs font-semibold text-gold flex-shrink-0 bg-red-50 px-1.5 py-0.5 rounded border border-gold/20">
                              {Math.round(src.similarity * 100)}%
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                    <p className="text-xs text-black mt-1">
                      These documents were retrieved from the knowledge base to inform this response.
                    </p>
                  </div>
                )}
            </div>
          </div>
        ))}

        {/* Standalone typing indicator (before first chunk arrives) */}
        {isTyping && messages[messages.length - 1]?.content === "" && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-md px-5 py-4 shadow-sm">
              <div className="flex items-center gap-1.5">
                <div className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}

        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 px-6 py-4 bg-white flex-shrink-0">
        <div className="flex items-end gap-3 max-w-3xl mx-auto">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask a question…"
            rows={1}
            className="flex-1 resize-none rounded-xl border border-gray-300 bg-white px-4 py-3 text-sm text-black placeholder:text-black focus:outline-none focus:ring-2 focus:ring-gold/40 focus:border-gold"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            className="h-11 w-11 rounded-xl bg-gold text-white disabled:opacity-40 hover:bg-gold-light transition flex items-center justify-center flex-shrink-0 shadow-sm"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}