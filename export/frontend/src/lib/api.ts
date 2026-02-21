/// <reference types="vite/client" />

const API = (import.meta.env.VITE_API_URL as string) || "http://localhost:8000";

export async function fetchLocations(maxYear: number) {
  const res = await fetch(`${API}/api/locations?max_year=${maxYear}`);
  return res.json();
}

export async function streamChat(
  messages: { role: string; content: string }[],
  onDelta: (text: string) => void,
  onDone: () => void,
  onError: (err: string) => void
) {
  const res = await fetch(`${API}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Request failed" }));
    onError(body.detail || `Error ${res.status}`);
    return;
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let idx: number;
    while ((idx = buffer.indexOf("\n")) !== -1) {
      let line = buffer.slice(0, idx).trim();
      buffer = buffer.slice(idx + 1);
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6);
      if (data === "[DONE]") { onDone(); return; }
      if (data.startsWith("ERROR:")) { onError(data); return; }
      onDelta(data);
    }
  }
  onDone();
}

export async function submitFeedback(data: {
  name?: string;
  email: string;
  feedback_type: string;
  message: string;
}) {
  const res = await fetch(`${API}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}
export async function fetchStats() {
  const res = await fetch(`${API}/api/stats`);
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}
