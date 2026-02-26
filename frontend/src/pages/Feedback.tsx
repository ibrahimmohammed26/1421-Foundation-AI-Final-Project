import { useState } from "react";
import { submitFeedback } from "@/lib/api";
import { Send, CheckCircle, AlertCircle } from "lucide-react";

export default function Feedback() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [type, setType] = useState("Suggestion");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!email || !message) return;
    setSubmitting(true);
    try {
      await submitFeedback({ name, email, feedback_type: type, message });
      setStatus("success");
      setMessage("");
      setName("");
      setEmail("");
    } catch {
      setStatus("error");
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass =
    "w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-gold/40 focus:border-gold focus:outline-none transition-colors";

  return (
    <div className="flex flex-col h-full bg-gray-100">

      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm flex-shrink-0">
        <h1 className="text-xl font-display font-bold text-gray-900">Send Feedback</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Share your thoughts, report issues, or suggest improvements
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-xl space-y-5">

          {/* Name + Email */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                Name <span className="text-gray-400">(optional)</span>
              </label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                Email <span className="text-gold">*</span>
              </label>
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                type="email"
                className={inputClass}
              />
            </div>
          </div>

          {/* Type */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Feedback Type
            </label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className={inputClass}
            >
              {["Bug Report", "Feature Request", "Suggestion", "Question", "Other"].map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </div>

          {/* Message */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Message <span className="text-gold">*</span>
            </label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Tell us what's on your mind…"
              rows={6}
              className={`${inputClass} resize-none`}
            />
          </div>

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={!email || !message || submitting}
            className="w-full rounded-lg bg-gold text-white font-semibold py-3 hover:bg-gold-light transition-colors disabled:opacity-50 flex items-center justify-center gap-2 shadow-sm"
          >
            <Send className="h-4 w-4" />
            {submitting ? "Submitting…" : "Submit Feedback"}
          </button>

          {/* Status messages */}
          {status === "success" && (
            <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-700 text-sm">
              <CheckCircle className="h-4 w-4 flex-shrink-0" />
              Thank you for your feedback! We'll review it shortly.
            </div>
          )}
          {status === "error" && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              Something went wrong. Please try again.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}