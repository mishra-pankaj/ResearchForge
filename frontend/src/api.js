// src/api.js
import { clearToken, getToken } from "./auth.js";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function extractMessage(data, status) {
  if (data && typeof data.detail === "string") return data.detail;
  if (data && Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg).join("; ");
  }
  return `Request failed with status ${status}`;
}

async function request(path, options = {}) {
  const token = getToken();

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
    });
  } catch {
    throw new Error("Cannot reach the backend. Is the server running?");
  }

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => null);

  if (response.status === 401 && token) {
    clearToken();
    window.location.href = "/auth";
    throw new ApiError(401, "Your session has expired. Please log in again.");
  }

  if (!response.ok) {
    throw new ApiError(response.status, extractMessage(data, response.status));
  }

  return data;
}

// Auth

export function register(email, password) {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function login(email, password) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function getMe() {
  return request("/auth/me");
}

// Research

export function createResearch(topic) {
  return request("/research", {
    method: "POST",
    body: JSON.stringify({ topic }),
  });
}

export function getResearch(id) {
  return request(`/research/${id}`);
}

export function listResearch({ limit = 20, offset = 0 } = {}) {
  return request(`/research?limit=${limit}&offset=${offset}`);
}

export function deleteResearch(id) {
  return request(`/research/${id}`, { method: "DELETE" });
}