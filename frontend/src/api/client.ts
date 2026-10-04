import type {
  HealthStatus,
  MemoryItem,
  LiveMetrics,
  EvalStatus,
} from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function createSession(
  sessionId?: string
): Promise<{ session_id: string; message: string }> {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId || null }),
  });
  if (!res.ok) throw new Error(`Failed to create session: ${res.statusText}`);
  return res.json();
}

export async function sendChatMessage(
  sessionId: string,
  message: string
): Promise<{
  reply: string;
  retrieved: any[];
  tool_calls: any[];
  memory_ops: any[];
  skipped_ops: any[];
}> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Chat request failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchMemories(
  search?: string
): Promise<{ memories: MemoryItem[]; total: number }> {
  const url = search
    ? `${API_BASE}/memory?search=${encodeURIComponent(search)}`
    : `${API_BASE}/memory`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch memories: ${res.statusText}`);
  return res.json();
}

export async function updateMemoryFact(
  id: string,
  text: string
): Promise<{ status: string; memory: MemoryItem }> {
  const res = await fetch(`${API_BASE}/memory/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(`Failed to update memory fact: ${res.statusText}`);
  return res.json();
}

export async function deleteMemoryFact(
  id: string
): Promise<{ status: string; id: string }> {
  const res = await fetch(`${API_BASE}/memory/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to delete memory fact: ${res.statusText}`);
  return res.json();
}

export async function fetchLiveMetrics(): Promise<LiveMetrics> {
  const res = await fetch(`${API_BASE}/metrics/live`);
  if (!res.ok) throw new Error(`Failed to fetch tool metrics: ${res.statusText}`);
  return res.json();
}

export async function triggerEvalRun(): Promise<{
  run_id: string;
  status: string;
  message: string;
}> {
  const res = await fetch(`${API_BASE}/eval/run`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Failed to start evaluation: ${res.statusText}`);
  return res.json();
}

export async function fetchEvalStatus(runId: string): Promise<EvalStatus> {
  const res = await fetch(`${API_BASE}/eval/${runId}`);
  if (!res.ok) throw new Error(`Failed to fetch eval status: ${res.statusText}`);
  return res.json();
}

export function getExportLogUrl(): string {
  return `${API_BASE}/export/log`;
}
