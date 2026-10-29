// src/App.jsx
import { Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing";
import Auth from "./pages/Auth";
import Home from "./pages/Home";
import History from "./pages/History";
import ResearchPage from "./pages/ResearchPage";
import ProtectedLayout from "./components/ProtectedLayout";

function Placeholder({ name }) {
  return <p className="p-8 text-slate-600">{name} page: coming next.</p>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/auth" element={<Auth />} />

      <Route element={<ProtectedLayout />}>
        <Route path="/home" element={<Home />} />
        <Route path="/history" element={<History />} />
        <Route path="/research/:id" element={<ResearchPage />} />
      </Route>

      <Route path="*" element={<Placeholder name="Not found" />} />
    </Routes>
  );
}