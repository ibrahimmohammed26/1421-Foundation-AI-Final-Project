import { useState, useEffect } from "react";
import { fetchLocations } from "@/lib/api";

interface Location {
  name: string;
  lat: number;
  lon: number;
  year: number;
  event: string;
}

export default function VoyageMap() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [mapType, setMapType] = useState<"terrain" | "satellite">("terrain");
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);

  useEffect(() => {
    fetchLocations(1421).then(data => {
      setLocations(data);
      setLoading(false);
    });
  }, []);

  // This is a placeholder - you'll need to integrate with a real map library
  // like Leaflet, Google Maps, or Mapbox
  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-gray-700 px-6 py-4">
        <h1 className="text-xl font-display font-bold text-gold">Voyage Map</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Explore Zheng He's treasure fleet routes (1405-1433)
        </p>
      </div>

      {/* Map Controls */}
      <div className="px-6 py-3 border-b border-gray-700 bg-navy-light">
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            <button
              onClick={() => setMapType("terrain")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                mapType === "terrain"
                  ? "bg-gold text-navy-dark"
                  : "bg-navy text-gray-400 hover:text-gray-200"
              }`}
            >
              Terrain
            </button>
            <button
              onClick={() => setMapType("satellite")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                mapType === "satellite"
                  ? "bg-gold text-navy-dark"
                  : "bg-navy text-gray-400 hover:text-gray-200"
              }`}
            >
              Satellite
            </button>
          </div>
          <div className="text-xs text-gray-400">
            {locations.length} locations across 3 continents
          </div>
        </div>
      </div>

      {/* Map Container - Light background for visibility */}
      <div className="flex-1 relative bg-gray-100">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold"></div>
          </div>
        ) : (
          <>
            {/* Placeholder for actual map */}
            <div className="absolute inset-0 p-6">
              <div className="bg-white/90 backdrop-blur-sm rounded-xl border border-gray-200 p-6 shadow-lg max-w-md">
                <h3 className="text-lg font-display font-bold text-navy-dark mb-4">
                  Voyage Locations
                </h3>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {locations.map((loc, idx) => (
                    <div
                      key={idx}
                      onClick={() => setSelectedLocation(loc)}
                      className={`p-3 rounded-lg cursor-pointer transition-colors ${
                        selectedLocation?.name === loc.name
                          ? "bg-gold/20 border border-gold/50"
                          : "hover:bg-gray-100 border border-transparent"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-navy-dark">{loc.name}</span>
                        <span className="text-xs text-gray-500">{loc.year}</span>
                      </div>
                      <p className="text-xs text-gray-600 mt-1">{loc.event}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Map Legend */}
            <div className="absolute bottom-6 right-6 bg-white/90 backdrop-blur-sm rounded-lg border border-gray-200 p-3 shadow-lg">
              <div className="text-xs font-medium text-navy-dark mb-2">Map Legend</div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-gold"></div>
                  <span className="text-xs text-gray-600">Voyage Start/End</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                  <span className="text-xs text-gray-600">Major Port</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-0.5 h-4 bg-gold"></div>
                  <span className="text-xs text-gray-600">Trade Route</span>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Selected Location Info */}
      {selectedLocation && (
        <div className="absolute bottom-6 left-6 bg-white rounded-xl border border-gray-200 p-4 shadow-lg max-w-sm">
          <div className="flex justify-between items-start mb-2">
            <h3 className="font-display font-bold text-navy-dark">{selectedLocation.name}</h3>
            <button
              onClick={() => setSelectedLocation(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
          <p className="text-sm text-gray-600 mb-1">Year: {selectedLocation.year}</p>
          <p className="text-sm text-gray-600">{selectedLocation.event}</p>
          <p className="text-xs text-gray-400 mt-2">
            Coordinates: {selectedLocation.lat}°N, {selectedLocation.lon}°E
          </p>
        </div>
      )}
    </div>
  );
}