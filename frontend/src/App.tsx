import { NavLink, Outlet } from "react-router-dom";
import {
  MessageSquare,
  Map,
  Send,
  Home,
  BarChart3,
  Settings,
  FileText,
} from "lucide-react";

const NAV = [
  { to: "/",          label: "Dashboard",  icon: Home },
  { to: "/chat",      label: "Chat",       icon: MessageSquare },
  { to: "/map",       label: "Voyage Map", icon: Map },
  { to: "/documents", label: "Documents",  icon: FileText },
  { to: "/analytics", label: "Analytics",  icon: BarChart3 },
  { to: "/feedback",  label: "Feedback",   icon: Send },
  { to: "/settings",  label: "Settings",   icon: Settings },
];

export default function App() {
  return (
    <div className="flex h-screen bg-gray-100">

      {/* ── Sidebar ──────────────────────────────────────────────────── */}
      <aside className="w-72 bg-white border-r border-gray-200 flex flex-col flex-shrink-0 shadow-sm">

        {/* Logo */}
        <div className="px-6 py-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-gold flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-display font-bold text-white tracking-tight leading-none">
                1421
              </span>
            </div>
            <div>
              <h1 className="text-lg font-display font-bold text-gray-900 leading-none">
                Foundation
              </h1>
              <p className="text-xs text-gray-400 mt-0.5">Research System</p>
            </div>
          </div>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-4 py-5 space-y-1 overflow-y-auto">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-4 px-4 py-3.5 rounded-xl text-[15px] font-medium transition-all duration-150 ${
                  isActive
                    ? "bg-gold text-white shadow-sm"
                    : "text-gray-500 hover:text-gray-900 hover:bg-gray-100 border border-transparent"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    className={`h-[22px] w-[22px] flex-shrink-0 ${
                      isActive ? "text-white" : "text-gray-400"
                    }`}
                  />
                  <span>{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div className="px-4 py-5 border-t border-gray-200">
          <div className="flex items-center gap-3 px-3 py-3 rounded-xl bg-gray-50 border border-gray-200">
            <div className="w-9 h-9 rounded-full bg-gold flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-bold text-white">R</span>
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-gray-900 leading-none">Researcher</p>
              <p className="text-xs text-gray-400 mt-0.5 truncate">1421 Foundation</p>
            </div>
          </div>
        </div>
      </aside>

      {/* ── Main ─────────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-hidden bg-gray-100">
        <Outlet />
      </main>
    </div>
  );
}