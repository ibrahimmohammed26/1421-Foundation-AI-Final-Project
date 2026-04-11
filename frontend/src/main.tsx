import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import App from "./App";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import DataMap from "./pages/DataMap";
import Analytics from "./pages/Analytics";
import Documents from "./pages/Documents";
import Feedback from "./pages/Feedback";
import Settings from "./pages/Settings";

import "./index.css";

// root render
const rootEl = document.getElementById("root");

if (!rootEl) {
  throw new Error("Root element not found");
}

const root = ReactDOM.createRoot(rootEl);

root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>

        {/* main app wrapper */}
        <Route element={<App />}>
          <Route index element={<Dashboard />} />

          {/* routes */}
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="chat" element={<Chat />} />
          <Route path="map" element={<DataMap />} />
          <Route path="documents" element={<Documents />} />

          <Route path="analytics" element={<Analytics />} />
          <Route path="feedback" element={<Feedback />} />
          <Route path="settings" element={<Settings />} />
        </Route>

      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);