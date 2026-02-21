import { NavLink, Outlet } from "react-router-dom";
import { 
  MessageSquare, 
  Map, 
  Send,
  Home,
  BarChart3,
  Settings,
  FileText 
} from "lucide-react";

const NAV = [
  { to: "/", label: "Dashboard", icon: Home },
  { to: "/chat", label: "Chat", icon: MessageSquare },
  { to: "/map", label: "Voyage Map", icon: Map },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/documents", label: "Documents", icon: FileText },
  { to: "/feedback", label: "Feedback", icon: Send },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function App() {
  return (
    <div className="flex h-screen bg-navy-dark">
      {/* Sidebar */}
      <aside className="w-64 bg-navy border-r border-gray-800 flex flex-col">
        <div className="p-5 border-b border-gray-800">
          <h1 className="text-xl font-display font-bold text-gold">1421</h1>
          <p className="text-xs text-gray-400 mt-1">Foundation Research</p>
        </div>
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? "bg-gold/20 text-gold font-semibold"
                    : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
                }`
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gold/20 flex items-center justify-center">
              <span className="text-sm font-bold text-gold">U</span>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-200">Researcher</p>
              <p className="text-xs text-gray-400">1421 Foundation</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-hidden bg-navy-dark">
        <Outlet />
      </main>
    </div>
  );
}