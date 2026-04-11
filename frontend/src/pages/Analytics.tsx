import { useState, useEffect } from "react";
import { fetchLocations, fetchStats } from "@/lib/api";
import {
  BarChart3,
  PieChart,
  TrendingUp,
  Globe,
  Calendar,
  Ship,
  Anchor,
  Compass,
  Database,
  FileText,
  Map,
} from "lucide-react";

interface Location {
  name: string;
  lat: number;
  lon: number;
  year: number;
  event: string;
}

// This is to match what the Data Map actually shows
const GLOBAL_REGIONS = [
  { label: "China", count: 3, detail: "Nanjing, Quanzhou, Beijing" },
  { label: "Southeast Asia", count: 10, detail: "Champa, Java, Sumatra, Malacca, Siam, Brunei, Philippines…" },
  { label: "South Asia", count: 4, detail: "Sri Lanka, Calicut, Cochin, Maldives" },
  { label: "Middle East", count: 4, detail: "Hormuz, Aden, Jidda, Muscat" },
  { label: "East Africa", count: 6, detail: "Mogadishu, Malindi, Mombasa, Zanzibar, Sofala, Madagascar" },
  { label: "Europe", count: 5, detail: "Venice, Portugal, Greenland, Dieppe, Piri Reis Map" },
  { label: "Australia", count: 6, detail: "Darwin, Broome, Perth, Sydney, Adelaide, Java la Grande" },
  { label: "New Zealand", count: 2, detail: "Northland NZ, South Island NZ" },
  { label: "South America", count: 8, detail: "Ecuador, Peru, Brazil, Chile, Patagonia, Paraguay, Argentina, Falklands" },
  { label: "North America", count: 5, detail: "California, Mexico, Caribbean, Rhode Island, British Columbia" },
  { label: "Antarctica", count: 2, detail: "West Antarctica, East Antarctica" },
];

const TOTAL_DATA_MAP_POINTS = GLOBAL_REGIONS.reduce((total, region) => total + region.count, 0);
const MAX_REGION_COUNT = Math.max(...GLOBAL_REGIONS.map((region) => region.count));

// helper function
export default function Analytics() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [docCount, setDocCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [activeChart, setActiveChart] = useState<"stats" | "timeline" | "regions" | "global">("stats");

  useEffect(() => {
    Promise.all([
      fetchLocations(1433),
      fetchStats(),
    ]).then(([locs, stats]) => {
      setLocations(locs);
      setDocCount(stats.documents_count);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-100">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold" />
      </div>
    );
  }

  const years = [...new Set(locations.map((loc) => loc.year))].sort((a, b) => a - b);

  // Confirmed voyage regions (from VOYAGE_LOCATIONS in main.py file)
  const voyageRegions = {
    "China": locations.filter((loc) => loc.lon > 100 && loc.lon < 125 && loc.lat > 20),
    "Southeast Asia": locations.filter((loc) => loc.lon > 95 && loc.lon < 120 && loc.lat < 20 && loc.lat > -10),
    "South Asia": locations.filter((loc) => loc.lon > 65 && loc.lon < 95 && loc.lat > 5 && loc.lat < 30),
    "Middle East": locations.filter((loc) => loc.lon > 45 && loc.lon < 65 && loc.lat > 10),
    "East Africa": locations.filter((loc) => loc.lon > 35 && loc.lon < 55 && loc.lat < 5),
  };
  const voyagesByYear = locations.reduce((acc, loc) => {
    acc[loc.year] = (acc[loc.year] || 0) + 1;
    return acc;
  }, {} as Record<number, number>);
  
  const maxVoyages = Math.max(...Object.values(voyagesByYear), 1);

  const periods = {
    "First Voyage (1405–1407)": locations.filter((loc) => loc.year >= 1405 && loc.year <= 1407).length,
    "Second Voyage (1407–1409)": locations.filter((loc) => loc.year >= 1407 && loc.year <= 1409).length,
    "Third Voyage (1409–1411)": locations.filter((loc) => loc.year >= 1409 && loc.year <= 1411).length,
    "Fourth Voyage (1413–1415)": locations.filter((loc) => loc.year >= 1413 && loc.year <= 1415).length,
    "Fifth Voyage (1417–1419)": locations.filter((loc) => loc.year >= 1417 && loc.year <= 1419).length,
    "Sixth Voyage (1421–1422)": locations.filter((loc) => loc.year >= 1421 && loc.year <= 1422).length,
    "Seventh Voyage (1431–1433)": locations.filter((loc) => loc.year >= 1431 && loc.year <= 1433).length,
  };
  
  const maxPeriod = Math.max(...Object.values(periods), 1);

  const tabClass = (tabName: string) => {
    return `py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 whitespace-nowrap ${
      activeChart === tabName
        ? "border-gold text-gold"
        : "border-transparent text-gray-500 hover:text-gray-800"
    }`;
  };

  return (
    <div className="flex flex-col h-full bg-gray-100">

      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm flex-shrink-0">
        <h1 className="text-xl font-display font-bold text-gray-900">Data Statistics</h1>
        <p className="text-xs text-gray-500 mt-0.5">Knowledge base statistics and historical insights</p>
      </div>
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 px-6 py-4 flex-shrink-0">
        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-500">Total Voyages</span>
            <Ship className="h-4 w-4 text-gold" />
          </div>
          <p className="text-2xl font-display font-bold text-gray-900">7</p>
          <p className="text-xs text-gray-500 mt-1">Between 1405–1433</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-500">Voyage Locations</span>
            <Globe className="h-4 w-4 text-gold" />
          </div>
          <p className="text-2xl font-display font-bold text-gray-900">{locations.length}</p>
          <p className="text-xs text-gray-500 mt-1">Confirmed stops</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-500">Data Map Points</span>
            <Map className="h-4 w-4 text-gold" />
          </div>
          <p className="text-2xl font-display font-bold text-gray-900">{TOTAL_DATA_MAP_POINTS}</p>
          <p className="text-xs text-gray-500 mt-1">Across 11 regions</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-500">Documents</span>
            <FileText className="h-4 w-4 text-gold" />
          </div>
          <p className="text-2xl font-display font-bold text-gray-900">{docCount || "—"}</p>
          <p className="text-xs text-gray-500 mt-1">In knowledge base</p>
        </div>
      </div>


      {/* Tab Navigation */}
      <div className="border-y border-gray-200 px-6 bg-white flex-shrink-0 overflow-x-auto">
        <div className="flex gap-6 min-w-max">
          <button onClick={() => setActiveChart("stats")} className={tabClass("stats")}>
            <Database className="h-4 w-4" /> Data Statistics
          </button>
          <button onClick={() => setActiveChart("global")} className={tabClass("global")}>
            <Map className="h-4 w-4" /> Data Map Locations
          </button>
          <button onClick={() => setActiveChart("timeline")} className={tabClass("timeline")}>
            <BarChart3 className="h-4 w-4" /> Voyage Timeline
          </button>
          <button onClick={() => setActiveChart("regions")} className={tabClass("regions")}>
            <PieChart className="h-4 w-4" /> Confirmed Voyages by Region
          </button>
        </div>
      </div>

      {/* Chart Area */}
      <div className="flex-1 overflow-y-auto px-6 py-6">

        {/* Data Statistics Tab */}
        {activeChart === "stats" && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-900">Voyage Period Analysis</h3>
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="space-y-4">
                {Object.entries(periods).map(([period, count]) => (
                  <div key={period} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-800 font-medium">{period}</span>
                      <span className="text-gold font-semibold">{count} location{count !== 1 ? "s" : ""}</span>
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
                <li>• Southeast Asia had the highest concentration of confirmed stops</li>
                <li>• The fleet travelled over 50,000 km across three oceans</li>
                <li>• Zanzibar was the southernmost confirmed point (East Africa, 1421)</li>
                <li>• Zheng He died at Calicut on the return leg of the seventh voyage in 1433</li>
                <li>• The 1421 Foundation's knowledge base covers {TOTAL_DATA_MAP_POINTS} global locations across 11 world regions</li>
              </ul>
            </div>
          </div>
        )}

        {/* Global Data Map Tab */}
        {activeChart === "global" && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-900">
              Data Map Locations by World Region — {TOTAL_DATA_MAP_POINTS} total points
            </h3>
            <p className="text-xs text-gray-500">
              Includes both confirmed voyage stops and evidence/research locations as shown on the Data Map.
            </p>

            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="space-y-4">
                {GLOBAL_REGIONS.map((region) => (
                  <div key={region.label} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <div>
                        <span className="text-gray-800 font-medium">{region.label}</span>
                        <span className="text-xs text-gray-400 ml-2">{region.detail}</span>
                      </div>
                      <span className="text-gold font-semibold flex-shrink-0 ml-4">
                        {region.count} point{region.count !== 1 ? "s" : ""}
                      </span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-gold rounded-full" style={{ width: `${(region.count / MAX_REGION_COUNT) * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-3 h-3 rounded-full inline-block bg-red-500" />
                  <span className="text-xs text-gray-500">Confirmed voyage stops</span>
                </div>
                <p className="text-2xl font-display font-bold text-gray-900">17</p>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-3 h-3 rounded-full inline-block bg-blue-500" />
                  <span className="text-xs text-gray-500">Evidence locations</span>
                </div>
                <p className="text-2xl font-display font-bold text-gray-900">{TOTAL_DATA_MAP_POINTS - 17}</p>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-3 h-3 rounded-full inline-block bg-gold" />
                  <span className="text-xs text-gray-500">Regions covered</span>
                </div>
                <p className="text-2xl font-display font-bold text-gray-900">11</p>
              </div>
            </div>
          </div>
        )}

        {/* Voyage Timeline Tab */}
        {activeChart === "timeline" && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-900">Confirmed Voyage Locations by Year</h3>
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="space-y-3">
                {years.map((year) => (

                  <div key={year} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-700 font-medium">{year}</span>
                      <span className="text-gold font-semibold">
                        {voyagesByYear[year] || 0} location{(voyagesByYear[year] || 0) !== 1 ? "s" : ""}
                      </span>
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

        {/* Confirmed Voyages by Region Tab */}
        {activeChart === "regions" && (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-900">Confirmed Voyage Locations by Region</h3>
            <p className="text-xs text-gray-500">Based on historically verified voyage stops only.</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(voyageRegions).map(([region, locs]) => (
                <div key={region} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="text-sm font-semibold text-gray-900">{region}</h4>
                    <span className="text-xs font-semibold text-gold">
                      {locs.length} location{locs.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-gold rounded-full" style={{ width: `${locations.length > 0 ? (locs.length / locations.length) * 100 : 0}%` }} />
                  </div>
                  <p className="mt-2 text-xs text-gray-500">
                    {locs.slice(0, 3).map((l) => l.name).join(", ")}
                    
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