import { useState, useRef, useEffect } from "react";
import {
  Send, Copy, Check, FileText, Trash2,
  ChevronDown, ChevronUp,
} from "lucide-react";
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
  const [messages, setMessages]               = useState<Message[]>([]);
  const [input, setInput]                     = useState("");
  const [isTyping, setIsTyping]               = useState(false);
  const [copiedIdx, setCopiedIdx]             = useState<number | null>(null);
  const [copiedAll, setCopiedAll]             = useState(false);
  const [expandedSources, setExpandedSources] = useState<Set<number>>(new Set());
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (overrideText?: string) => {
    const text = (overrideText ?? input).trim();
    if (!text || isTyping) return;

    setInput("");
    setIsTyping(true);

    const userMsg: Message = { role: "user", content: text };
    const newMsgs = [...messages, userMsg];

    // Add streaming placeholder — dots show until first chunk arrives
    setMessages([...newMsgs, { role: "assistant", content: "", streaming: true }]);

    let content = "";

    await streamChat(
      newMsgs.map((m) => ({ role: m.role, content: m.content })),
      (chunk) => {
        content += chunk;
        // Once first chunk arrives dots disappear, text streams in naturally
        setMessages([...newMsgs, { role: "assistant", content, streaming: true }]);
      },
      async () => {
        setIsTyping(false);
        // Fetch sources after streaming completes
        try {
          const full = await sendChatMessage(
            newMsgs.map((m) => ({ role: m.role, content: m.content })),
            undefined,
            true
          );
          setMessages([
            ...newMsgs,
            {
              role: "assistant",
              content,
              sources: full.sources || [],
              streaming: false,
            },
          ]);
        } catch {
          setMessages([...newMsgs, { role: "assistant", content, streaming: false }]);
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

  const handleCopyAll = () => {
    const full = messages
      .map((m) => `${m.role === "user" ? "You" : "1421 AI"}: ${m.content}`)
      .join("\n\n");
    navigator.clipboard.writeText(full);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2000);
  };

  const handleClear = () => {
    setMessages([]);
    setInput("");
  };

  const toggleSources = (idx: number) => {
    setExpandedSources((prev) => {
      const next = new Set(prev);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });
  };

  const STARTERS = [
    "What was the significance of Zheng He's voyages?",
    "Describe Ming Dynasty naval technology",
    "Is there evidence of Chinese ships reaching America?",
    "How did Chinese navigation compare to European methods?",
  ];

  const hasMessages = messages.length > 0;

  return (
    <div className="flex flex-col h-full bg-gray-100">

      {/* ── Header ───────────────────────────────────────────────────── */}
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm flex-shrink-0 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-display font-bold text-black">1421 AI Chat</h1>
          <p className="text-xs text-black mt-0.5">
            Ask about Chinese exploration &amp; the 1421 theory
          </p>
        </div>

        {/* Toolbar — only shown when conversation has started */}
        {hasMessages && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyAll}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-300 text-xs font-medium text-black hover:border-gold hover:text-gold transition-colors bg-white"
            >
              {copiedAll ? (
                <><Check className="h-3.5 w-3.5 text-emerald-600" /><span className="text-emerald-600">Copied</span></>
              ) : (
                <><Copy className="h-3.5 w-3.5" /> Copy all</>
              )}
            </button>
            <button
              onClick={handleClear}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-300 text-xs font-medium text-black hover:border-red-400 hover:text-red-600 transition-colors bg-white"
            >
              <Trash2 className="h-3.5 w-3.5" /> Clear chat
            </button>
          </div>
        )}
      </div>

      {/* ── Messages ─────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">

        {/* Welcome screen */}
        {!hasMessages && (
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
                  onClick={() => handleSend(q)}
                  className="text-left rounded-xl border border-gray-200 bg-white p-3 text-sm text-black hover:border-gold hover:bg-red-50 transition-all shadow-sm"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message list */}
        {messages.map((msg, idx) => {
          const isStreaming = msg.streaming === true;
          const hasContent  = msg.content.trim().length > 0;
          const showDots    = isStreaming && !hasContent;
          const showSources = expandedSources.has(idx);
          const sourceCount = msg.sources?.length ?? 0;

          return (
            <div
              key={idx}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[78%] rounded-2xl px-5 py-4 ${
                  msg.role === "user"
                    ? "bg-gold text-white rounded-br-md shadow-sm"
                    : "bg-white border border-gray-200 text-black rounded-bl-md shadow-sm"
                }`}
              >
                {/* Dots — only before first character arrives */}
                {showDots && (
                  <div className="flex items-center gap-1.5 py-1">
                    <div className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: "0ms" }} />
                    <div className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: "150ms" }} />
                    <div className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                )}

                {/* Message text — dots gone once content starts arriving */}
                {hasContent && (
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">
                    {msg.content}
                  </p>
                )}

                {/* Action bar — only after streaming fully ends */}
                {msg.role === "assistant" && !isStreaming && hasContent && (
                  <>
                    <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-3 flex-wrap">

                      {/* Copy this message */}
                      <button
                        onClick={() => handleCopy(msg.content, idx)}
                        className="flex items-center gap-1.5 text-xs font-medium text-black hover:text-gold transition-colors"
                      >
                        {copiedIdx === idx ? (
                          <><Check className="h-3.5 w-3.5 text-emerald-600" /><span className="text-emerald-600">Copied</span></>
                        ) : (
                          <><Copy className="h-3.5 w-3.5" /> Copy</>
                        )}
                      </button>

                      {/* View all documents — links to Documents page */}
                      <a
                        href="/documents"
                        className="flex items-center gap-1.5 text-xs font-medium text-gold border border-gold/30 rounded-lg px-2.5 py-1 bg-red-50 hover:bg-red-100 transition-colors"
                      >
                        <FileText className="h-3.5 w-3.5" />
                        View documents
                      </a>

                      {/* Inline sources toggle */}
                      {sourceCount > 0 && (
                        <button
                          onClick={() => toggleSources(idx)}
                          className="flex items-center gap-1.5 text-xs font-medium text-black hover:text-gold transition-colors"
                        >
                          {showSources ? (
                            <><ChevronUp className="h-3.5 w-3.5" /> Hide sources</>
                          ) : (
                            <><ChevronDown className="h-3.5 w-3.5" /> {sourceCount} source{sourceCount > 1 ? "s" : ""}</>
                          )}
                        </button>
                      )}
                    </div>

                    {/* Expanded sources panel */}
                    {showSources && sourceCount > 0 && (
                      <div className="mt-3 space-y-2">
                        {msg.sources!.map((src, sIdx) => (
                          <div
                            key={sIdx}
                            className="bg-gray-50 rounded-lg border border-gray-200 px-3 py-2"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex items-center gap-2 min-w-0">
                                <FileText className="h-3.5 w-3.5 text-gold flex-shrink-0 mt-0.5" />
                                <div className="min-w-0">
                                  <p className="text-xs font-semibold text-black truncate">
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
                              {src.similarity != null && (
                                <span className="text-xs font-semibold text-gold flex-shrink-0 bg-red-50 px-1.5 py-0.5 rounded border border-gold/20">
                                  {Math.round(src.similarity * 100)}%
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                        <p className="text-xs text-black">
                          These documents were retrieved from the knowledge base to inform this response.
                        </p>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          );
        })}

        <div ref={endRef} />
      </div>

      {/* ── Input ────────────────────────────────────────────────────── */}
      <div className="border-t border-gray-200 px-6 py-4 bg-white flex-shrink-0">
        <div className="flex items-end gap-3 max-w-3xl mx-auto">
          <div className="flex-1 relative">
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
              className="w-full resize-none rounded-xl border border-gray-300 bg-white px-4 py-3 pr-16 text-sm text-black placeholder:text-black focus:outline-none focus:ring-2 focus:ring-gold/40 focus:border-gold"
            />
            {input.length > 0 && (
              <span className="absolute bottom-3 right-3 text-xs text-black pointer-events-none">
                {input.length}
              </span>
            )}
          </div>
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isTyping}
            className="h-11 w-11 rounded-xl bg-gold text-white disabled:opacity-40 hover:bg-gold-light transition flex items-center justify-center flex-shrink-0 shadow-sm"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
        <p className="text-xs text-black text-center mt-2">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}