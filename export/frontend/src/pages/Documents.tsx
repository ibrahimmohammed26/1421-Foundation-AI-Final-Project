import { useState, useEffect, useCallback } from "react";
import {
  Search, FileText, Filter, X, ChevronLeft, ChevronRight,
} from "lucide-react";
import {
  getAllDocuments, searchDocuments, getDocumentTypes, getDocumentYears,
  Document,
} from "@/lib/api";

const PAGE_SIZE = 50; // show 50 per page → 7 pages for 347 docs

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

  // Load filter options once
  useEffect(() => {
    getDocumentTypes().then(setTypes).catch(() => {});
    getDocumentYears().then(setYears).catch(() => {});
  }, []);

  const loadDocuments = useCallback(async (page: number) => {
    setLoading(true);
    setIsSearchMode(false);
    try {
      const data = await getAllDocuments(PAGE_SIZE, (page - 1) * PAGE_SIZE);
      setDocuments(data.documents || []);
      setTotalDocuments(data.total || 0);
    } catch (err) {
      console.error("Error loading documents:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments(currentPage);
  }, [currentPage, loadDocuments]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setCurrentPage(1);
      loadDocuments(1);
      return;
    }
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

  // Client-side type/year filtering (applied on top of whatever the server returned)
  const filteredDocuments = documents.filter((doc) => {
    const matchesType = selectedType === "all" || doc.type === selectedType;
    const matchesYear = selectedYear === "all" || doc.year === selectedYear;
    return matchesType && matchesYear;
  });

  const totalPages = Math.ceil(totalDocuments / PAGE_SIZE);

  return (
    <div className="flex flex-col h-full bg-navy-dark">
      {/* Header */}
      <div className="border-b border-gray-800 px-6 py-4 bg-navy">
        <h1 className="text-xl font-display font-bold text-gold">Research Documents</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          {totalDocuments > 0
            ? `${totalDocuments} documents in the knowledge base`
            : "Loading knowledge base…"}
        </p>
      </div>

      {/* Search + Filters */}
      <div className="px-6 py-4 border-b border-gray-800">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search by title, author, or content…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="w-full bg-navy border border-gray-700 rounded-lg pl-10 pr-10 py-2.5 text-sm text-gray-200 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gold/50"
            />
            {searchQuery && (
              <button
                onClick={handleClearSearch}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          <button
            onClick={handleSearch}
            disabled={searching}
            className="px-6 py-2.5 bg-gold text-navy-dark rounded-lg text-sm font-medium hover:bg-gold/90 transition-colors disabled:opacity-50"
          >
            {searching ? "Searching…" : "Search"}
          </button>

          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-2.5 rounded-lg border text-sm flex items-center gap-2 transition-colors ${
              showFilters
                ? "bg-gold text-navy-dark border-gold"
                : "border-gray-700 text-gray-400 hover:text-gray-200 hover:border-gray-600"
            }`}
          >
            <Filter className="h-4 w-4" />
            Filters
          </button>
        </div>

        {showFilters && (
          <div className="mt-4 p-4 bg-navy rounded-lg border border-gray-800">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Document Type</label>
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="w-full bg-navy-light border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200"
                >
                  <option value="all">All Types</option>
                  {types.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Year</label>
                <select
                  value={selectedYear}
                  onChange={(e) =>
                    setSelectedYear(e.target.value === "all" ? "all" : Number(e.target.value))
                  }
                  className="w-full bg-navy-light border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200"
                >
                  <option value="all">All Years</option>
                  {years.map((y) => (
                    <option key={y} value={y}>{y}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Status bar + pagination */}
      <div className="px-6 py-2 text-xs text-gray-400 flex justify-between items-center border-b border-gray-800">
        <span>
          {isSearchMode
            ? `${filteredDocuments.length} result${filteredDocuments.length !== 1 ? "s" : ""} for "${searchQuery}"`
            : `Showing ${(currentPage - 1) * PAGE_SIZE + 1}–${Math.min(
                currentPage * PAGE_SIZE,
                totalDocuments
              )} of ${totalDocuments} documents`}
        </span>

        {!isSearchMode && totalPages > 1 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1 rounded hover:bg-navy-light disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span>
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1 rounded hover:bg-navy-light disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>

      {/* Document list */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold" />
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="h-12 w-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No documents found</p>
            {searchQuery && (
              <button
                onClick={handleClearSearch}
                className="mt-3 text-gold hover:text-gold/80 text-sm"
              >
                Clear search
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredDocuments.map((doc) => (
              <div
                key={doc.id}
                className="bg-navy rounded-xl border border-gray-800 p-5 hover:border-gold/30 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <FileText className="h-5 w-5 text-gold flex-shrink-0" />
                      <h3 className="text-base font-display font-semibold text-gray-200 truncate">
                        {doc.title}
                      </h3>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-gray-400 mb-2 flex-wrap">
                      {doc.author && doc.author !== "Unknown" && (
                        <span>By {doc.author}</span>
                      )}
                      {doc.year > 0 && (
                        <>
                          <span>•</span>
                          <span>{doc.year}</span>
                        </>
                      )}
                      {doc.type && doc.type !== "unknown" && (
                        <>
                          <span>•</span>
                          <span className="capitalize">{doc.type}</span>
                        </>
                      )}
                      {doc.source_file && doc.source_file !== "Unknown" && (
                        <>
                          <span>•</span>
                          <span className="font-mono truncate max-w-[200px]">
                            {doc.source_file.split("/").pop()}
                          </span>
                        </>
                      )}
                      {doc.page_number != null && (
                        <>
                          <span>•</span>
                          <span>p.{doc.page_number}</span>
                        </>
                      )}
                    </div>

                    {(doc.description || doc.content_preview) && (
                      <p className="text-sm text-gray-300 mb-3 line-clamp-3">
                        {doc.description || doc.content_preview}
                      </p>
                    )}

                    {doc.tags && doc.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {doc.tags.slice(0, 8).map((tag, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 bg-navy-light rounded text-xs text-gray-400"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {doc.similarity_score != null && (
                    <div className="text-xs text-gold font-medium flex-shrink-0">
                      {Math.round(doc.similarity_score * 100)}% match
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}