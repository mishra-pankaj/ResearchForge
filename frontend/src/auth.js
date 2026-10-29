// src/auth.js
const TOKEN_KEY = "auth_token";

// export function saveToken(token) {
//   localStorage.setItem(TOKEN_KEY, token);
// }

export function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

// export function clearToken() {
//   localStorage.removeItem(TOKEN_KEY);
// }

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

// Reads the expiry time from a JWT without verifying it.
// The backend still verifies the signature; this only avoids using an expired token.
function isExpired(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return typeof payload.exp === "number" && payload.exp * 1000 <= Date.now();
  } catch {
    return true;
  }
}

// A token counts as logged in only if it is present and not expired.
export function isLoggedIn() {
  const token = getToken();
  if (!token) return false;
  if (isExpired(token)) {
    clearToken();
    return false;
  }
  return true;
}