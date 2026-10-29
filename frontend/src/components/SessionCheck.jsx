// src/components/SessionCheck.jsx
import { useEffect } from "react";
import { clearToken, getToken } from "../auth";
import { getMe } from "../api";

// Runs once when the app loads. If a stored token is rejected by the
// backend, it is cleared right away, so the header never shows Logout
// for a session that no longer works.
export default function SessionCheck() {
  useEffect(() => {
    if (!getToken()) return;

    getMe().catch(() => {
      clearToken();
    });
  }, []);

  return null;
}