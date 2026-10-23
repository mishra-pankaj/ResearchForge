// src/App.jsx
import { Routes, Route } from "react-router-dom";
import ResearchPage from "./pages/ResearchPage";
import History from "./pages/History";
import Home from "./pages/Home";

function Placeholder({ name }) {
  return <p className="p-8 text-slate-600">{name} page: coming next.</p>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/research/:id" element={<ResearchPage />} />
      <Route path="/history" element={<History />} />
      <Route path="*" element={<Placeholder name="Not found" />} />
    </Routes>
  );
}