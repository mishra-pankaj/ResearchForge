
const TOKEN_KEY = "auth_token";



export function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}



export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}


function isExpired(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return typeof payload.exp === "number" && payload.exp * 1000 <= Date.now();
  } catch {
    return true;
  }
}


export function isLoggedIn() {
  const token = getToken();
  if (!token) return false;
  if (isExpired(token)) {
    clearToken();
    return false;
  }
  return true;
}