// The ONLY place the frontend talks to the backend. Components never call fetch directly.
import type {
  AuditRow, AuditVerify, Decision, EvalResult, Health, NewSessionResponse, Scenario, SegmentView, StreamEvent,
} from "./types";

export const API_URL: string = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "http://localhost:8000";

const CODE_KEY = "passport.demoCode";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
  }
}

export function getAccessCode(): string {
  try {
    return sessionStorage.getItem(CODE_KEY) ?? "";
  } catch {
    return "";
  }
}

export function setAccessCode(code: string): void {
  try {
    sessionStorage.setItem(CODE_KEY, code);
  } catch {
    /* storage blocked: the code just won't be remembered */
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body) headers.set("Content-Type", "application/json");
  if (init.method === "POST" && getAccessCode()) headers.set("X-Demo-Code", getAccessCode());
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "network_error", `Can't reach the backend at ${API_URL}. Is it running?`);
  }
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const err = body?.error ?? {};
    throw new ApiError(res.status, err.code ?? "http_error", err.message ?? `Request failed (${res.status}).`);
  }
  return body as T;
}

const post = <T>(path: string, data?: unknown) =>
  request<T>(path, { method: "POST", body: data === undefined ? undefined : JSON.stringify(data) });

export const api = {
  health: () => request<Health>("/health"),
  scenarios: () => request<Scenario[]>("/scenarios"),
  startSession: (p: { scenario_id: string; shield_on: boolean; mode: "replay" | "live"; user_request?: string }) =>
    post<NewSessionResponse>("/sessions", p),
  session: (id: string) =>
    request<{ decisions: Decision[]; pending_approvals: Decision[]; session: { status: string } }>(`/sessions/${id}`),
  segment: (sessionId: string, segmentId: string) =>
    request<SegmentView>(`/sessions/${sessionId}/segments/${encodeURIComponent(segmentId)}`),
  approve: (decisionId: string, approve: boolean) => post<{ ok: boolean }>(`/approvals/${decisionId}`, { approve }),
  audit: (limit = 100) => request<{ items: AuditRow[] }>(`/audit?limit=${limit}`),
  verifyAudit: () => request<AuditVerify>("/audit/verify"),
  runEval: () => post<EvalResult>("/eval/run"),
  latestEval: () => request<EvalResult & { id: string; ts: number }>("/eval/latest"),
  reset: () => post<{ ok: boolean }>("/admin/reset"),
};

/** Live events for one session. Returns a function that closes the stream. */
export function subscribe(sessionId: string, onEvent: (e: StreamEvent) => void, onError: (msg: string) => void): () => void {
  const es = new EventSource(`${API_URL}/sessions/${sessionId}/events`);
  const types = ["session_started", "capsule", "llm_step", "decision", "approval_needed", "approval_result",
    "tool_result", "world_event", "done", "error"];
  for (const t of types) {
    es.addEventListener(t, (msg) => {
      const ev = JSON.parse((msg as MessageEvent).data) as StreamEvent;
      onEvent(ev);
      if (t === "done" || t === "error") es.close();
    });
  }
  es.onerror = () => {
    if (es.readyState === EventSource.CLOSED) onError("Lost the live connection to the backend.");
  };
  return () => es.close();
}
