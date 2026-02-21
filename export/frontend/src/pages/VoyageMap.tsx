import { useState, useEffect, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet";
import L from "leaflet";
import { LatLngTuple } from "leaflet";
import "leaflet/dist/leaflet.css";
import { fetchLocations } from "@/lib/api";
import { Play, Pause, RotateCcw, Clock, Zap } from "lucide-react";

// Fix for default marker icons
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

// Custom gold icon for all locations
const goldIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-gold.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Red icon for current year
const redIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

interface Location {
  name: string;
  lat: number;
  lon: number;
  year: number;
  event: string;
}

// Component to handle map animations
function MapController({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom);
  }, [center, zoom, map]);
  return null;
}

// Timeline component with speed control
function Timeline({ 
  locations, 
  currentYear, 
  onYearChange,
  isPlaying,
  onPlayPause,
  onReset,
  speed,
  onSpeedChange
}: { 
  locations: Location[];
  currentYear: number;
  onYearChange: (year: number) => void;
  isPlaying: boolean;
  onPlayPause: () => void;
  onReset: () => void;
  speed: number;
  onSpeedChange: (speed: number) => void;
}) {
  const years = [...new Set(locations.map(l => l.year))].sort((a, b) => a - b);
  const minYear = 1368; // Start from 1368
  const maxYear = years[years.length - 1] || 1433;

  return (
    <div className="bg-navy border-t border-gray-800 p-4">
      <div className="flex items-center gap-4 max-w-4xl mx-auto">
        <button
          onClick={onPlayPause}
          className="w-10 h-10 rounded-lg bg-gold text-navy-dark flex items-center justify-center hover:bg-gold/90 transition-colors"
        >
          {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
        </button>
        <button
          onClick={onReset}
          className="w-10 h-10 rounded-lg bg-navy-light text-gray-300 flex items-center justify-center hover:text-gold transition-colors border border-gray-700"
        >
          <RotateCcw className="h-5 w-5" />
        </button>
        
        {/* Speed control */}
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-gold" />
          <select
            value={speed}
            onChange={(e) => onSpeedChange(Number(e.target.value))}
            className="bg-navy-light border border-gray-700 rounded-lg px-2 py-1 text-sm text-gray-300"
          >
            <option value={1}>1x (1 sec/year)</option>
            <option value={2}>2x</option>
            <option value={5}>5x</option>
            <option value={10}>10x</option>
          </select>
        </div>
        
        <div className="flex-1 flex items-center gap-3">
          <Clock className="h-4 w-4 text-gold" />
          <span className="text-sm text-gray-300 min-w-[80px]">Year: {currentYear}</span>
          <input
            type="range"
            min={minYear}
            max={maxYear}
            value={currentYear}
            onChange={(e) => onYearChange(parseInt(e.target.value))}
            className="flex-1 h-2 bg-navy-light rounded-lg appearance-none cursor-pointer accent-gold"
          />
          <span className="text-xs text-gray-400">{minYear} - {maxYear}</span>
        </div>
      </div>
    </div>
  );
}

export default function VoyageMap() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentYear, setCurrentYear] = useState(1368); // Start at 1368
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1); // 1x speed = 1 second per year
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>([20, 100]);
  const [mapZoom, setMapZoom] = useState(4);
  const animationRef = useRef<number>();
  const lastUpdateRef = useRef<number>(Date.now());

  useEffect(() => {
    fetchLocations(1433).then(data => {
      setLocations(data);
      setLoading(false);
    });
  }, []);

  // Animation loop with speed control
  useEffect(() => {
    if (isPlaying) {
      const years = [...new Set(locations.map(l => l.year))].sort((a, b) => a - b);
      const maxYear = years[years.length - 1] || 1433;
      
      const animate = () => {
        const now = Date.now();
        const deltaTime = now - lastUpdateRef.current;
        
        // Update year based on speed (1 second = 1 year at 1x speed)
        if (deltaTime >= 1000 / speed) {
          setCurrentYear(prev => {
            if (prev >= maxYear) {
              setIsPlaying(false);
              return maxYear;
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
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    }
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying, locations, speed]);

  // Filter locations up to current year
  const visibleLocations = locations.filter(loc => loc.year <= currentYear);
  
  // Get locations for current year (for highlighting)
  const currentYearLocations = locations.filter(loc => loc.year === currentYear);

  // Create route lines
  const sortedLocations = [...visibleLocations].sort((a, b) => a.year - b.year);
  const routeLines: LatLngTuple[][] = [];
  
  for (let i = 0; i < sortedLocations.length - 1; i++) {
    routeLines.push([
      [sortedLocations[i].lat, sortedLocations[i].lon],
      [sortedLocations[i + 1].lat, sortedLocations[i + 1].lon]
    ]);
  }

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentYear(1368);
    setMapCenter([20, 100]);
    setMapZoom(4);
  };

  const handleLocationClick = (location: Location) => {
    setSelectedLocation(location);
    setMapCenter([location.lat, location.lon]);
    setMapZoom(6);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-navy-dark">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold"></div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-navy-dark">
      <div className="border-b border-gray-800 px-6 py-4 bg-navy">
        <h1 className="text-xl font-display font-bold text-gold">Voyage Map</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Explore Zheng He's treasure fleet routes (1368-1433)
        </p>
      </div>

      {/* Map Container */}
      <div className="flex-1 relative">
        <MapContainer
          center={mapCenter}
          zoom={mapZoom}
          style={{ height: "100%", width: "100%", background: "#1a2a3a" }}
          zoomControl={false}
        >
          <MapController center={mapCenter} zoom={mapZoom} />
          
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Route lines */}
          {routeLines.map((line, idx) => (
            <Polyline
              key={idx}
              positions={line}
              color="#E6B800"
              weight={3}
              opacity={0.6}
            />
          ))}

          {/* Markers for all visited locations - all gold */}
          {visibleLocations.map((loc, idx) => (
            <Marker
              key={idx}
              position={[loc.lat, loc.lon]}
              icon={goldIcon}
              eventHandlers={{
                click: () => handleLocationClick(loc)
              }}
            >
              <Popup>
                <div className="text-navy-dark">
                  <h3 className="font-bold">{loc.name}</h3>
                  <p className="text-sm">Year: {loc.year}</p>
                  <p className="text-xs">{loc.event}</p>
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Highlight current year locations in red */}
          {currentYearLocations.map((loc, idx) => (
            <Marker
              key={`current-${idx}`}
              position={[loc.lat, loc.lon]}
              icon={redIcon}
            >
              <Popup>
                <div className="text-navy-dark">
                  <h3 className="font-bold">{loc.name}</h3>
                  <p className="text-sm font-semibold text-red-600">Current Year: {loc.year}</p>
                  <p className="text-xs">{loc.event}</p>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        {/* Map Legend - simplified */}
        <div className="absolute top-4 right-4 bg-navy/90 backdrop-blur-sm rounded-lg border border-gray-800 p-3 shadow-lg z-[1000]">
          <div className="text-xs font-medium text-gold mb-2">Map Legend</div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-gold"></div>
              <span className="text-xs text-gray-300">Voyage Location</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-xs text-gray-300">Current Year</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-0.5 bg-gold"></div>
              <span className="text-xs text-gray-300">Voyage Route</span>
            </div>
          </div>
        </div>

        {/* Selected Location Info */}
        {selectedLocation && (
          <div className="absolute bottom-4 left-4 bg-navy rounded-xl border border-gray-800 p-4 shadow-lg z-[1000] max-w-sm">
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-display font-bold text-gold">{selectedLocation.name}</h3>
              <button
                onClick={() => setSelectedLocation(null)}
                className="text-gray-400 hover:text-gray-200"
              >
                ×
              </button>
            </div>
            <p className="text-sm text-gray-300 mb-1">Year: {selectedLocation.year}</p>
            <p className="text-sm text-gray-400">{selectedLocation.event}</p>
          </div>
        )}
      </div>

      {/* Timeline Component with Speed Control */}
      <Timeline
        locations={locations}
        currentYear={currentYear}
        onYearChange={setCurrentYear}
        isPlaying={isPlaying}
        onPlayPause={() => setIsPlaying(!isPlaying)}
        onReset={handleReset}
        speed={speed}
        onSpeedChange={setSpeed}
      />
    </div>
  );
}