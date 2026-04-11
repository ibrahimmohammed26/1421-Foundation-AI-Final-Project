import { useState } from "react";
import { submitFeedback } from "@/lib/api";
import { Send, CheckCircle, AlertCircle, Info } from "lucide-react";

const FEEDBACK_TYPES = [
  "Suggestion",
  "Bug Report",
  "Feature Request",
  "Data Request",
  "Question",
  "Other",
];

export default function Feedback() {
  const [name, setName]       = useState("");
  const [email, setEmail]     = useState("");
  const [type, setType]       = useState("Suggestion");
  const [message, setMessage] = useState("");
  const [status, setStatus]   = useState<"idle" | "success" | "error">("idle");
  const [submitting, setSubmitting] = useState(false);

  const isDataRequest = type === "Data Request";

  const handleSubmit = async () => {
    if (!email || !message) return;
    setSubmitting(true);
    try {
      await submitFeedback({ name, email, feedback_type: type, message });
      setStatus("success");
      setMessage("");
      setName("");
      setEmail("");
      setType("Suggestion");
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
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm flex-shrink-0">
        <h1 className="text-xl font-display font-bold text-gray-900">Send Feedback</h1>
        <p className="text-xs text-gray-400 mt-0.5">Share your thoughts, report issues, or request new data sources</p>
      </div>

      <div className="flex-1 overflow-y-auto flex items-start justify-center px-6 py-6">
        <div className="w-full max-w-xl space-y-5">

          {/* Intro panel */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <h2 className="text-sm font-display font-bold text-gray-900 mb-2 flex items-center gap-2">
              <Info className="h-4 w-4 text-gold flex-shrink-0" />
              About this form
            </h2>
            <p className="text-sm text-gray-600 leading-relaxed mb-3">
              Use this form to share feedback, report bugs, suggest improvements, or request that additional sources be added to the knowledge base. All submissions are reviewed by the 1421 Foundation research and development team.
            </p>
            <div className="bg-red-50 border border-gold/20 rounded-lg px-4 py-3">
              <p className="text-xs text-gray-700 leading-relaxed">
                <span className="font-semibold text-gold">Requesting new data?</span>{" "}
                Select <span className="font-semibold">Data Request</span> as the feedback type and describe the source you would like added. It is recommended to include a URL where possible, but if the source does not have one, please describe where it is from — for example, the book title, publication, or archive it comes from.
              </p>
            </div>
          </div>

          {/* Form */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-4">

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

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                Feedback Type
              </label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value)}
                className={inputClass}
              >
                {FEEDBACK_TYPES.map((t) => (
                  <option key={t}>{t}</option>
                ))}
              </select>
            </div>

            {/* Data Request guidance — shown only when that type is selected */}
            {isDataRequest && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
                <p className="text-xs font-semibold text-amber-800 mb-1">Source information</p>
                <p className="text-xs text-amber-700 leading-relaxed">
                  Please describe the source in your message below. A URL is recommended where one is available — paste the full link (e.g.{" "}
                  <span className="font-mono">https://www.example.com/article</span>). If there is no URL, describe where the source is from, such as a book title, author, publication name, or archive. The more detail you provide, the easier it is for the team to locate and review the source.
                </p>
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                Message <span className="text-gold">*</span>
                {isDataRequest && (
                  <span className="ml-1 text-gray-400">— include a URL or describe where the source is from</span>
                )}
              </label>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder={
                  isDataRequest
                    ? "Please add this source to the knowledge base:\n\nSource: [URL or book title / publication / archive]\n\nReason: This source covers [topic] which is relevant to the 1421 Foundation research because..."
                    : "Tell us what's on your mind…"
                }
                rows={6}
                className={`${inputClass} resize-none`}
              />
            </div>

            <button
              onClick={handleSubmit}
              disabled={!email || !message || submitting}
              className="w-full rounded-lg bg-gold text-white font-semibold py-3 hover:bg-gold-light transition-colors disabled:opacity-50 flex items-center justify-center gap-2 shadow-sm"
            >
              <Send className="h-4 w-4" />
              {submitting ? "Submitting…" : "Submit Feedback"}
            </button>

            {status === "success" && (
              <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-700 text-sm">
                <CheckCircle className="h-4 w-4 flex-shrink-0" />
                Thank you! Your feedback has been sent to the 1421 Foundation team.
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
    </div>
  );
}