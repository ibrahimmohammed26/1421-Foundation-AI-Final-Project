import { useState, useEffect } from "react";
import { fetchLocations } from "@/lib/api";
import { 
  BarChart3, 
  PieChart, 
  TrendingUp,
  Globe,
  Calendar,
  Ship,
  Anchor,
  Compass
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
  const [activeChart, setActiveChart] = useState<"timeline" | "regions" | "stats">("timeline");

  useEffect(() => {
    fetchLocations(1433).then(data => {
      setLocations(data);
      setLoading(false);
    });
  }, []);

  // Calculate statistics
  const years = [...new Set(locations.map(l => l.year))].sort((a, b) => a - b);
  
  // Group by region (approximate based on longitude)
  const regions = {
    "China": locations.filter(l => l.lon > 100 && l.lon < 125 && l.lat > 20),
    "Southeast Asia": locations.filter(l => l.lon > 95 && l.lon < 120 && l.lat < 20 && l.lat > -10),
    "South Asia": locations.filter(l => l.lon > 65 && l.lon < 95 && l.lat > 5 && l.lat < 30),
    "Middle East": locations.filter(l => l.lon > 45 && l.lon < 65 && l.lat > 10),
    "East Africa": locations.filter(l => l.lon > 35 && l.lon < 55 && l.lat < 0),
  };

  // Count by year for timeline
  const voyagesByYear = locations.reduce((acc, loc) => {
    acc[loc.year] = (acc[loc.year] || 0) + 1;
    return acc;
  }, {} as Record<number, number>);

  const maxVoyages = Math.max(...Object.values(voyagesByYear));

  // Voyage numbers by period
  const periods = {
    "First Voyage (1405-1407)": locations.filter(l => l.year >= 1405 && l.year <= 1407).length,
    "Second Voyage (1407-1409)": locations.filter(l => l.year >= 1407 && l.year <= 1409).length,
    "Third Voyage (1409-1411)": locations.filter(l => l.year >= 1409 && l.year <= 1411).length,
    "Fourth Voyage (1413-1415)": locations.filter(l => l.year >= 1413 && l.year <= 1415).length,
    "Fifth Voyage (1417-1419)": locations.filter(l => l.year >= 1417 && l.year <= 1419).length,
    "Sixth Voyage (1421-1422)": locations.filter(l => l.year >= 1421 && l.year <= 1422).length,
    "Seventh Voyage (1431-1433)": locations.filter(l => l.year >= 1431 && l.year <= 1433).length,
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
        <h1 className="text-xl font-display font-bold text-gold">Analytics</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Voyage statistics and historical insights
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 px-6 py-4">
        <div className="bg-navy rounded-xl border border-gray-800 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-400">Total Voyages</span>
            <Ship className="h-4 w-4 text-gold" />
          </div>
          <p className="text-2xl font-display font-bold text-gold">7</p>
          <p className="text-xs text-gray-500 mt-1">Between 1405-1433</p>
        </div>
        <div className="bg-navy rounded-xl border border-gray-800 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-400">Locations Visited</span>
            <Globe className="h-4 w-4 text-gold" />
          </div>
          <p className="text-2xl font-display font-bold text-gold">{locations.length}</p>
          <p className="text-xs text-gray-500 mt-1">Across 3 continents</p>
        </div>
        <div className="bg-navy rounded-xl border border-gray-800 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-400">Years Active</span>
            <Calendar className="h-4 w-4 text-gold" />
          </div>
          <p className="text-2xl font-display font-bold text-gold">{years.length}</p>
          <p className="text-xs text-gray-500 mt-1">Peak in 1418-1421</p>
        </div>
        <div className="bg-navy rounded-xl border border-gray-800 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-400">Farthest Point</span>
            <Compass className="h-4 w-4 text-gold" />
          </div>
          <p className="text-2xl font-display font-bold text-gold">Mombasa</p>
          <p className="text-xs text-gray-500 mt-1">East Africa</p>
        </div>
      </div>

      {/* Chart Navigation */}
      <div className="border-y border-gray-800 px-6 bg-navy">
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
            onClick={() => setActiveChart("stats")}
            className={`py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
              activeChart === "stats"
                ? "border-gold text-gold"
                : "border-transparent text-gray-400 hover:text-gray-300"
            }`}
          >
            <TrendingUp className="h-4 w-4" />
            Voyage Statistics
          </button>
        </div>
      </div>

      {/* Chart Area */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {activeChart === "timeline" && (
          <div className="space-y-4">
            <h3 className="text-md font-semibold text-gray-200">Number of Locations Visited by Year</h3>
            <div className="bg-navy rounded-xl border border-gray-800 p-6">
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
                          width: `${((voyagesByYear[year] || 0) / maxVoyages) * 100}%` 
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
                <div key={region} className="bg-navy rounded-xl border border-gray-800 p-4">
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

        {activeChart === "stats" && (
          <div className="space-y-4">
            <h3 className="text-md font-semibold text-gray-200">Voyage Period Analysis</h3>
            <div className="bg-navy rounded-xl border border-gray-800 p-6">
              <div className="space-y-4">
                {Object.entries(periods).map(([period, count]) => (
                  <div key={period} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">{period}</span>
                      <span className="text-gold">{count} locations</span>
                    </div>
                    <div className="h-2 bg-navy-light rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gold rounded-full"
                        style={{ width: `${(count / Math.max(...Object.values(periods))) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-navy rounded-xl border border-gray-800 p-6 mt-4">
              <h4 className="text-sm font-medium text-gray-200 mb-3 flex items-center gap-2">
                <Anchor className="h-4 w-4 text-gold" />
                Key Insights
              </h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>• The voyages reached their peak during the 1421 expedition</li>
                <li>• Southeast Asia had the highest concentration of stops ({regions["Southeast Asia"].length} locations)</li>
                <li>• The fleet traveled over 50,000 km across three oceans</li>
                <li>• East Africa was the farthest point reached (Mombasa, 1418)</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}