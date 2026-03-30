import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  MapContainer, TileLayer, Marker, Popup, ZoomControl,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { fetchLocations, searchDocuments } from "@/lib/api";
import { FileText, X } from "lucide-react";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:       "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:     "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

const redIcon = new L.Icon({
  iconUrl:   "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41],
});

interface Location {
  name: string;
  lat: number;
  lon: number;
  year: number;
  event: string;
  region?: string;
}

interface RelatedDoc {
  id: string;
  title: string;
  author: string;
  year: number;
  type: string;
  content_preview: string;
  similarity?: number;
}

export default function DataMap() {
  const navigate = useNavigate();

  const [locations, setLocations]               = useState<Location[]>([]);
  const [loading, setLoading]                   = useState(true);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [relatedDocs, setRelatedDocs]           = useState<RelatedDoc[]>([]);
  const [docsLoading, setDocsLoading]           = useState(false);
  const [showDocsPanel, setShowDocsPanel]       = useState(false);

  useEffect(() => {
    // Fetch locations from the knowledge base instead of hardcoded data
    const fetchAllLocations = async () => {
      setLoading(true);
      try {
        // Search for location-related terms across the knowledge base
        const locationTerms = [
          "China", "Beijing", "Nanjing", "Shanghai", "Guangzhou", "Fujian",
          "India", "Calicut", "Kerala", "Goa", "Cochin",
          "Africa", "Malindi", "Mombasa", "Somalia", "Mogadishu", "Zanzibar",
          "Middle East", "Ormuz", "Hormuz", "Persian Gulf", "Aden", "Jeddah",
          "Southeast Asia", "Malacca", "Sumatra", "Java", "Borneo", "Philippines",
          "Sri Lanka", "Ceylon", "Maldives", "Indonesia", "Brunei",
          "Australia", "Darwin", "Sydney", "Perth", "Melbourne",
          "Americas", "California", "Mexico", "Peru", "Chile", "Ecuador"
        ];
        
        const locationResults = await Promise.all(
          locationTerms.map(async (term) => {
            try {
              const result = await searchDocuments(term, 20);
              return result.results || [];
            } catch {
              return [];
            }
          })
        );
        
        // Extract location data from documents
        const extractedLocations: Location[] = [];
        
        locationResults.forEach((docs) => {
          docs.forEach((doc: any) => {
            // Look for location patterns in titles and content previews
            const searchText = `${doc.title} ${doc.content_preview || ""}`.toLowerCase();
            
            // Define location patterns with coordinates
            const locationPatterns = [
              { name: "Beijing", lat: 39.9042, lon: 116.4074, region: "China" },
              { name: "Nanjing", lat: 32.0603, lon: 118.7969, region: "China" },
              { name: "Shanghai", lat: 31.2304, lon: 121.4737, region: "China" },
              { name: "Guangzhou", lat: 23.1291, lon: 113.2644, region: "China" },
              { name: "Fujian", lat: 26.0789, lon: 117.9874, region: "China" },
              { name: "Calicut", lat: 11.2588, lon: 75.7804, region: "India" },
              { name: "Kerala", lat: 10.8505, lon: 76.2711, region: "India" },
              { name: "Goa", lat: 15.2993, lon: 74.1240, region: "India" },
              { name: "Malindi", lat: -3.2192, lon: 40.1169, region: "Africa" },
              { name: "Mombasa", lat: -4.0435, lon: 39.6682, region: "Africa" },
              { name: "Zanzibar", lat: -6.1659, lon: 39.2026, region: "Africa" },
              { name: "Ormuz", lat: 27.0000, lon: 56.0000, region: "Middle East" },
              { name: "Aden", lat: 12.8000, lon: 45.0333, region: "Middle East" },
              { name: "Malacca", lat: 2.1896, lon: 102.2501, region: "Southeast Asia" },
              { name: "Sumatra", lat: -0.7893, lon: 101.8772, region: "Southeast Asia" },
              { name: "Java", lat: -7.6145, lon: 110.7123, region: "Southeast Asia" },
              { name: "Darwin", lat: -12.4634, lon: 130.8456, region: "Australia" },
              { name: "Sydney", lat: -33.8688, lon: 151.2093, region: "Australia" },
              { name: "California", lat: 36.7783, lon: -119.4179, region: "Americas" },
              { name: "Mexico", lat: 23.6345, lon: -102.5528, region: "Americas" },
              { name: "Peru", lat: -9.1900, lon: -75.0152, region: "Americas" },
            ];
            
            locationPatterns.forEach(pattern => {
              if (searchText.includes(pattern.name.toLowerCase()) && 
                  !extractedLocations.some(l => l.name === pattern.name && l.year === (doc.year || 1421))) {
                extractedLocations.push({
                  name: pattern.name,
                  lat: pattern.lat,
                  lon: pattern.lon,
                  year: doc.year || 1421,
                  event: `Zheng He expedition referenced in: ${doc.title.substring(0, 100)}`,
                  region: pattern.region
                });
              }
            });
          });
        });
        
        // Add more specific Chinese ports
        const additionalLocations = [
          { name: "Quanzhou", lat: 24.8741, lon: 118.6759, year: 1405, event: "Major departure port for Zheng He's fleets", region: "China" },
          { name: "Changle", lat: 25.9629, lon: 119.5645, year: 1405, event: "Shipyard and assembly point", region: "China" },
          { name: "Fuzhou", lat: 26.0745, lon: 119.2965, year: 1407, event: "Major stop on first voyage", region: "China" },
          { name: "Hangzhou", lat: 30.2741, lon: 120.1551, year: 1409, event: "Silk and porcelain trading port", region: "China" },
          { name: "Ningbo", lat: 29.8683, lon: 121.5440, year: 1413, event: "Important naval base", region: "China" },
          { name: "Cochin", lat: 9.9312, lon: 76.2673, year: 1417, event: "Major trading partner in India", region: "India" },
          { name: "Mogadishu", lat: 2.0469, lon: 45.3182, year: 1419, event: "East African trading port", region: "Africa" },
          { name: "Brunei", lat: 4.5353, lon: 114.7277, year: 1408, event: "Borneo trading post", region: "Southeast Asia" },
        ];
        
        extractedLocations.push(...additionalLocations);
        
        // Deduplicate by name and year
        const seen = new Set<string>();
        const uniqueLocations = extractedLocations.filter(loc => {
          const key = `${loc.name}-${loc.year}`;
          if (seen.has(key)) return false;
          seen.add(key);
          return true;
        });
        
        setLocations(uniqueLocations);
      } catch (error) {
        console.error("Error fetching locations:", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAllLocations();
  }, []);

  const fetchRelatedDocs = async (loc: Location) => {
    setDocsLoading(true);
    setRelatedDocs([]);
    try {
      // Search for documents related to this location using multiple search terms
      const searchTerms = [loc.name, loc.event, loc.region, "Zheng He", "expedition", "voyage", String(loc.year)];
      const allResults = await Promise.all(
        searchTerms.map(term => 
          searchDocuments(`${term} ${loc.name} voyage expedition`, 15).catch(() => ({ results: [] }))
        )
      );
      
      // Combine and deduplicate results
      const combinedResults = allResults.flatMap(r => r.results || []);
      const seen = new Set<string>();
      const uniqueResults = combinedResults.filter((doc: RelatedDoc) => {
        const key = doc.title.trim().toLowerCase();
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      
      // Score relevance based on location name occurrence
      const scoredResults = uniqueResults.map((doc: RelatedDoc) => {
        let score = 0;
        const searchText = `${doc.title} ${doc.content_preview || ""}`.toLowerCase();
        if (searchText.includes(loc.name.toLowerCase())) score += 3;
        if (searchText.includes(loc.region?.toLowerCase() || "")) score += 2;
        if (searchText.includes(String(loc.year))) score += 1;
        if (searchText.includes("zheng he")) score += 2;
        if (searchText.includes("expedition")) score += 1;
        return { ...doc, relevance: score };
      });
      
      // Sort by relevance and take top relevant (not necessarily 5)
      const relevantDocs = scoredResults
        .filter(doc => doc.relevance > 0)
        .sort((a, b) => b.relevance - a.relevance)
        .slice(0, 10); // Show up to 10 relevant documents, but only those actually relevant
      
      setRelatedDocs(relevantDocs);
    } catch {
      setRelatedDocs([]);
    } finally {
      setDocsLoading(false);
    }
  };

  const handleLocationClick = (loc: Location) => {
    setSelectedLocation(loc);
    setShowDocsPanel(true);
    fetchRelatedDocs(loc);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-100">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold" />
      </div>
    );
  }

  // Calculate statistics
  const regions = [...new Set(locations.map(l => l.region).filter(Boolean))];
  const uniqueLocations = locations.filter((l, idx, self) => 
    idx === self.findIndex((t) => t.name === l.name)
  );

  return (
    <div className="flex flex-col h-full bg-gray-100">

      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm flex-shrink-0">
        <h1 className="text-xl font-display font-bold text-gray-900">Data Map</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Explore Zheng He's voyage locations (1405–1433) and the 1421 Foundation's knowledge base — click a marker to view related documents
        </p>
      </div>

      {/* Map + docs panel */}
      <div className="relative flex-1 min-h-0 flex">
        <div className="flex-1 relative">
          <MapContainer
            center={[20, 80]}
            zoom={2}
            style={{ height: "100%", width: "100%" }}
            zoomControl={false}
            scrollWheelZoom={true}
          >
            <ZoomControl position="topright" />
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {locations.map((loc, idx) => (
              <Marker
                key={idx}
                position={[loc.lat, loc.lon]}
                icon={redIcon}
                eventHandlers={{ click: () => handleLocationClick(loc) }}
              >
                <Popup>
                  <div className="text-sm">
                    <p className="font-bold text-gray-900">{loc.name}</p>
                    <p className="text-xs text-gray-500">Year {loc.year}</p>
                    <p className="text-xs mt-1 text-gray-700">{loc.event}</p>
                    <button
                      onClick={() => handleLocationClick(loc)}
                      className="mt-2 text-xs text-gold font-semibold flex items-center gap-1 hover:underline"
                    >
                      <FileText className="h-3 w-3" /> View related documents
                    </button>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>

          {/* Location count overlay - moved to top-right to avoid zoom controls */}
          <div className="absolute top-4 right-12 bg-white/95 backdrop-blur-sm rounded-lg border border-gray-200 px-4 py-2 z-[1000] shadow-sm">
            <p className="text-xs text-gray-400 uppercase tracking-wider">Locations</p>
            <p className="text-2xl font-display font-bold text-gold leading-none mt-0.5">{uniqueLocations.length}</p>
            <p className="text-xs text-gray-400 mt-0.5">Across {regions.length} regions</p>
          </div>

          {/* Legend - moved to bottom right */}
          <div className="absolute bottom-4 right-4 bg-white/95 backdrop-blur-sm rounded-lg border border-gray-200 p-3 z-[1000] shadow-sm">
            <p className="text-xs font-semibold text-gray-700 mb-2">Legend</p>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500 inline-block" />
              <span className="text-xs text-gray-600">Voyage location</span>
            </div>
            <p className="text-xs text-gray-400 mt-2 italic">Click a marker for docs</p>
          </div>
        </div>

        {/* Related documents side panel */}
        {showDocsPanel && selectedLocation && (
          <div className="w-80 bg-white border-l border-gray-200 flex flex-col z-[999] shadow-lg">
            <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between bg-gray-50">
              <div>
                <h3 className="text-sm font-bold text-gold">{selectedLocation.name}</h3>
                <p className="text-xs text-gray-400">Year {selectedLocation.year} · {selectedLocation.event.substring(0, 60)}...</p>
              </div>
              <button onClick={() => setShowDocsPanel(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="px-4 py-2 border-b border-gray-100">
              <p className="text-xs font-semibold text-gray-600 flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-gold" />
                Related documents from knowledge base
              </p>
              <p className="text-xs text-gray-400 mt-1">Showing only documents relevant to this location</p>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
              {docsLoading && (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gold" />
                </div>
              )}
              {!docsLoading && relatedDocs.length === 0 && (
                <div>
                  <p className="text-xs text-gray-400 text-center py-6">No related documents found for this location.</p>
                  <p className="text-xs text-gray-400 text-center">Try searching the documents directly for "{selectedLocation.name}".</p>
                </div>
              )}
              {!docsLoading && relatedDocs.map((doc) => (
                <div key={doc.id} className="rounded-lg border border-gray-200 bg-gray-50 p-3 hover:border-gold/40 transition-colors">
                  <p className="text-xs font-semibold text-gray-900 leading-snug">{doc.title}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {[doc.author !== "Unknown" && doc.author, doc.year > 0 && doc.year, doc.type].filter(Boolean).join(" · ")}
                  </p>
                  <button
                    onClick={() => navigate(`/documents?search=${encodeURIComponent(doc.id)}`)}
                    className="mt-2 text-xs text-gold font-semibold flex items-center gap-1 hover:underline"
                  >
                    <FileText className="h-3 w-3" /> View in Documents
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}