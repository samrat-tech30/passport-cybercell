import { useCallback, useEffect, useReducer, useRef } from "react";
import { api, ApiError, subscribe } from "./api/client";
import type { Capsule, Decision, StreamEvent, WorldEvent } from "./api/types";

export type RunStatus = "idle" | "starting" | "running" | "waiting" | "done" | "error";

export interface RunState {
  sessionId: string | null;
  status: RunStatus;
  shieldOn: boolean;
  capsule: Capsule | null;
  decisions: Decision[];
  steps: { step: number; content: string }[];
  world: WorldEvent[];
  pending: Decision | null;
  answer: string | null;
  error: string | null;
  lastSeq: number;
}

const initial: RunState = {
  sessionId: null, status: "idle", shieldOn: true, capsule: null, decisions: [], steps: [], world: [],
  pending: null, answer: null, error: null, lastSeq: 0,
};

type Action =
  | { type: "start"; shieldOn: boolean }
  | { type: "started"; sessionId: string; capsule: Capsule }
  | { type: "event"; event: StreamEvent }
  | { type: "fail"; message: string }
  | { type: "reset" };

function upsert(list: Decision[], d: Decision): Decision[] {
  const i = list.findIndex((x) => x.id === d.id);
  if (i === -1) return [...list, d];
  const next = list.slice();
  next[i] = d;
  return next;
}

function reducer(s: RunState, a: Action): RunState {
  switch (a.type) {
    case "start":
      return { ...initial, status: "starting", shieldOn: a.shieldOn };
    case "started":
      return { ...s, sessionId: a.sessionId, capsule: a.capsule, status: "running" };
    case "fail":
      return { ...s, status: "error", error: a.message };
    case "reset":
      return initial;
    case "event": {
      const e = a.event;
      if (e.seq <= s.lastSeq) return s; // already seen (reconnect)
      const next = { ...s, lastSeq: e.seq };
      switch (e.type) {
        case "capsule":
          return { ...next, capsule: e.data as unknown as Capsule };
        case "llm_step": {
          const content = String(e.data.content ?? "");
          return content ? { ...next, steps: [...s.steps, { step: Number(e.data.step), content }] } : next;
        }
        case "decision":
          return { ...next, decisions: upsert(s.decisions, e.data as unknown as Decision) };
        case "approval_needed":
          return { ...next, status: "waiting", pending: e.data as unknown as Decision };
        case "approval_result":
          return { ...next, status: "running", pending: null };
        case "world_event":
          return { ...next, world: [...s.world, e.data as unknown as WorldEvent] };
        case "done":
          return { ...next, status: "done", pending: null, answer: String(e.data.answer ?? "") };
        case "error":
          return { ...next, status: "error", pending: null, error: String(e.data.message ?? "The run failed.") };
        default:
          return next;
      }
    }
  }
}

export function useRun() {
  const [state, dispatch] = useReducer(reducer, initial);
  const close = useRef<(() => void) | null>(null);

  useEffect(() => () => close.current?.(), []);

  const start = useCallback(async (p: { scenarioId: string; shieldOn: boolean; mode: "replay" | "live" }) => {
    close.current?.();
    dispatch({ type: "start", shieldOn: p.shieldOn });
    try {
      const res = await api.startSession({ scenario_id: p.scenarioId, shield_on: p.shieldOn, mode: p.mode });
      dispatch({ type: "started", sessionId: res.session_id, capsule: res.capsule });
      close.current = subscribe(
        res.session_id,
        (event) => dispatch({ type: "event", event }),
        (message) => dispatch({ type: "fail", message }),
      );
    } catch (e) {
      dispatch({ type: "fail", message: e instanceof ApiError ? e.message : "Could not start the run." });
    }
  }, []);

  const answer = useCallback(async (decisionId: string, approve: boolean) => {
    try {
      await api.approve(decisionId, approve);
    } catch (e) {
      dispatch({ type: "fail", message: e instanceof ApiError ? e.message : "Could not send your answer." });
    }
  }, []);

  return { state, start, answer, reset: () => dispatch({ type: "reset" }) };
}
