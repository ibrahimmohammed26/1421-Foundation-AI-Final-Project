import { useState, useEffect, useRef } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  useMap,
} from "react-leaflet";
import L, { LatLngTuple } from "leaflet";
import "leaflet/dist/leaflet.css";
import { fetchLocations } from "@/lib/api";
import { Play, Pause, RotateCcw, Zap, MapPin, Clock } from "lucide-react";

// ── Fix default marker icons ──────────────────────────────────────────
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

const goldIcon = new L.Icon({
  iconUrl:
    "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-gold.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const redIcon = new L.Icon({
  iconUrl:
    "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

interface Location {
  name: string;
  lat: number;
  lon: number;
  year: number;
  event: string;
}

// ── Map view controller ───────────────────────────────────────────────
function MapController({
  center,
  zoom,
}: {
  center: [number, number];
  zoom: number;
}) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom, { animate: true });
  }, [center, zoom, map]);
  return null;
}

// ── Main component ────────────────────────────────────────────────────
export default function VoyageMap() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentYear, setCurrentYear] = useState(1368);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>([20, 100]);
  const [mapZoom, setMapZoom] = useState(4);
  const animationRef = useRef<number>();
  const lastUpdateRef = useRef<number>(Date.now());

  const MIN_YEAR = 1368;
  const MAX_YEAR = 1421;

  useEffect(() => {
    // Fetch all locations up to 1421
    fetchLocations(MAX_YEAR).then((data) => {
      setLocations(data);
      setLoading(false);
    });
  }, []);

  // ── Animation loop ──────────────────────────────────────────────────
  useEffect(() => {
    if (isPlaying) {
      const animate = () => {
        const now = Date.now();
        const delta = now - lastUpdateRef.current;
        if (delta >= 1000 / speed) {
          setCurrentYear((prev) => {
            if (prev >= MAX_YEAR) {
              setIsPlaying(false);
              return MAX_YEAR;
            }
            return prev + 1;
          });
          lastUpdateRef.current = now;
        }
        animationRef.current = requestAnimationFrame(animate);
      };
      lastUpdateRef.current = Date.now();
      animationRef.current = requestAnimationFrame(animate);
    } else {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    }
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [isPlaying, speed]);

  // Derived data
  const visibleLocations = locations.filter((l) => l.year <= currentYear);
  const currentYearLocations = locations.filter((l) => l.year === currentYear);

  // Build route lines between chronologically sorted visible locations
  const sorted = [...visibleLocations].sort((a, b) => a.year - b.year);
  const routeLines: LatLngTuple[][] = [];
  for (let i = 0; i < sorted.length - 1; i++) {
    routeLines.push([
      [sorted[i].lat, sorted[i].lon],
      [sorted[i + 1].lat, sorted[i + 1].lon],
    ]);
  }

  // Progress percentage for slider fill
  const progress = ((currentYear - MIN_YEAR) / (MAX_YEAR - MIN_YEAR)) * 100;

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentYear(MIN_YEAR);
    setMapCenter([20, 100]);
    setMapZoom(4);
    setSelectedLocation(null);
  };

  const handleLocationClick = (loc: Location) => {
    setSelectedLocation(loc);
    setMapCenter([loc.lat, loc.lon]);
    setMapZoom(6);
  };

  // Locations that have appeared at or before current year, for timeline description list
  const recentLocations = [...visibleLocations]
    .sort((a, b) => b.year - a.year)
    .slice(0, 6);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-navy-dark">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-navy-dark">
      {/* ── Page header ──────────────────────────────────────────────── */}
      <div className="border-b border-gray-800 px-6 py-4 bg-navy flex-shrink-0">
        <h1 className="text-xl font-display font-bold text-gold">Voyage Map</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Explore Zheng He's treasure fleet routes ({MIN_YEAR}–{MAX_YEAR})
        </p>
      </div>

      {/* ── Map ──────────────────────────────────────────────────────── */}
      <div className="flex-1 relative min-h-0">
        <MapContainer
          center={mapCenter}
          zoom={mapZoom}
          style={{ height: "100%", width: "100%" }}
          zoomControl={true}
        >
          <MapController center={mapCenter} zoom={mapZoom} />

          {/*
            English-only tile layer using Stadia Maps (Stamen Toner Lite).
            All labels are in English regardless of zoom level.
            No API key required for moderate usage.
          */}
          <TileLayer
            attribution='&copy; <a href="https://stadia.com" target="_blank">Stadia Maps</a> &copy; <a href="https://stamen.com" target="_blank">Stamen Design</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://tiles.stadiamaps.com/tiles/stamen_toner_lite/{z}/{x}/{y}{r}.png"
          />

          {/* Route lines */}
          {routeLines.map((line, idx) => (
            <Polyline
              key={idx}
              positions={line}
              color="#E6B800"
              weight={2.5}
              opacity={0.65}
              dashArray="6 4"
            />
          ))}

          {/* Past/visited locations — gold */}
          {visibleLocations.map((loc, idx) => (
            <Marker
              key={`v-${idx}`}
              position={[loc.lat, loc.lon]}
              icon={goldIcon}
              eventHandlers={{ click: () => handleLocationClick(loc) }}
            >
              <Popup>
                <div className="text-sm">
                  <p className="font-bold">{loc.name}</p>
                  <p className="text-xs text-gray-600">Year {loc.year}</p>
                  <p className="text-xs mt-1">{loc.event}</p>
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Current year locations — red highlight */}
          {currentYearLocations.map((loc, idx) => (
            <Marker
              key={`c-${idx}`}
              position={[loc.lat, loc.lon]}
              icon={redIcon}
            >
              <Popup>
                <div className="text-sm">
                  <p className="font-bold">{loc.name}</p>
                  <p className="text-xs font-semibold text-red-600">
                    ▶ Year {loc.year}
                  </p>
                  <p className="text-xs mt-1">{loc.event}</p>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        {/* Map legend */}
        <div className="absolute top-4 right-4 bg-navy/90 backdrop-blur-sm rounded-lg border border-gray-800 p-3 shadow-lg z-[1000]">
          <p className="text-xs font-semibold text-gold mb-2">Legend</p>
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-[#E6B800] inline-block" />
              <span className="text-xs text-gray-300">Visited location</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500 inline-block" />
              <span className="text-xs text-gray-300">Current year</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-5 h-0.5 border-t-2 border-dashed border-[#E6B800] inline-block" />
              <span className="text-xs text-gray-300">Voyage route</span>
            </div>
          </div>
        </div>

        {/* Year counter overlay */}
        <div className="absolute top-4 left-4 bg-navy/90 backdrop-blur-sm rounded-lg border border-gray-800 px-4 py-2 z-[1000]">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Year</p>
          <p className="text-2xl font-display font-bold text-gold leading-none mt-0.5">
            {currentYear}
          </p>
          <p className="text-xs text-gray-400 mt-0.5">
            {visibleLocations.length} location{visibleLocations.length !== 1 ? "s" : ""} reached
          </p>
        </div>

        {/* Selected location detail panel */}
        {selectedLocation && (
          <div className="absolute bottom-4 left-4 bg-navy rounded-xl border border-gray-800 p-4 shadow-lg z-[1000] max-w-xs">
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-display font-bold text-gold text-sm">
                {selectedLocation.name}
              </h3>
              <button
                onClick={() => setSelectedLocation(null)}
                className="text-gray-500 hover:text-gray-300 ml-2 text-lg leading-none"
              >
                ×
              </button>
            </div>
            <p className="text-xs text-gray-400 mb-1">Year {selectedLocation.year}</p>
            <p className="text-xs text-gray-300 leading-relaxed">
              {selectedLocation.event}
            </p>
          </div>
        )}
      </div>

      {/* ── Timeline controls ─────────────────────────────────────────── */}
      <div className="bg-navy border-t border-gray-800 px-6 py-4 flex-shrink-0">
        {/* Controls row */}
        <div className="flex items-center gap-4 mb-4">
          {/* Play / Pause */}
          <button
            onClick={() => setIsPlaying((p) => !p)}
            className="w-10 h-10 rounded-lg bg-gold text-navy-dark flex items-center justify-center hover:bg-gold/90 transition-colors flex-shrink-0"
          >
            {isPlaying ? (
              <Pause className="h-4 w-4" />
            ) : (
              <Play className="h-4 w-4" />
            )}
          </button>

          {/* Reset */}
          <button
            onClick={handleReset}
            className="w-10 h-10 rounded-lg border border-gray-700 text-gray-400 flex items-center justify-center hover:text-gold hover:border-gold/50 transition-colors flex-shrink-0"
          >
            <RotateCcw className="h-4 w-4" />
          </button>

          {/* Speed */}
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-gold flex-shrink-0" />
            <select
              value={speed}
              onChange={(e) => setSpeed(Number(e.target.value))}
              className="bg-navy-dark border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-gray-300 focus:outline-none focus:ring-1 focus:ring-gold/50"
            >
              <option value={1}>1× speed</option>
              <option value={2}>2× speed</option>
              <option value={5}>5× speed</option>
              <option value={10}>10× speed</option>
            </select>
          </div>

          {/* Slider + year labels */}
          <div className="flex-1 flex items-center gap-3">
            <span className="text-xs text-gray-500 flex-shrink-0">{MIN_YEAR}</span>
            <div className="flex-1 relative">
              {/* Progress fill bar */}
              <div className="relative h-2 bg-navy-dark rounded-full border border-gray-700">
                <div
                  className="absolute inset-y-0 left-0 bg-gold rounded-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <input
                type="range"
                min={MIN_YEAR}
                max={MAX_YEAR}
                value={currentYear}
                onChange={(e) => setCurrentYear(parseInt(e.target.value))}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
            </div>
            <span className="text-xs text-gray-500 flex-shrink-0">{MAX_YEAR}</span>
          </div>

          {/* Current year label */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <Clock className="h-3.5 w-3.5 text-gold" />
            <span className="text-sm font-semibold text-gold w-10">{currentYear}</span>
          </div>
        </div>

        {/* ── Location descriptions below slider ──────────────────────── */}
        <div className="border-t border-gray-800 pt-3">
          <div className="flex items-center gap-2 mb-2">
            <MapPin className="h-3.5 w-3.5 text-gold" />
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Locations reached by {currentYear}
            </p>
            <span className="ml-auto text-xs text-gray-600">
              {visibleLocations.length} of {locations.length}
            </span>
          </div>

          {visibleLocations.length === 0 ? (
            <p className="text-xs text-gray-600 italic">
              Move the slider or press play to reveal voyage locations.
            </p>
          ) : (
            <div className="flex gap-3 overflow-x-auto pb-1 scrollbar-thin">
              {recentLocations.map((loc, idx) => (
                <button
                  key={idx}
                  onClick={() => handleLocationClick(loc)}
                  className={`flex-shrink-0 rounded-lg border px-3 py-2 text-left transition-colors min-w-[150px] max-w-[200px] ${
                    selectedLocation?.name === loc.name
                      ? "border-gold/60 bg-gold/10"
                      : "border-gray-700 bg-navy-dark hover:border-gold/40 hover:bg-gold/5"
                  }`}
                >
                  <p className="text-xs font-semibold text-gray-200 truncate">
                    {loc.name}
                  </p>
                  <p className="text-xs text-gold mt-0.5">{loc.year}</p>
                  <p className="text-xs text-gray-500 mt-0.5 line-clamp-2 leading-tight">
                    {loc.event}
                  </p>
                </button>
              ))}

              {visibleLocations.length > 6 && (
                <div className="flex-shrink-0 flex items-center px-3 text-xs text-gray-600">
                  +{visibleLocations.length - 6} more
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}