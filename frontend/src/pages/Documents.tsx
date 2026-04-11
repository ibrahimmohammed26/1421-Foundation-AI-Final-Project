import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Search, FileText, Filter, X, ChevronLeft, ChevronRight,
  ExternalLink, Tag, User, Calendar, Layers, Hash, Eye,
} from "lucide-react";
import {
  getAllDocuments,
  searchDocuments,
  getDocumentTypes,
  getDocumentAuthors,
  Document,
} from "@/lib/api";

const PAGE_SIZE = 50;

// simple sort helper (not over-engineered)
function sortDocs(docs: Document[]) {
  return [...docs].sort((a, b) => {
    const aNum = parseInt(a.id, 10);
    const bNum = parseInt(b.id, 10);

    if (!isNaN(aNum) && !isNaN(bNum)) return aNum - bNum;
    return a.id.localeCompare(b.id);
  });
}

function DocumentModal({ doc, onClose }: { doc: Document; onClose: () => void }) {
  useEffect(() => {
    const esc = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };

    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [onClose]);

  const MetaRow = ({
    icon: Icon,
    label,
    value,
  }: {
    icon: React.ElementType;
    label: string;
    value: React.ReactNode;
  }) => (
    <div className="flex items-start gap-3 py-2 border-b border-gray-100 last:border-0">
      <div className="flex items-center gap-2 w-28 flex-shrink-0">
        <Icon className="h-3.5 w-3.5 text-gray-400" />
        <span className="text-xs text-gray-400 uppercase">{label}</span>
      </div>
      <div className="flex-1 text-sm text-gray-800">{value}</div>
    </div>
  );


  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white border border-gray-200 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl">

        {/* header */}
        <div className="flex justify-between px-6 py-5 border-b">
          <div className="flex gap-3">
            <div className="w-9 h-9 bg-gold text-white flex items-center justify-center rounded">
              {doc.id}
            </div>
            <div>
              <h2 className="font-bold text-gray-900">{doc.title}</h2>
              {doc.author && doc.author !== "Unknown" && (
                <p className="text-xs text-gray-400">by {doc.author}</p>
              )}
            </div>
          </div>

          <button onClick={onClose} className="text-gray-400 hover:text-gray-700">
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* body */}
        <div className="p-6 overflow-y-auto space-y-5">

          <div className="bg-gray-50 rounded-lg border px-4">
            <MetaRow icon={Hash} label="Doc" value={doc.id} />
            <MetaRow
              icon={User}
              label="Author"
              value={
                doc.author && doc.author !== "Unknown"
                  ? doc.author
                  : <span className="italic text-gray-400">No author</span>
              }
            />

            {doc.year > 0 && (
              <MetaRow icon={Calendar} label="Year" value={doc.year} />
            )}

            {doc.type && doc.type !== "unknown" && (
              <MetaRow icon={Layers} label="Type" value={doc.type} />
            )}

            <MetaRow
              icon={ExternalLink}
              label="URL"
              value={
                doc.url
                  ? <a href={doc.url} target="_blank" className="text-gold underline break-all">{doc.url}</a>
                  : <span className="text-gray-400">No source</span>
              }
            />
          </div>


          {doc.tags?.length > 0 && (
            <div>
              <p className="text-xs text-gray-400 mb-2">Tags</p>
              <div className="flex flex-wrap gap-2">
                {doc.tags.map((t, i) => (
                  <span key={i} className="px-2 py-1 bg-gray-100 text-xs rounded">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* footer */}
        <div className="flex justify-end gap-2 p-4 border-t">
          {doc.url && (
            <a href={doc.url} target="_blank" className="bg-gold text-white px-4 py-2 rounded text-sm">
              Open Source
            </a>
          )}
          <button onClick={onClose} className="bg-gray-100 px-4 py-2 rounded text-sm">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// main functions here
export default function Documents() {
  const [params] = useSearchParams();

  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Document[]>([]);
  const [isSearch, setIsSearch] = useState(false);

  const [types, setTypes] = useState<string[]>([]);
  const [authors, setAuthors] = useState<string[]>([]);

  const [type, setType] = useState("all");
  const [author, setAuthor] = useState("all");

  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Document | null>(null);

  useEffect(() => {
    getDocumentTypes().then(setTypes);
    getDocumentAuthors().then(setAuthors);
  }, []);

  const loadDocs = useCallback(async () => {
    setLoading(true);

    try {
      let all: Document[] = [];
      let offset = 0;
      let done = false;

      while (!done) {
        const res = await getAllDocuments(500, offset);
        const chunk = res.documents || [];

        all = [...all, ...chunk];
        done = chunk.length < 500;
        offset += 500;
      }


      setDocs(sortDocs(all));
    } catch {
      console.error("failed loading docs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const q = params.get("search");

    if (q) {
      setQuery(q);
      setIsSearch(true);

      searchDocuments(q, 500)
        .then((d) => setResults(d.results || []))
        .finally(() => setLoading(false));

      loadDocs();
    } else {
      loadDocs();
    }
  }, [params, loadDocs]);


  const visibleDocs = (isSearch ? results : docs).filter((d) => {
    if (type !== "all" && d.type !== type) return false;

    if (author !== "all") {
      if (author === "__no_author__") {
        if (d.author && d.author !== "Unknown") return false;
      } else if (d.author !== author) return false;
    }

    return true;
  });

  const pageDocs = isSearch
    ? visibleDocs
    : visibleDocs.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <>
      <div className="p-6">

        {/* search */}
        <div className="flex gap-2 mb-4">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search..."
            className="border px-3 py-2 rounded w-full"
          />
          <button
            onClick={async () => {
              if (!query.trim()) return;

              setIsSearch(true);
              const r = await searchDocuments(query, 500);
              setResults(r.results || []);
            }}
            className="bg-gold text-white px-4 rounded"
          >
            Search
          </button>
        </div>

        {/* list */}
        {loading ? (
          <p>Loading...</p>
        ) : (
          <div className="space-y-3">
            {pageDocs.map((d) => (
              <div
                key={d.id}
                className="border rounded p-4 hover:shadow cursor-pointer"
                onClick={() => setSelected(d)}
              >
                <p className="font-semibold">{d.title}</p>
                <p className="text-xs text-gray-400">
                  {d.author || "Unknown"} • {d.type || "unknown"}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {selected && (
        <DocumentModal doc={selected} onClose={() => setSelected(null)} />
      )}
    </>
  );
  
}