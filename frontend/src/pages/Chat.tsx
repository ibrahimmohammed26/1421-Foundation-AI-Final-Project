import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send, Copy, Check, FileText, Trash2,
  ChevronDown, ChevronUp,
} from "lucide-react";
import { streamChat, sendChatMessage } from "@/lib/api";

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

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

// ─────────────────────────────────────────────────────────────────────────────
// Global chat store — lives outside React so it survives page navigation
// The component subscribes via a simple listener pattern.
// ─────────────────────────────────────────────────────────────────────────────

const STORAGE_KEY = "1421_chat_messages";

function persistMessages(msgs: Message[]) {
  try {
    // Never persist a mid-stream placeholder
    const clean = msgs.map((m) => (m.streaming ? { ...m, streaming: false } : m));
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(clean));
  } catch {}
}

function restoreMessages(): Message[] {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return (JSON.parse(raw) as Message[]).map((m) =>
      m.streaming ? { ...m, streaming: false } : m
    );
  } catch {
    return [];
  }
}

type Listener = () => void;

const chatStore = {
  messages: restoreMessages() as Message[],
  isTyping: false,
  listeners: new Set<Listener>(),

  subscribe(fn: Listener) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  },

  notify() {
    this.listeners.forEach((fn) => fn());
  },

  setMessages(msgs: Message[]) {
    this.messages = msgs;
    persistMessages(msgs);
    this.notify();
  },

  setIsTyping(v: boolean) {
    this.isTyping = v;
    this.notify();
  },

  clear() {
    this.messages = [];
    this.isTyping = false;
    sessionStorage.removeItem(STORAGE_KEY);
    this.notify();
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Smart spacing — adds a space between letters and digits EXCEPT ordinals
// e.g. "1421AD" → "1421 AD", "early15th" → "early 15th", "15th" stays "15th"
// ─────────────────────────────────────────────────────────────────────────────

function smartSpace(text: string): string {
  return (
    text
      // letter → digit: always add a space
      .replace(/([a-zA-Z])(\d)/g, "$1 $2")
      // digit → letter: add a space ONLY if it is NOT an ordinal suffix
      .replace(/(\d)([a-zA-Z])/g, (match, digit, letter, offset, str) => {
        // look ahead: is the letter the start of th / st / nd / rd?
        const ahead = str.slice(offset + 1); // everything from the letter onward
        const isOrdinal = /^(th|st|nd|rd)(?:[^a-zA-Z]|$)/i.test(ahead);
        return isOrdinal ? digit + letter : digit + " " + letter;
      })
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// MessageContent — bold [Document N] + smart spacing
// ─────────────────────────────────────────────────────────────────────────────

function MessageContent({ content }: { content: string }) {
  const parts = content.split(/(\[Document\s*\d+\])/gi);
  return (
    <p className="text-sm leading-relaxed whitespace-pre-wrap">
      {parts.map((part, i) => {
        if (/^\[Document\s*\d+\]$/i.test(part)) {
          const normalised = part.replace(/\[Document\s*(\d+)\]/i, "[Document $1]");
          return <strong key={i}>{normalised}</strong>;
        }
        return <span key={i}>{smartSpace(part)}</span>;
      })}
    </p>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Chat component
// ─────────────────────────────────────────────────────────────────────────────

export default function Chat() {
  // Mirror global store into local state so React re-renders on changes
  const [messages, setMessagesLocal]   = useState<Message[]>(() => chatStore.messages);
  const [isTyping, setIsTypingLocal]   = useState(() => chatStore.isTyping);
  const [input, setInput]              = useState("");
  const [copiedIdx, setCopiedIdx]      = useState<number | null>(null);
  const [copiedAll, setCopiedAll]      = useState(false);
  const [expandedSources, setExpandedSources] = useState<Set<number>>(new Set());
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const endRef = useRef<HTMLDivElement>(null);

  // Subscribe to global store — re-render whenever store changes
  useEffect(() => {
    const unsub = chatStore.subscribe(() => {
      setMessagesLocal([...chatStore.messages]);
      setIsTypingLocal(chatStore.isTyping);
    });
    return () => {
      unsub();
    };
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── Send ──────────────────────────────────────────────────────────────────

  const handleSend = async (overrideText?: string) => {
    const text = (overrideText ?? input).trim();
    if (!text || chatStore.isTyping) return;

    setInput("");
    chatStore.setIsTyping(true);

    const userMsg: Message = { role: "user", content: text };
    const newMsgs = [...chatStore.messages, userMsg];

    chatStore.setMessages([...newMsgs, { role: "assistant", content: "", streaming: true }]);

    let content = "";

    await streamChat(
      newMsgs.map((m) => ({ role: m.role, content: m.content })),
      (chunk) => {
        // Stream continues even when component is unmounted (user navigated away)
        if (!chatStore.isTyping) return; // aborted
        content += chunk;
        chatStore.setMessages([...newMsgs, { role: "assistant", content, streaming: true }]);
      },
      async () => {
        if (!chatStore.isTyping) return;
        chatStore.setIsTyping(false);
        try {
          const full = await sendChatMessage(
            newMsgs.map((m) => ({ role: m.role, content: m.content })),
            undefined,
            true
          );
          chatStore.setMessages([
            ...newMsgs,
            {
              role: "assistant",
              content,
              sources: full.sources || [],
              streaming: false,
            },
          ]);
        } catch {
          chatStore.setMessages([...newMsgs, { role: "assistant", content, streaming: false }]);
        }
      },
      (err) => {
        if (!chatStore.isTyping) return;
        chatStore.setIsTyping(false);
        chatStore.setMessages([
          ...newMsgs,
          { role: "assistant", content: `Error: ${err}`, streaming: false },
        ]);
      }
    );
  };

  // ── Copy ──────────────────────────────────────────────────────────────────

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

  // ── Clear ─────────────────────────────────────────────────────────────────

  const handleClearRequest = () => setShowClearConfirm(true);

  const handleClearConfirmed = useCallback(() => {
    chatStore.clear(); // stops typing flag → stream callbacks bail out
    setInput("");
    setShowClearConfirm(false);
  }, []);

  // ── Sources ───────────────────────────────────────────────────────────────

  const toggleSources = (idx: number) => {
    setExpandedSources((prev) => {
      const next = new Set(prev);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });
  };

  // ─────────────────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────────────────

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
              onClick={handleClearRequest}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-300 text-xs font-medium text-red-600 hover:border-red-400 hover:bg-red-50 transition-colors bg-white"
            >
              <Trash2 className="h-3.5 w-3.5" /> Clear chat
            </button>
          </div>
        )}
      </div>

      {/* ── Messages ─────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">

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
                {showDots && (
                  <div className="flex items-center gap-1.5 py-1">
                    <div className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: "0ms" }} />
                    <div className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: "150ms" }} />
                    <div className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                )}

                {hasContent && (
                  msg.role === "assistant"
                    ? <MessageContent content={msg.content} />
                    : <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                )}

                {/* Action bar — only after streaming fully ends */}
                {msg.role === "assistant" && !isStreaming && hasContent && (
                  <>
                    <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-3 flex-wrap">

                      {/* Copy */}
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

                      {/* Sources toggle — left of view documents */}
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

                      {/* View documents */}
                      <a
                        href="/documents"
                        className="flex items-center gap-1.5 text-xs font-medium text-gold border border-gold/30 rounded-lg px-2.5 py-1 bg-red-50 hover:bg-red-100 transition-colors"
                      >
                        <FileText className="h-3.5 w-3.5" />
                        View documents
                      </a>
                    </div>

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

      {/* ── Clear Chat Confirmation Modal ─────────────────────────────── */}
      {showClearConfirm && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl border border-gray-200 p-6 max-w-sm w-full mx-4 shadow-2xl">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-red-50 border border-red-200 flex items-center justify-center flex-shrink-0">
                <Trash2 className="h-4 w-4 text-red-600" />
              </div>
              <h3 className="text-base font-display font-bold text-gray-900">Clear Chat?</h3>
            </div>
            <p className="text-sm text-gray-500 mb-1 leading-relaxed">
              This will permanently delete all messages in this conversation.
            </p>
            {isTyping && (
              <p className="text-sm text-amber-600 font-medium mb-4">
                The current response will also be stopped.
              </p>
            )}
            {!isTyping && <div className="mb-4" />}
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowClearConfirm(false)}
                className="px-4 py-2 rounded-lg border border-gray-200 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleClearConfirmed}
                className="px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-semibold hover:bg-red-700 transition-colors"
              >
                Clear all
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}