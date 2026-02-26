import { useState, useEffect, useCallback } from "react";
import {
  Search, FileText, Filter, X, ChevronLeft, ChevronRight,
  ExternalLink, Tag, User, Calendar, Layers, Hash, Eye,
} from "lucide-react";
import {
  getAllDocuments, searchDocuments, getDocumentTypes, getDocumentYears,
  Document,
} from "@/lib/api";

const PAGE_SIZE = 50;

// ── Document Detail Modal ─────────────────────────────────────────────

function DocumentModal({ doc, onClose }: { doc: Document; onClose: () => void }) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
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
    <div className="flex items-start gap-3 py-2.5 border-b border-gray-100 last:border-0">
      <div className="flex items-center gap-2 w-28 flex-shrink-0">
        <Icon className="h-3.5 w-3.5 text-gray-400" />
        <span className="text-xs text-gray-400 uppercase tracking-wide">{label}</span>
      </div>
      <div className="flex-1 text-sm text-gray-800">{value}</div>
    </div>
  );

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white border border-gray-200 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl">

        {/* Modal header */}
        <div className="flex items-start justify-between gap-4 px-6 py-5 border-b border-gray-100">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-lg bg-gold flex items-center justify-center flex-shrink-0">
              <FileText className="h-4 w-4 text-white" />
            </div>
            <div className="min-w-0">
              <h2 className="text-base font-display font-bold text-gray-900 leading-snug line-clamp-2">
                {doc.title}
              </h2>
              {doc.author && doc.author !== "Unknown" && (
                <p className="text-xs text-gray-400 mt-0.5">by {doc.author}</p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors flex-shrink-0"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Modal body */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">

          {/* Badges */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-xs font-medium text-emerald-700">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
              Active
            </span>
            {doc.type && doc.type !== "unknown" && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-50 border border-gold/30 text-xs font-medium text-gold capitalize">
                {doc.type}
              </span>
            )}
            {doc.similarity_score != null && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-xs font-medium text-blue-700">
                {Math.round(doc.similarity_score * 100)}% match
              </span>
            )}
          </div>

          {/* Metadata */}
          <div className="bg-gray-50 rounded-xl border border-gray-100 px-4 py-1">
            {doc.author && doc.author !== "Unknown" && (
              <MetaRow icon={User} label="Author" value={doc.author} />
            )}
            {doc.year > 0 && (
              <MetaRow icon={Calendar} label="Year" value={doc.year} />
            )}
            {doc.type && doc.type !== "unknown" && (
              <MetaRow
                icon={Layers}
                label="Type"
                value={<span className="capitalize">{doc.type}</span>}
              />
            )}
            {doc.source_file && doc.source_file !== "Unknown" && (
              <MetaRow
                icon={ExternalLink}
                label="Source"
                value={
                  <span className="font-mono text-xs text-gray-600 break-all">
                    {doc.source_file}
                  </span>
                }
              />
            )}
            {doc.page_number != null && (
              <MetaRow icon={Hash} label="Page" value={`p. ${doc.page_number}`} />
            )}
            <MetaRow
              icon={Hash}
              label="Doc ID"
              value={<span className="font-mono text-xs text-gray-400">{doc.id}</span>}
            />
          </div>

          {/* Description */}
          {doc.description && (
            <div>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                Description
              </h3>
              <p className="text-sm text-gray-700 leading-relaxed">{doc.description}</p>
            </div>
          )}

          {/* Content preview */}
          {doc.content_preview && (
            <div>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                <Eye className="h-3.5 w-3.5" />
                Content Preview
              </h3>
              <div className="bg-gray-50 rounded-xl border border-gray-100 p-4">
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {doc.content_preview}
                </p>
              </div>
            </div>
          )}

          {/* Tags */}
          {doc.tags && doc.tags.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                <Tag className="h-3.5 w-3.5" />
                Tags
              </h3>
              <div className="flex flex-wrap gap-2">
                {doc.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 bg-gray-100 border border-gray-200 rounded-lg text-xs text-gray-600"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal footer */}
        <div className="px-6 py-4 border-t border-gray-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-lg bg-gray-100 border border-gray-200 text-sm text-gray-700 hover:bg-gray-200 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Documents Page ───────────────────────────────────────────────

export default function Documents() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [isSearchMode, setIsSearchMode] = useState(false);

  const [types, setTypes] = useState<string[]>([]);
  const [years, setYears] = useState<number[]>([]);
  const [selectedType, setSelectedType] = useState<string>("all");
  const [selectedYear, setSelectedYear] = useState<number | "all">("all");
  const [showFilters, setShowFilters] = useState(false);

  const [totalDocuments, setTotalDocuments] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);

  useEffect(() => {
    getDocumentTypes().then(setTypes).catch(() => {});
    getDocumentYears().then(setYears).catch(() => {});
  }, []);

  const loadDocuments = useCallback(async (page: number) => {
    setLoading(true);
    setIsSearchMode(false);
    try {
      const data = await getAllDocuments(PAGE_SIZE, (page - 1) * PAGE_SIZE);
      setDocuments(data.documents ?? []);
      setTotalDocuments(data.total ?? 0);
    } catch (err) {
      setError("Failed to load documents. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadDocuments(currentPage); }, [currentPage, loadDocuments]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) { setCurrentPage(1); loadDocuments(1); return; }
    setSearching(true);
    setIsSearchMode(true);
    try {
      const data = await searchDocuments(searchQuery, 200);
      setDocuments(data.results || []);
      setTotalDocuments(data.results?.length || 0);
    } catch (err) {
      console.error("Search error:", err);
    } finally {
      setSearching(false);
    }
  };

  const handleClearSearch = () => {
    setSearchQuery("");
    setCurrentPage(1);
    loadDocuments(1);
  };

  const filteredDocuments = documents.filter((doc) => {
    const matchesType = selectedType === "all" || doc.type === selectedType;
    const matchesYear = selectedYear === "all" || doc.year === selectedYear;
    return matchesType && matchesYear;
  });

  const totalPages = Math.ceil(totalDocuments / PAGE_SIZE);

  return (
    <>
      <div className="flex flex-col h-full bg-gray-100">

        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm">
          <h1 className="text-xl font-display font-bold text-gray-900">Research Documents</h1>
          <p className="text-xs text-gray-400 mt-0.5">
            {totalDocuments > 0
              ? `${totalDocuments} documents in the knowledge base`
              : "Loading knowledge base…"}
          </p>
        </div>

        {/* Search + Filters */}
        <div className="px-6 py-4 border-b border-gray-200 bg-white">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search by title, author, or content…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="w-full bg-white border border-gray-300 rounded-lg pl-10 pr-10 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gold/30 focus:border-gold"
              />
              {searchQuery && (
                <button
                  onClick={handleClearSearch}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
            <button
              onClick={handleSearch}
              disabled={searching}
              className="px-6 py-2.5 bg-gold text-white rounded-lg text-sm font-medium hover:bg-gold-light transition-colors disabled:opacity-50 shadow-sm"
            >
              {searching ? "Searching…" : "Search"}
            </button>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-2.5 rounded-lg border text-sm flex items-center gap-2 transition-colors ${
                showFilters
                  ? "bg-gold text-white border-gold"
                  : "border-gray-300 text-gray-500 hover:text-gray-900 hover:border-gray-400 bg-white"
              }`}
            >
              <Filter className="h-4 w-4" />
              Filters
            </button>
          </div>

          {showFilters && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Document Type</label>
                  <select
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value)}
                    className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800"
                  >
                    <option value="all">All Types</option>
                    {types.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Year</label>
                  <select
                    value={selectedYear}
                    onChange={(e) =>
                      setSelectedYear(e.target.value === "all" ? "all" : Number(e.target.value))
                    }
                    className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800"
                  >
                    <option value="all">All Years</option>
                    {years.map((y) => <option key={y} value={y}>{y}</option>)}
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Status + pagination */}
        <div className="px-6 py-2 text-xs text-gray-500 flex justify-between items-center border-b border-gray-200 bg-white">
          <span>
            {isSearchMode
              ? `${filteredDocuments.length} result${filteredDocuments.length !== 1 ? "s" : ""} for "${searchQuery}"`
              : `Showing ${(currentPage - 1) * PAGE_SIZE + 1}–${Math.min(currentPage * PAGE_SIZE, totalDocuments)} of ${totalDocuments} documents`}
          </span>
          {!isSearchMode && totalPages > 1 && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-1 rounded hover:bg-gray-100 disabled:opacity-50"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span>Page {currentPage} of {totalPages}</span>
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="p-1 rounded hover:bg-gray-100 disabled:opacity-50"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>

        {/* Document list */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold" />
            </div>
          ) : filteredDocuments.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No documents found</p>
              {searchQuery && (
                <button onClick={handleClearSearch} className="mt-3 text-gold hover:text-gold-dark text-sm">
                  Clear search
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {filteredDocuments.map((doc) => (
                <div
                  key={doc.id}
                  className="bg-white rounded-xl border border-gray-200 p-5 hover:border-gold/50 hover:shadow-sm transition-all"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <FileText className="h-5 w-5 text-gold flex-shrink-0" />
                        <h3 className="text-base font-display font-semibold text-gray-900 truncate">
                          {doc.title}
                        </h3>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-gray-400 mb-2 flex-wrap">
                        {doc.author && doc.author !== "Unknown" && <span>By {doc.author}</span>}
                        {doc.year > 0 && <><span>•</span><span>{doc.year}</span></>}
                        {doc.type && doc.type !== "unknown" && (
                          <><span>•</span><span className="capitalize">{doc.type}</span></>
                        )}
                        {doc.source_file && doc.source_file !== "Unknown" && (
                          <><span>•</span>
                          <span className="font-mono truncate max-w-[200px]">
                            {doc.source_file.split("/").pop()}
                          </span></>
                        )}
                        {doc.page_number != null && (
                          <><span>•</span><span>p.{doc.page_number}</span></>
                        )}
                        <span>•</span>
                        <span className="inline-flex items-center gap-1 text-emerald-600">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
                          Active
                        </span>
                      </div>
                      {(doc.description || doc.content_preview) && (
                        <p className="text-sm text-gray-600 mb-3 line-clamp-3">
                          {doc.description || doc.content_preview}
                        </p>
                      )}
                      {doc.tags && doc.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {doc.tags.slice(0, 8).map((tag, idx) => (
                            <span key={idx} className="px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-500">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-3 flex-shrink-0">
                      {doc.similarity_score != null && (
                        <div className="text-xs text-gold font-medium">
                          {Math.round(doc.similarity_score * 100)}% match
                        </div>
                      )}
                      <button
                        onClick={() => setSelectedDoc(doc)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-50 border border-gold/30 text-xs font-medium text-gold hover:bg-red-100 transition-colors"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        View
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {selectedDoc && (
        <DocumentModal doc={selectedDoc} onClose={() => setSelectedDoc(null)} />
      )}
    </>
  );
}