/**
 * API Client — communicates with the FastAPI backend.
 * Handles JWT auth tokens automatically.
 */

const API_BASE = "http://localhost:8000/api";

// ── Token Management ──────────────────────────────────────────────

function getToken() {
  return localStorage.getItem("scrapo_token");
}

function setToken(token) {
  localStorage.setItem("scrapo_token", token);
}

function removeToken() {
  localStorage.removeItem("scrapo_token");
  localStorage.removeItem("scrapo_user");
}

function getUser() {
  try {
    return JSON.parse(localStorage.getItem("scrapo_user"));
  } catch {
    return null;
  }
}

function setUser(user) {
  localStorage.setItem("scrapo_user", JSON.stringify(user));
}

function isLoggedIn() {
  return !!getToken();
}


// ── HTTP Wrapper ──────────────────────────────────────────────────

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = { "Content-Type": "application/json" };

  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const config = { headers, ...options };

  const response = await fetch(url, config);

  // Handle 401 — token expired or invalid
  if (response.status === 401) {
    removeToken();
    window.location.reload();
    throw new Error("Session expired. Please log in again.");
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }

  // For CSV export, return raw response
  if (response.headers.get("content-type")?.includes("text/csv")) {
    return response;
  }

  return response.json();
}


// ── Auth ──────────────────────────────────────────────────────────

export async function register(username, email, password) {
  const data = await request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, email, password }),
  });
  setToken(data.access_token);
  setUser(data.user);
  return data;
}

export async function login(username, password) {
  const data = await request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  setToken(data.access_token);
  setUser(data.user);
  return data;
}

export function logout() {
  removeToken();
}

export async function getProfile() {
  return request("/auth/me");
}

export async function updateProfile(data) {
  return request("/auth/me", { method: "PUT", body: JSON.stringify(data) });
}


// ── Products ──────────────────────────────────────────────────────

export async function fetchProducts() {
  return request("/products/");
}

export async function addProduct(productUrl, targetPrice = null) {
  const body = { url: productUrl };
  if (targetPrice) body.target_price = parseFloat(targetPrice);
  return request("/products/", { method: "POST", body: JSON.stringify(body) });
}

export async function getProductDetail(id) {
  return request(`/products/${id}`);
}

export async function deleteProduct(id) {
  return request(`/products/${id}`, { method: "DELETE" });
}

export async function refreshPrice(id) {
  return request(`/products/${id}/refresh`, { method: "POST" });
}

export async function exportPriceHistory(id) {
  const response = await request(`/products/${id}/export`);
  return response;
}


// ── Compare ───────────────────────────────────────────────────────

export async function compareProducts(query = "") {
  const params = query ? `?query=${encodeURIComponent(query)}` : "";
  return request(`/compare/${params}`);
}


// Re-export helpers
export { isLoggedIn, getUser, getToken, removeToken };
