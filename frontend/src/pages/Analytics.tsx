import { useState, useEffect } from "react";
import { fetchLocations } from "@/lib/api";
import { BarChart3, PieChart, TrendingUp, Globe, Calendar, Ship, Anchor, Compass, Database } from "lucide-react";

interface Location {
  name: string; lat: number; lon: number; year: number; event: string;
}

export default function Analytics() {
  const [locations, setLocations]   = useState<Location[]>([]);
  const [loading, setLoading]       = useState(true);
  const [activeChart, setActiveChart] = useState<"stats" | "timeline" | "regions">("stats");

  useEffect(() => {
    fetchLocations(1433).then(data => { setLocations(data); setLoading(false); });
  }, []);

  const years = [...new Set(locations.map(l => l.year))].sort((a, b) => a - b);

  const regions = {
    "China":          locations.filter(l => l.lon > 100 && l.lon < 125 && l.lat > 20),
    "Southeast Asia": locations.filter(l => l.lon > 95  && l.lon < 120 && l.lat < 20 && l.lat > -10),
    "South Asia":     locations.filter(l => l.lon > 65  && l.lon < 95  && l.lat > 5  && l.lat < 30),
    "Middle East":    locations.filter(l => l.lon > 45  && l.lon < 65  && l.lat > 10),
    "East Africa":    locations.filter(l => l.lon > 35  && l.lon < 55  && l.lat < 5),
  };

  const voyagesByYear = locations.reduce((acc, loc) => {
    acc[loc.year] = (acc[loc.year] || 0) + 1; return acc;
  }, {} as Record<number, number>);
  const maxVoyages = Math.max(...Object.values(voyagesByYear), 1);

  const periods = {
    "First Voyage (1405–1407)":    locations.filter(l => l.year >= 1405 && l.year <= 1407).length,
    "Second Voyage (1407–1409)":   locations.filter(l => l.year >= 1407 && l.year <= 1409).length,
    "Third Voyage (1409–1411)":    locations.filter(l => l.year >= 1409 && l.year <= 1411).length,
    "Fourth Voyage (1413–1415)":   locations.filter(l => l.year >= 1413 && l.year <= 1415).length,
    "Fifth Voyage (1417–1419)":    locations.filter(l => l.year >= 1417 && l.year <= 1419).length,
    "Sixth Voyage (1421–1422)":    locations.filter(l => l.year >= 1421 && l.year <= 1422).length,
    "Seventh Voyage (1431–1433)":  locations.filter(l => l.year >= 1431 && l.year <= 1433).length,
  };
  const maxPeriod = Math.max(...Object.values(periods), 1);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-100">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold" />
      </div>
    );
  }

  const tabClass = (tab: string) =>
    `py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
      activeChart === tab
        ? "border-gold text-gold"
        : "border-transparent text-gray-500 hover:text-gray-800"
    }`;

  return (
    <div className="flex flex-col h-full bg-gray-100">

      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm flex-shrink-0">
        <h1 className="text-xl font-display font-bold text-gray-900">Data Statistics</h1>
        <p className="text-xs text-gray-500 mt-0.5">Voyage data and historical insights</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 px-6 py-4 flex-shrink-0">
        {[
          { label: "Total Voyages",     icon: Ship,    value: "7",               sub: "Between 1405–1433" },
          { label: "Locations",         icon: Globe,   value: locations.length,  sub: "Across 3 continents" },
          { label: "Years Span",        icon: Calendar, value: `${1433 - 1403}`, sub: "From 1403 to 1433" },
          { label: "Farthest Point",    icon: Compass, value: "Zanzibar",        sub: "East Africa, 1421" },
        ].map(({ label, icon: Icon, value, sub }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-500">{label}</span>
              <Icon className="h-4 w-4 text-gold" />
            </div>
            <p className="text-2xl font-display font-bold text-gray-900">{value}</p>
            <p className="text-xs text-gray-500 mt-1">{sub}</p>
          </div>
        ))}
      </div>

      {/* Tab Navigation */}
      <div className="border-y border-gray-200 px-6 bg-white flex-shrink-0">
        <div className="flex gap-6">
          <button onClick={() => setActiveChart("stats")} className={tabClass("stats")}>
            <Database className="h-4 w-4" /> Data Statistics
          </button>
          <button onClick={() => setActiveChart("timeline")} className={tabClass("timeline")}>
            <BarChart3 className="h-4 w-4" /> Voyage Timeline
          </button>
          <button onClick={() => setActiveChart("regions")} className={tabClass("regions")}>
            <PieChart className="h-4 w-4" /> Regional Distribution
          </button>
        </div>
      </div>

      {/* Chart Area */}
      <div className="flex-1 overflow-y-auto px-6 py-6">

        {activeChart === "stats" && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-900">Voyage Period Analysis</h3>
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="space-y-4">
                {Object.entries(periods).map(([period, count]) => (
                  <div key={period} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-800 font-medium">{period}</span>
                      <span className="text-gold font-semibold">{count} locations</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-gold rounded-full" style={{ width: `${(count / maxPeriod) * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Anchor className="h-4 w-4 text-gold" /> Key Insights
              </h4>
              <ul className="space-y-2 text-sm text-gray-700">
                <li>• The voyages spanned 30 years from 1403 to 1433</li>
                <li>• Southeast Asia had the highest concentration of stops</li>
                <li>• The fleet travelled over 50,000 km across three oceans</li>
                <li>• Zanzibar was the southernmost point reached (East Africa, 1421)</li>
                <li>• Zheng He died at Calicut on the return leg of the seventh voyage in 1433</li>
              </ul>
            </div>
          </div>
        )}

        {activeChart === "timeline" && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-900">Number of Locations Visited by Year</h3>
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="space-y-3">
                {years.map(year => (
                  <div key={year} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-700 font-medium">{year}</span>
                      <span className="text-gold font-semibold">{voyagesByYear[year] || 0} locations</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-gold rounded-full" style={{ width: `${((voyagesByYear[year] || 0) / maxVoyages) * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeChart === "regions" && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-900">Locations by Region</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(regions).map(([region, locs]) => (
                <div key={region} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="text-sm font-semibold text-gray-900">{region}</h4>
                    <span className="text-xs font-semibold text-gold">{locs.length} locations</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-gold rounded-full" style={{ width: `${locations.length > 0 ? (locs.length / locations.length) * 100 : 0}%` }} />
                  </div>
                  <p className="mt-2 text-xs text-gray-500">
                    {locs.slice(0, 3).map(l => l.name).join(", ")}
                    {locs.length > 3 && ` +${locs.length - 3} more`}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}