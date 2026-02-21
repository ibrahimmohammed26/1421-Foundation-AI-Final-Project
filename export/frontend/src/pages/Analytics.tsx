import { useState, useEffect } from "react";
import { fetchLocations } from "@/lib/api";  // Import your existing function

interface Location {
  name: string;
  lat: number;
  lon: number;
  year: number;
  event: string;
}

export default function Analytics() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [maxYear, setMaxYear] = useState(1421);

  useEffect(() => {
    const loadLocations = async () => {
      try {
        const data = await fetchLocations(maxYear);
        setLocations(data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching locations:', error);
        setLoading(false);
      }
    };

    loadLocations();
  }, [maxYear]);

  // Group locations by year
  const locationsByYear = locations.reduce((acc, loc) => {
    if (!acc[loc.year]) acc[loc.year] = [];
    acc[loc.year].push(loc);
    return acc;
  }, {} as Record<number, Location[]>);

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-gray-700 px-6 py-4">
        <h1 className="text-xl font-display font-bold text-gold">Analytics</h1>
        <p className="text-xs text-gray-400 mt-0.5">Voyage data and insights</p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        {/* Year filter */}
        <div className="mb-6 bg-navy rounded-xl border border-gray-700 p-4">
          <label className="block text-sm text-gray-400 mb-2">Filter by year (up to)</label>
          <input
            type="range"
            min="1368"
            max="1421"
            value={maxYear}
            onChange={(e) => setMaxYear(parseInt(e.target.value))}
            className="w-full accent-gold"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>1368</span>
            <span className="text-gold font-medium">{maxYear}</span>
            <span>1421</span>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold"></div>
          </div>
        ) : (
          <div className="space-y-6">
            {Object.entries(locationsByYear)
              .sort(([a], [b]) => Number(a) - Number(b))
              .map(([year, locs]) => (
                <div key={year} className="bg-navy rounded-xl border border-gray-700 p-6">
                  <h3 className="text-lg font-display font-bold text-gold mb-4">Year {year}</h3>
                  <div className="space-y-3">
                    {locs.map((loc, idx) => (
                      <div key={idx} className="border-l-2 border-gold pl-4">
                        <p className="font-medium text-gray-200">{loc.name}</p>
                        <p className="text-sm text-gray-400">{loc.event}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          Coordinates: {loc.lat}°, {loc.lon}°
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}