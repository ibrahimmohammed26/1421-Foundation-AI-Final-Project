/// <reference types="vite/client" />

const API = import.meta.env.DEV ? "http://localhost:8000" : "";

// ── Types ─────────────────────────────────────────────────────────────

export interface Location {
  name: string; lat: number; lon: number; year: number; event: string;
}
export interface Stats {
  feedback_count: number; locations_count: number; documents_count: number;
}
export interface Document {
  id: string; title: string; author: string; year: number; type: string;
  description: string; tags: string[]; content_preview: string;
  source_file: string; url?: string; page_number?: number;
  // similarity_score removed - we don't want to expose it to the frontend
}
export interface DocumentsResponse {
  documents: Document[]; total: number; limit: number; offset: number;
}
export interface ChatSource {
  title: string; author: string; year: number; type: string;
  // similarity removed - don't show percentages
}
export interface ChatResponse {
  content: string; session_id: string; sources?: ChatSource[];
}

// ── Documents ─────────────────────────────────────────────────────────

export async function getAllDocuments(limit = 500, offset = 0): Promise<DocumentsResponse> {
  const res = await fetch(`${API}/api/documents?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error("Failed to fetch documents");
  const data = await res.json();
  // Remove similarity_score from documents if present
  if (data.documents) {
    data.documents = data.documents.map((doc: any) => {
      const { similarity_score, ...rest } = doc;
      return rest;
    });
  }
  return data;
}

export async function searchDocuments(query: string, limit = 500) {
  const res = await fetch(`${API}/api/documents/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  if (!res.ok) throw new Error("Failed to search documents");
  const data = await res.json();
  // Remove similarity_score from results if present
  if (data.results) {
    data.results = data.results.map((doc: any) => {
      const { similarity_score, ...rest } = doc;
      return rest;
    });
  }
  return data;
}

export async function getDocumentTypes(): Promise<string[]> {
  const res = await fetch(`${API}/api/documents/types`);
  if (!res.ok) throw new Error("Failed to fetch document types");
  return (await res.json()).types;
}
export async function getDocumentYears(): Promise<number[]> {
  const res = await fetch(`${API}/api/documents/years`);
  if (!res.ok) throw new Error("Failed to fetch document years");
  return (await res.json()).years;
}
export async function getDocumentAuthors(): Promise<string[]> {
  const res = await fetch(`${API}/api/documents/authors`);
  if (!res.ok) throw new Error("Failed to fetch document authors");
  return (await res.json()).authors;
}

// ── Locations / Stats ─────────────────────────────────────────────────

export async function fetchLocations(maxYear = 1433): Promise<Location[]> {
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
  useDocuments = true
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
  const data = await res.json();
  // Remove similarity from sources if present
  if (data.sources) {
    data.sources = data.sources.map((source: any) => {
      const { similarity, ...rest } = source;
      return rest;
    });
  }
  return data;
}

export async function streamChat(
  messages: { role: string; content: string }[],
  onDelta: (text: string) => void,
  onDone: (sources?: ChatSource[]) => void,
  onError: (err: string) => void,
  useDocuments = true
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
    
    // Remove similarity from sources
    const cleanSources = (data.sources || []).map((source: any) => {
      const { similarity, ...rest } = source;
      return rest;
    });
    
    const seen = new Set<string>();
    const uniqueSources = cleanSources.filter((s) => {
      if (seen.has(s.title)) return false;
      seen.add(s.title);
      return true;
    });
    
    const words = fullText.split(" ");
    for (let i = 0; i < words.length; i++) {
      await new Promise((resolve) => setTimeout(resolve, 8));
      onDelta(i === 0 ? words[i] : " " + words[i]);
    }
    onDone(uniqueSources);
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