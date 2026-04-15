import { API_BASE } from "./config.js";
import { clearAuth, setAuth, state } from "./state.js";

export async function login(username, password) {
  const res = await fetch(`${API_BASE}/auth/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!res.ok) {
    throw new Error("登录失败，请检查用户名和密码");
  }

  const auth = await res.json();
  setAuth(auth);
  return auth;
}

export async function register(username, password, email = "") {
  const res = await fetch(`${API_BASE}/auth/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, email }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "注册失败，请检查输入内容");
  }

  const auth = await res.json();
  setAuth(auth);
  return auth;
}

export async function guestLogin() {
  const res = await fetch(`${API_BASE}/auth/guest/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "游客体验暂不可用");
  }

  const auth = await res.json();
  setAuth(auth);
  return auth;
}

export async function apiFetch(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (state.auth?.access) {
    headers.Authorization = `Bearer ${state.auth.access}`;
  }

  let response = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (response.status === 401 && state.auth?.refresh) {
    const refreshed = await refreshToken(state.auth.refresh);
    if (refreshed) {
      headers.Authorization = `Bearer ${state.auth.access}`;
      response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    }
  }

  if (response.status === 401) {
    clearAuth();
    if (typeof window !== "undefined") {
      window.location.hash = "#/login";
    }
    throw new Error("登录状态已失效，请重新登录。");
  }

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `请求失败: ${response.status}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

async function refreshToken(refresh) {
  const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  if (!res.ok) {
    clearAuth();
    return false;
  }

  const data = await res.json();
  setAuth({ ...state.auth, ...data, refresh: data.refresh || refresh });
  return true;
}
