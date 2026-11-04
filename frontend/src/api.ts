// Thin fetch wrapper for the FastAPI backend. Token lives in sessionStorage so closing the
// register's browser signs the cashier out.

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";
const TOKEN_KEY = "sts.token";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public fieldErrors: Record<string, string> = {},
  ) {
    super(message);
  }
}

function readToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

let token = readToken();
let onUnauthorized: () => void = () => {};

export function setToken(value: string | null) {
  token = value;
  try {
    if (value) sessionStorage.setItem(TOKEN_KEY, value);
    else sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable: token stays in memory */
  }
}

export const hasToken = () => token !== null;
export const setUnauthorizedHandler = (fn: () => void) => (onUnauthorized = fn);

type Params = Record<string, string | number | undefined | null>;

export async function api<T>(
  path: string,
  opts: { method?: string; body?: unknown; params?: Params } = {},
): Promise<T> {
  const url = new URL(path, BASE);
  for (const [k, v] of Object.entries(opts.params ?? {})) {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
  }
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";

  let resp: Response;
  try {
    resp = await fetch(url, {
      method: opts.method ?? "GET",
      headers,
      body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
    });
  } catch {
    throw new ApiError(0, `Cannot reach the API at ${BASE}. Is the backend running?`);
  }

  if (resp.status === 401 && token) onUnauthorized();
  if (!resp.ok) throw await toError(resp);
  return (resp.status === 204 ? undefined : await resp.json()) as T;
}

async function toError(resp: Response): Promise<ApiError> {
  const body = await resp.json().catch(() => ({}));
  const detail = body?.detail;
  if (typeof detail === "string") return new ApiError(resp.status, detail);
  if (Array.isArray(detail)) {
    // FastAPI 422: [{loc: ["body", "field"], msg}]
    const fields: Record<string, string> = {};
    for (const d of detail) {
      const field = String(d.loc?.[d.loc.length - 1] ?? "form");
      fields[field] = String(d.msg ?? "Invalid value").replace(/^Value error, /, "");
    }
    return new ApiError(resp.status, "Please fix the highlighted fields.", fields);
  }
  return new ApiError(resp.status, `Request failed (${resp.status})`);
}
