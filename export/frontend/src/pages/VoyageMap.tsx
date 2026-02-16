import { useState, useEffect, useRef } from "react";
import { MapContainer, TileLayer, CircleMarker, Polyline, Popup, Tooltip } from "react-leaflet";
import { Play, Pause, RotateCcw } from "lucide-react";
import "leaflet/dist/leaflet.css";

const LOCATIONS = [
  { name: "Nanjing", lat: 32.06, lon: 118.80, year: 1368, event: "Early Ming capital established" },
  { name: "Beijing", lat: 39.90, lon: 116.41, year: 1403, event: "Capital moved to Beijing" },
  { name: "Champa", lat: 10.82, lon: 106.63, year: 1405, event: "Southeast Asian ally" },
  { name: "Calicut", lat: 11.26, lon: 75.78, year: 1406, event: "Zheng He fleet first arrived" },
  { name: "Sumatra", lat: -0.59, lon: 101.34, year: 1407, event: "Strategic trading post established" },
  { name: "Java", lat: -7.61, lon: 110.71, year: 1407, event: "Diplomatic missions conducted" },
  { name: "Siam", lat: 13.74, lon: 100.52, year: 1408, event: "Diplomatic relations established" },
  { name: "Malacca", lat: 2.19, lon: 102.25, year: 1409, event: "Strategic port established" },
  { name: "Sri Lanka", lat: 7.87, lon: 80.77, year: 1409, event: "Trilingual inscription erected" },
  { name: "Hormuz", lat: 27.16, lon: 56.28, year: 1414, event: "Persian Gulf trade route opened" },
  { name: "Aden", lat: 12.79, lon: 45.02, year: 1417, event: "Arabian Peninsula contact made" },
  { name: "Mombasa", lat: -4.04, lon: 39.67, year: 1418, event: "East African trade commenced" },
  { name: "Mogadishu", lat: 2.05, lon: 45.32, year: 1418, event: "Somali coast exploration" },
  { name: "Zanzibar", lat: -6.17, lon: 39.20, year: 1419, event: "Trade agreements established" },
];

export default function VoyageMap() {
  const [currentYear, setCurrentYear] = useState(1368);
  const [isPlaying, setIsPlaying] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const filtered = LOCATIONS.filter((l) => l.year <= currentYear).sort((a, b) => a.year - b.year);
  const routeCoords: [number, number][] = filtered.map((l) => [l.lat, l.lon]);

  useEffect(() => {
    if (isPlaying) {
      intervalRef.current = setInterval(() => {
        setCurrentYear((y) => {
          if (y >= 1421) { setIsPlaying(false); return 1421; }
          return y + 1;
        });
      }, 500);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [isPlaying]);

  const reset = () => { setIsPlaying(false); setCurrentYear(1368); };

  return (
    <div className="p-6 space-y-5 h-full overflow-y-auto">
      <div>
        <h1 className="text-2xl font-display font-bold text-gold">Voyage Map</h1>
        <p className="text-sm text-gray-400">Explore Zheng He's maritime routes across Asia and Africa</p>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-4 rounded-xl bg-navy border border-gray-700 p-4">
        <div className="flex items-center gap-2">
          <button onClick={() => setIsPlaying(!isPlaying)} className="h-9 w-9 rounded-lg bg-gold flex items-center justify-center text-navy-dark hover:bg-gold-light transition">
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </button>
          <button onClick={reset} className="h-9 w-9 rounded-lg border border-gray-600 flex items-center justify-center text-gray-400 hover:text-gray-200 hover:bg-white/5 transition">
            <RotateCcw className="h-4 w-4" />
          </button>
        </div>
        <input type="range" min={1368} max={1421} value={currentYear} onChange={(e) => setCurrentYear(Number(e.target.value))} className="flex-1 min-w-[200px] accent-[#d4af37]" />
        <span className="text-lg font-display font-bold text-gold min-w-[4ch]">{currentYear}</span>
      </div>

      {/* Leaflet Map */}
      <div className="rounded-xl overflow-hidden border border-gray-700" style={{ height: 480 }}>
        <MapContainer center={[15, 80]} zoom={3} style={{ height: "100%", width: "100%" }} scrollWheelZoom={true}>
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />
          {routeCoords.length > 1 && (
            <Polyline positions={routeCoords} pathOptions={{ color: "#d4af37", weight: 3, opacity: 0.8, dashArray: "10 5" }} />
          )}
          {filtered.map((loc) => (
            <CircleMarker key={loc.name} center={[loc.lat, loc.lon]} radius={7} pathOptions={{ color: "#d4af37", fillColor: "#d4af37", fillOpacity: 0.8 }}>
              <Tooltip>{loc.name}</Tooltip>
              <Popup>
                <strong>{loc.name}</strong><br />
                {loc.year} — {loc.event}
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>

      {/* Timeline */}
      <div>
        <h2 className="text-lg font-display font-bold mb-3">Timeline</h2>
        <div className="space-y-2">
          {filtered.map((loc) => (
            <div key={loc.name} className="flex items-start gap-4 rounded-xl bg-navy border border-gray-700 p-4">
              <div className="flex-shrink-0 h-10 w-10 rounded-lg bg-gold flex items-center justify-center">
                <span className="text-xs font-bold text-navy-dark">{loc.year}</span>
              </div>
              <div>
                <p className="text-sm font-semibold">{loc.name}</p>
                <p className="text-xs text-gray-400">{loc.event}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
