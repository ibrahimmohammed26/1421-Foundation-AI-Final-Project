import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  MapContainer, TileLayer, Marker, Popup, Polyline, useMap,
} from "react-leaflet";
import L, { LatLngTuple } from "leaflet";
import "leaflet/dist/leaflet.css";
import { fetchLocations, searchDocuments } from "@/lib/api";
import { Play, Pause, RotateCcw, Zap, MapPin, Clock, FileText, X } from "lucide-react";

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
const greyIcon = new L.Icon({
  iconUrl:   "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-grey.png",
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

function MapController({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => { map.setView(center, zoom, { animate: true }); }, [center, zoom, map]);
  return null;
}

export default function VoyageMap() {
  const navigate = useNavigate();

  const [locations, setLocations]               = useState<Location[]>([]);
  const [loading, setLoading]                   = useState(true);
  const [currentYear, setCurrentYear]           = useState(1403);
  const [isPlaying, setIsPlaying]               = useState(false);
  const [speed, setSpeed]                       = useState(1);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [relatedDocs, setRelatedDocs]           = useState<RelatedDoc[]>([]);
  const [docsLoading, setDocsLoading]           = useState(false);
  const [showDocsPanel, setShowDocsPanel]       = useState(false);
  const [mapCenter, setMapCenter]               = useState<[number, number]>([20, 100]);
  const [mapZoom, setMapZoom]                   = useState(4);
  const animationRef  = useRef<number>();
  const lastUpdateRef = useRef<number>(Date.now());

  const MIN_YEAR = 1403;
  const MAX_YEAR = 1433;

  useEffect(() => {
    fetchLocations(MAX_YEAR).then((d) => { setLocations(d); setLoading(false); });
  }, []);

  useEffect(() => {
    if (isPlaying) {
      const tick = () => {
        const now   = Date.now();
        const delta = now - lastUpdateRef.current;
        if (delta >= 1000 / speed) {
          setCurrentYear((prev) => {
            if (prev >= MAX_YEAR) { setIsPlaying(false); return MAX_YEAR; }
            return prev + 1;
          });
          lastUpdateRef.current = now;
        }
        animationRef.current = requestAnimationFrame(tick);
      };
      lastUpdateRef.current = Date.now();
      animationRef.current  = requestAnimationFrame(tick);
    } else {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    }
    return () => { if (animationRef.current) cancelAnimationFrame(animationRef.current); };
  }, [isPlaying, speed]);

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
    setMapCenter([loc.lat, loc.lon]);
    setMapZoom(6);
    setShowDocsPanel(true);
    fetchRelatedDocs(loc);
  };

  const visibleLocations     = locations.filter((l) => l.year <= currentYear);
  const currentYearLocations = locations.filter((l) => l.year === currentYear);
  const sorted = [...visibleLocations].sort((a, b) => a.year - b.year);
  const routeLines: LatLngTuple[][] = [];
  for (let i = 0; i < sorted.length - 1; i++) {
    routeLines.push([
      [sorted[i].lat, sorted[i].lon],
      [sorted[i + 1].lat, sorted[i + 1].lon],
    ]);
  }

  const progress = ((currentYear - MIN_YEAR) / (MAX_YEAR - MIN_YEAR)) * 100;

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentYear(MIN_YEAR);
    setMapCenter([20, 100]);
    setMapZoom(4);
    setSelectedLocation(null);
    setShowDocsPanel(false);
  };

  const timelineLocations = [...visibleLocations].sort((a, b) => b.year - a.year);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-100">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-100">

      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm flex-shrink-0">
        <h1 className="text-xl font-display font-bold text-gray-900">Voyage Map</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Explore Zheng He's voyage routes ({MIN_YEAR}–{MAX_YEAR}) — click a location to view related documents
        </p>
      </div>

      {/* Map + docs panel */}
      <div className="relative flex-1 min-h-0 flex">
        <div className="flex-1 relative">
          <MapContainer center={mapCenter} zoom={mapZoom} style={{ height: "100%", width: "100%" }} zoomControl={true}>
            <MapController center={mapCenter} zoom={mapZoom} />
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {routeLines.map((line, idx) => (
              <Polyline key={idx} positions={line} color="#c0272d" weight={2.5} opacity={0.7} dashArray="6 4" />
            ))}
            {visibleLocations.map((loc, idx) => (
              <Marker key={`v-${idx}`} position={[loc.lat, loc.lon]} icon={greyIcon}
                eventHandlers={{ click: () => handleLocationClick(loc) }}>
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
            {currentYearLocations.map((loc, idx) => (
              <Marker key={`c-${idx}`} position={[loc.lat, loc.lon]} icon={redIcon}
                eventHandlers={{ click: () => handleLocationClick(loc) }}>
                <Popup>
                  <div className="text-sm">
                    <p className="font-bold text-gray-900">{loc.name}</p>
                    <p className="text-xs font-semibold text-red-600">▶ Year {loc.year}</p>
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

          {/* Year overlay */}
          <div className="absolute top-4 left-4 bg-white/95 backdrop-blur-sm rounded-lg border border-gray-200 px-4 py-2 z-[1000] shadow-sm">
            <p className="text-xs text-gray-400 uppercase tracking-wider">Year</p>
            <p className="text-2xl font-display font-bold text-gold leading-none mt-0.5">{currentYear}</p>
            <p className="text-xs text-gray-400 mt-0.5">{visibleLocations.length} location{visibleLocations.length !== 1 ? "s" : ""} reached</p>
          </div>

          {/* Legend */}
          <div className="absolute top-4 right-4 bg-white/95 backdrop-blur-sm rounded-lg border border-gray-200 p-3 z-[1000] shadow-sm">
            <p className="text-xs font-semibold text-gray-700 mb-2">Legend</p>
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-gray-400 inline-block" />
                <span className="text-xs text-gray-600">Visited location</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-gold inline-block" />
                <span className="text-xs text-gray-600">Current year</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-5 h-0.5 border-t-2 border-dashed border-gold inline-block" />
                <span className="text-xs text-gray-600">Voyage route</span>
              </div>
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
                  {doc.content_preview && (
                    <p className="text-xs text-gray-600 mt-1.5 leading-relaxed line-clamp-3">{doc.content_preview}</p>
                  )}
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

      {/* Slider controls */}
      <div className="bg-white border-t border-gray-200 px-6 py-4 flex-shrink-0 shadow-sm">
        <div className="flex items-center gap-4">
          <button onClick={() => setIsPlaying((p) => !p)}
            className="w-10 h-10 rounded-lg bg-gold text-white flex items-center justify-center hover:bg-gold-light transition-colors flex-shrink-0 shadow-sm">
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </button>
          <button onClick={handleReset}
            className="w-10 h-10 rounded-lg border border-gray-300 text-gray-500 flex items-center justify-center hover:text-gold hover:border-gold/50 transition-colors flex-shrink-0">
            <RotateCcw className="h-4 w-4" />
          </button>
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-gold flex-shrink-0" />
            <select value={speed} onChange={(e) => setSpeed(Number(e.target.value))}
              className="bg-white border border-gray-300 rounded-lg px-2 py-1.5 text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-gold/50">
              <option value={1}>1× speed</option>
              <option value={2}>2× speed</option>
              <option value={5}>5× speed</option>
              <option value={10}>10× speed</option>
            </select>
          </div>
          <div className="flex-1 flex items-center gap-3">
            <span className="text-xs text-gray-400 flex-shrink-0">{MIN_YEAR}</span>
            <div className="flex-1 relative h-2">
              <div className="absolute inset-0 bg-gray-200 rounded-full" />
              <div className="absolute inset-y-0 left-0 bg-gold rounded-full transition-all" style={{ width: `${progress}%` }} />
              <input type="range" min={MIN_YEAR} max={MAX_YEAR} value={currentYear}
                onChange={(e) => setCurrentYear(parseInt(e.target.value))}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
            </div>
            <span className="text-xs text-gray-400 flex-shrink-0">{MAX_YEAR}</span>
          </div>
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <Clock className="h-3.5 w-3.5 text-gold" />
            <span className="text-sm font-semibold text-gold w-10">{currentYear}</span>
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-white border-t border-gray-200 flex-shrink-0" style={{ maxHeight: "220px" }}>
        <div className="px-6 py-2 border-b border-gray-100 flex items-center gap-2 sticky top-0 bg-white z-10">
          <MapPin className="h-4 w-4 text-gold flex-shrink-0" />
          <p className="text-sm font-semibold text-gray-800">Locations reached by {currentYear}</p>
          <span className="ml-auto text-xs font-medium text-gold bg-red-50 px-2 py-0.5 rounded-full border border-gold/20">
            {visibleLocations.length} / {locations.length}
          </span>
        </div>
        <div className="overflow-y-auto" style={{ maxHeight: "172px" }}>
          {timelineLocations.length === 0 ? (
            <div className="px-6 py-4 text-xs text-gray-400 text-center">Press play or move the slider to reveal voyage locations</div>
          ) : (
            <div className="px-6 py-2">
              <div className="space-y-0">
                {timelineLocations.map((loc, idx) => {
                  const isCurrent  = loc.year === currentYear;
                  const isSelected = selectedLocation?.name === loc.name;
                  return (
                    <button key={idx} onClick={() => handleLocationClick(loc)}
                      className={`w-full text-left flex items-start gap-3 py-2.5 pl-2 pr-2 rounded-lg transition-colors ${isSelected ? "bg-red-50" : "hover:bg-gray-50"}`}>
                      <span className={`mt-1 w-3.5 h-3.5 rounded-full border-2 flex-shrink-0 ${isCurrent ? "bg-gold border-gold shadow-sm" : isSelected ? "bg-gold/50 border-gold/50" : "bg-white border-gray-300"}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-xs font-bold ${isCurrent ? "text-gold" : "text-gray-400"}`}>{loc.year}</span>
                          {isCurrent && <span className="text-[10px] font-semibold bg-gold text-white px-1.5 py-0.5 rounded-full leading-none">NOW</span>}
                          <span className={`text-sm font-semibold ${isSelected ? "text-gold" : "text-gray-800"}`}>{loc.name}</span>
                        </div>
                        <p className="text-xs text-gray-500 leading-snug mt-0.5 truncate">{loc.event}</p>
                        {isSelected && (
                          <p className="text-xs text-gold mt-0.5 flex items-center gap-1">
                            <FileText className="h-3 w-3" /> {docsLoading ? "Loading docs..." : `${relatedDocs.length} related doc${relatedDocs.length !== 1 ? "s" : ""}`}
                          </p>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}