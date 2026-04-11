import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  MessageSquare, Map, Send, Home, BarChart3, Settings,
  FileText, ChevronLeft, ChevronRight,
} from "lucide-react";

// Side Navigation bar, with logo image later on
const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: Home },
  { to: "/chat", label: "Chat", icon: MessageSquare },
  { to: "/documents", label: "Documents", icon: FileText },
  { to: "/map", label: "Data Map", icon: Map },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/feedback", label: "Feedback", icon: Send },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [logoFailed, setLogoFailed] = useState(false);

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const sidebarWidth = sidebarCollapsed ? "w-20" : "w-72";
  // text content
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className={`bg-white border-r border-gray-200 flex flex-col flex-shrink-0 shadow-sm transition-all duration-300 ${sidebarWidth}`}>

        {/* Logo header with collapse button */}
        <div className="relative border-b border-gray-200 flex-shrink-0 overflow-hidden" style={{ height: "80px" }}>
          {!logoFailed ? (
            <img
              src="/logo.JPG"
              alt="1421 Foundation"
              className="absolute inset-0 w-full h-full object-cover"
              onError={() => setLogoFailed(true)}
            />
          ) : (
            <div className="absolute inset-0 bg-gold flex items-center justify-center">
              <span className="text-xl font-bold text-white">1421</span>
            </div>
          )}

          {/* Collapse button */}
          <button
            onClick={toggleSidebar}
            className="absolute top-2 right-2 z-10 w-7 h-7 rounded-lg flex items-center justify-center bg-black/30 text-white hover:bg-black/50 transition-colors"
            title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        {/* Navigation links */}
        <nav className="flex-1 px-3 py-5 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const { to, label, icon: Icon } = item;
            
            return (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                title={sidebarCollapsed ? label : undefined}
                className={({ isActive }) => {
                  let baseClasses = "flex items-center gap-4 px-3 py-3.5 rounded-xl text-[15px] font-medium transition-all duration-150";
                  
                  if (sidebarCollapsed) {
                    baseClasses += " justify-center";
                  }
                  
                  if (isActive) {
                    return `${baseClasses} bg-gold text-white shadow-sm`;
                  } else {
                    return `${baseClasses} text-gray-500 hover:text-gray-900 hover:bg-gray-100 border border-transparent`;
                  }
                }}
              >
                {({ isActive }) => (
                  <>
                    <Icon className={`h-[22px] w-[22px] flex-shrink-0 ${isActive ? "text-white" : "text-gray-400"}`} />
                    {!sidebarCollapsed && <span>{label}</span>}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* User footer - expanded state */}
        {!sidebarCollapsed && (
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
        
        {/* User footer - collapsed state */}
        {sidebarCollapsed && (
          <div className="px-3 py-4 border-t border-gray-200 flex justify-center">
            <div className="w-9 h-9 rounded-full bg-gold flex items-center justify-center">
              <span className="text-sm font-bold text-white">R</span>
            </div>
          </div>
        )}
      </aside>

      {/* Main content area */}
      <main className="flex-1 overflow-hidden bg-gray-100">
        <Outlet />
      </main>
    </div>
  );
}