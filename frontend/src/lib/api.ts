/// <reference types="vite/client" />

const API = import.meta.env.DEV ? "http://localhost:8000" : "";

// ── Types ─────────────────────────────────────────────────────────────

export interface Location {
  name: string;
  lat: number;
  lon: number;
  year: number;
  event: string;
}

export interface Stats {
  feedback_count: number;
  locations_count: number;
  documents_count: number;
}

export interface Document {
  id: string;
  title: string;
  author: string;
  year: number;
  type: string;
  description: string;
  tags: string[];
  content_preview: string;
  source_file: string;
  page_number?: number;
  similarity_score?: number;
}

export interface DocumentsResponse {
  documents: Document[];
  total: number;
  limit: number;
  offset: number;
}

export interface ChatSource {
  title: string;
  author: string;
  year: number;
  type: string;
  similarity?: number;
}

export interface ChatResponse {
  content: string;
  session_id: string;
  sources?: ChatSource[];
}

// ── Documents ─────────────────────────────────────────────────────────

export async function getAllDocuments(
  limit: number = 50,
  offset: number = 0
): Promise<DocumentsResponse> {
  const res = await fetch(`${API}/api/documents?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function searchDocuments(
  query: string,
  limit: number = 50
): Promise<{ results: Document[]; total: number; query: string }> {
  const res = await fetch(
    `${API}/api/documents/search?q=${encodeURIComponent(query)}&limit=${limit}`
  );
  if (!res.ok) throw new Error("Failed to search documents");
  return res.json();
}

export async function getDocumentTypes(): Promise<string[]> {
  const res = await fetch(`${API}/api/documents/types`);
  if (!res.ok) throw new Error("Failed to fetch document types");
  const data = await res.json();
  return data.types;
}

export async function getDocumentYears(): Promise<number[]> {
  const res = await fetch(`${API}/api/documents/years`);
  if (!res.ok) throw new Error("Failed to fetch document years");
  const data = await res.json();
  return data.years;
}

export async function getDocumentAuthors(): Promise<string[]> {
  const res = await fetch(`${API}/api/documents/authors`);
  if (!res.ok) throw new Error("Failed to fetch document authors");
  const data = await res.json();
  return data.authors;
}

// ── Locations / Stats ─────────────────────────────────────────────────

export async function fetchLocations(maxYear: number = 1421): Promise<Location[]> {
  const res = await fetch(`${API}/api/locations?max_year=${maxYear}`);
  if (!res.ok) throw new Error("Failed to fetch locations");
  return res.json();
}

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${API}/api/stats`);
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

// ── Chat ──────────────────────────────────────────────────────────────

export async function sendChatMessage(
  messages: { role: string; content: string }[],
  sessionId?: string,
  useDocuments: boolean = true
): Promise<ChatResponse> {
  const res = await fetch(`${API}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, session_id: sessionId, use_documents: useDocuments }),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `Error ${res.status}`);
  }

  return res.json();
}

// ── streamChat — uses /api/chat (non-streaming) and simulates word-by-word
//    display on the frontend. This avoids CORS issues with SSE on Render's
//    free tier which strips Access-Control headers from streaming responses.
export async function streamChat(
  messages: { role: string; content: string }[],
  onDelta: (text: string) => void,
  onDone: () => void,
  onError: (err: string) => void,
  useDocuments: boolean = true
) {
  try {
    const res = await fetch(`${API}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages, use_documents: useDocuments }),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: "Request failed" }));
      onError(body.detail || `Error ${res.status}`);
      return;
    }

    const data: ChatResponse = await res.json();
    const fullText = data.content || "";

    // Simulate word-by-word streaming for a natural feel
    const words = fullText.split(" ");
    for (let i = 0; i < words.length; i++) {
      // Small delay between words to simulate streaming
      await new Promise((resolve) => setTimeout(resolve, 18));
      const chunk = i === 0 ? words[i] : " " + words[i];
      onDelta(chunk);
    }

    onDone();
  } catch (error) {
    onError(error instanceof Error ? error.message : "Request failed");
  }
}

// ── Feedback ──────────────────────────────────────────────────────────

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
  if (!res.ok) throw new Error("Failed to submit feedback");
  return res.json();
}