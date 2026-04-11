import { useState } from "react";
import { submitFeedback } from "@/lib/api";
import { Send, CheckCircle, AlertCircle, Info } from "lucide-react";

const TYPES = [
  "Suggestion",
  "Bug Report",
  "Feature Request",
  "Data Request",
  "Question",
  "Other",
];

// main feedback function
export default function Feedback() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [type, setType] = useState("Suggestion");
  const [message, setMessage] = useState("");

  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
  const [loading, setLoading] = useState(false);

  const isData = type === "Data Request";

  async function handleSubmit() {
    if (!email || !message) return;

    setLoading(true);

    try {
      await submitFeedback({
        name,
        email,
        feedback_type: type,
        message,
      });

      setStatus("success");

      // reset form
      setName("");
      setEmail("");
      setMessage("");
      setType("Suggestion");
    } catch (err) {
      console.error(err);
      setStatus("error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full bg-gray-100">

      {/* header */}
      <div className="border-b px-6 py-4 bg-white">
        <h1 className="text-xl font-bold text-gray-900">Send Feedback</h1>
        <p className="text-xs text-gray-400">
          Share feedback or request new sources
        </p>
      </div>

      <div className="flex-1 flex justify-center px-6 py-6 overflow-y-auto">
        <div className="w-full max-w-xl space-y-4">

          {/* info */}
          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Info className="h-4 w-4 text-gold" />
              <p className="text-sm font-semibold">About this form</p>
            </div>

            <p className="text-sm text-gray-600 mb-3">
              Use this form to report bugs, suggest features, or request new sources.
            </p>

            <div className="bg-red-50 border rounded p-3 text-xs">
              <b>Requesting data?</b> Choose “Data Request” and include a URL or describe the source.
            </div>
          </div>

          {/* form */}
          <div className="bg-white border rounded-lg p-4 space-y-3">

            <div className="flex gap-3">
              <input
                placeholder="Name (optional)"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="flex-1 border rounded px-3 py-2 text-sm"
              />

              <input
                placeholder="Email *"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex-1 border rounded px-3 py-2 text-sm"
              />
            </div>

            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="border rounded px-3 py-2 text-sm w-full"
            >
              {TYPES.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>

            {isData && (
              <div className="bg-yellow-50 border rounded p-3 text-xs">
                Include a URL if possible, or describe where the source comes from.
              </div>
            )}


            <textarea
              rows={6}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={
                isData
                  ? "Source: ...\nReason: ..."
                  : "Write your message here..."
              }
              className="border rounded px-3 py-2 text-sm w-full resize-none"
            />

            <button
              onClick={handleSubmit}
              disabled={!email || !message || loading}
              className="w-full bg-gold text-white py-2 rounded flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
              {loading ? "Submitting..." : "Submit"}
            </button>

            {status === "success" && (
              <div className="flex items-center gap-2 text-green-600 text-sm">
                <CheckCircle className="h-4 w-4" />
                Feedback sent
              </div>
            )}

            {status === "error" && (
              <div className="flex items-center gap-2 text-red-600 text-sm">
                <AlertCircle className="h-4 w-4" />
                Something went wrong
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}