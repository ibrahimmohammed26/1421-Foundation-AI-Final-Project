import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppProvider } from './context/AppContext';
import Sidebar from './components/Layout/Sidebar';
import Navbar from './components/Layout/Navbar';

// Pages
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Documents from './pages/Documents';
import Map from './pages/Map';
import Analytics from './pages/Analytics';
import Feedback from './pages/Feedback';
import Settings from './pages/Settings';

import './App.css';

const queryClient = new QueryClient();

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <QueryClientProvider client={queryClient}>
      <AppProvider>
        <Router>
          <div className="flex h-screen bg-gradient-to-br from-gray-50 to-gray-100">
            <Sidebar isOpen={sidebarOpen} toggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
            
            <div className="flex-1 flex flex-col overflow-hidden">
              <Navbar />
              
              <main className="flex-1 overflow-y-auto p-6">
                <div className="max-w-7xl mx-auto">
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/chat" element={<Chat />} />
                    <Route path="/documents" element={<Documents />} />
                    <Route path="/map" element={<Map />} />
                    <Route path="/analytics" element={<Analytics />} />
                    <Route path="/feedback" element={<Feedback />} />
                    <Route path="/settings" element={<Settings />} />
                  </Routes>
                </div>
              </main>
            </div>
          </div>
        </Router>
      </AppProvider>
    </QueryClientProvider>
  );
}

export default App;