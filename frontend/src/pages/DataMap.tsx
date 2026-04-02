import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
<<<<<<< HEAD
import { searchDocuments } from "@/lib/api";
import { FileText, X } from "lucide-react";
=======
import { fetchLocations, searchDocuments } from "@/lib/api";
import { FileText, X, CheckCircle, XCircle } from "lucide-react";
>>>>>>> bc36e49d9bd7f52521c24db351f7b16c36714141

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

const blueIcon = new L.Icon({
  iconUrl:   "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41],
});

interface DataPoint {
  id: string;
  name: string;
  lat: number;
  lon: number;
  year?: number;
  event: string;
  searchTerm: string;   // what to search in knowledge base
  category: "voyage" | "evidence"; // red = confirmed voyage, blue = evidence/research
}

// All data points — both confirmed voyage stops (red) and evidence locations (blue)
const ALL_DATA_POINTS: DataPoint[] = [
  // ── CHINA ───────────────────────────────────────────────────────────
  { id: "nanjing",   name: "Nanjing",   lat: 32.06,  lon: 118.80, year: 1403, category: "voyage",
    event: "Yongle Emperor commissions the treasure fleet; first voyage departs 1405 with 317 ships and 28,000 men.",
    searchTerm: "Nanjing treasure fleet" },
  { id: "quanzhou",  name: "Quanzhou",  lat: 24.87,  lon: 118.68, year: 1405, category: "voyage",
    event: "Major departure port for early voyages; home of the world's largest medieval shipyard.",
    searchTerm: "Quanzhou shipyard" },
  { id: "beijing",   name: "Beijing",   lat: 39.90,  lon: 116.41, year: 1421, category: "voyage",
    event: "Imperial capital under the Yongle Emperor; seat of power during all seven voyages.",
    searchTerm: "Beijing Yongle Emperor" },

<<<<<<< HEAD
  // ── SOUTHEAST ASIA ──────────────────────────────────────────────────
  { id: "champa",    name: "Champa",    lat: 10.82,  lon: 106.63, year: 1405, category: "voyage",
    event: "First stop on Voyage 1 — Southeast Asian ally (modern Vietnam).",
    searchTerm: "Champa Vietnam Zheng He" },
  { id: "java",      name: "Java",      lat: -7.61,  lon: 110.71, year: 1406, category: "voyage",
    event: "Diplomatic missions conducted on Java during Voyage 1.",
    searchTerm: "Java Zheng He" },
  { id: "sumatra",   name: "Sumatra",   lat: -0.59,  lon: 101.34, year: 1406, category: "voyage",
    event: "Strategic trading post established at Palembang, Sumatra.",
    searchTerm: "Sumatra Palembang" },
  { id: "malacca",   name: "Malacca",   lat:  2.19,  lon: 102.25, year: 1406, category: "voyage",
    event: "Key port established; local piracy suppressed by Zheng He's fleet.",
    searchTerm: "Malacca Zheng He" },
  { id: "siam",      name: "Siam",      lat: 13.74,  lon: 100.52, year: 1408, category: "voyage",
    event: "Voyage 2 — diplomatic relations established with modern Thailand.",
    searchTerm: "Siam Thailand Zheng He" },
  { id: "brunei",    name: "Brunei",    lat:  4.94,  lon: 114.95, year: 1408, category: "evidence",
    event: "Chinese porcelain and artefacts found indicating trade during the Ming dynasty.",
    searchTerm: "Brunei Chinese porcelain" },
  { id: "philippines", name: "Philippines", lat: 12.88, lon: 121.77, year: 1417, category: "evidence",
    event: "Chinese ceramics and evidence of pre-colonial contact with Ming dynasty fleets.",
    searchTerm: "Philippines Chinese ceramics" },

  // ── SOUTH ASIA ───────────────────────────────────────────────────────
  { id: "sri-lanka", name: "Sri Lanka", lat:  7.87,  lon:  80.77, year: 1409, category: "voyage",
    event: "Voyage 2 — trilingual inscription erected at Galle in Chinese, Tamil and Persian.",
    searchTerm: "Sri Lanka Galle trilingual inscription" },
  { id: "calicut",   name: "Calicut",   lat: 11.26,  lon:  75.78, year: 1407, category: "voyage",
    event: "Primary destination on Malabar Coast, India. Zheng He dies here 1433.",
    searchTerm: "Calicut Kozhikode Zheng He" },
  { id: "cochin",    name: "Cochin",    lat:  9.93,  lon:  76.27, year: 1417, category: "evidence",
    event: "Indian trading port with strong evidence of Ming dynasty ceramic trade.",
    searchTerm: "Cochin India Chinese trade" },
  { id: "maldives",  name: "Maldives",  lat:  3.20,  lon:  73.22, year: 1413, category: "evidence",
    event: "Ibn Battuta records Chinese vessels visiting the Maldive Islands; artefacts found.",
    searchTerm: "Maldives Chinese" },

  // ── MIDDLE EAST ──────────────────────────────────────────────────────
  { id: "hormuz",    name: "Hormuz",    lat: 27.16,  lon:  56.28, year: 1414, category: "voyage",
    event: "Voyage 4 — Persian Gulf reached for first time; 18 states sent tribute to China.",
    searchTerm: "Hormuz Persian Gulf Zheng He" },
  { id: "aden",      name: "Aden",      lat: 12.79,  lon:  45.02, year: 1417, category: "voyage",
    event: "Voyage 5 — Arabian Peninsula; gifts of zebras and lions received.",
    searchTerm: "Aden Yemen Zheng He" },
  { id: "jidda",     name: "Jidda",     lat: 21.49,  lon:  39.19, year: 1432, category: "voyage",
    event: "Voyage 7 — Red Sea reached; auxiliary fleet sent towards Mecca.",
    searchTerm: "Jidda Mecca Red Sea" },
  { id: "muscat",    name: "Muscat",    lat: 23.58,  lon:  58.40, year: 1414, category: "evidence",
    event: "Omani coast visited during Persian Gulf expeditions; Chinese coins found.",
    searchTerm: "Muscat Oman Chinese" },

  // ── EAST AFRICA ──────────────────────────────────────────────────────
  { id: "mogadishu", name: "Mogadishu", lat:  2.05,  lon:  45.32, year: 1418, category: "voyage",
    event: "Voyage 5 — Somali coast; first Chinese fleet to reach East Africa.",
    searchTerm: "Mogadishu Somalia Zheng He" },
  { id: "malindi",   name: "Malindi",   lat: -3.22,  lon:  40.12, year: 1418, category: "voyage",
    event: "Voyage 5 — Kenya coast; famous giraffe gifted to the Yongle Emperor.",
    searchTerm: "Malindi Kenya giraffe Zheng He" },
  { id: "mombasa",   name: "Mombasa",   lat: -4.04,  lon:  39.67, year: 1419, category: "voyage",
    event: "Voyage 5 — East African trade firmly established.",
    searchTerm: "Mombasa Kenya Zheng He" },
  { id: "zanzibar",  name: "Zanzibar",  lat: -6.17,  lon:  39.20, year: 1421, category: "voyage",
    event: "Voyage 6 — southernmost confirmed point of the treasure fleet.",
    searchTerm: "Zanzibar Zheng He" },
  { id: "sofala",    name: "Sofala",    lat: -20.17, lon:  34.70, year: 1421, category: "evidence",
    event: "Menzies argues Chinese maps show knowledge of southern Mozambique coast.",
    searchTerm: "Sofala Mozambique Chinese map" },

  // ── EUROPE ───────────────────────────────────────────────────────────
  { id: "venice",    name: "Venice",    lat: 45.44,  lon:  12.33, year: 1428, category: "evidence",
    event: "Fra Mauro's 1450 map shows detailed knowledge of Africa and Asia — possibly derived from Chinese sources brought via traders.",
    searchTerm: "Venice Fra Mauro map Chinese" },
  { id: "portugal",  name: "Portugal",  lat: 38.72,  lon:  -9.14, year: 1421, category: "evidence",
    event: "Menzies argues Portuguese cartographers had access to Chinese maps that aided Vasco da Gama's route.",
    searchTerm: "Portugal Chinese maps Vasco da Gama" },
  { id: "greenland", name: "Greenland", lat: 72.00,  lon: -42.00, year: 1421, category: "evidence",
    event: "Menzies contends Chinese fleets rounded the Arctic and mapped Greenland before European contact.",
    searchTerm: "Greenland Chinese Arctic" },

  // ── AUSTRALIA ────────────────────────────────────────────────────────
  { id: "darwin",    name: "Darwin",    lat: -12.46, lon: 130.84, year: 1421, category: "evidence",
    event: "Chinese artefacts and stone anchors found near Darwin; possible evidence of early contact with northern Australia.",
    searchTerm: "Darwin Australia Chinese artefacts" },
  { id: "broome",    name: "Broome",    lat: -17.96, lon: 122.23, year: 1421, category: "evidence",
    event: "Beeswax figures and Chinese coins discovered; Menzies argues this is evidence of Chinese landings on Australia's northwest coast.",
    searchTerm: "Broome Australia Chinese beeswax" },
  { id: "perth",     name: "Perth",     lat: -31.95, lon: 115.86, year: 1421, category: "evidence",
    event: "Research suggests Chinese fleets may have charted the southwest Australian coast during the 1421 voyages.",
    searchTerm: "Perth Australia Chinese" },
  { id: "sydney",    name: "Sydney",    lat: -33.87, lon: 151.21, year: 1421, category: "evidence",
    event: "Claims of Chinese presence in eastern Australia appear in 1421 Foundation research.",
    searchTerm: "Sydney Australia Chinese 1421" },
  { id: "adelaide",  name: "Adelaide",  lat: -34.93, lon: 138.60, year: 1421, category: "evidence",
    event: "Southern Australian coast discussed in context of Chinese mapping of the continent.",
    searchTerm: "Australia southern coast Chinese" },

  // ── NEW ZEALAND ──────────────────────────────────────────────────────
  { id: "northland-nz", name: "Northland, NZ", lat: -35.73, lon: 174.32, year: 1421, category: "evidence",
    event: "Waitaha oral traditions and stone structures suggest pre-Māori contact possibly linked to Chinese voyages.",
    searchTerm: "New Zealand Waitaha Chinese" },
  { id: "south-island-nz", name: "South Island, NZ", lat: -44.00, lon: 170.50, year: 1421, category: "evidence",
    event: "Menzies cites genetic and archaeological evidence of Chinese contact with New Zealand before European arrival.",
    searchTerm: "New Zealand Maori Chinese genetics" },

  // ── SOUTH AMERICA ────────────────────────────────────────────────────
  { id: "ecuador",   name: "Ecuador",   lat: -1.83,  lon: -78.18, year: 1421, category: "evidence",
    event: "Chinese chickens (pre-Columbian) and sweet potato evidence points to Pacific contact; Menzies links this to Chinese fleets.",
    searchTerm: "Ecuador Chinese chickens pre-Columbian" },
  { id: "peru",      name: "Peru",      lat: -9.19,  lon: -75.02, year: 1421, category: "evidence",
    event: "Menzies argues Chinese navigators reached Peru and influenced Andean cultures; genetic and botanical evidence cited.",
    searchTerm: "Peru Chinese Inca 1421" },
  { id: "brazil",    name: "Brazil",    lat: -14.24, lon: -51.93, year: 1421, category: "evidence",
    event: "1421 Foundation research cites possible Chinese presence on the Brazilian coast before Cabral's 1500 arrival.",
    searchTerm: "Brazil Chinese pre-Columbian" },
  { id: "chile",     name: "Chile",     lat: -35.68, lon: -71.54, year: 1421, category: "evidence",
    event: "Araucanian people of Chile show possible Asian genetic markers; discussed in 1421 hypothesis.",
    searchTerm: "Chile Araucanian Chinese genetics" },

  // ── NORTH AMERICA ────────────────────────────────────────────────────
  { id: "california", name: "California", lat: 36.78, lon: -119.42, year: 1421, category: "evidence",
    event: "Chinese brass plates and artefacts found along the California coast; Menzies argues Chinese fleets mapped North America.",
    searchTerm: "California Chinese brass plates 1421" },
  { id: "mexico",    name: "Mexico",    lat: 23.63,  lon: -102.55, year: 1421, category: "evidence",
    event: "Evidence of pre-Columbian contact including Chinese-style stone anchors off the Mexican coast.",
    searchTerm: "Mexico Chinese pre-Columbian" },
  { id: "caribbean", name: "Caribbean", lat: 18.70,  lon: -70.16, year: 1421, category: "evidence",
    event: "Menzies cites Chinese maps showing detailed Caribbean island outlines before Columbus.",
    searchTerm: "Caribbean Chinese maps pre-Columbian" },
];

const EXCLUDE_PATTERNS = ["gallery", "minoan", "atlantis", "fresco", "artist impression", "image gallery"];
=======
// Keywords that indicate a document is actually relevant to a location
const getRelevanceKeywords = (locationName: string): string[] => {
  const keywords: Record<string, string[]> = {
    "Hormuz": ["Hormuz", "Ormus", "Persian Gulf", "4th voyage", "fourth voyage", "1414"],
    "Malindi": ["Malindi", "Kenya", "East Africa", "giraffe", "5th voyage", "fifth voyage"],
    "Mogadishu": ["Mogadishu", "Somalia", "Somali", "East Africa", "porcelain"],
    "Aden": ["Aden", "Yemen", "Arabia", "Arabian Peninsula", "5th voyage"],
    "Calicut": ["Calicut", "Kozhikode", "Malabar Coast", "India", "1st voyage"],
    "Malacca": ["Malacca", "Melaka", "Strait of Malacca", "Malaysia"],
    "Sri Lanka": ["Sri Lanka", "Galle", "Ceylon", "trilingual inscription"],
    "Nanjing": ["Nanjing", "shipyard", "treasure fleet", "Longjiang"],
  };
  return keywords[locationName] || [locationName];
};

// Check if a document is relevant to the location
const isDocumentRelevant = (doc: RelatedDoc, locationName: string): boolean => {
  const title = doc.title?.toLowerCase() || "";
  const sourceFile = doc.source_file?.toLowerCase() || "";
  const type = doc.type?.toLowerCase() || "";
  const author = doc.author?.toLowerCase() || "";
  
  const relevantKeywords = getRelevanceKeywords(locationName);
  
  // Check title
  for (const keyword of relevantKeywords) {
    if (title.includes(keyword.toLowerCase())) {
      return true;
    }
  }
  
  // Check source file (e.g., "1421_book", "evidence_annex")
  for (const keyword of ["1421", "evidence", "annex", "zheng he", "voyage"]) {
    if (sourceFile.includes(keyword) || title.includes(keyword)) {
      // If it's from a book or evidence source, it's more likely relevant
      return true;
    }
  }
  
  // Facebook posts about events/general content are NOT relevant for specific locations
  if (type === "facebook_posts" && !title.includes(locationName.toLowerCase())) {
    return false;
  }
  
  // Generic news articles without location mention are NOT relevant
  if (type === "general" && !title.toLowerCase().includes(locationName.toLowerCase())) {
    return false;
  }
  
  return false;
};

// Calculate relevance score for sorting
const calculateRelevanceScore = (doc: RelatedDoc, locationName: string): number => {
  let score = 0;
  const title = doc.title?.toLowerCase() || "";
  const sourceFile = doc.source_file?.toLowerCase() || "";
  const relevantKeywords = getRelevanceKeywords(locationName);
  
  // Exact location name in title: +10
  if (title.includes(locationName.toLowerCase())) {
    score += 10;
  }
  
  // Keyword matches: +5 each
  for (const keyword of relevantKeywords) {
    if (title.includes(keyword.toLowerCase())) {
      score += 5;
    }
  }
  
  // From book/evidence files: +8
  if (sourceFile.includes("1421") || sourceFile.includes("evidence") || sourceFile.includes("book")) {
    score += 8;
  }
  
  // From foundation/gavin menzies website: +4
  if (sourceFile.includes("foundation") || sourceFile.includes("gavin") || sourceFile.includes("menzies")) {
    score += 4;
  }
  
  // Similarity score from backend: + (similarity * 10)
  if (doc.similarity_score) {
    score += doc.similarity_score * 10;
  }
  
  return score;
};

// Define search variations for each location
const getSearchVariations = (loc: Location): string[] => {
  const variations: string[] = [loc.name];
  
  if (loc.name === "Hormuz") {
    variations.push("Hormuz Persian Gulf", "Zheng He Hormuz", "Ormus", "fourth voyage Hormuz", "1414 Hormuz");
  } else if (loc.name === "Malindi") {
    variations.push("Malindi Kenya", "giraffe Malindi", "Zheng He Malindi", "fifth voyage Malindi");
  } else if (loc.name === "Mogadishu") {
    variations.push("Mogadishu Somalia", "Somali coast", "Zheng He Mogadishu");
  } else if (loc.name === "Aden") {
    variations.push("Aden Yemen", "Arabian Peninsula", "Zheng He Aden");
  } else if (loc.name === "Calicut") {
    variations.push("Calicut India", "Kozhikode", "Malabar Coast", "Zheng He Calicut");
  } else if (loc.name === "Malacca") {
    variations.push("Malacca Malaysia", "Melaka", "Strait of Malacca");
  } else if (loc.name === "Sri Lanka") {
    variations.push("Galle Sri Lanka", "Ceylon", "trilingual inscription");
  } else if (loc.name === "Nanjing") {
    variations.push("Nanjing shipyard", "treasure fleet Nanjing", "Longjiang shipyard");
  }
  
  return variations;
};
>>>>>>> bc36e49d9bd7f52521c24db351f7b16c36714141

export default function DataMap() {
  const navigate = useNavigate();

<<<<<<< HEAD
  const [selectedPoint, setSelectedPoint]   = useState<DataPoint | null>(null);
  const [relatedDocs, setRelatedDocs]       = useState<any[]>([]);
  const [docsLoading, setDocsLoading]       = useState(false);
  const [showDocsPanel, setShowDocsPanel]   = useState(false);
  const [filterCategory, setFilterCategory] = useState<"all" | "voyage" | "evidence">("all");
=======
  const [locations, setLocations]               = useState<Location[]>([]);
  const [loading, setLoading]                   = useState(true);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [relatedDocs, setRelatedDocs]           = useState<RelatedDoc[]>([]);
  const [docsLoading, setDocsLoading]           = useState(false);
  const [showDocsPanel, setShowDocsPanel]       = useState(false);
  const [searchDebug, setSearchDebug]           = useState<string[]>([]);
>>>>>>> bc36e49d9bd7f52521c24db351f7b16c36714141

  const fetchRelatedDocs = async (point: DataPoint) => {
    setDocsLoading(true);
    setRelatedDocs([]);
<<<<<<< HEAD
=======
    setSearchDebug([]);
    
    const variations = getSearchVariations(loc);
    console.log(`🔍 Searching for "${loc.name}" with variations:`, variations);
    
>>>>>>> bc36e49d9bd7f52521c24db351f7b16c36714141
    try {
      const seenIds = new Set<string>();
<<<<<<< HEAD
      let allResults: any[] = [];

      // Search using the point's dedicated search term + location name
      for (const term of [point.searchTerm, point.name, `${point.name} Zheng He`, `${point.name} Chinese`]) {
        try {
          const res = await searchDocuments(term, 15);
          for (const doc of (res.results || [])) {
=======
      const debugMessages: string[] = [];
      
      // Try each search variation
      for (const term of variations) {
        debugMessages.push(`Searching: "${term}"`);
        try {
          const res = await searchDocuments(term, 30);
          const results: RelatedDoc[] = res.results || [];
          debugMessages.push(`  → Found ${results.length} raw results`);
          
          for (const doc of results) {
>>>>>>> bc36e49d9bd7f52521c24db351f7b16c36714141
            if (!seenIds.has(doc.id)) {
              seenIds.add(doc.id);
              allResults.push(doc);
            }
          }
<<<<<<< HEAD
        } catch {}
      }

      // Filter out gallery/image pages
      const filtered = allResults.filter((doc) => {
        const t = doc.title.toLowerCase();
        return !EXCLUDE_PATTERNS.some((p) => t.includes(p));
      });

      // Deduplicate by title
      const seenTitles = new Set<string>();
      const unique = filtered.filter((doc) => {
=======
        } catch (err) {
          debugMessages.push(`  → Error: ${err}`);
        }
      }
      
      // Also search with "Zheng He"
      const zhengHeTerm = `Zheng He ${loc.name}`;
      debugMessages.push(`Searching: "${zhengHeTerm}"`);
      try {
        const res = await searchDocuments(zhengHeTerm, 20);
        const results: RelatedDoc[] = res.results || [];
        debugMessages.push(`  → Found ${results.length} raw results`);
        for (const doc of results) {
          if (!seenIds.has(doc.id)) {
            seenIds.add(doc.id);
            allResults.push(doc);
          }
        }
      } catch (err) {
        debugMessages.push(`  → Error: ${err}`);
      }
      
      // Filter for relevance
      const relevantDocs = allResults.filter(doc => isDocumentRelevant(doc, loc.name));
      debugMessages.push(`✅ After relevance filter: ${relevantDocs.length} / ${allResults.length}`);
      
      // Sort by relevance score
      const sortedDocs = relevantDocs.sort((a, b) => {
        const scoreA = calculateRelevanceScore(a, loc.name);
        const scoreB = calculateRelevanceScore(b, loc.name);
        return scoreB - scoreA;
      });
      
      // Deduplicate by title
      const seenTitles = new Set<string>();
      const unique = sortedDocs.filter((doc) => {
>>>>>>> bc36e49d9bd7f52521c24db351f7b16c36714141
        const key = doc.title.trim().toLowerCase();
        if (seenTitles.has(key)) return false;
        seenTitles.add(key);
        return true;
      });
<<<<<<< HEAD

      setRelatedDocs(unique.slice(0, 6));
    } catch {
=======
      
      // Limit to 8 most relevant documents
      const topRelevant = unique.slice(0, 8);
      
      debugMessages.push(`📚 Final results: ${topRelevant.length} relevant documents`);
      setSearchDebug(debugMessages);
      console.log(`📚 Found ${topRelevant.length} relevant documents for ${loc.name}`);
      
      setRelatedDocs(topRelevant);
      
    } catch (err) {
      console.error("Error fetching related docs:", err);
      setSearchDebug([`Error: ${err}`]);
>>>>>>> bc36e49d9bd7f52521c24db351f7b16c36714141
      setRelatedDocs([]);
    } finally {
      setDocsLoading(false);
    }
  };

  const handlePointClick = (point: DataPoint) => {
    setSelectedPoint(point);
    setShowDocsPanel(true);
    fetchRelatedDocs(point);
  };

  const visiblePoints = ALL_DATA_POINTS.filter((p) =>
    filterCategory === "all" || p.category === filterCategory
  );

  const voyageCount   = ALL_DATA_POINTS.filter((p) => p.category === "voyage").length;
  const evidenceCount = ALL_DATA_POINTS.filter((p) => p.category === "evidence").length;

  return (
    <div className="flex flex-col h-full bg-gray-100">
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm flex-shrink-0">
        <h1 className="text-xl font-display font-bold text-gray-900">Data Map</h1>
        <p className="text-xs text-gray-400 mt-0.5">
<<<<<<< HEAD
          Global locations from the 1421 Foundation knowledge base — click any marker to find related documents
=======
          Zheng He's voyage locations (1403–1433) — click a marker to find related documents
>>>>>>> bc36e49d9bd7f52521c24db351f7b16c36714141
        </p>
      </div>

      {/* Filter bar */}
      <div className="px-6 py-2 bg-white border-b border-gray-200 flex items-center gap-3 flex-shrink-0">
        <span className="text-xs text-gray-500 font-medium">Show:</span>
        {(["all", "voyage", "evidence"] as const).map((cat) => (
          <button key={cat} onClick={() => setFilterCategory(cat)}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
              filterCategory === cat
                ? "bg-gold text-white border-gold"
                : "border-gray-300 text-gray-600 hover:border-gold hover:text-gold bg-white"
            }`}>
            {cat === "all"      && `All (${ALL_DATA_POINTS.length})`}
            {cat === "voyage"   && `Confirmed voyages (${voyageCount})`}
            {cat === "evidence" && `Evidence locations (${evidenceCount})`}
          </button>
        ))}
      </div>

      <div className="relative flex-1 min-h-0 flex">
        <div className="flex-1 relative">
          <MapContainer center={[20, 30]} zoom={2}
            style={{ height: "100%", width: "100%" }} zoomControl={true}>
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {visiblePoints.map((point) => (
              <Marker key={point.id}
                position={[point.lat, point.lon]}
                icon={point.category === "voyage" ? redIcon : blueIcon}
                eventHandlers={{ click: () => handlePointClick(point) }}>
                <Popup>
                  <div className="text-sm max-w-xs">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
                        point.category === "voyage"
                          ? "bg-red-100 text-red-700"
                          : "bg-blue-100 text-blue-700"
                      }`}>
                        {point.category === "voyage" ? "Voyage stop" : "Evidence"}
                      </span>
                      {point.year && <span className="text-xs text-gray-400">{point.year}</span>}
                    </div>
                    <p className="font-bold text-gray-900">{point.name}</p>
                    <p className="text-xs mt-1 text-gray-700 leading-relaxed">{point.event}</p>
                    <button onClick={() => handlePointClick(point)}
                      className="mt-2 text-xs text-gold font-semibold flex items-center gap-1 hover:underline">
                      <FileText className="h-3 w-3" /> View related documents
                    </button>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>

          {/* Stats overlay — left-14 to clear zoom controls */}
          <div className="absolute top-4 left-14 bg-white/95 backdrop-blur-sm rounded-lg border border-gray-200 px-4 py-2 z-[1000] shadow-sm">
            <p className="text-xs text-gray-400 uppercase tracking-wider">Locations</p>
            <p className="text-2xl font-display font-bold text-gold leading-none mt-0.5">{visiblePoints.length}</p>
          </div>

          {/* Legend */}
          <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur-sm rounded-lg border border-gray-200 p-3 z-[1000] shadow-sm">
            <p className="text-xs font-semibold text-gray-700 mb-2">Legend</p>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-3 h-3 rounded-full bg-red-500 inline-block" />
              <span className="text-xs text-gray-600">Confirmed voyage stop</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-blue-500 inline-block" />
              <span className="text-xs text-gray-600">Evidence / research location</span>
            </div>
            <p className="text-xs text-gray-400 mt-2 italic">Click any marker for documents</p>
          </div>
        </div>

        {/* Related documents side panel */}
        {showDocsPanel && selectedPoint && (
          <div className="w-80 bg-white border-l border-gray-200 flex flex-col z-[999] shadow-lg">
            <div className="px-4 py-3 border-b border-gray-200 flex items-start justify-between bg-gray-50">
              <div className="min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
                    selectedPoint.category === "voyage"
                      ? "bg-red-100 text-red-700"
                      : "bg-blue-100 text-blue-700"
                  }`}>
                    {selectedPoint.category === "voyage" ? "Voyage stop" : "Evidence"}
                  </span>
                  {selectedPoint.year && <span className="text-xs text-gray-400">{selectedPoint.year}</span>}
                </div>
                <h3 className="text-sm font-bold text-gold">{selectedPoint.name}</h3>
                <p className="text-xs text-gray-500 mt-1 leading-snug">{selectedPoint.event}</p>
              </div>
              <button onClick={() => setShowDocsPanel(false)}
                className="text-gray-400 hover:text-gray-600 flex-shrink-0 ml-2 mt-1">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="px-4 py-2 border-b border-gray-100">
              <p className="text-xs font-semibold text-gray-600 flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-gold" />
                Related documents from knowledge base
              </p>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
              {docsLoading && (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gold" />
                </div>
              )}
              {!docsLoading && relatedDocs.length === 0 && (
                <div className="text-center py-6">
                  <p className="text-xs text-gray-400 mb-3">No documents found for "{selectedPoint.name}".</p>
                  <button
                    onClick={() => navigate(`/documents?search=${encodeURIComponent(selectedPoint.searchTerm)}`)}
                    className="text-xs text-gold font-semibold hover:underline">
                    Search documents manually →
                  </button>
                </div>
              )}
              {!docsLoading && relatedDocs.map((doc) => (
                <div key={doc.id}
                  className="rounded-lg border border-gray-200 bg-gray-50 p-3 hover:border-gold/40 transition-colors">
                  <div className="flex items-start gap-2">
<<<<<<< HEAD
                    {/* Uniform gold badge — no special colour for any position */}
                    <div className="flex-shrink-0 w-5 h-5 rounded-full bg-gold/10 border border-gold/30 flex items-center justify-center">
                      <span className="text-gold text-[10px] font-bold">{index + 1}</span>
                    </div>
                    <div className="flex-1 min-w-0">
=======
                    <CheckCircle className="h-3.5 w-3.5 text-emerald-500 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
>>>>>>> bc36e49d9bd7f52521c24db351f7b16c36714141
                      <p className="text-xs font-semibold text-gray-900 leading-snug">{doc.title}</p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {[
                          doc.author !== "Unknown" && doc.author,
                          doc.year > 0 && doc.year,
                          doc.type && doc.type !== "unknown" && doc.type,
                        ].filter(Boolean).join(" · ")}
                      </p>
                      <button
                        onClick={() => navigate(`/documents?search=${encodeURIComponent(doc.id)}`)}
                        className="mt-2 text-xs text-gold font-semibold flex items-center gap-1 hover:underline">
                        <FileText className="h-3 w-3" /> View Document
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="px-4 py-3 border-t border-gray-100">
              <button
                onClick={() => navigate(`/documents?search=${encodeURIComponent(selectedPoint.searchTerm)}`)}
                className="w-full text-xs text-gold font-semibold flex items-center justify-center gap-1.5 hover:underline">
                <FileText className="h-3.5 w-3.5" />
                Search all documents for "{selectedPoint.name}"
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
