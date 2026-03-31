import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  MapContainer, TileLayer, Marker, Popup,
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

// Define search variations for each location to improve matching
const getSearchVariations = (loc: Location): string[] => {
  const variations: string[] = [loc.name];
  
  // Add variations with location name plus context
  if (loc.name === "Malindi") {
    variations.push("Malindi Kenya", "Malindi East Africa", "giraffe Malindi", "Zheng He Malindi");
  } else if (loc.name === "Mogadishu") {
    variations.push("Mogadishu Somalia", "Mogadishu East Africa", "Somali coast", "Zheng He Mogadishu");
  } else if (loc.name === "Aden") {
    variations.push("Aden Yemen", "Arabian Peninsula Aden", "Zheng He Aden");
  } else if (loc.name === "Hormuz") {
    variations.push("Hormuz Persian Gulf", "Ormus", "Zheng He Hormuz", "Persian Gulf");
  } else if (loc.name === "Sri Lanka") {
    variations.push("Galle Sri Lanka", "Ceylon", "trilingual inscription", "Zheng He Sri Lanka");
  } else if (loc.name === "Calicut") {
    variations.push("Calicut India", "Kozhikode", "Malabar Coast", "Zheng He Calicut");
  } else if (loc.name === "Malacca") {
    variations.push("Malacca Malaysia", "Melaka", "Strait of Malacca", "Zheng He Malacca");
  } else if (loc.name === "Nanjing") {
    variations.push("Nanjing China", "Nanjing shipyard", "treasure fleet Nanjing", "Longjiang shipyard");
  } else if (loc.name === "Antarctica") {
    variations.push("Antarctic", "southern continent", "Hong Bao Antarctica");
  } else {
    // Generic: add location with year and key words from event
    variations.push(`${loc.name} ${loc.year}`);
    const eventWords = loc.event.split(' — ')[0];
    if (eventWords && !variations.includes(eventWords)) {
      variations.push(eventWords);
    }
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
  const [searchDebug, setSearchDebug]           = useState<string[]>([]);

  // Fetch the historically accurate locations from main.py's VOYAGE_LOCATIONS
  useEffect(() => {
    fetchLocations(1433)
      .then((d) => { setLocations(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const fetchRelatedDocs = async (loc: Location) => {
    setDocsLoading(true);
    setRelatedDocs([]);
    setSearchDebug([]);
    
    const variations = getSearchVariations(loc);
    console.log(`🔍 Searching for "${loc.name}" with variations:`, variations);
    
    try {
      let allResults: RelatedDoc[] = [];
      const seenIds = new Set<string>();
      const debugMessages: string[] = [];
      
      // Try each search variation
      for (const term of variations) {
        debugMessages.push(`Searching: "${term}"`);
        try {
          const res = await searchDocuments(term, 20);
          const results: RelatedDoc[] = res.results || [];
          debugMessages.push(`  → Found ${results.length} results`);
          
          for (const doc of results) {
            if (!seenIds.has(doc.id)) {
              seenIds.add(doc.id);
              allResults.push(doc);
            }
          }
        } catch (err) {
          debugMessages.push(`  → Error: ${err}`);
          console.error(`Search failed for "${term}":`, err);
        }
      }
      
      // Also try searching with the event text (first part)
      const eventText = loc.event.split(' — ')[0];
      if (eventText && eventText !== loc.name && !variations.includes(eventText)) {
        debugMessages.push(`Searching event text: "${eventText}"`);
        try {
          const res = await searchDocuments(eventText, 15);
          const results: RelatedDoc[] = res.results || [];
          debugMessages.push(`  → Found ${results.length} results`);
          for (const doc of results) {
            if (!seenIds.has(doc.id)) {
              seenIds.add(doc.id);
              allResults.push(doc);
            }
          }
        } catch (err) {
          debugMessages.push(`  → Error: ${err}`);
        }
      }
      
      // Also try searching with "Zheng He" plus location
      const zhengHeTerm = `Zheng He ${loc.name}`;
      debugMessages.push(`Searching: "${zhengHeTerm}"`);
      try {
        const res = await searchDocuments(zhengHeTerm, 15);
        const results: RelatedDoc[] = res.results || [];
        debugMessages.push(`  → Found ${results.length} results`);
        for (const doc of results) {
          if (!seenIds.has(doc.id)) {
            seenIds.add(doc.id);
            allResults.push(doc);
          }
        }
      } catch (err) {
        debugMessages.push(`  → Error: ${err}`);
      }
      
      // Deduplicate by title
      const seenTitles = new Set<string>();
      const unique = allResults.filter((doc: RelatedDoc) => {
        const key = doc.title.trim().toLowerCase();
        if (seenTitles.has(key)) return false;
        seenTitles.add(key);
        return true;
      });
      
      debugMessages.push(`✅ Total unique documents: ${unique.length}`);
      setSearchDebug(debugMessages);
      console.log(`📚 Found ${unique.length} documents for ${loc.name}`);
      
      setRelatedDocs(unique.slice(0, 15));
      
    } catch (err) {
      console.error("Error fetching related docs:", err);
      setSearchDebug([`Error: ${err}`]);
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

  // Deduplicate markers by name so Nanjing/Calicut only appear once
  const seen = new Set<string>();
  const uniqueLocations = locations.filter((l) => {
    if (seen.has(l.name)) return false;
    seen.add(l.name);
    return true;
  });

  return (
    <div className="flex flex-col h-full bg-gray-100">

      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm flex-shrink-0">
        <h1 className="text-xl font-display font-bold text-gray-900">Data Map</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Zheng He's voyage locations (1403–1433) — click a marker to find related documents in the knowledge base
        </p>
      </div>

      {/* Map + docs panel */}
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

          {/* Stats overlay */}
          <div className="absolute top-4 left-4 bg-white/95 backdrop-blur-sm rounded-lg border border-gray-200 px-4 py-2 z-[1000] shadow-sm">
            <p className="text-xs text-gray-400 uppercase tracking-wider">Locations</p>
            <p className="text-2xl font-display font-bold text-gold leading-none mt-0.5">{uniqueLocations.length}</p>
            <p className="text-xs text-gray-400 mt-0.5">From Zheng He's voyages</p>
          </div>

          {/* Legend */}
          <div className="absolute top-4 right-4 bg-white/95 backdrop-blur-sm rounded-lg border border-gray-200 p-3 z-[1000] shadow-sm">
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
                Documents ({relatedDocs.length})
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
                    No documents found for "{selectedLocation.name}" in the knowledge base.
                  </p>
                  <p className="text-xs text-gray-400 mb-3">
                    Try searching the Documents page directly.
                  </p>
                  <button
                    onClick={() => navigate(`/documents?search=${encodeURIComponent(selectedLocation.name)}`)}
                    className="text-xs text-gold font-semibold hover:underline">
                    Search documents manually →
                  </button>
                  
                  {/* Debug info - remove in production */}
                  {searchDebug.length > 0 && (
                    <div className="mt-4 text-left border-t border-gray-200 pt-3">
                      <p className="text-xs text-gray-400 font-mono mb-1">🔍 Debug:</p>
                      {searchDebug.slice(0, 8).map((msg, i) => (
                        <p key={i} className="text-xs text-gray-400 font-mono">{msg}</p>
                      ))}
                    </div>
                  )}
                </div>
              )}
              {!docsLoading && relatedDocs.map((doc) => (
                <div key={doc.id}
                  className="rounded-lg border border-gray-200 bg-gray-50 p-3 hover:border-gold/40 transition-colors">
                  <p className="text-xs font-semibold text-gray-900 leading-snug">{doc.title}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {[
                      doc.author !== "Unknown" && doc.author,
                      doc.year > 0 && doc.year,
                      doc.type && doc.type !== "unknown" && doc.type,
                    ].filter(Boolean).join(" · ")}
                  </p>
                  {doc.content_preview && (
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                      {doc.content_preview.substring(0, 120)}...
                    </p>
                  )}
                  <button
                    onClick={() => navigate(`/documents?search=${encodeURIComponent(doc.id)}`)}
                    className="mt-2 text-xs text-gold font-semibold flex items-center gap-1 hover:underline">
                    <FileText className="h-3 w-3" /> View in Documents
                  </button>
                </div>
              ))}
            </div>

            <div className="px-4 py-3 border-t border-gray-100">
              <button
                onClick={() => navigate(`/documents?search=${encodeURIComponent(selectedLocation.name)}`)}
                className="w-full text-xs text-gold font-semibold flex items-center justify-center gap-1.5 hover:underline">
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