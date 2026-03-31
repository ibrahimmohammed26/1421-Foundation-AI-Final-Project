import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  MapContainer, TileLayer, Marker, Popup,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { fetchLocations, searchDocuments } from "@/lib/api";
import { FileText, X, CheckCircle, XCircle, ChevronUp, ChevronDown } from "lucide-react";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:       "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:     "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

const redIcon = new L.Icon({
  iconUrl:   "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41],
});

interface Location {
  name: string;
  lat: number;
  lon: number;
  year: number;
  event: string;
}

interface RelatedDoc {
  id: string;
  title: string;
  author: string;
  year: number;
  type: string;
  url?: string;
  similarity_score?: number;
  content_preview?: string;
  source_file?: string;
}

// Location-specific keywords for relevance
const locationKeywords: Record<string, { required: string[], optional: string[], exclude: string[] }> = {
  "Sri Lanka": {
    required: ["Sri Lanka", "Galle", "Ceylon", "trilingual inscription"],
    optional: ["Zheng He", "trading", "port", "1409", "tribute"],
    exclude: ["Gallery", "Minoan", "Atlantis", "fresco", "artist impression", "gallery 1", "gallery 2", "gallery 3"]
  },
  "Hormuz": {
    required: ["Hormuz", "Ormus", "Persian Gulf"],
    optional: ["Zheng He", "fourth voyage", "1414", "tribute"],
    exclude: ["Gallery", "Minoan", "Atlantis", "fresco"]
  },
  "Malindi": {
    required: ["Malindi", "Kenya", "East Africa"],
    optional: ["giraffe", "Zheng He", "fifth voyage", "1418"],
    exclude: ["Gallery", "Minoan", "Atlantis"]
  },
  "Mogadishu": {
    required: ["Mogadishu", "Somalia", "Somali"],
    optional: ["Zheng He", "porcelain", "East Africa"],
    exclude: ["Gallery", "Minoan", "Atlantis"]
  },
  "Aden": {
    required: ["Aden", "Yemen", "Arabia"],
    optional: ["Zheng He", "fifth voyage", "1417"],
    exclude: ["Gallery", "Minoan", "Atlantis"]
  },
  "Calicut": {
    required: ["Calicut", "Kozhikode", "Malabar Coast"],
    optional: ["Zheng He", "first voyage", "1406", "India"],
    exclude: ["Gallery", "Minoan", "Atlantis"]
  },
  "Malacca": {
    required: ["Malacca", "Melaka", "Strait of Malacca"],
    optional: ["Zheng He", "port", "Malaysia"],
    exclude: ["Gallery", "Minoan", "Atlantis"]
  },
  "Nanjing": {
    required: ["Nanjing", "shipyard", "Longjiang"],
    optional: ["Zheng He", "treasure fleet", "1403"],
    exclude: ["Gallery", "Minoan", "Atlantis"]
  }
};

// Default keywords for any location
const defaultKeywords = {
  required: [] as string[],
  optional: [] as string[],
  exclude: ["Gallery", "Minoan", "Atlantis", "fresco", "artist impression", "gallery 1", "gallery 2", "gallery 3", "image", "photo"]
};

// Calculate relevance score (higher is better)
const calculateRelevanceScore = (doc: RelatedDoc, locationName: string): number => {
  const title = doc.title?.toLowerCase() || "";
  const sourceFile = doc.source_file?.toLowerCase() || "";
  const type = doc.type?.toLowerCase() || "";
  
  const keywords = locationKeywords[locationName] || defaultKeywords;
  let score = 0;
  
  // Penalty for excluded keywords (Gallery, Minoan, etc.)
  for (const excludeWord of keywords.exclude) {
    if (title.includes(excludeWord.toLowerCase())) {
      return -100; // Completely exclude these documents
    }
  }
  
  // Check required keywords
  for (const requiredWord of keywords.required) {
    if (title.includes(requiredWord.toLowerCase())) {
      score += 20; // High score for exact match
    }
  }
  
  // Check optional keywords
  for (const optionalWord of keywords.optional) {
    if (title.includes(optionalWord.toLowerCase())) {
      score += 8;
    }
  }
  
  // Bonus for source type
  if (sourceFile.includes("1421") || sourceFile.includes("evidence") || sourceFile.includes("book")) {
    score += 15;
  }
  if (sourceFile.includes("foundation")) {
    score += 10;
  }
  
  // Bonus for type
  if (type === "gavin_menzies" && !title.includes("gallery")) {
    score += 5;
  }
  
  // Similarity score from backend
  if (doc.similarity_score) {
    score += doc.similarity_score * 10;
  }
  
  return score;
};

// Check if document is relevant at all
const isDocumentRelevant = (doc: RelatedDoc, locationName: string): boolean => {
  const title = doc.title?.toLowerCase() || "";
  const keywords = locationKeywords[locationName] || defaultKeywords;
  
  // Explicitly exclude gallery/image documents
  if (title.includes("gallery") || 
      title.includes("minoan") || 
      title.includes("atlantis") || 
      title.includes("fresco") ||
      title.includes("artist impression")) {
    return false;
  }
  
  // Must contain at least one required or optional keyword
  const allRelevantKeywords = [...keywords.required, ...keywords.optional];
  for (const keyword of allRelevantKeywords) {
    if (title.includes(keyword.toLowerCase())) {
      return true;
    }
  }
  
  return false;
};

// Search variations for each location
const getSearchVariations = (loc: Location): string[] => {
  const variations: string[] = [loc.name];
  
  if (loc.name === "Sri Lanka") {
    variations.push("Galle Sri Lanka", "Zheng He Galle", "trilingual inscription", "Ceylon Zheng He", "Sri Lanka Zheng He");
  } else if (loc.name === "Hormuz") {
    variations.push("Hormuz Persian Gulf", "Zheng He Hormuz", "Ormus", "fourth voyage");
  } else if (loc.name === "Malindi") {
    variations.push("Malindi Kenya", "giraffe Malindi", "Zheng He Malindi", "fifth voyage");
  } else if (loc.name === "Mogadishu") {
    variations.push("Mogadishu Somalia", "Somali coast", "Zheng He Mogadishu");
  } else if (loc.name === "Aden") {
    variations.push("Aden Yemen", "Arabian Peninsula", "Zheng He Aden");
  } else if (loc.name === "Calicut") {
    variations.push("Calicut India", "Kozhikode", "Malabar Coast", "Zheng He Calicut");
  } else if (loc.name === "Malacca") {
    variations.push("Malacca Malaysia", "Melaka", "Strait of Malacca");
  } else if (loc.name === "Nanjing") {
    variations.push("Nanjing shipyard", "treasure fleet Nanjing", "Longjiang shipyard");
  }
  
  return variations;
};

export default function DataMap() {
  const navigate = useNavigate();

  const [locations, setLocations]               = useState<Location[]>([]);
  const [loading, setLoading]                   = useState(true);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [relatedDocs, setRelatedDocs]           = useState<RelatedDoc[]>([]);
  const [docsLoading, setDocsLoading]           = useState(false);
  const [showDocsPanel, setShowDocsPanel]       = useState(false);
  const [showDebug, setShowDebug]               = useState(false);

  useEffect(() => {
    fetchLocations(1433)
      .then((d) => { setLocations(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const fetchRelatedDocs = async (loc: Location) => {
    setDocsLoading(true);
    setRelatedDocs([]);
    
    const variations = getSearchVariations(loc);
    console.log(`🔍 Searching for "${loc.name}" with variations:`, variations);
    
    try {
      let allResults: RelatedDoc[] = [];
      const seenIds = new Set<string>();
      
      // Try each search variation
      for (const term of variations) {
        try {
          const res = await searchDocuments(term, 30);
          const results: RelatedDoc[] = res.results || [];
          
          for (const doc of results) {
            if (!seenIds.has(doc.id)) {
              seenIds.add(doc.id);
              allResults.push(doc);
            }
          }
        } catch (err) {
          console.error(`Search failed for "${term}":`, err);
        }
      }
      
      // Also search with "Zheng He"
      try {
        const res = await searchDocuments(`Zheng He ${loc.name}`, 20);
        const results: RelatedDoc[] = res.results || [];
        for (const doc of results) {
          if (!seenIds.has(doc.id)) {
            seenIds.add(doc.id);
            allResults.push(doc);
          }
        }
      } catch (err) {
        console.error(`Search failed for Zheng He ${loc.name}:`, err);
      }
      
      console.log(`Raw results: ${allResults.length}`);
      
      // Filter for relevance
      const relevantDocs = allResults.filter(doc => isDocumentRelevant(doc, loc.name));
      console.log(`After relevance filter: ${relevantDocs.length}`);
      
      // Calculate scores and sort (highest to lowest)
      const scoredDocs = relevantDocs.map(doc => ({
        doc,
        score: calculateRelevanceScore(doc, loc.name)
      }));
      
      // Filter out negative scores (completely irrelevant)
      const positiveDocs = scoredDocs.filter(item => item.score > 0);
      
      // Sort by score descending
      positiveDocs.sort((a, b) => b.score - a.score);
      
      // Deduplicate by title
      const seenTitles = new Set<string>();
      const unique = positiveDocs.filter((item) => {
        const key = item.doc.title.trim().toLowerCase();
        if (seenTitles.has(key)) return false;
        seenTitles.add(key);
        return true;
      });
      
      // Take top 8 most relevant
      const topRelevant = unique.slice(0, 8).map(item => item.doc);
      
      console.log(`Final relevant documents: ${topRelevant.length}`);
      console.log("Top scores:", unique.slice(0, 8).map(item => ({ title: item.doc.title.substring(0, 50), score: item.score })));
      
      setRelatedDocs(topRelevant);
      
    } catch (err) {
      console.error("Error fetching related docs:", err);
      setRelatedDocs([]);
    } finally {
      setDocsLoading(false);
    }
  };

  const handleLocationClick = (loc: Location) => {
    setSelectedLocation(loc);
    setShowDocsPanel(true);
    fetchRelatedDocs(loc);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-100">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold" />
      </div>
    );
  }

  const seen = new Set<string>();
  const uniqueLocations = locations.filter((l) => {
    if (seen.has(l.name)) return false;
    seen.add(l.name);
    return true;
  });

  return (
    <div className="flex flex-col h-full bg-gray-100">
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm flex-shrink-0">
        <h1 className="text-xl font-display font-bold text-gray-900">Data Map</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Zheng He's voyage locations (1403–1433) and Relevant 1421 Foundation Knowledge Base Locations— click a marker to find related documents
        </p>
      </div>

      <div className="relative flex-1 min-h-0 flex">
        <div className="flex-1 relative">
          <MapContainer center={[20, 80]} zoom={3}
            style={{ height: "100%", width: "100%" }} zoomControl={true}>
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {uniqueLocations.map((loc, idx) => (
              <Marker key={idx} position={[loc.lat, loc.lon]} icon={redIcon}
                eventHandlers={{ click: () => handleLocationClick(loc) }}>
                <Popup>
                  <div className="text-sm">
                    <p className="font-bold text-gray-900">{loc.name}</p>
                    <p className="text-xs text-gray-500">Year {loc.year}</p>
                    <p className="text-xs mt-1 text-gray-700">{loc.event}</p>
                    <button onClick={() => handleLocationClick(loc)}
                      className="mt-2 text-xs text-gold font-semibold flex items-center gap-1 hover:underline">
                      <FileText className="h-3 w-3" /> View related documents
                    </button>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>

          <div className="absolute top-4 left-4 bg-white/95 backdrop-blur-sm rounded-lg border border-gray-200 px-4 py-2 z-[1000] shadow-sm">
            <p className="text-xs text-gray-400 uppercase tracking-wider">Locations</p>
            <p className="text-2xl font-display font-bold text-gold leading-none mt-0.5">{uniqueLocations.length}</p>
            <p className="text-xs text-gray-400 mt-0.5">From Zheng He's voyages</p>
          </div>

          <div className="absolute top-4 right-4 bg-white/95 backdrop-blur-sm rounded-lg border border-gray-200 p-3 z-[1000] shadow-sm">
            <p className="text-xs font-semibold text-gray-700 mb-2">Legend</p>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500 inline-block" />
              <span className="text-xs text-gray-600">Voyage location</span>
            </div>
          </div>
        </div>

        {showDocsPanel && selectedLocation && (
          <div className="w-96 bg-white border-l border-gray-200 flex flex-col z-[999] shadow-lg">
            <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between bg-gray-50">
              <div className="min-w-0 flex-1">
                <h3 className="text-sm font-bold text-gold">{selectedLocation.name}</h3>
                <p className="text-xs text-gray-400 mt-0.5 leading-snug">{selectedLocation.event}</p>
              </div>
              <button onClick={() => setShowDocsPanel(false)}
                className="text-gray-400 hover:text-gray-600 flex-shrink-0 ml-2">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="px-4 py-2 border-b border-gray-100 flex justify-between items-center">
              <p className="text-xs font-semibold text-gray-600 flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-gold" />
                Related Documents ({relatedDocs.length})
              </p>
              {docsLoading && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gold" />
              )}
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
              {docsLoading && (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gold" />
                </div>
              )}
              {!docsLoading && relatedDocs.length === 0 && (
                <div className="text-center py-6">
                  <p className="text-xs text-gray-400 mb-3">
                    No relevant documents found for "{selectedLocation.name}".
                  </p>
                  <p className="text-xs text-gray-400 mb-3">
                    Try searching the Documents page directly.
                  </p>
                  <button
                    onClick={() => navigate(`/documents?search=${encodeURIComponent(selectedLocation.name)}`)}
                    className="text-xs text-gold font-semibold hover:underline">
                    Search documents manually →
                  </button>
                </div>
              )}
              {!docsLoading && relatedDocs.map((doc, index) => (
                <div key={doc.id}
                  className={`rounded-lg border p-3 transition-colors ${
                    index === 0 
                      ? "border-gold bg-gold/5" 
                      : "border-gray-200 bg-gray-50 hover:border-gold/40"
                  }`}>
                  <div className="flex items-start gap-2">
                    {index === 0 && (
                      <div className="flex-shrink-0 w-5 h-5 rounded-full bg-gold flex items-center justify-center">
                        <span className="text-white text-[10px] font-bold">1</span>
                      </div>
                    )}
                    {index === 1 && (
                      <div className="flex-shrink-0 w-5 h-5 rounded-full bg-gray-400 flex items-center justify-center">
                        <span className="text-white text-[10px] font-bold">2</span>
                      </div>
                    )}
                    {index === 2 && (
                      <div className="flex-shrink-0 w-5 h-5 rounded-full bg-amber-600 flex items-center justify-center">
                        <span className="text-white text-[10px] font-bold">3</span>
                      </div>
                    )}
                    {index > 2 && (
                      <div className="flex-shrink-0 w-5 h-5 rounded-full bg-gray-300 flex items-center justify-center">
                        <span className="text-gray-600 text-[10px] font-bold">{index + 1}</span>
                      </div>
                    )}
                    <div className="flex-1">
                      <p className={`text-xs font-semibold leading-snug ${index === 0 ? "text-gold" : "text-gray-900"}`}>
                        {doc.title}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {[
                          doc.author !== "Unknown" && doc.author,
                          doc.year > 0 && doc.year,
                          doc.type && doc.type !== "unknown" && doc.type,
                        ].filter(Boolean).join(" · ")}
                      </p>
                      <button
                        onClick={() => navigate(`/documents?search=${encodeURIComponent(doc.id)}`)}
                        className="mt-2 text-xs text-gold font-semibold flex items-center gap-1 hover:underline">
                        <FileText className="h-3 w-3" /> View Document
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="px-4 py-3 border-t border-gray-100">
              <button
                onClick={() => navigate(`/documents?search=${encodeURIComponent(selectedLocation.name)}`)}
                className="w-full text-xs text-gold font-semibold flex items-center justify-center gap-1.5 hover:underline">
                <FileText className="h-3.5 w-3.5" />
                Search all documents
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}