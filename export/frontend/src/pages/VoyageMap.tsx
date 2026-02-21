import { useState, useEffect, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet";
import L from "leaflet";
import type { LatLngTuple } from "leaflet";
import "leaflet/dist/leaflet.css";
import { fetchLocations } from "@/lib/api";
import { Play, Pause, RotateCcw, Clock } from "lucide-react";

// Fix for default marker icons in React-Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

// Custom ship icon for start/end points
const shipIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-gold.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Custom port icon
const portIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png",
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

// Timeline component
function Timeline({ 
  locations, 
  currentYear, 
  onYearChange,
  isPlaying,
  onPlayPause,
  onReset 
}: { 
  locations: Location[];
  currentYear: number;
  onYearChange: (year: number) => void;
  isPlaying: boolean;
  onPlayPause: () => void;
  onReset: () => void;
}) {
  const years = [...new Set(locations.map(l => l.year))].sort((a, b) => a - b);
  const minYear = years[0] || 1405;
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
        
        <div className="flex-1 flex items-center gap-3">
          <Clock className="h-4 w-4 text-gold" />
          <span className="text-sm text-gray-300 min-w-[60px]">Year: {currentYear}</span>
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
  const [currentYear, setCurrentYear] = useState(1405);
  const [isPlaying, setIsPlaying] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>([20, 100]); // Center on Southeast Asia
  const [mapZoom, setMapZoom] = useState(4);
  const animationRef = useRef<number>();

  useEffect(() => {
    fetchLocations(1433).then(data => {
      setLocations(data);
      setLoading(false);
    });
  }, []);

  // Animation loop
  useEffect(() => {
    if (isPlaying) {
      const years = [...new Set(locations.map(l => l.year))].sort((a, b) => a - b);
      const maxYear = years[years.length - 1] || 1433;
      
      const animate = () => {
        setCurrentYear(prev => {
          if (prev >= maxYear) {
            setIsPlaying(false);
            return maxYear;
          }
          return prev + 1;
        });
        animationRef.current = requestAnimationFrame(animate);
      };
      
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
  }, [isPlaying, locations]);

  // Filter locations up to current year
  const visibleLocations = locations.filter(loc => loc.year <= currentYear);
  
  // Get locations for current year (for highlighting)
  const currentYearLocations = locations.filter(loc => loc.year === currentYear);

  // Create route lines
  const sortedLocations = [...visibleLocations].sort((a, b) => a.year - b.year);
  const routeLines = [];
  
  for (let i = 0; i < sortedLocations.length - 1; i++) {
    routeLines.push([
      [sortedLocations[i].lat, sortedLocations[i].lon],
      [sortedLocations[i + 1].lat, sortedLocations[i + 1].lon]
    ]);
  }

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentYear(1405);
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

  const years = [...new Set(locations.map(l => l.year))].sort((a, b) => a - b);
  const firstLocation = locations.find(l => l.year === Math.min(...years)) || locations[0];

  return (
    <div className="flex flex-col h-full bg-navy-dark">
      <div className="border-b border-gray-800 px-6 py-4 bg-navy">
        <h1 className="text-xl font-display font-bold text-gold">Voyage Map</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Explore Zheng He's treasure fleet routes (1405-1433)
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
          
          {/* Base map layers */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          {/* Add satellite layer option */}
          <TileLayer
            attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            opacity={0.7}
          />

          {/* Route lines */}
          {routeLines.map((line, idx) => (
            <Polyline
              key={idx}
              positions={line as LatLngTuple[]}
              color="#E6B800"
              weight={3}
              opacity={0.8}
              dashArray={idx === routeLines.length - 1 ? "5, 5" : undefined}
            />
          ))}

          {/* Markers for all visited locations */}
          {visibleLocations.map((loc, idx) => (
            <Marker
              key={idx}
              position={[loc.lat, loc.lon]}
              icon={loc.year === 1405 || loc.year === 1433 ? shipIcon : portIcon}
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

          {/* Highlight current year locations */}
          {currentYearLocations.map((loc, idx) => (
            <Marker
              key={`current-${idx}`}
              position={[loc.lat, loc.lon]}
              icon={new L.Icon({
                iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
                shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
              })}
            >
              <Popup>
                <div className="text-navy-dark">
                  <h3 className="font-bold">{loc.name}</h3>
                  <p className="text-sm">Current Year: {loc.year}</p>
                  <p className="text-xs">{loc.event}</p>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        {/* Map Legend */}
        <div className="absolute top-4 right-4 bg-navy/90 backdrop-blur-sm rounded-lg border border-gray-800 p-3 shadow-lg z-[1000]">
          <div className="text-xs font-medium text-gold mb-2">Map Legend</div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-gold"></div>
              <span className="text-xs text-gray-300">Start/End (1405/1433)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span className="text-xs text-gray-300">Major Port</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-xs text-gray-300">Current Year</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-0.5 bg-gold"></div>
              <span className="text-xs text-gray-300">Trade Route</span>
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
            <p className="text-xs text-gray-500 mt-2">
              Coordinates: {selectedLocation.lat.toFixed(2)}°N, {selectedLocation.lon.toFixed(2)}°E
            </p>
          </div>
        )}
      </div>

      {/* Timeline Component */}
      <Timeline
        locations={locations}
        currentYear={currentYear}
        onYearChange={setCurrentYear}
        isPlaying={isPlaying}
        onPlayPause={() => setIsPlaying(!isPlaying)}
        onReset={handleReset}
      />
    </div>
  );
}