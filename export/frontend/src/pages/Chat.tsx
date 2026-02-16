import { useState, useRef, useEffect } from "react";
import { Send, Copy, Check } from "lucide-react";
import { streamChat } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;
    const userMsg: Message = { role: "user", content: input.trim() };
    const newMsgs = [...messages, userMsg];
    setMessages(newMsgs);
    setInput("");
    setIsTyping(true);

    let content = "";

    await streamChat(
      newMsgs.map((m) => ({ role: m.role, content: m.content })),
      (chunk) => {
        content += chunk;
        setMessages([...newMsgs, { role: "assistant", content }]);
      },
      () => setIsTyping(false),
      (err) => {
        setIsTyping(false);
        setMessages([...newMsgs, { role: "assistant", content: `Error: ${err}` }]);
      }
    );
  };

  const handleCopy = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  const STARTERS = [
    "What was the significance of Zheng He's voyages?",
    "Describe Ming Dynasty naval technology",
    "Is there evidence of Chinese ships reaching America?",
    "How did Chinese navigation compare to European methods?",
  ];

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-gray-700 px-6 py-4">
        <h1 className="text-xl font-display font-bold text-gold">1421 AI Chat</h1>
        <p className="text-xs text-gray-400 mt-0.5">Ask about Chinese exploration & the 1421 theory</p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
        {messages.length === 0 && !isTyping && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-14 h-14 rounded-2xl bg-gold flex items-center justify-center mb-4">
              <span className="text-xl font-display font-bold text-navy-dark">14</span>
            </div>
            <h2 className="text-2xl font-display font-bold mb-2">Welcome to 1421 AI</h2>
            <p className="text-gray-400 max-w-md mb-6">
              Ask any question about Chinese maritime exploration.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
              {STARTERS.map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="text-left rounded-xl border border-gray-700 bg-navy p-3 text-sm text-gray-300 hover:border-gold/50 hover:bg-navy-light transition-all"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[75%] rounded-2xl px-5 py-4 ${
                msg.role === "user"
                  ? "bg-gold text-navy-dark rounded-br-md"
                  : "bg-navy border border-gray-700 text-gray-200 rounded-bl-md"
              }`}
            >
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
              {msg.role === "assistant" && (
                <div className="mt-2 pt-2 border-t border-gray-700 flex items-center gap-2">
                  <button
                    onClick={() => handleCopy(msg.content, idx)}
                    className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200 transition-colors"
                  >
                    {copiedIdx === idx ? <><Check className="h-3 w-3" /> Copied</> : <><Copy className="h-3 w-3" /> Copy</>}
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-navy border border-gray-700 rounded-2xl rounded-bl-md px-5 py-4">
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

      <div className="border-t border-gray-700 px-6 py-4">
        <div className="flex items-end gap-3 max-w-3xl mx-auto">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
            placeholder="Ask a question..."
            rows={1}
            className="flex-1 resize-none rounded-xl border border-gray-600 bg-navy px-4 py-3 text-sm text-gray-100 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gold/50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            className="h-11 w-11 rounded-xl bg-gold text-navy-dark disabled:opacity-40 hover:bg-gold-light transition flex items-center justify-center flex-shrink-0"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
