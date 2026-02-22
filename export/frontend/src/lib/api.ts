/// <reference types="vite/client" />

const API = (import.meta.env.VITE_API_URL as string) || "http://localhost:8000";

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

export async function getAllDocuments(limit: number = 50, offset: number = 0): Promise<DocumentsResponse> {
  const res = await fetch(`${API}/api/documents?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

export async function searchDocuments(query: string, limit: number = 50): Promise<{ results: Document[] }> {
  const res = await fetch(`${API}/api/documents/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  if (!res.ok) throw new Error('Failed to search documents');
  return res.json();
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

export interface DocumentSearchResponse {
  documents: Document[];
  total_found: number;
  search_time_ms: number;
  query: string;
}

// Add to your existing api.ts

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


export async function fetchLocations(maxYear: number = 1421): Promise<Location[]> {
  const res = await fetch(`${API}/api/locations?max_year=${maxYear}`);
  if (!res.ok) throw new Error('Failed to fetch locations');
  return res.json();
}

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${API}/api/stats`);
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}

export async function sendChatMessage(
  messages: { role: string; content: string }[],
  sessionId?: string,
  useDocuments: boolean = true
): Promise<ChatResponse> {
  const res = await fetch(`${API}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      messages, 
      session_id: sessionId,
      use_documents: useDocuments 
    }),
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `Error ${res.status}`);
  }
  
  return res.json();
}

export async function streamChat(
  messages: { role: string; content: string }[],
  onDelta: (text: string) => void,
  onDone: () => void,
  onError: (err: string) => void,
  useDocuments: boolean = true
) {
  const res = await fetch(`${API}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, use_documents: useDocuments }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Request failed" }));
    onError(body.detail || `Error ${res.status}`);
    return;
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });

      let idx: number;
      while ((idx = buffer.indexOf("\n")) !== -1) {
        const line = buffer.slice(0, idx).trim();
        buffer = buffer.slice(idx + 1);
        
        if (!line.startsWith("data: ")) continue;
        
        const data = line.slice(6);
        if (data === "[DONE]") { 
          onDone(); 
          return; 
        }
        if (data.startsWith("ERROR:")) { 
          onError(data); 
          return; 
        }
        onDelta(data);
      }
    }
    onDone();
  } catch (error) {
    onError(error instanceof Error ? error.message : "Stream error");
  }
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
  
  if (!res.ok) {
    throw new Error('Failed to submit feedback');
  }
  
  return res.json();
}



export async function getDocumentTypes(): Promise<string[]> {
  const res = await fetch(`${API}/api/documents/types`);
  if (!res.ok) throw new Error('Failed to fetch document types');
  const data = await res.json();
  return data.types;
}

export async function getDocumentYears(): Promise<number[]> {
  const res = await fetch(`${API}/api/documents/years`);
  if (!res.ok) throw new Error('Failed to fetch document years');
  const data = await res.json();
  return data.years;
}

export async function getDocumentAuthors(): Promise<string[]> {
  const res = await fetch(`${API}/api/documents/authors`);
  if (!res.ok) throw new Error('Failed to fetch document authors');
  const data = await res.json();
  return data.authors;
}
