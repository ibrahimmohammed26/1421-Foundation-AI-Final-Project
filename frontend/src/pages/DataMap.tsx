import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { searchDocuments } from "@/lib/api";
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
  year?: number;  // Only voyage locations have years
  event: string;
  searchTerms: string[];
  requiredKeywords: string[];
  category: "voyage" | "evidence";
}

interface RelatedDoc {
  id: string;
  title: string;
  author: string;
  year: number;
  type: string;
  url?: string;
  _relevanceScore: number;
}

const EXCLUDE_TITLE_PATTERNS = [
  "gallery", "minoan", "atlantis", "fresco", "artist impression",
  "image gallery", "photo gallery", "cookie", "privacy policy",
];

function scoreDoc(doc: any, point: DataPoint): number {
  const title   = (doc.title || "").toLowerCase();
  const preview = (doc.content_preview || "").toLowerCase();
  const combined = title + " " + preview;

  const hasRequired = point.requiredKeywords.some(
    (kw) => combined.includes(kw.toLowerCase())
  );
  if (!hasRequired) return 0;

  let score = 0;

  for (const kw of point.requiredKeywords) {
    const k = kw.toLowerCase();
    if (title.includes(k))   score += 15;
    if (preview.includes(k)) score += 5;
  }

  for (const term of point.searchTerms) {
    const t = term.toLowerCase();
    const words = t.split(" ").filter((w) => w.length > 3);
    for (const word of words) {
      if (title.includes(word))   score += 4;
      if (preview.includes(word)) score += 1;
    }
  }

  if (doc.similarity_score != null && doc.similarity_score > 0) {
    score += Math.min(doc.similarity_score * 3, 6);
  }

  return score;
}

// ── ALL DATA POINTS ───────────────────────────────────────────────────────────
const ALL_DATA_POINTS: DataPoint[] = [

  // ══ CHINA ════════════════════════════════════════════════════════════
  {
    id: "nanjing", name: "Nanjing", lat: 32.06, lon: 118.80, year: 1403, category: "voyage",
    event: "Yongle Emperor commissions the treasure fleet; first voyage departs 1405 with 317 ships and 28,000 men.",
    searchTerms: ["Nanjing treasure fleet", "Nanjing Zheng He", "treasure fleet departs"],
    requiredKeywords: ["nanjing", "treasure fleet", "first voyage"],
  },
  {
    id: "quanzhou", name: "Quanzhou", lat: 24.87, lon: 118.68, year: 1405, category: "voyage",
    event: "Major departure port and home of the world's largest medieval shipyard.",
    searchTerms: ["Quanzhou shipyard", "Quanzhou port", "Chinese shipyard"],
    requiredKeywords: ["quanzhou", "shipyard", "departure port"],
  },
  {
    id: "beijing", name: "Beijing", lat: 39.90, lon: 116.41, year: 1421, category: "voyage",
    event: "Imperial capital under the Yongle Emperor; seat of power during all seven voyages.",
    searchTerms: ["Beijing Yongle Emperor", "Ming court Beijing", "Forbidden City"],
    requiredKeywords: ["beijing", "yongle", "ming court", "imperial"],
  },

  // ══ SOUTHEAST ASIA ═══════════════════════════════════════════════════
  {
    id: "champa", name: "Champa", lat: 10.82, lon: 106.63, year: 1405, category: "voyage",
    event: "First stop on Voyage 1 — Southeast Asian ally (modern Vietnam).",
    searchTerms: ["Champa Vietnam Zheng He", "Champa kingdom", "Champa voyage"],
    requiredKeywords: ["champa", "vietnam"],
  },
  {
    id: "java", name: "Java", lat: -7.61, lon: 110.71, year: 1406, category: "voyage",
    event: "Diplomatic missions conducted on Java during Voyage 1.",
    searchTerms: ["Java Zheng He", "Java Ming dynasty", "Java diplomatic"],
    requiredKeywords: ["java"],
  },
  {
    id: "sumatra", name: "Sumatra", lat: -0.59, lon: 101.34, year: 1406, category: "voyage",
    event: "Strategic trading post established at Palembang, Sumatra.",
    searchTerms: ["Sumatra Palembang Zheng He", "Sumatra Ming", "Palembang trading"],
    requiredKeywords: ["sumatra", "palembang"],
  },
  {
    id: "malacca", name: "Malacca", lat: 2.19, lon: 102.25, year: 1406, category: "voyage",
    event: "Key port established; local piracy suppressed by Zheng He's fleet.",
    searchTerms: ["Malacca Zheng He", "Malacca strait", "Melaka Ming"],
    requiredKeywords: ["malacca", "melaka"],
  },
  {
    id: "siam", name: "Siam", lat: 13.74, lon: 100.52, year: 1408, category: "voyage",
    event: "Voyage 2 — diplomatic relations established with modern Thailand.",
    searchTerms: ["Siam Thailand Zheng He", "Siam tribute", "Thailand Ming"],
    requiredKeywords: ["siam", "thailand"],
  },
  {
    id: "brunei", name: "Brunei", lat: 4.94, lon: 114.95, category: "evidence",
    event: "Chinese porcelain and artefacts found indicating Ming dynasty trade contact.",
    searchTerms: ["Brunei Chinese porcelain", "Brunei Ming trade"],
    requiredKeywords: ["brunei", "borneo"],
  },
  {
    id: "philippines", name: "Philippines", lat: 12.88, lon: 121.77, category: "evidence",
    event: "Chinese ceramics and evidence of pre-colonial contact with Ming dynasty fleets.",
    searchTerms: ["Philippines Chinese ceramics", "Philippines Ming dynasty"],
    requiredKeywords: ["philippines", "filipino"],
  },

  // ══ SOUTH ASIA ════════════════════════════════════════════════════════
  {
    id: "sri-lanka", name: "Sri Lanka", lat: 7.87, lon: 80.77, year: 1409, category: "voyage",
    event: "Voyage 2 — trilingual inscription erected at Galle in Chinese, Tamil and Persian.",
    searchTerms: ["Sri Lanka Galle trilingual inscription", "Galle Sri Lanka", "Ceylon Zheng He"],
    requiredKeywords: ["sri lanka", "galle", "ceylon", "trilingual"],
  },
  {
    id: "calicut", name: "Calicut", lat: 11.26, lon: 75.78, year: 1407, category: "voyage",
    event: "Primary destination on Malabar Coast, India. Zheng He dies here 1433.",
    searchTerms: ["Calicut Zheng He", "Kozhikode Malabar", "Calicut India Ming"],
    requiredKeywords: ["calicut", "kozhikode", "malabar"],
  },
  {
    id: "cochin", name: "Cochin", lat: 9.93, lon: 76.27, category: "evidence",
    event: "Indian trading port with strong evidence of Ming dynasty ceramic trade.",
    searchTerms: ["Cochin India Chinese trade", "Kochi Ming dynasty"],
    requiredKeywords: ["cochin", "kochi"],
  },
  {
    id: "maldives", name: "Maldives", lat: 3.20, lon: 73.22, category: "evidence",
    event: "Chinese vessels recorded visiting; artefacts found on the islands.",
    searchTerms: ["Maldives Chinese", "Maldives Ming trade"],
    requiredKeywords: ["maldives", "maldive"],
  },

  // ══ MIDDLE EAST ══════════════════════════════════════════════════════
  {
    id: "hormuz", name: "Hormuz", lat: 27.16, lon: 56.28, year: 1414, category: "voyage",
    event: "Voyage 4 — Persian Gulf reached for first time; 18 states sent tribute.",
    searchTerms: ["Hormuz Persian Gulf Zheng He", "Ormus Zheng He", "Hormuz tribute"],
    requiredKeywords: ["hormuz", "ormus", "persian gulf"],
  },
  {
    id: "aden", name: "Aden", lat: 12.79, lon: 45.02, year: 1417, category: "voyage",
    event: "Voyage 5 — Arabian Peninsula reached; gifts of zebras and lions received.",
    searchTerms: ["Aden Yemen Zheng He", "Aden fifth voyage", "Arabian Peninsula Ming"],
    requiredKeywords: ["aden", "yemen", "arabian"],
  },
  {
    id: "jidda", name: "Jidda", lat: 21.49, lon: 39.19, year: 1432, category: "voyage",
    event: "Voyage 7 — Red Sea reached; auxiliary fleet sent towards Mecca.",
    searchTerms: ["Jidda Mecca Red Sea Zheng He", "Jeddah Ming seventh voyage"],
    requiredKeywords: ["jidda", "jeddah", "mecca", "red sea"],
  },
  {
    id: "muscat", name: "Muscat", lat: 23.58, lon: 58.40, category: "evidence",
    event: "Omani coast visited during Persian Gulf expeditions; Chinese coins found.",
    searchTerms: ["Muscat Oman Chinese", "Oman Ming coins"],
    requiredKeywords: ["muscat", "oman"],
  },

  // ══ EAST AFRICA ══════════════════════════════════════════════════════
  {
    id: "mogadishu", name: "Mogadishu", lat: 2.05, lon: 45.32, year: 1418, category: "voyage",
    event: "Voyage 5 — Somali coast; first Chinese fleet to reach East Africa.",
    searchTerms: ["Mogadishu Somalia Zheng He", "Mogadishu fifth voyage", "Somali coast Chinese"],
    requiredKeywords: ["mogadishu", "somalia", "somali"],
  },
  {
    id: "malindi", name: "Malindi", lat: -3.22, lon: 40.12, year: 1418, category: "voyage",
    event: "Voyage 5 — Kenya coast; famous giraffe gifted to the Yongle Emperor.",
    searchTerms: ["Malindi Kenya Zheng He", "Malindi giraffe Yongle", "Kenya coast fifth voyage"],
    requiredKeywords: ["malindi", "kenya", "giraffe"],
  },
  {
    id: "mombasa", name: "Mombasa", lat: -4.04, lon: 39.67, year: 1419, category: "voyage",
    event: "Voyage 5 — East African trade firmly established.",
    searchTerms: ["Mombasa Kenya Zheng He", "Mombasa Ming trade", "East Africa fifth voyage"],
    requiredKeywords: ["mombasa"],
  },
  {
    id: "zanzibar", name: "Zanzibar", lat: -6.17, lon: 39.20, year: 1421, category: "voyage",
    event: "Voyage 6 — southernmost confirmed point of the treasure fleet.",
    searchTerms: ["Zanzibar Zheng He", "Zanzibar sixth voyage"],
    requiredKeywords: ["zanzibar"],
  },
  {
    id: "sofala", name: "Sofala", lat: -20.17, lon: 34.70, category: "evidence",
    event: "Menzies argues Chinese maps show detailed knowledge of the Mozambique coast.",
    searchTerms: ["Sofala Mozambique Chinese map", "Mozambique Ming"],
    requiredKeywords: ["sofala", "mozambique"],
  },
  {
    id: "madagascar", name: "Madagascar", lat: -18.77, lon: 46.87, category: "evidence",
    event: "Chinese ceramic fragments and genetic evidence suggest Ming-era contact with Madagascar.",
    searchTerms: ["Madagascar Chinese contact", "Madagascar Ming dynasty ceramics"],
    requiredKeywords: ["madagascar"],
  },

  // ══ EUROPE ════════════════════════════════════════════════════════════
  {
    id: "venice", name: "Venice", lat: 45.44, lon: 12.33, category: "evidence",
    event: "Fra Mauro's 1450 world map shows detailed knowledge of Africa and Asia, possibly derived from Chinese charts brought via traders.",
    searchTerms: ["Venice Fra Mauro map Chinese", "Fra Mauro world map", "Venice Ming maps"],
    requiredKeywords: ["venice", "fra mauro"],
  },
  {
    id: "portugal", name: "Portugal", lat: 38.72, lon: -9.14, category: "evidence",
    event: "Menzies argues Portuguese cartographers had access to Chinese charts that aided Vasco da Gama's route around Africa.",
    searchTerms: ["Portugal Chinese maps Vasco da Gama", "Portuguese Ming charts", "Portugal 1421"],
    requiredKeywords: ["portugal", "portuguese", "vasco da gama"],
  },
  {
    id: "greenland", name: "Greenland", lat: 72.00, lon: -42.00, category: "evidence",
    event: "Menzies contends Chinese fleets rounded the Arctic and mapped Greenland before European contact.",
    searchTerms: ["Greenland Chinese Arctic", "Greenland Ming 1421"],
    requiredKeywords: ["greenland", "arctic"],
  },
  {
    id: "dieppe-france", name: "Dieppe, France", lat: 49.93, lon: 1.08, category: "evidence",
    event: "The Dieppe maps (1540s) show 'Java la Grande' — a large southern landmass Menzies argues is Australia, derived from Chinese originals.",
    searchTerms: ["Dieppe maps Java Grande Australia", "Dieppe France Chinese maps", "Dieppe cartography"],
    requiredKeywords: ["dieppe", "java la grande", "dieppe map"],
  },
  {
    id: "piri-reis", name: "Piri Reis Map (Turkey)", lat: 40.98, lon: 28.85, category: "evidence",
    event: "The Piri Reis map of 1513 appears to show Antarctica and the Americas. Menzies argues it was derived from Chinese charts.",
    searchTerms: ["Piri Reis map Chinese Antarctica", "Piri Reis 1513", "Ottoman map Chinese source"],
    requiredKeywords: ["piri reis", "piri re'is"],
  },

  // ══ AUSTRALIA ════════════════════════════════════════════════════════
  {
    id: "darwin", name: "Darwin", lat: -12.46, lon: 130.84, category: "evidence",
    event: "Chinese artefacts and stone anchors found near Darwin; possible evidence of early contact with northern Australia.",
    searchTerms: ["Darwin Australia Chinese artefacts", "Northern Territory Chinese contact"],
    requiredKeywords: ["darwin", "northern territory"],
  },
  {
    id: "broome", name: "Broome", lat: -17.96, lon: 122.23, category: "evidence",
    event: "Beeswax figures and Chinese coins discovered on Australia's northwest coast near Broome.",
    searchTerms: ["Broome Australia Chinese beeswax", "Broome Chinese coins northwest"],
    requiredKeywords: ["broome", "beeswax"],
  },
  {
    id: "perth", name: "Perth", lat: -31.95, lon: 115.86, category: "evidence",
    event: "Research suggests Chinese fleets may have charted the southwest Australian coast, with stone inscriptions claimed near Mundaring.",
    searchTerms: ["Perth Australia Chinese", "Mundaring inscription Western Australia"],
    requiredKeywords: ["perth", "mundaring", "western australia"],
  },
  {
    id: "sydney", name: "Sydney", lat: -33.87, lon: 151.21, category: "evidence",
    event: "Claims of Chinese presence in eastern Australia appear in 1421 Foundation research.",
    searchTerms: ["Sydney Australia Chinese 1421", "Eastern Australia Ming"],
    requiredKeywords: ["sydney", "eastern australia"],
  },
  {
    id: "adelaide", name: "Adelaide", lat: -34.93, lon: 138.60, category: "evidence",
    event: "Southern Australian coast discussed in context of Chinese mapping of the continent.",
    searchTerms: ["Adelaide South Australia Chinese", "South Australia Ming mapping"],
    requiredKeywords: ["adelaide", "south australia"],
  },
  {
    id: "java-la-grande", name: "Java la Grande (Australia)", lat: -22.00, lon: 135.00, category: "evidence",
    event: "'Java la Grande' on the Dieppe maps is argued by Menzies to represent Australia, charted by Chinese fleets around 1421.",
    searchTerms: ["Java la Grande Australia Dieppe", "Australia Chinese mapping Menzies"],
    requiredKeywords: ["java la grande", "australia", "dieppe"],
  },

  // ══ NEW ZEALAND ══════════════════════════════════════════════════════
  {
    id: "northland-nz", name: "Northland, NZ", lat: -35.73, lon: 174.32, category: "evidence",
    event: "Waitaha oral traditions and stone structures in Northland suggest pre-Māori contact possibly linked to Chinese voyages.",
    searchTerms: ["New Zealand Waitaha Chinese", "Northland New Zealand Chinese contact"],
    requiredKeywords: ["new zealand", "waitaha", "northland"],
  },
  {
    id: "south-island-nz", name: "South Island, NZ", lat: -44.00, lon: 170.50, category: "evidence",
    event: "Genetic and archaeological evidence of Chinese contact with New Zealand before European arrival; wreck claims at Moeraki.",
    searchTerms: ["New Zealand Maori Chinese genetics", "South Island New Zealand Chinese", "Moeraki wreck"],
    requiredKeywords: ["new zealand", "maori", "moeraki"],
  },

  // ══ SOUTH AMERICA ═════════════════════════════════════════════════════
  {
    id: "ecuador", name: "Ecuador", lat: -1.83, lon: -78.18, category: "evidence",
    event: "Pre-Columbian chickens (matching Chinese genetic profiles) and sweet potato evidence points to Pacific contact with Chinese fleets.",
    searchTerms: ["Ecuador Chinese chickens pre-Columbian", "Ecuador Pacific contact Ming"],
    requiredKeywords: ["ecuador", "pre-columbian chicken"],
  },
  {
    id: "peru", name: "Peru", lat: -9.19, lon: -75.02, category: "evidence",
    event: "Menzies argues Chinese navigators reached Peru; genetic and botanical evidence cited alongside Andean cultural parallels.",
    searchTerms: ["Peru Chinese Inca 1421", "Peru pre-Columbian Chinese", "Peru Ming contact"],
    requiredKeywords: ["peru", "inca"],
  },
  {
    id: "brazil", name: "Brazil", lat: -14.24, lon: -51.93, category: "evidence",
    event: "1421 Foundation research cites possible Chinese presence on the Brazilian coast before Cabral's 1500 arrival.",
    searchTerms: ["Brazil Chinese pre-Columbian", "Brazil Ming 1421", "Brazil Chinese coast"],
    requiredKeywords: ["brazil", "brazilian"],
  },
  {
    id: "chile", name: "Chile", lat: -35.68, lon: -71.54, category: "evidence",
    event: "Araucanian people of Chile show possible Asian genetic markers discussed in the 1421 hypothesis.",
    searchTerms: ["Chile Araucanian Chinese genetics", "Chile pre-Columbian Chinese"],
    requiredKeywords: ["chile", "araucanian"],
  },
  {
    id: "patagonia", name: "Patagonia", lat: -50.00, lon: -69.00, category: "evidence",
    event: "Menzies argues Chinese fleets reached southern South America and possibly rounded Cape Horn.",
    searchTerms: ["Patagonia Chinese Menzies", "Patagonia Ming 1421", "South America Chinese fleet"],
    requiredKeywords: ["patagonia", "cape horn"],
  },

  // ══ NEW LOCATIONS: PARAGUAY, ARGENTINA, FALKLANDS ═════════════════════════
  {
    id: "paraguay", name: "Paraguay", lat: -23.44, lon: -58.44, category: "evidence",
    event: "Annex 8 – Evidence of the Voyages of Chinese Fleets visiting Paraguay. Research suggests possible Ming dynasty contact with inland South America.",
    searchTerms: ["Paraguay Chinese fleets", "Paraguay Ming contact", "Annex 8 Paraguay"],
    requiredKeywords: ["paraguay", "annex 8", "chinese fleets"],
  },
  {
    id: "argentina", name: "Argentina", lat: -34.60, lon: -58.38, category: "evidence",
    event: "Annex 8 – Evidence of the Voyages of Chinese Fleets visiting Argentina. Archaeological and cartographic evidence suggests Chinese exploration of the Rio de la Plata region.",
    searchTerms: ["Argentina Chinese fleets", "Argentina Ming contact", "Annex 8 Argentina", "Rio de la Plata Chinese"],
    requiredKeywords: ["argentina", "annex 8", "rio de la plata"],
  },
  {
    id: "falklands", name: "Falkland Islands", lat: -51.80, lon: -59.52, category: "evidence",
    event: "Annex 8 – Evidence of the Voyages of Chinese Fleets visiting the Falkland Islands. The Falklands appear on pre-Columbian maps, which Menzies argues were derived from Chinese charts.",
    searchTerms: ["Falkland Islands Chinese", "Falklands pre-Columbian map", "Annex 8 Falklands", "Malvinas Chinese"],
    requiredKeywords: ["falkland", "malvinas", "annex 8"],
  },

  // ══ NORTH AMERICA ═════════════════════════════════════════════════════
  {
    id: "california", name: "California", lat: 36.78, lon: -119.42, category: "evidence",
    event: "Chinese brass plates and artefacts found along the California coast; Menzies argues Chinese fleets mapped North America.",
    searchTerms: ["California Chinese brass plates 1421", "California Ming contact pre-Columbian"],
    requiredKeywords: ["california"],
  },
  {
    id: "mexico", name: "Mexico", lat: 23.63, lon: -102.55, category: "evidence",
    event: "Evidence of pre-Columbian contact including Chinese-style stone anchors off the Mexican coast.",
    searchTerms: ["Mexico Chinese pre-Columbian", "Mexico Ming 1421"],
    requiredKeywords: ["mexico", "mexican"],
  },
  {
    id: "caribbean", name: "Caribbean", lat: 18.70, lon: -70.16, category: "evidence",
    event: "Menzies cites Chinese maps showing detailed Caribbean island outlines before Columbus.",
    searchTerms: ["Caribbean Chinese maps pre-Columbian", "Caribbean Ming 1421"],
    requiredKeywords: ["caribbean"],
  },
  {
    id: "rhode-island", name: "Rhode Island, USA", lat: 41.49, lon: -71.31, category: "evidence",
    event: "The Newport Tower in Rhode Island is claimed by Menzies to be a Chinese astronomical observatory built during the 1421 voyages.",
    searchTerms: ["Newport Tower Rhode Island Chinese", "Rhode Island Chinese observatory 1421"],
    requiredKeywords: ["newport tower", "rhode island"],
  },
  {
    id: "british-columbia", name: "British Columbia", lat: 49.28, lon: -123.12, category: "evidence",
    event: "Menzies argues Chinese settlers remained in the Pacific Northwest; linguistic links to Haida Gwaii claimed.",
    searchTerms: ["British Columbia Chinese settlement 1421", "Haida Chinese Menzies"],
    requiredKeywords: ["british columbia", "haida", "pacific northwest"],
  },

  // ══ ANTARCTICA ════════════════════════════════════════════════════════
  {
    id: "antarctica-west", name: "West Antarctica", lat: -75.00, lon: -90.00, category: "evidence",
    event: "Menzies argues Hong Bao's fleet charted the Antarctic coastline in 1421, visible on the Piri Reis map of 1513.",
    searchTerms: ["Antarctica Chinese Piri Reis 1421", "Antarctic coastline Chinese map Hong Bao"],
    requiredKeywords: ["antarctica", "antarctic", "hong bao", "piri reis"],
  },
  {
    id: "antarctica-east", name: "East Antarctica", lat: -72.00, lon: 75.00, category: "evidence",
    event: "Menzies contends Zhou Man's fleet sailed Antarctic waters and knowledge was passed to later European cartographers.",
    searchTerms: ["East Antarctica Chinese Zhou Man", "Antarctica Ming fleet 1421"],
    requiredKeywords: ["antarctica", "antarctic", "zhou man"],
  },
];

export default function DataMap() {
  const navigate = useNavigate();

  const [selectedPoint, setSelectedPoint]   = useState<DataPoint | null>(null);
  const [relatedDocs, setRelatedDocs]       = useState<RelatedDoc[]>([]);
  const [docsLoading, setDocsLoading]       = useState(false);
  const [showDocsPanel, setShowDocsPanel]   = useState(false);
  const [filterCategory, setFilterCategory] = useState<"all" | "voyage" | "evidence">("all");

  const fetchRelatedDocs = async (point: DataPoint) => {
    setDocsLoading(true);
    setRelatedDocs([]);
    try {
      const seenIds = new Set<string>();
      let allResults: any[] = [];

      for (const term of point.searchTerms) {
        try {
          const res = await searchDocuments(term, 20);
          for (const doc of (res.results || [])) {
            if (!seenIds.has(doc.id)) {
              seenIds.add(doc.id);
              allResults.push(doc);
            }
          }
        } catch {}
      }

      const filtered = allResults.filter((doc) => {
        const t = (doc.title || "").toLowerCase();
        return !EXCLUDE_TITLE_PATTERNS.some((p) => t.includes(p));
      });

      const scored: RelatedDoc[] = [];
      for (const doc of filtered) {
        const s = scoreDoc(doc, point);
        if (s > 0) {
          scored.push({
            id:              doc.id,
            title:           doc.title,
            author:          doc.author || "Unknown",
            year:            doc.year || 0,
            type:            doc.type || "document",
            url:             doc.url,
            _relevanceScore: s,
          });
        }
      }

      const seenTitles = new Set<string>();
      const unique = scored.filter((doc) => {
        const key = doc.title.trim().toLowerCase();
        if (seenTitles.has(key)) return false;
        seenTitles.add(key);
        return true;
      });

      unique.sort((a, b) => b._relevanceScore - a._relevanceScore);
      setRelatedDocs(unique.slice(0, 8));
    } catch {
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

  const visiblePoints = ALL_DATA_POINTS.filter(
    (p) => filterCategory === "all" || p.category === filterCategory
  );
  const voyageCount   = ALL_DATA_POINTS.filter((p) => p.category === "voyage").length;
  const evidenceCount = ALL_DATA_POINTS.filter((p) => p.category === "evidence").length;

  return (
    <div className="flex flex-col h-full bg-gray-100">
      <div className="border-b border-gray-200 px-6 py-4 bg-white shadow-sm flex-shrink-0">
        <h1 className="text-xl font-display font-bold text-gray-900">Data Map</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Global locations from the 1421 Foundation knowledge base — click any marker for related documents, ranked by relevance
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
                        point.category === "voyage" ? "bg-red-100 text-red-700" : "bg-blue-100 text-blue-700"
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

          {/* Stats overlay */}
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

        {/* Side panel */}
        {showDocsPanel && selectedPoint && (
          <div className="w-80 bg-white border-l border-gray-200 flex flex-col z-[999] shadow-lg">
            <div className="px-4 py-3 border-b border-gray-200 flex items-start justify-between bg-gray-50">
              <div className="min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
                    selectedPoint.category === "voyage" ? "bg-red-100 text-red-700" : "bg-blue-100 text-blue-700"
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
                {relatedDocs.length > 0
                  ? `${relatedDocs.length} relevant document${relatedDocs.length > 1 ? "s" : ""} — most relevant first`
                  : "Searching knowledge base…"}
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
                  <p className="text-xs text-gray-400 mb-1 font-medium">No relevant documents found</p>
                  <p className="text-xs text-gray-400 mb-3">
                    The knowledge base does not currently contain documents specifically about {selectedPoint.name}.
                  </p>
                  <button
                    onClick={() => navigate(`/documents?search=${encodeURIComponent(selectedPoint.searchTerms[0])}`)}
                    className="text-xs text-gold font-semibold hover:underline">
                    Browse documents manually →
                  </button>
                </div>
              )}
              {!docsLoading && relatedDocs.map((doc, index) => (
                <div key={doc.id}
                  className="rounded-lg border border-gray-200 bg-gray-50 p-3 hover:border-gold/40 transition-colors">
                  <div className="flex items-start gap-2">
                    <div className="flex-shrink-0 w-5 h-5 rounded-full bg-gold/10 border border-gold/30 flex items-center justify-center">
                      <span className="text-gold text-[10px] font-bold">{index + 1}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-gray-900 leading-snug">{doc.title}</p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {[doc.author !== "Unknown" && doc.author,
                          doc.year > 0 && doc.year,
                          doc.type && doc.type !== "unknown" && doc.type]
                          .filter(Boolean).join(" · ")}
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
                onClick={() => navigate(`/documents?search=${encodeURIComponent(selectedPoint.searchTerms[0])}`)}
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