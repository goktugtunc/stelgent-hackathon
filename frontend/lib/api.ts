// lib/api.js

const API_BASE_URL = "http://hackstack.com.tr:8005";
console.log("API_BASE_URL:", API_BASE_URL); // Debug için

// Freighter public key = session token
function getSessionToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export async function apiRequest(path, options) {
  // options undefined geldiyse boş bir obje oluştur
  options = options || {};

  // headers yoksa oluştur
  options.headers = options.headers || {};

  // JSON body gönderiyorsak Content-Type ekle
  if (!options.headers["Content-Type"] && !(options.body instanceof FormData)) {
    options.headers["Content-Type"] = "application/json";
  }

  // Session token header'ı ekle (Backend X-Public-Key veya Authorization: Bearer bekliyor)
  const token = getSessionToken();
  if (token) {
    options.headers["Authorization"] = `Bearer ${token}`;
  }

  const fullUrl = `${API_BASE_URL}${path}`;
  console.log("Making API request to:", fullUrl); // Debug için
  return fetch(fullUrl, options);
}

export function apiGet(path) {
  return apiRequest(path, { method: "GET" });
}

export function apiPost(path, body) {
  return apiRequest(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function apiPut(path, body) {
  return apiRequest(path, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export function apiDelete(path) {
  return apiRequest(path, { method: "DELETE" });
}
