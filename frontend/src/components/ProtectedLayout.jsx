// src/components/ProtectedLayout.jsx
import { Navigate, Outlet } from "react-router-dom";
import { isLoggedIn } from "../auth";
import Header from "./Header";

export default function ProtectedLayout() {
  if (!isLoggedIn()) {
    return <Navigate to="/auth" replace />;
  }

  return (
    <div className="min-h-screen bg-white">
      <Header />
      <Outlet />
    </div>
  );
}