import { NavLink, Outlet } from "react-router-dom";
import { MessageSquare, Map, Send } from "lucide-react";

const NAV = [
  { to: "/chat", label: "Chat", icon: MessageSquare },
  { to: "/map", label: "Voyage Map", icon: Map },
  { to: "/feedback", label: "Feedback", icon: Send },
];

export default function App() {
  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-56 bg-navy border-r border-gray-700 flex flex-col">
        <div className="p-5 border-b border-gray-700">
          <h1 className="text-xl font-display font-bold text-gold">1421</h1>
          <p className="text-xs text-gray-400 mt-1">Foundation Research</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
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
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
