// نبراس — عميل API (fetch wrapper + تخزين الجلسة)
import { tr } from "./i18n.js";

const TOKEN_KEY = "nibras_access";
const REFRESH_KEY = "nibras_refresh";
const USER_KEY = "nibras_user";

export const session = {
  get token() { return localStorage.getItem(TOKEN_KEY); },
  set token(v) { v ? localStorage.setItem(TOKEN_KEY, v) : localStorage.removeItem(TOKEN_KEY); },
  get refresh() { return localStorage.getItem(REFRESH_KEY); },
  set refresh(v) { v ? localStorage.setItem(REFRESH_KEY, v) : localStorage.removeItem(REFRESH_KEY); },
  get user() {
    try { return JSON.parse(localStorage.getItem(USER_KEY) || "null"); }
    catch { return null; }
  },
  set user(v) { v ? localStorage.setItem(USER_KEY, JSON.stringify(v)) : localStorage.removeItem(USER_KEY); },
  get isAdmin() { return !!this.user && Array.isArray(this.user.roles) && this.user.roles.includes("admin"); },
  clear() { this.token = null; this.refresh = null; this.user = null; },
};

let onUnauthorized = null;
export function setUnauthorizedHandler(fn) { onUnauthorized = fn; }

export function apiError(resp, data) {
  if (resp.status === 401) {
    session.clear();
    if (onUnauthorized) onUnauthorized();
    return new Error(tr("unauthorized"));
  }
  if (resp.status === 403) return new Error(tr("forbidden"));
  if (data && data.error) return new Error(data.error);
  if (data && data.message) return new Error(data.message);
  return new Error(`${tr("error")} (${resp.status})`);
}

async function request(method, url, body, isForm) {
  const headers = {};
  if (session.token) headers["Authorization"] = `Bearer ${session.token}`;
  let payload = body;
  if (!isForm && body !== undefined && body !== null) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  const opts = { method, headers, body: payload };
  if (url.includes("/api/auth/")) opts.cache = "no-store";
  const resp = await fetch(url, opts);
  let data = null;
  const ct = resp.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    try { data = await resp.json(); } catch { data = null; }
  }
  if (!resp.ok) {
    throw await apiError(resp, data);
  }
  return data;
}

export const api = {
  get: (url) => request("GET", url),
  post: (url, body) => request("POST", url, body),
  put: (url, body) => request("PUT", url, body),
  del: (url) => request("DELETE", url),
  upload: (url, file, field = "file") => {
    const fd = new FormData();
    fd.append(field, file);
    return request("POST", url, fd, true);
  },
  uploadFields: (url, formData, method = "POST") => request(method, url, formData, true),
};

export async function refreshToken() {
  if (!session.refresh) return false;
  try {
    const resp = await fetch("/api/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: session.refresh }),
    });
    if (!resp.ok) return false;
    const data = await resp.json();
    session.token = data.access_token;
    session.refresh = data.refresh_token;
    if (data.user) session.user = data.user;
    return true;
  } catch { return false; }
}
