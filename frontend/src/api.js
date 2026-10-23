// src/api.js
const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new Error("Cannot reach the backend. Is the server running?");
  }

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(response.status, extractMessage(data, response.status));
  }

  return data;
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

// FastAPI returns validation errors as a list, and other errors as {detail: "..."}.
function extractMessage(data, status) {
  if (data && typeof data.detail === "string") {
    return data.detail;
  }
  if (data && Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg).join("; ");
  }
  return `Request failed with status ${status}`;
}

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