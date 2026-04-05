export const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function readError(res: Response): Promise<string> {
  const t = await res.text();
  try {
    const j = JSON.parse(t) as { detail?: unknown };
    if (j.detail !== undefined) return String(j.detail);
  } catch {
    /* not JSON */
  }
  return t || `${res.status} ${res.statusText}`;
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(await readError(res));
  return res.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json() as Promise<T>;
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json() as Promise<T>;
}

export interface HealthResponse {
  status: string;
  services_running: number;
}

export interface InventoryItem {
  item_id: string;
  name: string;
  quantity: number;
  threshold: number;
  unit: string;
}

export interface Task {
  task_id?: number;
  title: string;
  description: string;
  status: string;
  created_at: string;
}

export interface ContainerRow {
  id: string;
  name: string;
  status: string;
}

export interface AuditLogRow {
  id: number;
  timestamp: string;
  service: string;
  event_type: string;
  user: string;
  details: string;
}
