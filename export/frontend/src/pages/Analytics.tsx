import { useState, useEffect } from "react";
import { api } from "@/lib/api";

export default function Analytics() {
  const [locations, setLocations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getLocations(1421).then(data => {
      setLocations(data);
      setLoading(false);
    });
  }, []);

  // Group locations by year
  const locationsByYear = locations.reduce((acc, loc) => {
    if (!acc[loc.year]) acc[loc.year] = [];
    acc[loc.year].push(loc);
    return acc;
  }, {} as Record<number, any[]>);

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-gray-700 px-6 py-4">
        <h1 className="text-xl font-display font-bold text-gold">Analytics</h1>
        <p className="text-xs text-gray-400 mt-0.5">Voyage data and insights</p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        {loading ? (
          <div className="flex items-center justify-center h-full">
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