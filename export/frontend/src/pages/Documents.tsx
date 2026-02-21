import { useState } from "react";
import { Search, FileText, Download, Filter, X } from "lucide-react";

interface Document {
  id: string;
  title: string;
  author: string;
  year: number;
  type: "book" | "article" | "manuscript" | "thesis";
  description: string;
  tags: string[];
  url: string;
}

// Sample documents data - you can replace this with real data from your backend
const SAMPLE_DOCUMENTS: Document[] = [
  {
    id: "1",
    title: "1421: The Year China Discovered the World",
    author: "Gavin Menzies",
    year: 2002,
    type: "book",
    description: "Controversial book proposing that Chinese fleets circumnavigated the globe before Columbus.",
    tags: ["1421 hypothesis", "exploration", "Ming dynasty"],
    url: "#"
  },
  {
    id: "2",
    title: "Zheng He: China's Great Explorer",
    author: "Zhang Wei",
    year: 2015,
    type: "book",
    description: "Biography of Admiral Zheng He and his seven voyages.",
    tags: ["Zheng He", "biography", "Ming dynasty"],
    url: "#"
  },
  {
    id: "3",
    title: "Ming Dynasty Naval Technology",
    author: "Li Hua",
    year: 2020,
    type: "article",
    description: "Analysis of shipbuilding techniques and navigation methods during the Ming era.",
    tags: ["naval technology", "shipbuilding", "navigation"],
    url: "#"
  },
  {
    id: "4",
    title: "Treasure Fleet: The Secret Voyages of Zheng He",
    author: "Louise Levathes",
    year: 1994,
    type: "book",
    description: "Historical account of China's great explorer and his treasure ships.",
    tags: ["treasure fleet", "Zheng He", "exploration"],
    url: "#"
  },
  {
    id: "5",
    title: "Chinese Maritime Expansion: 1405-1433",
    author: "Chen Ming",
    year: 2018,
    type: "thesis",
    description: "Academic study of China's naval expeditions during the early Ming dynasty.",
    tags: ["maritime expansion", "Ming dynasty", "academic"],
    url: "#"
  }
];

export default function Documents() {
  const [search, setSearch] = useState("");
  const [selectedType, setSelectedType] = useState<string>("all");
  const [selectedYear, setSelectedYear] = useState<number | "all">("all");
  const [showFilters, setShowFilters] = useState(false);

  // Get unique years for filter
  const years = Array.from(new Set(SAMPLE_DOCUMENTS.map(d => d.year))).sort();

  // Filter documents
  const filteredDocuments = SAMPLE_DOCUMENTS.filter(doc => {
    const matchesSearch = doc.title.toLowerCase().includes(search.toLowerCase()) ||
                         doc.author.toLowerCase().includes(search.toLowerCase()) ||
                         doc.description.toLowerCase().includes(search.toLowerCase()) ||
                         doc.tags.some(tag => tag.toLowerCase().includes(search.toLowerCase()));
    
    const matchesType = selectedType === "all" || doc.type === selectedType;
    const matchesYear = selectedYear === "all" || doc.year === selectedYear;
    
    return matchesSearch && matchesType && matchesYear;
  });

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-gray-700 px-6 py-4">
        <h1 className="text-xl font-display font-bold text-gold">Research Documents</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Access historical documents, papers, and resources
        </p>
      </div>

      {/* Search and Filter Bar */}
      <div className="px-6 py-4 border-b border-gray-700">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search documents by title, author, or keywords..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-navy border border-gray-700 rounded-lg pl-10 pr-4 py-2.5 text-sm text-gray-200 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gold/50"
            />
          </div>
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

        {/* Expanded Filters */}
        {showFilters && (
          <div className="mt-4 p-4 bg-navy rounded-lg border border-gray-700">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-sm font-medium text-gray-200">Filter Documents</h3>
              <button
                onClick={() => {
                  setSelectedType("all");
                  setSelectedYear("all");
                }}
                className="text-xs text-gold hover:text-gold-light"
              >
                Reset Filters
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Document Type</label>
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="w-full bg-navy-light border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200"
                >
                  <option value="all">All Types</option>
                  <option value="book">Books</option>
                  <option value="article">Articles</option>
                  <option value="manuscript">Manuscripts</option>
                  <option value="thesis">Theses</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Publication Year</label>
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
        <div className="space-y-4">
          {filteredDocuments.length > 0 ? (
            filteredDocuments.map((doc) => (
              <div
                key={doc.id}
                className="bg-navy rounded-xl border border-gray-700 p-5 hover:border-gold/30 transition-colors"
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
                      <span>•</span>
                      <span>{doc.year}</span>
                      <span>•</span>
                      <span className="capitalize">{doc.type}</span>
                    </div>
                    <p className="text-sm text-gray-300 mb-3">{doc.description}</p>
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
                  </div>
                  <button
                    onClick={() => window.open(doc.url, '_blank')}
                    className="ml-4 p-2 rounded-lg border border-gray-700 text-gray-400 hover:text-gold hover:border-gold/50 transition-colors"
                  >
                    <Download className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400">No documents found matching your criteria</p>
              <button
                onClick={() => {
                  setSearch("");
                  setSelectedType("all");
                  setSelectedYear("all");
                }}
                className="mt-3 text-gold hover:text-gold-light text-sm"
              >
                Clear all filters
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}