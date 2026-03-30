import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  MapContainer, TileLayer, Marker, Popup, ZoomControl,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { fetchLocations, searchDocuments, getDocumentById } from "@/lib/api";
import { FileText, X, ExternalLink } from "lucide-react";

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
  sourceDoc?: string;
  sourceDocId?: string;  // Add document ID for direct linking
  sourceUrl?: string;     // Add URL for external linking
}

interface RelatedDoc {
  id: string;
  title: string;
  author: string;
  year: number;
  type: string;
  url?: string;
  content_preview?: string;
}

// Pre-defined locations with their associated document IDs from your knowledge base
const PREDEFINED_LOCATIONS: Location[] = [
  { 
    name: "Nanjing", lat: 32.0603, lon: 118.7969, year: 1405, 
    event: "Yongle Emperor commissions the treasure fleet. First voyage departs with 317 ships and 28,000 men.",
    sourceDocId: "1", sourceDoc: "1421: The Year China Discovered America"
  },
  { 
    name: "Champa", lat: 10.8231, lon: 106.6297, year: 1405, 
    event: "First stop on Voyage 1 — Southeast Asian ally (modern Vietnam)",
    sourceDocId: "2", sourceDoc: "1421 evidence documents"
  },
  { 
    name: "Java", lat: -7.6145, lon: 110.7123, year: 1406, 
    event: "Diplomatic missions conducted on Java",
    sourceDocId: "3", sourceDoc: "1421 evidence documents"
  },
  { 
    name: "Malacca", lat: 2.1896, lon: 102.2501, year: 1406, 
    event: "Key port established, local piracy suppressed",
    sourceDocId: "4", sourceDoc: "1421 evidence documents"
  },
  { 
    name: "Calicut", lat: 11.2588, lon: 75.7804, year: 1407, 
    event: "Primary destination on the Malabar Coast, India. Zheng He dies here in 1433.",
    sourceDocId: "5", sourceDoc: "1421 evidence documents"
  },
  { 
    name: "Sri Lanka", lat: 7.8731, lon: 80.7718, year: 1409, 
    event: "Trilingual inscription erected at Galle (Chinese, Tamil, Persian)",
    sourceDocId: "6", sourceDoc: "1421 evidence documents"
  },
  { 
    name: "Hormuz", lat: 27.1600, lon: 56.2800, year: 1414, 
    event: "Persian Gulf reached — 18 states sent tribute",
    sourceDocId: "7", sourceDoc: "1421 evidence documents"
  },
  { 
    name: "Aden", lat: 12.8000, lon: 45.0333, year: 1417, 
    event: "Arabian Peninsula reached, gifts of zebras and lions received",
    sourceDocId: "8", sourceDoc: "1421 evidence documents"
  },
  { 
    name: "Mogadishu", lat: 2.0500, lon: 45.3200, year: 1418, 
    event: "Somali coast — first Chinese fleet to reach East Africa",
    sourceDocId: "9", sourceDoc: "1421 evidence documents"
  },
  { 
    name: "Malindi", lat: -3.2192, lon: 40.1169, year: 1418, 
    event: "Kenya coast — famous giraffe gifted to the Yongle Emperor",
    sourceDocId: "10", sourceDoc: "1421 evidence documents"
  },
];

export default function DataMap() {
  const navigate = useNavigate();

  const [staticLocations, setStaticLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [relatedDocs, setRelatedDocs] = useState<RelatedDoc[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [showDocsPanel, setShowDocsPanel] = useState(false);

  useEffect(() => {
    const loadLocations = async () => {
      setLoading(true);
      try {
        // Try to fetch from API first
        const apiLocations = await fetchLocations(1433);
        
        if (apiLocations && apiLocations.length > 0) {
          // Use API locations if available
          setStaticLocations(apiLocations);
        } else {
          // Fallback to predefined locations
          setStaticLocations(PREDEFINED_LOCATIONS);
        }
      } catch (error) {
        console.error("Error loading locations:", error);
        // Use predefined locations as fallback
        setStaticLocations(PREDEFINED_LOCATIONS);
      } finally {
        setLoading(false);
      }
    };
    
    loadLocations();
  }, []);

  const fetchRelatedDocs = async (loc: Location) => {
    setDocsLoading(true);
    setRelatedDocs([]);
    
    try {
      let results: RelatedDoc[] = [];
      
      // If location has a specific document ID, fetch that document directly
      if (loc.sourceDocId) {
        try {
          const doc = await getDocumentById(loc.sourceDocId);
          if (doc) {
            results.push({
              id: doc.id,
              title: doc.title,
              author: doc.author || "Gavin Menzies",
              year: doc.year || loc.year,
              type: doc.type || "document",
              url: doc.url,
              content_preview: doc.content_preview || loc.event
            });
          }
        } catch (e) {
          console.log("Direct doc fetch failed, falling back to search");
        }
      }
      
      // Also search for documents related to this location
      const searchQueries = [
        loc.name,
        `${loc.name} Zheng He`,
        `${loc.name} treasure fleet`,
        loc.event.split('.')[0].substring(0, 50)
      ];
      
      for (const query of searchQueries) {
        if (results.length >= 8) break;
        
        try {
          const searchRes = await searchDocuments(query, 5);
          const searchResults = searchRes.results || [];
          
          for (const doc of searchResults) {
            // Check if this document is about the location
            const docText = `${doc.title} ${doc.content_preview || ""}`.toLowerCase();
            const locationName = loc.name.toLowerCase();
            
            if (docText.includes(locationName) && !results.some(r => r.id === doc.id)) {
              results.push({
                id: doc.id,
                title: doc.title,
                author: doc.author || "Gavin Menzies",
                year: doc.year || 0,
                type: doc.type || "document",
                url: doc.url,
                content_preview: doc.content_preview
              });
            }
          }
        } catch (e) {
          console.log(`Search failed for ${query}`);
        }
      }
      
      // If still no results, create a placeholder that links to general search
      if (results.length === 0) {
        results.push({
          id: "search",
          title: `Search all documents for "${loc.name}"`,
          author: "1421 Foundation",
          year: loc.year,
          type: "search_suggestion",
          url: `/documents?search=${encodeURIComponent(loc.name)}`,
          content_preview: `Click to search for documents about ${loc.name}`
        });
      }
      
      setRelatedDocs(results.slice(0, 10));
      
    } catch (error) {
      console.error("Error fetching related docs:", error);
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

  const handleDocClick = (doc: RelatedDoc) => {
    if (doc.id === "search") {
      // Navigate to search page
      navigate(doc.url || `/documents?search=${encodeURIComponent(selectedLocation?.name || "")}`);
    } else if (doc.url && doc.url.startsWith("http")) {
      // Open external URL in new tab
      window.open(doc.url, "_blank");
    } else {
      // Navigate to document in the documents page
      navigate(`/documents?search=${encodeURIComponent(doc.id)}`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-100">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold" />
      </div>
    );
  }

  const allLocations = staticLocations;
  const regions = new Set(allLocations.map(l => {
    if (l.lat > -10 && l.lat < 50 && l.lon > 60 && l.lon < 150) return "Asia";
    if (l.lat > -35 && l.lat < 15 && l.lon > 20 && l.lon < 55) return "Africa";
    if (l.lat > -45 && l.lat < -10 && l.lon > 110 && l.lon < 155) return "Australia";
    if (l.lat > -60 && l.lat < 30 && l.lon > -130 && l.lon < -60) return "Americas";
    return "Other";
  }));

  return (
    <div className="flex flex-col h-full bg-gray-100">

      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm flex-shrink-0">
        <h1 className="text-xl font-display font-bold text-gray-900">Zheng He's Voyage Map</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Click any marker to see related documents from the 1421 Foundation knowledge base
        </p>
      </div>

      {/* Map + docs panel */}
      <div className="relative flex-1 min-h-0 flex">
        <div className="flex-1 relative">
          <MapContainer
            center={[20, 80]}
            zoom={2}
            style={{ height: "100%", width: "100%" }}
            zoomControl={true}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {allLocations.map((loc, idx) => (
              <Marker
                key={`${loc.name}-${idx}`}
                position={[loc.lat, loc.lon]}
                icon={redIcon}
                eventHandlers={{ click: () => handleLocationClick(loc) }}
              >
                <Popup>
                  <div className="text-sm max-w-xs">
                    <p className="font-bold text-gray-900 text-base">{loc.name}</p>
                    <p className="text-xs text-gray-500 mt-0.5">Year {loc.year}</p>
                    <p className="text-xs mt-2 text-gray-700 leading-relaxed">{loc.event}</p>
                    <button
                      onClick={() => handleLocationClick(loc)}
                      className="mt-3 w-full text-xs text-gold font-semibold flex items-center justify-center gap-1.5 hover:underline py-1.5 border-t border-gray-100"
                    >
                      <FileText className="h-3 w-3" /> View related documents
                    </button>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>

          {/* Stats overlay */}
          <div className="absolute top-4 right-4 bg-white/95 backdrop-blur-sm rounded-lg border border-gray-200 px-4 py-2 z-[1000] shadow-sm">
            <p className="text-xs text-gray-400 uppercase tracking-wider">Voyage Locations</p>
            <p className="text-2xl font-display font-bold text-gold leading-none mt-0.5">{allLocations.length}</p>
            <p className="text-xs text-gray-400 mt-0.5">Across {regions.size} regions</p>
            <p className="text-xs text-gray-400 mt-1">1405-1433 CE</p>
          </div>

          {/* Legend */}
          <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur-sm rounded-lg border border-gray-200 p-3 z-[1000] shadow-sm">
            <p className="text-xs font-semibold text-gray-700 mb-2">Legend</p>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500 inline-block" />
              <span className="text-xs text-gray-600">Zheng He voyage stop</span>
            </div>
            <p className="text-xs text-gray-400 mt-2 italic">Click any marker for source documents</p>
          </div>
        </div>

        {/* Related documents side panel */}
        {showDocsPanel && selectedLocation && (
          <div className="w-96 bg-white border-l border-gray-200 flex flex-col z-[999] shadow-xl">
            <div className="px-5 py-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
              <div className="min-w-0 flex-1">
                <h3 className="text-lg font-display font-bold text-gold">{selectedLocation.name}</h3>
                <p className="text-xs text-gray-500 mt-1">Year {selectedLocation.year}</p>
                <p className="text-xs text-gray-600 mt-2 leading-relaxed">{selectedLocation.event}</p>
              </div>
              <button 
                onClick={() => setShowDocsPanel(false)} 
                className="text-gray-400 hover:text-gray-600 flex-shrink-0 ml-3 p-1"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="px-5 py-3 border-b border-gray-100 bg-white">
              <p className="text-xs font-semibold text-gray-700 flex items-center gap-2">
                <FileText className="h-3.5 w-3.5 text-gold" />
                Related Documents in Knowledge Base
              </p>
              <p className="text-xs text-gray-400 mt-1">Click any document to view full content</p>
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
              {docsLoading && (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold" />
                </div>
              )}
              
              {!docsLoading && relatedDocs.length === 0 && (
                <div className="text-center py-8">
                  <FileText className="h-10 w-10 text-gray-300 mx-auto mb-3" />
                  <p className="text-sm text-gray-500">No documents found mentioning "{selectedLocation.name}"</p>
                  <button
                    onClick={() => navigate(`/documents?search=${encodeURIComponent(selectedLocation.name)}`)}
                    className="mt-4 text-sm text-gold font-semibold hover:underline inline-flex items-center gap-1"
                  >
                    Search all documents →
                  </button>
                </div>
              )}
              
              {!docsLoading && relatedDocs.map((doc, idx) => (
                <div 
                  key={doc.id} 
                  className="rounded-lg border border-gray-200 bg-white p-4 hover:border-gold/50 hover:shadow-md transition-all cursor-pointer"
                  onClick={() => handleDocClick(doc)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-bold text-gold bg-gold/10 px-2 py-0.5 rounded">
                          #{idx + 1}
                        </span>
                        {doc.type && doc.type !== "search_suggestion" && (
                          <span className="text-xs text-gray-400 capitalize">{doc.type}</span>
                        )}
                      </div>
                      <p className="text-sm font-semibold text-gray-900 leading-snub break-words">
                        {doc.title}
                      </p>
                      {doc.author && doc.author !== "Unknown" && (
                        <p className="text-xs text-gray-500 mt-1">by {doc.author}</p>
                      )}
                      {doc.content_preview && doc.type !== "search_suggestion" && (
                        <p className="text-xs text-gray-500 mt-2 line-clamp-2">
                          {doc.content_preview.substring(0, 150)}...
                        </p>
                      )}
                    </div>
                    <ExternalLink className="h-4 w-4 text-gray-400 flex-shrink-0 mt-1" />
                  </div>
                </div>
              ))}
            </div>

            <div className="px-5 py-3 border-t border-gray-100 bg-gray-50">
              <button
                onClick={() => navigate(`/documents?search=${encodeURIComponent(selectedLocation.name)}`)}
                className="w-full text-sm text-gold font-semibold flex items-center justify-center gap-2 py-2 hover:underline"
              >
                <FileText className="h-4 w-4" />
                View all documents about {selectedLocation.name}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}