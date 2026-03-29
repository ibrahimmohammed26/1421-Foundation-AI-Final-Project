import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Send, Copy, Check, FileText, Trash2,
  ChevronDown, ChevronUp, Square,
} from "lucide-react";
import { streamChat } from "@/lib/api";

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

const STORAGE_KEY = "1421_chat_messages";

function persistMessages(msgs: Message[]) {
  try {
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
  subscribe(fn: Listener) { this.listeners.add(fn); return () => this.listeners.delete(fn); },
  notify() { this.listeners.forEach((fn) => fn()); },
  setMessages(msgs: Message[]) { this.messages = msgs; persistMessages(msgs); this.notify(); },
  setIsTyping(v: boolean) { this.isTyping = v; this.notify(); },
  clear() {
    this.messages = [];
    this.isTyping = false;
    sessionStorage.removeItem(STORAGE_KEY);
    this.notify();
  },
};

window.addEventListener("storage", () => {
  if (!sessionStorage.getItem(STORAGE_KEY)) {
    chatStore.clear();
  }
});

function deduplicateSources(sources: Source[]): Source[] {
  const seen = new Set<string>();
  return (sources || []).filter((s) => {
    const key = s.title?.trim().toLowerCase();
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

// Renders message content, turning [Document X] into clickable gold links
function MessageContent({
  content,
  sources,
  onDocClick,
}: {
  content: string;
  sources: Source[];
  onDocClick: (docNum: number) => void;
}) {
  // Split on [Document N] or [Document N][Document M] patterns
  const parts = content.split(/(\[Document\s*\d+\](?:\[Document\s*\d+\])*)/gi);

  return (
    <div className="text-sm leading-relaxed whitespace-pre-wrap space-y-0">
      {parts.map((part, i) => {
        // Check if this part contains document references
        const docRefs = [...part.matchAll(/\[Document\s*(\d+)\]/gi)];
        if (docRefs.length > 0) {
          return (
            <span key={i}>
              {docRefs.map((ref, j) => {
                const docNum = parseInt(ref[1], 10);
                const source = sources[docNum - 1];
                return (
                  <button
                    key={j}
                    onClick={() => onDocClick(docNum)}
                    title={source ? source.title : `Document ${docNum}`}
                    className="inline-flex items-center gap-0.5 mx-0.5 px-1.5 py-0.5 rounded bg-red-50 border border-gold/40 text-gold text-xs font-semibold hover:bg-red-100 hover:border-gold transition-colors"
                  >
                    <FileText className="h-3 w-3" />
                    {docNum}
                  </button>
                );
              })}
            </span>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </div>
  );
}

export default function Chat() {
  const navigate = useNavigate();

  const [messages, setMessagesLocal]   = useState<Message[]>(() => chatStore.messages);
  const [isTyping, setIsTypingLocal]   = useState(() => chatStore.isTyping);
  const [input, setInput]              = useState("");
  const [copiedIdx, setCopiedIdx]      = useState<number | null>(null);
  const [copiedAll, setCopiedAll]      = useState(false);
  const [expandedSources, setExpandedSources] = useState<Set<number>>(new Set());
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const endRef      = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const unsub = chatStore.subscribe(() => {
      setMessagesLocal([...chatStore.messages]);
      setIsTypingLocal(chatStore.isTyping);
    });
    return () => { unsub(); };
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    const maxH = 200;
    el.style.height = Math.min(el.scrollHeight, maxH) + "px";
    el.style.overflowY = el.scrollHeight > maxH ? "auto" : "hidden";
  }, [input]);

  const handleStop = useCallback(() => {
    chatStore.setIsTyping(false);
    const msgs = chatStore.messages;
    if (msgs.length > 0 && msgs[msgs.length - 1].streaming) {
      chatStore.setMessages(
        msgs.map((m, i) => i === msgs.length - 1 ? { ...m, streaming: false } : m)
      );
    }
  }, []);

  const handleSend = async (overrideText?: string) => {
    const text = (overrideText ?? input).trim();
    if (!text || chatStore.isTyping) return;
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    chatStore.setIsTyping(true);

    const userMsg: Message = { role: "user", content: text };
    const newMsgs = [...chatStore.messages, userMsg];
    chatStore.setMessages([...newMsgs, { role: "assistant", content: "", streaming: true }]);

    let content = "";

    await streamChat(
      newMsgs.map((m) => ({ role: m.role, content: m.content })),
      (chunk) => {
        if (!chatStore.isTyping) return;
        content += chunk;
        chatStore.setMessages([...newMsgs, { role: "assistant", content, streaming: true }]);
      },
      (streamSources) => {
        if (!chatStore.isTyping) return;
        chatStore.setIsTyping(false);
        const uniqueSources = deduplicateSources(streamSources || []);
        chatStore.setMessages([
          ...newMsgs,
          { role: "assistant", content, sources: uniqueSources, streaming: false },
        ]);
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

  const handleClearConfirmed = useCallback(() => {
    chatStore.clear();
    setInput("");
    setShowClearConfirm(false);
  }, []);

  const toggleSources = (idx: number) => {
    setExpandedSources((prev) => {
      const next = new Set(prev);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });
  };

  // When a [Document X] badge is clicked, navigate to that document
  const handleDocClick = (sources: Source[], docNum: number) => {
    const source = sources[docNum - 1];
    if (source) {
      navigate(`/documents?search=${encodeURIComponent(source.title)}`);
    } else {
      navigate(`/documents?search=${docNum}`);
    }
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

      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm flex-shrink-0 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-display font-bold text-black">1421 AI Chat</h1>
          <p className="text-xs text-gray-500 mt-0.5">Ask about Chinese exploration &amp; the 1421 theory — answers sourced from the knowledge base only</p>
        </div>
        {hasMessages && (
          <div className="flex items-center gap-2">
            <button onClick={handleCopyAll}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-300 text-xs font-medium text-gray-700 hover:border-gold hover:text-gold transition-colors bg-white">
              {copiedAll
                ? <><Check className="h-3.5 w-3.5 text-emerald-600" /><span className="text-emerald-600">Copied</span></>
                : <><Copy className="h-3.5 w-3.5" /> Copy all</>}
            </button>
            <button onClick={() => setShowClearConfirm(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-300 text-xs font-medium text-red-600 hover:border-red-400 hover:bg-red-50 transition-colors bg-white">
              <Trash2 className="h-3.5 w-3.5" /> Clear chat
            </button>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
        {!hasMessages && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-20 h-20 rounded-2xl bg-gold flex items-center justify-center mb-5 shadow-md">
              <span className="text-xl font-display font-bold text-white tracking-tight">1421</span>
            </div>
            <h2 className="text-2xl font-display font-bold text-black mb-2">Welcome to 1421 AI</h2>
            <p className="text-gray-600 max-w-md mb-2">Ask any question about Chinese maritime exploration.</p>
            <p className="text-xs text-gray-400 max-w-md mb-6">All answers are sourced exclusively from the 1421 Foundation knowledge base. Click any document badge in responses to view the source.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
              {STARTERS.map((q) => (
                <button key={q} onClick={() => handleSend(q)}
                  className="text-left rounded-xl border border-gray-200 bg-white p-3 text-sm text-gray-700 hover:border-gold hover:bg-red-50 transition-all shadow-sm">
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
          const sources     = deduplicateSources(msg.sources || []);
          const sourceCount = sources.length;

          return (
            <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[78%] rounded-2xl px-5 py-4 ${
                msg.role === "user"
                  ? "bg-gold text-white rounded-br-md shadow-sm"
                  : "bg-white border border-gray-200 text-black rounded-bl-md shadow-sm"
              }`}>
                {showDots && (
                  <div className="flex items-center gap-1.5 py-1">
                    {[0, 150, 300].map((delay) => (
                      <div key={delay} className="h-2 w-2 rounded-full bg-gold animate-bounce"
                        style={{ animationDelay: `${delay}ms` }} />
                    ))}
                  </div>
                )}

                {hasContent && (
                  msg.role === "assistant" ? (
                    <MessageContent
                      content={msg.content}
                      sources={sources}
                      onDocClick={(docNum) => handleDocClick(sources, docNum)}
                    />
                  ) : (
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  )
                )}

                {msg.role === "assistant" && !isStreaming && hasContent && (
                  <>
                    <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-3 flex-wrap">
                      <button onClick={() => handleCopy(msg.content, idx)}
                        className="flex items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-gold transition-colors">
                        {copiedIdx === idx
                          ? <><Check className="h-3.5 w-3.5 text-emerald-600" /><span className="text-emerald-600">Copied</span></>
                          : <><Copy className="h-3.5 w-3.5" /> Copy</>}
                      </button>
                      {sourceCount > 0 && (
                        <button onClick={() => toggleSources(idx)}
                          className="flex items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-gold transition-colors">
                          {showSources
                            ? <><ChevronUp className="h-3.5 w-3.5" /> Hide sources</>
                            : <><ChevronDown className="h-3.5 w-3.5" /> {sourceCount} source{sourceCount > 1 ? "s" : ""}</>}
                        </button>
                      )}
                    </div>

                    {showSources && sourceCount > 0 && (
                      <div className="mt-3 space-y-2">
                        {sources.map((src, sIdx) => (
                          <div key={sIdx} className="bg-gray-50 rounded-lg border border-gray-200 px-3 py-2">
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex items-center gap-2 min-w-0">
                                <span className="w-5 h-5 rounded bg-gold/10 border border-gold/30 flex items-center justify-center text-gold text-xs font-bold flex-shrink-0">
                                  {sIdx + 1}
                                </span>
                                <div className="min-w-0">
                                  <p className="text-xs font-semibold text-gray-900 truncate">{src.title}</p>
                                  <p className="text-xs text-gray-500 mt-0.5">
                                    {[
                                      src.author !== "Unknown" && src.author,
                                      src.year > 0 && src.year,
                                      src.type && src.type !== "unknown" && src.type,
                                    ].filter(Boolean).join(" · ")}
                                  </p>
                                </div>
                              </div>
                              {src.similarity != null && (
                                <span className="text-xs font-semibold text-gold flex-shrink-0 bg-red-50 px-1.5 py-0.5 rounded border border-gold/20">
                                  {Math.round(src.similarity * 100)}%
                                </span>
                              )}
                            </div>
                            <button
                              onClick={() => navigate(`/documents?search=${encodeURIComponent(src.title)}`)}
                              className="mt-2 text-xs text-gold font-semibold flex items-center gap-1 hover:underline"
                            >
                              <FileText className="h-3 w-3" /> View in Documents
                            </button>
                          </div>
                        ))}
                        <p className="text-xs text-gray-400">Click any document badge in the response to jump directly to that source.</p>
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

      {/* Input */}
      <div className="border-t border-gray-200 px-6 py-4 bg-white flex-shrink-0">
        <div className="flex items-end gap-3 max-w-3xl mx-auto">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              placeholder="Ask a question…"
              rows={1}
              className="w-full resize-none rounded-xl border border-gray-300 bg-white px-4 py-3 pr-16 text-sm text-black placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gold/40 focus:border-gold"
              style={{ minHeight: "48px", maxHeight: "200px", overflowY: "hidden" }}
            />
            {input.length > 0 && (
              <span className="absolute bottom-3 right-3 text-xs text-gray-400 pointer-events-none">{input.length}</span>
            )}
          </div>
          {isTyping ? (
            <button onClick={handleStop}
              className="h-11 w-11 rounded-xl bg-gray-800 text-white hover:bg-gray-900 transition flex items-center justify-center flex-shrink-0 shadow-sm"
              title="Stop generating">
              <Square className="h-4 w-4 fill-white" />
            </button>
          ) : (
            <button onClick={() => handleSend()} disabled={!input.trim()}
              className="h-11 w-11 rounded-xl bg-gold text-white disabled:opacity-40 hover:bg-gold-light transition flex items-center justify-center flex-shrink-0 shadow-sm"
              title="Send message">
              <Send className="h-4 w-4" />
            </button>
          )}
        </div>
        <p className="text-xs text-gray-400 text-center mt-2">Press Enter to send · Shift+Enter for new line · Answers sourced from knowledge base only</p>
      </div>

      {/* Clear Chat Modal */}
      {showClearConfirm && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl border border-gray-200 p-6 max-w-sm w-full mx-4 shadow-2xl">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-red-50 border border-red-200 flex items-center justify-center flex-shrink-0">
                <Trash2 className="h-4 w-4 text-red-600" />
              </div>
              <h3 className="text-base font-display font-bold text-gray-900">Clear Chat?</h3>
            </div>
            <p className="text-sm text-gray-500 mb-4 leading-relaxed">
              This will permanently delete all messages in this conversation.
            </p>
            {isTyping && <p className="text-sm text-amber-600 font-medium mb-4">The current response will also be stopped.</p>}
            <div className="flex gap-3 justify-end">
              <button onClick={() => setShowClearConfirm(false)}
                className="px-4 py-2 rounded-lg border border-gray-200 text-sm text-gray-600 hover:bg-gray-50 transition-colors">
                Cancel
              </button>
              <button onClick={handleClearConfirmed}
                className="px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-semibold hover:bg-red-700 transition-colors">
                Clear all
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}