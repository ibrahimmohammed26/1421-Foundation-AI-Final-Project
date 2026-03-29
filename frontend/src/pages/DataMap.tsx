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
  content_preview: string;
}

export default function DataMap() {
  const navigate = useNavigate();

  const [locations, setLocations]               = useState<Location[]>([]);
  const [loading, setLoading]                   = useState(true);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [relatedDocs, setRelatedDocs]           = useState<RelatedDoc[]>([]);
  const [docsLoading, setDocsLoading]           = useState(false);
  const [showDocsPanel, setShowDocsPanel]       = useState(false);

  useEffect(() => {
    fetchLocations(1433).then((d) => { setLocations(d); setLoading(false); });
  }, []);

  const fetchRelatedDocs = async (loc: Location) => {
    setDocsLoading(true);
    setRelatedDocs([]);
    try {
      const res = await searchDocuments(`${loc.name} ${loc.event} Zheng He`, 10);
      const seen = new Set<string>();
      const unique = (res.results as RelatedDoc[]).filter((doc) => {
        const key = doc.title.trim().toLowerCase().replace(/^[\d\s"']+/, "");
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      setRelatedDocs(unique.slice(0, 5));
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

  // Deduplicate locations by name+year for display
  const seen = new Set<string>();
  const uniqueLocations = locations.filter((l) => {
    const key = `${l.name}-${l.year}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  return (
    <div className="flex flex-col h-full bg-gray-100">

      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm flex-shrink-0">
        <h1 className="text-xl font-display font-bold text-gray-900">Data Map</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Explore Zheng He's voyage locations (1403–1433) — click a marker to view related documents
        </p>
      </div>

      {/* Map + docs panel */}
      <div className="relative flex-1 min-h-0 flex">
        <div className="flex-1 relative">
          <MapContainer
            center={[20, 80]}
            zoom={3}
            style={{ height: "100%", width: "100%" }}
            zoomControl={true}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {uniqueLocations.map((loc, idx) => (
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
                    <p className="text-xs mt-1 text-gray-700">{loc.event}</p>
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

          {/* Location count overlay */}
          <div className="absolute top-4 left-4 bg-white/95 backdrop-blur-sm rounded-lg border border-gray-200 px-4 py-2 z-[1000] shadow-sm">
            <p className="text-xs text-gray-400 uppercase tracking-wider">Locations</p>
            <p className="text-2xl font-display font-bold text-gold leading-none mt-0.5">{uniqueLocations.length}</p>
            <p className="text-xs text-gray-400 mt-0.5">Across 3 continents</p>
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
          <div className="w-80 bg-white border-l border-gray-200 flex flex-col z-[999] shadow-lg">
            <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between bg-gray-50">
              <div>
                <h3 className="text-sm font-bold text-gold">{selectedLocation.name}</h3>
                <p className="text-xs text-gray-400">Year {selectedLocation.year} · {selectedLocation.event}</p>
              </div>
              <button onClick={() => setShowDocsPanel(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="px-4 py-2 border-b border-gray-100">
              <p className="text-xs font-semibold text-gray-600 flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-gold" />
                Related documents from knowledge base
              </p>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
              {docsLoading && (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gold" />
                </div>
              )}
              {!docsLoading && relatedDocs.length === 0 && (
                <p className="text-xs text-gray-400 text-center py-6">No related documents found for this location.</p>
              )}
              {!docsLoading && relatedDocs.map((doc) => (
                <div key={doc.id} className="rounded-lg border border-gray-200 bg-gray-50 p-3 hover:border-gold/40 transition-colors">
                  <p className="text-xs font-semibold text-gray-900 leading-snug">{doc.title}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {[doc.author !== "Unknown" && doc.author, doc.year > 0 && doc.year, doc.type].filter(Boolean).join(" · ")}
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
          </div>
        )}
      </div>
    </div>
  );
}