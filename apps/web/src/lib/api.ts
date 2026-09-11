// API 客户端：封装 fetch，统一鉴权与错误处理

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8787/api/v1";

export class ApiError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

const TOKEN_KEY = "rf_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(t: string) {
  localStorage.setItem(TOKEN_KEY, t);
}
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

interface ReqOpts {
  method?: string;
  body?: unknown;
  auth?: boolean;
}

async function request<T>(path: string, opts: ReqOpts = {}): Promise<T> {
  const { method = "GET", body, auth = true } = opts;
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    const t = getToken();
    if (t) headers["Authorization"] = `Bearer ${t}`;
  }
  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  let json: { code?: number | string; message?: string; data?: T } | null = null;
  try {
    json = await res.json();
  } catch {
    /* 非 JSON 响应 */
  }
  if (!res.ok) {
    throw new ApiError(res.status, String(json?.code ?? "error"), json?.message ?? res.statusText);
  }
  if (json && typeof json === "object" && json.code !== undefined && json.code !== 0) {
    throw new ApiError(res.status, String(json.code), json.message ?? "请求失败");
  }
  return json?.data as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: "PUT", body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: "PATCH", body }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),

  async postFile<T>(path: string, file: File): Promise<T> {
    const headers: Record<string, string> = {};
    const t = getToken();
    if (t) headers["Authorization"] = `Bearer ${t}`;
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(`${API_URL}${path}`, { method: "POST", headers, body: fd });
    const json = await res.json().catch(() => null);
    if (!res.ok) {
      throw new ApiError(res.status, String(json?.code ?? "error"), json?.message ?? res.statusText);
    }
    return json?.data as T;
  },

  /** 下载文件（带鉴权），返回 blob 与文件名 */
  async download(path: string): Promise<{ blob: Blob; filename: string }> {
    const headers: Record<string, string> = {};
    const t = getToken();
    if (t) headers["Authorization"] = `Bearer ${t}`;
    const res = await fetch(`${API_URL}${path}`, { headers });
    if (!res.ok) {
      const json = await res.json().catch(() => null);
      throw new ApiError(res.status, String(json?.code ?? "error"), json?.message ?? res.statusText);
    }
    const blob = await res.blob();
    const cd = res.headers.get("Content-Disposition") ?? "";
    let filename = "export.zip";
    const m = cd.match(/filename\*=UTF-8''([^;]+)/i);
    if (m) {
      try {
        filename = decodeURIComponent(m[1]);
      } catch {
        /* 保底用默认名 */
      }
    }
    return { blob, filename };
  },
};

/** 触发浏览器下载一个 Blob */
export function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

/** 从 API 地址推导文件服务根地址（生产同域部署时自动适配，不再硬编码 localhost） */
function fileBase(): string {
  try {
    const u = new URL(API_URL);
    return `${u.protocol}//${u.host}`;
  } catch {
    return "http://localhost:8787";
  }
}

export function assetUrl(url: string | null | undefined): string {
  if (!url) return "";
  if (url.startsWith("http")) return url;
  return `${fileBase()}${url.startsWith("/") ? "" : "/"}${url}`;
}
