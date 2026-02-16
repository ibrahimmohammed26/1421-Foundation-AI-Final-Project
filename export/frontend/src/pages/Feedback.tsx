import { useState } from "react";
import { submitFeedback } from "@/lib/api";

export default function Feedback() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [type, setType] = useState("Suggestion");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");

  const handleSubmit = async () => {
    if (!email || !message) return;
    try {
      await submitFeedback({ name, email, feedback_type: type, message });
      setStatus("success");
      setMessage("");
    } catch {
      setStatus("error");
    }
  };

  return (
    <div className="p-6 max-w-xl mx-auto space-y-6">
      <h1 className="text-2xl font-display font-bold text-gold">Send Feedback</h1>

      <div className="grid grid-cols-2 gap-4">
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your Name (optional)"
          className="rounded-lg border border-gray-600 bg-navy px-3 py-2 text-sm text-gray-100 placeholder:text-gray-500 focus:ring-2 focus:ring-gold/50 focus:outline-none" />
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email (required)"
          className="rounded-lg border border-gray-600 bg-navy px-3 py-2 text-sm text-gray-100 placeholder:text-gray-500 focus:ring-2 focus:ring-gold/50 focus:outline-none" />
      </div>

      <select value={type} onChange={(e) => setType(e.target.value)}
        className="w-full rounded-lg border border-gray-600 bg-navy px-3 py-2 text-sm text-gray-100 focus:ring-2 focus:ring-gold/50 focus:outline-none">
        {["Bug Report", "Feature Request", "Suggestion", "Question", "Other"].map((t) => (
          <option key={t}>{t}</option>
        ))}
      </select>

      <textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Your message..."
        rows={5} className="w-full rounded-lg border border-gray-600 bg-navy px-3 py-2 text-sm text-gray-100 placeholder:text-gray-500 focus:ring-2 focus:ring-gold/50 focus:outline-none resize-none" />

      <button onClick={handleSubmit} className="w-full rounded-lg bg-gold text-navy-dark font-semibold py-2.5 hover:bg-gold-light transition">
        Submit Feedback
      </button>

      {status === "success" && <p className="text-green-400 text-sm">Thank you for your feedback!</p>}
      {status === "error" && <p className="text-red-400 text-sm">Something went wrong. Try again.</p>}
    </div>
  );
}
