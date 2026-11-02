import { useEffect } from "react";
import { clearToken, getToken } from "../auth";
import { getMe } from "../api";


export default function SessionCheck() {
  useEffect(() => {
    if (!getToken()) return;

    getMe().catch(() => {
      clearToken();
    });
  }, []);

  return null;
}