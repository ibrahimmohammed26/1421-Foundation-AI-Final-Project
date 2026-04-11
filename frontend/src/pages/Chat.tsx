import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Send, Copy, Check, FileText, Trash2,
  ChevronDown, ChevronUp, Square, AlertTriangle,
} from "lucide-react";
import { streamChat } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  streaming?: boolean;
  usedWebFallback?: boolean;
}


interface Source {
  title: string;
  author: string;
  year: number;
  type: string;
  relevance_score?: number;
}

const STORAGE_KEY = "1421_chat_messages";

function persistMessages(msgs: Message[]) {
  try {
    const withoutStreaming = msgs.map((m) => {
      if (m.streaming) {
        return { ...m, streaming: false };
      }
      return m;
    });
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(withoutStreaming));
  } catch (err) {
    // Silently fail - not critical
  }
}


function restoreMessages(): Message[] {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Message[];
    return parsed.map((m) => {
      if (m.streaming) {
        return { ...m, streaming: false };
      }
      return m;
    });
  } catch (err) {
    return [];
  }
}

type Listener = () => void;
type Unsubscribe = () => void;

// to store chat messages
const chatStore = {
  messages: restoreMessages() as Message[],
  isTyping: false,
  listeners: new Set<Listener>(),
  
  subscribe(fn: Listener): Unsubscribe {
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
  
  setIsTyping(typing: boolean) {
    this.isTyping = typing;
    this.notify();
  },
  
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
  const result = [];
  
  for (const s of sources || []) {
    const key = s.title?.trim().toLowerCase();
    if (!key || seen.has(key)) {
      continue;
    }
    seen.add(key);
    result.push(s);
  }
  
  return result;
}

// Turns [Document X] into clickable badge buttons
function MessageContent({ content, sources, onDocClick }: {
  content: string;
  sources: Source[];
  onDocClick: (n: number) => void;
}) {
  const parts = content.split(/(\[Document\s*\d+\](?:\[Document\s*\d+\])*)/gi);
  
  return (
    <div className="text-sm leading-relaxed whitespace-pre-wrap">
      {parts.map((part, i) => {
        const docRefs = [...part.matchAll(/\[Document\s*(\d+)\]/gi)];
        
        if (docRefs.length > 0) {
          return (
            <span key={i}>
              {docRefs.map((ref, j) => {
                const docNum = parseInt(ref[1], 10);
                const src = sources[docNum - 1];
                return (
                  <button
                    key={j}
                    onClick={() => onDocClick(docNum)}
                    title={src ? src.title : `Document ${docNum}`}
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

  const [messages, setMessagesLocal] = useState<Message[]>(() => chatStore.messages);
  const [isTyping, setIsTypingLocal] = useState(() => chatStore.isTyping);
  const [input, setInput] = useState("");
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Set<number>>(new Set());
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const unsubscribe = chatStore.subscribe(() => {
      setMessagesLocal([...chatStore.messages]);
      setIsTypingLocal(chatStore.isTyping);
    });
    return unsubscribe;
  }, []);

  useEffect(() => {
    if (endRef.current) {
      endRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    
    el.style.height = "auto";
    const newHeight = Math.min(el.scrollHeight, 200);
    el.style.height = newHeight + "px";
    el.style.overflowY = el.scrollHeight > 200 ? "auto" : "hidden";
  }, [input]);


  const handleStop = useCallback(() => {
    chatStore.setIsTyping(false);
    const msgs = chatStore.messages;
    if (msgs.length > 0 && msgs[msgs.length - 1].streaming) {
      const updated = msgs.map((m, i) => {
        if (i === msgs.length - 1) {
          return { ...m, streaming: false };
        }
        return m;
      });
      chatStore.setMessages(updated);
    }
  }, []);

  const handleSend = async (overrideText?: string) => {
    const text = (overrideText ?? input).trim();
    if (!text || chatStore.isTyping) return;
    
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
    
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
      
      (streamSources, usedWebFallback) => {
        if (!chatStore.isTyping) return;
        chatStore.setIsTyping(false);
        const dedupedSources = deduplicateSources(streamSources || []);
        chatStore.setMessages([
          ...newMsgs,
          {
            role: "assistant",
            content,
            sources: dedupedSources,
            streaming: false,
            usedWebFallback: usedWebFallback ?? false,
          },
        ]);
      },
    

      (err) => {
        if (!chatStore.isTyping) return;
        chatStore.setIsTyping(false);
        chatStore.setMessages([
          ...newMsgs,
          { role: "assistant", content: `Error: ${err}`, streaming: false }
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
    const allText = messages.map((m) => {
      const prefix = m.role === "user" ? "You" : "1421 AI";
      return `${prefix}: ${m.content}`;
    }).join("\n\n");
    
    navigator.clipboard.writeText(allText);
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
      if (next.has(idx)) {
        next.delete(idx);
      } else {
        next.add(idx);
      }

      return next;
    });
  };

  const handleDocClick = (sources: Source[], docNum: number) => {
    const src = sources[docNum - 1];
    if (src) {
      navigate(`/documents?search=${encodeURIComponent(src.title)}`);
    } else {
      navigate(`/documents?search=${docNum}`);
    }
  };
  // example questions on the defaul chat page
  const STARTERS = [
    "What does the 1421 Foundation say about Zheng He's voyages?",
    "What evidence exists for Chinese exploration of the Americas?",
    "What is the significance of the 1418 map?",
    "What does the research say about Chinese fleets visiting Africa?",
  ];

  const hasMessages = messages.length > 0;

  return (
    <div className="flex flex-col h-full bg-gray-100">

      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm flex-shrink-0 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-display font-bold text-black">1421 AI Chat</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Answers sourced from the 1421 Foundation knowledge base — sources ranked by relevance
          </p>
        </div>
        
        {hasMessages && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyAll}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-300 text-xs font-medium text-gray-700 hover:border-gold hover:text-gold transition-colors bg-white"
            >
              {copiedAll ? (
                <>
                  <Check className="h-3.5 w-3.5 text-emerald-600" />
                  <span className="text-emerald-600">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="h-3.5 w-3.5" />
                  Copy all
                </>
              )}
            </button>
            
            <button
              onClick={() => setShowClearConfirm(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-300 text-xs font-medium text-red-600 hover:border-red-400 hover:bg-red-50 transition-colors bg-white"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Clear chat
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
            <p className="text-gray-600 max-w-md mb-2">
              Ask questions about Chinese maritime exploration and the 1421 hypothesis.
            </p>
            <p className="text-xs text-gray-400 max-w-md mb-6">
              Answers come from the 1421 Foundation knowledge base. Sources are ranked by relevance — most relevant first.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
              {STARTERS.map((q) => (
                <button
                  key={q}
                  onClick={() => handleSend(q)}
                  className="text-left rounded-xl border border-gray-200 bg-white p-3 text-sm text-gray-700 hover:border-gold hover:bg-red-50 transition-all shadow-sm"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => {
          const isStreaming = msg.streaming === true;
          const hasContent = msg.content.trim().length > 0;
          const showDots = isStreaming && !hasContent;
          const showSources = expandedSources.has(idx);
          const sources = deduplicateSources(msg.sources || []);
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
                    <div className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: "0ms" }} />
                    <div className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: "150ms" }} />
                    <div className="h-2 w-2 rounded-full bg-gold animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                )}

                {hasContent && msg.role === "assistant" ? (
                  <MessageContent
                    content={msg.content}
                    sources={sources}
                    onDocClick={(n) => handleDocClick(sources, n)}
                  />
                ) : hasContent ? (
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                ) : null}

                {msg.role === "assistant" && !isStreaming && msg.usedWebFallback && (
                  <div className="mt-3 flex items-start gap-2 px-3 py-2.5 rounded-lg bg-amber-50 border border-amber-200">
                    <AlertTriangle className="h-3.5 w-3.5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-amber-700 leading-relaxed">
                      <span className="font-semibold">No matching documents found in the 1421 Foundation knowledge base.</span>{" "}
                      This response was generated from the AI's general training knowledge, not from indexed documents.
                    </p>
                  </div>
                )}

                {msg.role === "assistant" && !isStreaming && hasContent && (
                  <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-3 flex-wrap">
                    <button
                      onClick={() => handleCopy(msg.content, idx)}
                      className="flex items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-gold transition-colors"
                    >
                      {copiedIdx === idx ? (
                        <>
                          <Check className="h-3.5 w-3.5 text-emerald-600" />
                          <span className="text-emerald-600">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="h-3.5 w-3.5" />
                          Copy
                        </>
                      )}
                    </button>
                    
                    {sourceCount > 0 && (
                      <button
                        onClick={() => toggleSources(idx)}
                        className="flex items-center gap-1.5 text-xs font-medium text-gray-500 hover:text-gold transition-colors"
                      >
                        {showSources ? (
                          <>
                            <ChevronUp className="h-3.5 w-3.5" />
                            Hide sources
                          </>
                        ) : (
                          <>
                            <ChevronDown className="h-3.5 w-3.5" />
                            {sourceCount} source{sourceCount > 1 ? "s" : ""} — ranked by relevance
                          </>
                        )}
                      </button>
                    )}
                  </div>
                )}

                {showSources && sourceCount > 0 && (
                  <div className="mt-3 space-y-2">
                    <p className="text-xs text-gray-400 mb-1">Sources ranked most → least relevant:</p>
                    {sources.map((src, sIdx) => (
                      <div key={sIdx} className="bg-gray-50 rounded-lg border border-gray-200 px-3 py-2">
                        <div className="flex items-start gap-2 min-w-0">
                          <span className="w-5 h-5 rounded bg-gold/10 border border-gold/30 flex items-center justify-center text-gold text-xs font-bold flex-shrink-0 mt-0.5">
                            {sIdx + 1}
                          </span>
                          <div className="min-w-0 flex-1">
                            <p className="text-xs font-semibold text-gray-900 truncate">{src.title}</p>
                            <p className="text-xs text-gray-500 mt-0.5">
                              {[
                                src.author !== "Unknown" && src.author,
                                src.year > 0 && src.year,
                                src.type && src.type !== "unknown" && src.type
                              ].filter(Boolean).join(" · ")}
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => navigate(`/documents?search=${encodeURIComponent(src.title)}`)}
                          className="mt-2 text-xs text-gold font-semibold flex items-center gap-1 hover:underline"
                        >
                          <FileText className="h-3 w-3" />
                          View in Documents
                        </button>
                      </div>
                    ))}
                    <p className="text-xs text-gray-400">
                      Click any <span className="text-gold font-semibold">[Document X]</span> badge to jump to that source.
                    </p>
                  </div>
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
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask a question about Zheng He, the 1421 hypothesis, or Chinese maritime exploration…"
              rows={1}
              className="w-full resize-none rounded-xl border border-gray-300 bg-white px-4 py-3 pr-16 text-sm text-black placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gold/40 focus:border-gold"
              style={{ minHeight: "48px", maxHeight: "200px", overflowY: "hidden" }}
            />
            {input.length > 0 && (
              <span className="absolute bottom-3 right-3 text-xs text-gray-400 pointer-events-none">
                {input.length}
              </span>
            )}
          </div>
          
          {isTyping ? (
            <button
              onClick={handleStop}
              className="h-11 w-11 rounded-xl bg-gray-800 text-white hover:bg-gray-900 transition flex items-center justify-center flex-shrink-0 shadow-sm"
              title="Stop"
            >
              <Square className="h-4 w-4 fill-white" />
            </button>
          ) : (

            <button
              onClick={() => handleSend()}
              disabled={!input.trim()}
              className="h-11 w-11 rounded-xl bg-gold text-white disabled:opacity-40 hover:bg-gold-light transition flex items-center justify-center flex-shrink-0 shadow-sm"
              title="Send"
            >
              <Send className="h-4 w-4" />
            </button>
          )}
        </div>
        <p className="text-xs text-gray-400 text-center mt-2">Enter to send · Shift+Enter for new line</p>
      </div>

      {/* Clear Modal */}
      {showClearConfirm && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl border border-gray-200 p-6 max-w-sm w-full mx-4 shadow-2xl">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-red-50 border border-red-200 flex items-center justify-center flex-shrink-0">
                <Trash2 className="h-4 w-4 text-red-600" />
              </div>
              <h3 className="text-base font-display font-bold text-gray-900">Clear Chat?</h3>
            </div>
            <p className="text-sm text-gray-500 mb-4">This will permanently delete all messages.</p>
            {isTyping && (
              <p className="text-sm text-amber-600 font-medium mb-4">The current response will also be stopped.</p>
            )}
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