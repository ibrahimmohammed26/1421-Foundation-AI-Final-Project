import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import App from "./App";
import Chat from "./pages/Chat";
import VoyageMap from "./pages/VoyageMap";
import Feedback from "./pages/Feedback";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<App />}>
          <Route index element={<Chat />} />
          <Route path="chat" element={<Chat />} />
          <Route path="map" element={<VoyageMap />} />
          <Route path="feedback" element={<Feedback />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
