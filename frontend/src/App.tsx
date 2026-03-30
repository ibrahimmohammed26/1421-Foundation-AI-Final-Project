import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  MessageSquare, Map, Send, Home, BarChart3, Settings,
  FileText, ChevronLeft, ChevronRight,
} from "lucide-react";

const NAV = [
  { to: "/",          label: "Dashboard",  icon: Home },
  { to: "/chat",      label: "Chat",       icon: MessageSquare },
  { to: "/documents", label: "Documents",  icon: FileText },
  { to: "/map",       label: "Data Map", icon: Map },
  { to: "/analytics", label: "Analytics",  icon: BarChart3 },
  { to: "/feedback",  label: "Feedback",   icon: Send },
  { to: "/settings",  label: "Settings",   icon: Settings },
];

export default function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [logoError, setLogoError] = useState(false);

  return (
    <div className="flex h-screen bg-gray-100">
      <aside className={`bg-white border-r border-gray-200 flex flex-col flex-shrink-0 shadow-sm transition-all duration-300 ${collapsed ? "w-20" : "w-72"}`}>

        {/* Logo header — no text overlay, just image + collapse button */}
        <div className="relative border-b border-gray-200 flex-shrink-0 overflow-hidden" style={{ height: "80px" }}>
          {!logoError ? (
            <img
              src="/logo.JPG"
              alt="1421 Foundation"
              className="absolute inset-0 w-full h-full object-cover"
              onError={() => setLogoError(true)}
            />
          ) : (
            <div className="absolute inset-0 bg-gold flex items-center justify-center">
              <span className="text-xl font-bold text-white">1421</span>
            </div>
          )}

          {/* Collapse button only — no text */}
          <button
            onClick={() => setCollapsed((c) => !c)}
            className="absolute top-2 right-2 z-10 w-7 h-7 rounded-lg flex items-center justify-center bg-black/30 text-white hover:bg-black/50 transition-colors"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-3 py-5 space-y-1 overflow-y-auto">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              title={collapsed ? label : undefined}
              className={({ isActive }) =>
                `flex items-center gap-4 px-3 py-3.5 rounded-xl text-[15px] font-medium transition-all duration-150 ${collapsed ? "justify-center" : ""} ${
                  isActive
                    ? "bg-gold text-white shadow-sm"
                    : "text-gray-500 hover:text-gray-900 hover:bg-gray-100 border border-transparent"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={`h-[22px] w-[22px] flex-shrink-0 ${isActive ? "text-white" : "text-gray-400"}`} />
                  {!collapsed && <span>{label}</span>}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        {!collapsed && (
          <div className="px-4 py-4 border-t border-gray-200">
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
        )}
        {collapsed && (
          <div className="px-3 py-4 border-t border-gray-200 flex justify-center">
            <div className="w-9 h-9 rounded-full bg-gold flex items-center justify-center">
              <span className="text-sm font-bold text-white">R</span>
            </div>
          </div>
        )}
      </aside>

      <main className="flex-1 overflow-hidden bg-gray-100">
        <Outlet />
      </main>
    </div>
  );
}