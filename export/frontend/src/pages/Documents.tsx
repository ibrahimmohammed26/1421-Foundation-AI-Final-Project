import { useState, useEffect } from "react";
import { Search, FileText, Download, Filter, X } from "lucide-react";
import { getAllDocuments, searchDocuments, Document } from "@/lib/api";

export default function Documents() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [selectedType, setSelectedType] = useState<string>("all");
  const [selectedYear, setSelectedYear] = useState<number | "all">("all");
  const [showFilters, setShowFilters] = useState(false);

  // Get unique types and years from documents
  const types = [...new Set(documents.map(d => d.type))];
  const years = [...new Set(documents.map(d => d.year))].sort((a, b) => b - a);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const data = await getAllDocuments(100);
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Error loading documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadDocuments();
      return;
    }

    setSearching(true);
    try {
      const data = await searchDocuments(searchQuery, 50);
      setDocuments(data.results || []);
    } catch (error) {
      console.error('Error searching documents:', error);
    } finally {
      setSearching(false);
    }
  };

  // Filter documents by type and year
  const filteredDocuments = documents.filter(doc => {
    const matchesType = selectedType === "all" || doc.type === selectedType;
    const matchesYear = selectedYear === "all" || doc.year === selectedYear;
    return matchesType && matchesYear;
  });

  return (
    <div className="flex flex-col h-full bg-navy-dark">
      <div className="border-b border-gray-800 px-6 py-4 bg-navy">
        <h1 className="text-xl font-display font-bold text-gold">Research Documents</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Access historical documents from the knowledge base
        </p>
      </div>

      {/* Search Bar */}
      <div className="px-6 py-4 border-b border-gray-800">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full bg-navy border border-gray-700 rounded-lg pl-10 pr-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gold/50"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={searching}
            className="px-6 py-2.5 bg-gold text-navy-dark rounded-lg text-sm font-medium hover:bg-gold/90 transition-colors disabled:opacity-50"
          >
            {searching ? 'Searching...' : 'Search'}
          </button>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-2.5 rounded-lg border text-sm flex items-center gap-2 transition-colors ${
              showFilters 
                ? 'bg-gold text-navy-dark border-gold' 
                : 'border-gray-700 text-gray-400 hover:text-gray-200 hover:border-gray-600'
            }`}
          >
            <Filter className="h-4 w-4" />
            Filters
          </button>
        </div>

        {/* Filters */}
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
                  {types.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Year</label>
                <select
                  value={selectedYear}
                  onChange={(e) => setSelectedYear(e.target.value === "all" ? "all" : Number(e.target.value))}
                  className="w-full bg-navy-light border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200"
                >
                  <option value="all">All Years</option>
                  {years.map(year => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Results Count */}
      <div className="px-6 py-2 text-xs text-gray-400">
        Found {filteredDocuments.length} document{filteredDocuments.length !== 1 ? 's' : ''}
      </div>

      {/* Documents List */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold"></div>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredDocuments.map((doc) => (
              <div
                key={doc.id}
                className="bg-navy rounded-xl border border-gray-800 p-5 hover:border-gold/30 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <FileText className="h-5 w-5 text-gold" />
                      <h3 className="text-lg font-display font-semibold text-gray-200">
                        {doc.title}
                      </h3>
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-400 mb-2">
                      <span>By {doc.author}</span>
                      {doc.year > 0 && (
                        <>
                          <span>•</span>
                          <span>{doc.year}</span>
                        </>
                      )}
                      <span>•</span>
                      <span className="capitalize">{doc.type}</span>
                    </div>
                    <p className="text-sm text-gray-300 mb-3">{doc.description || doc.content_preview}</p>
                    {doc.tags && doc.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {doc.tags.map((tag, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-navy-light rounded text-xs text-gray-400"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  {doc.similarity_score && (
                    <div className="ml-4 text-xs text-gold">
                      Relevance: {Math.round(doc.similarity_score * 100)}%
                    </div>
                  )}
                </div>
              </div>
            ))}

            {filteredDocuments.length === 0 && (
              <div className="text-center py-12">
                <FileText className="h-12 w-12 text-gray-600 mx-auto mb-3" />
                <p className="text-gray-400">No documents found</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}