import { useState, useEffect } from "react";
import { fetchLocations } from "@/lib/api";
import { 
  BarChart3, 
  PieChart, 
  TrendingUp,
  Globe,
  Calendar,
  Ship
} from "lucide-react";

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
  const [activeChart, setActiveChart] = useState<"timeline" | "regions" | "events">("timeline");

  useEffect(() => {
    fetchLocations(1421).then(data => {
      setLocations(data);
      setLoading(false);
    });
  }, []);

  // Calculate statistics
  const years = [...new Set(locations.map(l => l.year))].sort();
  
  // Group by region (approximate based on longitude)
  const regions = {
    "East Asia": locations.filter(l => l.lon > 100 && l.lon < 130),
    "Southeast Asia": locations.filter(l => l.lon > 95 && l.lon < 120 && l.lat < 20),
    "South Asia": locations.filter(l => l.lon > 70 && l.lon < 90 && l.lat > 5 && l.lat < 30),
    "Middle East": locations.filter(l => l.lon > 45 && l.lon < 60),
    "East Africa": locations.filter(l => l.lon > 35 && l.lon < 50 && l.lat < 0),
  };

  // Count by year for timeline
  const voyagesByYear = locations.reduce((acc, loc) => {
    acc[loc.year] = (acc[loc.year] || 0) + 1;
    return acc;
  }, {} as Record<number, number>);

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-gray-700 px-6 py-4">
        <h1 className="text-xl font-display font-bold text-gold">Analytics</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Voyage statistics and historical insights
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 px-6 py-4">
        <div className="bg-navy rounded-xl border border-gray-700 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-400">Total Voyages</span>
            <Ship className="h-4 w-4 text-gold" />
          </div>
          <p className="text-2xl font-display font-bold text-gold">7</p>
          <p className="text-xs text-gray-500 mt-1">Between 1405-1433</p>
        </div>
        <div className="bg-navy rounded-xl border border-gray-700 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-400">Locations Visited</span>
            <Globe className="h-4 w-4 text-gold" />
          </div>
          <p className="text-2xl font-display font-bold text-gold">{locations.length}</p>
          <p className="text-xs text-gray-500 mt-1">Across 3 continents</p>
        </div>
        <div className="bg-navy rounded-xl border border-gray-700 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-400">Years Active</span>
            <Calendar className="h-4 w-4 text-gold" />
          </div>
          <p className="text-2xl font-display font-bold text-gold">{years.length}</p>
          <p className="text-xs text-gray-500 mt-1">Peak in 1418-1421</p>
        </div>
        <div className="bg-navy rounded-xl border border-gray-700 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-400">Farthest Point</span>
            <TrendingUp className="h-4 w-4 text-gold" />
          </div>
          <p className="text-2xl font-display font-bold text-gold">Mombasa</p>
          <p className="text-xs text-gray-500 mt-1">East Africa</p>
        </div>
      </div>

      {/* Chart Navigation */}
      <div className="border-y border-gray-700 px-6">
        <div className="flex gap-6">
          <button
            onClick={() => setActiveChart("timeline")}
            className={`py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
              activeChart === "timeline"
                ? "border-gold text-gold"
                : "border-transparent text-gray-400 hover:text-gray-300"
            }`}
          >
            <BarChart3 className="h-4 w-4" />
            Voyage Timeline
          </button>
          <button
            onClick={() => setActiveChart("regions")}
            className={`py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
              activeChart === "regions"
                ? "border-gold text-gold"
                : "border-transparent text-gray-400 hover:text-gray-300"
            }`}
          >
            <PieChart className="h-4 w-4" />
            Regional Distribution
          </button>
          <button
            onClick={() => setActiveChart("events")}
            className={`py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
              activeChart === "events"
                ? "border-gold text-gold"
                : "border-transparent text-gray-400 hover:text-gray-300"
            }`}
          >
            <Calendar className="h-4 w-4" />
            Key Events
          </button>
        </div>
      </div>

      {/* Chart Area */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold"></div>
          </div>
        ) : (
          <>
            {activeChart === "timeline" && (
              <div className="space-y-4">
                <h3 className="text-md font-semibold text-gray-200">Voyage Intensity by Year</h3>
                <div className="bg-navy rounded-xl border border-gray-700 p-6">
                  <div className="space-y-3">
                    {years.map(year => (
                      <div key={year} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="text-gray-400">{year}</span>
                          <span className="text-gold">{voyagesByYear[year] || 0} locations</span>
                        </div>
                        <div className="h-2 bg-navy-light rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-gold rounded-full"
                            style={{ 
                              width: `${((voyagesByYear[year] || 0) / Math.max(...Object.values(voyagesByYear))) * 100}%` 
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeChart === "regions" && (
              <div className="space-y-4">
                <h3 className="text-md font-semibold text-gray-200">Locations by Region</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(regions).map(([region, locs]) => (
                    <div key={region} className="bg-navy rounded-xl border border-gray-700 p-4">
                      <div className="flex justify-between items-center mb-2">
                        <h4 className="text-sm font-medium text-gray-200">{region}</h4>
                        <span className="text-xs text-gold">{locs.length} locations</span>
                      </div>
                      <div className="h-2 bg-navy-light rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gold rounded-full"
                          style={{ width: `${(locs.length / locations.length) * 100}%` }}
                        />
                      </div>
                      <div className="mt-3 text-xs text-gray-400">
                        {locs.slice(0, 3).map(l => l.name).join(', ')}
                        {locs.length > 3 && ` +${locs.length - 3} more`}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeChart === "events" && (
              <div className="space-y-4">
                <h3 className="text-md font-semibold text-gray-200">Historical Timeline</h3>
                <div className="bg-navy rounded-xl border border-gray-700 p-6">
                  <div className="space-y-4">
                    {locations
                      .sort((a, b) => a.year - b.year)
                      .map((loc, idx) => (
                        <div key={idx} className="flex gap-3">
                          <div className="relative">
                            <div className="w-2 h-2 rounded-full bg-gold mt-1.5"></div>
                            {idx < locations.length - 1 && (
                              <div className="absolute top-3 left-1 w-0.5 h-12 bg-gray-700" />
                            )}
                          </div>
                          <div className="flex-1 pb-4">
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-gold">{loc.year}</span>
                              <span className="text-sm font-medium text-gray-200">{loc.name}</span>
                            </div>
                            <p className="text-xs text-gray-400 mt-1">{loc.event}</p>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}