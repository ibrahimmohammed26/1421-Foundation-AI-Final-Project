import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  MapContainer, TileLayer, Marker, Popup, ZoomControl,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { fetchLocations, searchDocuments } from "@/lib/api";
import { FileText, X } from "lucide-react";

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
}

interface RelatedDoc {
  id: string;
  title: string;
  author: string;
  year: number;
  type: string;
  url?: string;
}

// Extract locations from document content
function extractLocationsFromDocuments(documents: RelatedDoc[]): Location[] {
  const extractedLocations: Location[] = [];
  const knownLocations = new Set<string>();
  
  const locationDatabase: Record<string, { lat: number; lon: number; region: string }> = {
    "beijing": { lat: 39.9042, lon: 116.4074, region: "China" },
    "nanjing": { lat: 32.0603, lon: 118.7969, region: "China" },
    "shanghai": { lat: 31.2304, lon: 121.4737, region: "China" },
    "calicut": { lat: 11.2588, lon: 75.7804, region: "India" },
    "malacca": { lat: 2.1896, lon: 102.2501, region: "Southeast Asia" },
    "hormuz": { lat: 27.1600, lon: 56.2800, region: "Middle East" },
    "aden": { lat: 12.8000, lon: 45.0333, region: "Middle East" },
    "malindi": { lat: -3.2192, lon: 40.1169, region: "Africa" },
    "mombasa": { lat: -4.0435, lon: 39.6682, region: "Africa" },
    "zanzibar": { lat: -6.1659, lon: 39.2026, region: "Africa" },
    "java": { lat: -7.6145, lon: 110.7123, region: "Southeast Asia" },
    "sumatra": { lat: -0.7893, lon: 101.8772, region: "Southeast Asia" },
    "sri lanka": { lat: 7.8731, lon: 80.7718, region: "South Asia" },
    "australia": { lat: -25.2744, lon: 133.7751, region: "Australia" },
    "darwin": { lat: -12.4634, lon: 130.8456, region: "Australia" },
    "sydney": { lat: -33.8688, lon: 151.2093, region: "Australia" },
  };
  
  for (const doc of documents) {
    const searchText = `${doc.title} ${doc.content_preview || ""}`.toLowerCase();
    
    for (const [locationName, coords] of Object.entries(locationDatabase)) {
      if (searchText.includes(locationName) && !knownLocations.has(locationName)) {
        knownLocations.add(locationName);
        extractedLocations.push({
          name: locationName.charAt(0).toUpperCase() + locationName.slice(1),
          lat: coords.lat,
          lon: coords.lon,
          year: doc.year || 1421,
          event: `Referenced in: ${doc.title.substring(0, 100)}`,
          sourceDoc: doc.title
        });
      }
    }
  }
  
  return extractedLocations;
}

export default function DataMap() {
  const navigate = useNavigate();

  const [staticLocations, setStaticLocations] = useState<Location[]>([]);
  const [dynamicLocations, setDynamicLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [relatedDocs, setRelatedDocs] = useState<RelatedDoc[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [showDocsPanel, setShowDocsPanel] = useState(false);

  useEffect(() => {
    const loadAllLocations = async () => {
      setLoading(true);
      try {
        const staticLocs = await fetchLocations(1433);
        setStaticLocations(staticLocs);
        
        const locationSearchTerms = [
          "voyage", "expedition", "port", "harbor", "coast", "island",
          "China", "India", "Africa", "Australia", "America", "Europe"
        ];
        
        const allDocResults = await Promise.all(
          locationSearchTerms.map(term => searchDocuments(term, 30).catch(() => ({ results: [] })))
        );
        
        const allDocs = allDocResults.flatMap(r => r.results || []);
        const uniqueDocs = Array.from(new Map(allDocs.map(d => [d.id, d])).values());
        
        const dynamicLocs = extractLocationsFromDocuments(uniqueDocs);
        setDynamicLocations(dynamicLocs);
        
      } catch (error) {
        console.error("Error loading locations:", error);
      } finally {
        setLoading(false);
      }
    };
    
    loadAllLocations();
  }, []);

  const fetchRelatedDocs = async (loc: Location) => {
    setDocsLoading(true);
    setRelatedDocs([]);
    try {
      const res = await searchDocuments(loc.name, 15);
      const results = res.results || [];

      const seen = new Set<string>();
      const unique = results.filter((doc: RelatedDoc) => {
        const key = doc.title.trim().toLowerCase();
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });

      const cleanResults = unique.map((doc: RelatedDoc) => {
        const { similarity_score, ...rest } = doc;
        return rest;
      });

      setRelatedDocs(cleanResults.slice(0, 10));
    } catch {
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

  const allLocations = [...staticLocations];
  const seenNames = new Set(staticLocations.map(l => l.name.toLowerCase()));
  
  for (const dynLoc of dynamicLocations) {
    if (!seenNames.has(dynLoc.name.toLowerCase())) {
      allLocations.push(dynLoc);
      seenNames.add(dynLoc.name.toLowerCase());
    }
  }

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
        <h1 className="text-xl font-display font-bold text-gray-900">Data Map</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Explore Zheng He's voyage locations — click a marker to find related documents from the knowledge base
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
            zoomControlPosition="topright"
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {allLocations.map((loc, idx) => (
              <Marker
                key={idx}
                position={[loc.lat, loc.lon]}
                icon={redIcon}
                eventHandlers={{ click: () => handleLocationClick(loc) }}
              >
                <Popup>
                  <div className="text-sm">
                    <p className="font-bold text-gray-900">{loc.name}</p>
                    <p className="text-xs text-gray-500">Year {loc.year}</p>
                    <p className="text-xs mt-1 text-gray-700">{loc.event.substring(0, 100)}...</p>
                    <button
                      onClick={() => handleLocationClick(loc)}
                      className="mt-2 text-xs text-gold font-semibold flex items-center gap-1 hover:underline"
                    >
                      <FileText className="h-3 w-3" /> View related documents
                    </button>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>

          {/* Stats overlay - top right */}
          <div className="absolute top-4 right-14 bg-white/95 backdrop-blur-sm rounded-lg border border-gray-200 px-4 py-2 z-[1000] shadow-sm">
            <p className="text-xs text-gray-400 uppercase tracking-wider">Locations</p>
            <p className="text-2xl font-display font-bold text-gold leading-none mt-0.5">{allLocations.length}</p>
            <p className="text-xs text-gray-400 mt-0.5">Across {regions.size} regions</p>
            {dynamicLocations.length > 0 && (
              <p className="text-xs text-gray-400 mt-1">+{dynamicLocations.length} from documents</p>
            )}
          </div>

          {/* Legend - NOW ON TOP LEFT */}
          <div className="absolute top-4 left-4 bg-white/95 backdrop-blur-sm rounded-lg border border-gray-200 p-3 z-[1000] shadow-sm">
            <p className="text-xs font-semibold text-gray-700 mb-2">Legend</p>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500 inline-block" />
              <span className="text-xs text-gray-600">Voyage location</span>
            </div>
            <p className="text-xs text-gray-400 mt-2 italic">Click a marker for docs</p>
          </div>
        </div>

        {/* Related documents side panel */}
        {showDocsPanel && selectedLocation && (
          <div className="w-80 bg-white border-l border-gray-200 flex flex-col z-[999] shadow-lg">
            <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between bg-gray-50">
              <div className="min-w-0">
                <h3 className="text-sm font-bold text-gold">{selectedLocation.name}</h3>
                <p className="text-xs text-gray-400 mt-0.5 leading-snug">{selectedLocation.event.substring(0, 80)}...</p>
              </div>
              <button onClick={() => setShowDocsPanel(false)} className="text-gray-400 hover:text-gray-600 flex-shrink-0 ml-2">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="px-4 py-2 border-b border-gray-100">
              <p className="text-xs font-semibold text-gray-600 flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-gold" />
                Related documents from knowledge base
              </p>
              <p className="text-xs text-gray-400 mt-0.5">Using same search as chat</p>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
              {docsLoading && (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gold" />
                </div>
              )}
              {!docsLoading && relatedDocs.length === 0 && (
                <div className="text-center py-6">
                  <p className="text-xs text-gray-400">No documents found mentioning "{selectedLocation.name}" in the knowledge base.</p>
                  <button
                    onClick={() => navigate(`/documents?search=${encodeURIComponent(selectedLocation.name)}`)}
                    className="mt-3 text-xs text-gold font-semibold hover:underline"
                  >
                    Search documents manually →
                  </button>
                </div>
              )}
              {!docsLoading && relatedDocs.map((doc) => (
                <div key={doc.id} className="rounded-lg border border-gray-200 bg-gray-50 p-3 hover:border-gold/40 transition-colors">
                  <p className="text-xs font-semibold text-gray-900 leading-snug">{doc.title}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {[
                      doc.author !== "Unknown" && doc.author,
                      doc.year > 0 && doc.year,
                      doc.type && doc.type !== "unknown" && doc.type,
                    ].filter(Boolean).join(" · ")}
                  </p>
                  <button
                    onClick={() => navigate(`/documents?search=${encodeURIComponent(doc.id)}`)}
                    className="mt-2 text-xs text-gold font-semibold flex items-center gap-1 hover:underline"
                  >
                    <FileText className="h-3 w-3" /> View in Documents
                  </button>
                </div>
              ))}
            </div>

            <div className="px-4 py-3 border-t border-gray-100">
              <button
                onClick={() => navigate(`/documents?search=${encodeURIComponent(selectedLocation.name)}`)}
                className="w-full text-xs text-gold font-semibold flex items-center justify-center gap-1.5 hover:underline"
              >
                <FileText className="h-3.5 w-3.5" />
                Search all documents for "{selectedLocation.name}"
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}